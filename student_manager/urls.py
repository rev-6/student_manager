from django.contrib import admin
from django.urls import path
from app.views import main, admin_student_list, student_registration
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', main, name='home' ),
    path('register/', student_registration, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='register/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    path('admin/students/', admin_student_list, name='admin_student_list'),
]
