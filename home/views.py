from django.shortcuts import render


def home_view(request):
    """
    Renders the LIORA landing page.
    Featured products below are placeholder/demo data — wire up to a real
    Product model when the catalog app is built.
    """
    featured_products = [
        {'name': 'Aurelia Tote', 'price': '18,500', 'image': 'images/bag-1.jpg'},
        {'name': 'Vesper Clutch', 'price': '12,900', 'image': 'images/bag-2.jpg'},
        {'name': 'Noir Crossbody', 'price': '15,200', 'image': 'images/bag-3.jpg'},
        {'name': 'Ember Satchel', 'price': '21,000', 'image': 'images/bag-4.jpg'},
    ]
    return render(request, 'home/home.html', {'featured_products': featured_products})
