"""
Management command para popular dados de teste no dashboard
Uso: python manage.py seed_dashboard
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.categories.models import Category
from apps.transactions.models import Transaction


class Command(BaseCommand):
    help = 'Popula dados de teste para o dashboard'

    def handle(self, *args, **options):
        # Cria usuário de teste se não existir
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'João',
                'last_name': 'Silva'
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS('✓ Usuário criado: testuser'))
        else:
            self.stdout.write(self.style.WARNING('✓ Usuário já existe: testuser'))

        # Define categorias padrão
        categories_data = [
            ('Salário', 'income', 'briefcase'),
            ('Bônus', 'income', 'gift'),
            ('Outros Rendimentos', 'income', 'coins'),
            ('Alimentação', 'expense', 'utensils'),
            ('Transporte', 'expense', 'car'),
            ('Lazer', 'expense', 'gamepad'),
            ('Moradia', 'expense', 'home'),
            ('Saúde', 'expense', 'hospital'),
            ('Educação', 'expense', 'book'),
        ]

        categories = {}
        for name, type_, icon in categories_data:
            category, created = Category.objects.get_or_create(
                user=user,
                name=name,
                type=type_,
                defaults={'icon': icon}
            )
            categories[name] = category
            if created:
                self.stdout.write(f'✓ Categoria criada: {name}')

        # Cria transações de teste dos últimos 180 dias
        today = timezone.now().date()
        base_transactions = [
            # Receitas
            ('Salário', 'Salário mensal', 5000, 'income', 'Salário', 1),  # 1º de cada mês
            ('Bônus', 'Bônus de performance', 1500, 'income', 'Bônus', 5),
            
            # Despesas variadas
            ('Supermercado', 'Compras no mercado', 350, 'expense', 'Alimentação', None),
            ('Restaurante', 'Almoço fora', 85, 'expense', 'Alimentação', None),
            ('Uber', 'Transporte', 42, 'expense', 'Transporte', None),
            ('Netflix', 'Assinatura mensal', 39.90, 'expense', 'Lazer', None),
            ('Aluguel', 'Aluguel do apartamento', 1500, 'expense', 'Moradia', 5),
            ('Conta de luz', 'Energia', 250, 'expense', 'Moradia', None),
            ('Academia', 'Mensalidade', 80, 'expense', 'Saúde', 10),
            ('Curso Online', 'Plataforma de educação', 99, 'expense', 'Educação', 15),
        ]

        created_count = 0
        for i in range(6):  # Últimos 6 meses
            month_offset = 30 * i
            
            for description, notes, amount, trans_type, category_name, day_offset in base_transactions:
                if day_offset is None:
                    day_offset = (i * 5 + hash(description)) % 25 + 1
                
                trans_date = today - timedelta(days=month_offset + (day_offset or 1))
                
                exists = Transaction.objects.filter(
                    user=user,
                    description=description,
                    date=trans_date,
                    category__name=category_name
                ).exists()
                
                if not exists:
                    Transaction.objects.create(
                        user=user,
                        category=categories[category_name],
                        amount=Decimal(str(amount)),
                        description=description,
                        type=trans_type,
                        date=trans_date,
                        notes=notes
                    )
                    created_count += 1

        self.stdout.write(self.style.SUCCESS(f'✓ {created_count} transações criadas'))
        self.stdout.write(self.style.SUCCESS('\n✓ Dados de teste populados com sucesso!'))
        self.stdout.write(self.style.WARNING('\nCredenciais de teste:'))
        self.stdout.write('  Usuário: testuser')
        self.stdout.write('  Senha: testpass123')
