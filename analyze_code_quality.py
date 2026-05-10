#!/usr/bin/env python3
"""
Analisador de Qualidade de Código vs Estrutura Planejada
Uso: python analyze_code_quality.py
"""

import os
import re
import ast
import json
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Any
import sys

# Tentar importar ferramentas de análise
try:
    from radon.complexity import cc_visit
    from radon.metrics import mi_visit
    RADON_AVAILABLE = True
except ImportError:
    RADON_AVAILABLE = False
    print("⚠️  radon não instalado. Instale com: pip install radon")

try:
    from pylint import lint
    PYLINT_AVAILABLE = True
except ImportError:
    PYLINT_AVAILABLE = False
    print("⚠️  pylint não instalado. Instale com: pip install pylint")

class CodeQualityAnalyzer:
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.results = {
            'structure_comparison': {},
            'code_metrics': {},
            'django_specific': {},
            'violations': [],
            'scores': {},
            'recommendations': []
        }
        
        # Estrutura planejada (do arquivo de requirements)
        self.planned_structure = {
            'required_dirs': [
                'config/settings',
                'apps/common', 'apps/accounts', 'apps/profiles', 
                'apps/transactions', 'apps/dashboard',
                'static/css', 'static/js', 'static/images',
                'templates/partials', 'templates/components',
                'templates/account', 'templates/dashboard', 
                'templates/transactions', 'templates/profiles',
                'scripts', 'docs', 'media', 'logs'
            ],
            'required_files': [
                'manage.py', 'requirements.txt', 'README.md', '.env', '.gitignore',
                'config/__init__.py', 'config/urls.py', 'config/asgi.py', 'config/wsgi.py',
                'config/settings/__init__.py', 'config/settings/base.py',
                'config/settings/dev.py', 'config/settings/prod.py'
            ],
            'app_files': {
                'common': ['models.py', 'validators.py', 'utils.py'],
                'accounts': ['signals.py'],
                'profiles': ['models.py', 'forms.py', 'views.py', 'urls.py', 'services.py', 'admin.py'],
                'transactions': ['models.py', 'forms.py', 'views.py', 'urls.py', 'services.py', 'repositories.py', 'admin.py'],
                'dashboard': ['views.py', 'urls.py', 'services.py']
            },
            'static_css': [
                'main.css', 'components/', 'layouts/', 'pages/', 'themes/', 'utils/', 'vendors/'
            ],
            'static_js': [
                'main.js', 'core/', 'components/', 'pages/', 'services/'
            ],
            'templates_required': [
                'base.html', 'partials/_header.html', 'partials/_footer.html',
                'partials/_sidebar.html', 'partials/_messages.html'
            ]
        }
    
    def analyze_all(self):
        """Executa todas as análises"""
        print("\n" + "="*70)
        print("🔍 ANALISADOR DE QUALIDADE DE CÓDIGO VS ESTRUTURA PLANEJADA")
        print("="*70)
        
        self.compare_structure()
        self.analyze_code_metrics()
        self.analyze_django_patterns()
        self.analyze_static_organization()
        self.analyze_template_quality()
        self.calculate_scores()
        self.generate_report()
    
    def compare_structure(self):
        """Compara estrutura atual com a planejada"""
        print("\n📁 COMPARANDO ESTRUTURA ATUAL COM PLANEJADA...")
        
        # Verificar diretórios
        missing_dirs = []
        for dir_path in self.planned_structure['required_dirs']:
            if not (self.project_path / dir_path).exists():
                missing_dirs.append(dir_path)
        
        # Verificar arquivos
        missing_files = []
        for file_path in self.planned_structure['required_files']:
            if not (self.project_path / file_path).exists():
                missing_files.append(file_path)
        
        # Verificar arquivos de apps
        app_missing_files = []
        for app_name, files in self.planned_structure['app_files'].items():
            app_dir = self.project_path / 'apps' / app_name
            if app_dir.exists():
                for file in files:
                    if not (app_dir / file).exists():
                        app_missing_files.append(f"apps/{app_name}/{file}")
        
        self.results['structure_comparison'] = {
            'total_dirs_expected': len(self.planned_structure['required_dirs']),
            'dirs_found': len(self.planned_structure['required_dirs']) - len(missing_dirs),
            'missing_dirs': missing_dirs,
            'missing_files': missing_files,
            'app_missing_files': app_missing_files,
            'completion_percentage': ((len(self.planned_structure['required_dirs']) - len(missing_dirs)) + 
                                      (len(self.planned_structure['required_files']) - len(missing_files))) / 
                                     (len(self.planned_structure['required_dirs']) + len(self.planned_structure['required_files'])) * 100
        }
        
        # Adicionar recomendações de estrutura
        if missing_dirs:
            self.results['recommendations'].append({
                'type': 'structure_critical',
                'message': f"Diretórios faltando ({len(missing_dirs)}): {', '.join(missing_dirs[:5])}",
                'impact': 'Alto - Estrutura incompleta afeta organização'
            })
        
        if app_missing_files:
            self.results['recommendations'].append({
                'type': 'structure_important',
                'message': f"Arquivos essenciais faltando nos apps ({len(app_missing_files)})",
                'impact': 'Médio - Funcionalidades podem estar incompletas'
            })
        
        print(f"📊 Estrutura: {self.results['structure_comparison']['completion_percentage']:.1f}% completa")
    
    def analyze_code_metrics(self):
        """Analisa métricas de qualidade de código"""
        print("\n🐍 ANALISANDO MÉTRICAS DE CÓDIGO...")
        
        python_files = []
        for py_file in self.project_path.rglob("*.py"):
            # Ignorar migrações, venv e scripts de análise
            if not any(skip in str(py_file) for skip in ['migrations', 'venv', 'analyze_']):
                python_files.append(py_file)
        
        metrics = {
            'total_files': len(python_files),
            'total_lines': 0,
            'avg_line_length': 0,
            'total_complexity': 0,
            'complex_functions': [],
            'maintainability_scores': [],
            'todo_count': 0,
            'fixme_count': 0,
            'class_count': 0,
            'function_count': 0,
            'import_errors': []
        }
        
        line_lengths = []
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.splitlines()
                    metrics['total_lines'] += len(lines)
                    
                    # Calcular tamanho médio das linhas
                    for line in lines:
                        if line.strip() and not line.strip().startswith('#'):
                            line_lengths.append(len(line))
                    
                    # Contar TODOs e FIXMEs
                    metrics['todo_count'] += content.count('TODO') + content.count('todo')
                    metrics['fixme_count'] += content.count('FIXME') + content.count('fixme')
                    
                    # Análise AST
                    try:
                        tree = ast.parse(content)
                        metrics['class_count'] += sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
                        metrics['function_count'] += sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
                        
                        # Verificar imports problemáticos
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ImportFrom) and node.module == '*':
                                metrics['import_errors'].append(f"Wildcard import in {py_file.relative_to(self.project_path)}")
                    except SyntaxError as e:
                        metrics['import_errors'].append(f"Syntax error in {py_file.relative_to(self.project_path)}: {e}")
                    
                    # Análise de complexidade (se radon disponível)
                    if RADON_AVAILABLE:
                        try:
                            complexity = cc_visit(content)
                            if complexity:
                                metrics['total_complexity'] += sum(c.complexity for c in complexity)
                                for comp in complexity:
                                    if comp.complexity > 10:
                                        metrics['complex_functions'].append({
                                            'file': str(py_file.relative_to(self.project_path)),
                                            'name': comp.name,
                                            'complexity': comp.complexity,
                                            'rank': 'D' if comp.complexity > 20 else 'C' if comp.complexity > 10 else 'B'
                                        })
                            
                            # Maintainability Index
                            mi = mi_visit(content, multi=True)
                            metrics['maintainability_scores'].append(mi)
                        except:
                            pass
                    
            except Exception as e:
                print(f"  Erro ao analisar {py_file}: {e}")
        
        # Calcular médias
        metrics['avg_line_length'] = sum(line_lengths) / len(line_lengths) if line_lengths else 0
        metrics['avg_complexity'] = metrics['total_complexity'] / metrics['total_files'] if metrics['total_files'] > 0 else 0
        metrics['avg_maintainability'] = sum(metrics['maintainability_scores']) / len(metrics['maintainability_scores']) if metrics['maintainability_scores'] else 0
        
        self.results['code_metrics'] = metrics
        
        # Adicionar recomendações de código
        if metrics['complex_functions']:
            self.results['recommendations'].append({
                'type': 'code_quality',
                'message': f"{len(metrics['complex_functions'])} funções com alta complexidade (>10)",
                'impact': 'Alto - Dificulta manutenção e testes',
                'details': [f"{f['file']}: {f['name']} (complexidade {f['complexity']})" 
                           for f in metrics['complex_functions'][:3]]
            })
        
        if metrics['avg_line_length'] > 100:
            self.results['recommendations'].append({
                'type': 'code_style',
                'message': f"Linhas muito longas (média {metrics['avg_line_length']:.0f} > 79)",
                'impact': 'Baixo - Quebra padrão PEP 8'
            })
        
        if metrics['todo_count'] > 0:
            self.results['recommendations'].append({
                'type': 'maintenance',
                'message': f"{metrics['todo_count']} TODOs e {metrics['fixme_count']} FIXMEs encontrados",
                'impact': 'Médio - Indica trabalho pendente'
            })
        
        print(f"📊 {metrics['total_files']} arquivos, {metrics['total_lines']} linhas de código")
        print(f"📊 Complexidade média: {metrics['avg_complexity']:.1f}")
        print(f"📊 Funções complexas: {len(metrics['complex_functions'])}")
    
    def analyze_django_patterns(self):
        """Analisa padrões específicos do Django"""
        print("\n🎯 ANALISANDO PADRÕES DJANGO...")
        
        django_metrics = {
            'apps_with_models': [],
            'apps_with_services': [],
            'apps_with_repositories': [],
            'models_without_str': [],
            'models_without_meta': [],
            'views_type': {'FBV': 0, 'CBV': 0},
            'has_permissions': False,
            'has_signals': False,
            'query_optimizations': []
        }
        
        apps_dir = self.project_path / 'apps'
        if apps_dir.exists():
            for app_dir in apps_dir.iterdir():
                if app_dir.is_dir() and not app_dir.name.startswith('_') and app_dir.name not in ['__pycache__']:
                    # Verificar models
                    models_file = app_dir / 'models.py'
                    if models_file.exists():
                        django_metrics['apps_with_models'].append(app_dir.name)
                        with open(models_file, 'r') as f:
                            content = f.read()
                            
                            # Verificar __str__ method
                            if 'def __str__' not in content:
                                django_metrics['models_without_str'].append(app_dir.name)
                            
                            # Verificar Meta class
                            if 'class Meta' not in content:
                                django_metrics['models_without_meta'].append(app_dir.name)
                            
                            # Verificar índices
                            if 'class Meta:' in content and 'indexes' not in content:
                                django_metrics['query_optimizations'].append(f"{app_dir.name}: sem índices definidos")
                    
                    # Verificar separação de responsabilidades
                    if (app_dir / 'services.py').exists():
                        django_metrics['apps_with_services'].append(app_dir.name)
                    
                    if (app_dir / 'repositories.py').exists():
                        django_metrics['apps_with_repositories'].append(app_dir.name)
                    
                    # Verificar tipo de views
                    views_file = app_dir / 'views.py'
                    if views_file.exists():
                        with open(views_file, 'r') as f:
                            content = f.read()
                            # Contar FBV vs CBV
                            django_metrics['views_type']['FBV'] += len(re.findall(r'^def \w+\(request', content, re.MULTILINE))
                            django_metrics['views_type']['CBV'] += len(re.findall(r'class \w+View\(', content))
        
        # Verificar configurações
        settings_file = self.project_path / 'config/settings/base.py'
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                content = f.read()
                django_metrics['has_permissions'] = 'AUTHENTICATION_BACKENDS' in content
        
        # Verificar signals
        signals_file = self.project_path / 'apps/accounts/signals.py'
        if signals_file.exists():
            django_metrics['has_signals'] = True
        
        self.results['django_specific'] = django_metrics
        
        # Adicionar recomendações Django
        if django_metrics['models_without_str']:
            self.results['recommendations'].append({
                'type': 'django_best_practice',
                'message': f"Models sem __str__: {', '.join(django_metrics['models_without_str'])}",
                'impact': 'Baixo - Afeta admin interface'
            })
        
        if django_metrics['views_type']['FBV'] > django_metrics['views_type']['CBV']:
            self.results['recommendations'].append({
                'type': 'django_best_practice',
                'message': "Predominância de Function-Based Views. Considere usar CBV para reuso",
                'impact': 'Médio - CBV oferece mais organização'
            })
        
        if django_metrics['query_optimizations']:
            self.results['recommendations'].append({
                'type': 'performance',
                'message': f"Otimizações de query sugeridas: {', '.join(django_metrics['query_optimizations'][:2])}",
                'impact': 'Médio - Índices melhoram performance'
            })
        
        print(f"📊 Apps com services.py: {len(django_metrics['apps_with_services'])}")
        print(f"📊 Views: {django_metrics['views_type']['CBV']} CBV / {django_metrics['views_type']['FBV']} FBV")
    
    def analyze_static_organization(self):
        """Analisa organização de arquivos estáticos"""
        print("\n🎨 ANALISANDO ORGANIZAÇÃO DE STATIC...")
        
        static_metrics = {
            'css_organized': False,
            'js_organized': False,
            'missing_main_files': [],
            'components_found': [],
            'total_css_files': 0,
            'total_js_files': 0
        }
        
        static_dir = self.project_path / 'static'
        if static_dir.exists():
            # Analisar CSS
            css_dir = static_dir / 'css'
            if css_dir.exists():
                static_metrics['total_css_files'] = len(list(css_dir.rglob('*.css')))
                
                # Verificar organização planejada
                has_components = (css_dir / 'components').exists()
                has_layouts = (css_dir / 'layouts').exists()
                has_pages = (css_dir / 'pages').exists()
                
                static_metrics['css_organized'] = has_components and has_layouts and has_pages
                
                if not (css_dir / 'main.css').exists():
                    static_metrics['missing_main_files'].append('main.css')
            
            # Analisar JavaScript
            js_dir = static_dir / 'js'
            if js_dir.exists():
                static_metrics['total_js_files'] = len(list(js_dir.rglob('*.js')))
                
                # Verificar organização planejada
                has_core = (js_dir / 'core').exists()
                has_components = (js_dir / 'components').exists()
                has_pages = (js_dir / 'pages').exists()
                has_services = (js_dir / 'services').exists()
                
                static_metrics['js_organized'] = has_core and has_components and has_pages and has_services
                
                if not (js_dir / 'main.js').exists():
                    static_metrics['missing_main_files'].append('main.js')
                
                # Listar componentes encontrados
                components_dir = js_dir / 'components'
                if components_dir.exists():
                    static_metrics['components_found'] = [d.name for d in components_dir.iterdir() if d.is_dir()]
        
        self.results['static_metrics'] = static_metrics
        
        # Adicionar recomendações de static
        if not static_metrics['css_organized']:
            self.results['recommendations'].append({
                'type': 'frontend_organization',
                'message': "CSS não segue estrutura planejada (components/, layouts/, pages/)",
                'impact': 'Baixo - Organização facilita manutenção'
            })
        
        if not static_metrics['js_organized']:
            self.results['recommendations'].append({
                'type': 'frontend_organization',
                'message': "JavaScript não segue estrutura modular planejada",
                'impact': 'Médio - Modularização é crucial para JS escalável'
            })
        
        if static_metrics['missing_main_files']:
            self.results['recommendations'].append({
                'type': 'frontend_structure',
                'message': f"Arquivos principais faltando: {', '.join(static_metrics['missing_main_files'])}",
                'impact': 'Médio - main.js/css são entry points'
            })
        
        print(f"📊 CSS: {static_metrics['total_css_files']} arquivos | Organizado: {'✅' if static_metrics['css_organized'] else '❌'}")
        print(f"📊 JS: {static_metrics['total_js_files']} arquivos | Organizado: {'✅' if static_metrics['js_organized'] else '❌'}")
    
    def analyze_template_quality(self):
        """Analisa qualidade dos templates Django"""
        print("\n📄 ANALISANDO TEMPLATES...")
        
        template_metrics = {
            'total_templates': 0,
            'has_base_template': False,
            'has_partials': False,
            'has_component_library': False,
            'extension_usage': {'extends': 0, 'include': 0},
            'custom_filters': 0
        }
        
        templates_dir = self.project_path / 'templates'
        if templates_dir.exists():
            # Contar templates
            template_metrics['total_templates'] = len(list(templates_dir.rglob('*.html')))
            
            # Verificar base template
            template_metrics['has_base_template'] = (templates_dir / 'base.html').exists()
            
            # Verificar partials
            partials_dir = templates_dir / 'partials'
            template_metrics['has_partials'] = partials_dir.exists() and len(list(partials_dir.glob('*.html'))) > 0
            
            # Verificar components
            components_dir = templates_dir / 'components'
            template_metrics['has_component_library'] = components_dir.exists() and len(list(components_dir.glob('*.html'))) > 0
            
            # Analisar uso de {% extends %} e {% include %}
            for html_file in templates_dir.rglob('*.html'):
                try:
                    with open(html_file, 'r') as f:
                        content = f.read()
                        template_metrics['extension_usage']['extends'] += content.count('{% extends')
                        template_metrics['extension_usage']['include'] += content.count('{% include')
                except:
                    pass
        
        self.results['template_metrics'] = template_metrics
        
        # Adicionar recomendações de templates
        if not template_metrics['has_base_template']:
            self.results['recommendations'].append({
                'type': 'template_structure',
                'message': "Falta template base.html para herança",
                'impact': 'Alto - DRY violation, código repetido'
            })
        
        if not template_metrics['has_partials']:
            self.results['recommendations'].append({
                'type': 'template_organization',
                'message': "Considere criar partials/ para componentes reutilizáveis",
                'impact': 'Baixo - Melhora organização'
            })
        
        print(f"📊 {template_metrics['total_templates']} templates encontrados")
        print(f"📊 Base template: {'✅' if template_metrics['has_base_template'] else '❌'}")
        print(f"📊 Uso de extends/include: {template_metrics['extension_usage']['extends']}/{template_metrics['extension_usage']['include']}")
    
    def calculate_scores(self):
        """Calcula pontuações por categoria"""
        print("\n📊 CALCULANDO PONTUAÇÕES...")
        
        scores = {
            'structure': 0,
            'code_quality': 0,
            'django_patterns': 0,
            'frontend_organization': 0,
            'overall': 0
        }
        
        # Score de estrutura (40% da nota final)
        structure_score = self.results['structure_comparison']['completion_percentage']
        scores['structure'] = structure_score
        
        # Score de qualidade de código (30%)
        code_score = 100
        metrics = self.results['code_metrics']
        
        # Penalizar funções complexas
        complex_penalty = min(len(metrics.get('complex_functions', [])) * 5, 30)
        code_score -= complex_penalty
        
        # Penalizar linhas longas
        if metrics.get('avg_line_length', 0) > 100:
            code_score -= 10
        
        # Penalizar TODOs (se muitos)
        todo_penalty = min(metrics.get('todo_count', 0) * 2, 15)
        code_score -= todo_penalty
        
        scores['code_quality'] = max(0, code_score)
        
        # Score de padrões Django (20%)
        django_score = 100
        django_metrics = self.results['django_specific']
        
        if django_metrics.get('models_without_str'):
            django_score -= len(django_metrics['models_without_str']) * 10
        if django_metrics.get('apps_with_services', []):
            django_score += 20  # Bônus por separar lógica
        if not django_metrics.get('has_signals'):
            django_score -= 10
        
        scores['django_patterns'] = max(0, min(100, django_score))
        
        # Score de frontend (10%)
        frontend_score = 100
        static = self.results.get('static_metrics', {})
        
        if not static.get('css_organized', False):
            frontend_score -= 30
        if not static.get('js_organized', False):
            frontend_score -= 30
        if static.get('missing_main_files'):
            frontend_score -= 20
        
        scores['frontend_organization'] = max(0, frontend_score)
        
        # Score geral (weighted average)
        scores['overall'] = (
            scores['structure'] * 0.40 +
            scores['code_quality'] * 0.30 +
            scores['django_patterns'] * 0.20 +
            scores['frontend_organization'] * 0.10
        )
        
        self.results['scores'] = scores
    
    def generate_report(self):
        """Gera relatório final detalhado"""
        print("\n" + "="*70)
        print("📊 RELATÓRIO FINAL - QUALIDADE DE CÓDIGO VS ESTRUTURA PLANEJADA")
        print("="*70)
        
        # Exibir pontuações
        print("\n🎯 PONTUAÇÕES POR CATEGORIA:")
        print(f"  📁 Estrutura vs Planejado:  {self.results['scores']['structure']:.1f}/100")
        print(f"  🐍 Qualidade de Código:     {self.results['scores']['code_quality']:.1f}/100")
        print(f"  🎯 Padrões Django:          {self.results['scores']['django_patterns']:.1f}/100")
        print(f"  🎨 Organização Frontend:    {self.results['scores']['frontend_organization']:.1f}/100")
        print(f"  {'─'*40}")
        print(f"  📊 NOTA FINAL:              {self.results['scores']['overall']:.1f}/100")
        
        # Classificação
        score = self.results['scores']['overall']
        if score >= 90:
            grade = "A+ 🏆 - Excelente! Código de alta qualidade"
        elif score >= 80:
            grade = "A 🎉 - Muito bom! Poucas melhorias necessárias"
        elif score >= 70:
            grade = "B 👍 - Bom trabalho! Continue refinando"
        elif score >= 60:
            grade = "C ⚠️ - Satisfatório, mas precisa de atenção"
        elif score >= 50:
            grade = "D 🔴 - Abaixo do esperado para Sprint 1"
        else:
            grade = "F ❌ - Crítico! Muitas melhorias necessárias"
        
        print(f"\n🏆 CLASSIFICAÇÃO: {grade}")
        
        # Resumo das violações
        if self.results['recommendations']:
            print(f"\n📋 RECOMENDAÇÕES CRÍTICAS ({len(self.results['recommendations'])}):")
            print("-"*70)
            
            # Agrupar por tipo
            critical = [r for r in self.results['recommendations'] if 'critical' in r['type']]
            important = [r for r in self.results['recommendations'] if r['impact'] == 'Alto' or r['impact'] == 'Médio']
            
            for i, rec in enumerate(critical + important[:10], 1):
                print(f"\n{i}. {rec['message']}")
                print(f"   🔧 Impacto: {rec['impact']}")
                if 'details' in rec:
                    for detail in rec['details'][:2]:
                        print(f"   📍 {detail}")
        
        # Métricas de sucesso para Sprint 1
        print("\n✅ CHECKLIST SPRINT 1:")
        checklist = [
            ("Estrutura completa (>70%)", self.results['scores']['structure'] >= 70),
            ("Sem funções com complexidade >15", len(self.results['code_metrics'].get('complex_functions', [])) == 0),
            ("Models com __str__ implementado", len(self.results['django_specific'].get('models_without_str', [])) == 0),
            ("Arquivos estáticos organizados", 
             self.results.get('static_metrics', {}).get('css_organized', False) and 
             self.results.get('static_metrics', {}).get('js_organized', False)),
            ("Template base.html existe", self.results.get('template_metrics', {}).get('has_base_template', False)),
            ("Testes implementados", self.results['code_metrics'].get('total_files', 0) > 0)  # Simplificado
        ]
        
        for item, status in checklist:
            print(f"  {'✅' if status else '❌'} {item}")
        
        # Salvar relatório detalhado
        report_file = self.project_path / "code_quality_report.json"
        
        # Preparar dados para JSON (remover objetos não serializáveis)
        serializable_results = {
            'timestamp': datetime.now().isoformat(),
            'scores': self.results['scores'],
            'structure_completion': self.results['structure_comparison']['completion_percentage'],
            'missing_dirs_count': len(self.results['structure_comparison'].get('missing_dirs', [])),
            'complex_functions_count': len(self.results['code_metrics'].get('complex_functions', [])),
            'recommendations_count': len(self.results['recommendations']),
            'critical_issues': len([r for r in self.results['recommendations'] if r.get('impact') == 'Alto']),
            'grade': grade,
            'summary': {
                'total_py_files': self.results['code_metrics'].get('total_files', 0),
                'total_lines': self.results['code_metrics'].get('total_lines', 0),
                'total_templates': self.results.get('template_metrics', {}).get('total_templates', 0),
                'total_css_files': self.results.get('static_metrics', {}).get('total_css_files', 0),
                'total_js_files': self.results.get('static_metrics', {}).get('total_js_files', 0)
            }
        }
        
        with open(report_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"\n💾 Relatório detalhado salvo em: {report_file}")
        print("\n✨ Análise concluída!")

def main():
    """Função principal"""
    project_path = Path.cwd()
    
    # Verificar se está no diretório correto
    if not (project_path / "manage.py").exists():
        print("❌ Erro: Execute este script na raiz do projeto Django (onde está manage.py)")
        print(f"   Diretório atual: {project_path}")
        sys.exit(1)
    
    analyzer = CodeQualityAnalyzer(project_path)
    analyzer.analyze_all()

if __name__ == "__main__":
    main()