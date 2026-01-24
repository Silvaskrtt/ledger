# backend/services/credit_card_service.py

import logging
from decimal import Decimal
from django.utils import timezone
from django.db import transaction as db_transaction
from django.db.models import Sum, Q
from datetime import timedelta
from dateutil.relativedelta import relativedelta

# Importar Transaction corretamente
from transactions.models import Transaction, TransactionAccount
from transactions.services.balance_service import recalculate_account_balance

# Importar modelos de outras apps
from categories.models import Category
from payments.models import PaymentMethod
from accounts.models import Account, CreditCardBill, CreditCardPayment

logger = logging.getLogger(__name__)

class CreditCardService:
    
    @staticmethod
    def generate_credit_card_bills(card, start_date=None, end_date=None):
        """
        Gera faturas APENAS com transações de COMPRA (PURCHASE).
        """
        if not card.is_credit_card:
            raise ValueError("Apenas cartões de crédito podem gerar faturas")
        
        if not card.closing_day:
            raise ValueError("Cartão não tem dia de fechamento configurado")
        
        if not card.due_day:
            raise ValueError("Cartão não tem dia de vencimento configurado")
        
        if not start_date:
            # Data da primeira COMPRA (PURCHASE) do cartão
            first_purchase = Transaction.objects.filter(
                transaction_accounts__account=card,
                transaction_type='PURCHASE',  # ← Alterado para transaction_type
                is_deleted=False
            ).order_by('occurred_at').first()
            
            if first_purchase:
                start_date = first_purchase.occurred_at.date()
            else:
                start_date = timezone.now().date()
        
        if not end_date:
            end_date = timezone.now().date() + relativedelta(months=3)
        
        bills_created = []
        current_date = start_date
        
        while current_date <= end_date:
            bill_start_date, bill_end_date, due_date = CreditCardService.calculate_bill_dates(
                current_date, card.closing_day, card.due_day
            )
            
            # Buscar APENAS transações de COMPRA do período (não vinculadas)
            purchase_transactions = Transaction.objects.filter(
                transaction_accounts__account=card,
                occurred_at__date__range=[bill_start_date, bill_end_date],
                transaction_type='PURCHASE',  # ← APENAS compras
                is_deleted=False,
                credit_card_bill__isnull=True  # Apenas não vinculadas
            )
            
            # Calcular total baseado em COMPRAS
            total_amount = sum(t.amount for t in purchase_transactions)
            
            if total_amount > 0:
                # Calcular pagamento mínimo
                minimum_payment = max(
                    Decimal('0.01'),
                    (total_amount * Decimal('0.10')).quantize(Decimal('0.01'))
                )
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
                
                # Vincular APENAS transações de compra que não estão vinculadas
                if purchase_transactions.exists():
                    purchase_transactions.update(credit_card_bill=bill)
                    logger.info(f"Vinculadas {purchase_transactions.count()} compras à fatura {bill.end_date}")
                
                if created:
                    bills_created.append(bill)
                    logger.info(f"Fatura criada: {bill} - R${total_amount} (mínimo: R${minimum_payment})")
            
            current_date = bill_end_date + timedelta(days=1)
        
        return bills_created
    
    @staticmethod
    def calculate_bill_dates(reference_date, closing_day, due_day):
        """Calcula datas do ciclo da fatura."""
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
        Padrão: Só cria transação SE solicitado.
        """
        try:
            from decimal import Decimal
            
            # Garantir que amount seja Decimal
            if not isinstance(amount, Decimal):
                amount = Decimal(str(amount))
                
            # Buscar fatura com lock
            bill = CreditCardBill.objects.select_for_update().get(
                id_bill=bill_id,
                credit_card__user=user
            )
            
            # Buscar conta de pagamento com lock
            payment_account = Account.objects.select_for_update().get(
                account=payment_account_id,
                user=user,
                type__in=['CHECKING', 'SAVINGS', 'CASH']
            )
            
            # Validar valores
            if amount <= 0:
                raise ValueError("Valor do pagamento deve ser positivo")
            
            # Verificar se o pagamento não excede o total
            pending_amount = bill.total_amount - bill.paid_amount
            if amount > pending_amount:
                raise ValueError(
                    f"Valor do pagamento excede o valor em aberto da fatura. "
                    f"Total: R${bill.total_amount}, "
                    f"Pago: R${bill.paid_amount}, "
                    f"Pendente: R${pending_amount}, "
                    f"Máximo permitido: R${pending_amount}"
                )
            
            transaction = None
            
            # ============================================================
            # 1. CRIAR TRANSAÇÃO APENAS SE SOLICITADO
            # ============================================================
            if create_transaction:
                from categories.models import Category
                from payments.models import PaymentMethod
                
                # Buscar categoria
                payment_category, _ = Category.objects.get_or_create(
                    user=user,
                    name='Pagamento de Faturas',
                    defaults={'color': '#EF4444'}
                )
                
                # Buscar método de pagamento
                payment_method, _ = PaymentMethod.objects.get_or_create(
                    user=user,
                    type='BANK_TRANSFER',
                    defaults={'description': 'Transferência para pagar fatura'}
                )
                
                # Criar transação de pagamento
                transaction = Transaction.objects.create(
                    user=user,
                    amount=amount,
                    transaction_type='CREDIT_CARD_PAYMENT',  # ← FIXO
                    direction='OUT',  # Dinheiro saindo da conta
                    currency='BRL',
                    origin='MANUAL',
                    occurred_at=timezone.now(),
                    description=f"Pagamento fatura {bill.credit_card.name} {bill.end_date.strftime('%m/%Y')}",
                    category=payment_category,
                    payment_method=payment_method,
                    credit_card_bill=bill  # Vincular à fatura
                )
                
                # Relacionar com contas
                TransactionAccount.objects.create(
                    transaction=transaction,
                    account=payment_account,
                    role='source'  # Dinheiro saindo desta conta
                )
                
                TransactionAccount.objects.create(
                    transaction=transaction,
                    account=bill.credit_card,
                    role='destination'  # Pagamento entrando no cartão (reduz dívida)
                )
            
            # ============================================================
            # 2. SEMPRE criar registro de pagamento
            # ============================================================
            payment = CreditCardPayment.objects.create(
                bill=bill,
                payment_account=payment_account,
                amount=amount,
                transaction=transaction,  # Pode ser None se não criou transação
                notes=notes,
                paid_at=timezone.now()
            )
            
            # ============================================================
            # 3. ATUALIZAR FATURA
            # ============================================================
            bill.paid_amount += amount
            
            # Atualizar status
            if bill.paid_amount >= bill.total_amount:
                bill.status = 'PAID'
            elif timezone.now().date() > bill.due_date:
                bill.status = 'OVERDUE'
            else:
                bill.status = 'CLOSED'
            
            bill.save(update_fields=['paid_amount', 'status'])
            
            # ============================================================
            # 4. RECALCULAR SALDOS (IMPORTANTE!)
            # ============================================================
            from transactions.services.balance_service import recalculate_account_balance
            
            # Recalcular conta de pagamento
            recalculate_account_balance(payment_account)
            
            # Recalcular cartão de crédito
            recalculate_account_balance(bill.credit_card)
            
            # ============================================================
            # 5. VERIFICAR CONSISTÊNCIA
            # ============================================================
            from transactions.services.balance_service import verify_account_balance
            
            # Verificar conta de pagamento
            is_consistent_payment, calc_payment, stored_payment = verify_account_balance(payment_account)
            
            # Verificar cartão
            is_consistent_card, calc_card, stored_card = verify_account_balance(bill.credit_card)
            
            if not is_consistent_payment or not is_consistent_card:
                logger.error(f"INCONSISTÊNCIA após pagamento:")
                if not is_consistent_payment:
                    logger.error(f"  Conta {payment_account.name}: Armazenado={stored_payment}, Calculado={calc_payment}")
                if not is_consistent_card:
                    logger.error(f"  Cartão {bill.credit_card.name}: Armazenado={stored_card}, Calculado={calc_card}")
            
            # ============================================================
            # 6. RETORNAR RESULTADO
            # ============================================================
            return {
                'payment': payment,
                'transaction': transaction,  # Pode ser None
                'bill': bill,
                'message': f'Pagamento de R${amount:.2f} realizado com sucesso!'
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar pagamento: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def get_card_bills(card_id, user):
        """
        Obtém faturas do cartão.
        CORREÇÃO: Usa transaction_type='PURCHASE' para encontrar compras não vinculadas.
        """
        try:
            card = Account.objects.get(account=card_id, user=user)
            
            # PRIMEIRO: Garantir que faturas existem para COMPRAS não vinculadas
            unlinked_purchases = Transaction.objects.filter(
                transaction_accounts__account=card,
                transaction_type='PURCHASE',  # ← Alterado para transaction_type
                is_deleted=False,
                credit_card_bill__isnull=True,
                occurred_at__lte=timezone.now().date() + timedelta(days=60)
            )
            
            if unlinked_purchases.exists():
                # Gerar faturas para compras não vinculadas
                CreditCardService.generate_credit_card_bills(card)
            
            # SEGUNDO: Obter todas as faturas
            bills = CreditCardBill.objects.filter(
                credit_card=card
            ).order_by('-end_date')
            
            for bill in bills:
                # Calcular total baseado em COMPRAS (PURCHASE) vinculadas
                purchases_total = Transaction.objects.filter(
                    credit_card_bill=bill,
                    transaction_type='PURCHASE',  # ← APENAS compras
                    is_deleted=False
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
                
                # Calcular pagamentos (CREDIT_CARD_PAYMENT) vinculados
                payments_total = Transaction.objects.filter(
                    credit_card_bill=bill,
                    transaction_type='CREDIT_CARD_PAYMENT',  # ← Pagamentos
                    is_deleted=False
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
                
                # Atualizar totais da fatura
                if bill.total_amount != purchases_total:
                    bill.total_amount = purchases_total
                    
                    # Recalcular pagamento mínimo
                    if purchases_total > 0:
                        minimum_payment = max(
                            Decimal('0.01'),
                            (bill.total_amount * Decimal('0.10')).quantize(Decimal('0.01'))
                        )
                        minimum_payment = min(minimum_payment, bill.total_amount)
                        bill.minimum_payment = minimum_payment
                    else:
                        bill.minimum_payment = Decimal('0.00')
                    
                    bill.save(update_fields=['total_amount', 'minimum_payment'])
                
                # Atualizar valor pago
                if bill.paid_amount != payments_total:
                    bill.paid_amount = payments_total
                    bill.save(update_fields=['paid_amount'])
                
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