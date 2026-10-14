from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone

from education.grading import score_payload
from education.models import Course, Lesson, LessonSession, Test, TestAttempt


class GradingTests(TestCase):
    def test_types(self):
        choice = {"qtype": "choice", "points": 1, "correct_answer": "Ýokary"}
        self.assertEqual(score_payload(choice, {"value": "Ýokary"})[0], 1)
        number = {"qtype": "number", "points": 2, "number_value": 3, "number_unit": "A", "number_tolerance": 0.05}
        self.assertEqual(score_payload(number, {"value": "3.01", "unit": "A"})[0], 2)
        self.assertEqual(score_payload(number, {"value": "9", "unit": "A"})[0], 0)
        opened = {"qtype": "open", "points": 2}
        points, manual = score_payload(opened, {"value": "..."})
        self.assertTrue(manual)
        self.assertIsNone(points)


class SessionFlowTests(TestCase):
    def test_join_and_save(self):
        User = get_user_model()
        teacher = User.objects.create_user(username="t1", password="pass12345", role="TH")
        test = Test.objects.create(title="Synag", author=teacher, duration_minutes=10, allow_retry=True)
        course = Course.objects.create(title="Fizika", description="d", subject="physics", group_name="8", author=teacher)
        lesson = Lesson.objects.create(course=course, title="Om", objective="Ölçeg", content_text="I = U / R", interactive="physics_circuit", test=test)
        from education.models import Question
        Question.objects.create(test=test, text="Tok?", qtype="number", points=1, number_value=3, number_unit="A", number_tolerance=0)
        session = LessonSession.objects.create(lesson=lesson, teacher=teacher, code="AB12CD")
        client = Client()
        page = client.get("/sapak/AB12CD/")
        self.assertEqual(page.status_code, 200)
        joined = client.post("/sapak/AB12CD/", {"name": "Aýna"})
        self.assertEqual(joined.status_code, 302)
        start = client.get("/sapak/AB12CD/synag/")
        self.assertEqual(start.status_code, 302)
        attempt = TestAttempt.objects.get()
        self.assertGreater(attempt.deadline, timezone.now())
        saved = client.post(
            f"/synag/{attempt.id}/sakla/",
            data='{"question_id": %d, "payload": {"value": "3", "unit": "A"}}' % test.questions.first().id,
            content_type="application/json",
        )
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.json()["status"], "saved")
        done = client.post(f"/synag/{attempt.id}/tabshyr/")
        self.assertEqual(done.status_code, 302)
        attempt.refresh_from_db()
        self.assertEqual(attempt.score, 1)
        hidden = client.get(f"/synag/{attempt.id}/netije/")
        self.assertContains(hidden, "garaşylýar")
        client.force_login(teacher)
        results = client.get("/sapak/AB12CD/netije/")
        self.assertEqual(results.status_code, 200)
        self.assertContains(results, "Aýna")
