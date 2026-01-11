# services/patrimony_service.py
from django.db.models import Sum

from backend.categories import models

class PatrimonyService:
    
    @staticmethod
    def calculate_user_patrimony(user):
        """Calcula patrimônio completo do usuário."""
        from accounts.models import Account
        
        # Busca todas as contas de uma vez
        accounts = Account.objects.filter(user=user, is_active=True)
        
        # Agrega por tipo
        aggregates = accounts.aggregate(
            total_normal=Sum('balance', filter=models.Q(type__in=[
                'CHECKING', 'SAVINGS', 'INVESTMENT', 'CASH', 'OTHER'
            ])),
            total_credit_cards=Sum('balance', filter=models.Q(type='CREDIT_CARD'))
        )
        
        patrimonio_contas = aggregates['total_normal'] or 0
        total_credit_cards = aggregates['total_credit_cards'] or 0
        
        return {
            'patrimony_normal': patrimonio_contas,
            'patrimony_credit_cards': total_credit_cards,  # NEGATIVO
            'total_patrimony': patrimonio_contas + total_credit_cards,
            'credit_card_debt_abs': abs(total_credit_cards)  # Para exibição
        }