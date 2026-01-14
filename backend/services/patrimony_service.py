# services/patrimony_service.py

from django.db.models import Sum, Q
from accounts.models import Account
from categories import models

class PatrimonyService:
    
    @staticmethod
    def calculate_user_patrimony(user):
        """Calcula patrimônio completo do usuário."""
        
        # Busca todas as contas de uma vez
        accounts = Account.objects.filter(user=user, is_active=True)
        
        # Agrega por tipo usando Q objects do Django
        aggregates = accounts.aggregate(
            total_normal=Sum('balance', filter=Q(type__in=[
                'CHECKING', 'SAVINGS', 'INVESTMENT', 'CASH', 'OTHER'
            ])),
            total_credit_cards=Sum('balance', filter=Q(type='CREDIT_CARD'))
        )
        
        patrimonio_contas = aggregates['total_normal'] or 0
        total_credit_cards = aggregates['total_credit_cards'] or 0
        
        return {
            'patrimony_normal': float(patrimonio_contas),
            'patrimony_credit_cards': float(total_credit_cards),  # NEGATIVO
            'total_patrimony': float(patrimonio_contas + total_credit_cards),
            'credit_card_debt_abs': float(abs(total_credit_cards))  # Para exibição
        }