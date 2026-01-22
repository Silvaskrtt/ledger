# backend/services/credit_card_service.py

import logging
from decimal import Decimal
from django.utils import timezone
from django.db import transaction as db_transaction
from django.db.models import Sum, Q
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from accounts.models import Account, CreditCardBill, CreditCardPayment
from transactions.models import Transaction, TransactionAccount, TransactionTag
from transactions.services.balance_service import recalculate_account_balance
from categories.models import Category
from payments.models import PaymentMethod

logger = logging.getLogger(__name__)

class CreditCardService:
    
    @staticmethod
    def generate_credit_card_bills(card, start_date=None, end_date=None):
        """
        Gera faturas para um cartão de crédito baseado nas transações.
        CORRIGIDO: Agora vincula transações mesmo se fatura já existir.
        """
        if not card.is_credit_card:
            raise ValueError("Apenas cartões de crédito podem gerar faturas")
        
        if not card.closing_day:
            raise ValueError("Cartão não tem dia de fechamento configurado")
        
        if not card.due_day:
            raise ValueError("Cartão não tem dia de vencimento configurado")
        
        if not start_date:
            # Data da primeira transação do cartão
            first_transaction = Transaction.objects.filter(
                transaction_accounts__account=card,
                direction='OUT',
                is_deleted=False
            ).order_by('occurred_at').first()
            
            if first_transaction:
                start_date = first_transaction.occurred_at.date()
            else:
                start_date = timezone.now().date()
        
        if not end_date:
            end_date = timezone.now().date() + relativedelta(months=3)
        
        bills_created = []
        current_date = start_date
        
        while current_date <= end_date:
            # Calcular datas do ciclo
            bill_start_date, bill_end_date, due_date = CreditCardService.calculate_bill_dates(
                current_date, card.closing_day, card.due_day
            )
            
            # Buscar TODAS as transações do período (INCLUINDO as já vinculadas)
            all_transactions = Transaction.objects.filter(
                transaction_accounts__account=card,
                occurred_at__date__range=[bill_start_date, bill_end_date],
                direction='OUT',
                is_deleted=False
            )
            
            # Calcular total baseado em TODAS as transações
            total_amount = sum(t.amount for t in all_transactions)
            
            if total_amount > 0:
                # Calcular pagamento mínimo (10% do total, mínimo R$ 0.01)
                minimum_payment = max(
                    Decimal('0.01'),
                    (total_amount * Decimal('0.10')).quantize(Decimal('0.01'))
                )
            
                # Garantir que minimum_payment nunca seja maior que total_amount
                minimum_payment = min(minimum_payment, total_amount)
            
                # Buscar ou criar fatura
                bill, created = CreditCardBill.objects.get_or_create(
                    credit_card=card,
                    start_date=bill_start_date,
                    end_date=bill_end_date,
                    defaults={
                        'due_date': due_date,
                        'total_amount': total_amount,
                        'minimum_payment': minimum_payment,
                        'status': 'OPEN'
                    }
                )
                
                if not created:
                    # Se fatura já existe, atualizar valores
                    bill.total_amount = total_amount
                    bill.due_date = due_date
                    bill.minimum_payment = minimum_payment
                    bill.save(update_fields=['total_amount', 'due_date', 'minimum_payment'])
                
                # Vincular transações que não estão vinculadas
                unlinked_transactions = all_transactions.filter(credit_card_bill__isnull=True)
                
                if unlinked_transactions.exists():
                    unlinked_transactions.update(credit_card_bill=bill)
                    logger.info(f"Vinculadas {unlinked_transactions.count()} transações à fatura {bill.end_date}")
                
                if created:
                    bills_created.append(bill)
                    logger.info(f"Fatura criada: {bill} - R${total_amount} (mínimo: R${minimum_payment})")
            
            current_date = bill_end_date + timedelta(days=1)
        
        return bills_created
    
    @staticmethod
    def calculate_bill_dates(reference_date, closing_day, due_day):
        """
        Calcula datas do ciclo da fatura.
        """
        logger.debug(f"=== DEBUG CALCULATE_BILL_DATES ===")
        logger.debug(f"Reference date: {reference_date}")
        logger.debug(f"Closing day: {closing_day}")
        logger.debug(f"Due day: {due_day}")
        
        # Data de fechamento deste mês
        if reference_date.day <= closing_day:
            # Fechamento ainda não ocorreu este mês
            end_date = reference_date.replace(day=closing_day)
            start_date = (end_date - relativedelta(months=1)).replace(day=1)
        else:
            # Próximo fechamento
            next_month = reference_date + relativedelta(months=1)
            end_date = next_month.replace(day=closing_day)
            start_date = reference_date.replace(day=1)
        
        # Data de vencimento (geralmente 7-10 dias após fechamento)
        due_date = end_date + timedelta(days=7)
        
        logger.debug(f"Start date: {start_date}")
        logger.debug(f"End date: {end_date}")
        logger.debug(f"Due date: {due_date}")
        
        return start_date, end_date, due_date
    
    @staticmethod
    @db_transaction.atomic
    def pay_bill(bill_id, payment_account_id, amount, user, notes=None, create_transaction=True):
        """
        Processa pagamento de uma fatura.
        """
        try:
            from decimal import Decimal
        
            # Garantir que amount seja Decimal
            if not isinstance(amount, Decimal):
                amount = Decimal(str(amount))
                
            # Buscar fatura
            bill = CreditCardBill.objects.select_for_update().get(
                id_bill=bill_id,
                credit_card__user=user
            )
            
            # Buscar conta de pagamento
            payment_account = Account.objects.select_for_update().get(
                account=payment_account_id,
                user=user,
                type__in=['CHECKING', 'SAVINGS', 'CASH']  # Contas que podem pagar faturas
            )
            
            # Validar valores
            if amount <= 0:
                raise ValueError("Valor do pagamento deve ser positivo")
            
            if amount > bill.total_amount - bill.paid_amount:
                raise ValueError("Valor do pagamento excede o valor em aberto da fatura")
            
            # Validar saldo da conta de pagamento
            if payment_account.balance < amount:
                raise ValueError(f"Saldo insuficiente na conta {payment_account.name}")
            
            transaction = None
            
            if create_transaction:
                # Criar transação para o pagamento
                transaction = Transaction.objects.create(
                    user=user,
                    amount=amount,
                    direction='OUT',
                    currency='BRL',
                    origin='MANUAL',
                    occurred_at=timezone.now(),
                    description=f"Pagamento fatura {bill.credit_card.name} {bill.end_date.strftime('%m/%Y')}",
                    category=Category.objects.get_or_create(
                        user=user,
                        name='Pagamento de Faturas',
                        defaults={'color': '#EF4444'}
                    )[0],
                    payment_method=PaymentMethod.objects.get_or_create(
                        user=user,
                        type='BANK_TRANSFER',
                        defaults={'description': 'Transferência para pagar fatura'}
                    )[0]
                )
                
                logger.info(f"Transação de pagamento criada:")
                logger.info(f"  ID: {transaction.transaction}")
                logger.info(f"  Direction: {transaction.direction}")
                logger.info(f"  Valor: {transaction.amount}")
                logger.info(f"  Cartão: {bill.credit_card.name}")
                logger.info(f"  Saldo anterior do cartão: {bill.credit_card.balance}")
                
                # Relacionar com conta de pagamento (source)
                TransactionAccount.objects.create(
                    transaction=transaction,
                    account=payment_account,
                    role='source'
                )
                
                # Relacionar com cartão de crédito (destination - entrada no cartão)
                TransactionAccount.objects.create(
                    transaction=transaction,
                    account=bill.credit_card,
                    role='destination'  # Entrada no cartão
                )
            
            # Criar registro de pagamento
            payment = CreditCardPayment.objects.create(
                bill=bill,
                payment_account=payment_account,
                amount=amount,
                transaction=transaction,
                notes=notes
            )
            
            # Atualizar fatura
            bill.paid_amount += amount
            
            # Verificar se fatura foi totalmente paga
            if bill.paid_amount >= bill.total_amount:
                bill.status = 'PAID'
            elif timezone.now().date() > bill.due_date:
                bill.status = 'OVERDUE'
            else:
                bill.status = 'CLOSED'
            
            bill.save()
            
            # Recalcular saldos
            recalculate_account_balance(payment_account)
            recalculate_account_balance(bill.credit_card)
            
            bill.credit_card.refresh_from_db()
            new_balance = bill.credit_card.balance
            
            old_balance = new_balance + amount
            
            logger.info(f"Saldo do cartão {bill.credit_card.name}:")
            logger.info(f"  Antes: {old_balance}")
            logger.info(f"  Depois: {new_balance}")
            logger.info(f"  Diferença: {new_balance - old_balance}")
            
            # Verificar consistência
            from transactions.services.balance_service import verify_account_balance
            is_consistent, calculated, stored = verify_account_balance(bill.credit_card)
            
            if not is_consistent:
                logger.error(f"INCONSISTÊNCIA no cartão {bill.credit_card.name}")
                logger.error(f"  Calculado: {calculated}")
                logger.error(f"  Armazenado: {stored}")
            
            # Verificar consistência do patrimônio
            from services.patrimony_service import PatrimonyService
            patrimony = PatrimonyService.calculate_user_patrimony(user)
            
            logger.info(f"Pagamento processado: {payment.id_payment} - R${amount}")
            
            return {
                'payment': payment,
                'transaction': transaction,
                'bill': bill,
                'patrimony': patrimony,
                'message': f'Pagamento de R${amount:.2f} realizado com sucesso!'
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar pagamento: {str(e)}")
            raise
    
    @staticmethod
    def get_card_bills(card_id, user):
        """
        Obtém todas as faturas de um cartão.
        """
        try:
            card = Account.objects.get(account=card_id, user=user)
            
            # PRIMEIRO: Garantir que faturas existem para transações não vinculadas
            unlinked_transactions = Transaction.objects.filter(
                transaction_accounts__account=card,
                direction='OUT',
                is_deleted=False,
                credit_card_bill__isnull=True,
                occurred_at__lte=timezone.now().date() + timedelta(days=60)
            )
            
            if unlinked_transactions.exists():
                # Gerar faturas para transações não vinculadas
                CreditCardService.generate_credit_card_bills(card)
            
            # SEGUNDO: Atualizar totais e status de todas as faturas
            bills = CreditCardBill.objects.filter(
                credit_card=card
            ).order_by('-end_date')
            
            for bill in bills:
                # Calcular total REAL baseado nas transações
                transactions_total = Transaction.objects.filter(
                    credit_card_bill=bill,
                    is_deleted=False
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
                
                # Se não há transações, usar valor atual
                if transactions_total == 0:
                    transactions_total = bill.total_amount
                
                # Atualizar se diferente
                if bill.total_amount != transactions_total:
                    bill.total_amount = transactions_total
                    
                    # Recalcular pagamento mínimo apenas se total > 0
                    if transactions_total > 0:
                        minimum_payment = max(
                            Decimal('0.01'),
                            (bill.total_amount * Decimal('0.10')).quantize(Decimal('0.01'))
                        )
                        minimum_payment = min(minimum_payment, bill.total_amount)
                        bill.minimum_payment = minimum_payment
                    else:
                        bill.minimum_payment = Decimal('0.00')
                    
                    bill.save(update_fields=['total_amount', 'minimum_payment'])
                
                # Atualizar status
                if bill.status != 'PAID':
                    if bill.paid_amount >= bill.total_amount:
                        bill.status = 'PAID'
                    elif timezone.now().date() > bill.due_date:
                        bill.status = 'OVERDUE'
                    elif bill.total_amount > 0:
                        bill.status = 'OPEN'
                    else:
                        bill.status = 'CLOSED'
                    
                    bill.save(update_fields=['status'])
            
            return bills
            
        except Account.DoesNotExist:
            raise ValueError("Cartão não encontrado")
        except Exception as e:
            logger.error(f"Erro ao obter faturas: {str(e)}")
            raise