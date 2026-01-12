from datetime import date
from .models import Budget


def get_or_create_current_month_budget(user):
    """Obtém ou cria um orçamento para o mês atual"""
    today = date.today()
    period_start = today.replace(day=1)
    
    # Tentar encontrar um orçamento existente
    budget = Budget.objects.filter(
        user=user,
        period_type='MONTHLY',
        period_start=period_start
    ).first()
    
    # Se não existir, criar um novo
    if not budget:
        budget = Budget.objects.create(
            user=user,
            period_type='MONTHLY',
            period_start=period_start,
            status='ACTIVE'
        )
        print(f"Novo orçamento criado: {budget}")
    
    return budget