# Transaction choices
TRANSACTION_DIRECTION_CHOICES = [
    ('IN', 'Income'),
    ('OUT', 'Expense'),
]

TRANSACTION_CURRENCIES = [
    ('BRL', 'Brazilian Real'),
    ('USD', 'US Dollar'),
    ('EUR', 'Euro'),
]

# Account types
ACCOUNT_TYPE_CHOICES = [
    ('CHECKING', 'Checking Account'),
    ('WALLET', 'Digital Wallet'),
    ('CREDIT_CARD', 'Credit Card'),
]

# Payment methods
PAYMENT_METHOD_TYPE_CHOICES = [
    ('CREDIT', 'Credit Card'),
    ('DEBIT', 'Debit Card'),
    ('PIX', 'Pix'),
    ('CASH', 'Cash'),
]

# Budget periods
BUDGET_PERIOD_CHOICES = [
    ('DAILY', 'Daily'),
    ('WEEKLY', 'Weekly'),
    ('MONTHLY', 'Monthly'),
    ('YEARLY', 'Yearly'),
]

# Recurrence frequencies
RECURRENCE_FREQUENCY_CHOICES = [
    ('DAILY', 'Daily'),
    ('WEEKLY', 'Weekly'),
    ('BIWEEKLY', 'Biweekly'),
    ('MONTHLY', 'Monthly'),
    ('QUARTERLY', 'Quarterly'),
    ('YEARLY', 'Yearly'),
]

# Financial goal strategies
FINANCIAL_GOAL_STRATEGY_CHOICES = [
    ('SAVE', 'Save'),
    ('INVEST', 'Invest'),
    ('SPEND', 'Spend'),
]

# Financial goal status
FINANCIAL_GOAL_STATUS_CHOICES = [
    ('ACTIVE', 'Active'),
    ('COMPLETED', 'Completed'),
    ('CANCELLED', 'Cancelled'),
]
