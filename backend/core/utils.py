from decimal import Decimal
from django.utils import timezone
from datetime import timedelta


def format_currency(amount, currency='BRL'):
    """Format amount as currency string"""
    if currency == 'BRL':
        return f"R$ {amount:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
    elif currency == 'USD':
        return f"$ {amount:,.2f}"
    elif currency == 'EUR':
        return f"€ {amount:,.2f}"
    return f"{amount:,.2f} {currency}"


def calculate_installment_amount(total_amount, num_installments):
    """Calculate amount per installment"""
    if num_installments <= 0:
        raise ValueError("Number of installments must be greater than 0")
    return Decimal(total_amount) / Decimal(num_installments)


def get_period_dates(period_type):
    """Get start and end dates for a period"""
    now = timezone.now()
    
    if period_type == 'DAILY':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    elif period_type == 'WEEKLY':
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)
    elif period_type == 'MONTHLY':
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
    elif period_type == 'YEARLY':
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(year=start.year + 1)
    else:
        raise ValueError(f"Invalid period type: {period_type}")
    
    return start, end
