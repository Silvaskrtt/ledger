# backend/payments/apps.py

from django.apps import AppConfig

class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'
    verbose_name = 'Payments'

    def ready(self):
        # Importa os sinais para que sejam registrados
        import payments.signals
        
        # Em desenvolvimento, também cria para superusuários
        if not hasattr(self, 'defaults_created'):
            from django.contrib.auth.models import User
            from .defaults import create_default_payment_methods_for_user
            
            self.defaults_created = True