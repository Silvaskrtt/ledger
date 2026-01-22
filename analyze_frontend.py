"""
ANALISADOR COMPLETO DO FRONTEND
Analisa CSS, JS, HTML e estrutura do frontend para refatoração
"""

import os
import re
import json
import glob
from pathlib import Path
from collections import defaultdict, Counter
import datetime

class FrontendAnalyzer:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.frontend_path = self.project_root / "frontend"
        self.static_path = self.frontend_path / "static"
        self.templates_path = self.frontend_path / "templates"
        
        self.analysis = {
            "metadata": {},
            "css_analysis": {},
            "js_analysis": {},
            "html_analysis": {},
            "scss_analysis": {},
            "conflicts": [],
            "recommendations": [],
            "refactoring_plan": {}
        }
    
    def analyze_complete_frontend(self):
        """Executa análise completa do frontend"""
        print("🎨 INICIANDO ANÁLISE DO FRONTEND")
        print("="*60)
        
        # Verificar se frontend existe
        if not self.frontend_path.exists():
            print("❌ Pasta frontend não encontrada!")
            return None
        
        print("📊 Coletando metadados...")
        self.analyze_metadata()
        
        print("🎨 Analisando CSS...")
        self.analyze_css_structure()
        
        print("📝 Analisando SCSS/Sass...")
        self.analyze_scss_usage()
        
        print("⚡ Analisando JavaScript...")
        self.analyze_javascript()
        
        print("📄 Analisando Templates HTML...")
        self.analyze_html_templates()
        
        print("🔍 Buscando conflitos CSS...")
        self.find_css_conflicts()
        
        print("💡 Gerando recomendações...")
        self.generate_recommendations()
        
        print("📋 Criando plano de refatoração...")
        self.create_refactoring_plan()
        
        return self.analysis
    
    def analyze_metadata(self):
        """Analisa metadados do frontend"""
        css_files = list(self.static_path.rglob("*.css"))
        js_files = list(self.static_path.rglob("*.js"))
        html_files = list(self.templates_path.rglob("*.html"))
        scss_files = list(self.static_path.rglob("*.scss"))
        
        self.analysis["metadata"] = {
            "total_css_files": len(css_files),
            "total_js_files": len(js_files),
            "total_html_templates": len(html_files),
            "total_scss_files": len(scss_files),
            "css_size_kb": self.calculate_total_size(css_files),
            "js_size_kb": self.calculate_total_size(js_files),
            "analysis_date": datetime.datetime.now().isoformat(),
            "frontend_structure": self.get_frontend_structure()
        }
    
    def analyze_css_structure(self):
        """Analisa estrutura e organização do CSS"""
        css_structure = {
            "by_directory": defaultdict(list),
            "total_selectors": 0,
            "total_rules": 0,
            "selector_types": Counter(),
            "css_methodologies": self.detect_css_methodologies(),
            "specificity_issues": [],
            "duplicate_selectors": [],
            "unused_selectors": []
        }
        
        # Analisar todos arquivos CSS
        css_files = list(self.static_path.rglob("*.css"))
        
        for css_file in css_files:
            rel_path = css_file.relative_to(self.static_path)
            directory = str(rel_path.parent)
            
            try:
                with open(css_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Adicionar à estrutura por diretório
                css_structure["by_directory"][directory].append(str(rel_path))
                
                # Analisar conteúdo CSS
                file_analysis = self.analyze_css_file(content)
                css_structure["total_selectors"] += file_analysis["selectors_count"]
                css_structure["total_rules"] += file_analysis["rules_count"]
                
                # Contar tipos de seletores
                for selector_type, count in file_analysis["selector_types"].items():
                    css_structure["selector_types"][selector_type] += count
                
                # Verificar especificidade
                specificity_issues = self.check_css_specificity(content, str(rel_path))
                css_structure["specificity_issues"].extend(specificity_issues)
                
            except Exception as e:
                print(f"Erro ao analisar {css_file}: {e}")
        
        self.analysis["css_analysis"] = css_structure
    
    def analyze_css_file(self, content):
        """Analisa um arquivo CSS individual"""
        # Remover comentários
        content_no_comments = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Contar seletores
        selectors = re.findall(r'([^{]+)\{', content_no_comments)
        selectors_count = len(selectors)
        
        # Contar regras
        rules_count = content_no_comments.count('{')
        
        # Analisar tipos de seletores
        selector_types = Counter()
        for selector in selectors:
            selector = selector.strip()
            
            # Class
            if '.' in selector and ':' not in selector.split('.')[0]:
                selector_types['class'] += 1
            # ID
            elif '#' in selector:
                selector_types['id'] += 1
            # Tag
            elif re.match(r'^[a-zA-Z][a-zA-Z0-9]*$', selector.split(':')[0].strip()):
                selector_types['tag'] += 1
            # Pseudo-classes/elements
            elif ':' in selector:
                selector_types['pseudo'] += 1
            # Attribute selectors
            elif '[' in selector:
                selector_types['attribute'] += 1
            else:
                selector_types['other'] += 1
        
        return {
            "selectors_count": selectors_count,
            "rules_count": rules_count,
            "selector_types": dict(selector_types)
        }
    
    def detect_css_methodologies(self):
        """Detecta metodologias CSS utilizadas"""
        methodologies = {
            "bem": False,
            "oocss": False,
            "smacss": False,
            "itcss": False,
            "atomic": False,
            "custom": True  # Assume custom por padrão
        }
        
        # Verificar padrões BEM
        bem_patterns = [r'__', r'--', r'block__element--modifier']
        css_files = list(self.static_path.rglob("*.css"))
        
        for css_file in css_files[:5]:  # Verificar apenas alguns arquivos
            try:
                with open(css_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    if any(pattern in content for pattern in bem_patterns):
                        methodologies["bem"] = True
                    
                    # Verificar OOCSS (separação estrutura vs skin)
                    if 'width:' in content and 'color:' in content:
                        methodologies["oocss"] = True
                    
                    # Verificar Atomic CSS (classes muito pequenas)
                    lines = content.split('\n')
                    short_rules = 0
                    for line in lines:
                        if '{' in line and '}' in line:
                            rule_content = line[line.find('{')+1:line.find('}')]
                            if len(rule_content.strip()) < 30:
                                short_rules += 1
                    
                    if short_rules > len(lines) * 0.3:  # 30% das regras são curtas
                        methodologies["atomic"] = True
                        
            except:
                continue
        
        return methodologies
    
    def check_css_specificity(self, content, filepath):
        """Verifica problemas de especificidade CSS"""
        issues = []
        
        # Encontrar seletores com alta especificidade
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if '{' in line and not line.startswith('@'):
                selector = line[:line.find('{')].strip()
                
                # Verificar especificidade
                id_count = selector.count('#')
                class_count = selector.count('.')
                tag_count = len(re.findall(r'(^|\s)[a-zA-Z][a-zA-Z0-9]*($|\s|\.|#|\[)', selector))
                
                # Heurística: mais de 3 classes ou IDs é problemático
                if class_count > 3 or id_count > 1:
                    issues.append({
                        "file": filepath,
                        "line": i,
                        "selector": selector,
                        "specificity": f"ids:{id_count}, classes:{class_count}, tags:{tag_count}",
                        "issue": "Alta especificidade - difícil sobrescrever"
                    })
                
                # Seletores muito longos
                if len(selector) > 100:
                    issues.append({
                        "file": filepath,
                        "line": i,
                        "selector": selector[:50] + "...",
                        "issue": "Seletor muito longo"
                    })
        
        return issues
    
    def analyze_scss_usage(self):
        """Analisa uso de SCSS/Sass"""
        scss_files = list(self.static_path.rglob("*.scss"))
        
        scss_analysis = {
            "has_scss": len(scss_files) > 0,
            "scss_files": [str(f.relative_to(self.static_path)) for f in scss_files],
            "scss_features_used": self.detect_scss_features(),
            "compilation_check": self.check_scss_compilation(),
            "import_structure": self.analyze_scss_imports()
        }
        
        # Verificar se SCSS está sendo usado corretamente
        if scss_analysis["has_scss"]:
            # Verificar se há CSS compilado dos arquivos SCSS
            css_files = list(self.static_path.rglob("*.css"))
            scss_basenames = [f.stem for f in scss_files]
            css_basenames = [f.stem for f in css_files]
            
            # Verificar quais arquivos SCSS têm CSS correspondente
            compiled = []
            not_compiled = []
            for scss_file in scss_files:
                css_name = scss_file.stem + '.css'
                css_path = scss_file.with_suffix('.css')
                if css_path.exists():
                    compiled.append(str(scss_file.relative_to(self.static_path)))
                else:
                    not_compiled.append(str(scss_file.relative_to(self.static_path)))
            
            scss_analysis["compilation_status"] = {
                "compiled": compiled,
                "not_compiled": not_compiled
            }
        
        self.analysis["scss_analysis"] = scss_analysis
    
    def detect_scss_features(self):
        """Detecta quais features do SCSS estão sendo usadas"""
        features = {
            "variables": False,
            "nesting": False,
            "mixins": False,
            "extends": False,
            "functions": False,
            "imports": False,
            "partials": False
        }
        
        scss_files = list(self.static_path.rglob("*.scss"))
        
        for scss_file in scss_files:
            try:
                with open(scss_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    if '$' in content:
                        features["variables"] = True
                    
                    if '&' in content:
                        features["nesting"] = True
                    
                    if '@mixin' in content:
                        features["mixins"] = True
                    
                    if '@extend' in content:
                        features["extends"] = True
                    
                    if '@function' in content:
                        features["functions"] = True
                    
                    if '@import' in content:
                        features["imports"] = True
                    
                    if scss_file.name.startswith('_'):
                        features["partials"] = True
                        
            except:
                continue
        
        return features
    
    def check_scss_compilation(self):
        """Verifica configuração de compilação SCSS"""
        # Verificar por config files comuns
        config_files = [
            "package.json",
            "webpack.config.js",
            "gulpfile.js",
            "gruntfile.js",
            "vite.config.js"
        ]
        
        config_found = []
        for config in config_files:
            config_path = self.project_root / config
            if config_path.exists():
                config_found.append(config)
        
        return {
            "config_files": config_found,
            "recommended_tool": "sass" if config_found else "Recomendo usar sass CLI ou Vite"
        }
    
    def analyze_scss_imports(self):
        """Analisa estrutura de imports do SCSS"""
        imports_structure = defaultdict(list)
        
        scss_files = list(self.static_path.rglob("*.scss"))
        main_scss = self.static_path / "scss" / "styles.scss"
        
        if main_scss.exists():
            try:
                with open(main_scss, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines:
                        if '@import' in line or '@use' in line:
                            imports_structure["main_imports"].append(line.strip())
            except:
                pass
        
        return dict(imports_structure)
    
    def analyze_javascript(self):
        """Analisa estrutura JavaScript"""
        js_analysis = {
            "modules_by_directory": defaultdict(list),
            "total_functions": 0,
            "total_event_listeners": 0,
            "ajax_calls": [],
            "global_variables": [],
            "code_patterns": self.detect_js_patterns(),
            "potential_issues": []
        }
        
        js_files = list(self.static_path.rglob("*.js"))
        
        for js_file in js_files:
            rel_path = js_file.relative_to(self.static_path)
            directory = str(rel_path.parent)
            
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                js_analysis["modules_by_directory"][directory].append(str(rel_path))
                
                # Análise básica
                function_count = content.count('function ') + content.count('=>')
                js_analysis["total_functions"] += function_count
                
                # Event listeners
                event_patterns = ['.addEventListener', '.onclick', '.onchange', '.onsubmit']
                for pattern in event_patterns:
                    js_analysis["total_event_listeners"] += content.count(pattern)
                
                # AJAX calls
                ajax_patterns = ['fetch(', 'axios.', '$.ajax', 'XMLHttpRequest']
                for pattern in ajax_patterns:
                    if pattern in content:
                        js_analysis["ajax_calls"].append({
                            "file": str(rel_path),
                            "pattern": pattern
                        })
                
                # Global variables (potenciais problemas)
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    line = line.strip()
                    if line and not line.startswith(('//', '/*')):
                        # Verificar declarações sem var/let/const
                        if re.match(r'^[a-zA-Z_$][a-zA-Z0-9_$]*\s*=', line):
                            if not line.startswith(('var ', 'let ', 'const ', 'function ')):
                                js_analysis["global_variables"].append({
                                    "file": str(rel_path),
                                    "line": i,
                                    "variable": line.split('=')[0].strip()
                                })
                
            except Exception as e:
                print(f"Erro ao analisar {js_file}: {e}")
        
        self.analysis["js_analysis"] = js_analysis
    
    def detect_js_patterns(self):
        """Detecta padrões JavaScript utilizados"""
        patterns = {
            "modules_es6": False,
            "jquery": False,
            "vanilla_js": True,  # Assume vanilla por padrão
            "state_management": False,
            "component_based": False
        }
        
        js_files = list(self.static_path.rglob("*.js"))
        
        for js_file in js_files[:10]:  # Analisar apenas alguns
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    if 'import ' in content or 'export ' in content:
                        patterns["modules_es6"] = True
                    
                    if '$(' in content or 'jQuery' in content:
                        patterns["jquery"] = True
                        patterns["vanilla_js"] = False
                    
                    if 'state-manager' in str(js_file) or 'app-state' in str(js_file):
                        patterns["state_management"] = True
                    
                    if 'class ' in content and 'extends' in content:
                        patterns["component_based"] = True
                        
            except:
                continue
        
        return patterns
    
    def analyze_html_templates(self):
        """Analisa templates HTML"""
        html_analysis = {
            "templates_by_directory": defaultdict(list),
            "total_templates": 0,
            "template_inheritance": self.check_template_inheritance(),
            "css_classes_used": [],
            "js_integration": self.check_js_integration(),
            "responsive_check": self.check_responsive_design()
        }
        
        html_files = list(self.templates_path.rglob("*.html"))
        html_analysis["total_templates"] = len(html_files)
        
        for html_file in html_files:
            rel_path = html_file.relative_to(self.templates_path)
            directory = str(rel_path.parent)
            html_analysis["templates_by_directory"][directory].append(str(rel_path))
        
        self.analysis["html_analysis"] = html_analysis
    
    def check_template_inheritance(self):
        """Verifica herança de templates Django"""
        base_template = self.templates_path / "base.html"
        
        if not base_template.exists():
            return {"has_base_template": False}
        
        try:
            with open(base_template, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificar blocks
            blocks = re.findall(r'\{% block (\w+)', content)
            
            # Verificar templates que estendem base
            extending_templates = []
            html_files = list(self.templates_path.rglob("*.html"))
            
            for html_file in html_files:
                if html_file.name != "base.html":
                    try:
                        with open(html_file, 'r', encoding='utf-8') as f:
                            if '{% extends "base.html" %}' in f.read():
                                extending_templates.append(str(html_file.relative_to(self.templates_path)))
                    except:
                        pass
            
            return {
                "has_base_template": True,
                "blocks_defined": blocks,
                "templates_extending": extending_templates,
                "extends_count": len(extending_templates)
            }
        except:
            return {"has_base_template": False}
    
    def check_js_integration(self):
        """Verifica integração JavaScript nos templates"""
        integration = {
            "inline_js": False,
            "external_js": [],
            "event_handlers_inline": False
        }
        
        html_files = list(self.templates_path.rglob("*.html"))
        
        for html_file in html_files[:5]:  # Verificar alguns templates
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    if '<script>' in content:
                        integration["inline_js"] = True
                    
                    # Encontrar scripts externos
                    script_tags = re.findall(r'<script[^>]+src="([^"]+)"', content)
                    integration["external_js"].extend(script_tags)
                    
                    if 'onclick="' in content or 'onchange="' in content:
                        integration["event_handlers_inline"] = True
                        
            except:
                continue
        
        # Remover duplicados
        integration["external_js"] = list(set(integration["external_js"]))
        
        return integration
    
    def check_responsive_design(self):
        """Verifica implementação de design responsivo"""
        responsive = {
            "has_viewport": False,
            "media_queries": False,
            "flexbox_grid": False
        }
        
        # Verificar viewport em templates
        html_files = list(self.templates_path.rglob("*.html"))
        for html_file in html_files[:3]:
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    if 'viewport' in f.read():
                        responsive["has_viewport"] = True
                        break
            except:
                pass
        
        # Verificar media queries em CSS
        css_files = list(self.static_path.rglob("*.css"))
        for css_file in css_files[:5]:
            try:
                with open(css_file, 'r', encoding='utf-8') as f:
                    if '@media' in f.read():
                        responsive["media_queries"] = True
                        break
            except:
                pass
        
        # Verificar uso de flexbox/grid
        for css_file in css_files[:5]:
            try:
                with open(css_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'display: flex' in content or 'display: grid' in content:
                        responsive["flexbox_grid"] = True
                        break
            except:
                pass
        
        return responsive
    
    def find_css_conflicts(self):
        """Encontra conflitos e problemas no CSS"""
        conflicts = []
        
        # 1. Verificar seletores duplicados
        css_files = list(self.static_path.rglob("*.css"))
        all_selectors = defaultdict(list)
        
        for css_file in css_files:
            try:
                with open(css_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Remover comentários
                    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
                    
                    # Encontrar todos seletores
                    selector_blocks = re.findall(r'([^{]+)\{([^}]+)\}', content)
                    
                    for selector, rules in selector_blocks:
                        selector = selector.strip()
                        if selector:  # Ignorar vazios
                            all_selectors[selector].append({
                                "file": str(css_file.relative_to(self.static_path)),
                                "rules": rules.strip()
                            })
            except:
                continue
        
        # Identificar seletores duplicados
        for selector, occurrences in all_selectors.items():
            if len(occurrences) > 1:
                conflicts.append({
                    "type": "duplicate_selector",
                    "selector": selector,
                    "occurrences": occurrences,
                    "severity": "medium"
                })
        
        # 2. Verificar regras !important
        for css_file in css_files:
            try:
                with open(css_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for i, line in enumerate(lines, 1):
                        if '!important' in line:
                            conflicts.append({
                                "type": "important_override",
                                "file": str(css_file.relative_to(self.static_path)),
                                "line": i,
                                "content": line.strip(),
                                "severity": "high"
                            })
            except:
                continue
        
        # 3. Verificar conflitos de z-index sem organização
        zindex_values = []
        for css_file in css_files:
            try:
                with open(css_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    zindex_matches = re.findall(r'z-index\s*:\s*([^;]+)', content)
                    for match in zindex_matches:
                        zindex_values.append({
                            "file": str(css_file.relative_to(self.static_path)),
                            "value": match.strip()
                        })
            except:
                continue
        
        if len(zindex_values) > 10:  # Muitos z-index podem indicar problemas
            unique_values = len(set(v["value"] for v in zindex_values))
            if unique_values > 15:  # Muitos valores diferentes
                conflicts.append({
                    "type": "z_index_chaos",
                    "description": f"Muitos valores de z-index diferentes ({unique_values})",
                    "severity": "low"
                })
        
        self.analysis["conflicts"] = conflicts
    
    def generate_recommendations(self):
        """Gera recomendações baseadas na análise"""
        recommendations = []
        analysis = self.analysis
        
        # CSS Recommendations
        css_analysis = analysis.get("css_analysis", {})
        if css_analysis.get("specificity_issues"):
            recommendations.append({
                "priority": "high",
                "category": "css",
                "title": "Reduzir especificidade CSS",
                "description": f"Encontrados {len(css_analysis['specificity_issues'])} seletores com alta especificidade",
                "action": "Refatorar seletores para usar menos classes/IDs aninhados"
            })
        
        # SCSS Recommendations
        scss_analysis = analysis.get("scss_analysis", {})
        if scss_analysis.get("has_scss") and scss_analysis.get("compilation_status", {}).get("not_compiled"):
            recommendations.append({
                "priority": "high",
                "category": "scss",
                "title": "Configurar compilação SCSS",
                "description": f"{len(scss_analysis['compilation_status']['not_compiled'])} arquivos SCSS não estão compilados",
                "action": "Configurar Sass compiler ou usar Vite/Webpack"
            })
        
        # Conflict Recommendations
        if analysis.get("conflicts"):
            duplicate_selectors = [c for c in analysis["conflicts"] if c["type"] == "duplicate_selector"]
            if duplicate_selectors:
                recommendations.append({
                    "priority": "medium",
                    "category": "css",
                    "title": "Remover seletores duplicados",
                    "description": f"Encontrados {len(duplicate_selectors)} seletores definidos em múltiplos arquivos",
                    "action": "Centralizar estilos duplicados em arquivos compartilhados"
                })
        
        # JavaScript Recommendations
        js_analysis = analysis.get("js_analysis", {})
        if js_analysis.get("global_variables"):
            recommendations.append({
                "priority": "medium",
                "category": "javascript",
                "title": "Eliminar variáveis globais",
                "description": f"Encontradas {len(js_analysis['global_variables'])} variáveis globais potenciais",
                "action": "Usar modules ES6 ou IIFE para encapsular código"
            })
        
        # Template Recommendations
        html_analysis = analysis.get("html_analysis", {})
        if html_analysis.get("js_integration", {}).get("inline_js"):
            recommendations.append({
                "priority": "low",
                "category": "html",
                "title": "Remover JavaScript inline",
                "description": "JavaScript inline encontrado em templates",
                "action": "Mover todo JavaScript para arquivos externos"
            })
        
        self.analysis["recommendations"] = recommendations
    
    def create_refactoring_plan(self):
        """Cria plano de refatoração detalhado"""
        plan = {
            "phase_1": {
                "title": "Organização Estrutural",
                "tasks": [
                    "Criar sistema de design tokens (cores, tipografia, espaçamento)",
                    "Organizar CSS por responsabilidade (base, componentes, utilitários)",
                    "Configurar compilação SCSS se necessário"
                ],
                "estimated_time": "1-2 semanas"
            },
            "phase_2": {
                "title": "Refatoração CSS",
                "tasks": [
                    "Resolver conflitos de especificidade",
                    "Remover !important desnecessários",
                    "Consolidar estilos duplicados",
                    "Implementar metodologia consistente (BEM recomendado)"
                ],
                "estimated_time": "2-3 semanas"
            },
            "phase_3": {
                "title": "Otimização JavaScript",
                "tasks": [
                    "Modularizar código JavaScript",
                    "Remover variáveis globais",
                    "Implementar padrão de state management consistente",
                    "Otimizar carregamento de scripts"
                ],
                "estimated_time": "1-2 semanas"
            },
            "phase_4": {
                "title": "Melhorias Finais",
                "tasks": [
                    "Otimizar performance (critical CSS, lazy loading)",
                    "Garantir acessibilidade",
                    "Documentar sistema de design",
                    "Criar guia de estilos para desenvolvedores"
                ],
                "estimated_time": "1 semana"
            }
        }
        
        # Adicionar recomendações específicas baseadas na análise
        specific_recommendations = []
        
        if self.analysis["css_analysis"].get("selector_types", {}).get("id", 0) > 20:
            specific_recommendations.append("Reduzir uso de IDs em seletores CSS (use classes)")
        
        if self.analysis["js_analysis"].get("code_patterns", {}).get("jquery", False):
            specific_recommendations.append("Considerar migração gradual de jQuery para Vanilla JS")
        
        if self.analysis["scss_analysis"].get("has_scss", False):
            scss_features = self.analysis["scss_analysis"].get("scss_features_used", {})
            if not scss_features.get("variables", False):
                specific_recommendations.append("Implementar variáveis SCSS para cores e tamanhos")
            if not scss_features.get("mixins", False):
                specific_recommendations.append("Criar mixins para estilos reutilizáveis")
        
        if specific_recommendations:
            plan["quick_wins"] = {
                "title": "Melhorias Rápidas",
                "tasks": specific_recommendations,
                "estimated_time": "2-3 dias"
            }
        
        self.analysis["refactoring_plan"] = plan
    
    # ========== UTILITY METHODS ==========
    
    def calculate_total_size(self, files):
        """Calcula tamanho total de arquivos em KB"""
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        return round(total_size / 1024, 2)
    
    def get_frontend_structure(self):
        """Obtém estrutura de diretórios do frontend"""
        structure = {}
        
        if self.static_path.exists():
            for item in self.static_path.iterdir():
                if item.is_dir():
                    sub_items = list(item.rglob("*"))
                    structure[item.name] = {
                        "files": len([f for f in sub_items if f.is_file()]),
                        "folders": len([f for f in sub_items if f.is_dir()])
                    }
        
        return structure
    
    def generate_report(self, output_file="frontend_analysis_report.json"):
        """Gera relatório completo em JSON"""
        report = {
            "summary": self.generate_summary(),
            "detailed_analysis": self.analysis,
            "executive_summary": self.generate_executive_summary()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Relatório salvo em: {output_file}")
        
        # Gerar também um relatório em markdown
        self.generate_markdown_report("frontend_analysis.md")
        
        return report
    
    def generate_summary(self):
        """Gera resumo executivo"""
        css_analysis = self.analysis.get("css_analysis", {})
        scss_analysis = self.analysis.get("scss_analysis", {})
        conflicts = self.analysis.get("conflicts", [])
        
        return {
            "total_css_selectors": css_analysis.get("total_selectors", 0),
            "total_css_rules": css_analysis.get("total_rules", 0),
            "using_scss": scss_analysis.get("has_scss", False),
            "conflicts_found": len(conflicts),
            "recommendations_count": len(self.analysis.get("recommendations", [])),
            "estimated_refactor_time": "4-8 semanas",
            "primary_issues": [
                "Conflitos de especificidade CSS",
                "Organização fragmentada",
                "Potenciais problemas de manutenção"
            ]
        }
    
    def generate_executive_summary(self):
        """Gera resumo para tomada de decisão"""
        return {
            "current_state": "Frontend funcional mas com organização fragmentada e conflitos CSS",
            "recommended_approach": "Refatoração incremental mantendo arquitetura atual",
            "key_benefits": [
                "Melhoria na manutenibilidade",
                "Redução de conflitos CSS",
                "Performance otimizada",
                "Base sólida para futuras features"
            ],
            "risks": [
                "Possível quebra de layout durante refatoração",
                "Curva de aprendizado para nova organização",
                "Tempo inicial de investimento"
            ],
            "mitigation_strategies": [
                "Refatorar componente por componente",
                "Manter branch de referência",
                "Testes visuais para regressões"
            ]
        }
    
    def generate_markdown_report(self, output_file="frontend_analysis.md"):
        """Gera relatório em markdown para fácil leitura"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Análise Completa do Frontend\n\n")
            f.write(f"**Data da análise:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            
            # Sumário Executivo
            f.write("## 📊 Sumário Executivo\n\n")
            summary = self.generate_summary()
            f.write(f"- **Total de seletores CSS:** {summary['total_css_selectors']}\n")
            f.write(f"- **Total de regras CSS:** {summary['total_css_rules']}\n")
            f.write(f"- **Usando SCSS:** {'Sim' if summary['using_scss'] else 'Não'}\n")
            f.write(f"- **Conflitos encontrados:** {summary['conflicts_found']}\n")
            f.write(f"- **Tempo estimado de refatoração:** {summary['estimated_refactor_time']}\n\n")
            
            # Análise CSS
            f.write("## 🎨 Análise CSS\n\n")
            css = self.analysis.get("css_analysis", {})
            f.write(f"- **Arquivos CSS:** {self.analysis['metadata']['total_css_files']}\n")
            f.write(f"- **Metodologia detectada:** {self.get_detected_methodology(css.get('css_methodologies', {}))}\n")
            
            if css.get("specificity_issues"):
                f.write(f"- **⚠️ Problemas de especificidade:** {len(css['specificity_issues'])}\n")
            
            # Análise SCSS
            scss = self.analysis.get("scss_analysis", {})
            if scss.get("has_scss"):
                f.write("\n## 🔧 Análise SCSS\n\n")
                f.write(f"- **Arquivos SCSS:** {len(scss['scss_files'])}\n")
                f.write(f"- **Features utilizadas:** {', '.join([k for k, v in scss.get('scss_features_used', {}).items() if v])}\n")
                
                if scss.get("compilation_status", {}).get("not_compiled"):
                    f.write(f"- **⚠️ Arquivos não compilados:** {len(scss['compilation_status']['not_compiled'])}\n")
            
            # Conflitos
            conflicts = self.analysis.get("conflicts", [])
            if conflicts:
                f.write("\n## ⚠️ Conflitos Detectados\n\n")
                for conflict in conflicts[:5]:  # Mostrar apenas 5
                    f.write(f"### {conflict['type'].replace('_', ' ').title()}\n")
                    f.write(f"- **Severidade:** {conflict['severity']}\n")
                    if 'selector' in conflict:
                        f.write(f"- **Seletor:** `{conflict['selector'][:50]}...`\n")
                    f.write("\n")
            
            # Recomendações
            recommendations = self.analysis.get("recommendations", [])
            if recommendations:
                f.write("\n## 💡 Recomendações Prioritárias\n\n")
                for rec in recommendations:
                    f.write(f"### {rec['title']}\n")
                    f.write(f"- **Prioridade:** {rec['priority']}\n")
                    f.write(f"- **Categoria:** {rec['category']}\n")
                    f.write(f"- **Descrição:** {rec['description']}\n")
                    f.write(f"- **Ação recomendada:** {rec['action']}\n\n")
            
            # Plano de Refatoração
            f.write("## 📋 Plano de Refatoração\n\n")
            plan = self.analysis.get("refactoring_plan", {})
            for phase_name, phase in plan.items():
                if isinstance(phase, dict):
                    f.write(f"### {phase.get('title', phase_name.replace('_', ' ').title())}\n")
                    f.write(f"**Tempo estimado:** {phase.get('estimated_time', 'N/A')}\n\n")
                    for task in phase.get('tasks', []):
                        f.write(f"- {task}\n")
                    f.write("\n")
        
        print(f"📝 Relatório Markdown salvo em: {output_file}")
    
    def get_detected_methodology(self, methodologies):
        """Retorna metodologia CSS detectada"""
        for method, used in methodologies.items():
            if used and method != "custom":
                return method.upper()
        return "Custom"
    
    def print_analysis_summary(self):
        """Imprime resumo da análise no console"""
        print("\n" + "="*60)
        print("📊 RESUMO DA ANÁLISE DO FRONTEND")
        print("="*60)
        
        metadata = self.analysis["metadata"]
        css = self.analysis["css_analysis"]
        scss = self.analysis["scss_analysis"]
        conflicts = self.analysis["conflicts"]
        recommendations = self.analysis["recommendations"]
        
        print(f"\n📁 ESTRUTURA:")
        print(f"  • Arquivos CSS: {metadata['total_css_files']}")
        print(f"  • Arquivos JS: {metadata['total_js_files']}")
        print(f"  • Templates HTML: {metadata['total_html_templates']}")
        print(f"  • Tamanho CSS: {metadata['css_size_kb']} KB")
        
        print(f"\n🎨 CSS:")
        print(f"  • Seletores: {css.get('total_selectors', 0)}")
        print(f"  • Regras: {css.get('total_rules', 0)}")
        print(f"  • Metodologia: {self.get_detected_methodology(css.get('css_methodologies', {}))}")
        print(f"  • Issues especificidade: {len(css.get('specificity_issues', []))}")
        
        print(f"\n🔧 SCSS:")
        print(f"  • Usando SCSS: {'✅ Sim' if scss.get('has_scss') else '❌ Não'}")
        if scss.get('has_scss'):
            features = scss.get('scss_features_used', {})
            used_features = [f for f, v in features.items() if v]
            print(f"  • Features: {', '.join(used_features)}")
        
        print(f"\n⚠️  CONFLITOS:")
        print(f"  • Total encontrados: {len(conflicts)}")
        conflict_types = Counter(c['type'] for c in conflicts)
        for ctype, count in conflict_types.most_common(3):
            print(f"    - {ctype}: {count}")
        
        print(f"\n💡 RECOMENDAÇÕES ({len(recommendations)}):")
        high_priority = [r for r in recommendations if r.get('priority') == 'high']
        if high_priority:
            print(f"  • Alta prioridade: {len(high_priority)}")
            for rec in high_priority[:2]:
                print(f"    - {rec['title']}")
        
        print(f"\n🔄 PLANO DE REFATORAÇÃO:")
        plan = self.analysis["refactoring_plan"]
        print(f"  • Fases: {len(plan)}")
        print(f"  • Tempo estimado: 4-8 semanas")
        
        print("\n" + "="*60)


def main():
    """Função principal"""
    print("🎨 ANALISADOR COMPLETO DO FRONTEND")
    print("="*60)
    print("Analisando estrutura para refatoração mantendo arquitetura...")
    
    analyzer = FrontendAnalyzer()
    
    try:
        # Executar análise completa
        analysis = analyzer.analyze_complete_frontend()
        
        if analysis:
            # Gerar relatórios
            analyzer.generate_report("frontend_analysis.json")
            
            # Imprimir resumo
            analyzer.print_analysis_summary()
            
            print(f"\n✅ Análise concluída com sucesso!")
            print(f"📋 Relatório JSON: frontend_analysis.json")
            print(f"📝 Relatório Markdown: frontend_analysis.md")
            
            print("\n🎯 PRÓXIMOS PASSOS:")
            print("1. Revise os relatórios gerados")
            print("2. Comece pelas recomendações de alta prioridade")
            print("3. Implemente fase por fase do plano de refatoração")
            print("4. Use testes visuais para evitar regressões")
            
    except Exception as e:
        print(f"❌ Erro durante a análise: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()