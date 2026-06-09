from django import forms
from .forms import StudentRegistrationForm, AdminStudentForm, WorkSessionForm
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count
from .models import *
from datetime import timedelta
import datetime
import threading
import time

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

@csrf_exempt
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

@login_required
def dashboard(request):
    # Проверяем наличие профиля студента
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        # Если профиля нет, отправляем на страницу создания профиля
        messages.warning(request, 'Для доступа к дашборду необходимо создать профиль студента.')
        
        # Если пользователь админ - показываем ссылку на создание в админке
        if request.user.is_staff:
            messages.info(request, 'Администратор: создайте профиль студента через админ-панель.')
            return redirect('/admin/app/student/add/')
        
        # Для обычных пользователей - показываем форму регистрации студента
        return redirect('student_registration')  # Используйте ваш URL для регистрации студента
    
    # Если профиль есть, показываем дашборд
    context = {
        'student': student,
        'student_name': student.full_name,
        'student_email': student.email,
        'student_group': student.group,
        'student_id': student.student_id,
    }
    
    return render(request, 'student/dashboard.html', context)

@login_required
def student_message_list(request):
    """Список сообщений для студента"""
    
    # Проверяем наличие профиля студента
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Профиль студента не найден. Пожалуйста, обратитесь к администратору.')
        
        # Если пользователь админ - перенаправляем в админку
        if request.user.is_staff:
            messages.info(request, 'Как администратор, вы можете создать профиль в админ-панели.')
            return redirect('/admin/app/student/add/')
        
        return redirect('home')
    
    # Получаем все сообщения студента
    messages_list = Message.objects.filter(student=student).order_by('-sent_at')
    
    # Отмечаем сообщения как прочитанные (опционально)
    if request.GET.get('mark_read'):
        unread_messages = messages_list.filter(is_read=False)
        unread_messages.update(is_read=True)
        messages.success(request, f'Отмечено {unread_messages.count()} сообщений как прочитанные')
        return redirect('student_messages')
    
    # Пагинация
    from django.core.paginator import Paginator
    paginator = Paginator(messages_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'student': student,
        'messages': page_obj,
        'page_obj': page_obj,
        'unread_count': messages_list.filter(is_read=False).count(),
    }
    return render(request, 'student/message_list.html', context)

@login_required
def start_work_session(request):
    """Начать рабочую сессию"""
    student = get_object_or_404(Student, user=request.user)
    
    # Проверяем, нет ли активной сессии
    active_session = student.get_active_session()
    if active_session:
        messages.warning(request, 'У вас уже есть активная рабочая сессия')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = WorkSessionForm(request.POST)
        if form.is_valid():
            # Создаем новую сессию
            session = WorkSession.objects.create(
                student=student,
                start_time=timezone.now(),
                computer_number=form.cleaned_data['computer_number'],
                is_active=True
            )
            
            # Запускаем таймер авто-выключения (8 часов)
            auto_stop_time = timezone.now() + timedelta(hours=8)
            # В реальном проекте здесь будет Celery task
            
            messages.success(request, f'Рабочая сессия начата в {session.start_time.strftime("%H:%M")}')
            return redirect('dashboard')
    else:
        form = WorkSessionForm()
    
    return render(request, 'students/student/start_session.html', {'form': form})

@login_required
def stop_work_session(request):
    """Завершить рабочую сессию"""
    student = get_object_or_404(Student, user=request.user)
    active_session = student.get_active_session()
    
    if not active_session:
        messages.error(request, 'Нет активной рабочей сессии')
        return redirect('dashboard')
    
    if request.method == 'POST':
        active_session.end_time = timezone.now()
        active_session.is_active = False
        active_session.save()
        
        duration_hours = active_session.duration_minutes / 60
        messages.success(request, 
            f'Сессия завершена. Время работы: {duration_hours:.2f} часов')
        return redirect('dashboard')
    
    return render(request, 'students/student/stop_session.html', {
        'session': active_session,
        'current_time': timezone.now()
    })

@login_required
def mark_all_read(request):
    """Отметить все сообщения студента как прочитанные"""
    
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Профиль студента не найден')
        return redirect('home')
    
    unread_count = Message.objects.filter(
        student=student,
        is_read=False
    ).update(is_read=True)
    
    if unread_count > 0:
        messages.success(request, f'Отмечено {unread_count} сообщений как прочитанные')
    else:
        messages.info(request, 'Нет непрочитанных сообщений')
    
    return redirect('student_messages')

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
        'current_time': datetime.datetime.now(),
    }
    return render(request, 'public/working_students.html', context)


def admin_required(view_func): #Декоратор для проверки прав администратора
    decorated_view_func = login_required(
        user_passes_test(
            lambda u: u.is_staff or hasattr(u, 'adminprofile'),
            login_url='/login/'
        )(view_func)
    )
    return decorated_view_func

@admin_required
def admin_dashboard(request):
    """Админ-панель"""
    
    context = {
        'total_students': Student.objects.count(),
        'working_now': WorkSession.objects.filter(is_active=True).count(),
        'unread_messages': Message.objects.filter(is_read=False).count(),
        'active_rules': Rule.objects.filter(is_active=True).count(),
        'recent_students': Student.objects.all().order_by('-id')[:5],
        'active_sessions': WorkSession.objects.filter(is_active=True).select_related('student')[:5],
    }
    
    return render(request, 'admin/admin_dashboard.html', context)

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
def admin_student(request, pk):
    """Детальный просмотр студента"""
    
    student = get_object_or_404(Student, id=pk)
    
    # Получаем сессии студента
    work_sessions = WorkSession.objects.filter(student=student).order_by('-start_time')[:10]
    
    # Получаем сообщения студента
    messages = Message.objects.filter(student=student).order_by('-sent_at')[:10]
    
    # Статистика
    total_minutes = sum(s.duration_minutes for s in work_sessions.filter(is_active=False))
    total_hours = total_minutes / 60
    
    context = {
        'student': student,
        'work_sessions': work_sessions,
        'messages': messages,
        'total_hours': round(total_hours, 1),
        'sessions_count': work_sessions.count(),
    }
    
    return render(request, 'admin/student_view.html', context)

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

@admin_required
def admin_student_create(request): 
    if request.method == 'POST':
        form = AdminStudentForm(request.POST, request.FILES)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['email'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'])
           
            student = form.save(commit=False)
            student.user = user
            student.save()

            messages.success(request, f'Студент {student.full_name} успешно')
            return redirect('admin_student_list')
    else:
        form = AdminStudentForm()
   
    return render(request, 'admin/student_form.html', {'form': form, 'action': 'create'})

@admin_required
def admin_student_edit(request, pk):
    """Редактирование студента администратором"""
    
    # Получаем студента или 404
    student = get_object_or_404(Student, id=pk)
    
    if request.method == 'POST':
        form = AdminStudentForm(request.POST, request.FILES, instance=student)
        
        if form.is_valid():
            # Обновляем данные пользователя
            user = student.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.username = form.cleaned_data['email']  # Обновляем username тоже
            
            # Если указан новый пароль
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)
            
            user.save()
            
            # Сохраняем студента
            student = form.save(commit=False)
            student.user = user
            student.full_name = f"{user.first_name} {user.last_name}"
            student.email = user.email
            student.save()
            
            messages.success(request, f'Студент "{student.full_name}" успешно обновлен!')
            return redirect('admin_student_list')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        # GET запрос - заполняем форму данными студента
        initial_data = {
            'first_name': student.user.first_name if student.user else '',
            'last_name': student.user.last_name if student.user else '',
            'email': student.email,
            'student_id': student.student_id,
            'phone': student.phone,
            'group': student.group,
            'redmine_id': student.redmine_id,
            'gitlab_id': student.gitlab_id,
        }
        form = AdminStudentForm(initial=initial_data, instance=student)
    
    context = {
        'form': form,
        'student': student,
        'action': 'edit',
        'page_title': f'Редактирование студента: {student.full_name}'
    }
    
    return render(request, 'admin/student_form.html', context)

@admin_required
def admin_student_delete(request, pk):
    """Удаление студента администратором"""
    
    student = get_object_or_404(Student, id=pk)
    student_name = student.full_name
    
    if request.method == 'POST':
        # Удаляем связанного пользователя
        user = student.user
        student.delete()
        
        if user:
            user.delete()
        
        messages.success(request, f'Студент "{student_name}" успешно удален!')
        return redirect('admin_student_list')
    
    context = {
        'student': student,
        'student_name': student_name,
    }
    
    return render(request, 'admin/student_confirm_delete.html', context)

@admin_required
def admin_rule_list(request):
    """Админ: управление правилами"""
    rules = Rule.objects.all()
    
    if request.method == 'POST':
        # Создание нового правила
        title = request.POST.get('title')
        content = request.POST.get('content')
        category = request.POST.get('category')
        
        if title and content:
            rule = Rule.objects.create(
                title=title,
                content=content,
                category=category,
                created_by=request.user
            )
            messages.success(request, 'Правило создано')
            return redirect('admin_rule_list')
    
    return render(request, 'admin/rule_list.html', {'rules': rules})

@admin_required
def admin_rule_create(request):
    """Создание нового правила"""
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        category = request.POST.get('category', '')
        is_active = request.POST.get('is_active') == 'on'
        
        if title and content:
            rule = Rule.objects.create(
                title=title,
                content=content,
                category=category,
                is_active=is_active,
                created_by=request.user
            )
            messages.success(request, f'Правило "{rule.title}" успешно создано!')
            return redirect('admin_rule_list')
        else:
            messages.error(request, 'Заполните все обязательные поля')
    
    return render(request, 'admin/rule_form.html', {'action': 'create'})

@admin_required
def admin_rule_edit(request, rule_id):
    """Админ: редактирование правила"""
    rule = get_object_or_404(Rule, id=rule_id)
    
    if request.method == 'POST':
        rule.title = request.POST.get('title')
        rule.content = request.POST.get('content')
        rule.category = request.POST.get('category')
        rule.version += 1  # Увеличиваем версию при редактировании
        rule.save()
        
        messages.success(request, 'Правило обновлено')
        return redirect('admin_rule_list')
    
    return render(request, 'admin/rule_edit.html', {'rule': rule})

@login_required
def view_rules(request):
    """Просмотр правил студентом"""
    
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Профиль студента не найден')
        return redirect('home')
    
    from .models import Rule
    rules = Rule.objects.filter(is_active=True).order_by('id')
    
    return render(request, 'student/student_rules.html', {
        'rules': rules,
        'student': student
    })


@login_required
def accept_rules(request, rule_id):
    """Принятие правил студентом"""
    
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Профиль студента не найден')
        return redirect('home')
    
    from .models import Rule, RuleAcceptance
    
    rule = get_object_or_404(Rule, id=rule_id)
    
    # Создаем запись о принятии
    acceptance, created = RuleAcceptance.objects.get_or_create(
        student=student,
        rule=rule,
        defaults={
            'accepted_at': timezone.now(),
            'ip_address': get_client_ip(request),
        }
    )
    
    if created:
        messages.success(request, f'Правило "{rule.title}" принято')
    else:
        messages.info(request, 'Вы уже приняли это правило')
    
    return redirect('view_rules')