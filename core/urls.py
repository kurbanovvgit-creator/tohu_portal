from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from education import live, views
from django.contrib.auth import views as auth_views
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    # Регистрация и логин
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Остальные пути
    path('test/<int:test_id>/', views.take_test, name='take_test'),
    path('generate/', views.generate_test_view, name='generate_test'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('profile/', views.profile_view, name='profile'),
    path('test/create/manual/', views.create_test_manual, name='create_test_manual'),
    path('chat/', views.chat_view, name='chat'),
    path('messages/', views.dialogs_list, name='dialogs'),
    path('messages/<int:user_id>/', views.private_chat, name='private_chat'),
    path('ai-assistant/', views.ai_assistant_chat, name='ai_assistant'),
    path('course/<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('lesson/<int:lesson_id>/start/', live.start_session, name='start_session'),
    path('gir/', live.join_by_code, name='sapak_enter'),
    path('sapak/<str:code>/', live.session_board, name='session_board'),
    path('sapak/<str:code>/join-toggle/', live.toggle_join, name='toggle_join'),
    path('sapak/<str:code>/heartbeat/', live.heartbeat, name='heartbeat'),
    path('sapak/<str:code>/synag/', live.begin_attempt, name='begin_attempt'),
    path('sapak/<str:code>/netije/', live.class_results, name='class_results'),
    path('sapak/<str:code>/netije/ac/', live.release_results, name='release_results'),
    path('sapak/<str:code>/netije/eksport/', live.export_results, name='export_results'),
    path('sapak/<str:code>/wagt/', live.extra_time, name='extra_time'),
    path('sapak/<str:code>/ekran/', live.screen_toggle, name='screen_toggle'),
    path('sapak/<str:code>/ekran/kadr/', live.screen_frame, name='screen_frame'),
    path('sapak/<str:code>/ekran/surat/', live.screen_image, name='screen_image'),
    path('synag/<int:attempt_id>/', live.attempt_page, name='attempt_page'),
    path('synag/<int:attempt_id>/sakla/', live.save_answer, name='save_answer'),
    path('synag/<int:attempt_id>/fayl/', live.upload_practical, name='upload_practical'),
    path('synag/<int:attempt_id>/tabshyr/', live.submit_attempt, name='submit_attempt'),
    path('synag/<int:attempt_id>/yagday/', live.attempt_state, name='attempt_state'),
    path('synag/<int:attempt_id>/netije/', live.attempt_result, name='attempt_result'),
    path('synag/<int:attempt_id>/barla/', live.review_attempt, name='review_attempt'),
    path('synag/<int:attempt_id>/çap/', live.print_attempt, name='print_attempt'),
    path('atiyac/', live.download_backup, name='download_backup'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
