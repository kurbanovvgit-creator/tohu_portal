from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Answer, Course, GradeChange, Lesson, LessonSession, Question,
    SessionParticipant, Test, TestAttempt, TestResult, User,
)


class MyUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Goşmaça', {'fields': ('role', 'score', 'points')}),
    )
    list_display = ['username', 'email', 'role', 'points', 'is_staff']
    list_filter = ['role', 'is_staff']


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'duration_minutes', 'results_released', 'created_at']
    search_fields = ['title', 'author__username']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['short_text', 'test', 'qtype', 'points']
    list_filter = ['qtype']
    search_fields = ['text', 'test__title']

    @admin.display(description='Sorag')
    def short_text(self, obj):
        text = (obj.text or '').replace('\n', ' ')
        return text[:70] + ('…' if len(text) > 70 else '')


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'test', 'score', 'date_passed']
    search_fields = ['student__username', 'test__title']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'group_name', 'author', 'created_at']
    list_filter = ['subject']
    search_fields = ['title', 'group_name']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'interactive', 'test']
    search_fields = ['title', 'course__title']


@admin.register(LessonSession)
class LessonSessionAdmin(admin.ModelAdmin):
    list_display = ['code', 'lesson', 'teacher', 'status', 'join_open', 'created_at']
    search_fields = ['code', 'lesson__title', 'teacher__username']
    list_filter = ['status', 'join_open']


@admin.register(SessionParticipant)
class SessionParticipantAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'session', 'user', 'joined_at', 'last_seen']
    search_fields = ['display_name', 'session__code']


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'test', 'status', 'score', 'max_score', 'started_at', 'submitted_at']
    list_filter = ['status']
    search_fields = ['display_name', 'test__title']


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question_id', 'status', 'points_awarded', 'needs_manual', 'graded']
    list_filter = ['status', 'needs_manual', 'graded']


@admin.register(GradeChange)
class GradeChangeAdmin(admin.ModelAdmin):
    list_display = ['answer', 'teacher', 'old_points', 'new_points', 'reason', 'created_at']


admin.site.register(User, MyUserAdmin)
