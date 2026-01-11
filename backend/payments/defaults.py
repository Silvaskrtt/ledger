# backend/payments/defaults.py

DEFAULT_PAYMENT_METHODS = [
    {
        'type': 'PIX',
        'description': 'Transferência via PIX',
        'requires_account': True,
        'allows_installments': False,
        'icon': 'qrcode',  # Para uso futuro no frontend
        'color': '#32BCAD',  # Cor do PIX
    },
    {
        'type': 'DEBIT',
        'description': 'Cartão de Débito',
        'requires_account': True,
        'allows_installments': False,
        'icon': 'credit-card',
        'color': '#3B82F6',
    },
    {
        'type': 'CREDIT',
        'description': 'Cartão de Crédito',
        'requires_account': True,
        'allows_installments': True,
        'icon': 'credit-card',
        'color': '#8B5CF6',
    },
    {
        'type': 'CASH',
        'description': 'Dinheiro',
        'requires_account': False,
        'allows_installments': False,
        'icon': 'money-bill-wave',
        'color': '#10B981',
    },
    {
        'type': 'BANK_TRANSFER',
        'description': 'Transferência Bancária',
        'requires_account': True,
        'allows_installments': False,
        'icon': 'university',
        'color': '#6366F1',
    },
]

def create_default_payment_methods_for_user(user):
    """
    Função utilitária para criar métodos padrão para um usuário.
    """
    from .models import PaymentMethod
    import uuid
    
    created_methods = []
    
    for method_data in DEFAULT_PAYMENT_METHODS:
        # Remove campos extras que não estão no modelo
        method_data_copy = method_data.copy()
        method_data_copy.pop('icon', None)
        method_data_copy.pop('color', None)
        
        method, created = PaymentMethod.objects.get_or_create(
            user=user,
            type=method_data['type'],
            defaults=method_data_copy
        )
        
        if created:
            created_methods.append(method)
    
    return created_methods