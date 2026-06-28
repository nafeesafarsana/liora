from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_otp_email(email, code, purpose='signup'):
    """
    Sends a styled OTP email via Gmail SMTP.
    purpose: 'signup' | 'forgot_password' | 'email_change'
    """
    subject_map = {
        'signup': 'Verify your LIORA account',
        'forgot_password': 'Reset your LIORA password',
        'email_change': 'Confirm your new email address',
    }
    subject = subject_map.get(purpose, 'Your LIORA verification code')

    html_message = render_to_string('accounts/email_otp_template.html', {
        'code': code,
        'subject': subject,
    })
    plain_message = strip_tags(html_message)

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )