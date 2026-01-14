#!/usr/bin/env python
"""
Script de verificação pré-deployment para dashboards
Valida se todas as configurações estão corretas

Uso: python dashboards_check.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.apps import apps
from django.urls import reverse
from django.contrib.auth.models import User
import json


def colored_text(text, color):
    """Retorna texto colorido"""
    colors = {
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'reset': '\033[0m'
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"


def print_header(text):
    """Imprime header"""
    print(f"\n{colored_text('='*60, 'blue')}")
    print(f"{colored_text(f'  {text}', 'blue')}")
    print(f"{colored_text('='*60, 'blue')}\n")


def check(title, condition, details=""):
    """Verifica uma condição e imprime resultado"""
    status = "✅" if condition else "❌"
    result = colored_text("OK", "green") if condition else colored_text("ERRO", "red")
    
    print(f"{status} {title}: {result}")
    if details and not condition:
        print(f"   └─ {colored_text(details, 'yellow')}")


def check_app_installed():
    """Verifica se app 'dashboards' está instalado"""
    print_header("1. APP INSTALADO")
    
    try:
        app = apps.get_app_config('dashboards')
        check("App 'dashboards'", True)
        return True
    except LookupError:
        check(
            "App 'dashboards'",
            False,
            "Adicione 'dashboards' a INSTALLED_APPS em config/settings.py"
        )
        return False


def check_urls_registered():
    """Verifica se URLs estão registradas"""
    print_header("2. URLs REGISTRADAS")
    
    try:
        # Tentar acessar as URLs
        urls = [
            'dashboards:card-expenses',
            'dashboards:category-expenses',
            'dashboards:cash-flow',
            'dashboards_web:dashboard'
        ]
        
        all_ok = True
        for url_name in urls:
            try:
                reverse(url_name)
                check(f"URL '{url_name}'", True)
            except Exception as e:
                check(f"URL '{url_name}'", False, str(e))
                all_ok = False
        
        return all_ok
    except Exception as e:
        check("Verificação de URLs", False, str(e))
        return False


def check_services():
    """Verifica se services estão disponíveis"""
    print_header("3. SERVIÇOS DE NEGÓCIO")
    
    try:
        from dashboards.services import (
            CardExpenseService,
            CategoryExpenseService,
            CashFlowService
        )
        
        check("CardExpenseService", True)
        check("CategoryExpenseService", True)
        check("CashFlowService", True)
        return True
    except ImportError as e:
        check("Services", False, str(e))
        return False


def check_serializers():
    """Verifica se serializers estão disponíveis"""
    print_header("4. SERIALIZERS")
    
    try:
        from dashboards.serializers import (
            CardExpenseDataSerializer,
            CategoryExpenseDataSerializer,
            CashFlowDataSerializer
        )
        
        check("CardExpenseDataSerializer", True)
        check("CategoryExpenseDataSerializer", True)
        check("CashFlowDataSerializer", True)
        return True
    except ImportError as e:
        check("Serializers", False, str(e))
        return False


def check_views():
    """Verifica se views estão disponíveis"""
    print_header("5. VIEWS")
    
    try:
        from dashboards.views import (
            card_expenses_dashboard,
            category_expenses_dashboard,
            cash_flow_dashboard
        )
        from dashboards.views_web import DashboardView
        
        check("card_expenses_dashboard", True)
        check("category_expenses_dashboard", True)
        check("cash_flow_dashboard", True)
        check("DashboardView", True)
        return True
    except ImportError as e:
        check("Views", False, str(e))
        return False


def check_templates():
    """Verifica se templates existem"""
    print_header("6. TEMPLATES E STATIC")
    
    template_path = "frontend/templates/dashboards.html"
    js_path = "frontend/static/js/dashboards.js"
    
    template_exists = os.path.exists(template_path)
    js_exists = os.path.exists(js_path)
    
    check(
        "dashboards.html",
        template_exists,
        f"Arquivo não encontrado em {template_path}"
    )
    check(
        "dashboards.js",
        js_exists,
        f"Arquivo não encontrado em {js_path}"
    )
    
    return template_exists and js_exists


def check_migrations():
    """Verifica se há pendências de migração"""
    print_header("7. MIGRAÇÕES")
    
    # Como o app não tem models, não há migrações
    check("Migrações pendentes", True, "App não possui models")
    return True


def check_database():
    """Verifica se banco está pronto"""
    print_header("8. BANCO DE DADOS")
    
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        check("Conexão com BD", True)
        return True
    except Exception as e:
        check("Conexão com BD", False, str(e))
        return False


def check_authentication():
    """Verifica se autenticação está funcional"""
    print_header("9. AUTENTICAÇÃO")
    
    try:
        # Tentar criar um usuário de teste
        test_user = User.objects.filter(username='test_dashboard_check').first()
        if not test_user:
            test_user = User.objects.create_user(
                username='test_dashboard_check',
                email='test@dashboards.local',
                password='test123'
            )
        
        check("Sistema de autenticação", True)
        
        # Limpar
        test_user.delete()
        return True
    except Exception as e:
        check("Sistema de autenticação", False, str(e))
        return False


def check_dependencies():
    """Verifica dependências externas"""
    print_header("10. DEPENDÊNCIAS")
    
    deps = {
        'rest_framework': 'Django REST Framework',
        'django': 'Django',
    }
    
    all_ok = True
    for package, name in deps.items():
        try:
            __import__(package)
            check(name, True)
        except ImportError:
            check(name, False, f"Instale com: pip install {package}")
            all_ok = False
    
    return all_ok


def print_summary(results):
    """Imprime resumo final"""
    print_header("RESUMO FINAL")
    
    total = len(results)
    passed = sum(results.values())
    failed = total - passed
    
    print(f"Total de verificações: {total}")
    print(f"Passou: {colored_text(str(passed), 'green')}")
    print(f"Falhou: {colored_text(str(failed), 'red')}")
    print()
    
    if failed == 0:
        print(colored_text("✅ TUDO PRONTO PARA DEPLOYMENT!", "green"))
        print()
        print("Próximos passos:")
        print("  1. Execute: python manage.py runserver")
        print("  2. Acesse:  http://localhost:8000/dashboards/")
        print("  3. Verifique os 3 dashboards funcionando")
        return True
    else:
        print(colored_text("❌ EXISTEM PROBLEMAS", "red"))
        print()
        print("Corrija os erros acima e execute este script novamente.")
        return False


def main():
    """Executa todas as verificações"""
    print(colored_text("\n╔════════════════════════════════════════════════════════════╗", "blue"))
    print(colored_text("║         VERIFICAÇÃO PRÉ-DEPLOYMENT - DASHBOARDS          ║", "blue"))
    print(colored_text("╚════════════════════════════════════════════════════════════╝", "blue"))
    
    results = {
        'App Instalado': check_app_installed(),
        'URLs Registradas': check_urls_registered(),
        'Services': check_services(),
        'Serializers': check_serializers(),
        'Views': check_views(),
        'Templates': check_templates(),
        'Migrações': check_migrations(),
        'Banco de Dados': check_database(),
        'Autenticação': check_authentication(),
        'Dependências': check_dependencies(),
    }
    
    success = print_summary(results)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
