from django.contrib import admin
from django.urls import path
from app.views import main, view_rules, accept_rules, student_message_list, dashboard, admin_student_list, admin_message_list, student_registration, public_working_students
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

    # Для студента 
    path('dashboard/', dashboard, name='dashboard'),
    path('messages/', student_message_list, name='student_messages'),
    path('rules/', view_rules, name='view_rules'),
    path('accept-rules/', accept_rules, name='accept_rules'),
]
