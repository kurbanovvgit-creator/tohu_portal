import json
import re
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q
from .models import User, PrivateMessage  # Не забудь импортировать!
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Test, Question, TestResult, User, ChatMessage, Course, Lesson
from .ai_utils import get_ai_explanation, generate_questions_ai
from .ai_utils import model# Импортируем готовые функции
from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import CourseSerializer

@login_required
def lesson_detail(request, lesson_id):
    # Ищем урок по ID, если не находим — выдаем 404
    lesson = get_object_or_404(Lesson, id=lesson_id)
    return render(request, 'education/lesson_detail.html', {
        'lesson': lesson
    })

@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    course.students.add(request.user)
    return redirect('course_detail', course_id=course.id)

@api_view(['GET'])
def api_courses(request):
    courses = Course.objects.all()
    serializer = CourseSerializer(courses, many=True)
    return Response(serializer.data)
@login_required()
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    lessons = course.lessons.select_related('test').all()
    return render(request, 'education/course_detail.html', {
        'course': course,
        'lessons': lessons
    })

@login_required
def ai_assistant_chat(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')

            if not user_message:
                return JsonResponse({'error': 'Empty message'}, status=400)

            # Формируем промпт, чтобы он не писал мемуары
            prompt = f"Ты помощник на образовательном портале. Отвечай кратко, по делу и на русском языке. Вопрос: {user_message}"

            response = model.generate_content(prompt)

            # Возвращаем текст ответа
            return JsonResponse({'reply': response.text})

        except Exception as e:
            print(f"Ошибка чата: {e}")
            return JsonResponse({'error': 'Ошибка нейронки'}, status=500)

    return JsonResponse({'error': 'Метод не разрешен'}, status=405)


def home(request):
    query = request.GET.get('search')
    if query:
        # Ищем курсы, где в названии или описании есть введенный текст
        courses = Course.objects.filter(title__icontains=query) | Course.objects.filter(description__icontains=query)
    else:
        courses = Course.objects.all()

    sessions = []
    if request.user.is_authenticated and request.user.role == 'TH':
        from .models import LessonSession
        sessions = LessonSession.objects.filter(teacher=request.user).select_related('lesson').order_by('-created_at')[:6]
    return render(request, 'education/home.html', {
        'courses': courses,
        'search_query': query,
        'live_sessions': sessions,
    })


@login_required
def take_test(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    questions = test.questions.all()

    if request.method == "POST":
        score = 0
        mistakes = []

        # Считаем баллы и собираем ошибки
        for q in questions:
            user_ans = request.POST.get(f'q_{q.id}', '').strip().lower()
            correct_ans = q.correct_answer.strip().lower()
            if user_ans == correct_ans:
                score += 1
            else:
                mistakes.append(f"Вопрос: {q.text}, Правильный ответ: {q.correct_answer}")

        total_q = questions.count()
        # Считаем процент, так как в шаблоне {{ result.score }}%
        percent = int((score / total_q * 100)) if total_q > 0 else 0
        ai_advice = None

        # Сохраняем результат в базу (используем student!)
        new_result = TestResult.objects.create(
            student=request.user,
            test=test,
            score=percent,
            ai_feedback=ai_advice
        )

        # Начисляем поинты в профиль (только студентам)
        if request.user.role == 'ST':
            request.user.points += score
            request.user.save()

        # ВНИМАНИЕ: рендерим именно result.html и передаем 'result'
        return render(request, 'education/result.html', {
            'result': new_result,
        })

    return render(request, 'education/test_detail.html', {'test': test})

@login_required
def generate_test_view(request):
    # Проверка роли (Учитель - TH)
    if request.user.role != 'TH':
        return redirect('home')

    if request.method == "POST":
        topic = request.POST.get('topic')

        # Вызываем функцию генерации из ai_utils
        raw_response = generate_questions_ai(topic)

        if not raw_response:
            return render(request, 'education/error.html', {'error': "AI не вернул ответ. Проверьте соединение."})

        try:
            # Очищаем JSON от лишних знаков (бывает, что AI пишет ```json ... ```)
            clean_json = re.sub(r'```json|```', '', raw_response).strip()
            questions_data = json.loads(clean_json)

            # Создаем сам тест
            new_test = Test.objects.create(
                title=f"Тест по теме: {topic}",
                author=request.user
            )

            # Сохраняем вопросы из JSON в базу данных
            for item in questions_data:
                Question.objects.create(
                    test=new_test,
                    text=item['question'],
                    correct_answer=item['answer']
                )

            return redirect('home')
        except Exception as e:
            print(f"Ошибка при парсинге JSON: {e}")
            return render(request, 'education/error.html', {'error': f"Ошибка обработки данных: {e}"})

    return render(request, 'education/generate_form.html')


@login_required
def profile_view(request):
    # Твои результаты тестов (уже есть)
    results = TestResult.objects.filter(student=request.user).order_by('-date_passed')

    # Твои курсы (добавляем это)
    # related_name='enrolled_courses' должен быть прописан в модели Course в ManyToManyField
    my_courses = request.user.enrolled_courses.all()

    return render(request, 'education/profile.html', {
        'results': results,
        'my_courses': my_courses
    })


@login_required
@login_required
def leaderboard(request):
    # Просто берем студентов и сортируем по очкам
    users = User.objects.filter(role='ST').order_by('-points')
    return render(request, 'education/leaderboard.html', {'users': users})

    print(f"DEBUG: Найдено пользователей для лидерборда: {top_students.count()}")
    for student in top_students:
        print(f"DEBUG: Юзер: {student.username}, Очки: {student.score}")

    return render(request, 'education/leaderboard.html', {'students': top_students})


@login_required
def create_test_manual(request):
    if request.user.role != 'TH' and not request.user.is_staff:
        return redirect('home')

    # Mugallymlar ähli sapaklara synag baglap biler (hakaton / umumy baza)
    lessons = Lesson.objects.select_related('course', 'test').order_by('course__title', 'title')
    my_tests = Test.objects.filter(author=request.user).order_by('-created_at')[:12]

    def page(**extra):
        ctx = {'lessons': lessons, 'my_tests': my_tests}
        ctx.update(extra)
        return render(request, 'education/create_manual.html', ctx)

    if request.method == "POST":
        title = (request.POST.get('title') or '').strip()
        lesson_id = (request.POST.get('lesson_id') or '').strip()
        new_course_title = (request.POST.get('new_course_title') or '').strip()
        new_lesson_title = (request.POST.get('new_lesson_title') or '').strip()
        questions = request.POST.getlist('questions[]')
        answers = request.POST.getlist('answers[]')
        qtypes = request.POST.getlist('qtypes[]')
        points_list = request.POST.getlist('points[]')

        lesson = lessons.filter(id=lesson_id).first() if lesson_id else None
        if not lesson and new_course_title and new_lesson_title:
            course = Course.objects.create(
                title=new_course_title,
                description=new_course_title,
                subject='other',
                author=request.user,
            )
            lesson = Lesson.objects.create(
                course=course,
                title=new_lesson_title,
                content_text='',
            )

        pairs = []
        for idx, q_text in enumerate(questions):
            text = (q_text or '').strip()
            if not text:
                continue
            answer = (answers[idx] if idx < len(answers) else '') or ''
            qtype = (qtypes[idx] if idx < len(qtypes) else 'short') or 'short'
            try:
                points = float(points_list[idx]) if idx < len(points_list) and points_list[idx] else 1
            except ValueError:
                points = 1
            pairs.append((text, answer.strip(), qtype, points))

        if not title:
            return page(error='Synagyň adyny ýazyň.')
        if not pairs:
            return page(error='Azyndan bir sorag goşuň.')
        if not lesson:
            return page(error='Sapak saýlaň ýa-da täze sapak adyny ýazyň.')

        try:
            duration = max(1, min(int(request.POST.get('duration_minutes') or 15), 180))
        except ValueError:
            duration = 15

        old_test = lesson.test
        new_test = Test.objects.create(
            title=title,
            author=request.user,
            duration_minutes=duration,
            allow_retry=True,
        )
        for text, answer, qtype, points in pairs:
            qtype = qtype if qtype in dict(Question.TYPES) else 'short'
            data = {
                'test': new_test,
                'text': text,
                'qtype': qtype,
                'points': points,
                'correct_answer': answer,
                'accepted_answers': answer,
            }
            if qtype == 'choice' and '|' in answer:
                opts = [part.strip() for part in answer.split('|') if part.strip()]
                while len(opts) < 4:
                    opts.append('')
                data['option_a'] = opts[0]
                data['option_b'] = opts[1]
                data['option_c'] = opts[2]
                data['option_d'] = opts[3]
                data['correct_answer'] = opts[0]
            if qtype == 'number':
                try:
                    data['number_value'] = float(answer.replace(',', '.'))
                except ValueError:
                    pass
            Question.objects.create(**data)

        lesson.test = new_test
        lesson.save(update_fields=['test'])
        if old_test and old_test.id != new_test.id and not Lesson.objects.filter(test=old_test).exists():
            old_test.delete()

        messages.success(request, f'Synag saklandy: «{new_test.title}» → {lesson.title}')
        return redirect('lesson_detail', lesson_id=lesson.id)

    return page()


@login_required
def chat_view(request):
    if request.method == "POST":
        text = request.POST.get('text')
        if text:
            ChatMessage.objects.create(user=request.user, text=text)
            return redirect('chat')  # Перезагружаем, чтобы очистить форму

    messages = ChatMessage.objects.all().order_by('-created_at')[:50]
    return render(request, 'education/chat.html', {'chat_messages': messages})


@login_required
def dialogs_list(request):
    # Получаем всех пользователей, кроме самого себя, чтобы выбрать кому написать
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'education/dialogs.html', {'users': users})


@login_required
def private_chat(request, user_id):
    recipient = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        text = request.POST.get('text')
        if text:
            PrivateMessage.objects.create(sender=request.user, recipient=recipient, text=text)
            return redirect('private_chat', user_id=user_id)

    # Получаем историю переписки именно между этими двумя пользователями
    messages = PrivateMessage.objects.filter(
        Q(sender=request.user, recipient=recipient) |
        Q(sender=recipient, recipient=request.user)
    ).order_by('created_at')

    return render(request, 'education/private_chat.html', {
        'recipient': recipient,
        'chat_messages': messages
    })
