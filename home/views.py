from django.shortcuts import render
from products.models import Product


def home_view(request):
    # Get real featured products from database
    featured_products = Product.objects.filter(
        is_deleted=False,
        is_listed=True,
        category__is_deleted=False,
        category__is_listed=True,
    ).select_related('category').prefetch_related('images').order_by('-created_at')[:4]

    context = {
        'featured_products': featured_products,
    }
    return render(request, 'home/home.html', context)


def about_view(request):
    return render(request, 'home/about.html')