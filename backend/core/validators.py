from django.core.exceptions import ValidationError
from decimal import Decimal


def validate_positive_amount(value):
    """Validate that amount is positive"""
    if isinstance(value, Decimal):
        if value <= 0:
            raise ValidationError("Amount must be greater than 0")
    else:
        if float(value) <= 0:
            raise ValidationError("Amount must be greater than 0")


def validate_installments(value):
    """Validate that installments count is valid"""
    if not isinstance(value, int) or value <= 0:
        raise ValidationError("Installments must be a positive integer")


def validate_percentage(value):
    """Validate that value is between 0 and 100"""
    if not (0 <= float(value) <= 100):
        raise ValidationError("Percentage must be between 0 and 100")
