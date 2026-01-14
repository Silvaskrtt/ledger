# backend/dashboards/tests.py

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import datetime, timedelta
from decimal import Decimal
import json

from transactions.models import Transaction
from payments.models import PaymentMethod
from categories.models import Category
from accounts.models import Account


class DashboardAPITestCase(TestCase):
    """Testes para os endpoints de dashboards"""
    
    def setUp(self):
        """Configuração inicial para testes"""
        # Criar usuário
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Criar categorias
        self.food_category = Category.objects.create(
            name='Alimentação',
            type='OUT',
            color='#FF5733',
            user=self.user
        )
        
        self.transport_category = Category.objects.create(
            name='Transporte',
            type='OUT',
            color='#33FF57',
            user=self.user
        )
        
        # Criar métodos de pagamento (cartões)
        self.credit_card_1 = PaymentMethod.objects.create(
            type='CREDIT',
            description='Cartão Nubank',
            user=self.user
        )
        
        self.credit_card_2 = PaymentMethod.objects.create(
            type='CREDIT',
            description='Cartão Itaú',
            user=self.user
        )
        
        # Criar conta
        self.account = Account.objects.create(
            name='Conta Principal',
            account_type='CHECKING',
            user=self.user
        )
        
        # Criar transações de teste
        today = datetime.now().date()
        
        # Cartão 1 - Alimentação
        Transaction.objects.create(
            amount=Decimal('100.00'),
            direction='OUT',
            occurred_at=datetime.combine(today - timedelta(days=5), datetime.min.time()),
            origin='MANUAL',
            user=self.user,
            category=self.food_category,
            payment_method=self.credit_card_1
        )
        
        Transaction.objects.create(
            amount=Decimal('150.00'),
            direction='OUT',
            occurred_at=datetime.combine(today - timedelta(days=3), datetime.min.time()),
            origin='MANUAL',
            user=self.user,
            category=self.food_category,
            payment_method=self.credit_card_1
        )
        
        # Cartão 2 - Transporte
        Transaction.objects.create(
            amount=Decimal('50.00'),
            direction='OUT',
            occurred_at=datetime.combine(today - timedelta(days=2), datetime.min.time()),
            origin='MANUAL',
            user=self.user,
            category=self.transport_category,
            payment_method=self.credit_card_2
        )
        
        # Receita
        income_category = Category.objects.create(
            name='Salário',
            type='IN',
            user=self.user
        )
        
        Transaction.objects.create(
            amount=Decimal('5000.00'),
            direction='IN',
            occurred_at=datetime.combine(today - timedelta(days=1), datetime.min.time()),
            origin='MANUAL',
            user=self.user,
            category=income_category,
            payment_method=self.credit_card_1
        )
        
        self.client = Client()
    
    def test_card_expenses_dashboard_authenticated(self):
        """Teste: Dashboard de gastos por cartão com autenticação"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('dashboards:card-expenses'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Validar estrutura de resposta
        self.assertIn('data', data)
        self.assertIn('total', data)
        self.assertIn('metadata', data)
        
        # Validar dados
        self.assertEqual(len(data['data']), 2)  # Dois cartões com despesas
        
        # Cartão 1 deve ter 250 (100 + 150) em alimentação + 5000 em renda
        # Cartão 2 deve ter 50 em transporte
        
        card_names = [item['card_name'] for item in data['data']]
        self.assertIn('Cartão Nubank', card_names)
        self.assertIn('Cartão Itaú', card_names)
    
    def test_card_expenses_dashboard_unauthenticated(self):
        """Teste: Dashboard de gastos por cartão sem autenticação"""
        response = self.client.get(reverse('dashboards:card-expenses'))
        
        # Deve redirecionar para login ou retornar 403
        self.assertIn(response.status_code, [302, 403])
    
    def test_card_expenses_with_date_filter(self):
        """Teste: Dashboard de gastos por cartão com filtro de data"""
        self.client.login(username='testuser', password='testpass123')
        
        today = datetime.now().date()
        start_date = (today - timedelta(days=4)).strftime('%Y-%m-%d')
        end_date = (today - timedelta(days=2)).strftime('%Y-%m-%d')
        
        response = self.client.get(
            reverse('dashboards:card-expenses'),
            {'start_date': start_date, 'end_date': end_date}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Deve retornar apenas transações no período
        self.assertGreater(len(data['data']), 0)
    
    def test_category_expenses_dashboard(self):
        """Teste: Dashboard de gastos por categoria"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('dashboards:category-expenses'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Validar estrutura
        self.assertIn('data', data)
        self.assertIn('total', data)
        
        # Validar dados
        category_names = [item['category_name'] for item in data['data']]
        self.assertIn('Alimentação', category_names)
        
        # Validar percentuais
        for item in data['data']:
            self.assertIn('percentage', item)
            self.assertGreaterEqual(float(item['percentage']), 0)
            self.assertLessEqual(float(item['percentage']), 100)
    
    def test_category_expenses_with_include_pending(self):
        """Teste: Dashboard de categoria com toggle de pendentes"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('dashboards:category-expenses'),
            {'include_pending': 'true'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('metadata', data)
        self.assertTrue(data['metadata']['include_pending'])
    
    def test_cash_flow_dashboard(self):
        """Teste: Dashboard de fluxo de caixa"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('dashboards:cash-flow'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Validar estrutura
        self.assertIn('data', data)
        self.assertEqual(len(data['data']), 12)  # 12 meses
        
        # Validar campos de cada mês
        for month_data in data['data']:
            self.assertIn('month', month_data)
            self.assertIn('month_number', month_data)
            self.assertIn('income', month_data)
            self.assertIn('expense', month_data)
            self.assertIn('balance', month_data)
    
    def test_cash_flow_with_specific_year(self):
        """Teste: Dashboard de fluxo de caixa com ano específico"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('dashboards:cash-flow'),
            {'year': '2024'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['metadata']['year'], 2024)
    
    def test_invalid_date_format(self):
        """Teste: Formato de data inválido"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('dashboards:card-expenses'),
            {'start_date': 'invalid-date', 'end_date': '2024-01-31'}
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
    
    def test_invalid_year(self):
        """Teste: Ano inválido"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('dashboards:cash-flow'),
            {'year': 'invalid'}
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)


class DashboardWebTestCase(TestCase):
    """Testes para a página web de dashboards"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
    
    def test_dashboard_page_authenticated(self):
        """Teste: Página de dashboards com usuário autenticado"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('dashboards_web:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('dashboards.html', response.template_name)
    
    def test_dashboard_page_unauthenticated(self):
        """Teste: Página de dashboards sem autenticação"""
        response = self.client.get(reverse('dashboards_web:dashboard'))
        
        # Deve redirecionar para login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
