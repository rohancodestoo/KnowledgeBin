from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Note

class StyledFormMixin:
    """Mixin to apply Tailwind styles to form fields"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'flex h-10 w-full rounded-md border border-stone-300 bg-transparent px-3 py-2 text-sm placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-green-600 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50'

class SignUpForm(StyledFormMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email']

class LoginForm(StyledFormMixin, AuthenticationForm):
    """
    AuthenticationForm already has fields 'username' and 'password'.
    We just apply the styles via the mixin.
    """
    pass

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'content', 'image_url']