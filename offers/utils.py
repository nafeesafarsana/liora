from decimal import Decimal
from django.utils import timezone
from .models import Offer


def get_best_offer_for_product(product):
    """
    Returns the best applicable offer for a product.
    Compares product-specific offer vs category offer.
    Returns the one with the highest discount percentage.
    """
    now = timezone.now()
    best_offer = None
    best_discount = Decimal('0')

    # Product-specific offer
    product_offer = Offer.objects.filter(
        offer_type='product',
        product=product,
        is_active=True,
        valid_from__lte=now,
        valid_until__gte=now
    ).order_by('-discount_percentage').first()

    if product_offer:
        best_offer = product_offer
        best_discount = product_offer.discount_percentage

    # Category offer
    if product.category:
        category_offer = Offer.objects.filter(
            offer_type='category',
            category=product.category,
            is_active=True,
            valid_from__lte=now,
            valid_until__gte=now
        ).order_by('-discount_percentage').first()

        if category_offer and category_offer.discount_percentage > best_discount:
            best_offer = category_offer
            best_discount = category_offer.discount_percentage

    return best_offer


def calculate_offer_discount(product, price):
    """Returns discount amount for a product based on best offer."""
    offer = get_best_offer_for_product(product)
    if offer:
        return round((price * offer.discount_percentage) / 100, 2)
    return Decimal('0')