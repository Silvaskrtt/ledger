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
    
    # 1. PATRIMÔNIO TOTAL (apenas contas normais - exclui cartões)
    patrimonio_contas = (
        Account.objects
        .filter(
            user=user, 
            is_active=True,
            type__in=['CHECKING', 'SAVINGS', 'INVESTMENT', 'CASH', 'OTHER']
        )
        .aggregate(total=Sum('balance'))['total'] or 0
    )
    
    # 2. DÉBITO EM CARTÕES (valor ABSOLUTO para exibição)
    # OBS: balance de cartões é NEGATIVO
    sum_credit_cards = (
        Account.objects
        .filter(user=user, is_active=True, type='CREDIT_CARD')
        .aggregate(total=Sum('balance'))['total'] or 0
    )
    
    # 3. DÉBITO ABSOLUTO (apenas para exibição)
    debito_absoluto = abs(sum_credit_cards)
    
    # 4. PATRIMÔNIO LÍQUIDO = Contas + Cartões (cartões são negativos)
    # Ex: contas 2000 + cartões -500 = 1500
    total_patrimonio = patrimonio_contas + sum_credit_cards
    
    # 5. SALDO DISPONÍVEL (apenas contas normais)
    saldo_atual = patrimonio_contas
    
    # 6. TOTAL INVESTIDO
    total_investido = (
        Account.objects
        .filter(user=user, is_active=True, type='INVESTMENT')
        .aggregate(total=Sum('balance'))['total'] or 0
    )
    
    # 7. Cálculo de entradas e saídas do mês
    entradas_mes = Transaction.objects.filter(
        user=user,
        direction='IN',
        occurred_at__year=today.year,
        occurred_at__month=today.month,
        is_deleted=False
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    saidas_mes = Transaction.objects.filter(
        user=user,
        direction='OUT',
        occurred_at__year=today.year,
        occurred_at__month=today.month,
        is_deleted=False
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    return render(request, 'home/home.html', {
        'total_patrimonio': total_patrimonio,      # Patrimônio líquido
        'saldo_atual': saldo_atual,               # Saldo disponível (contas)
        'debito_cartoes': debito_absoluto,         # Dívida cartões (valor absoluto para exibição)
        'entradas_mes': entradas_mes,
        'saidas_mes': saidas_mes,
        'total_investido': total_investido,
    })