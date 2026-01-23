#!/usr/bin/env python3
"""
ANALISADOR DE CÓDIGOS PROBLEMÁTICOS - SISTEMA LEDGER
Analisa e extrai trechos de código específicos que precisam ser refatorados.
"""

import os
import re
from pathlib import Path
from datetime import datetime

class CodeProblemDetector:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.problematic_codes = []
        self.critical_files = []
        
    def detect_problematic_patterns(self):
        """Detecta padrões problemáticos nos arquivos críticos."""
        
        # Arquivos críticos para análise
        critical_files = [
            ('backend/services/credit_card_service.py', self.analyze_credit_card_service),
            ('backend/transactions/services/balance_service.py', self.analyze_balance_service),
            ('backend/transactions/views.py', self.analyze_transaction_views),
            ('backend/accounts/views.py', self.analyze_accounts_views),
            ('backend/transactions/services/installment_service.py', self.analyze_installment_service),
        ]
        
        for rel_path, analyzer_func in critical_files:
            file_path = self.base_path / rel_path
            if file_path.exists():
                print(f"🔍 Analisando: {rel_path}")
                analyzer_func(file_path)
                self.critical_files.append(rel_path)
            else:
                print(f"⚠️  Arquivo não encontrado: {rel_path}")
    
    def analyze_credit_card_service(self, file_path):
        """Analisa o arquivo de serviço de cartão de crédito."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Padrões problemáticos específicos
        patterns = [
            {
                'name': 'PAGAMENTO COM DIRECTION CONFUSA',
                'pattern': r'def pay_bill\(.*?\):.*?(?=def|\Z)',
                'flags': re.DOTALL,
                'description': 'Lógica complexa de direction/role para pagamentos'
            },
            {
                'name': 'VINCULAÇÃO DE TRANSAÇÕES À FATURA',
                'pattern': r'unlinked_transactions\.update\(credit_card_bill=bill\)',
                'description': 'Atualização em massa sem validação de período'
            },
            {
                'name': 'GERAÇÃO DE FATURAS FUTURAS',
                'pattern': r'generate_credit_card_bills\(.*?\):.*?(?=def|\Z)',
                'flags': re.DOTALL,
                'description': 'Lógica de geração de faturas pode estar incorreta'
            },
            {
                'name': 'CÁLCULO DE DATAS DE FATURA',
                'pattern': r'calculate_bill_dates\(.*?\):.*?(?=def|\Z)',
                'flags': re.DOTALL,
                'description': 'Lógica de cálculo de datas pode estar errada'
            }
        ]
        
        self.extract_problematic_sections(content, str(file_path), patterns)
    
    def analyze_balance_service(self, file_path):
        """Analisa o serviço de cálculo de saldo."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        patterns = [
            {
                'name': 'CÁLCULO COMPLEXO PARA CARTÕES',
                'pattern': r'if locked_account\.is_credit_card:.*?(?=if |else|\Z)',
                'flags': re.DOTALL,
                'description': 'Lógica muito complexa para cálculo de saldo de cartões'
            },
            {
                'name': 'LÓGICA CONFUSA DE DIRECTION/ROLE',
                'pattern': r'if ta\.role == [\'"]source[\'"]:.*?elif ta\.role == [\'"]destination[\'"]:',
                'flags': re.DOTALL,
                'description': 'Lógica difícil de entender para determinar efeito no saldo'
            },
            {
                'name': 'VALIDAÇÃO DE SALDO POSITIVO',
                'pattern': r'if.*?calculated_balance > 0.*?calculated_balance = 0',
                'description': 'Ajuste manual de saldo positivo - pode mascarar erros'
            }
        ]
        
        self.extract_problematic_sections(content, str(file_path), patterns)
    
    def analyze_transaction_views(self, file_path):
        """Analisa as views de transações."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        patterns = [
            {
                'name': 'EXCLUSÃO SEM ATUALIZAR FATURAS',
                'pattern': r'def destroy\(.*?\):.*?(?=def|\Z)',
                'flags': re.DOTALL,
                'description': 'Exclusão não atualiza faturas relacionadas'
            },
            {
                'name': 'SOFT DELETE SEM RECÁLCULO',
                'pattern': r'instance\.is_deleted = True.*?instance\.save\(\)',
                'flags': re.DOTALL,
                'description': 'Marca como deletado mas não recalcula dependências'
            },
            {
                'name': 'FALTA DE VERIFICAÇÃO DE PARCELAMENTO',
                'pattern': r'installment_plan.*exclude|delete.*installment',
                'description': 'Não verifica se é transação parcelada na exclusão'
            }
        ]
        
        self.extract_problematic_sections(content, str(file_path), patterns)
    
    def analyze_accounts_views(self, file_path):
        """Analisa as views de contas."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        patterns = [
            {
                'name': 'BUSCA DE FATURAS SEM FILTRO',
                'pattern': r'get_credit_card_bills\(.*?\):.*?(?=def|\Z)',
                'flags': re.DOTALL,
                'description': 'Não filtra transações deletadas na contagem'
            },
            {
                'name': 'FALTA DE ENDPOINT PARA DETALHES',
                'pattern': r'def.*transactions.*bill.*',
                'description': 'Não há endpoint para transações específicas da fatura'
            }
        ]
        
        self.extract_problematic_sections(content, str(file_path), patterns)
    
    def analyze_installment_service(self, file_path):
        """Analisa o serviço de parcelamento."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        patterns = [
            {
                'name': 'EXCLUSÃO PARCIAL DE PARCELAMENTO',
                'pattern': r'def cancel_installment_plan\(.*?\):.*?(?=def|\Z)',
                'flags': re.DOTALL,
                'description': 'Só exclui parcelas futuras, não oferece opção completa'
            },
            {
                'name': 'CRIAÇÃO DE TRANSAÇÕES INDEPENDENTES',
                'pattern': r'create_installment_transactions\(.*?\):.*?(?=def|\Z)',
                'flags': re.DOTALL,
                'description': 'Cria N transações sem relação forte entre elas'
            }
        ]
        
        self.extract_problematic_sections(content, str(file_path), patterns)
    
    def extract_problematic_sections(self, content, file_path, patterns):
        """Extrai seções problemáticas do código."""
        for pattern_info in patterns:
            pattern = pattern_info['pattern']
            flags = pattern_info.get('flags', 0)
            
            matches = re.finditer(pattern, content, flags)
            for match in matches:
                # Extrair contexto (linhas antes e depois)
                start = max(0, match.start() - 200)
                end = min(len(content), match.end() + 200)
                context = content[start:end]
                
                # Encontrar número da linha
                line_number = content[:match.start()].count('\n') + 1
                
                self.problematic_codes.append({
                    'file': Path(file_path).relative_to(self.base_path),
                    'line': line_number,
                    'pattern_name': pattern_info['name'],
                    'description': pattern_info['description'],
                    'code_snippet': self.clean_code_snippet(context),
                    'match': match.group(0)[:500]  # Primeiros 500 chars do match
                })
    
    def clean_code_snippet(self, snippet):
        """Limpa e formata o snippet de código."""
        # Remove múltiplas quebras de linha
        snippet = re.sub(r'\n{3,}', '\n\n', snippet)
        # Limita a 30 linhas
        lines = snippet.split('\n')
        if len(lines) > 30:
            return '\n'.join(lines[:15] + ['...', '... [código omitido] ...', '...'] + lines[-15:])
        return snippet
    
    def generate_detailed_report(self):
        """Gera relatório detalhado com os códigos problemáticos."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.base_path / f'problemas_codigo_detalhado_{timestamp}.txt'
        
        report_lines = []
        
        # Cabeçalho
        report_lines.append("=" * 100)
        report_lines.append("ANÁLISE DETALHADA DE CÓDIGOS PROBLEMÁTICOS - SISTEMA LEDGER")
        report_lines.append(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        report_lines.append(f"Total de problemas identificados: {len(self.problematic_codes)}")
        report_lines.append(f"Arquivos críticos analisados: {len(self.critical_files)}")
        report_lines.append("=" * 100)
        report_lines.append("")
        
        # Agrupar por arquivo
        problems_by_file = {}
        for problem in self.problematic_codes:
            file_key = str(problem['file'])
            if file_key not in problems_by_file:
                problems_by_file[file_key] = []
            problems_by_file[file_key].append(problem)
        
        # Para cada arquivo, mostrar problemas
        for file_path, problems in problems_by_file.items():
            report_lines.append(f"\n{'='*80}")
            report_lines.append(f"ARQUIVO: {file_path}")
            report_lines.append(f"{'='*80}\n")
            
            for i, problem in enumerate(problems, 1):
                report_lines.append(f"\n{'─'*60}")
                report_lines.append(f"PROBLEMA {i}: {problem['pattern_name']}")
                report_lines.append(f"Linha: {problem['line']}")
                report_lines.append(f"Descrição: {problem['description']}")
                report_lines.append(f"{'─'*60}\n")
                
                # Mostrar código problemático
                report_lines.append("📍 CÓDIGO PROBLEMÁTICO:")
                report_lines.append("```python")
                report_lines.append(problem['code_snippet'])
                report_lines.append("```\n")
                
                # Sugestão de solução
                report_lines.append("💡 SUGESTÃO DE SOLUÇÃO:")
                suggestion = self.generate_suggestion(problem['pattern_name'])
                report_lines.append(suggestion)
                report_lines.append("")
        
        # Resumo e recomendações
        report_lines.append("\n" + "="*100)
        report_lines.append("RESUMO E RECOMENDAÇÕES PRIORITÁRIAS")
        report_lines.append("="*100)
        
        # Contar tipos de problemas
        problem_types = {}
        for problem in self.problematic_codes:
            ptype = problem['pattern_name']
            problem_types[ptype] = problem_types.get(ptype, 0) + 1
        
        report_lines.append("\n📊 DISTRIBUIÇÃO DE PROBLEMAS:")
        for ptype, count in sorted(problem_types.items(), key=lambda x: x[1], reverse=True):
            report_lines.append(f"  {ptype}: {count} ocorrências")
        
        report_lines.append("\n🚨 PROBLEMAS MAIS CRÍTICOS (resolver primeiro):")
        critical_patterns = [
            'PAGAMENTO COM DIRECTION CONFUSA',
            'EXCLUSÃO SEM ATUALIZAR FATURAS', 
            'CÁLCULO COMPLEXO PARA CARTÕES',
            'SOFT DELETE SEM RECÁLCULO'
        ]
        
        for pattern in critical_patterns:
            if pattern in problem_types:
                report_lines.append(f"  • {pattern}: {problem_types[pattern]} ocorrência(s)")
        
        report_lines.append("\n🔧 AÇÕES RECOMENDADAS:")
        report_lines.append("1. Refatorar completamente pay_bill() no credit_card_service.py")
        report_lines.append("2. Implementar atualização automática de faturas após exclusão")
        report_lines.append("3. Simplificar cálculo de saldo para cartões de crédito")
        report_lines.append("4. Criar endpoint para excluir parcelamentos completos")
        report_lines.append("5. Adicionar modal de detalhes de fatura com transações")
        
        # Salvar relatório
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        print(f"\n✅ Relatório gerado: {report_file}")
        print(f"📋 Total de problemas identificados: {len(self.problematic_codes)}")
        
        return report_file
    
    def generate_suggestion(self, pattern_name):
        """Gera sugestão baseada no tipo de problema."""
        suggestions = {
            'PAGAMENTO COM DIRECTION CONFUSA': """Solução:
1. Adicionar campo 'transaction_type' na model Transaction com valores:
   - 'PURCHASE' para compras
   - 'PAYMENT' para pagamentos de fatura
   - 'TRANSFER' para transferências
2. Simplificar pay_bill() para criar uma transação com type='PAYMENT'
3. Ajustar cálculo de saldo para usar transaction_type ao invés de direction""",
            
            'EXCLUSÃO SEM ATUALIZAR FATURAS': """Solução:
1. No método destroy(), após excluir a transação:
   if transaction.credit_card_bill:
       bill = transaction.credit_card_bill
       bill.recalculate_total()
       bill.save()
2. Adicionar método recalculate_total() no modelo CreditCardBill
3. Atualizar todos os totais automaticamente""",
            
            'CÁLCULO COMPLEXO PARA CARTÕES': """Solução:
1. Simplificar a lógica para cartões:
   saldo = total_pagamentos - total_compras
2. Usar transaction_type para diferenciar
3. Manter saldo sempre negativo ou zero para cartões
4. Remover lógica complexa de role+direction""",
            
            'SOFT DELETE SEM RECÁLCULO': """Solução:
1. Criar signal post_save para Transaction
2. Quando is_deleted muda para True, recalcular:
   - Saldo da conta
   - Totais da fatura (se houver)
   - Limite disponível do cartão""",
            
            'VINCULAÇÃO DE TRANSAÇÕES À FATURA': """Solução:
1. Validar período da transação antes de vincular
2. Garantir que transações de pagamento não sejam vinculadas como compras
3. Criar validação: data_transacao deve estar entre start_date e end_date""",
            
            'EXCLUSÃO PARCIAL DE PARCELAMENTO': """Solução:
1. Criar endpoint DELETE /api/installments/{plan_id}/
2. Oferecer opções ao usuário:
   - Excluir apenas esta parcela
   - Excluir todas as parcelas futuras
   - Excluir TODO o parcelamento
3. Implementar exclusão em cascata""",
            
            'FALTA DE ENDPOINT PARA DETALHES': """Solução:
1. Criar endpoint GET /api/bills/{bill_id}/transactions/
2. Retornar lista detalhada de transações
3. Incluir filtro para excluir transações deletadas
4. Permitir ordenação por data, valor, etc."""
        }
        
        return suggestions.get(pattern_name, "Analisar caso específico para sugerir solução.")
    
    def run_analysis(self):
        """Executa análise completa."""
        print("🔍 Iniciando análise detalhada de códigos problemáticos...")
        print(f"📁 Diretório base: {self.base_path}")
        print()
        
        self.detect_problematic_patterns()
        
        if not self.problematic_codes:
            print("✅ Nenhum problema crítico encontrado!")
            return None
        
        print(f"\n📊 Análise concluída. Problemas encontrados: {len(self.problematic_codes)}")
        
        # Gerar relatório detalhado
        report_file = self.generate_detailed_report()
        
        # Mostrar resumo no console
        print("\n" + "="*80)
        print("RESUMO DA ANÁLISE:")
        print("="*80)
        
        problem_counts = {}
        for problem in self.problematic_codes:
            ptype = problem['pattern_name']
            problem_counts[ptype] = problem_counts.get(ptype, 0) + 1
        
        for ptype, count in sorted(problem_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {ptype}: {count}")
        
        print(f"\n📄 Relatório completo salvo em: {report_file}")
        print("="*80)
        
        return report_file

def main():
    """Função principal."""
    # Verificar se estamos no diretório correto
    base_dirs_to_try = [
        Path.cwd(),  # Diretório atual
        Path.cwd().parent,  # Pai do diretório atual
        Path.cwd() / 'backend',  # Subdiretório backend
        Path.home() / 'Documents' / 'ledger',  # Caminho comum
    ]
    
    base_path = None
    for test_dir in base_dirs_to_try:
        if (test_dir / 'backend' / 'services').exists():
            base_path = test_dir
            break
    
    if not base_path:
        print("❌ Não foi possível encontrar o diretório do projeto.")
        print("Por favor, execute este script do diretório raiz do projeto.")
        return
    
    print(f"✅ Projeto encontrado em: {base_path}")
    
    # Executar análise
    detector = CodeProblemDetector(base_path)
    detector.run_analysis()
    
    print("\n🎯 PRÓXIMOS PASSOS:")
    print("1. Revisar o relatório gerado")
    print("2. Priorizar problemas críticos")
    print("3. Implementar as correções sugeridas")
    print("4. Testar cada correção antes de prosseguir")

if __name__ == "__main__":
    main()