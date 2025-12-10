from django import forms
from django.core.validators import RegexValidator
import re

#class AdminStudentForm(forms.ModelForm):
#   first_name = forms.CharField(max_length=100, label='Имя')
#   last_name = forms.CharField(max_length=100, label='Фамилия')
#   email = forms.EmailField(label='Email')
#   password = forms.CharField(
#       widget=forms.PasswordInput, 
#       label='Пароль',
#       required=False,
#       help_text='Оставьте пустым, если не нужно менять пароль'
#   )
#   
#   class Meta:
#       model = Student
#       fields = [
#           'student_id', 'first_name', 'last_name', 'email', 
#           'phone', 'group', 'photo', 'redmine_id', 'gitlab_id', 
#           'github_id', 'status'
#       ]
#       widgets = {
#           'phone': forms.TextInput(attrs={'placeholder': '+7 (XXX) XXX-XX-XX'}),
#           'group': forms.TextInput(attrs={'placeholder': 'ПИ-101'}),
#       }
    
#    def __init__(self, *args, **kwargs):
#        super().__init__(*args, **kwargs)
#        if self.instance and self.instance.pk:
#            self.fields['password'].required = False
#    
#    def save(self, commit=True):
#        student = super().save(commit=False)
#        
#        if 'password' in self.cleaned_data and self.cleaned_data['password']:
#            student.user.set_password(self.cleaned_data['password'])
#        
#       if commit:
#            student.save()
#        return student


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