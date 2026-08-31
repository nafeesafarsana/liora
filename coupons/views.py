from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Coupon, CouponUsage


@login_required
@require_POST
def apply_coupon_view(request):
    """Apply coupon code at checkout. Stores in session."""
    code = request.POST.get('coupon_code', '').strip().upper()

    if not code:
        messages.error(request, "Please enter a coupon code.")
        return redirect('orders:checkout')

    try:
        coupon = Coupon.objects.get(code=code)
    except Coupon.DoesNotExist:
        messages.error(request, "Invalid coupon code.")
        return redirect('orders:checkout')

    # Check validity
    is_valid, reason = coupon.is_valid()
    if not is_valid:
        messages.error(request, reason)
        return redirect('orders:checkout')

    # Check if user already used this coupon
    if CouponUsage.objects.filter(coupon=coupon, user=request.user).exists():
        messages.error(request, "You have already used this coupon.")
        return redirect('orders:checkout')

    # Check minimum order amount
    try:
        cart = request.user.cart
        subtotal = cart.total_price
    except Exception:
        subtotal = Decimal('0')

    if subtotal < coupon.minimum_order_amount:
        messages.error(
            request,
            f"Minimum order amount for this coupon is ₹{coupon.minimum_order_amount}."
        )
        return redirect('orders:checkout')

    # Store in session
    request.session['coupon_id'] = coupon.pk
    discount = coupon.calculate_discount(subtotal)
    messages.success(
        request,
        f"Coupon '{coupon.code}' applied! You save ₹{discount:.2f}."
    )
    return redirect('orders:checkout')


@login_required
@require_POST
def remove_coupon_view(request):
    """Remove applied coupon from session."""
    if 'coupon_id' in request.session:
        del request.session['coupon_id']
        messages.success(request, "Coupon removed.")
    return redirect('orders:checkout')