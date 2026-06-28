from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone

from .forms import (
    SignupForm, OTPForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
)
from .models import OTP
from .utils import send_otp_email


# ------------------------------------------------------------------
# SIGNUP
# ------------------------------------------------------------------
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home:home')

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # Stash pending signup data in session until OTP is verified
            request.session['pending_signup'] = {
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'email': data['email'],
                'password': data['password'],
            }
            otp = OTP.create_otp(email=data['email'], purpose='signup')
            send_otp_email(data['email'], otp.code, purpose='signup')
            messages.success(request, f"A verification code has been sent to {data['email']}.")
            return redirect('accounts:signup_otp')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SignupForm()

    return render(request, 'accounts/signup.html', {'form': form})


def signup_otp_view(request):
    pending = request.session.get('pending_signup')
    if not pending:
        messages.error(request, "Your signup session has expired. Please sign up again.")
        return redirect('accounts:signup')

    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            code = form.get_otp_code()
            otp_qs = OTP.objects.filter(
                email=pending['email'], purpose='signup', is_used=False
            ).order_by('-created_at').first()

            if otp_qs and otp_qs.is_valid(code):
                otp_qs.is_used = True
                otp_qs.save()

                user = User.objects.create_user(
                    username=pending['email'],
                    email=pending['email'],
                    password=pending['password'],
                    first_name=pending['first_name'],
                    last_name=pending['last_name'],
                )
                del request.session['pending_signup']
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f"Welcome to LIORA, {user.first_name}! Your account is verified.")
                return redirect('home:home')
            elif otp_qs and otp_qs.is_expired():
                messages.error(request, "This code has expired. Please request a new one.")
            else:
                messages.error(request, "Invalid verification code. Please try again.")
        else:
            messages.error(request, "Please enter the complete 6-digit code.")
    else:
        form = OTPForm()

    return render(request, 'accounts/signup_otp.html', {
        'form': form,
        'email': pending['email'],
    })


def resend_signup_otp_view(request):
    pending = request.session.get('pending_signup')
    if not pending:
        messages.error(request, "Your signup session has expired. Please sign up again.")
        return redirect('accounts:signup')

    otp = OTP.create_otp(email=pending['email'], purpose='signup')
    send_otp_email(pending['email'], otp.code, purpose='signup')
    messages.success(request, "A new verification code has been sent.")
    return redirect('accounts:signup_otp')


# ------------------------------------------------------------------
# LOGIN / LOGOUT
# ------------------------------------------------------------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home:home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower().strip()
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me')

            try:
                user_obj = User.objects.get(email=email)
                username = user_obj.username
            except User.DoesNotExist:
                username = None

            user = authenticate(request, username=username, password=password) if username else None

            if user is not None:
                login(request, user)
                if remember_me:
                    request.session.set_expiry(60 * 60 * 24 * 14)  # 14 days
                else:
                    request.session.set_expiry(0)  # expires on browser close
                messages.success(request, f"Welcome back, {user.first_name}!")
                return redirect('home:home')
            else:
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home:home')


# ------------------------------------------------------------------
# FORGOT PASSWORD
# ------------------------------------------------------------------
def forgot_password_view(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            otp = OTP.create_otp(email=email, purpose='forgot_password')
            send_otp_email(email, otp.code, purpose='forgot_password')
            request.session['reset_email'] = email
            messages.success(request, f"A verification code has been sent to {email}.")
            return redirect('accounts:forgot_otp')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ForgotPasswordForm()

    return render(request, 'accounts/forgot_password.html', {'form': form})


def forgot_otp_view(request):
    email = request.session.get('reset_email')
    if not email:
        messages.error(request, "Your session has expired. Please try again.")
        return redirect('accounts:forgot_password')

    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            code = form.get_otp_code()
            otp_qs = OTP.objects.filter(
                email=email, purpose='forgot_password', is_used=False
            ).order_by('-created_at').first()

            if otp_qs and otp_qs.is_valid(code):
                otp_qs.is_used = True
                otp_qs.save()
                request.session['otp_verified_for_reset'] = True
                return redirect('accounts:reset_password')
            elif otp_qs and otp_qs.is_expired():
                messages.error(request, "This code has expired. Please request a new one.")
            else:
                messages.error(request, "Invalid verification code. Please try again.")
        else:
            messages.error(request, "Please enter the complete 6-digit code.")
    else:
        form = OTPForm()

    return render(request, 'accounts/forgot_otp.html', {'form': form, 'email': email})


def resend_forgot_otp_view(request):
    email = request.session.get('reset_email')
    if not email:
        messages.error(request, "Your session has expired. Please try again.")
        return redirect('accounts:forgot_password')

    otp = OTP.create_otp(email=email, purpose='forgot_password')
    send_otp_email(email, otp.code, purpose='forgot_password')
    messages.success(request, "A new verification code has been sent.")
    return redirect('accounts:forgot_otp')


def reset_password_view(request):
    email = request.session.get('reset_email')
    verified = request.session.get('otp_verified_for_reset')

    if not email or not verified:
        messages.error(request, "Please verify your identity before resetting your password.")
        return redirect('accounts:forgot_password')

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.get(email=email)
                user.set_password(form.cleaned_data['new_password'])
                user.save()

                del request.session['reset_email']
                del request.session['otp_verified_for_reset']

                messages.success(request, "Your password has been reset successfully. Please log in.")
                return redirect('accounts:login')
            except User.DoesNotExist:
                messages.error(request, "Something went wrong. Please try again.")
                return redirect('accounts:forgot_password')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ResetPasswordForm()

    return render(request, 'accounts/reset_password.html', {'form': form})