import random


def _norm(value):
    return " ".join(str(value or "").strip().lower().split())


def snapshot_question(question):
    qtype = question.qtype or "choice"
    if qtype == "choice" and not question.option_a and question.correct_answer:
        qtype = "short"
    return {
        "id": question.id,
        "text": question.text,
        "qtype": qtype,
        "points": float(question.points or 0),
        "hint": question.hint or "",
        "explanation": question.explanation or "",
        "options": [question.option_a, question.option_b, question.option_c, question.option_d],
        "correct_answer": question.correct_answer or "",
        "accepted_answers": question.accepted_answers or "",
        "number_value": question.number_value,
        "number_unit": question.number_unit or "",
        "number_tolerance": float(question.number_tolerance or 0),
        "match_pairs": question.match_pairs or [],
        "order_items": question.order_items or [],
        "rubric": question.rubric or "",
    }


def public_question(item, shuffle_options=False):
    data = {
        "id": item["id"],
        "text": item["text"],
        "qtype": item["qtype"],
        "points": item["points"],
        "hint": item["hint"],
    }
    options = [opt for opt in item.get("options") or [] if opt]
    if shuffle_options and options:
        options = options[:]
        random.shuffle(options)
    if item["qtype"] in ("choice", "multi"):
        data["options"] = options
    if item["qtype"] == "number":
        data["number_unit"] = item.get("number_unit") or ""
    if item["qtype"] == "match":
        pairs = list(item.get("match_pairs") or [])
        rights = [pair[1] for pair in pairs]
        random.shuffle(rights)
        data["lefts"] = [pair[0] for pair in pairs]
        data["rights"] = rights
    if item["qtype"] == "order":
        items = list(item.get("order_items") or [])
        random.shuffle(items)
        data["items"] = items
    if item["qtype"] in ("open", "practical"):
        data["rubric"] = item.get("rubric") or ""
    return data


def score_payload(item, payload):
    points = float(item.get("points") or 0)
    qtype = item.get("qtype")
    payload = payload or {}
    if qtype in ("open", "practical"):
        return None, True
    if qtype == "choice":
        ok = _norm(payload.get("value")) == _norm(item.get("correct_answer"))
        return (points if ok else 0), False
    if qtype == "multi":
        correct = {_norm(part) for part in str(item.get("correct_answer") or "").split("|") if part.strip()}
        given = {_norm(part) for part in payload.get("values") or []}
        return (points if correct and given == correct else 0), False
    if qtype == "short":
        accepted = [item.get("correct_answer") or ""]
        accepted.extend(str(item.get("accepted_answers") or "").split("|"))
        allowed = {_norm(part) for part in accepted if str(part).strip()}
        ok = _norm(payload.get("value")) in allowed
        return (points if ok else 0), False
    if qtype == "number":
        raw = str(payload.get("value") or "").replace(",", ".")
        try:
            value = float(raw)
        except ValueError:
            return 0, False
        target = item.get("number_value")
        if target is None:
            return 0, False
        tolerance = float(item.get("number_tolerance") or 0)
        unit_ok = True
        if item.get("number_unit"):
            unit_ok = _norm(payload.get("unit")) == _norm(item.get("number_unit"))
        ok = abs(value - float(target)) <= tolerance + 1e-9 and unit_ok
        return (points if ok else 0), False
    if qtype == "match":
        expected = {_norm(left): _norm(right) for left, right in item.get("match_pairs") or []}
        given = {_norm(key): _norm(val) for key, val in (payload.get("pairs") or {}).items()}
        return (points if expected and given == expected else 0), False
    if qtype == "order":
        expected = [_norm(part) for part in item.get("order_items") or []]
        given = [_norm(part) for part in payload.get("order") or []]
        return (points if expected and given == expected else 0), False
    return 0, False


def rescore(attempt):
    by_id = {item["id"]: item for item in attempt.snapshot}
    total = 0
    manual_left = False
    for answer in attempt.answers.all():
        item = by_id.get(answer.question_id)
        if not item:
            continue
        if answer.needs_manual and not answer.graded:
            manual_left = True
            continue
        if answer.points_awarded is not None:
            total += float(answer.points_awarded)
    attempt.score = total
    attempt.max_score = sum(float(item.get("points") or 0) for item in attempt.snapshot)
    if attempt.status != "in_progress":
        attempt.status = "preliminary" if manual_left else "final"
    attempt.save(update_fields=["score", "max_score", "status"])
    return attempt
