import base64
import csv
import io
import secrets
from pathlib import Path

import qrcode
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .context import private_ips, public_base
from .grading import public_question, rescore, score_payload, snapshot_question
from .models import (
    Answer,
    GradeChange,
    Lesson,
    LessonSession,
    SessionParticipant,
    TestAttempt,
)


def _teacher(user):
    return user.is_authenticated and (getattr(user, "role", "") == "TH" or user.is_staff)


def _code():
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(6))


def _participant(request, session):
    pid = request.session.get(f"part_{session.id}")
    if not pid:
        return None
    return SessionParticipant.objects.filter(id=pid, session=session).first()


def _join_ip(request):
    preferred = request.GET.get("ip") or request.session.get("join_ip")
    if preferred and preferred in private_ips():
        request.session["join_ip"] = preferred
        return preferred
    return public_base(request).split("://", 1)[1].split(":")[0]


def _join_url(request, session):
    return f"{public_base(request, _join_ip(request))}/sapak/{session.code}/"


def _qr_svg(data):
    code = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=4,
    )
    code.add_data(data)
    code.make(fit=True)
    image = code.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f'<img class="qr-img" alt="{data}" src="data:image/png;base64,{encoded}">'


def _screen_path(session):
    from django.conf import settings
    folder = Path(settings.MEDIA_ROOT) / "screens"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{session.id}.jpg"


def _seconds_left(attempt):
    left = int((attempt.deadline - timezone.now()).total_seconds())
    return max(left, 0)


def _close_if_expired(attempt):
    if attempt.status == "in_progress" and timezone.now() >= attempt.deadline:
        _submit(attempt)
    return attempt


def _submit(attempt):
    if attempt.status != "in_progress":
        rescore(attempt)
        return attempt
    attempt.submitted_at = timezone.now()
    attempt.status = "submitted"
    attempt.save(update_fields=["submitted_at", "status"])
    return rescore(attempt)


def _owns_attempt(request, attempt):
    if _teacher(request.user) and attempt.session and attempt.session.teacher_id == request.user.id:
        return True
    if request.user.is_authenticated and attempt.student_id == request.user.id:
        return True
    participant = _participant(request, attempt.session) if attempt.session_id else None
    return participant is not None and attempt.participant_id == participant.id


@login_required
@require_POST
def start_session(request, lesson_id):
    if not _teacher(request.user):
        return redirect("home")
    lesson = get_object_or_404(Lesson, id=lesson_id)
    code = _code()
    while LessonSession.objects.filter(code=code).exists():
        code = _code()
    session = LessonSession.objects.create(
        lesson=lesson,
        teacher=request.user,
        code=code,
        status="live",
        join_open=True,
    )
    return redirect("session_board", code=session.code)


def join_by_code(request):
    error = ""
    if request.method == "POST":
        code = (request.POST.get("code") or "").strip().upper()
        if LessonSession.objects.filter(code=code).exists():
            return redirect("session_board", code=code)
        error = "Beýle kod tapylmady."
    return render(request, "education/join_code.html", {"error": error})


def session_board(request, code):
    session = get_object_or_404(LessonSession, code=code)
    teacher = _teacher(request.user) and request.user.id == session.teacher_id
    participant = _participant(request, session)
    if request.method == "POST" and not teacher:
        if not session.join_open and participant is None:
            return render(request, "education/join_closed.html", {"session": session})
        name = (request.POST.get("name") or "").strip()[:80]
        if not name:
            return render(request, "education/session_board.html", {
                "session": session, "lesson": session.lesson, "error": "Adyňyzy ýazyň.",
                "need_name": True, "join_url": _join_url(request, session),
            })
        participant, _ = SessionParticipant.objects.get_or_create(
            session=session,
            display_name=name,
            defaults={"user": request.user if request.user.is_authenticated else None},
        )
        request.session[f"part_{session.id}"] = participant.id
        return redirect("session_board", code=code)
    if not teacher and participant is None:
        return render(request, "education/session_board.html", {
            "session": session,
            "lesson": session.lesson,
            "need_name": True,
            "join_url": _join_url(request, session),
            "qr_svg": _qr_svg(_join_url(request, session)),
        })
    participants = session.participants.order_by("joined_at")
    join_url = _join_url(request, session)
    return render(request, "education/session_board.html", {
        "session": session,
        "teacher_view": teacher,
        "participant": participant,
        "participants": participants,
        "join_url": join_url,
        "join_ip": _join_ip(request),
        "join_ips": private_ips(),
        "qr_svg": _qr_svg(join_url) if teacher else "",
        "lesson": session.lesson,
    })


@login_required
@require_POST
def toggle_join(request, code):
    session = get_object_or_404(LessonSession, code=code, teacher=request.user)
    session.join_open = not session.join_open
    session.save(update_fields=["join_open"])
    return redirect("session_board", code=code)


def heartbeat(request, code):
    session = get_object_or_404(LessonSession, code=code)
    participant = _participant(request, session)
    if participant:
        participant.last_seen = timezone.now()
        participant.save(update_fields=["last_seen"])
    online = session.participants.filter(last_seen__gte=timezone.now() - timezone.timedelta(seconds=20)).count()
    return JsonResponse({
        "online": online,
        "screen": session.screen_sharing,
        "join_open": session.join_open,
    })


def begin_attempt(request, code):
    session = get_object_or_404(LessonSession, code=code)
    lesson = session.lesson
    if not lesson.test_id:
        return render(request, "education/error.html", {"error": "Bu sapakda synag ýok."})
    teacher = _teacher(request.user) and request.user.id == session.teacher_id
    participant = _participant(request, session)
    if not teacher and participant is None:
        return redirect("session_board", code=code)
    test = lesson.test
    existing = TestAttempt.objects.filter(session=session, status="in_progress")
    if participant:
        existing = existing.filter(participant=participant)
    elif teacher:
        existing = existing.filter(student=request.user)
    current = existing.order_by("-started_at").first()
    if current:
        return redirect("attempt_page", attempt_id=current.id)
    if not test.allow_retry:
        done = TestAttempt.objects.filter(session=session).exclude(status="in_progress")
        if participant:
            done = done.filter(participant=participant)
        elif request.user.is_authenticated:
            done = done.filter(student=request.user)
        if done.exists():
            return render(request, "education/error.html", {"error": "Bu synagy gaýtadan tabşyryp bolmaýar."})
    questions = list(test.questions.all())
    if test.shuffle_questions:
        secrets.SystemRandom().shuffle(questions)
    snapshot = [snapshot_question(q) for q in questions]
    attempt = TestAttempt.objects.create(
        test=test,
        session=session,
        participant=participant,
        student=request.user if request.user.is_authenticated else None,
        display_name=participant.display_name if participant else request.user.username,
        snapshot=snapshot,
        deadline=timezone.now() + timezone.timedelta(minutes=test.duration_minutes or 15),
        max_score=sum(item["points"] for item in snapshot),
    )
    return redirect("attempt_page", attempt_id=attempt.id)


def attempt_page(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id)
    if not _owns_attempt(request, attempt):
        return redirect("home")
    attempt = _close_if_expired(attempt)
    if attempt.status != "in_progress":
        return redirect("attempt_result", attempt_id=attempt.id)
    test = attempt.test
    questions = [public_question(item, test.shuffle_options) for item in attempt.snapshot]
    saved = {a.question_id: a for a in attempt.answers.all()}
    return render(request, "education/attempt.html", {
        "attempt": attempt,
        "questions": questions,
        "saved": saved,
        "seconds_left": _seconds_left(attempt),
    })


@require_POST
def save_answer(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id)
    if not _owns_attempt(request, attempt):
        return JsonResponse({"error": "Rugsat ýok"}, status=403)
    attempt = _close_if_expired(attempt)
    if attempt.status != "in_progress":
        return JsonResponse({"expired": True, "status": attempt.status})
    import json
    try:
        body = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Nädogry maglumat"}, status=400)
    qid = body.get("question_id")
    item = next((q for q in attempt.snapshot if q["id"] == qid), None)
    if not item:
        return JsonResponse({"error": "Sorag tapylmady"}, status=404)
    payload = body.get("payload") or {}
    points, manual = score_payload(item, payload)
    answer, _ = Answer.objects.get_or_create(attempt=attempt, question_id=qid)
    if answer.status == "submitted" and attempt.status != "in_progress":
        return JsonResponse({"status": "submitted"})
    answer.payload = payload
    answer.needs_manual = manual
    answer.graded = not manual
    answer.points_awarded = points
    answer.status = "saved"
    answer.save()
    return JsonResponse({
        "status": "saved",
        "label": "Saklandy",
        "seconds_left": _seconds_left(attempt),
    })


@require_POST
def upload_practical(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id)
    if not _owns_attempt(request, attempt):
        return JsonResponse({"error": "Rugsat ýok"}, status=403)
    attempt = _close_if_expired(attempt)
    if attempt.status != "in_progress":
        return JsonResponse({"expired": True})
    qid = int(request.POST.get("question_id") or 0)
    item = next((q for q in attempt.snapshot if q["id"] == qid), None)
    if not item or item["qtype"] != "practical":
        return JsonResponse({"error": "Sorag tapylmady"}, status=404)
    upload = request.FILES.get("file")
    answer, _ = Answer.objects.get_or_create(attempt=attempt, question_id=qid)
    if upload:
        answer.file = upload
    answer.payload = {"note": request.POST.get("note") or ""}
    answer.needs_manual = True
    answer.graded = False
    answer.points_awarded = None
    answer.status = "saved"
    answer.save()
    return JsonResponse({"status": "saved", "label": "Saklandy"})


@require_POST
def submit_attempt(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id)
    if not _owns_attempt(request, attempt):
        return redirect("home")
    _submit(attempt)
    return redirect("attempt_result", attempt_id=attempt.id)


def attempt_state(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id)
    if not _owns_attempt(request, attempt):
        return JsonResponse({"error": "Rugsat ýok"}, status=403)
    attempt = _close_if_expired(attempt)
    return JsonResponse({
        "seconds_left": _seconds_left(attempt),
        "status": attempt.status,
        "expired": attempt.status != "in_progress",
    })


def attempt_result(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id)
    if not _owns_attempt(request, attempt):
        return redirect("home")
    released = attempt.test.results_released
    teacher = _teacher(request.user) and attempt.session and attempt.session.teacher_id == request.user.id
    if not released and not teacher:
        return render(request, "education/attempt_wait.html", {"attempt": attempt})
    by_id = {item["id"]: item for item in attempt.snapshot}
    rows = []
    for answer in attempt.answers.all():
        item = by_id.get(answer.question_id)
        if not item:
            continue
        rows.append({"item": item, "answer": answer})
    return render(request, "education/attempt_result.html", {
        "attempt": attempt,
        "rows": rows,
        "teacher_view": teacher,
    })


@login_required
def class_results(request, code):
    session = get_object_or_404(LessonSession, code=code)
    if not _teacher(request.user) or session.teacher_id != request.user.id:
        return redirect("home")
    attempts = session.attempts.exclude(status="in_progress").order_by("display_name")
    wrong = {}
    for attempt in attempts:
        snap = {item["id"]: item for item in attempt.snapshot}
        for answer in attempt.answers.all():
            item = snap.get(answer.question_id)
            if not item or answer.needs_manual and not answer.graded:
                continue
            if float(answer.points_awarded or 0) < float(item["points"] or 0):
                wrong[item["text"]] = wrong.get(item["text"], 0) + 1
    top_wrong = sorted(wrong.items(), key=lambda pair: pair[1], reverse=True)[:5]
    return render(request, "education/class_results.html", {
        "session": session,
        "attempts": attempts,
        "top_wrong": top_wrong,
    })


@login_required
def review_attempt(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id)
    if not _teacher(request.user):
        return redirect("home")
    if request.method == "POST":
        answer = get_object_or_404(Answer, id=request.POST.get("answer_id"), attempt=attempt)
        reason = (request.POST.get("reason") or "").strip()
        if not reason:
            return render(request, "education/review_attempt.html", {
                "attempt": attempt, "error": "Sebäbini ýazyň.",
                "rows": _review_rows(attempt),
            })
        try:
            new_points = float(request.POST.get("points") or 0)
        except ValueError:
            new_points = 0
        GradeChange.objects.create(
            answer=answer,
            teacher=request.user,
            old_points=answer.points_awarded,
            new_points=new_points,
            reason=reason,
        )
        answer.points_awarded = new_points
        answer.graded = True
        answer.teacher_comment = request.POST.get("comment") or answer.teacher_comment
        answer.save()
        rescore(attempt)
        return redirect("review_attempt", attempt_id=attempt.id)
    return render(request, "education/review_attempt.html", {
        "attempt": attempt,
        "rows": _review_rows(attempt),
    })


def _review_rows(attempt):
    by_id = {item["id"]: item for item in attempt.snapshot}
    rows = []
    for answer in attempt.answers.all():
        item = by_id.get(answer.question_id)
        if item:
            rows.append({"item": item, "answer": answer, "changes": answer.changes.all()})
    return rows


@login_required
@require_POST
def release_results(request, code):
    session = get_object_or_404(LessonSession, code=code, teacher=request.user)
    if session.lesson.test_id:
        test = session.lesson.test
        test.results_released = True
        test.save(update_fields=["results_released"])
    return redirect("class_results", code=code)


@login_required
@require_POST
def extra_time(request, code):
    session = get_object_or_404(LessonSession, code=code, teacher=request.user)
    try:
        minutes = int(request.POST.get("minutes") or 1)
    except ValueError:
        minutes = 1
    minutes = max(1, min(minutes, 30))
    for attempt in session.attempts.filter(status="in_progress"):
        attempt.deadline = attempt.deadline + timezone.timedelta(minutes=minutes)
        attempt.save(update_fields=["deadline"])
    return redirect("session_board", code=code)


@login_required
def export_results(request, code):
    session = get_object_or_404(LessonSession, code=code, teacher=request.user)
    kind = request.GET.get("fmt", "csv")
    rows = [["Ady", "Topar", "Synag", "Bal", "Maks", "Göterim", "Wagt", "Ýagdaý", "El bilen"]]
    group = session.lesson.course.group_name
    for attempt in session.attempts.exclude(status="in_progress"):
        rows.append([
            attempt.display_name,
            group,
            attempt.test.title,
            attempt.score,
            attempt.max_score,
            attempt.percent,
            timezone.localtime(attempt.submitted_at).strftime("%Y-%m-%d %H:%M") if attempt.submitted_at else "",
            attempt.get_status_display(),
            attempt.pending_manual,
        ])
    if kind == "xlsx":
        return HttpResponse(_xlsx(rows), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={
            "Content-Disposition": f'attachment; filename="netije-{session.code}.xlsx"'
        })
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerows(rows)
    response = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="netije-{session.code}.csv"'
    return response


def print_attempt(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id)
    if not _owns_attempt(request, attempt):
        return redirect("home")
    if not attempt.test.results_released and not _teacher(request.user):
        return redirect("attempt_result", attempt_id=attempt.id)
    return render(request, "education/print_attempt.html", {
        "attempt": attempt,
        "rows": _review_rows(attempt),
    })


def _xlsx(rows):
    import zipfile
    from xml.sax.saxutils import escape

    def col(n):
        name = ""
        while n:
            n, rem = divmod(n - 1, 26)
            name = chr(65 + rem) + name
        return name

    cells = []
    for r, row in enumerate(rows, start=1):
        for c, value in enumerate(row, start=1):
            ref = f"{col(c)}{r}"
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>')
        cells.append("")
    sheet_rows = []
    idx = 0
    flat = []
    r = 1
    line = []
    for r_i, row in enumerate(rows, start=1):
        bits = []
        for c, value in enumerate(row, start=1):
            ref = f"{col(c)}{r_i}"
            bits.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>')
        sheet_rows.append(f'<row r="{r_i}">{"".join(bits)}</row>')
    sheet = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_rows)}</sheetData></worksheet>'
    )
    content_types = '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>'''
    rels = '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>'''
    wb = '''<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="Netije" sheetId="1" r:id="rId1"/></sheets></workbook>'''
    wb_rels = '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>'''
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("xl/workbook.xml", wb)
        zf.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        zf.writestr("xl/worksheets/sheet1.xml", sheet)
    return buffer.getvalue()


@login_required
@require_POST
def screen_toggle(request, code):
    session = get_object_or_404(LessonSession, code=code, teacher=request.user)
    session.screen_sharing = request.POST.get("on") == "1"
    if not session.screen_sharing:
        path = _screen_path(session)
        if path.exists():
            path.unlink()
    session.save(update_fields=["screen_sharing"])
    return JsonResponse({"screen": session.screen_sharing})


@login_required
@require_POST
def screen_frame(request, code):
    session = get_object_or_404(LessonSession, code=code, teacher=request.user)
    upload = request.FILES.get("frame")
    if not upload:
        return JsonResponse({"error": "Kadr ýok"}, status=400)
    path = _screen_path(session)
    path.write_bytes(upload.read())
    session.screen_sharing = True
    session.screen_updated_at = timezone.now()
    session.save(update_fields=["screen_sharing", "screen_updated_at"])
    return JsonResponse({"ok": True})


def screen_image(request, code):
    session = get_object_or_404(LessonSession, code=code)
    path = _screen_path(session)
    if not session.screen_sharing or not path.exists():
        return HttpResponse(status=204)
    return FileResponse(path.open("rb"), content_type="image/jpeg")


@login_required
def download_backup(request):
    if not _teacher(request.user):
        return redirect("home")
    from django.conf import settings
    from django.core.management import call_command
    folder = Path(settings.BASE_DIR) / "backups"
    folder.mkdir(exist_ok=True)
    stamp = timezone.now().strftime("%Y%m%d-%H%M%S")
    dest = folder / f"db-{stamp}.sqlite3"
    src = Path(settings.DATABASES["default"]["NAME"])
    dest.write_bytes(src.read_bytes())
    json_path = folder / f"dump-{stamp}.json"
    with json_path.open("w", encoding="utf-8") as handle:
        call_command("dumpdata", "education", stdout=handle)
    return FileResponse(dest.open("rb"), as_attachment=True, filename=dest.name)
