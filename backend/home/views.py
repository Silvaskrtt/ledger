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
    
    # 1. PATRIMÔNIO TOTAL: Soma de TODAS as contas
    total_patrimonio = (
        Account.objects
        .filter(user=user, is_active=True)
        .aggregate(total=Sum('balance'))['total'] or 0
    )
    
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

    # 2. ENTRADAS do mês
    entradas_mes = Transaction.objects.filter(
        id_user=user,
        direction='IN',
        occurred_at__year=today.year,
        occurred_at__month=today.month,
        is_deleted=False
    ).aggregate(total=Sum('amount'))['total'] or 0

    # 3. SAÍDAS do mês
    saidas_mes = Transaction.objects.filter(
        id_user=user,
        direction='OUT',
        occurred_at__year=today.year,
        occurred_at__month=today.month,
        is_deleted=False
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Calcula saldo atual usando uma única agregação com lógica de sinal
    # Entradas são positivas, saídas são negativas
    # 4. SALDO ATUAL: Somente contas não-cartão
    saldo_atual = (
        Account.objects
        .filter(
            user=user, 
            is_active=True,
            type__in=['CHECKING', 'SAVINGS', 'INVESTMENT', 'CASH', 'OTHER']
        )
        .aggregate(total=Sum('balance'))['total'] or 0
    )

    # 5. TOTAL INVESTIDO (opcional)
    total_investido = (
        Account.objects
        .filter(user=user, is_active=True, type='INVESTMENT')
        .aggregate(total=Sum('balance'))['total'] or 0
    )
    
    # 6. DÉBITO TOTAL EM CARTÕES
    debito_cartoes = (
        Account.objects
        .filter(user=user, is_active=True, type='CREDIT_CARD')
        .aggregate(total=Sum('balance'))['total'] or 0
    )
    
    return render(request, 'home/home.html', {
        'total_patrimonio': total_patrimonio,
        'saldo_atual': saldo_atual,
        'entradas_mes': entradas_mes,
        'saidas_mes': saidas_mes,
        'total_investido': total_investido,
        'debito_cartoes': abs(debito_cartoes),  # Valor absoluto para exibição
    })