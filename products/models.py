from django.db import models
from django.utils.text import slugify
from PIL import Image
import os
from django.conf import settings

class Category(models.Model):
    """
    Represents a product category (e.g. Totes, Clutches, Crossbody).
    Soft delete means we never actually delete from database —
    we just set is_deleted=True so order history stays intact.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_listed = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def restore(self):
        self.is_deleted = False
        self.save()


class Product(models.Model):
    """
    Represents a LIORA handbag product.
    Linked to Category. Has multiple images via ProductImage.
    Soft delete same as Category.
    """
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        blank=True, null=True
    )
    stock = models.PositiveIntegerField(default=0)
    brand = models.CharField(max_length=100, blank=True, null=True)
    is_listed = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def restore(self):
        self.is_deleted = False
        self.save()

    @property
    def effective_price(self):
        """Returns discount price if available, else regular price."""
        return self.discount_price if self.discount_price else self.price

    @property
    def discount_percentage(self):
        """Returns discount % if discount price exists."""
        if self.discount_price and self.price:
            discount = ((self.price - self.discount_price) / self.price) * 100
            return round(discount)
        return 0

    @property
    def is_in_stock(self):
        return self.stock > 0

    @property
    def primary_image(self):
        """Returns the primary image, or first image if no primary set."""
        primary = self.images.filter(is_primary=True).first()
        if primary:
            return primary
        return self.images.first()


class ProductImage(models.Model):
    """
    Stores multiple images per product.
    Minimum 3 images required (enforced in the form, not the model).
    Images are resized to 800x800 by Pillow after upload (server-side).
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='product_images/')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_primary', 'created_at']

    def __str__(self):
        return f"Image for {self.product.name}"

    def save(self, *args, **kwargs):
        """
        Override save to resize image to 800x800 using Pillow.
        This runs AFTER Cropper.js has already cropped it in the browser.
        Two-step: browser crops → server resizes to exact dimensions.
        """
        super().save(*args, **kwargs)
        if self.image:
            img_path = self.image.path
            img = Image.open(img_path)

            # Convert to RGB (in case PNG with transparency)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Resize to exactly 800x800
            img = img.resize((800, 800), Image.LANCZOS)
            img.save(img_path, 'JPEG', quality=90)
class Review(models.Model):
    """
    Product review submitted by a logged-in user.
    One review per user per product.
    """
    RATING_CHOICES = (
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} → {self.product.name} ({self.rating}★)"        
class ProductColor(models.Model):
    """
    Stores available colors for a product.
    Each color has its own stock count.
    Same product — different color options.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='colors'
    )
    name = models.CharField(max_length=50)       # e.g. "Red", "Forest Green"
    hex_code = models.CharField(max_length=7)    # e.g. "#FF0000"
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.product.name} — {self.name}"        