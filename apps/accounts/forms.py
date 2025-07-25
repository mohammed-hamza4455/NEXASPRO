"""
Authentication forms for NEXAS application.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordResetForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML, Field
from crispy_forms.bootstrap import FormActions

from .models import User, UserProfile


class CustomLoginForm(AuthenticationForm):
    """
    Custom login form with enhanced styling and validation.
    """
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@domain.com',
            'id': 'emailInput',
            'required': True,
            'aria-label': 'Email address'
        }),
        label=_('Email address')
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'id': 'passwordInput',
            'required': True,
            'aria-label': 'Password'
        }),
        label=_('Password')
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label=_('Remember me')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'loginForm'
        self.helper.layout = Layout(
            Div(
                Field('username', css_class='mb-4'),
                css_class='mb-4'
            ),
            Div(
                Field('password', css_class='mb-4'),
                css_class='mb-4 password-field'
            ),
            Div(
                Field('remember_me'),
                css_class='mb-4'
            ),
            FormActions(
                Submit('submit', _('Log In'), css_class='btn login-btn w-100')
            )
        )

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            # Check if user exists and is active
            try:
                user = User.objects.get(email=username)
                if not user.is_active:
                    raise ValidationError(_('This account has been deactivated.'))
                
                # Check if account is locked
                if user.account_locked_until:
                    from django.utils import timezone
                    if timezone.now() < user.account_locked_until:
                        raise ValidationError(_('Account is temporarily locked. Please try again later.'))
                
            except User.DoesNotExist:
                raise ValidationError(_('Invalid email or password.'))

            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )
            
            if self.user_cache is None:
                # Increment failed login attempts
                try:
                    user = User.objects.get(email=username)
                    user.failed_login_attempts += 1
                    
                    # Lock account after 5 failed attempts
                    if user.failed_login_attempts >= 5:
                        from django.utils import timezone
                        from datetime import timedelta
                        user.account_locked_until = timezone.now() + timedelta(minutes=30)
                    
                    user.save()
                except User.DoesNotExist:
                    pass
                
                raise ValidationError(_('Invalid email or password.'))
            else:
                # Reset failed login attempts on successful login
                self.user_cache.failed_login_attempts = 0
                self.user_cache.account_locked_until = None
                self.user_cache.save()

        return self.cleaned_data


class CustomUserCreationForm(UserCreationForm):
    """
    Custom user creation form for admin to create users.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@domain.com'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    
    role = forms.ChoiceField(
        choices=User.UserRole.choices,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    phone_number = forms.CharField(
        max_length=17,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+1234567890'
        })
    )
    
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Department/Organization'
        })
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'role', 'phone_number', 'department', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(
                Div('email', css_class='col-md-6'),
                Div('role', css_class='col-md-6'),
                css_class='row'
            ),
            Div(
                Div('first_name', css_class='col-md-6'),
                Div('last_name', css_class='col-md-6'),
                css_class='row'
            ),
            Div(
                Div('phone_number', css_class='col-md-6'),
                Div('department', css_class='col-md-6'),
                css_class='row'
            ),
            Div(
                Div('password1', css_class='col-md-6'),
                Div('password2', css_class='col-md-6'),
                css_class='row'
            ),
            FormActions(
                Submit('submit', _('Create User'), css_class='btn btn-primary')
            )
        )

    def clean_email(self):
        """Validate email uniqueness."""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError(_('A user with this email already exists.'))
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.role = self.cleaned_data['role']
        user.phone_number = self.cleaned_data['phone_number']
        user.department = self.cleaned_data['department']
        
        if commit:
            try:
                user.save()
                # Create user profile
                UserProfile.objects.get_or_create(user=user)
            except Exception as e:
                raise ValidationError(_('Failed to create user. Please try again.'))
        
        return user


class CustomPasswordResetForm(PasswordResetForm):
    """
    Custom password reset form with enhanced styling.
    """
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@domain.com',
            'autocomplete': 'email'
        }),
        label=_('Email address')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('email', css_class='mb-4'),
            FormActions(
                Submit('submit', _('Send Reset Link'), css_class='btn btn-primary w-100')
            )
        )


class UserProfileForm(forms.ModelForm):
    """
    Form for updating user profile information.
    """
    
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'location', 'website', 'linkedin_profile',
            'email_notifications', 'sms_notifications',
            'skills', 'interests', 'availability'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell us about yourself...'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City, State or Country'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://yourwebsite.com'
            }),
            'linkedin_profile': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/in/yourprofile'
            }),
            'skills': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'e.g., Project Management, Web Development, Marketing'
            }),
            'interests': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'What areas are you interested in helping with?'
            }),
            'availability': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Weekends, Evenings, Full-time'
            }),
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'sms_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(
                HTML('<h5 class="mb-3">Basic Information</h5>'),
                'bio',
                Div(
                    Div('location', css_class='col-md-6'),
                    Div('website', css_class='col-md-6'),
                    css_class='row'
                ),
                'linkedin_profile',
                css_class='mb-4'
            ),
            Div(
                HTML('<h5 class="mb-3">Volunteer Information</h5>'),
                'skills',
                'interests',
                'availability',
                css_class='mb-4'
            ),
            Div(
                HTML('<h5 class="mb-3">Notification Preferences</h5>'),
                Div(
                    Field('email_notifications', wrapper_class='form-check'),
                    css_class='mb-2'
                ),
                Div(
                    Field('sms_notifications', wrapper_class='form-check'),
                    css_class='mb-3'
                ),
                css_class='mb-4'
            ),
            FormActions(
                Submit('submit', _('Update Profile'), css_class='btn btn-primary')
            )
        )


class UserUpdateForm(forms.ModelForm):
    """
    Form for updating basic user information.
    """
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'department']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1234567890'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(
                Div('first_name', css_class='col-md-6'),
                Div('last_name', css_class='col-md-6'),
                css_class='row'
            ),
            Div(
                Div('phone_number', css_class='col-md-6'),
                Div('department', css_class='col-md-6'),
                css_class='row'
            ),
            FormActions(
                Submit('submit', _('Update Information'), css_class='btn btn-primary')
            )
        )
