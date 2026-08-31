from django.conf import settings
from django.db import models
from django.utils import timezone
from products.models import Product, Category


class Offer(models.Model):
    OFFER_TYPE_CHOICES = (
        ('product', 'Product Offer'),
        ('category', 'Category Offer'),
        ('referral', 'Referral Offer'),
    )

    name = models.CharField(max_length=100)
    offer_type = models.CharField(max_length=10, choices=OFFER_TYPE_CHOICES)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)

    # For product/category offers
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        null=True, blank=True, related_name='offers'
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE,
        null=True, blank=True, related_name='offers'
    )

    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.discount_percentage}%)"

    def is_valid(self):
        now = timezone.now()
        return self.is_active and self.valid_from <= now <= self.valid_until


class ReferralCode(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referral_code'
    )
    code = models.CharField(max_length=20, unique=True)
    reward_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=100
    )
    times_used = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} — {self.code}"


class ReferralUsage(models.Model):
    referral_code = models.ForeignKey(
        ReferralCode, on_delete=models.CASCADE, related_name='usages'
    )
    referred_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referral_usage'
    )
    reward_given = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.referred_user.email} referred by {self.referral_code.user.email}"