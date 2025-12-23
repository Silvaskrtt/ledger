class BudgetExceededError(Exception):
    """Raised when a budget limit is exceeded"""
    pass


class InsufficientFundsError(Exception):
    """Raised when there are insufficient funds for a transaction"""
    pass


class InvalidTransactionError(Exception):
    """Raised when a transaction data is invalid"""
    pass


class RecurrenceExecutionError(Exception):
    """Raised when a recurrence rule cannot be executed"""
    pass


class GoalNotFoundError(Exception):
    """Raised when a financial goal is not found"""
    pass


class CategoryNotFoundError(Exception):
    """Raised when a category is not found"""
    pass
