from functools import wraps

from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import redirect
from django.urls import reverse


def staff_required(view_func):
    """
    Only allows access to users who are logged in AND is_staff=True.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = reverse('admin_panel:login')
            return redirect(f"{login_url}?{REDIRECT_FIELD_NAME}={request.path}")

        if not request.user.is_staff:
            messages.error(request, "You do not have permission to access the admin panel.")
            return redirect('admin_panel:login')

        return view_func(request, *args, **kwargs)

    return _wrapped_view