import uuid
from django.db import models

# Importing constraints and expressions
from django.db.models import CheckConstraint, Q, F

# Importing Postgres-specific functions
from django.contrib.postgres.functions import RandomUUID
from django.utils import timezone

# Model for users
class users(models.Model):
    id_user = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False)
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    
    def __str__(self):
        return f"{self.name} {self.surname} ({self.email})"
    
# Model for categories
class categories(models.Model):
    id_category = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False)
    name = models.CharField(max_length=100, unique=True)
    id_user = models.ForeignKey(
        users, 
        on_delete=models.CASCADE, 
        related_name='categories')
    
    id_parent_category = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    
# Model for payment methods
class payment_methods(models.Model):
    id_payment_method = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    description = models.CharField(max_length=100, null=True, blank=True)
    requires_account = models.BooleanField(default=True)
    allows_installments = models.BooleanField(default=True)
    id_user = models.ForeignKey(
        users, 
        on_delete=models.CASCADE, 
        related_name='payment_methods')
    
    TYPE_CHOICES = [
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
        ('PIX', 'Pix'),
        ('CASH', 'Cash'),
    ]
    
    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default='PIX'
        )
    
# Model for accounts
class accounts(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('CHECKING', 'Checking Account'),
        ('WALLET', 'Digital Wallet'),
        ('CREDIT_CARD', 'Credit Card'),
    ]
    
    id_account = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    active = models.BooleanField(default=True)
    id_user = models.ForeignKey(
        users,
        on_delete=models.CASCADE,
        related_name='accounts')

# Model for installment plans
class installment_plans(models.Model):
    id_installment_plan = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    # Constraints to ensure total_amount is positive and below a certain limit
    class Meta:
        constraints = [
            CheckConstraint(condition=Q(total_amount__gt=0), name='total_amount_positive'),
            CheckConstraint(condition=Q(total_amount__lt=10000), name='total_amount_max_limit'),
            CheckConstraint(condition=Q(installments__gt=0), name='installments_positive'),
            CheckConstraint(condition=Q(installments__lte=36), name='installments_max_limit'),
        ]
        
    def __str__(self):
        return f"Total: {self.total_amount}"
    
    installments = models.IntegerField()   
    start_date = models.DateField(default=timezone.now)
    
    id_user = models.ForeignKey(
        users,
        on_delete=models.CASCADE,
        related_name='installment_plans')
    
    id_account = models.ForeignKey(
        accounts,
        on_delete=models.CASCADE,
        related_name='installment_plans')
    
    id_category = models.ForeignKey(
        categories,
        on_delete=models.CASCADE,
        related_name='installment_plans')
    
class transactions(models.Model):
    DIRECTION_CHOICES = [
        ('IN', 'Income'),
        ('OUT', 'Expense'),
    ]
    
    ORIGIN_CHOICES = [
        ('MANUAL', 'Manual'),
        ('RECURRENT', 'Recurrent'),
        ('INSTALLMENT', 'Installment'),
    ]
    
    CURRENCY_CHOICES = [
    ('BRL', 'Brazilian Real'),
    ('USD', 'US Dollar'),
    ('EUR', 'Euro'),
    ]
    
    id_transaction = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    direction = models.CharField(max_length=3, choices=DIRECTION_CHOICES)
    occurred_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='BRL')
    origin = models.CharField(max_length=20, choices=ORIGIN_CHOICES)
    id_user = models.ForeignKey(
        users,
        on_delete=models.CASCADE,
        related_name='transactions')
    
    id_category = models.ForeignKey(
        categories,
        on_delete=models.CASCADE,
        related_name='transactions')
    
    id_payment_method = models.ForeignKey(
        payment_methods,
        on_delete=models.CASCADE,
        related_name='transactions')
    
    id_installment_plan = models.ForeignKey(
        installment_plans,
        on_delete=models.CASCADE,
        related_name='transactions',
        null=True,
        blank=True
    )
    
    # Constraints to ensure direction is either 'income' or 'expense' and amount is positive
    class Meta:
        constraints = [
            CheckConstraint(
                condition=Q(direction__in=['IN', 'OUT']),
                name='valid_transaction_direction'
            ),
            CheckConstraint(
                condition=Q(amount__gt=0),
                name='amount_positive'
            )
        ]
        
    def __str__(self):
        return f"Transaction {self.id_transaction}: {self.direction} of {self.amount} {self.currency} on {self.occurred_at}"
   
# Model for budgets     
class budgets(models.Model):
    PERIOD_TYPE_CHOICES = [
        ('MONTHLY', 'Monthly'),
    ]
    
    id_budget = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPE_CHOICES)
    
     # Constraints to ensure period_type is either 'monthly', 'quarterly', or 'yearly'
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['id_user', 'period_type', 'period_start'],
                name='unique_budget_period'
            )
        ]
        
    period_start = models.DateField()
    
    id_user = models.ForeignKey(
        users,
        on_delete=models.CASCADE,
        related_name='budgets')
    
# Model for financial goals
class financial_goals(models.Model):
    STRATEGY_CHOICES = [
        ('SAVING', 'Saving'),
        ('DEBT_PAYOFF', 'Debt Payoff'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('ABANDONED', 'Abandoned'),
    ]
    
    id_financial_goal = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    target_amount = models.DecimalField(max_digits=14, decimal_places=2)
    
    class Meta:
        constraints = [
            CheckConstraint(
                condition=Q(target_amount__gt=0),
                name='target_amount_positive'
            )
        ]
    
    deadline = models.DateField()
    strategy = models.CharField(max_length=20, choices=STRATEGY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    id_user = models.ForeignKey(
        users,
        on_delete=models.CASCADE,
        related_name='financial_goals')
    
# Model for tags
class tags(models.Model):
    id_tag = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(max_length=100)
    
    id_user = models.ForeignKey(
        users,
        on_delete=models.CASCADE,
        related_name='tags')
    
    # Unique constraint to ensure tag names are unique per user
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['id_user', 'name'],
                name='unique_tag_per_user'
            )
        ]
    
class recurrence_rules(models.Model):
    FREQUENCY_CHOICES = [
    ('DAILY', 'Daily'),
    ('WEEKLY', 'Weekly'),
    ('MONTHLY', 'Monthly'),
    ]
    
    DIRECTION_CHOICES = [
        ('IN', 'Income'),
        ('OUT', 'Expense'),
    ]
    
    id_recurrence_rule = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    frequency = models.CharField(max_length=50, choices=FREQUENCY_CHOICES)
    next_execution = models.DateField()
    max_executions = models.IntegerField(null=True, blank=True)
    
    class Meta:
        constraints = [
            CheckConstraint(
                condition=Q(max_executions__gt=0),
                name='max_executions_positive'
            )
        ]
    
    executions_count = models.IntegerField(default=0)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    direction = models.CharField(max_length=50, choices=DIRECTION_CHOICES)
    
    id_user = models.ForeignKey(
        users,
        on_delete=models.CASCADE,
        related_name='recurrence_rules')
    
    id_category = models.ForeignKey(
        categories,
        on_delete=models.CASCADE,
        related_name='recurrence_rules')
    
    id_payment_method = models.ForeignKey(
        payment_methods,
        on_delete=models.CASCADE,
        related_name='recurrence_rules')
    
    id_account = models.ForeignKey(
        accounts,
        on_delete=models.CASCADE,
        related_name='recurrence_rules')
    
# Model for transaction-tags relationship
class transaction_tags(models.Model):
    id_transaction = models.ForeignKey(
        transactions,
        on_delete=models.CASCADE,
        related_name='transaction_tags')
    
    id_tag = models.ForeignKey(
        tags,
        on_delete=models.CASCADE,
        related_name='transaction_tags')
    
    # Unique constraint to prevent duplicate tag assignments to the same transaction
    class Meta:
        unique_together = [('id_transaction', 'id_tag')]
    
# Model for transaction-accounts relationship
class transaction_accounts(models.Model):
    id_transaction = models.ForeignKey(
        transactions,
        on_delete=models.CASCADE,
        related_name='transaction_accounts')
    
    id_account = models.ForeignKey(
        accounts,
        on_delete=models.CASCADE,
        related_name='transaction_accounts')
    
    role = models.CharField(max_length=50)
    
    class Meta:
        constraints = [
            CheckConstraint(
                condition=Q(role__in=['source', 'destination']),
                name='valid_account_role'
            )
        ]
        
        # Unique constraint to prevent duplicate account-role assignments for the same transaction
        unique_together = [('id_transaction', 'id_account', 'role')] 

# Model for budget-category limits
class budget_categories_limits(models.Model):
    id_budget = models.ForeignKey(
        budgets,
        on_delete=models.CASCADE,
        related_name='budget_categories_limits')
    
    id_category = models.ForeignKey(
        categories,
        on_delete=models.CASCADE,
        related_name='budget_categories_limits')
    
    limit_amount = models.DecimalField(max_digits=14, decimal_places=2)
    
    class Meta:
        constraints = [
            CheckConstraint(
                condition=Q(limit_amount__gt=0),
                name='limit_amount_positive'
            )
        ]