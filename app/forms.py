from django import forms
from django.core.validators import RegexValidator
import re
from django.utils import timezone
from .models import Student, WorkSession

class AdminStudentForm(forms.ModelForm):
    """Форма для создания/редактирования студента администратором"""
    
    # Дополнительные поля для пользователя
    first_name = forms.CharField(max_length=100, label='Имя', widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, label='Фамилия', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='Оставьте пустым, чтобы не менять пароль'
    )
    password_confirm = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    
    class Meta:
        model = Student
        fields = ['student_id', 'email', 'phone', 'group', 'photo', 'redmine_id', 'gitlab_id']
        widgets = {
            'student_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ST-001'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'student@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (123) 456-78-90'}),
            'group': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ПИ-301'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'redmine_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Redmine ID'}),
            'gitlab_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'GitLab Username'}),
        }
        labels = {
            'student_id': 'Номер студенческого',
            'email': 'Email',
            'phone': 'Телефон',
            'group': 'Группа',
            'photo': 'Фотография',
            'redmine_id': 'Redmine ID',
            'gitlab_id': 'GitLab ID',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Если редактируем, делаем student_id только для чтения
        if self.instance and self.instance.pk:
            self.fields['student_id'].widget.attrs['readonly'] = True
            self.fields['student_id'].help_text = 'Номер студенческого нельзя изменить'
            self.fields['email'].widget.attrs['readonly'] = True
            self.fields['email'].help_text = 'Email нельзя изменить (создайте нового студента для смены email)'
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password != password_confirm:
            raise forms.ValidationError('Пароли не совпадают')
        
        if password and len(password) < 6:
            raise forms.ValidationError('Пароль должен содержать минимум 6 символов')
        
        return cleaned_data
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            instance = getattr(self, 'instance', None)
            if instance and instance.user and instance.user.email == email:
                return email
            raise forms.ValidationError('Пользователь с таким email уже существует')
        return email
    
    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id')
        if Student.objects.filter(student_id=student_id).exists():
            instance = getattr(self, 'instance', None)
            if instance and instance.student_id == student_id:
                return student_id
            raise forms.ValidationError('Студент с таким номером уже существует')
        return student_id

class StudentRegistrationForm(forms.Form):
    student_id = forms.CharField(
        max_length=20,
        label='Номер студенческого билета *',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: 123456'
        }),
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z0-9\-_]+$',
                message='Номер может содержать только буквы, цифры, дефисы и подчеркивания'
            )
        ]
    )
    
    first_name = forms.CharField(
        max_length=100,
        label='Имя *',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Иван'
        })
    )
    
    last_name = forms.CharField(
        max_length=100,
        label='Фамилия *',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Иванов'
        })
    )
    
    email = forms.EmailField(
        label='Email *',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ivan@example.com'
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        label='Телефон',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (999) 123-45-67'
        }),
        validators=[
            RegexValidator(
                regex=r'^\+?[0-9\s\-\(\)]+$',
                message='Введите корректный номер телефона'
            )
        ]
    )
    
    group = forms.CharField(
        max_length=50,
        label='Группа/Курс *',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ПИ-101 или 3 курс'
        })
    )
    
    password = forms.CharField(
        label='Пароль *',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Минимум 8 символов'
        }),
        min_length=8
    )
    
    password_confirm = forms.CharField(
        label='Подтверждение пароля *',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите пароль'
        })
    )
    
    photo = forms.ImageField(
        label='Фотография',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    
    def clean(self):
        """Дополнительная валидация формы"""
        cleaned_data = super().clean()
        
        # Проверка совпадения паролей
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'Пароли не совпадают')
        
        
        return cleaned_data
    
    def clean_phone(self):
        """Очистка номера телефона"""
        phone = self.cleaned_data.get('phone', '')
        # Удаляем все нецифровые символы, кроме +
        phone = re.sub(r'[^\d+]', '', phone)
        return phone

class WorkSessionForm(forms.ModelForm):
    """Форма для учета рабочего времени"""
    
    class Meta:
        model = WorkSession
        fields = ['student', 'start_time', 'end_time', 'duration_minutes', 'computer_number', 'is_active']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': 'Длительность в минутах'
            }),
            'computer_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: PC-01, COMP-5'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'student': 'Студент',
            'start_time': 'Время начала',
            'end_time': 'Время окончания',
            'duration_minutes': 'Длительность (минуты)',
            'computer_number': 'Номер ПК',
            'is_active': 'Активна',
        }
        help_texts = {
            'duration_minutes': 'Длительность рабочей сессии в минутах',
            'computer_number': 'Укажите номер компьютера, за которым работает студент',
            'is_active': 'Отметьте, если сессия активна в данный момент',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Если это редактирование и сессия активна, делаем end_time необязательным
        if self.instance and self.instance.pk and self.instance.is_active:
            self.fields['end_time'].required = False
            self.fields['duration_minutes'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        is_active = cleaned_data.get('is_active')
        duration_minutes = cleaned_data.get('duration_minutes')
        
        # Проверка: время начала не может быть позже времени окончания
        if start_time and end_time and start_time > end_time:
            raise forms.ValidationError('Время начала не может быть позже времени окончания')
        
        # Проверка: время начала не может быть в будущем
        if start_time and start_time > timezone.now():
            raise forms.ValidationError('Время начала не может быть в будущем')
        
        # Проверка: если сессия не активна, должно быть время окончания
        if not is_active and not end_time:
            raise forms.ValidationError('Для завершенной сессии укажите время окончания')
        
        # Проверка: если сессия активна, время окончания должно быть пустым
        if is_active and end_time:
            raise forms.ValidationError('Для активной сессии время окончания должно быть пустым')
        
        # Проверка: длительность должна быть положительной
        if duration_minutes and duration_minutes < 0:
            raise forms.ValidationError('Длительность не может быть отрицательной')
        
        # Автоматический расчет длительности, если указаны start_time и end_time
        if start_time and end_time and not duration_minutes:
            delta = end_time - start_time
            cleaned_data['duration_minutes'] = int(delta.total_seconds() / 60)
        
        return cleaned_data