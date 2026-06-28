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