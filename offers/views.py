from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .models import ReferralCode, ReferralUsage
from wallet.views import get_or_create_wallet
import uuid


def generate_referral_code(user):
    """Generate unique referral code for user."""
    code = f"LIORA{user.pk}{uuid.uuid4().hex[:4].upper()}"
    referral, created = ReferralCode.objects.get_or_create(
        user=user,
        defaults={'code': code, 'reward_amount': 100}
    )
    return referral


@login_required
def my_referral_view(request):
    """Shows user their referral code and usage stats."""
    referral = generate_referral_code(request.user)
    usages = referral.usages.select_related('referred_user').all()

    return render(request, 'offers/referral.html', {
        'referral': referral,
        'usages': usages,
        'referral_url': request.build_absolute_uri(
            f"/accounts/signup/?ref={referral.code}"
        ),
    })


@login_required
@require_POST
def apply_referral_view(request):
    """Apply referral code during signup bonus."""
    code = request.POST.get('referral_code', '').strip().upper()

    try:
        referral = ReferralCode.objects.get(code=code)
    except ReferralCode.DoesNotExist:
        messages.error(request, "Invalid referral code.")
        return redirect('home:home')

    if referral.user == request.user:
        messages.error(request, "You cannot use your own referral code.")
        return redirect('home:home')

    if ReferralUsage.objects.filter(referred_user=request.user).exists():
        messages.error(request, "You have already used a referral code.")
        return redirect('home:home')

    # Give reward to referrer
    referrer_wallet = get_or_create_wallet(referral.user)
    referrer_wallet.credit(
        referral.reward_amount,
        description=f"Referral bonus — {request.user.email} joined"
    )

    # Give reward to new user
    new_user_wallet = get_or_create_wallet(request.user)
    new_user_wallet.credit(
        referral.reward_amount,
        description=f"Welcome bonus — joined via referral"
    )

    ReferralUsage.objects.create(
        referral_code=referral,
        referred_user=request.user,
        reward_given=True
    )
    referral.times_used += 1
    referral.save(update_fields=['times_used'])

    messages.success(
        request,
        f"Referral applied! ₹{referral.reward_amount} added to your wallet."
    )
    return redirect('wallet:wallet')