import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_brazilian_phone(value):
    """
    Valida se o telefone está no formato brasileiro.
    Aceita formatos: (XX) XXXXX-XXXX, (XX) XXXX-XXXX, XXXXXXXXXX, XXXXXXXXXXX
    """
    if not value:
        return
    
    # Remove caracteres não numéricos para validação
    phone_digits = re.sub(r'\D', '', value)
    
    # Telefone brasileiro deve ter 10 ou 11 dígitos
    if len(phone_digits) not in (10, 11):
        raise ValidationError(
            _('Telefone inválido. Deve conter 10 ou 11 dígitos.'),
            code='invalid_phone_length'
        )
    
    # Verifica se começa com DDD válido (2 primeiros dígitos entre 11 e 99)
    ddd = int(phone_digits[:2])
    if ddd < 11 or ddd > 99:
        raise ValidationError(
            _('DDD inválido. Deve estar entre 11 e 99.'),
            code='invalid_ddd'
        )
    
    # Verifica se o primeiro dígito após o DDD é válido (6-9 para celular ou 2-5 para fixo)
    first_digit = int(phone_digits[2])
    if first_digit not in range(2, 10):
        raise ValidationError(
            _('Número de telefone inválido.'),
            code='invalid_phone_number'
        )


def format_brazilian_phone(phone):
    """
    Formata um telefone para o padrão brasileiro (XX) XXXXX-XXXX ou (XX) XXXX-XXXX.
    """
    if not phone:
        return phone
    
    # Remove caracteres não numéricos
    digits = re.sub(r'\D', '', phone)
    
    # Se não tem 10 ou 11 dígitos, retorna como está
    if len(digits) not in (10, 11):
        return phone
    
    # Formata de acordo com a quantidade de dígitos
    if len(digits) == 11:  # Celular (XX) 9XXXX-XXXX
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    else:  # Fixo (XX) XXXX-XXXX
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
