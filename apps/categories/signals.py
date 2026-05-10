# finance/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Category

User = get_user_model()

@receiver(post_save, sender=User)
def create_default_categories(sender, instance, created, **kwargs):
    """Cria categorias padrão quando um novo usuário é criado"""
    
    if created:
        # Categorias padrão
        default_categories = [
            # Entradas (income)
            {'name': 'Salário', 'type': 'income', 'icon': 'attach_money', 'description': 'Salário e remunerações'},
            {'name': 'Freelancer', 'type': 'income', 'icon': 'work', 'description': 'Trabalhos autônomos'},
            {'name': 'Investimentos', 'type': 'income', 'icon': 'trending_up', 'description': 'Rendimentos de investimentos'},
            
            # Saídas (expense)
            {'name': 'Alimentação', 'type': 'expense', 'icon': 'restaurant', 'description': 'Supermercado e alimentação'},
            {'name': 'Moradia', 'type': 'expense', 'icon': 'home', 'description': 'Aluguel, condomínio, contas'},
            {'name': 'Transporte', 'type': 'expense', 'icon': 'directions_car', 'description': 'Combustível, Uber, ônibus'},
            {'name': 'Saúde', 'type': 'expense', 'icon': 'health_and_safety', 'description': 'Médicos, remédios, plano'},
            {'name': 'Lazer', 'type': 'expense', 'icon': 'celebration', 'description': 'Cinema, shows, hobbies'},
            {'name': 'Educação', 'type': 'expense', 'icon': 'school', 'description': 'Cursos, livros, mensalidades'},
            {'name': 'Vestuário', 'type': 'expense', 'icon': 'checkroom', 'description': 'Roupas e acessórios'},
        ]
        
        for cat_data in default_categories:
            Category.objects.create(
                user=instance,
                name=cat_data['name'],
                type=cat_data['type'],
                icon=cat_data['icon'],
                description=cat_data['description'],
                is_default=True
            )