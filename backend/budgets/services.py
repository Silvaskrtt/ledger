# backend/budgets/services.py

from datetime import date
from .models import Budget

def get_or_create_current_month_budget(user):
    today = date.today()
    period_start = today.replace(day=1)

    budget, _ = Budget.objects.get_or_create(
        id_user=user,
        period_type='MONTHLY',
        period_start=period_start
    )

    return budget