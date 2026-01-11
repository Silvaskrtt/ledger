# backend/recurrence/services/recurrence_service.py

import logging
from decimal import Decimal
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db import transaction as db_transaction
import uuid

from transactions.models import Transaction, TransactionAccount, TransactionTag
from accounts.models import Account

logger = logging.getLogger(__name__)

def calculate_next_execution(frequency, last_execution=None):
    """
    Calcula próxima data de execução baseada na frequência.
    """
    if not last_execution:
        last_execution = timezone.now().date()
    
    if frequency == 'DAILY':
        return last_execution + timedelta(days=1)
    elif frequency == 'WEEKLY':
        return last_execution + timedelta(weeks=1)
    elif frequency == 'BIWEEKLY':
        return last_execution + timedelta(weeks=2)
    elif frequency == 'MONTHLY':
        return last_execution + relativedelta(months=1)
    elif frequency == 'QUARTERLY':
        return last_execution + relativedelta(months=3)
    elif frequency == 'SEMIANNUAL':
        return last_execution + relativedelta(months=6)
    elif frequency == 'ANNUAL':
        return last_execution + relativedelta(years=1)
    else:
        return last_execution + timedelta(days=30)  # default

def create_recurrence_rule(
    user,
    amount: Decimal,
    direction: str,
    category,
    payment_method,
    account,
    frequency: str,
    tags=None,
    max_executions=None,
    start_date=None
):
    """
    Cria uma regra de recorrência.
    """
    if not start_date:
        start_date = timezone.now().date()
    
    next_execution = calculate_next_execution(frequency, start_date)
    
    recurrence_rule = RecurrenceRule.objects.create(
        recurrence_rule=uuid.uuid4(),
        frequency=frequency,
        next_execution=next_execution,
        max_executions=max_executions,
        executions_count=0,
        amount=amount,
        direction=direction,
        user=user,
        category=category,
        payment_method=payment_method,
        account=account
    )
    
    # Cria primeira transação
    create_recurrence_transaction(recurrence_rule)
    
    # Adicionar tags à primeira transação
    if tags and transaction:
        for tag in tags:
            TransactionTag.objects.create(
                transaction=transaction,
                tag=tag  # tag já é objeto Tag
            )
    
    return recurrence_rule

def create_recurrence_transaction(recurrence_rule):
    """
    Cria uma transação baseada em uma regra de recorrência.
    """
    # Verifica se atingiu limite de execuções
    if (recurrence_rule.max_executions and 
        recurrence_rule.executions_count >= recurrence_rule.max_executions):
        logger.info(f"Regra {recurrence_rule.recurrence_rule} atingiu limite de execuções")
        return None
    
    with db_transaction.atomic():
        # Cria transação
        transaction = Transaction.objects.create(
            transaction=uuid.uuid4(),
            user=recurrence_rule.user,
            category=recurrence_rule.category,
            payment_method=recurrence_rule.payment_method,
            amount=recurrence_rule.amount,
            direction=recurrence_rule.direction,
            currency='BRL',
            origin='RECURRENT',
            occurred_at=timezone.make_aware(
                datetime.combine(recurrence_rule.next_execution, datetime.min.time())
            )
        )
        
        # Relaciona com conta
        role = 'source' if recurrence_rule.direction == 'OUT' else 'destination'
        
        # Validar que conta pertence ao mesmo user
        if recurrence_rule.account.user != recurrence_rule.user:
            raise ValueError("Conta não pertence ao usuário da regra de recorrência")
        
        TransactionAccount.objects.create(
            transaction=transaction,
            account=recurrence_rule.account,
            role=role
        )
        
        # Atualiza regra de recorrência
        recurrence_rule.executions_count += 1
        recurrence_rule.next_execution = calculate_next_execution(
            recurrence_rule.frequency, recurrence_rule.next_execution
        )
        recurrence_rule.save()
        
        logger.info(f"Transação recorrente criada: {transaction.transaction}")
        return transaction

def process_pending_recurrences():
    """
    Processa todas as recorrências pendentes.
    Deve ser executado periodicamente (cron job).
    """
    today = timezone.now().date()
    pending_rules = RecurrenceRule.objects.filter(
        next_execution__lte=today
    )
    
    created_count = 0
    for rule in pending_rules:
        try:
            transaction = create_recurrence_transaction(rule)
            if transaction:
                created_count += 1
        except Exception as e:
            logger.error(f"Erro ao processar recorrência {rule.recurrence_rule}: {str(e)}")
    
    logger.info(f"Processadas {created_count} transações recorrentes")
    return created_count