from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, SetPasswordForm
from django.contrib.auth.models import User


class CustomUserCreationForm(UserCreationForm):

    class Meta:
        model = User
        fields = ('first_name', 'username', 'password1', 'password2', 'is_superuser', 'is_staff')

    def save(self, commit=True):
        user = super(CustomUserCreationForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name'].upper()
        user.username = self.cleaned_data['username'].lower()
        if commit:
            user.save()
        return user

class UpdatePasswordForm(PasswordChangeForm):
    pass


class SetPasswordForm(SetPasswordForm):
    class Meta:
        model = User
        fields = ['new_password1', 'new_password2']
