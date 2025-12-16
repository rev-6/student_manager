from django import forms
from .forms import StudentRegistrationForm
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count
from app.models import *
import datetime

def main(request):
    try:
        total_students = Student.objects.count()
    except:
        total_students = 0
    try:
        working_now = Student.objects.filter(
            work_sessions__is_active=True
        ).distinct().count()
    except:
        working_now = 0
    try:
        week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        active_messages = Message.objects.filter(
            sent_at__gte=week_ago
        ).count()
    except:
        active_messages = 0
    try:
        recent_workers = Student.objects.filter(
            work_sessions__is_active=False
        ).annotate(
            last_session=models.Max('work_sessions__end_time')
        ).order_by('-last_session')[:6]
    except:
        recent_workers = []
    
    context = {
        'total_students': total_students,
        'working_now': working_now,
        'active_messages': active_messages,
        'recent_workers': recent_workers,
    }
    
    return render(request, 'Main.html', context)

def student_registration(request):
    if request.user.is_authenticated:
        messages.info(request, 'Вы уже авторизованы в системе.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                if User.objects.filter(email=form.cleaned_data['email']).exists():
                    messages.error(request, 'Пользователь с таким email уже существует.')
                    return render(request, 'register/registration.html', {'form': form})

                if Student.objects.filter(student_id=form.cleaned_data['student_id']).exists():
                    messages.error(request, 'Студент с таким номером студенческого уже зарегистрирован.')
                    return render(request, 'register/registration.html', {'form': form})
                
                user = User.objects.create_user(
                    username=form.cleaned_data['email'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name']
                )
                
                student = Student(
                    user=user,
                    student_id=form.cleaned_data['student_id'],
                    full_name=f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}",
                    email=form.cleaned_data['email'],
                    phone=form.cleaned_data['phone'],
                    group=form.cleaned_data['group'],
                )
                
                if 'photo' in request.FILES:
                    student.photo = request.FILES['photo']
                student.save()
                
                user = authenticate(
                    username=form.cleaned_data['email'],
                    password=form.cleaned_data['password']
                )
                
                if user is not None:
                    login(request, user)
                    messages.success(request, 'Регистрация прошла успешно!')
                    
                    # Перенаправляем на страницу с правилами
                    #return redirect('view_rules')
                else:
                    messages.error(request, 'Ошибка авторизации после регистрации.')
                    return redirect('login')
                    
            except Exception as e:
                messages.error(request, f'Ошибка при регистрации: {str(e)}')
                # Удаляем пользователя, если что-то пошло не так
                if 'user' in locals():
                    user.delete()
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = StudentRegistrationForm()
    context = {
        'form': form,
        'page_title': 'Регистрация студента'
    }
    return render(request, 'register/registration.html', context)

class CustomLoginView(LoginView):
    template_name = 'register/login.html'
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        messages.success(self.request, f'Добро пожаловать, {form.get_user().username}!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Неверное имя пользователя или пароль.')
        return super().form_invalid(form)
    
    def get_success_url(self):
        try:
            student = Student.objects.get(user=self.request.user)
            return '/dashboard/'
        except Student.DoesNotExist:
            # Проверяем, является ли пользователь администратором
            try:
                admin_profile = self.request.user.adminprofile
                return '/dashboard/'
            except:
                return '/'

def public_working_students(request):
    working_students = Student.objects.filter(
        work_sessions__is_active=True
    ).distinct().select_related('user')
    
    # Компьютерные станции с текущими студентами
    occupied_stations = ComputerStation.objects.filter(
        status2='occupied'
    ).select_related('current_student')
    
    # Статистика
    total_working = working_students.count()
    total_computers = ComputerStation.objects.count()
    available_computers = ComputerStation.objects.filter(status2='available').count()
    
    context = {
        'working_students': working_students,
        'occupied_stations': occupied_stations,
        'total_working': total_working,
        'total_computers': total_computers,
        'available_computers': available_computers,
        'current_time': timezone.now(),
    }
    return render(request, 'students/public/working_students.html', context)


def admin_required(view_func): #Декоратор для проверки прав администратора
    decorated_view_func = login_required(
        user_passes_test(
            lambda u: u.is_staff or hasattr(u, 'adminprofile'),
            login_url='/login/'
        )(view_func)
    )
    return decorated_view_func


@admin_required
def admin_student_list(request): #Список студентов с фильтрацией и поиском
    students = Student.objects.all()
    # Фильтрация по статусу
    status_filter = request.GET.get('status')
    if status_filter:
        students = students.filter(status=status_filter)

    # Фильтрация по группе
    group_filter = request.GET.get('group')
    if group_filter:
        students = students.filter(group=group_filter)

    # Поиск
    search_query = request.GET.get('q')
    if search_query:
        students = students.filter(
            Q(student_id__icontains=search_query) |
            Q(full_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query))

    # Сортировка
    sort_by = request.GET.get('sort', '-registration_date')
    students = students.order_by(sort_by)
    
    # Пагинация
    paginator = Paginator(students, 20)
    page = request.GET.get('page')
    students_page = paginator.get_page(page)
    
    # Статистика
    total_students = Student.objects.count()
    active_students = Student.objects.filter(status='active').count()
    working_now = Student.objects.filter(work_sessions__is_active=True).distinct().count()
    
    context = {
        'students': students_page,
        'total_students': total_students,
        'active_students': active_students,
        'working_now': working_now,
        'status_filter': status_filter,
        'group_filter': group_filter,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    return render(request, 'admin/student_list.html', context)


@admin_required
def admin_message_list(request):
    message_list = Message.objects.all().order_by('-sent_at', 'is_read')
    
    # Фильтр по типу
    type_filter = request.GET.get('type')
    if type_filter:
        message_list = message_list.filter(message_type=type_filter)
    
    # Фильтр по статусу прочтения
    read_filter = request.GET.get('read')
    if read_filter == 'unread':
        message_list = message_list.filter(is_read=False)
    elif read_filter == 'read':
        message_list = message_list.filter(is_read=True)
    
    # Поиск
    search_query = request.GET.get('q')
    if search_query:
        message_list = message_list.filter(
            Q(subject__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(student__full_name__icontains=search_query)
        )
    
    # Пагинация
    paginator = Paginator(message_list, 20)
    page = request.GET.get('page')
    messages_page = paginator.get_page(page)
    
    # Статистика
    unread_count = Message.objects.filter(is_read=False).count()
    
    context = {
        'messages': messages_page,
        'unread_count': unread_count,
        'type_filter': type_filter,
        'read_filter': read_filter,
        'search_query': search_query,
    }
    return render(request, 'admin/message_list.html', context)

#def admin_student_create(request): 
#    if request.method == 'POST':
#        form = AdminStudentForm(request.POST, request.FILES)
#        if form.is_valid():
#            user = User.objects.create_user(
#                username=form.cleaned_data['email'],
#                email=form.cleaned_data['email'],
#                password=form.cleaned_data['password'],
#                first_name=form.cleaned_data['first_name'],
#                last_name=form.cleaned_data['last_name'])
#           
#            student = form.save(commit=False)
#            student.user = user
#           student.save()
#           
#           messages.success(request, f'Студент {student.full_name} успешно')
#           return redirect('admin_student_list')
#   else:
#       form = AdminStudentForm()
#   
#   return render(request, 'admin/student_form.html', {'form': form, 'action': 'create'})