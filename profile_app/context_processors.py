from allauth.socialaccount.models import SocialAccount


def google_user(request):
    is_google_user = False
    cart_count = 0
    wishlist_count = 0

    if request.user.is_authenticated:
        try:
            from allauth.socialaccount.models import SocialAccount
            is_google_user = SocialAccount.objects.filter(
                user=request.user, provider='google'
            ).exists()
        except Exception:
            pass

        try:
            cart_count = request.user.cart.total_items
        except Exception:
            cart_count = 0

        try:
            from cart.models import Wishlist
            wishlist_count = Wishlist.objects.filter(
                user=request.user
            ).count()
        except Exception:
            wishlist_count = 0

    return {
        'is_google_user': is_google_user,
        'cart_count': cart_count,
        'wishlist_count': wishlist_count,
    }