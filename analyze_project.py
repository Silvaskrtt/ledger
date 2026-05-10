#!/usr/bin/env python3
"""
Analisador de Qualidade do Projeto Financeiro
Uso: python analyze_project.py
"""

import os
import re
import ast
import json
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Any
import sys

try:
    import radon
    from radon.complexity import cc_rank, cc_visit
    from radon.metrics import mi_visit, mi_rank
except ImportError:
    print("Instalando radon para análise de complexidade...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "radon"])
    from radon.complexity import cc_rank, cc_visit
    from radon.metrics import mi_visit, mi_rank

try:
    from pylint import lint
except ImportError:
    print("Pylint não instalado. Instale com: pip install pylint")

# Configurações
PROJECT_ROOT = Path.cwd()
REQUIRED_DIRS = [
    "config/settings",
    "apps/common",
    "apps/accounts",
    "apps/profiles",
    "apps/transactions",
    "apps/dashboard",
    "static/css",
    "static/js",
    "templates",
    "templates/partials",
    "templates/components",
    "scripts",
    "docs",
]

REQUIRED_FILES = [
    ".env",
    ".gitignore",
    "README.md",
    "requirements.txt",
    "manage.py",
    "config/__init__.py",
    "config/settings/__init__.py",
    "config/settings/base.py",
    "config/urls.py",
]

# Padrões para verificação
PATTERNS = {
    'debug_true': r'DEBUG\s*=\s*True',
    'secret_key_hardcoded': r'SECRET_KEY\s*=\s*[\'\"][^\'\"]+[\'\"]',
    'raw_sql': r'raw\([\'"]',
    'print_statement': r'print\(',
}

class ProjectAnalyzer:
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.results = {
            'structure': {},
            'code_quality': {},
            'django_best_practices': {},
            'security': {},
            'performance': {},
            'recommendations': []
        }
        self.apps = []
        
    def analyze_all(self):
        """Executa todas as análises"""
        print("🔍 INICIANDO ANÁLISE COMPLETA DO PROJETO\n" + "="*60)
        
        self.check_structure()
        self.check_requirements()
        self.analyze_python_files()
        self.analyze_django_apps()
        self.analyze_static_files()
        self.check_security()
        self.check_tests()
        self.generate_report()
        
    def check_structure(self):
        """Verifica estrutura de diretórios e arquivos"""
        print("\n📁 VERIFICANDO ESTRUTURA DO PROJETO...")
        
        # Verificar diretórios obrigatórios
        missing_dirs = []
        for dir_path in REQUIRED_DIRS:
            full_path = self.project_path / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
            else:
                self.results['structure'][f"dir_{dir_path}"] = "OK"
        
        # Verificar arquivos obrigatórios
        missing_files = []
        for file_path in REQUIRED_FILES:
            full_path = self.project_path / file_path
            if not full_path.exists():
                missing_files.append(file_path)
            else:
                self.results['structure'][f"file_{file_path}"] = "OK"
        
        # Verificar estrutura de apps
        apps_dir = self.project_path / "apps"
        if apps_dir.exists():
            self.apps = [d.name for d in apps_dir.iterdir() 
                        if d.is_dir() and not d.name.startswith('_') and d.name != 'common']
            self.results['structure']['apps_found'] = f"{len(self.apps)} apps: {', '.join(self.apps)}"
        
        # Relatório de estrutura
        if missing_dirs:
            self.results['recommendations'].append(
                f"❌ Diretórios faltando: {', '.join(missing_dirs)}"
            )
        else:
            print("✅ Todos os diretórios obrigatórios presentes")
            
        if missing_files:
            self.results['recommendations'].append(
                f"❌ Arquivos faltando: {', '.join(missing_files)}"
            )
        else:
            print("✅ Todos os arquivos obrigatórios presentes")
    
    def check_requirements(self):
        """Verifica arquivo requirements.txt"""
        print("\n📦 VERIFICANDO DEPENDÊNCIAS...")
        
        req_file = self.project_path / "requirements.txt"
        if not req_file.exists():
            self.results['recommendations'].append("❌ requirements.txt não encontrado")
            return
        
        with open(req_file, 'r') as f:
            requirements = f.read()
        
        required_packages = [
            'django>=', 'django-allauth', 'psycopg2', 'python-dotenv',
            'djangorestframework', 'celery', 'redis', 'pytest'
        ]
        
        missing_pkgs = []
        for pkg in required_packages:
            if pkg not in requirements:
                missing_pkgs.append(pkg)
        
        # Verificar versões fixas vs flexíveis
        has_pinned = any(re.search(r'==[\d\.]+', line) for line in requirements.split('\n') if '==' in line)
        
        if missing_pkgs:
            self.results['recommendations'].append(
                f"⚠️ Pacotes recomendados faltando: {', '.join(missing_pkgs)}"
            )
        
        if not has_pinned:
            self.results['recommendations'].append(
                "⚠️ Considere fixar versões exatas no requirements.txt (usando ==)"
            )
        
        print(f"✅ requirements.txt encontrado com {len(requirements.splitlines())} dependências")
    
    def analyze_python_files(self):
        """Analisa arquivos Python: complexidade, estilo, etc."""
        print("\n🐍 ANALISANDO CÓDIGO PYTHON...")
        
        python_files = []
        for py_file in self.project_path.rglob("*.py"):
            # Ignorar migrações e ambientes virtuais
            if 'migrations' not in str(py_file) and 'venv' not in str(py_file) and '.env' not in str(py_file):
                python_files.append(py_file)
        
        total_lines = 0
        total_complexity = 0
        high_complexity_files = []
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = len(content.splitlines())
                    total_lines += lines
                    
                    # Análise de complexidade ciclomática
                    try:
                        complexity = cc_visit(content)
                        if complexity:
                            total_complexity += sum(c.complexity for c in complexity)
                            # Verificar funções muito complexas
                            for comp in complexity:
                                if comp.complexity > 10:
                                    high_complexity_files.append({
                                        'file': str(py_file.relative_to(self.project_path)),
                                        'function': comp.name,
                                        'complexity': comp.complexity
                                    })
                    except:
                        pass
                    
                    # Verificar imports wildcard
                    if 'from .* import \*' in content or 'from modules import \*' in content:
                        self.results['recommendations'].append(
                            f"⚠️ Evite imports com * em {py_file.relative_to(self.project_path)}"
                        )
                    
            except Exception as e:
                print(f"  Erro ao analisar {py_file}: {e}")
        
        self.results['code_quality']['total_py_files'] = len(python_files)
        self.results['code_quality']['total_lines'] = total_lines
        self.results['code_quality']['avg_complexity'] = total_complexity / len(python_files) if python_files else 0
        
        if high_complexity_files:
            self.results['recommendations'].append(
                f"⚠️ {len(high_complexity_files)} funções com alta complexidade (>10)"
            )
            for item in high_complexity_files[:5]:  # Mostrar apenas 5
                print(f"  - {item['file']}: {item['function']} (complexidade: {item['complexity']})")
        
        print(f"✅ {len(python_files)} arquivos Python, {total_lines} linhas de código")
        print(f"📊 Complexidade média: {self.results['code_quality']['avg_complexity']:.1f}")
    
    def analyze_django_apps(self):
        """Análise específica para Django"""
        print("\n🎯 ANALISANDO APPS DJANGO...")
        
        for app in self.apps:
            app_path = self.project_path / "apps" / app
            if not app_path.exists():
                continue
                
            # Verificar arquivos essenciais
            essential_files = ['models.py', 'views.py', 'urls.py', 'apps.py']
            for ef in essential_files:
                if not (app_path / ef).exists():
                    self.results['recommendations'].append(
                        f"⚠️ App '{app}' não tem {ef} (pode ser intencional, mas verifique)"
                    )
            
            # Verificar models
            models_file = app_path / "models.py"
            if models_file.exists():
                with open(models_file, 'r') as f:
                    content = f.read()
                    
                    # Verificar se tem __str__ method
                    if 'def __str__' not in content:
                        self.results['recommendations'].append(
                            f"⚠️ App '{app}' - Model sem método __str__"
                        )
                    
                    # Verificar Meta class
                    if 'class Meta' not in content:
                        self.results['recommendations'].append(
                            f"⚠️ App '{app}' - Model sem class Meta (verbose_name, etc.)"
                        )
                    
                    # Verificar índices
                    if 'index_together' not in content and 'Meta.indexes' not in content:
                        self.results['recommendations'].append(
                            f"💡 App '{app}' - Considere adicionar índices para consultas frequentes"
                        )
            
            # Verificar views - separação de responsabilidades
            views_file = app_path / "views.py"
            if views_file.exists():
                with open(views_file, 'r') as f:
                    content = f.read()
                    
                    # Verificar uso de class-based views
                    if 'def ' in content and 'View' not in content:
                        self.results['recommendations'].append(
                            f"💡 App '{app}' - Considere usar Class-based Views para melhor organização"
                        )
                    
                    # Verificar lógica de negócio nas views
                    if re.search(r'Transaction\.objects\.', content) and 'services' not in content:
                        self.results['recommendations'].append(
                            f"⚠️ App '{app}' - App com lógica de negócio nas views. Considere services.py"
                        )
        
        # Verificar uso de django-allauth
        accounts_app = self.project_path / "apps" / "accounts"
        profiles_app = self.project_path / "apps" / "profiles"
        
        if accounts_app.exists() and profiles_app.exists():
            profiles_models = profiles_app / "models.py"
            if profiles_models.exists():
                with open(profiles_models, 'r') as f:
                    if 'OneToOneField' not in f.read():
                        self.results['recommendations'].append(
                            "⚠️ App profiles não tem OneToOneField com User do allauth"
                        )
        
        print(f"✅ Analisados {len(self.apps)} apps Django")
    
    def analyze_static_files(self):
        """Análise de arquivos estáticos (CSS/JS)"""
        print("\n🎨 VERIFICANDO ORGANIZAÇÃO DE STATIC...")
        
        static_dir = self.project_path / "static"
        if not static_dir.exists():
            self.results['recommendations'].append("❌ Diretório static não encontrado")
            return
        
        # Verificar estrutura CSS
        css_dir = static_dir / "css"
        if css_dir.exists():
            css_files = list(css_dir.rglob("*.css"))
            has_module_structure = any(d.name in ['components', 'layouts', 'pages'] for d in css_dir.iterdir() if d.is_dir())
            
            if not has_module_structure and len(css_files) > 5:
                self.results['recommendations'].append(
                    "💡 Considere organizar CSS em subpastas (components/, layouts/, pages/)"
                )
        
        # Verificar estrutura JS
        js_dir = static_dir / "js"
        if js_dir.exists():
            js_files = list(js_dir.rglob("*.js"))
            
            # Verificar modularização
            has_modules = any(d.name in ['core', 'components', 'pages', 'services'] for d in js_dir.iterdir() if d.is_dir())
            
            if not has_modules and len(js_files) > 10:
                self.results['recommendations'].append(
                    "💡 Considere organizar JavaScript em módulos (core/, components/, pages/, services/)"
                )
            
            # Verificar arquivo principal
            if not (js_dir / "main.js").exists():
                self.results['recommendations'].append(
                    "⚠️ Adicione um arquivo main.js como entry point do JavaScript"
                )
        
        print(f"✅ {len(list(static_dir.rglob('*.*')))} arquivos estáticos")
    
    def check_security(self):
        """Verificações de segurança"""
        print("\n🔒 VERIFICANDO SEGURANÇA...")
        
        # Verificar .gitignore
        gitignore = self.project_path / ".gitignore"
        if gitignore.exists():
            with open(gitignore, 'r') as f:
                content = f.read()
                sensitive_patterns = ['.env', '*.pyc', '__pycache__', 'staticfiles', 'media', 'logs']
                missing_patterns = [p for p in sensitive_patterns if p not in content]
                
                if missing_patterns:
                    self.results['recommendations'].append(
                        f"⚠️ .gitignore faltando padrões: {', '.join(missing_patterns)}"
                    )
        
        # Verificar .env
        env_file = self.project_path / ".env"
        if not env_file.exists():
            self.results['recommendations'].append("❌ Arquivo .env não encontrado (variáveis de ambiente)")
        else:
            # Verificar se .env tem as variáveis essenciais
            with open(env_file, 'r') as f:
                env_vars = f.read()
                essential_vars = ['SECRET_KEY', 'DEBUG', 'DATABASE_URL', 'ALLOWED_HOSTS']
                missing_vars = [v for v in essential_vars if v not in env_vars]
                
                if missing_vars:
                    self.results['recommendations'].append(
                        f"⚠️ .env faltando variáveis: {', '.join(missing_vars)}"
                    )
        
        # Verificar settings de produção
        prod_settings = self.project_path / "config/settings/prod.py"
        if prod_settings.exists():
            with open(prod_settings, 'r') as f:
                content = f.read()
                
                if 'DEBUG = False' not in content:
                    self.results['recommendations'].append(
                        "❌ Configuração de produção com DEBUG=False faltando"
                    )
                
                if 'ALLOWED_HOSTS' not in content:
                    self.results['recommendations'].append(
                        "❌ ALLOWED_HOSTS não configurado no prod.py"
                    )
                
                if 'CSRF_COOKIE_SECURE' not in content:
                    self.results['recommendations'].append(
                        "⚠️ Configure CSRF_COOKIE_SECURE=True em produção"
                    )
        
        print("✅ Verificações de segurança concluídas")
    
    def check_tests(self):
        """Verificar cobertura de testes"""
        print("\n🧪 VERIFICANDO TESTES...")
        
        test_files = []
        for test_file in self.project_path.rglob("test*.py"):
            if 'migrations' not in str(test_file):
                test_files.append(test_file)
        
        # Verificar pytest.ini ou setup.cfg
        has_test_config = (self.project_path / "pytest.ini").exists() or \
                         (self.project_path / "setup.cfg").exists() or \
                         (self.project_path / ".coveragerc").exists()
        
        if not test_files:
            self.results['recommendations'].append(
                "❌ Nenhum arquivo de teste encontrado! Implemente testes unitários."
            )
        else:
            self.results['code_quality']['test_files'] = len(test_files)
            print(f"✅ {len(test_files)} arquivos de teste encontrados")
            
            # Verificar se cada app tem sua pasta tests
            apps_without_tests = []
            for app in self.apps:
                app_test_dir = self.project_path / "apps" / app / "tests"
                if not app_test_dir.exists():
                    apps_without_tests.append(app)
            
            if apps_without_tests:
                self.results['recommendations'].append(
                    f"⚠️ Apps sem pasta tests/: {', '.join(apps_without_tests)}"
                )
        
        if not has_test_config:
            self.results['recommendations'].append(
                "💡 Considere adicionar pytest.ini ou .coveragerc para configuração de testes"
            )
    
    def generate_report(self):
        """Gera relatório final"""
        print("\n" + "="*60)
        print("📊 RELATÓRIO FINAL DE QUALIDADE")
        print("="*60)
        
        # Pontuação de qualidade
        total_checks = 0
        passed_checks = 0
        
        # Calcular pontuação baseada nas recomendações
        critical_issues = len([r for r in self.results['recommendations'] if r.startswith('❌')])
        warnings = len([r for r in self.results['recommendations'] if r.startswith('⚠️')])
        suggestions = len([r for r in self.results['recommendations'] if r.startswith('💡')])
        
        # Métricas
        print("\n📈 MÉTRICAS DO PROJETO:")
        print(f"  • Arquivos Python: {self.results['code_quality'].get('total_py_files', 0)}")
        print(f"  • Linhas de código: {self.results['code_quality'].get('total_lines', 0)}")
        print(f"  • Apps Django: {len(self.apps)}")
        print(f"  • Complexidade média: {self.results['code_quality'].get('avg_complexity', 0):.1f}")
        print(f"  • Testes: {self.results['code_quality'].get('test_files', 0)} arquivos")
        
        # Pontuação
        total_score = 100
        total_score -= critical_issues * 10
        total_score -= warnings * 5
        total_score -= suggestions * 1
        
        total_score = max(0, min(100, total_score))
        
        # Classificação
        if total_score >= 90:
            grade = "A 🏆"
            message = "Excelente! Projeto muito bem estruturado!"
        elif total_score >= 70:
            grade = "B 👍"
            message = "Bom trabalho! Pequenas melhorias recomendadas."
        elif total_score >= 50:
            grade = "C ⚠️"
            message = "Projeto razoável, mas requer atenção em vários pontos."
        else:
            grade = "D 🔴"
            message = "Projeto precisa de melhorias significativas."
        
        print(f"\n🎯 NOTA FINAL: {total_score}/100 - {grade}")
        print(f"   {message}")
        
        # Lista de recomendações
        if self.results['recommendations']:
            print(f"\n📋 RECOMENDAÇÕES ({len(self.results['recommendations'])}):")
            print("-" * 60)
            
            for i, rec in enumerate(sorted(self.results['recommendations']), 1):
                print(f"{i}. {rec}")
        else:
            print("\n🎉 Parabéns! Nenhuma recomendação pendente!")
        
        # Salvar relatório
        report_file = self.project_path / "quality_report.json"
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'score': total_score,
                'grade': grade,
                'metrics': self.results['code_quality'],
                'recommendations': self.results['recommendations'],
                'critical_issues': critical_issues,
                'warnings': warnings,
                'suggestions': suggestions
            }, f, indent=2)
        
        print(f"\n💾 Relatório detalhado salvo em: {report_file}")
        print("\n✨ Análise concluída!")

def main():
    """Função principal"""
    project_path = Path.cwd()
    
    # Verificar se está no diretório correto
    if not (project_path / "manage.py").exists():
        print("❌ Erro: Execute este script na raiz do projeto Django (onde está manage.py)")
        sys.exit(1)
    
    analyzer = ProjectAnalyzer(project_path)
    analyzer.analyze_all()

if __name__ == "__main__":
    main()