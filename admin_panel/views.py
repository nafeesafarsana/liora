from django.shortcuts import render

# Create your views here.
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from .decorators import staff_required
from .forms import AdminLoginForm, UserSearchForm
from products.models import Category
from products.forms import CategoryForm
from products.models import Category, Product, ProductImage
from products.forms import CategoryForm, ProductForm
from PIL import Image as PilImage
import base64
import uuid
import os
from django.conf import settings
from orders.models import Order, OrderItem
from products.forms import CategoryForm, ProductForm, ProductColorFormSet
from coupons.models import Coupon
from offers.models import Offer
from django.utils import timezone


USERS_PER_PAGE = 10


def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_panel:dashboard')

    next_url = request.GET.get('next') or request.POST.get('next') or ''

    if request.method == 'POST':
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['username'].strip()
            password = form.cleaned_data['password']

            username = identifier
            if '@' in identifier:
                try:
                    matched_user = User.objects.get(email__iexact=identifier)
                    username = matched_user.username
                except User.DoesNotExist:
                    username = identifier

            user = authenticate(request, username=username, password=password)

            if user is None:
                messages.error(request, "Invalid username/email or password.")
            elif not user.is_staff:
                messages.error(request, "This account does not have admin access.")
            elif not user.is_active:
                messages.error(request, "This admin account has been deactivated.")
            else:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}.")
                return redirect(next_url or 'admin_panel:dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AdminLoginForm()

    return render(request, 'admin_panel/login.html', {'form': form, 'next': next_url})


@staff_required
def admin_logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out of the admin panel.")
    return redirect('admin_panel:login')


@staff_required
def dashboard_view(request):
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    blocked_users = User.objects.filter(is_active=False).count()
    recent_users = User.objects.all().order_by('-date_joined')[:5]


    context = {
        'total_users': total_users,
        'active_users': active_users,
        'blocked_users': blocked_users,
        'recent_users': recent_users,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@staff_required
def user_management_view(request):
    search_form = UserSearchForm(request.GET or None)
    query = request.GET.get('q', '').strip()

    users_qs = User.objects.all().order_by('-date_joined')

    if query:
        users_qs = users_qs.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(username__icontains=query)
        )

    paginator = Paginator(users_qs, USERS_PER_PAGE)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'search_form': search_form,
        'query': query,
        'page_obj': page_obj,
        'paginator': paginator,
        'total_results': users_qs.count(),
    }
    return render(request, 'admin_panel/user_management.html', context)


@staff_required
@require_POST
def toggle_block_user_view(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)

    if target_user.pk == request.user.pk:
        messages.error(request, "You cannot block your own account.")
    else:
        target_user.is_active = not target_user.is_active
        target_user.save(update_fields=['is_active'])

        if target_user.is_active:
            messages.success(request, f"{target_user.get_full_name() or target_user.email} has been unblocked.")
        else:
            messages.success(request, f"{target_user.get_full_name() or target_user.email} has been blocked.")

    redirect_url = reverse('admin_panel:user_management')
    query_string = request.POST.get('redirect_qs', '')
    if query_string:
        redirect_url = f"{redirect_url}?{query_string}"

    return redirect(redirect_url)
# ------------------------------------------------------------------
# CATEGORY MANAGEMENT
# ------------------------------------------------------------------

@staff_required
def category_list_view(request):
    query = request.GET.get('q', '').strip()
    categories = Category.objects.filter(is_deleted=False).order_by('-created_at')

    if query:
        categories = categories.filter(name__icontains=query)

    paginator = Paginator(categories, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'total_results': categories.count(),
    }
    return render(request, 'admin_panel/category_list.html', context)


@staff_required
def category_add_view(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category added successfully.")
            return redirect('admin_panel:category_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CategoryForm()

    return render(request, 'admin_panel/category_form.html', {
        'form': form,
        'action': 'Add',
    })


@staff_required
def category_edit_view(request, pk):
    category = get_object_or_404(Category, pk=pk, is_deleted=False)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated successfully.")
            return redirect('admin_panel:category_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CategoryForm(instance=category)

    return render(request, 'admin_panel/category_form.html', {
        'form': form,
        'action': 'Edit',
        'category': category,
    })


@staff_required
@require_POST
def category_delete_view(request, pk):
    category = get_object_or_404(Category, pk=pk, is_deleted=False)
    category.soft_delete()
    messages.success(request, f"Category '{category.name}' has been deleted.")
    return redirect('admin_panel:category_list')


@staff_required
@require_POST
def category_toggle_list_view(request, pk):
    category = get_object_or_404(Category, pk=pk, is_deleted=False)
    category.is_listed = not category.is_listed
    category.save()
    status = "listed" if category.is_listed else "unlisted"
    messages.success(request, f"Category '{category.name}' is now {status}.")
    return redirect('admin_panel:category_list')
# ------------------------------------------------------------------
# PRODUCT MANAGEMENT
# ------------------------------------------------------------------

@staff_required
def product_list_view(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.filter(
        is_deleted=False
    ).select_related('category').order_by('-created_at')

    if query:
        products = products.filter(name__icontains=query)

    paginator = Paginator(products, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'total_results': products.count(),
    }
    return render(request, 'admin_panel/product_list.html', context)

@staff_required
def product_add_view(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        color_formset = ProductColorFormSet(request.POST, prefix='colors')

        if form.is_valid() and color_formset.is_valid():
            cropped_images = request.POST.getlist('cropped_images[]')

            if len(cropped_images) < 3:
                messages.error(request, "Please upload at least 3 product images.")
                return render(request, 'admin_panel/product_form.html', {
                    'form': form,
                    'color_formset': color_formset,
                    'action': 'Add'
                })

            product = form.save()

            # Save colors
            colors = color_formset.save(commit=False)
            for color in colors:
                color.product = product
                color.save()
            for deleted in color_formset.deleted_objects:
                deleted.delete()

            # Save images (same as before)
            for index, image_data in enumerate(cropped_images):
                try:
                    format, imgstr = image_data.split(';base64,')
                    ext = format.split('/')[-1]
                    filename = f"{uuid.uuid4()}.{ext}"
                    image_bytes = base64.b64decode(imgstr)
                    upload_dir = os.path.join(settings.MEDIA_ROOT, 'product_images')
                    os.makedirs(upload_dir, exist_ok=True)
                    file_path = os.path.join(upload_dir, filename)
                    with open(file_path, 'wb') as f:
                        f.write(image_bytes)
                    img = PilImage.open(file_path)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img = img.resize((800, 800), PilImage.LANCZOS)
                    img.save(file_path, 'JPEG', quality=90)
                    ProductImage.objects.create(
                        product=product,
                        image=f'product_images/{filename}',
                        is_primary=(index == 0)
                    )
                except Exception:
                    continue

            messages.success(request, f"Product '{product.name}' added successfully.")
            return redirect('admin_panel:product_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProductForm()
        color_formset = ProductColorFormSet(prefix='colors')

    return render(request, 'admin_panel/product_form.html', {
        'form': form,
        'color_formset': color_formset,
        'action': 'Add',
    })
    
@staff_required
def product_edit_view(request, pk):
    product = get_object_or_404(Product, pk=pk, is_deleted=False)
    existing_images = product.images.all()

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        color_formset = ProductColorFormSet(
            request.POST,
            instance=product,
            prefix='colors'
        )

        if form.is_valid() and color_formset.is_valid():
            cropped_images = request.POST.getlist('cropped_images[]')
            total_images = existing_images.count() + len(cropped_images)

            if total_images < 3:
                messages.error(request, "Product must have at least 3 images.")
                return render(request, 'admin_panel/product_form.html', {
                    'form': form,
                    'color_formset': color_formset,
                    'action': 'Edit',
                    'product': product,
                    'existing_images': existing_images,
                })

            product = form.save()

            # Save colors
            colors = color_formset.save(commit=False)
            for color in colors:
                color.product = product
                color.save()
            for deleted in color_formset.deleted_objects:
                deleted.delete()

            # Save new images
            for index, image_data in enumerate(cropped_images):
                try:
                    format, imgstr = image_data.split(';base64,')
                    ext = format.split('/')[-1]
                    filename = f"{uuid.uuid4()}.{ext}"
                    image_bytes = base64.b64decode(imgstr)
                    upload_dir = os.path.join(settings.MEDIA_ROOT, 'product_images')
                    os.makedirs(upload_dir, exist_ok=True)
                    file_path = os.path.join(upload_dir, filename)
                    with open(file_path, 'wb') as f:
                        f.write(image_bytes)
                    img = PilImage.open(file_path)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img = img.resize((800, 800), PilImage.LANCZOS)
                    img.save(file_path, 'JPEG', quality=90)
                    ProductImage.objects.create(
                        product=product,
                        image=f'product_images/{filename}',
                        is_primary=False
                    )
                except Exception:
                    continue

            messages.success(request, f"Product '{product.name}' updated successfully.")
            return redirect('admin_panel:product_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProductForm(instance=product)
        color_formset = ProductColorFormSet(instance=product, prefix='colors')

    return render(request, 'admin_panel/product_form.html', {
        'form': form,
        'color_formset': color_formset,
        'action': 'Edit',
        'product': product,
        'existing_images': existing_images,
    })


@staff_required
@require_POST
def product_delete_view(request, pk):
    product = get_object_or_404(Product, pk=pk, is_deleted=False)
    product.soft_delete()
    messages.success(request, f"Product '{product.name}' has been deleted.")
    return redirect('admin_panel:product_list')


@staff_required
@require_POST
def product_toggle_list_view(request, pk):
    product = get_object_or_404(Product, pk=pk, is_deleted=False)
    product.is_listed = not product.is_listed
    product.save()
    status = "listed" if product.is_listed else "unlisted"
    messages.success(request, f"Product '{product.name}' is now {status}.")
    return redirect('admin_panel:product_list')


@staff_required
@require_POST
def product_image_delete_view(request, pk):
    """Delete a single product image."""
    image = get_object_or_404(ProductImage, pk=pk)
    product = image.product

    # Ensure at least 3 images remain
    if product.images.count() <= 3:
        messages.error(request, "Product must have at least 3 images.")
        return redirect('admin_panel:product_edit', pk=product.pk)

    image.delete()
    messages.success(request, "Image deleted successfully.")
    return redirect('admin_panel:product_edit', pk=product.pk)
# ==================================================================
# ADMIN ORDER MANAGEMENT
# ==================================================================

@staff_required
def admin_order_list_view(request):
    """
    Lists all orders descending by date.
    Supports search by orderID or user email,
    filter by status, and pagination.
    """
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()

    orders = Order.objects.select_related('user').order_by('-created_at')

    if query:
        orders = orders.filter(
            Q(order_id__icontains=query) |
            Q(user__email__icontains=query) |
            Q(full_name__icontains=query)
)

    if status_filter:
        orders = orders.filter(status=status_filter)

    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'total_results': orders.count(),
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'admin_panel/order_list.html', context)

@staff_required
def admin_order_detail_view(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    items = order.items.select_related('product').all()

    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = [s[0] for s in Order.STATUS_CHOICES]

        if new_status in valid_statuses:
            old_status = order.status
            order.status = new_status
            order.save()

            # Restore stock if cancelled (and wasn't already cancelled)
            if new_status == 'cancelled' and old_status != 'cancelled':
                for item in items:
                    if item.status != 'cancelled' and item.product:
                        item.product.stock += item.quantity
                        item.product.save(update_fields=['stock'])
                        item.status = 'cancelled'
                        item.save()

            # Restore stock if returned (and wasn't already returned)
            if new_status == 'returned' and old_status != 'returned':
                for item in items:
                    if item.status not in ['cancelled', 'returned'] and item.product:
                        item.product.stock += item.quantity
                        item.product.save(update_fields=['stock'])
                        item.status = 'returned'
                        item.save()

            messages.success(
                request,
                f"Order {order.order_id} status updated to '{order.get_status_display()}'."
            )
        else:
            messages.error(request, "Invalid status selected.")

        return redirect('admin_panel:admin_order_detail', order_id=order_id)

    context = {
        'order': order,
        'items': items,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'admin_panel/order_detail.html', context)


# ==================================================================
# ADMIN INVENTORY / STOCK MANAGEMENT
# ==================================================================

@staff_required
def inventory_view(request):
    """
    Shows all products with their current stock.
    Supports search and sort by stock level.
    Admin can update stock directly from this page.
    """
    query = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', 'low_stock')

    products = Product.objects.filter(
        is_deleted=False
    ).select_related('category').order_by('stock')

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(category__name__icontains=query)
        )

    sort_options = {
        'low_stock': 'stock',
        'high_stock': '-stock',
        'name_az': 'name',
        'newest': '-created_at',
    }
    products = products.order_by(sort_options.get(sort, 'stock'))

    paginator = Paginator(products, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'sort': sort,
        'total_results': products.count(),
    }
    return render(request, 'admin_panel/inventory.html', context)


@staff_required
@require_POST
def update_stock_view(request, pk):
    """
    Admin updates stock for a specific product directly.
    """
    product = get_object_or_404(Product, pk=pk, is_deleted=False)
    new_stock = request.POST.get('stock', '').strip()

    try:
        new_stock = int(new_stock)
        if new_stock < 0:
            raise ValueError
        product.stock = new_stock
        product.save(update_fields=['stock'])
        messages.success(
            request,
            f"Stock for '{product.name}' updated to {new_stock}."
        )
    except ValueError:
        messages.error(request, "Invalid stock value.")

    redirect_url = reverse('admin_panel:inventory')
    query_string = request.POST.get('redirect_qs', '')
    if query_string:
        redirect_url = f"{redirect_url}?{query_string}"

    return redirect(redirect_url)



# ------------------------------------------------------------------
# COUPON MANAGEMENT
# ------------------------------------------------------------------
@staff_required
def coupon_list_view(request):
    coupons = Coupon.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/coupon_list.html', {'coupons': coupons})


@staff_required
def coupon_add_view(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        description = request.POST.get('description', '').strip()
        discount_type = request.POST.get('discount_type', 'percentage')
        discount_value = request.POST.get('discount_value', 0)
        minimum_order = request.POST.get('minimum_order_amount', 0)
        maximum_discount = request.POST.get('maximum_discount', None)
        usage_limit = request.POST.get('usage_limit', 0)
        valid_from = request.POST.get('valid_from')
        valid_until = request.POST.get('valid_until')

        if Coupon.objects.filter(code=code).exists():
            messages.error(request, "Coupon code already exists.")
            return render(request, 'admin_panel/coupon_form.html', {'action': 'Add'})

        Coupon.objects.create(
            code=code,
            description=description,
            discount_type=discount_type,
            discount_value=discount_value,
            minimum_order_amount=minimum_order,
            maximum_discount=maximum_discount or None,
            usage_limit=usage_limit,
            valid_from=valid_from,
            valid_until=valid_until,
        )
        messages.success(request, f"Coupon '{code}' created.")
        return redirect('admin_panel:coupon_list')

    return render(request, 'admin_panel/coupon_form.html', {'action': 'Add'})


@staff_required
@require_POST
def coupon_delete_view(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    code = coupon.code
    coupon.delete()
    messages.success(request, f"Coupon '{code}' deleted.")
    return redirect('admin_panel:coupon_list')


@staff_required
@require_POST
def coupon_toggle_view(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    coupon.is_active = not coupon.is_active
    coupon.save()
    status = "activated" if coupon.is_active else "deactivated"
    messages.success(request, f"Coupon '{coupon.code}' {status}.")
    return redirect('admin_panel:coupon_list')


# ------------------------------------------------------------------
# OFFER MANAGEMENT
# ------------------------------------------------------------------
@staff_required
def offer_list_view(request):
    offers = Offer.objects.select_related('product', 'category').order_by('-created_at')
    return render(request, 'admin_panel/offer_list.html', {'offers': offers})


@staff_required
def offer_add_view(request):
    from products.models import Product, Category
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        offer_type = request.POST.get('offer_type')
        discount_percentage = request.POST.get('discount_percentage', 0)
        valid_from = request.POST.get('valid_from')
        valid_until = request.POST.get('valid_until')
        product_id = request.POST.get('product_id')
        category_id = request.POST.get('category_id')

        offer = Offer(
            name=name,
            offer_type=offer_type,
            discount_percentage=discount_percentage,
            valid_from=valid_from,
            valid_until=valid_until,
        )

        if offer_type == 'product' and product_id:
            offer.product_id = product_id
        elif offer_type == 'category' and category_id:
            offer.category_id = category_id

        offer.save()
        messages.success(request, f"Offer '{name}' created.")
        return redirect('admin_panel:offer_list')

    products = Product.objects.filter(is_deleted=False, is_listed=True)
    categories = Category.objects.filter(is_deleted=False, is_listed=True)
    return render(request, 'admin_panel/offer_form.html', {
        'action': 'Add',
        'products': products,
        'categories': categories,
    })


@staff_required
@require_POST
def offer_delete_view(request, pk):
    offer = get_object_or_404(Offer, pk=pk)
    name = offer.name
    offer.delete()
    messages.success(request, f"Offer '{name}' deleted.")
    return redirect('admin_panel:offer_list')


@staff_required
@require_POST
def offer_toggle_view(request, pk):
    offer = get_object_or_404(Offer, pk=pk)
    offer.is_active = not offer.is_active
    offer.save()
    status = "activated" if offer.is_active else "deactivated"
    messages.success(request, f"Offer '{offer.name}' {status}.")
    return redirect('admin_panel:offer_list')


# ------------------------------------------------------------------
# RETURN VERIFICATION
# ------------------------------------------------------------------
@staff_required
def return_requests_view(request):
    """Admin reviews return requests and confirms refunds."""
    return_orders = Order.objects.filter(
        status='returned'
    ).select_related('user').order_by('-returned_at')

    return render(request, 'admin_panel/return_requests.html', {
        'return_orders': return_orders
    })


@staff_required
@require_POST
def confirm_refund_view(request, order_id):
    """Admin confirms return and refunds to wallet."""
    from wallet.views import get_or_create_wallet
    order = get_object_or_404(Order, order_id=order_id)

    if order.status != 'returned':
        messages.error(request, "This order is not in returned status.")
        return redirect('admin_panel:return_requests')

    refund_amount = order.total + (order.wallet_amount_used or 0)
    wallet = get_or_create_wallet(order.user)
    wallet.credit(
        refund_amount,
        description=f"Refund for returned order {order.order_id}"
    )

    order.payment_status = 'refunded'
    order.save(update_fields=['payment_status'])

    messages.success(
        request,
        f"₹{refund_amount} refunded to {order.user.email}'s wallet."
    )
    return redirect('admin_panel:return_requests')    
@staff_required
def sales_report_redirect(request):
    from django.shortcuts import redirect
    return redirect('reports:sales_report')    
