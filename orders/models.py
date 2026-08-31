from django.db import models

# Create your models here.
import uuid
from django.conf import settings
from django.db import models
from products.models import Product


def generate_order_id():
    """
    Generates a unique readable order ID like LIORA-2024-ABC123.
    Consistent format shown to both user and admin.
    """
    unique = uuid.uuid4().hex[:8].upper()
    return f"LIORA-{unique}"


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    )

    order_id = models.CharField(
        max_length=20,
        unique=True,
        default=generate_order_id,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders'
    )

    # Snapshot of address at time of order
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    house_name = models.CharField(max_length=150)
    area = models.CharField(max_length=150)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    landmark = models.CharField(max_length=150, blank=True, null=True)

    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # Payment
    payment_method = models.CharField(max_length=20, default='cod')
    payment_status = models.CharField(max_length=20, default='pending')
    # Add to Order model fields:
    coupon = models.ForeignKey(
        'coupons.Coupon',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='orders'
    )
    coupon_discount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    offer_discount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    wallet_amount_used = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)        



    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # Cancellation
    cancellation_reason = models.TextField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)

    # Return
    return_reason = models.TextField(blank=True, null=True)
    returned_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_id} — {self.user.email if self.user else 'Deleted User'}"

    @property
    def item_count(self):
        return self.items.count()


class OrderItem(models.Model):
    """
    Snapshot of each product at time of order.
    Stores price at time of purchase — so if product price changes later,
    the order still shows what was actually paid.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items'
    )

    # Snapshot fields
    product_name = models.CharField(max_length=200)
    product_image = models.CharField(max_length=500, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    # Per-item status (for individual item cancellation)
    status = models.CharField(
        max_length=20,
        choices=Order.STATUS_CHOICES,
        default='pending'
    )
    cancellation_reason = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

    @property
    def subtotal(self):
        return self.price * self.quantity

