from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import Wallet, WalletTransaction


def get_or_create_wallet(user):
    wallet, created = Wallet.objects.get_or_create(user=user)
    return wallet


@login_required
def wallet_view(request):
    wallet = get_or_create_wallet(request.user)
    transactions = wallet.transactions.all()[:20]
    return render(request, 'wallet/wallet.html', {
        'wallet': wallet,
        'transactions': transactions,
    })