from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Transaction


class CalendarBalanceTests(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(
			username='calendar-user',
			email='calendar@example.com',
			password='test-password',
		)
		self.client.force_login(self.user)

	def create_transaction(self, transaction_type, amount, transaction_date):
		return Transaction.objects.create(
			user=self.user,
			type=transaction_type,
			amount=amount,
			date=transaction_date,
			category='Teste',
			description='Transação de teste',
		)

	def test_savings_are_accumulated_and_reduce_balance(self):
		self.create_transaction('saving', '200.00', date(2026, 7, 31))
		self.create_transaction('income', '1000.00', date(2026, 8, 1))
		self.create_transaction('saving', '100.00', date(2026, 8, 2))
		self.create_transaction('saving', '50.00', date(2026, 8, 3))
		self.create_transaction('expense', '25.00', date(2026, 8, 4))

		response = self.client.get(
			reverse('dash_calendar:api_monthly_summary'),
			{'year': 2026, 'month': 8},
		)

		summary = response.json()['summary']
		self.assertEqual(summary['total_saving'], 350.0)
		self.assertEqual(summary['total_expense'], 25.0)
		self.assertEqual(summary['days'][-1]['balance'], 625.0)

		next_month = self.client.get(
			reverse('dash_calendar:api_monthly_summary'),
			{'year': 2026, 'month': 9},
		)
		self.assertEqual(next_month.json()['summary']['opening_balance'], 625.0)

# Create your tests here.
