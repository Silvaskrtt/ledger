# backend/transactions/services/installment_service.py

import logging
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction as db_transaction
from transactions.models import Transaction, TransactionAccount, TransactionTag
from accounts.models import Account
from payments.models import InstallmentPlan
import uuid

logger = logging.getLogger(__name__)

def calculate_installment_amount(total_amount: Decimal, installments: int, interest_rate: Decimal = Decimal('0')) -> Decimal:
    """
    Calcula o valor de cada parcela.
    
    Sem juros: valor total / número de parcelas
    Com juros: cálculo de prestação fixa com juros compostos
    """
    if installments <= 0:
        raise ValueError("Número de parcelas deve ser maior que zero")
    
    if total_amount <= 0:
        raise ValueError("Valor total deve ser maior que zero")
    
    # Sem juros
    if interest_rate == Decimal('0'):
        installment = total_amount / Decimal(str(installments))
        return installment.quantize(Decimal('0.01'))
    
    # Com juros - fórmula de prestação fixa
    # PMT = PV * [i(1+i)^n] / [(1+i)^n - 1]
    monthly_rate = interest_rate / Decimal('100') / Decimal('12')
    
    numerator = monthly_rate * (Decimal('1') + monthly_rate) ** installments
    denominator = (Decimal('1') + monthly_rate) ** installments - Decimal('1')
    
    installment = total_amount * (numerator / denominator)
    return installment.quantize(Decimal('0.01'))

def create_installment_transactions(
    user,
    total_amount: Decimal,
    installments: int,
    category,
    payment_method,
    account,
    tags=None,
    interest_rate: Decimal = Decimal('0'),
    start_date=None,
    description: str = ""
):
    """
    Cria transações parceladas automaticamente.
    
    Gera N transações, uma para cada parcela, com datas espaçadas de 30 dias.
    """
    if not start_date:
        start_date = timezone.now().date()
    
    # Calcula valor da parcela
    installment_amount = calculate_installment_amount(
        total_amount, installments, interest_rate
    )
    
    created_transactions = []
    
    try:
        # Cria plano de parcelamento
        installment_plan = InstallmentPlan.objects.create(
            installment_plan=uuid.uuid4(),
            total_amount=total_amount,
            installments=installments,
            start_date=start_date,
            user=user,
            account=account,
            category=category
        )
        
        # Gera transações para cada parcela
        for i in range(1, installments + 1):
            # Data da parcela (30 dias entre cada)
            parcel_date = start_date + timedelta(days=30 * (i - 1))
            
            # Cria transação
            transaction = Transaction.objects.create(
                transaction=uuid.uuid4(),
                user=user,
                category=category,
                payment_method=payment_method,
                installment_plan=installment_plan,
                amount=installment_amount,
                direction='OUT',  # Parcelas são sempre despesas
                currency='BRL',
                origin='INSTALLMENT',
                occurred_at=timezone.make_aware(
                    datetime.combine(parcel_date, datetime.min.time())
                ),
                installment_number=i,
                total_installments=installments,
                description=description 
            )
            
            # Relaciona com conta
            TransactionAccount.objects.create(
                transaction=transaction,
                account=account,
                role='source'
            )
            
            # Adiciona tags
            if tags:
                for tag in tags:
                    TransactionTag.objects.create(
                        transaction=transaction,
                        tag=tag
                    )
            
            created_transactions.append(transaction)
            logger.info(f"Parcela {i}/{installments} criada: R${installment_amount}")
        
        return {
            'installment_plan': installment_plan,
            'transactions': created_transactions,
            'installment_amount': installment_amount,
            'total_with_interest': installment_amount * installments
        }
        
    except Exception as e:
        logger.error(f"Erro ao criar parcelamento: {str(e)}")
        raise

def cancel_installment_plan(installment_plan_id, user):
    """
    Cancela parcelamentos futuros.
    """
    try:
        plan = InstallmentPlan.objects.get(
            installment_plan=installment_plan_id,
            user=user
        )
        
        # Encontra transações futuras
        future_transactions = Transaction.objects.filter(
            installment_plan=plan,
            occurred_at__gt=timezone.now()
        )
        
        # Marca como canceladas ou deleta
        deleted_count, _ = future_transactions.delete()
        
        logger.info(f"Canceladas {deleted_count} parcelas futuras")
        return True
        
    except InstallmentPlan.DoesNotExist:
        logger.error(f"Plano de parcelamento não encontrado: {installment_plan_id}")
        return False