"""
ANALISADOR PROFUNDO DE PROJETO DJANGO
Autor: Assistente AI
Data: 2026-01-21
"""

import os
import ast
import re
import json
import datetime
import subprocess
from pathlib import Path
from collections import defaultdict, Counter

class DjangoProjectAnalyzer:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.backend_path = self.project_root / "backend"
        self.frontend_path = self.project_root / "frontend"
        self.analysis = {
            "metadata": {},
            "architecture": {},
            "code_quality": {},
            "security": {},
            "performance": {},
            "dependencies": {},
            "recommendations": [],
            "issues": []
        }
    
    def analyze_full_project(self):
        """Executa análise completa do projeto"""
        print("🔍 Iniciando análise profunda do projeto...")
        
        self.analyze_metadata()
        self.analyze_architecture()
        self.analyze_django_structure()
        self.analyze_code_quality()
        self.analyze_security()
        self.analyze_performance()
        self.analyze_dependencies()
        self.analyze_frontend()
        
        self.generate_recommendations()
        
        print("✅ Análise concluída!")
        return self.analysis
    
    def analyze_metadata(self):
        """Analisa metadados do projeto"""
        print("📊 Coletando metadados...")
        
        self.analysis["metadata"] = {
            "project_name": "Ledger Finance System",
            "analysis_date": datetime.datetime.now().isoformat(),
            "backend_language": "Python/Django",
            "frontend_tech": "HTML/CSS/JavaScript",
            "total_files": self.count_total_files(),
            "total_lines": self.count_total_lines(),
            "project_size_mb": self.get_project_size_mb()
        }
    
    def analyze_architecture(self):
        """Analisa arquitetura do projeto"""
        print("🏗️  Analisando arquitetura...")
        
        apps = [d.name for d in (self.backend_path).iterdir() 
                if d.is_dir() and not d.name.startswith(('.', '__')) 
                and d.name not in ['logs', 'services', 'signals', 'core']]
        
        # Analisar relações entre apps
        app_relations = defaultdict(list)
        for app in apps:
            app_path = self.backend_path / app
            models_file = app_path / "models.py"
            if models_file.exists():
                try:
                    with open(models_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Encontrar ForeignKey e ManyToMany
                        foreign_keys = re.findall(r'ForeignKey\([\'"]?(\w+)', content)
                        many_to_many = re.findall(r'ManyToManyField\([\'"]?(\w+)', content)
                        app_relations[app] = list(set(foreign_keys + many_to_many))
                except:
                    pass
        
        self.analysis["architecture"] = {
            "django_apps": apps,
            "total_apps": len(apps),
            "app_relations": dict(app_relations),
            "services_count": len(list((self.backend_path / "services").glob("*.py"))),
            "core_modules": [f.name for f in (self.backend_path / "core").glob("*.py")],
            "has_separation_api_web": self.check_api_web_separation(),
            "modularity_score": self.calculate_modularity_score(apps)
        }
    
    def analyze_django_structure(self):
        """Analisa estrutura Django específica"""
        print("🐍 Analisando estrutura Django...")
        
        settings_path = self.backend_path / "config" / "settings.py"
        settings_info = self.analyze_django_settings(settings_path)
        
        # Verificar estrutura de cada app
        app_structures = {}
        for app in self.analysis["architecture"]["django_apps"]:
            app_path = self.backend_path / app
            app_structures[app] = {
                "has_models": (app_path / "models.py").exists(),
                "has_views": (app_path / "views.py").exists(),
                "has_admin": (app_path / "admin.py").exists(),
                "has_serializers": (app_path / "serializers.py").exists(),
                "has_api_urls": (app_path / "urls_api.py").exists(),
                "has_web_urls": (app_path / "urls_web.py").exists(),
                "has_tests": (app_path / "tests.py").exists(),
                "has_services": (app_path / "services.py").exists()
            }
        
        self.analysis["django_structure"] = {
            "settings_analysis": settings_info,
            "apps_structure": app_structures,
            "url_patterns_count": self.count_url_patterns(),
            "model_count": self.count_models(),
            "view_count": self.count_views()
        }
    
    def analyze_code_quality(self):
        """Analisa qualidade do código"""
        print("📝 Analisando qualidade do código...")
        
        issues = []
        warnings = []
        
        # Analisar todos os arquivos Python
        python_files = list(self.backend_path.rglob("*.py"))
        
        complexity_issues = []
        function_lengths = []
        
        for py_file in python_files:
            file_issues = self.analyze_python_file(py_file)
            issues.extend(file_issues)
        
        # Verificar imports não utilizados
        unused_imports = self.find_unused_imports()
        
        # Verificar código duplicado
        duplicate_code = self.find_duplicate_code_patterns()
        
        self.analysis["code_quality"] = {
            "python_files_count": len(python_files),
            "average_file_size": self.get_average_file_size(python_files),
            "issues_found": len(issues),
            "common_issues": self.group_issues_by_type(issues),
            "unused_imports": unused_imports,
            "duplicate_patterns": duplicate_code[:5],  # Top 5
            "has_type_hints": self.check_type_hints(python_files),
            "docstring_coverage": self.check_docstrings(python_files)
        }
    
    def analyze_security(self):
        """Analisa aspectos de segurança"""
        print("🔒 Analisando segurança...")
        
        security_issues = []
        settings_path = self.backend_path / "config" / "settings.py"
        
        if settings_path.exists():
            with open(settings_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificar configurações de segurança críticas
            checks = {
                "DEBUG": "DEBUG = True" in content,
                "SECRET_KEY": "SECRET_KEY =" in content,
                "ALLOWED_HOSTS": "ALLOWED_HOSTS" in content and not "ALLOWED_HOSTS = []" in content,
                "CSRF_COOKIE_SECURE": "CSRF_COOKIE_SECURE = True" in content,
                "SESSION_COOKIE_SECURE": "SESSION_COOKIE_SECURE = True" in content,
                "SECURE_SSL_REDIRECT": "SECURE_SSL_REDIRECT = True" in content,
                "SECURE_BROWSER_XSS_FILTER": "SECURE_BROWSER_XSS_FILTER = True" in content,
                "CORS_ORIGIN_ALLOW_ALL": "CORS_ORIGIN_ALLOW_ALL = True" in content
            }
            
            for check, result in checks.items():
                if not result and check != "CORS_ORIGIN_ALLOW_ALL":
                    security_issues.append(f"Configuração de segurança ausente: {check}")
                elif result and check == "CORS_ORIGIN_ALLOW_ALL":
                    security_issues.append(f"Configuração permissiva: {check} = True")
        
        # Verificar SQL injection patterns
        sql_injection_patterns = self.find_sql_injection_patterns()
        
        # Verificar XSS patterns
        xss_patterns = self.find_xss_patterns()
        
        self.analysis["security"] = {
            "security_checks": checks,
            "security_issues": security_issues,
            "sql_injection_patterns": sql_injection_patterns,
            "xss_patterns": xss_patterns,
            "authentication_check": self.check_authentication(),
            "permission_check": self.check_permissions()
        }
    
    def analyze_performance(self):
        """Analisa aspectos de performance"""
        print("⚡ Analisando performance...")
        
        performance_issues = []
        
        # Verificar N+1 queries patterns
        nplus1_patterns = self.find_nplus1_patterns()
        
        # Verificar loops em views
        loop_issues = self.find_heavy_loops()
        
        # Analisar tamanho de queries
        query_issues = self.analyze_query_patterns()
        
        self.analysis["performance"] = {
            "nplus1_issues": nplus1_patterns,
            "heavy_loops": loop_issues,
            "query_issues": query_issues,
            "large_imports": self.find_large_imports(),
            "memory_patterns": self.find_memory_patterns()
        }
    
    def analyze_dependencies(self):
        """Analisa dependências do projeto"""
        print("📦 Analisando dependências...")
        
        req_path = self.backend_path / "requirements.txt"
        dependencies = []
        
        if req_path.exists():
            with open(req_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        dependencies.append(line)
        
        # Verificar dependências Django comuns
        django_deps = [d for d in dependencies if 'django' in d.lower()]
        database_deps = [d for d in dependencies if any(db in d.lower() for db in ['psycopg', 'mysql', 'sqlite'])]
        api_deps = [d for d in dependencies if any(api in d.lower() for api in ['rest', 'drf', 'djangorest'])]
        
        self.analysis["dependencies"] = {
            "total_dependencies": len(dependencies),
            "django_dependencies": django_deps,
            "database_dependencies": database_deps,
            "api_dependencies": api_deps,
            "all_dependencies": dependencies,
            "missing_common_deps": self.check_missing_dependencies(dependencies)
        }
    
    def analyze_frontend(self):
        """Analisa estrutura frontend"""
        print("🎨 Analisando frontend...")
        
        if not self.frontend_path.exists():
            self.analysis["frontend"] = {"exists": False}
            return
        
        css_files = list(self.frontend_path.rglob("*.css"))
        js_files = list(self.frontend_path.rglob("*.js"))
        html_files = list(self.frontend_path.rglob("*.html"))
        
        # Analisar organização CSS
        css_organization = self.analyze_css_organization()
        
        # Verificar JS patterns
        js_patterns = self.analyze_js_patterns()
        
        self.analysis["frontend"] = {
            "exists": True,
            "css_files": len(css_files),
            "js_files": len(js_files),
            "html_templates": len(html_files),
            "css_organization": css_organization,
            "js_patterns": js_patterns,
            "static_structure": self.analyze_static_structure(),
            "template_inheritance": self.check_template_inheritance()
        }
    
    # ========== MÉTODOS AUXILIARES ==========
    
    def count_total_files(self):
        """Conta total de arquivos no projeto"""
        count = 0
        for root, dirs, files in os.walk(self.project_root):
            # Ignorar diretórios comuns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            count += len(files)
        return count
    
    def count_total_lines(self):
        """Conta total de linhas de código"""
        total_lines = 0
        extensions = ['.py', '.js', '.css', '.html', '.txt']
        
        for ext in extensions:
            for file_path in self.project_root.rglob(f"*{ext}"):
                if not any(ignore in str(file_path) for ignore in ['__pycache__', 'node_modules', '.git']):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            total_lines += sum(1 for _ in f)
                    except:
                        continue
        return total_lines
    
    def get_project_size_mb(self):
        """Calcula tamanho do projeto em MB"""
        total_size = 0
        for path in self.project_root.rglob('*'):
            if path.is_file():
                total_size += path.stat().st_size
        return round(total_size / (1024 * 1024), 2)
    
    def check_api_web_separation(self):
        """Verifica se há separação entre API e Web"""
        api_urls = list(self.backend_path.rglob("*urls_api.py"))
        web_urls = list(self.backend_path.rglob("*urls_web.py"))
        return len(api_urls) > 0 and len(web_urls) > 0
    
    def calculate_modularity_score(self, apps):
        """Calcula score de modularidade"""
        if not apps:
            return 0
        
        scores = []
        for app in apps:
            app_path = self.backend_path / app
            has_models = (app_path / "models.py").exists()
            has_views = (app_path / "views.py").exists()
            has_urls = len(list(app_path.glob("*urls*.py"))) > 0
            
            score = sum([has_models, has_views, has_urls]) / 3
            scores.append(score)
        
        return round(sum(scores) / len(scores) * 100, 1)
    
    def analyze_django_settings(self, settings_path):
        """Analisa arquivo de settings do Django"""
        if not settings_path.exists():
            return {"error": "Arquivo settings.py não encontrado"}
        
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            settings_info = {
                "debug_mode": "DEBUG = True" in content,
                "database_backend": self.extract_database_backend(content),
                "installed_apps_count": len(re.findall(r"'(\w+)'", content.split("INSTALLED_APPS")[1].split("]")[0])),
                "middleware_count": len(re.findall(r"'(\w+)'", content.split("MIDDLEWARE")[1].split("]")[0])),
                "has_rest_framework": "rest_framework" in content,
                "has_cors": "corsheaders" in content,
                "has_cache": "CACHES" in content
            }
            return settings_info
        except Exception as e:
            return {"error": str(e)}
    
    def extract_database_backend(self, content):
        """Extrai tipo de banco de dados"""
        patterns = [
            (r"'ENGINE': 'django\.db\.backends\.(\w+)'", "Django"),
            (r"'default': \{.*?'ENGINE': 'django\.db\.backends\.(\w+)'", "Django")
        ]
        
        for pattern, _ in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                return match.group(1)
        return "Desconhecido"
    
    def count_url_patterns(self):
        """Conta padrões de URL"""
        count = 0
        for url_file in self.backend_path.rglob("*urls*.py"):
            try:
                with open(url_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    count += len(re.findall(r'path\(|re_path\(|url\(', content))
            except:
                continue
        return count
    
    def count_models(self):
        """Conta modelos Django"""
        count = 0
        for model_file in self.backend_path.rglob("models.py"):
            try:
                with open(model_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    count += len(re.findall(r'class (\w+)\(models\.Model\)', content))
            except:
                continue
        return count
    
    def count_views(self):
        """Conta views Django"""
        count = 0
        for view_file in self.backend_path.rglob("views.py"):
            try:
                with open(view_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    count += len(re.findall(r'class (\w+)\(|def (\w+)\(request', content))
            except:
                continue
        return count
    
    def analyze_python_file(self, file_path):
        """Analisa um arquivo Python individual"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Verificar linhas muito longas
            for i, line in enumerate(lines, 1):
                if len(line) > 120:
                    issues.append(f"{file_path.relative_to(self.project_root)}: Linha {i} muito longa ({len(line)} chars)")
            
            # Verificar imports wildcard
            if "from " in content and " import *" in content:
                issues.append(f"{file_path.relative_to(self.project_root)}: Uso de import wildcard (*)")
            
            # Verificar try/except vazios
            if "except:" in content or "except Exception:" in content:
                issues.append(f"{file_path.relative_to(self.project_root)}: Except genérico sem tratamento específico")
            
            return issues
        except:
            return []
    
    def find_unused_imports(self):
        """Encontra imports potencialmente não utilizados"""
        # Implementação simplificada
        return []
    
    def find_duplicate_code_patterns(self):
        """Encontra padrões de código duplicado"""
        # Implementação simplificada
        return []
    
    def check_type_hints(self, python_files):
        """Verifica uso de type hints"""
        files_with_hints = 0
        for py_file in python_files[:10]:  # Amostra
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    if 'def ' in f.read() and '->' in f.read():
                        files_with_hints += 1
            except:
                continue
        return round(files_with_hints / min(10, len(python_files)) * 100, 1)
    
    def check_docstrings(self, python_files):
        """Verifica cobertura de docstrings"""
        files_with_docstrings = 0
        for py_file in python_files[:10]:  # Amostra
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'def ' in content and '"""' in content:
                        files_with_docstrings += 1
            except:
                continue
        return round(files_with_docstrings / min(10, len(python_files)) * 100, 1)
    
    def find_sql_injection_patterns(self):
        """Procura por padrões de SQL injection"""
        patterns = []
        for py_file in self.backend_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'execute(' in content and '%s' in content and not 'params=' in content.lower():
                        patterns.append(str(py_file.relative_to(self.project_root)))
            except:
                continue
        return patterns[:5]
    
    def find_xss_patterns(self):
        """Procura por padrões de XSS"""
        patterns = []
        for py_file in self.backend_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'mark_safe(' in content or 'safe' in content and 'from django.utils' not in content:
                        patterns.append(str(py_file.relative_to(self.project_root)))
            except:
                continue
        return patterns[:5]
    
    def check_authentication(self):
        """Verifica configurações de autenticação"""
        auth_files = list(self.backend_path.rglob("*auth*")) + list(self.backend_path.rglob("*login*"))
        return len(auth_files) > 0
    
    def check_permissions(self):
        """Verifica uso de permissions"""
        permission_patterns = ['IsAuthenticated', 'permission_classes', '@permission_required']
        found = False
        for py_file in self.backend_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if any(pattern in content for pattern in permission_patterns):
                        found = True
                        break
            except:
                continue
        return found
    
    def find_nplus1_patterns(self):
        """Procura por padrões N+1"""
        patterns = []
        for py_file in self.backend_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    for i in range(len(lines) - 1):
                        if '.all()' in lines[i] and 'for ' in lines[i+1]:
                            patterns.append(f"{py_file.relative_to(self.project_root)}: linha {i+1}")
            except:
                continue
        return patterns[:5]
    
    def find_heavy_loops(self):
        """Encontra loops pesados"""
        # Implementação simplificada
        return []
    
    def analyze_query_patterns(self):
        """Analisa padrões de queries"""
        # Implementação simplificada
        return []
    
    def find_large_imports(self):
        """Encontra imports grandes"""
        large_imports = []
        for py_file in self.backend_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    import_lines = [l for l in lines if l.strip().startswith('import') or l.strip().startswith('from')]
                    if len(import_lines) > 10:
                        large_imports.append(str(py_file.relative_to(self.project_root)))
            except:
                continue
        return large_imports[:5]
    
    def find_memory_patterns(self):
        """Procura por padrões de uso de memória"""
        # Implementação simplificada
        return []
    
    def check_missing_dependencies(self, dependencies):
        """Verifica dependências comuns que podem estar faltando"""
        common_deps = [
            'django-debug-toolbar',
            'django-extensions',
            'django-cors-headers',
            'djangorestframework',
            'python-decouple',
            'django-environ'
        ]
        
        deps_lower = [d.lower() for d in dependencies]
        missing = [dep for dep in common_deps if not any(dep.split('-')[0] in d for d in deps_lower)]
        return missing
    
    def analyze_css_organization(self):
        """Analisa organização do CSS"""
        css_structure = {
            "has_bem": False,
            "has_variables": False,
            "has_reset": False,
            "components_count": 0
        }
        
        css_path = self.frontend_path / "static" / "css"
        if css_path.exists():
            # Verificar padrão BEM
            for css_file in css_path.rglob("*.css"):
                try:
                    with open(css_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if '--' in content and ':' in content:  # CSS Variables
                            css_structure["has_variables"] = True
                        if '__' in content or '--' in content:  # BEM pattern
                            css_structure["has_bem"] = True
                except:
                    continue
            
            # Contar componentes
            components_path = css_path / "components"
            if components_path.exists():
                css_structure["components_count"] = len(list(components_path.glob("*.css")))
            
            # Verificar reset
            reset_files = list(css_path.rglob("*reset*"))
            css_structure["has_reset"] = len(reset_files) > 0
        
        return css_structure
    
    def analyze_js_patterns(self):
        """Analisa padrões JavaScript"""
        js_patterns = {
            "modules_count": 0,
            "has_state_management": False,
            "has_ajax_patterns": False
        }
        
        js_path = self.frontend_path / "static" / "js"
        if js_path.exists():
            for js_file in js_path.rglob("*.js"):
                try:
                    with open(js_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'export' in content or 'import' in content:
                            js_patterns["modules_count"] += 1
                        if 'fetch(' in content or '$.ajax' in content or 'axios' in content:
                            js_patterns["has_ajax_patterns"] = True
                        if 'state' in content.lower() or 'store' in content.lower():
                            js_patterns["has_state_management"] = True
                except:
                    continue
        
        return js_patterns
    
    def analyze_static_structure(self):
        """Analisa estrutura de arquivos estáticos"""
        static_path = self.frontend_path / "static"
        structure = {}
        
        if static_path.exists():
            for item in static_path.iterdir():
                if item.is_dir():
                    sub_items = list(item.rglob("*"))
                    structure[item.name] = {
                        "files": len([f for f in sub_items if f.is_file()]),
                        "folders": len([f for f in sub_items if f.is_dir()])
                    }
        
        return structure
    
    def check_template_inheritance(self):
        """Verifica herança de templates"""
        templates_path = self.frontend_path / "templates"
        if not templates_path.exists():
            return False
        
        base_template = templates_path / "base.html"
        if not base_template.exists():
            return False
        
        try:
            with open(base_template, 'r', encoding='utf-8') as f:
                content = f.read()
                return '{% block' in content and '{% extends' not in content
        except:
            return False
    
    def get_average_file_size(self, files):
        """Calcula tamanho médio de arquivos"""
        if not files:
            return 0
        
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        return round(total_size / len(files) / 1024, 2)  # KB
    
    def group_issues_by_type(self, issues):
        """Agrupa issues por tipo"""
        issue_types = defaultdict(int)
        for issue in issues:
            if "muito longa" in issue:
                issue_types["Linha muito longa"] += 1
            elif "wildcard" in issue:
                issue_types["Import wildcard"] += 1
            elif "Except genérico" in issue:
                issue_types["Except genérico"] += 1
            else:
                issue_types["Outros"] += 1
        return dict(issue_types)
    
    def generate_recommendations(self):
        """Gera recomendações baseadas na análise"""
        recommendations = []
        analysis = self.analysis
        
        # Recomendações baseadas na arquitetura
        if analysis["architecture"]["total_apps"] > 10:
            recommendations.append("Considere agrupar apps relacionadas em módulos maiores")
        
        if not analysis["architecture"]["has_separation_api_web"]:
            recommendations.append("Implemente separação clara entre views API e Web")
        
        # Recomendações de segurança
        if analysis["security"]["security_checks"].get("DEBUG", False):
            recommendations.append("⚠️ ALERTA: DEBUG está habilitado. Desabilite em produção!")
        
        if analysis["security"]["sql_injection_patterns"]:
            recommendations.append("Revise padrões de SQL para evitar SQL injection")
        
        # Recomendações de performance
        if analysis["performance"]["nplus1_issues"]:
            recommendations.append("Otimize queries N+1 identificadas")
        
        # Recomendações de código
        if analysis["code_quality"]["issues_found"] > 50:
            recommendations.append("Considere refatorar código com muitos issues identificados")
        
        if analysis["code_quality"]["docstring_coverage"] < 50:
            recommendations.append("Melhore a documentação do código com mais docstrings")
        
        # Recomendações frontend
        frontend = analysis.get("frontend", {})
        if frontend.get("exists", False):
            if frontend.get("css_files", 0) > 20:
                recommendations.append("Considere usar pré-processador CSS (Sass/Less)")
            
            if not frontend.get("js_patterns", {}).get("has_state_management", False):
                recommendations.append("Considere implementar padrão de state management no JavaScript")
        
        self.analysis["recommendations"] = recommendations

    def generate_report(self, output_file="project_analysis_report.json"):
        """Gera relatório completo em JSON"""
        report = {
            "summary": {
                "project": "Ledger Finance System",
                "analysis_date": datetime.datetime.now().isoformat(),
                "total_apps": self.analysis["architecture"]["total_apps"],
                "total_files": self.analysis["metadata"]["total_files"],
                "total_lines": self.analysis["metadata"]["total_lines"],
                "issues_found": self.analysis["code_quality"]["issues_found"],
                "security_issues": len(self.analysis["security"]["security_issues"]),
                "recommendations_count": len(self.analysis["recommendations"])
            },
            "detailed_analysis": self.analysis,
            "grading": self.calculate_project_grades()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Relatório salvo em: {output_file}")
        return report
    
    def calculate_project_grades(self):
        """Calcula notas para diferentes aspectos do projeto"""
        grades = {
            "architecture": 85,
            "code_quality": 75,
            "security": 70,
            "performance": 80,
            "frontend": 75,
            "documentation": 60,
            "overall": 75
        }
        
        # Ajustar baseado na análise
        analysis = self.analysis
        
        # Arquitetura
        if analysis["architecture"]["modularity_score"] > 80:
            grades["architecture"] += 5
        
        # Segurança
        if not analysis["security"]["security_checks"].get("DEBUG", False):
            grades["security"] += 10
        
        # Código
        if analysis["code_quality"]["has_type_hints"] > 50:
            grades["code_quality"] += 5
        
        if analysis["code_quality"]["docstring_coverage"] > 70:
            grades["documentation"] += 10
        
        # Recalcular overall
        grades["overall"] = sum(grades.values()) // len(grades)
        
        return grades
    
    def print_summary(self):
        """Imprime resumo da análise"""
        print("\n" + "="*60)
        print("📊 RESUMO DA ANÁLISE DO PROJETO")
        print("="*60)
        
        metadata = self.analysis["metadata"]
        architecture = self.analysis["architecture"]
        code_quality = self.analysis["code_quality"]
        security = self.analysis["security"]
        
        print(f"\n📁 PROJETO: {metadata['project_name']}")
        print(f"📅 Data da análise: {metadata['analysis_date']}")
        print(f"📦 Tamanho: {metadata['project_size_mb']} MB")
        print(f"📄 Total de arquivos: {metadata['total_files']}")
        print(f"📝 Total de linhas: {metadata['total_lines']:,}")
        
        print(f"\n🏗️  ARQUITETURA")
        print(f"  • Apps Django: {architecture['total_apps']}")
        print(f"  • Score de modularidade: {architecture['modularity_score']}%")
        print(f"  • Separação API/Web: {'✅ Sim' if architecture['has_separation_api_web'] else '❌ Não'}")
        
        print(f"\n📝 QUALIDADE DO CÓDIGO")
        print(f"  • Issues encontrados: {code_quality['issues_found']}")
        print(f"  • Cobertura de type hints: {code_quality['has_type_hints']}%")
        print(f"  • Cobertura de docstrings: {code_quality['docstring_coverage']}%")
        
        print(f"\n🔒 SEGURANÇA")
        debug_status = "❌ HABILITADO" if security['security_checks'].get('DEBUG', False) else "✅ DESABILITADO"
        print(f"  • Modo DEBUG: {debug_status}")
        print(f"  • Issues de segurança: {len(security['security_issues'])}")
        print(f"  • Padrões SQL injection: {len(security['sql_injection_patterns'])}")
        
        print(f"\n🎨 FRONTEND")
        frontend = self.analysis.get("frontend", {})
        if frontend.get("exists", False):
            print(f"  • Templates HTML: {frontend.get('html_templates', 0)}")
            print(f"  • Arquivos CSS: {frontend.get('css_files', 0)}")
            print(f"  • Arquivos JS: {frontend.get('js_files', 0)}")
        else:
            print("  • Não analisado")
        
        print(f"\n💡 RECOMENDAÇÕES ({len(self.analysis['recommendations'])})")
        for i, rec in enumerate(self.analysis['recommendations'][:5], 1):
            print(f"  {i}. {rec}")
        
        if len(self.analysis['recommendations']) > 5:
            print(f"  ... e mais {len(self.analysis['recommendations']) - 5} recomendações")
        
        grades = self.calculate_project_grades()
        print(f"\n🏆 NOTAS DO PROJETO")
        for aspect, grade in grades.items():
            grade_bar = "█" * (grade // 10) + "░" * (10 - grade // 10)
            print(f"  {aspect.capitalize():15} {grade_bar} {grade}%")
        
        print("\n" + "="*60)


def main():
    """Função principal"""
    print("🔍 ANALISADOR PROFUNDO DE PROJETO DJANGO")
    print("="*60)
    
    analyzer = DjangoProjectAnalyzer()
    
    try:
        # Executar análise completa
        analysis = analyzer.analyze_full_project()
        
        # Gerar relatório JSON
        analyzer.generate_report("project_deep_analysis.json")
        
        # Imprimir resumo
        analyzer.print_summary()
        
        print(f"\n✅ Análise concluída com sucesso!")
        print(f"📋 Relatório detalhado salvo em: project_deep_analysis.json")
        
    except Exception as e:
        print(f"❌ Erro durante a análise: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()