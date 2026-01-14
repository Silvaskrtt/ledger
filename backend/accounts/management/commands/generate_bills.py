# backend/accounts/management/commands/generate_bills.py

from django.core.management.base import BaseCommand
from accounts.models import Account
from services.credit_card_service import CreditCardService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Gera faturas para todos os cartões de crédito'

    def handle(self, *args, **options):
        self.stdout.write("Gerando faturas para cartões de crédito...")
        
        credit_cards = Account.objects.filter(
            type='CREDIT_CARD',
            is_active=True
        )
        
        total_bills = 0
        
        for card in credit_cards:
            try:
                bills = CreditCardService.generate_credit_card_bills(card)
                total_bills += len(bills)
                
                if bills:
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ {card.name}: {len(bills)} faturas geradas")
                    )
                else:
                    self.stdout.write(f"  → {card.name}: Nenhuma fatura gerada")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ {card.name}: {str(e)}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"\nTotal de faturas geradas: {total_bills}")
        )