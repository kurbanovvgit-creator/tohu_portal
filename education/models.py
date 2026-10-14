from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    IS_STUDENT = 'ST'
    IS_TEACHER = 'TH'
    ROLE_CHOICES = [
        (IS_STUDENT, 'Okuwçy'),
        (IS_TEACHER, 'Mugallym'),
    ]
    role = models.CharField(max_length=2, choices=ROLE_CHOICES, default=IS_STUDENT)
    score = models.IntegerField(default=0)  # Общий рейтинг студента
    points = models.IntegerField(default=0)

class Test(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'TH'})
    created_at = models.DateTimeField(auto_now_add=True)
    duration_minutes = models.PositiveIntegerField(default=15)
    shuffle_questions = models.BooleanField(default=False)
    shuffle_options = models.BooleanField(default=False)
    allow_retry = models.BooleanField(default=False)
    results_released = models.BooleanField(default=False)

    def __str__(self):
        return self.title or f"Synag #{self.pk}"

class Question(models.Model):
    TYPES = [
        ('choice', 'Saýlaw'),
        ('multi', 'Köp saýlaw'),
        ('short', 'Gysga jogap'),
        ('number', 'San'),
        ('match', 'Gabat getirmek'),
        ('order', 'Yzygiderlilik'),
        ('open', 'Açyk jogap'),
        ('practical', 'Amaly iş'),
    ]
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    qtype = models.CharField(max_length=16, choices=TYPES, default='choice')
    points = models.FloatField(default=1)
    hint = models.TextField(blank=True, default='')
    explanation = models.TextField(blank=True, default='')
    option_a = models.CharField(max_length=255, default="")
    option_b = models.CharField(max_length=255, default="")
    option_c = models.CharField(max_length=255, default="")
    option_d = models.CharField(max_length=255, default="")
    correct_answer = models.CharField(max_length=255, blank=True, default='')
    accepted_answers = models.TextField(blank=True, default='')
    number_value = models.FloatField(null=True, blank=True)
    number_unit = models.CharField(max_length=32, blank=True, default='')
    number_tolerance = models.FloatField(default=0)
    match_pairs = models.JSONField(default=list, blank=True)
    order_items = models.JSONField(default=list, blank=True)
    rubric = models.TextField(blank=True, default='')

    def __str__(self):
        text = (self.text or "").strip().replace("\n", " ")
        short = text[:60] + ("…" if len(text) > 60 else "")
        test_title = self.test.title if self.test_id else "?"
        return f"{test_title}: {short}" if short else f"Sorag #{self.pk}"

class TestResult(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    score = models.FloatField()
    ai_feedback = models.TextField(blank=True, null=True) # Здесь будет ответ Gemini
    date_passed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        who = self.student.username if self.student_id else "?"
        what = self.test.title if self.test_id else "?"
        return f"{who} · {what} · {self.score}%"

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.text[:20]}"

class PrivateMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"От {self.sender} к {self.recipient}: {self.text[:20]}"


class Course(models.Model):
    SUBJECTS = [
        ('math', 'Matematika'),
        ('physics', 'Fizika'),
        ('chemistry', 'Himiýa'),
        ('biology', 'Biologiýa'),
        ('informatics', 'Informatika'),
        ('other', 'Başga'),
    ]
    title = models.CharField(max_length=255)
    description = models.TextField()
    subject = models.CharField(max_length=20, choices=SUBJECTS, default='other')
    group_name = models.CharField(max_length=80, blank=True, default='')
    author = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'TH'})
    created_at = models.DateTimeField(auto_now_add=True)
    students = models.ManyToManyField(User, related_name='enrolled_courses', blank=True)
    def __str__(self):
        return self.title


class Lesson(models.Model):
    INTERACTIVES = [
        ('', 'Ýok'),
        ('math_graph', 'Funksiýa grafigi'),
        ('physics_circuit', 'Elektrik zynjyry'),
        ('chemistry_balance', 'Reaksiýany deňlemek'),
        ('biology_cell', 'Öýjük'),
        ('informatics_algo', 'Algoritm'),
    ]
    course = models.ForeignKey(Course, related_name='lessons', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    objective = models.TextField(blank=True, default='')
    content_text = models.TextField(blank=True)
    video_url = models.URLField(blank=True, null=True)
    video_file = models.FileField(upload_to='lessons/video/', blank=True, null=True)
    file = models.FileField(upload_to='lessons/', blank=True, null=True)
    interactive = models.CharField(max_length=32, choices=INTERACTIVES, blank=True, default='')
    test = models.OneToOneField('Test', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class LessonSession(models.Model):
    STATUS = [
        ('waiting', 'Garaşylýar'),
        ('live', 'Dowam edýär'),
        ('closed', 'Ýapyk'),
    ]
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='sessions')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    code = models.CharField(max_length=8, unique=True)
    status = models.CharField(max_length=16, choices=STATUS, default='live')
    join_open = models.BooleanField(default=True)
    screen_sharing = models.BooleanField(default=False)
    screen_updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} · {self.lesson.title}"


class SessionParticipant(models.Model):
    session = models.ForeignKey(LessonSession, on_delete=models.CASCADE, related_name='participants')
    display_name = models.CharField(max_length=80)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    last_seen = models.DateTimeField(auto_now=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('session', 'display_name')

    def __str__(self):
        code = self.session.code if self.session_id else "?"
        return f"{self.display_name} · {code}"


class TestAttempt(models.Model):
    STATUS = [
        ('in_progress', 'Dowam edýär'),
        ('submitted', 'Tabşyryldy'),
        ('preliminary', 'Deslapky'),
        ('final', 'Gutarnykly'),
    ]
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='attempts')
    session = models.ForeignKey(LessonSession, null=True, blank=True, on_delete=models.SET_NULL, related_name='attempts')
    participant = models.ForeignKey(SessionParticipant, null=True, blank=True, on_delete=models.SET_NULL)
    student = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    display_name = models.CharField(max_length=80, blank=True, default='')
    snapshot = models.JSONField(default=list)
    started_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField()
    submitted_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS, default='in_progress')
    score = models.FloatField(default=0)
    max_score = models.FloatField(default=0)

    @property
    def percent(self):
        if not self.max_score:
            return 0
        return round(self.score / self.max_score * 100, 1)

    @property
    def pending_manual(self):
        return self.answers.filter(needs_manual=True, graded=False).count()

    def __str__(self):
        who = self.display_name or (self.student.username if self.student_id else "?")
        what = self.test.title if self.test_id else "?"
        return f"{who} · {what} · {self.get_status_display()} · {self.score}/{self.max_score}"


class Answer(models.Model):
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='answers')
    question_id = models.PositiveIntegerField()
    payload = models.JSONField(default=dict, blank=True)
    file = models.FileField(upload_to='answers/', blank=True, null=True)
    status = models.CharField(max_length=16, default='saved')
    points_awarded = models.FloatField(null=True, blank=True)
    needs_manual = models.BooleanField(default=False)
    graded = models.BooleanField(default=False)
    teacher_comment = models.TextField(blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('attempt', 'question_id')

    def __str__(self):
        who = self.attempt.display_name if self.attempt_id else "?"
        return f"{who} · sorag #{self.question_id} · {self.status}"


class GradeChange(models.Model):
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='changes')
    teacher = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    old_points = models.FloatField(null=True, blank=True)
    new_points = models.FloatField(null=True, blank=True)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.old_points} → {self.new_points}: {self.reason[:40]}"