import io
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from cart.models import Cart, CartItem
from coupons.models import Coupon, CouponUsage
from offers.utils import calculate_offer_discount, get_best_offer_for_product
from products.models import Product
from profile_app.models import Address
from wallet.models import Wallet
from wallet.views import get_or_create_wallet

from .models import Order, OrderItem
from .utils import cancel_order, return_order


# ------------------------------------------------------------------
# CHECKOUT
# ------------------------------------------------------------------
@login_required
def checkout_view(request):
    try:
        cart = request.user.cart
        cart_items = cart.items.select_related('product').prefetch_related('product__images')
    except Exception:
        messages.error(request, "Your cart is empty.")
        return redirect('cart:cart_detail')

    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('cart:cart_detail')

    valid_items = []
    blocked_items = []

    for item in cart_items:
        if (item.product.is_deleted or
                not item.product.is_listed or
                not item.product.is_in_stock):
            blocked_items.append(item)
        elif item.quantity > item.product.stock:
            item.quantity = item.product.stock
            item.save()
            messages.warning(
                request,
                f"'{item.product.name}' quantity adjusted to {item.product.stock}."
            )
            valid_items.append(item)
        else:
            valid_items.append(item)

    if not valid_items:
        messages.error(request, "All items in your cart are unavailable.")
        return redirect('cart:cart_detail')

    if blocked_items:
        blocked_names = ", ".join([item.product.name for item in blocked_items])
        messages.warning(request, f"Unavailable items excluded: {blocked_names}")

    addresses = Address.objects.filter(
        user=request.user
    ).order_by('-is_default', '-created_at')
    default_address = addresses.filter(is_default=True).first() or addresses.first()

    # Calculate offer discounts per item
    item_offer_discounts = {}
    total_offer_discount = Decimal('0')
    for item in valid_items:
        offer_discount = calculate_offer_discount(
            item.product, item.product.effective_price
        ) * item.quantity
        item_offer_discounts[item.pk] = offer_discount
        total_offer_discount += offer_discount

    subtotal = sum(item.subtotal for item in valid_items)
    subtotal_after_offers = subtotal - total_offer_discount

    # Coupon
    coupon = None
    coupon_discount = Decimal('0')
    coupon_id = request.session.get('coupon_id')
    if coupon_id:
        try:
            coupon = Coupon.objects.get(pk=coupon_id)
            is_valid, reason = coupon.is_valid()
            if is_valid and subtotal_after_offers >= coupon.minimum_order_amount:
                if not CouponUsage.objects.filter(
                    coupon=coupon, user=request.user
                ).exists():
                    coupon_discount = coupon.calculate_discount(subtotal_after_offers)
            else:
                del request.session['coupon_id']
                coupon = None
        except Coupon.DoesNotExist:
            del request.session['coupon_id']
            coupon = None

    # Wallet
    try:
        wallet = get_or_create_wallet(request.user)
        wallet_balance = wallet.balance
    except Exception:
        wallet_balance = Decimal('0')

    subtotal_after_coupon = subtotal_after_offers - coupon_discount
    tax = Decimal('0.00')
    shipping = Decimal('0.00') if subtotal >= Decimal('500') else Decimal('50.00')
    total = subtotal_after_coupon + tax + shipping

    context = {
        'valid_items': valid_items,
        'blocked_items': blocked_items,
        'item_offer_discounts': item_offer_discounts,
        'addresses': addresses,
        'default_address': default_address,
        'subtotal': subtotal,
        'total_offer_discount': total_offer_discount,
        'subtotal_after_offers': subtotal_after_offers,
        'coupon': coupon,
        'coupon_discount': coupon_discount,
        'subtotal_after_coupon': subtotal_after_coupon,
        'tax': tax,
        'shipping': shipping,
        'total': total,
        'wallet_balance': wallet_balance,
    }
    return render(request, 'orders/checkout.html', context)


# ------------------------------------------------------------------
# PLACE ORDER
# ------------------------------------------------------------------
@login_required
@require_POST
def place_order_view(request):
    address_id = request.POST.get('address_id')
    payment_method = request.POST.get('payment_method', 'cod')
    use_wallet = request.POST.get('use_wallet') == 'on'

    if not address_id:
        messages.error(request, "Please select a delivery address.")
        return redirect('orders:checkout')

    address = get_object_or_404(Address, pk=address_id, user=request.user)

    try:
        cart = request.user.cart
        cart_items = cart.items.select_related('product').prefetch_related('product__images')
    except Exception:
        messages.error(request, "Your cart is empty.")
        return redirect('cart:cart_detail')

    valid_items = [
        item for item in cart_items
        if not item.product.is_deleted and item.product.is_listed
    ]

    if not valid_items:
        messages.error(request, "No valid items to place order.")
        return redirect('cart:cart_detail')

    # Final stock check
    for item in valid_items:
        if item.quantity > item.product.stock:
            messages.error(
                request,
                f"'{item.product.name}' only has {item.product.stock} units available."
            )
            return redirect('orders:checkout')

    # Calculate offer discounts
    total_offer_discount = Decimal('0')
    for item in valid_items:
        offer_discount = calculate_offer_discount(
            item.product, item.product.effective_price
        ) * item.quantity
        total_offer_discount += offer_discount

    subtotal = sum(item.subtotal for item in valid_items)
    subtotal_after_offers = subtotal - total_offer_discount

    # Coupon
    coupon = None
    coupon_discount = Decimal('0')
    coupon_id = request.session.get('coupon_id')
    if coupon_id:
        try:
            coupon = Coupon.objects.get(pk=coupon_id)
            is_valid, _ = coupon.is_valid()
            if is_valid and not CouponUsage.objects.filter(
                coupon=coupon, user=request.user
            ).exists():
                coupon_discount = coupon.calculate_discount(subtotal_after_offers)
        except Coupon.DoesNotExist:
            pass

    subtotal_after_coupon = subtotal_after_offers - coupon_discount
    tax = Decimal('0.00')
    shipping = Decimal('0.00') if subtotal >= Decimal('500') else Decimal('50.00')
    total = subtotal_after_coupon + tax + shipping

    # Wallet usage
    wallet_amount_used = Decimal('0')
    try:
        wallet = get_or_create_wallet(request.user)
        if use_wallet and wallet.balance > 0:
            wallet_amount_used = min(wallet.balance, total)
            total -= wallet_amount_used
    except Exception:
        wallet = None

    # Determine final payment method
    final_payment_method = payment_method
    if total <= 0:
        final_payment_method = 'wallet'

    # Create Order
    order = Order.objects.create(
        user=request.user,
        full_name=address.full_name,
        phone=address.phone,
        house_name=address.house_name,
        area=address.area,
        city=address.city,
        state=address.state,
        pincode=address.pincode,
        landmark=address.landmark or '',
        subtotal=subtotal,
        tax=tax,
        shipping_charge=shipping,
        offer_discount=total_offer_discount,
        coupon=coupon,
        coupon_discount=coupon_discount,
        wallet_amount_used=wallet_amount_used,
        total=max(total, Decimal('0')),
        payment_method=final_payment_method,
        payment_status='pending',
        status='pending',
    )

    # Record coupon usage
    if coupon:
        CouponUsage.objects.create(
            coupon=coupon, user=request.user, order=order
        )
        coupon.times_used += 1
        coupon.save(update_fields=['times_used'])
        if 'coupon_id' in request.session:
            del request.session['coupon_id']

    # Deduct from wallet
    if wallet_amount_used > 0 and wallet:
        try:
            wallet.debit(
                wallet_amount_used,
                description=f"Payment for order {order.order_id}"
            )
        except Exception:
            pass

    # Create OrderItems + decrement stock
    for item in valid_items:
        primary_img = item.product.primary_image
        img_path = str(primary_img.image) if primary_img else ''

        OrderItem.objects.create(
            order=order,
            product=item.product,
            product_name=item.product.name,
            product_image=img_path,
            price=item.product.effective_price,
            quantity=item.quantity,
            status='pending',
        )

        item.product.stock -= item.quantity
        item.product.save(update_fields=['stock'])

    # Clear cart
    cart.items.all().delete()

    # Razorpay redirect
    if final_payment_method == 'razorpay' and order.total > 0:
        return redirect('payments:initiate', order_id=order.order_id)

    return redirect('orders:order_success', order_id=order.order_id)


# ------------------------------------------------------------------
# ORDER SUCCESS
# ------------------------------------------------------------------
@login_required
def order_success_view(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, 'orders/order_success.html', {'order': order})


# ------------------------------------------------------------------
# ORDER LIST
# ------------------------------------------------------------------
@login_required
def order_list_view(request):
    query = request.GET.get('q', '').strip()
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    if query:
        orders = orders.filter(
            Q(order_id__icontains=query) | Q(status__icontains=query)
        )

    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'orders/order_list.html', {
        'page_obj': page_obj,
        'query': query,
    })


# ------------------------------------------------------------------
# ORDER DETAIL
# ------------------------------------------------------------------
@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    items = order.items.all()
    return render(request, 'orders/order_detail.html', {
        'order': order,
        'items': items,
    })


# ------------------------------------------------------------------
# CANCEL ORDER — with wallet refund fix
# ------------------------------------------------------------------
@login_required
@require_POST
def cancel_order_view(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    reason = request.POST.get('reason', '').strip()

    if order.status not in ['pending', 'shipped']:
        messages.error(request, "This order cannot be cancelled.")
        return redirect('orders:order_detail', order_id=order_id)

    # Cancel order and restore stock
    cancel_order(order, reason)

    # Calculate refund
    # Only refund if paid via Razorpay or wallet
    refund_amount = Decimal('0')

    if order.payment_status == 'paid':
        # Paid via Razorpay — refund order total to wallet
        refund_amount += order.total

    if order.wallet_amount_used and order.wallet_amount_used > 0:
        # Wallet portion was used — always refund this back
        refund_amount += order.wallet_amount_used

    if refund_amount > 0:
        try:
            wallet = get_or_create_wallet(request.user)
            wallet.credit(
                refund_amount,
                description=f"Refund for cancelled order {order.order_id}"
            )
            messages.success(
                request,
                f"Order cancelled. Rs.{refund_amount} refunded to your wallet."
            )
        except Exception:
            messages.success(request, f"Order {order.order_id} cancelled successfully.")
    else:
        # COD order — no refund needed
        messages.success(request, f"Order {order.order_id} cancelled successfully.")

    return redirect('orders:order_detail', order_id=order_id)


# ------------------------------------------------------------------
# CANCEL SINGLE ITEM
# ------------------------------------------------------------------
@login_required
@require_POST
def cancel_order_item_view(request, item_id):
    item = get_object_or_404(OrderItem, pk=item_id, order__user=request.user)
    reason = request.POST.get('reason', '').strip()

    if item.status != 'pending':
        messages.error(request, "This item cannot be cancelled.")
        return redirect('orders:order_detail', order_id=item.order.order_id)

    old_status = item.status
    item.status = 'cancelled'
    item.cancellation_reason = reason
    item.save()

    # Restore stock
    if item.product:
        item.product.stock += item.quantity
        item.product.save(update_fields=['stock'])

    # Proportional refund if order was paid
    if item.order.payment_status == 'paid':
        refund = item.subtotal
        try:
            wallet = get_or_create_wallet(request.user)
            wallet.credit(
                refund,
                description=f"Refund for cancelled item: {item.product_name}"
            )
            messages.success(
                request,
                f"'{item.product_name}' cancelled. Rs.{refund} refunded to wallet."
            )
        except Exception:
            messages.success(request, f"'{item.product_name}' cancelled.")
    else:
        messages.success(request, f"'{item.product_name}' cancelled.")

    return redirect('orders:order_detail', order_id=item.order.order_id)


# ------------------------------------------------------------------
# RETURN ORDER — fixed NameError
# ------------------------------------------------------------------
@login_required
@require_POST
def return_order_view(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    reason = request.POST.get('reason', '').strip()

    if not reason:
        messages.error(request, "Return reason is mandatory.")
        return redirect('orders:order_detail', order_id=order_id)

    if order.status != 'delivered':
        messages.error(request, "Only delivered orders can be returned.")
        return redirect('orders:order_detail', order_id=order_id)

    # return_order imported from .utils — fixes NameError
    return_order(order, reason)

    messages.success(
        request,
        "Return request submitted. Refund will be processed after admin approval."
    )
    return redirect('orders:order_detail', order_id=order_id)


# ------------------------------------------------------------------
# INVOICE PDF
# ------------------------------------------------------------------
@login_required
def download_invoice_view(request, order_id):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle,
        Paragraph, Spacer, HRFlowable
    )

    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    items = order.items.all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
    )

    styles = getSampleStyleSheet()
    story = []

    brand_style = ParagraphStyle(
        'Brand', fontName='Helvetica-Bold', fontSize=24,
        textColor=colors.HexColor('#4A1836'), spaceAfter=4,
    )
    story.append(Paragraph("LIORA", brand_style))

    tagline_style = ParagraphStyle(
        'Tagline', fontName='Helvetica', fontSize=9,
        textColor=colors.HexColor('#C8A96B'), spaceAfter=12,
    )
    story.append(Paragraph("Luxury Handbags — Invoice", tagline_style))
    story.append(HRFlowable(
        width="100%", thickness=1, color=colors.HexColor('#E8DCCB')
    ))
    story.append(Spacer(1, 10*mm))

    info_style = ParagraphStyle(
        'Info', fontName='Helvetica', fontSize=9,
        textColor=colors.HexColor('#2B2B2B'),
    )
    label_style = ParagraphStyle(
        'Label', fontName='Helvetica-Bold', fontSize=9,
        textColor=colors.HexColor('#4A1836'),
    )

    order_info = [
        [Paragraph("Order ID", label_style),
         Paragraph(order.order_id, info_style),
         Paragraph("Order Date", label_style),
         Paragraph(order.created_at.strftime("%d %b %Y"), info_style)],
        [Paragraph("Payment", label_style),
         Paragraph(order.payment_method.upper(), info_style),
         Paragraph("Status", label_style),
         Paragraph(order.get_status_display(), info_style)],
    ]
    info_table = Table(order_info, colWidths=[35*mm, 60*mm, 35*mm, 40*mm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FAF7F2')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E8DCCB')),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 8*mm))

    story.append(Paragraph("Delivery Address", label_style))
    story.append(Spacer(1, 3*mm))
    addr_text = (
        f"{order.full_name} | {order.phone}<br/>"
        f"{order.house_name}, {order.area}<br/>"
        f"{order.city}, {order.state} - {order.pincode}"
    )
    if order.landmark:
        addr_text += f"<br/>Landmark: {order.landmark}"
    story.append(Paragraph(addr_text, info_style))
    story.append(Spacer(1, 8*mm))

    story.append(Paragraph("Order Items", label_style))
    story.append(Spacer(1, 3*mm))

    item_header = [
        Paragraph("#", label_style),
        Paragraph("Product", label_style),
        Paragraph("Price", label_style),
        Paragraph("Qty", label_style),
        Paragraph("Subtotal", label_style),
    ]
    item_rows = [item_header]
    for i, item in enumerate(items, 1):
        item_rows.append([
            Paragraph(str(i), info_style),
            Paragraph(item.product_name, info_style),
            Paragraph(f"Rs.{item.price}", info_style),
            Paragraph(str(item.quantity), info_style),
            Paragraph(f"Rs.{item.subtotal}", info_style),
        ])

    items_table = Table(item_rows, colWidths=[12*mm, 80*mm, 28*mm, 15*mm, 30*mm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A1836')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E8DCCB')),
        ('PADDING', (0, 0), (-1, -1), 7),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 8*mm))

    summary_data = [
        [Paragraph("Subtotal", info_style),
         Paragraph(f"Rs.{order.subtotal}", info_style)],
    ]
    if order.offer_discount and order.offer_discount > 0:
        summary_data.append([
            Paragraph("Offer Discount", info_style),
            Paragraph(f"-Rs.{order.offer_discount}", info_style)
        ])
    if order.coupon_discount and order.coupon_discount > 0:
        coupon_label = (
            f"Coupon ({order.coupon.code})" if order.coupon else "Coupon"
        )
        summary_data.append([
            Paragraph(coupon_label, info_style),
            Paragraph(f"-Rs.{order.coupon_discount}", info_style)
        ])
    if order.wallet_amount_used and order.wallet_amount_used > 0:
        summary_data.append([
            Paragraph("Wallet Used", info_style),
            Paragraph(f"-Rs.{order.wallet_amount_used}", info_style)
        ])
    summary_data.append([
        Paragraph("Shipping", info_style),
        Paragraph(
            "FREE" if order.shipping_charge == 0
            else f"Rs.{order.shipping_charge}",
            info_style
        )
    ])
    summary_data.append([
        Paragraph("Total", label_style),
        Paragraph(f"Rs.{order.total}", ParagraphStyle(
            'Total', fontName='Helvetica-Bold', fontSize=11,
            textColor=colors.HexColor('#6D214F'),
        ))
    ])

    summary_table = Table(summary_data, colWidths=[130*mm, 35*mm])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#E8DCCB')),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10*mm))

    story.append(HRFlowable(
        width="100%", thickness=1, color=colors.HexColor('#E8DCCB')
    ))
    story.append(Spacer(1, 4*mm))
    footer_style = ParagraphStyle(
        'Footer', fontName='Helvetica', fontSize=8,
        textColor=colors.HexColor('#9b9b9b'), alignment=1,
    )
    story.append(Paragraph(
        "Thank you for shopping with LIORA | Luxury Handbags",
        footer_style
    ))

    doc.build(story)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="LIORA_Invoice_{order.order_id}.pdf"'
    )
    return response