from django.db.models import Sum, Q
from django.utils.timezone import now
from accounts.models import Account
from transactions.models import Transaction

class SummaryService:
    """Serviço unificado para todos os dados de resumo financeiro"""
    
    @staticmethod
    def get_summary_data(user, year=None, month=None):
        """
        Retorna TODOS os dados necessários para os cards de resumo.
        Se year/month não forem informados, usa o mês atual.
        """
        today = now()
        current_year = year if year else today.year
        current_month = month if month else today.month
        
        # ===== MÊS ANTERIOR =====
        if current_month == 1:
            prev_month = 12
            prev_year = current_year - 1
        else:
            prev_month = current_month - 1
            prev_year = current_year
        
        # ===== 1. PATRIMÔNIO TOTAL =====
        patrimonio_contas = (
            Account.objects
            .filter(
                user=user, 
                is_active=True,
                type__in=['CHECKING', 'SAVINGS', 'INVESTMENT', 'CASH', 'OTHER']
            )
            .aggregate(total=Sum('balance'))['total'] or 0
        )
        
        # ===== 2. DÉBITO EM CARTÕES =====
        sum_credit_cards = (
            Account.objects
            .filter(user=user, is_active=True, type='CREDIT_CARD')
            .aggregate(total=Sum('balance'))['total'] or 0
        )
        
        debito_absoluto = abs(sum_credit_cards)
        total_patrimonio = patrimonio_contas + sum_credit_cards
        saldo_atual = patrimonio_contas
        
        # ===== 3. TOTAL INVESTIDO =====
        total_investido = (
            Account.objects
            .filter(user=user, is_active=True, type='INVESTMENT')
            .aggregate(total=Sum('balance'))['total'] or 0
        )
        
        # ===== 4. TRANSAÇÕES DO MÊS ATUAL =====
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
        
        # ===== 5. TRANSAÇÕES DO MÊS ANTERIOR =====
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
        
        # ===== 6. VARIAÇÕES PERCENTUAIS =====
        if entradas_mes_anterior > 0:
            variacao_receitas = ((entradas_mes - entradas_mes_anterior) / entradas_mes_anterior) * 100
        else:
            variacao_receitas = 100 if entradas_mes > 0 else 0
        
        if saidas_mes_anterior > 0:
            variacao_despesas = ((saidas_mes - saidas_mes_anterior) / saidas_mes_anterior) * 100
        else:
            variacao_despesas = 100 if saidas_mes > 0 else 0
        
        # ===== 7. ORÇAMENTO (placeholder) =====
        orcamento_mes = 0
        
        return {
            # Patrimônio
            'total_patrimonio': total_patrimonio,
            'saldo_atual': saldo_atual,
            'debito_cartoes': debito_absoluto,
            'total_investido': total_investido,
            
            # Receitas e despesas
            'entradas_mes': entradas_mes,
            'saidas_mes': saidas_mes,
            'entradas_mes_anterior': entradas_mes_anterior,
            'saidas_mes_anterior': saidas_mes_anterior,
            
            # Variações
            'variacao_receitas': variacao_receitas,
            'variacao_despesas': variacao_despesas,
            
            # Orçamento
            'orcamento_mes': orcamento_mes,
            
            # Flags
            'tem_historico_anterior': entradas_mes_anterior > 0 or saidas_mes_anterior > 0,
        }