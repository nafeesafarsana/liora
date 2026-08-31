import re

from django import forms
from django.contrib.auth.models import User

from .models import Address, Profile


class EditProfileForm(forms.Form):
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'placeholder': 'First Name', 'class': 'form-input'})
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'placeholder': 'Last Name', 'class': 'form-input'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Email Address', 'class': 'form-input'})
    )

    def __init__(self, *args, current_user=None, **kwargs):
        self.current_user = current_user
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        qs = User.objects.filter(email=email)
        if self.current_user:
            qs = qs.exclude(pk=self.current_user.pk)
        if qs.exists():
            raise forms.ValidationError("This email is already in use by another account.")
        return email


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Current Password', 'class': 'form-input'})
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'New Password', 'class': 'form-input', 'id': 'newPassword'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm New Password', 'class': 'form-input'})
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        password = self.cleaned_data.get('current_password')
        if self.user and not self.user.check_password(password):
            raise forms.ValidationError("Current password is incorrect.")
        return password

    def clean_new_password(self):
        password = self.cleaned_data.get('new_password', '')
        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[0-9]', password):
            raise forms.ValidationError("Password must contain at least one number.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            'full_name', 'phone', 'house_name', 'area',
            'city', 'state', 'pincode', 'landmark', 'is_default'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Full Name', 'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Phone Number', 'class': 'form-input'}),
            'house_name': forms.TextInput(attrs={'placeholder': 'House / Flat Name', 'class': 'form-input'}),
            'area': forms.TextInput(attrs={'placeholder': 'Area / Street', 'class': 'form-input'}),
            'city': forms.TextInput(attrs={'placeholder': 'City', 'class': 'form-input'}),
            'state': forms.Select(attrs={'class': 'form-input'}),
            'pincode': forms.TextInput(attrs={'placeholder': 'Pincode', 'class': 'form-input'}),
            'landmark': forms.TextInput(attrs={'placeholder': 'Landmark (optional)', 'class': 'form-input'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        if not re.match(r'^[0-9]{10}$', phone):
            raise forms.ValidationError("Enter a valid 10-digit phone number.")
        return phone

    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode', '')
        if not re.match(r'^[0-9]{6}$', pincode):
            raise forms.ValidationError("Enter a valid 6-digit pincode.")
        return pincode
class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'profile-pic-input', 'accept': 'image/*'}),
        }        