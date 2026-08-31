from django.conf import settings
from django.db import models
from django.utils import timezone


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ('percentage', 'Percentage'),
        ('flat', 'Flat Amount'),
    )

    code = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=200, blank=True)
    discount_type = models.CharField(
        max_length=10,
        choices=DISCOUNT_TYPE_CHOICES,
        default='percentage'
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    maximum_discount = models.DecimalField(
        max_digits=10, decimal_places=2,
        blank=True, null=True,
        help_text="Max discount cap for percentage coupons"
    )
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(
        default=0,
        help_text="0 means unlimited"
    )
    times_used = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False, "This coupon is inactive."
        if now < self.valid_from:
            return False, "This coupon is not yet active."
        if now > self.valid_until:
            return False, "This coupon has expired."
        if self.usage_limit > 0 and self.times_used >= self.usage_limit:
            return False, "This coupon has reached its usage limit."
        return True, "Valid"

    def calculate_discount(self, subtotal):
        if self.discount_type == 'percentage':
            discount = (subtotal * self.discount_value) / 100
            if self.maximum_discount:
                discount = min(discount, self.maximum_discount)
        else:
            discount = self.discount_value
        return min(discount, subtotal)


class CouponUsage(models.Model):
    coupon = models.ForeignKey(
        Coupon, on_delete=models.CASCADE, related_name='usages'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coupon_usages'
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='coupon_usages',
        null=True, blank=True
    )
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('coupon', 'user')

    def __str__(self):
        return f"{self.user.email} used {self.coupon.code}"