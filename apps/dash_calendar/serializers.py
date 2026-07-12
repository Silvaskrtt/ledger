from .models import Transaction


class TransactionSerializer:
    @staticmethod
    def to_representation(transaction: Transaction) -> dict:
        return {
            'id': transaction.id,
            'type': transaction.type,
            'amount': float(transaction.amount),
            'date': transaction.date.isoformat(),
            'category': transaction.category,
            'description': transaction.description,
            'tag': transaction.tag or '',
            'recurrence': transaction.recurrence,
            'created_at': transaction.created_at.isoformat(),
            'updated_at': transaction.updated_at.isoformat(),
        }