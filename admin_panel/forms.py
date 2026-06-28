from django import forms


class AdminLoginForm(forms.Form):
    username = forms.CharField(
        label="Username or Email",
        widget=forms.TextInput(attrs={
            'placeholder': 'Admin username or email',
            'class': 'admin-form-input',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password',
            'class': 'admin-form-input',
        })
    )


class UserSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by name or email...',
            'class': 'admin-search-input',
            'autocomplete': 'off',
        })
    )