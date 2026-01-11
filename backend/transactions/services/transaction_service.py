# backend/transactions/services/transaction_service.py
import logging
from decimal import Decimal
from django.utils import timezone
from django.db import transaction as db_transaction
from django.core.exceptions import ValidationError

# IMPORTAR TAG MODEL
from payments.models import PaymentMethod
from tags.models import Tag
from transactions.models import Transaction, TransactionAccount, TransactionTag
from accounts.models import Account
from .installment_service import create_installment_transactions
from recurrence.models import RecurrenceRule
from .balance_service import recalculate_account_balance, verify_account_balance
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

def validate_transaction_for_account(account, amount, direction):
    """
    Valida se a transação é válida para a conta.
    
    Regras:
    1. Contas normais: saldo não pode ficar negativo (a menos que permitido)
    2. Cartões de crédito: valor não pode exceder limite disponível
    """
    if not account.is_credit_card:
        # Para contas normais, verificar se há saldo suficiente para saída
        if direction == 'OUT' and account.balance < amount:
            raise ValidationError(
                f"Saldo insuficiente na conta {account.name}. "
                f"Saldo atual: {account.balance}, Valor necessário: {amount}"
            )
    else:
        # Para cartões de crédito, verificar limite
        available_credit = account.available_credit
        if direction == 'OUT' and amount > available_credit:
            raise ValidationError(
                f"Limite de crédito insuficiente no cartão {account.name}. "
                f"Crédito disponível: {available_credit}, Valor da compra: {amount}"
            )
            
def validate_payment_method_compatibility(payment_method_type, account_type):
    """
    Valida se o método de pagamento é compatível com o tipo de conta.
    
    Regras:
    - PIX, CASH, BANK_TRANSFER: Só podem ser usados com contas normais
    - CREDIT: Só pode ser usado com cartões de crédito
    - DEBIT: Pode ser usado com contas normais
    """
    COMPATIBILITY_RULES = {
        # Método de pagamento: Tipos de conta permitidos
        'PIX': ['CHECKING', 'SAVINGS', 'INVESTMENT', 'CASH', 'OTHER'],
        'CASH': ['CHECKING', 'SAVINGS', 'INVESTMENT', 'CASH', 'OTHER'],
        'BANK_TRANSFER': ['CHECKING', 'SAVINGS', 'INVESTMENT', 'OTHER'],
        'CREDIT': ['CREDIT_CARD'],  # Só cartão de crédito
        'DEBIT': ['CHECKING', 'SAVINGS', 'INVESTMENT', 'OTHER'],
        'BOLETO': ['CHECKING', 'SAVINGS', 'INVESTMENT', 'OTHER'],
        'CRYPTO': ['CHECKING', 'SAVINGS', 'INVESTMENT', 'OTHER'],
        'OTHER': ['CHECKING', 'SAVINGS', 'INVESTMENT', 'CASH', 'CREDIT_CARD', 'OTHER']
    }
    
    allowed_accounts = COMPATIBILITY_RULES.get(payment_method_type, [])
    
    return account_type in allowed_accounts

def create_transaction_service(
    user,
    amount: Decimal,
    direction: str,
    id_category,
    id_payment_method,
    id_account,
    origin: str = 'MANUAL',
    tags=None,
    currency: str = 'BRL',
    occurred_at=None,
    installments: int = None,
    interest_rate: Decimal = Decimal('0'),
    recurrence_frequency: str = None,
    max_recurrences: int = None,
    description: str = "",
):
    """
    Serviço unificado para criação de transações.
    
    GARANTE: Saldo da conta sempre reflete a soma das transações.
    """
    logger.debug(f"=== CREATE TRANSACTION SERVICE ===")
    logger.debug(f"Usuário: {user.username}")
    logger.debug(f"Direction: {direction}")
    logger.debug(f"Amount: {amount}")
    logger.debug(f"Origin: {origin}")
    
    if not occurred_at:
        occurred_at = timezone.now()
    
    # VALIDAÇÕES INICIAIS
    if origin not in ['MANUAL', 'INSTALLMENT', 'RECURRENT']:
        raise ValueError(f"Origem inválida: {origin}")
    
    if origin == 'INSTALLMENT' and (not installments or installments <= 1):
        origin = 'MANUAL'
    
    # OBTER OBJETO CONTA E MÉTODO DE PAGAMENTO
    if isinstance(id_account, Account):
        account_obj = id_account
    else:
        account_obj = Account.objects.get(pk=id_account, user=user)
    
    if isinstance(id_payment_method, PaymentMethod):
        payment_method_obj = id_payment_method
    else:
        payment_method_obj = PaymentMethod.objects.get(pk=id_payment_method, id_user=user)
        
    # VALIDAR COMPATIBILIDADE
    if not validate_payment_method_compatibility(
        payment_method_obj.type,
        account_obj.type
    ):
        raise ValidationError(
            f"Método de pagamento '{payment_method_obj.get_type_display()}' "
            f"não é compatível com conta do tipo '{account_obj.get_type_display()}'."
        )
    
    # VALIDAR TRANSAÇÃO PARA A CONTA
    validate_transaction_for_account(account_obj, amount, direction)
    
    # CONVERTER TAGS
    tag_objects = convert_tags_to_objects(tags or [], user)
    logger.debug(f"Tags convertidas: {[str(tag.id_tag) for tag in tag_objects]}")
    
    # VERIFICAR SALDO ANTES DA TRANSAÇÃO
    balance_before = account_obj.balance
    logger.debug(f"Saldo antes: {balance_before}")
    
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
        
        # Atualiza saldo apenas da primeira parcela (se já passou da data)
        if occurred_at.date() <= timezone.now().date():
            recalculate_account_balance(account_obj)
        
        return {
            'type': 'INSTALLMENT',
            'data': result,
            'message': f'Parcelamento criado: {installments}x de R${result["installment_amount"]:.2f}',
            'balance_before': balance_before,
            'balance_after': account_obj.balance
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
            tags=tag_objects,
            max_executions=max_recurrences,
            start_date=occurred_at.date()
        )
        
        # Atualiza saldo (primeira ocorrência)
        recalculate_account_balance(account_obj)
        
        return {
            'type': 'RECURRENT',
            'data': rule,
            'message': f'Recorrência {recurrence_frequency.lower()} criada',
            'balance_before': balance_before,
            'balance_after': account_obj.balance
        }
    
    else:
        # MANUAL - Transação atômica
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
                id_account=account,
                role=role
            )
            
            # Adiciona tags
            for tag in tag_objects:
                TransactionTag.objects.create(
                    id_transaction=transaction,
                    id_tag=tag
                )
            
            # ATUALIZA SALDO
            recalculate_account_balance(account)
            
            # VERIFICA CONSISTÊNCIA
            is_consistent, calculated_balance, stored_balance = verify_account_balance(account)
            
            if not is_consistent:
                logger.error(
                    f"INCONSISTÊNCIA DETECTADA após criação da transação {transaction.id_transaction}"
                )
                # Tenta corrigir
                account.balance = calculated_balance
                account.save(update_fields=['balance'])
            
            logger.info(f"Transação manual criada: {transaction.id_transaction}")
            logger.info(f"Saldo: {balance_before} -> {account.balance}")
            
            return {
                'type': 'MANUAL',
                'data': transaction,
                'message': 'Transação criada com sucesso',
                'balance_before': balance_before,
                'balance_after': account.balance,
                'is_consistent': is_consistent
            }