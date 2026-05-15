# categories/signals.py
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
            {'name': 'Salário', 'type': 'income', 'icon': '💰', 'color': '#10b981', 'description': 'Salário e remunerações'},
            {'name': 'Freelancer', 'type': 'income', 'icon': '💼', 'color': '#14b8a6', 'description': 'Trabalhos autônomos'},
            {'name': 'Investimentos', 'type': 'income', 'icon': '📈', 'color': '#06b6d4', 'description': 'Rendimentos de investimentos'},
            {'name': 'Presentes', 'type': 'income', 'icon': '🎁', 'color': '#8b5cf6', 'description': 'Presentes recebidos'},
            
            # Saídas (expense)
            {'name': 'Alimentação', 'type': 'expense', 'icon': '🍔', 'color': '#ef4444', 'description': 'Supermercado e alimentação'},
            {'name': 'Moradia', 'type': 'expense', 'icon': '🏠', 'color': '#ec4899', 'description': 'Aluguel, condomínio, contas'},
            {'name': 'Transporte', 'type': 'expense', 'icon': '🚗', 'color': '#f59e0b', 'description': 'Combustível, Uber, ônibus'},
            {'name': 'Saúde', 'type': 'expense', 'icon': '💊', 'color': '#ef4444', 'description': 'Médicos, remédios, plano'},
            {'name': 'Lazer', 'type': 'expense', 'icon': '🎮', 'color': '#8b5cf6', 'description': 'Cinema, shows, hobbies'},
            {'name': 'Educação', 'type': 'expense', 'icon': '📚', 'color': '#3b82f6', 'description': 'Cursos, livros, mensalidades'},
            {'name': 'Vestuário', 'type': 'expense', 'icon': '👕', 'color': '#ec4899', 'description': 'Roupas e acessórios'},
            {'name': 'Assinaturas', 'type': 'expense', 'icon': '📺', 'color': '#6366f1', 'description': 'Streaming, apps, serviços'},
            {'name': 'Outros', 'type': 'expense', 'icon': '📌', 'color': '#6b7280', 'description': 'Outras despesas', 'is_default': True},
        ]
        
        for cat_data in default_categories:
            Category.objects.create(
                user=instance,
                name=cat_data['name'],
                type=cat_data['type'],
                icon=cat_data['icon'],
                color=cat_data.get('color', '#8A4FFF'),
                description=cat_data.get('description', ''),
                is_default=cat_data.get('is_default', False),
                budget=0
            )