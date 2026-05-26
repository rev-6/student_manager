from django.contrib import admin
from django.urls import path
from app.views import main, start_work_session, stop_work_session, admin_student_delete, admin_student_edit, admin_student_create, admin_rule_list, admin_rule_edit, view_rules, accept_rules, student_message_list, dashboard, admin_student_list, admin_message_list, student_registration, public_working_students
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', main, name='home' ),
    path('register/', student_registration, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='register/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('public/', public_working_students, name='public_working'),

    path('admin/students/', admin_student_list, name='admin_student_list'),
    path('admin/messages/', admin_message_list, name='admin_message_list'),
    path('admin/rules/', admin_rule_list, name='admin_rule_list'),
    path('admin/rules/<int:rule_id>/edit/', admin_rule_edit, name='admin_rule_edit'),
    path('admin/students/create/', admin_student_create, name='admin_student_create'),
    path('admin/students/', admin_student_list, name='admin_student_list'),
    path('admin/students/<int:pk>/edit/', admin_student_edit, name='admin_student_edit'),
    path('admin/students/<int:pk>/delete/', admin_student_delete, name='admin_student_delete'),

    # Для студента 
    path('dashboard/', dashboard, name='dashboard'),
    path('messages/', student_message_list, name='student_messages'),
    path('rules/', view_rules, name='view_rules'),
    path('accept-rules/', accept_rules, name='accept_rules'),
    path('start-session/', start_work_session, name='start_session'),
    path('stop-session/', stop_work_session, name='stop_session'),
]
