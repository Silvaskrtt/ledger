# backend/transactions/services/transaction_service.py
import logging
from decimal import Decimal
from django.utils import timezone
from django.db import transaction as db_transaction

# IMPORTAR TAG MODEL
from tags.models import Tag
from transactions.models import Transaction, TransactionAccount, TransactionTag
from accounts.models import Account
from .installment_service import create_installment_transactions
from recurrence.models import RecurrenceRule
from .balance_service import recalculate_account_balance
from recurrence.services.recurrence_service import create_recurrence_rule

logger = logging.getLogger(__name__)

def convert_tags_to_objects(tags, user):
    """
    Converte tags (que podem ser IDs ou objetos Tag) em objetos Tag.
    
    Args:
        tags: Lista de UUIDs (strings) ou objetos Tag
        user: Usuário para filtrar tags
    
    Returns:
        Lista de objetos Tag
    """
    if not tags:
        return []
    
    # Se já são objetos Tag
    if hasattr(tags[0], 'id_tag'):
        # Verificar se todas pertencem ao usuário
        for tag in tags:
            if tag.id_user != user:
                raise ValueError(f"A tag '{tag.name}' não pertence ao usuário {user.username}")
        return tags
    
    # Se são IDs (strings ou UUIDs)
    tag_objects = []
    for tag_id in tags:
        try:
            tag = Tag.objects.get(id_tag=tag_id, id_user=user)
            tag_objects.append(tag)
        except Tag.DoesNotExist:
            raise ValueError(f"Tag com ID {tag_id} não encontrada para o usuário {user.username}")
    
    return tag_objects

def create_transaction_service(
    user,
    amount: Decimal,
    direction: str,
    id_category,
    id_payment_method,
    id_account,  # Este é um objeto Account (PrimaryKeyRelatedField)
    origin: str = 'MANUAL',
    tags=None,  # Pode ser lista de UUIDs (strings) ou objetos Tag
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
    logger.debug(f"=== CREATE TRANSACTION SERVICE ===")
    logger.debug(f"Usuário: {user.username}")
    logger.debug(f"Origin: {origin}")
    logger.debug(f"Tags recebidas: {tags}")
    logger.debug(f"Tipo das tags: {type(tags)}")
    
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
        
    # CONVERTER TAGS para objetos Tag - PARA TODOS OS TIPOS!
    tag_objects = convert_tags_to_objects(tags or [], user)
    logger.debug(f"Tags convertidas: {[str(tag.id_tag) for tag in tag_objects]}")
    
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
            tags=tag_objects,
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
            tags=tag_objects,  # Passar objetos Tag - VARIÁVEL CORRETA
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
            for tag in tag_objects:
                TransactionTag.objects.create(
                    id_transaction=transaction,
                    id_tag=tag
                )
                logger.debug(f"Tag '{tag.name}' adicionada à transação")
                
            # Atualiza saldo
            recalculate_account_balance(account_obj)
            
            logger.info(f"Transação manual criada: {transaction.id_transaction}")            
            
            return {
                'type': 'MANUAL',
                'data': transaction,
                'message': 'Transação criada com sucesso'
            }