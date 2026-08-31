from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Product, Category,Review
from django.db.models import Avg
from .forms import ReviewForm
from django.contrib import messages



def product_list_view(request):
    """
    User-facing product listing page.
    Supports: search, category filter, price range filter, sorting, pagination.
    All combined together in one query.
    """
    # Get all active products (not deleted, not unlisted)
    products = Product.objects.filter(
        is_deleted=False,
        is_listed=True,
        category__is_deleted=False,
        category__is_listed=True,
    ).select_related('category').prefetch_related('images')

    # Get all listed categories for filter dropdown
    categories = Category.objects.filter(
        is_deleted=False,
        is_listed=True
    ).order_by('name')

    # --- Search ---
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query) |
            Q(category__name__icontains=query)
        )

    # --- Category filter ---
    category_id = request.GET.get('category', '').strip()
    selected_category = None
    if category_id:
        try:
            selected_category = Category.objects.get(
                pk=int(category_id),
                is_deleted=False,
                is_listed=True
            )
            products = products.filter(category=selected_category)
        except (ValueError, Category.DoesNotExist):
            category_id = ''

    # --- Price range filter ---
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            min_price = ''
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            max_price = ''

    # --- Brand filter ---
    brand = request.GET.get('brand', '').strip()
    if brand:
        products = products.filter(brand__iexact=brand)

    # Get all available brands for filter dropdown
    brands = Product.objects.filter(
        is_deleted=False,
        is_listed=True,
        brand__isnull=False
    ).exclude(brand='').values_list('brand', flat=True).distinct().order_by('brand')

    # --- Sorting ---
    sort = request.GET.get('sort', 'newest')
    sort_options = {
        'newest': '-created_at',
        'oldest': 'created_at',
        'price_low': 'price',
        'price_high': '-price',
        'name_az': 'name',
        'name_za': '-name',
    }
    sort_field = sort_options.get(sort, '-created_at')
    products = products.order_by(sort_field)

    # --- Pagination ---
    paginator = Paginator(products, 12)  # 12 products per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Build query string for pagination links
    # (preserves search/filter/sort params across pages)
    query_params = request.GET.copy()
    query_params.pop('page', None)
    query_string = query_params.urlencode()
    # Add near the end of product_list_view, before context dict
    wishlist_product_ids = set()
    if request.user.is_authenticated:
        from cart.models import Wishlist
        wishlist_product_ids = set(
            Wishlist.objects.filter(
                user=request.user
            ).values_list('product_id', flat=True)
        )

    # ---- Attach active offer to each product ----
    try:
        from offers.utils import get_best_offer_for_product
        from decimal import Decimal
        for product in page_obj:
            offer = get_best_offer_for_product(product)
            if offer:
                offer_pct = offer.discount_percentage
                # Compare offer % with existing discount_price %
                existing_pct = product.discount_percentage
                if offer_pct > existing_pct:
                    # Offer is better — show offer badge only
                    product.active_offer = offer
                    product.best_discount_pct = offer_pct
                else:
                    # Existing discount is better or equal — show that only
                    product.active_offer = None
                    product.best_discount_pct = existing_pct
            else:
                product.active_offer = None
                product.best_discount_pct = product.discount_percentage
    except Exception:
        for product in page_obj:
            product.active_offer = None
            product.best_discount_pct = product.discount_percentage
        # ---- End offer attachment ----


    context = {
        'page_obj': page_obj,
        'products': page_obj,
        'categories': categories,
        'query': query,
        'category_id': category_id,
        'selected_category': selected_category,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort,
        'brand': brand,
        'brands': brands,
        'total_results': products.count(),
        'query_string': query_string,
        'wishlist_product_ids': wishlist_product_ids,
    }

    return render(request, 'products/product_list.html', context)




def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if product.is_deleted or not product.is_listed:
        messages.error(request, "This product is no longer available.")
        return redirect('products:product_list')

    if product.category and (
        product.category.is_deleted or not product.category.is_listed
    ):
        messages.error(request, "This product is no longer available.")
        return redirect('products:product_list')

    # Colors
    colors = product.colors.all()

    # Reviews
    reviews = product.reviews.select_related('user').all()
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    avg_rating = round(avg_rating, 1) if avg_rating else None
    total_reviews = reviews.count()

    user_review = None
    user_has_reviewed = False
    review_form = None

    if request.user.is_authenticated:
        user_review = Review.objects.filter(
            product=product, user=request.user
        ).first()
        user_has_reviewed = user_review is not None

        if request.method == 'POST':
            if user_has_reviewed:
                review_form = ReviewForm(request.POST, instance=user_review)
            else:
                review_form = ReviewForm(request.POST)

            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.product = product
                review.user = request.user
                review.save()
                messages.success(request, "Your review has been submitted.")
                return redirect('products:product_detail', pk=pk)
            else:
                messages.error(request, "Please correct the errors below.")
        else:
            if user_has_reviewed:
                review_form = ReviewForm(instance=user_review)
            else:
                review_form = ReviewForm()

    related_products = Product.objects.filter(
        category=product.category,
        is_deleted=False,
        is_listed=True,
    ).exclude(pk=pk)[:4]

    images = product.images.all()

    is_in_wishlist = False
    if request.user.is_authenticated:
        from cart.models import Wishlist
        is_in_wishlist = Wishlist.objects.filter(
            user=request.user, product=product
        ).exists()


    context = {
        'product': product,
        'images': images,
        'colors': colors,
        'related_products': related_products,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'total_reviews': total_reviews,
        'review_form': review_form,
        'user_has_reviewed': user_has_reviewed,
        'user_review': user_review,
    }
    return render(request, 'products/product_detail.html', context)