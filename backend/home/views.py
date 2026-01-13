# backend/home/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils.timezone import now, timedelta
from datetime import datetime
from accounts.models import Account
from transactions.models import Transaction


@login_required
def home_view(request):
    """
    View principal do dashboard que exibe resumo financeiro do usuário.
    """
    user = request.user
    today = now()
    
    # Mês atual
    current_year = today.year
    current_month = today.month
    
    # Mês anterior
    if current_month == 1:
        prev_month = 12
        prev_year = current_year - 1
    else:
        prev_month = current_month - 1
        prev_year = current_year
    
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
    
    # 2. DÉBITO EM CARTÕES
    sum_credit_cards = (
        Account.objects
        .filter(user=user, is_active=True, type='CREDIT_CARD')
        .aggregate(total=Sum('balance'))['total'] or 0
    )
    
    debito_absoluto = abs(sum_credit_cards)
    total_patrimonio = patrimonio_contas + sum_credit_cards
    saldo_atual = patrimonio_contas
    
    # 3. TOTAL INVESTIDO
    total_investido = (
        Account.objects
        .filter(user=user, is_active=True, type='INVESTMENT')
        .aggregate(total=Sum('balance'))['total'] or 0
    )
    
    # 4. Cálculo de entradas e saídas do mês ATUAL
    entradas_mes = Transaction.objects.filter(
        user=user,
        direction='IN',
        occurred_at__year=current_year,
        occurred_at__month=current_month,
        is_deleted=False
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    saidas_mes = Transaction.objects.filter(
        user=user,
        direction='OUT',
        occurred_at__year=current_year,
        occurred_at__month=current_month,
        is_deleted=False
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # 5. Cálculo de entradas e saídas do mês ANTERIOR
    entradas_mes_anterior = Transaction.objects.filter(
        user=user,
        direction='IN',
        occurred_at__year=prev_year,
        occurred_at__month=prev_month,
        is_deleted=False
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    saidas_mes_anterior = Transaction.objects.filter(
        user=user,
        direction='OUT',
        occurred_at__year=prev_year,
        occurred_at__month=prev_month,
        is_deleted=False
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # 6. Cálculo da variação percentual
    # Para receitas
    if entradas_mes_anterior > 0:
        variacao_receitas = ((entradas_mes - entradas_mes_anterior) / entradas_mes_anterior) * 100
    else:
        variacao_receitas = 100 if entradas_mes > 0 else 0
    
    # Para despesas (usamos valor absoluto pois aumento de despesas é negativo)
    if saidas_mes_anterior > 0:
        variacao_despesas = ((saidas_mes - saidas_mes_anterior) / saidas_mes_anterior) * 100
    else:
        variacao_despesas = 100 if saidas_mes > 0 else 0
    
    # 7. Orçamento (você precisa implementar seu modelo de orçamento)
    # Por enquanto, vamos usar um valor fixo ou 0
    orcamento_mes = 0  # Você precisa substituir por sua lógica de orçamento
    
    return render(request, 'home/home.html', {
        'total_patrimonio': total_patrimonio,
        'saldo_atual': saldo_atual,
        'debito_cartoes': debito_absoluto,
        'entradas_mes': entradas_mes,
        'saidas_mes': saidas_mes,
        'entradas_mes_anterior': entradas_mes_anterior,
        'saidas_mes_anterior': saidas_mes_anterior,
        'total_investido': total_investido,
        'variacao_receitas': variacao_receitas,
        'variacao_despesas': variacao_despesas,
        'orcamento_mes': orcamento_mes,
        'tem_historico_anterior': entradas_mes_anterior > 0 or saidas_mes_anterior > 0,
    })