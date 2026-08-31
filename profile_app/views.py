from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from accounts.models import OTP
from accounts.forms import OTPForm
from accounts.utils import send_otp_email
from .forms import EditProfileForm, ChangePasswordForm, AddressForm, ProfilePictureForm
from .models import Address, Profile
from allauth.socialaccount.models import SocialAccount
    

# ------------------------------------------------------------------
# PROFILE
# ------------------------------------------------------------------
@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'profile_app/profile.html', {'profile': profile})





@login_required
def edit_profile_view(request):
    user = request.user

    if request.method == 'POST':
        form = EditProfileForm(request.POST, current_user=user)
        picture_form = ProfilePictureForm(request.POST, request.FILES, instance=user.profile)

        if form.is_valid() and picture_form.is_valid():
            new_email = form.cleaned_data['email']

            picture_form.save()  # saves the uploaded image (if one was provided)

            if new_email != user.email:
                request.session['pending_profile_update'] = {
                    'first_name': form.cleaned_data['first_name'],
                    'last_name': form.cleaned_data['last_name'],
                    'new_email': new_email,
                }
                otp = OTP.create_otp(email=new_email, purpose='email_change')
                send_otp_email(new_email, otp.code, purpose='email_change')
                messages.success(request, f"A verification code has been sent to {new_email}.")
                return redirect('profile_app:verify_email_change')
            else:
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                user.save()
                messages.success(request, "Your profile has been updated successfully.")
                return redirect('profile_app:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = EditProfileForm(initial={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
        }, current_user=user)
        picture_form = ProfilePictureForm(instance=user.profile)

    return render(request, 'profile_app/edit_profile.html', {
        'form': form,
        'picture_form': picture_form,
    })

@login_required
def verify_email_change_view(request):
    pending = request.session.get('pending_profile_update')
    if not pending:
        messages.error(request, "No pending email change found.")
        return redirect('profile_app:edit_profile')

    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            code = form.get_otp_code()
            otp_qs = OTP.objects.filter(
                email=pending['new_email'], purpose='email_change', is_used=False
            ).order_by('-created_at').first()

            if otp_qs and otp_qs.is_valid(code):
                otp_qs.is_used = True
                otp_qs.save()

                user = request.user
                user.first_name = pending['first_name']
                user.last_name = pending['last_name']
                user.email = pending['new_email']
                user.username = pending['new_email']
                user.save()

                del request.session['pending_profile_update']
                messages.success(request, "Your email has been updated successfully.")
                return redirect('profile_app:profile')
            elif otp_qs and otp_qs.is_expired():
                messages.error(request, "This code has expired. Please request a new one.")
            else:
                messages.error(request, "Invalid verification code. Please try again.")
        else:
            messages.error(request, "Please enter the complete 6-digit code.")
    else:
        form = OTPForm()

    return render(request, 'profile_app/verify_email_otp.html', {
        'form': form,
        'email': pending['new_email'],
    })


@login_required
def resend_email_change_otp_view(request):
    pending = request.session.get('pending_profile_update')
    if not pending:
        messages.error(request, "No pending email change found.")
        return redirect('profile_app:edit_profile')

    otp = OTP.create_otp(email=pending['new_email'], purpose='email_change')
    send_otp_email(pending['new_email'], otp.code, purpose='email_change')
    messages.success(request, "A new verification code has been sent.")
    return redirect('profile_app:verify_email_change')



@login_required
def change_password_view(request):
    
    
    if SocialAccount.objects.filter(user=request.user, provider='google').exists():
        messages.error(request, "Google account users cannot change their password here.")
        return redirect('profile_app:profile')

    if request.method == 'POST':
        form = ChangePasswordForm(request.POST, user=request.user)
        if form.is_valid():
            request.user.set_password(form.cleaned_data['new_password'])
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Your password has been changed successfully.")
            return redirect('profile_app:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ChangePasswordForm(user=request.user)

    return render(request, 'profile_app/change_password.html', {'form': form})

# ------------------------------------------------------------------
# ADDRESS MANAGEMENT
# ------------------------------------------------------------------
@login_required
def address_list_view(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'profile_app/address_list.html', {'addresses': addresses})


@login_required
def add_address_view(request):
    next_url = request.GET.get('next', '') or request.POST.get('next', '')

    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            if address.is_default:
                Address.objects.filter(
                    user=request.user, is_default=True
                ).update(is_default=False)
            address.save()
            messages.success(request, "Address added successfully.")

            if next_url:
                return redirect(next_url)
            return redirect('profile_app:address_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AddressForm()

    return render(request, 'profile_app/add_address.html', {
        'form': form,
        'next': next_url,
    })
    
@login_required
def edit_address_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    next_url = request.GET.get('next', '') or request.POST.get('next', '')

    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            updated_address = form.save(commit=False)
            if updated_address.is_default:
                Address.objects.filter(
                    user=request.user, is_default=True
                ).exclude(pk=address.pk).update(is_default=False)
            updated_address.save()
            messages.success(request, "Address updated successfully.")

            if next_url:
                return redirect(next_url)
            return redirect('profile_app:address_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AddressForm(instance=address)

    return render(request, 'profile_app/edit_address.html', {
        'form': form,
        'address': address,
        'next': next_url,
    })

@login_required
def delete_address_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, "Address deleted successfully.")
        return redirect('profile_app:address_list')
    return render(request, 'profile_app/address_list.html', {
        'addresses': Address.objects.filter(user=request.user),
        'confirm_delete_pk': pk,
    })