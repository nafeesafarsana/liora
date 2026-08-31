from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from products.models import Product
from .models import Cart, CartItem, Wishlist, MAX_QUANTITY_PER_ITEM


def get_or_create_cart(user):
    cart, created = Cart.objects.get_or_create(user=user)
    return cart


# ------------------------------------------------------------------
# CART
# ------------------------------------------------------------------
@login_required
@require_POST
def add_to_cart_view(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    # Block if product unavailable
    if product.is_deleted or not product.is_listed:
        messages.error(request, "This product is no longer available.")
        return redirect('products:product_list')

    if not product.is_in_stock:
        messages.error(request, "Sorry, this product is out of stock.")
        return redirect('products:product_detail', pk=product_id)

    quantity = int(request.POST.get('quantity', 1))
    cart = get_or_create_cart(request.user)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 0}
    )

    new_quantity = cart_item.quantity + quantity

    # Stock validation
    if new_quantity > product.stock:
        messages.error(request, f"Only {product.stock} units available.")
        return redirect('products:product_detail', pk=product_id)

    # Max quantity validation
    if new_quantity > MAX_QUANTITY_PER_ITEM:
        messages.error(request, f"Maximum {MAX_QUANTITY_PER_ITEM} units per item allowed.")
        return redirect('products:product_detail', pk=product_id)

    cart_item.quantity = new_quantity
    cart_item.save()

    # Remove from wishlist when added to cart
    Wishlist.objects.filter(user=request.user, product=product).delete()

    if created:
        messages.success(request, f"'{product.name}' added to your cart.")
    else:
        messages.success(request, f"Cart updated — {new_quantity} x '{product.name}'.")

    return redirect('cart:cart_detail')


@login_required
def cart_detail_view(request):
    cart = get_or_create_cart(request.user)
    items = cart.items.select_related('product').prefetch_related('product__images')

    valid_items = []
    invalid_items = []
    stock_warnings = []
    can_checkout = True

    for item in items:
        # Check if product is blocked/deleted
        if item.product.is_deleted or not item.product.is_listed:
            invalid_items.append(item)
            can_checkout = False
            continue

        # Check if product is out of stock
        if not item.product.is_in_stock:
            invalid_items.append(item)
            can_checkout = False
            continue

        # Check if quantity exceeds current stock
        if item.quantity > item.product.stock:
            # Auto-adjust to current stock
            item.quantity = item.product.stock
            item.save()
            stock_warnings.append(
                f"'{item.product.name}' quantity adjusted to {item.product.stock} (current stock)."
            )

        valid_items.append(item)

    # Show stock warnings
    for warning in stock_warnings:
        messages.warning(request, warning)

    # Checkout disabled if no valid items
    if not valid_items:
        can_checkout = False

    context = {
        'cart': cart,
        'valid_items': valid_items,
        'invalid_items': invalid_items,
        'total_price': sum(item.subtotal for item in valid_items),
        'can_checkout': can_checkout,
    }
    return render(request, 'cart/cart.html', context)


@login_required
@require_POST
def remove_from_cart_view(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    product_name = item.product.name
    item.delete()
    messages.success(request, f"'{product_name}' removed from your cart.")
    return redirect('cart:cart_detail')


@login_required
@require_POST
def update_cart_quantity_view(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    action = request.POST.get('action')

    if action == 'increment':
        if item.quantity >= item.product.stock:
            messages.error(request, f"Only {item.product.stock} units available.")
        elif item.quantity >= MAX_QUANTITY_PER_ITEM:
            messages.error(request, f"Maximum {MAX_QUANTITY_PER_ITEM} units allowed.")
        else:
            item.quantity += 1
            item.save()
    elif action == 'decrement':
        if item.quantity <= 1:
            item.delete()
            messages.success(request, "Item removed from cart.")
            return redirect('cart:cart_detail')
        else:
            item.quantity -= 1
            item.save()

    return redirect('cart:cart_detail')


# ------------------------------------------------------------------
# WISHLIST
# ------------------------------------------------------------------
@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related('product').prefetch_related('product__images')

    return render(request, 'cart/wishlist.html', {'wishlist_items': wishlist_items})


@login_required
@require_POST
def wishlist_toggle_view(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    existing = Wishlist.objects.filter(user=request.user, product=product).first()
    if existing:
        existing.delete()
        messages.success(request, f"'{product.name}' removed from wishlist.")
    else:
        Wishlist.objects.create(user=request.user, product=product)
        messages.success(request, f"'{product.name}' added to wishlist.")

    return redirect(request.META.get('HTTP_REFERER', 'products:product_list'))


@login_required
@require_POST
def wishlist_remove_view(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    messages.success(request, f"'{product.name}' removed from wishlist.")
    return redirect('cart:wishlist')