from django.contrib import admin
from django.urls import path
from app.views import main, mark_all_read, admin_student, admin_rule_create, start_work_session, stop_work_session, admin_dashboard, admin_student_delete, admin_student_edit, admin_student_create, admin_rule_list, admin_rule_edit, view_rules, accept_rules, student_message_list, dashboard, admin_student_list, admin_message_list, student_registration, public_working_students
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', main, name='home' ),
    path('register/', student_registration, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='register/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('public/', public_working_students, name='public_working'),

    path('admins/admin_dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admins/students/', admin_student_list, name='admin_student_list'),
    path('admins/students/<int:pk>/view/', admin_student, name='admin_student_view'),
    path('admins/messages/', admin_message_list, name='admin_message_list'),
    path('admins/rules/', admin_rule_list, name='admin_rule_list'),
    path('admins/rules/create/', admin_rule_create, name='rule_create'),
    path('admins/rules/<int:rule_id>/edit/', admin_rule_edit, name='admin_rule_edit'),
    path('admins/students/create/', admin_student_create, name='admin_student_create'),
    path('admins/students/<int:pk>/edit/', admin_student_edit, name='admin_student_edit'),
    path('admins/students/<int:pk>/delete/', admin_student_delete, name='admin_student_delete'),

    # Для студента 
    path('dashboard/', dashboard, name='dashboard'),
    path('messages/', student_message_list, name='student_messages'),
    path('messages/mark-all-read/', mark_all_read, name='mark_all_read'),
    path('rules/', view_rules, name='view_rules'),
    path('accept-rules/', accept_rules, name='accept_rules'),
    path('start-session/', start_work_session, name='start_session'),
    path('stop-session/', stop_work_session, name='stop_session'),
]
