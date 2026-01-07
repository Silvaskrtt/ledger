# backend/home/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Case, When, F, DecimalField
from django.utils.timezone import now
from accounts.models import Account
from transactions.models import Transaction


@login_required
def home_view(request):
    """
    View principal do dashboard que exibe resumo financeiro do usuário.
    
    Calcula e retorna:
    - Saldo atual (entradas - saídas)
    - Entradas do mês corrente
    - Saídas do mês corrente
    
    Requer autenticação do usuário.
    """
    user = request.user
    today = now()
    
    # Agregação otimizada para calcular totais de entradas e saídas em uma única query
    # Usa expressões condicionais do ORM para melhor performance
    dashboard = (
        Transaction.objects
        .filter(id_user=user)
        .aggregate(
            entradas=Sum(
                Case(
                    When(direction='IN', then=F('amount')),
                    default=0,
                    output_field=DecimalField()
                )
            ),
            saidas=Sum(
                Case(
                    When(direction='OUT', then=F('amount')),
                    default=0,
                    output_field=DecimalField()
                )
            )
        )
    )

    # Calcula saldo real considerando possíveis valores nulos
    saldo_real = (dashboard['entradas'] or 0) - (dashboard['saidas'] or 0)

    # Calcula entradas do mês atual - filtro por período
    entradas_mes = Transaction.objects.filter(
        id_user=user,
        direction='IN',
        occurred_at__year=today.year,
        occurred_at__month=today.month
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Calcula saídas do mês atual - filtro por período
    saidas_mes = Transaction.objects.filter(
        id_user=user,
        direction='OUT',
        occurred_at__year=today.year,
        occurred_at__month=today.month
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Calcula saldo atual usando uma única agregação com lógica de sinal
    # Entradas são positivas, saídas são negativas
    saldo_atual = (
        Transaction.objects
        .filter(id_user=user)
        .aggregate(
            saldo=Sum(
                Case(
                    When(direction='IN', then=F('amount')),
                    When(direction='OUT', then=-F('amount')),
                    output_field=DecimalField()
                )
            )
        )['saldo']
        or 0
    )

    # Contexto para renderização do template
    return render(request, 'home/home.html', {
        'saldo_atual': saldo_atual,
        'entradas_mes': entradas_mes,
        'saidas_mes': saidas_mes,
    })