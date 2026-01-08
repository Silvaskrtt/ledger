# backend/transactions/services/transaction_service.py
import logging
from decimal import Decimal
from django.utils import timezone
from django.db import transaction as db_transaction
from transactions.models import Transaction, TransactionAccount, TransactionTag
from accounts.models import Account
from .installment_service import create_installment_transactions
from recurrence.models import RecurrenceRule
from .balance_service import recalculate_account_balance
from recurrence.services.recurrence_service import create_recurrence_rule

logger = logging.getLogger(__name__)

def create_transaction_service(
    user,
    amount: Decimal,
    direction: str,
    id_category,
    id_payment_method,
    id_account, # Este é um objeto Account (PrimaryKeyRelatedField)
    origin: str = 'MANUAL',
    tags=None,
    currency: str = 'BRL',
    occurred_at=None,
    # Campos específicos para parcelamento
    installments: int = None,
    interest_rate: Decimal = Decimal('0'),
    # Campos específicos para recorrência
    recurrence_frequency: str = None,
    max_recurrences: int = None,
    description: str = "",
):
    """
    Serviço unificado para criação de transações.
    
    Args:
        origin: 'MANUAL', 'INSTALLMENT', 'RECURRENT'
        installments: número de parcelas (apenas para INSTALLMENT)
        interest_rate: taxa de juros em % (apenas para INSTALLMENT)
        recurrence_frequency: frequência da recorrência (apenas para RECURRENT)
        max_recurrences: número máximo de ocorrências (apenas para RECURRENT)
    """
    if not occurred_at:
        occurred_at = timezone.now()
    
    # VALIDAÇÕES
    if origin not in ['MANUAL', 'INSTALLMENT', 'RECURRENT']:
        raise ValueError(f"Origem inválida: {origin}")
    
    if origin == 'INSTALLMENT' and (not installments or installments <= 1):
        origin = 'MANUAL'  # Se 1 parcela, trata como manual
    
    if isinstance(id_account, Account):
        account_obj = id_account
    else:
        # Se for um ID numérico, buscar o objeto
        try:
            account_obj = Account.objects.get(pk=id_account)
        except Account.DoesNotExist:
            raise ValueError(f"Conta com ID {id_account} não encontrada")
    
    # PROCESSAMENTO POR TIPO
    if origin == 'INSTALLMENT':
        # PARCELADO
        if not installments or installments < 2:
            raise ValueError("Parcelamento requer pelo menos 2 parcelas")
        
        result = create_installment_transactions(
            user=user,
            total_amount=amount,
            installments=installments,
            category=id_category,
            payment_method=id_payment_method,
            account=account_obj,
            tags=tags,
            interest_rate=interest_rate,
            start_date=occurred_at.date(),
            description=description
        )
        
        # Atualiza saldo da conta (apenas primeira parcela se já passou da data)
        if occurred_at.date() <= timezone.now().date():
            recalculate_account_balance(account_obj)
        
        return {
            'type': 'INSTALLMENT',
            'data': result,
            'message': f'Parcelamento criado: {installments}x de R${result["installment_amount"]:.2f}'
        }
    
    elif origin == 'RECURRENT':
        # RECORRENTE
        if not recurrence_frequency:
            raise ValueError("Recorrência requer uma frequência")
        
        rule = create_recurrence_rule(
            user=user,
            amount=amount,
            direction=direction,
            category=id_category,
            payment_method=id_payment_method,
            account=account_obj,
            frequency=recurrence_frequency,
            tags=tags,
            max_executions=max_recurrences,
            start_date=occurred_at.date()
        )
        
        # Atualiza saldo da conta (primeira ocorrência)
        recalculate_account_balance(account_obj)
        
        return {
            'type': 'RECURRENT',
            'data': rule,
            'message': f'Recorrência {recurrence_frequency.lower()} criada'
        }
    
    else:
        # MANUAL
        with db_transaction.atomic():
            # Bloqueia conta para evitar race conditions
            account = Account.objects.select_for_update().get(pk=account_obj.pk)
            
            # Cria transação
            transaction = Transaction.objects.create(
                id_user=user,
                id_category=id_category,
                id_payment_method=id_payment_method,
                amount=amount,
                direction=direction,
                currency=currency,
                origin=origin,
                occurred_at=occurred_at,
                description=description
            )
            
            # Relaciona com conta
            role = 'source' if direction == 'OUT' else 'destination'
            TransactionAccount.objects.create(
                id_transaction=transaction,
                id_account=account_obj,
                role=role
            )
            
            # Adiciona tags
            if tags:
                for tag in tags:
                    TransactionTag.objects.create(
                        id_transaction=transaction,
                        id_tag=tag
                    )
            
            # Atualiza saldo
            recalculate_account_balance(account_obj)
            
            logger.info(f"Transação manual criada: {transaction.id_transaction}")
            
            return {
                'type': 'MANUAL',
                'data': transaction,
                'message': 'Transação criada com sucesso'
            }