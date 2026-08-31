import razorpay
import hmac
import hashlib

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from orders.models import Order


def get_client():
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


@login_required
def initiate_payment_view(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)

    if order.payment_status == 'paid':
        messages.info(request, "This order is already paid.")
        return redirect('orders:order_detail', order_id=order_id)

    client = get_client()
    amount_paise = int(order.total * 100)

    rz_order = client.order.create({
        'amount': amount_paise,
        'currency': 'INR',
        'receipt': order.order_id,
        'payment_capture': 1
    })

    order.razorpay_order_id = rz_order['id']
    order.save(update_fields=['razorpay_order_id'])

    return render(request, 'payments/payment_page.html', {
        'order': order,
        'razorpay_order_id': rz_order['id'],
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'amount_paise': amount_paise,
        'amount_inr': order.total,
        'user_name': f"{request.user.first_name} {request.user.last_name}",
        'user_email': request.user.email,
        # Callback URL — Razorpay will redirect here after payment
        'callback_url': request.build_absolute_uri('/payments/callback/'),
    })


@csrf_exempt
def payment_callback_view(request):
    """
    Razorpay redirects here after payment attempt.
    Works for ALL payment methods including Net Banking.
    This is the most reliable way to handle payments.
    """
    if request.method == 'POST':
        payment_id = request.POST.get('razorpay_payment_id', '')
        rz_order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')

        # If any of these are missing, payment failed
        if not payment_id or not rz_order_id or not signature:
            # Payment failed — find order and show failure
            # Try to find order from session or posted data
            order_id = request.POST.get('order_id', '')
            if order_id:
                return redirect('payments:failure', order_id=order_id)
            return redirect('orders:order_list')

        # Verify signature
        client = get_client()
        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': rz_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature,
            })
        except Exception:
            # Signature failed — find order and redirect to failure
            try:
                order = Order.objects.get(razorpay_order_id=rz_order_id)
                return redirect('payments:failure', order_id=order.order_id)
            except Order.DoesNotExist:
                return redirect('orders:order_list')

        # Payment verified — update order
        try:
            order = Order.objects.get(razorpay_order_id=rz_order_id)
        except Order.DoesNotExist:
            return redirect('orders:order_list')

        order.razorpay_payment_id = payment_id
        order.razorpay_signature = signature
        order.payment_status = 'paid'
        order.payment_method = 'razorpay'
        order.save(update_fields=[
            'razorpay_payment_id',
            'razorpay_signature',
            'payment_status',
            'payment_method',
        ])

        return render(request, 'payments/payment_success.html', {'order': order})

    # GET request — redirect
    return redirect('orders:order_list')


@csrf_exempt
@login_required
def payment_success_view(request):
    """Kept for backward compatibility with card payments."""
    if request.method == 'POST':
        payment_id = request.POST.get('razorpay_payment_id', '')
        rz_order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')

        if not payment_id or not rz_order_id or not signature:
            messages.error(request, "Payment data missing.")
            return redirect('orders:order_list')

        client = get_client()
        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': rz_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature,
            })
        except Exception:
            messages.error(request, "Payment verification failed.")
            return redirect('orders:order_list')

        try:
            order = Order.objects.get(razorpay_order_id=rz_order_id)
        except Order.DoesNotExist:
            return redirect('orders:order_list')

        order.razorpay_payment_id = payment_id
        order.razorpay_signature = signature
        order.payment_status = 'paid'
        order.payment_method = 'razorpay'
        order.save(update_fields=[
            'razorpay_payment_id',
            'razorpay_signature',
            'payment_status',
            'payment_method',
        ])

        return render(request, 'payments/payment_success.html', {'order': order})

    return redirect('orders:order_list')


@login_required
def payment_failure_view(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, 'payments/payment_failure.html', {'order': order})