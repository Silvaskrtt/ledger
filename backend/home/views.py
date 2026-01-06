from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils.timezone import now

from accounts.models import Account
from transactions.models import Transaction


@login_required
def home_view(request):
    user = request.user
    today = now()

    saldo_atual = (
        Account.objects
        .filter(user=user)
        .aggregate(total=Sum('balance'))['total']
        or 0
    )

    entradas_mes = (
        Transaction.objects
        .filter(
            id_user=user,
            direction='IN',
            occurred_at__year=today.year,
            occurred_at__month=today.month
        )
        .aggregate(total=Sum('amount'))['total']
        or 0
    )

    saidas_mes = (
        Transaction.objects
        .filter(
            id_user=user,
            direction='OUT',
            occurred_at__year=today.year,
            occurred_at__month=today.month
        )
        .aggregate(total=Sum('amount'))['total']
        or 0
    )

    return render(request, 'home/home.html', {
        'saldo_atual': saldo_atual,
        'entradas_mes': entradas_mes,
        'saidas_mes': saidas_mes,
    })