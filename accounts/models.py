import random
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class OTP(models.Model):
    """
    Stores OTP codes used for:
    - Signup email verification
    - Forgot password verification
    - Email change verification (used by profile_app too)
    """

    PURPOSE_CHOICES = (
        ('signup', 'Signup Verification'),
        ('forgot_password', 'Forgot Password'),
        ('email_change', 'Email Change'),
    )

    email = models.EmailField()
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} - {self.purpose} - {self.code}"

    @staticmethod
    def generate_code():
        """Generate a random 6 digit numeric OTP."""
        return str(random.randint(100000, 999999))

    @classmethod
    def create_otp(cls, email, purpose):
        """Invalidate old OTPs for this email/purpose and create a fresh one."""
        cls.objects.filter(email=email, purpose=purpose, is_used=False).update(is_used=True)
        code = cls.generate_code()
        otp = cls.objects.create(email=email, code=code, purpose=purpose)
        return otp

    @property
    def expires_at(self):
        return self.created_at + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_valid(self, code):
        """Check OTP correctness, expiry and usage state."""
        return (not self.is_used) and (not self.is_expired()) and (self.code == code)