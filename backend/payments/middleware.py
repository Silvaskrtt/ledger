# backend/payments/middleware.py

from django.utils.deprecation import MiddlewareMixin
from .models import PaymentMethod
from .defaults import create_default_payment_methods_for_user
import logging

logger = logging.getLogger(__name__)

class EnsurePaymentMethodsMiddleware(MiddlewareMixin):
    """
    Middleware que verifica se o usuário tem métodos de pagamento
    ao acessar páginas financeiras.
    """
    FINANCIAL_PATHS = [
        '/transactions/',
        '/accounts/',
        '/payments/',
        '/api/transactions/',
    ]
    
    def process_request(self, request):
        # Só verifica para usuários autenticados
        if not request.user.is_authenticated:
            return None
        
        # Só verifica em rotas financeiras
        if not any(path in request.path for path in self.FINANCIAL_PATHS):
            return None
        
        # Verifica se tem métodos de pagamento
        has_methods = PaymentMethod.objects.filter(id_user=request.user).exists()
        
        if not has_methods:
            try:
                created_methods = create_default_payment_methods_for_user(request.user)
                if created_methods:
                    logger.info(f"Criados métodos padrão para {request.user.username} via middleware")
            except Exception as e:
                logger.error(f"Erro no middleware: {str(e)}")
        
        return None