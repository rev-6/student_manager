from django.db import models
from django.contrib.auth.models import User

class Student(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активный'),
        ('inactive', 'Неактивный'),
        ('graduated', 'Выпустился'),
        ('expelled', 'Отчислен'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Связь с Django User
    student_id = models.CharField(max_length=20, unique=True)  # Номер студенческого
    full_name = models.CharField(max_length=200)
    photo = models.ImageField(upload_to='app/photos/', null=True, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    group = models.CharField(max_length=50)  # Группа/курс
    redmine_id = models.CharField(max_length=100, blank=True)  # ID в Redmine
    gitlab_id = models.CharField(max_length=100, blank=True)  # ID в GitLab
    github_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    registration_date = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name} ({self.student_id})"

class WorkSession(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='work_sessions')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=0)  # В минутах
    computer_number = models.CharField(max_length=10, blank=True)  # Номер ПК
    is_active = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.student} - {self.start_time}"

class Message(models.Model):
    MESSAGE_TYPES = [
        ('question', 'Вопрос'),
        ('problem', 'Проблема'),
        ('suggestion', 'Предложение'),
        ('other', 'Другое'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='messages')
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='question')
    subject = models.CharField(max_length=200)
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    response = models.TextField(blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.subject} - {self.student}"

class AdminProfile(models.Model):
    ROLE_CHOICES = [
        ('superadmin', 'Супер-админ'),
        ('admin', 'Администратор'),
        ('moderator', 'Модератор'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='admin')
    phone = models.CharField(max_length=20, blank=True)
    can_manage_students = models.BooleanField(default=False)
    can_manage_admins = models.BooleanField(default=False)
    can_view_reports = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.role})"

class ComputerStation(models.Model):
    STATUS_CHOICES2 = [
        ('available', 'Свободен'),
        ('occupied', 'Занят'),
        ('maintenance', 'На обслуживании'),
    ]
    
    room_number = models.CharField(max_length=10, unique=True)
    room = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    status2 = models.CharField(max_length=20, choices=STATUS_CHOICES2, default='available')
    current_student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Комната {self.room_number} ({self.room})"