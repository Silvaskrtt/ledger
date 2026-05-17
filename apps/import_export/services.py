"""
Serviços para importação de extratos bancários
Orquestra parsing, validação, deduplicação e salvamento
"""
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction as db_transaction
from decimal import Decimal
from typing import Dict, List, Tuple, Optional
import logging
import traceback

from .models import ImportHistory, TransactionImportMetadata
from .parsers import get_parser
from .validators import TransactionValidator, DuplicateDetector

logger = logging.getLogger(__name__)


class BankStatementImportService:
    """Serviço central para importação de extratos bancários"""
    
    def __init__(self, user: User, bank: str, file_format: str, filename: str, file_size: int):
        self.user = user
        self.bank = bank
        self.file_format = file_format
        self.filename = filename
        self.file_size = file_size
        
        # Estatísticas
        self.total_lines_read = 0
        self.records_imported = 0
        self.records_failed = 0
        self.duplicates_ignored = 0
        self.validation_errors = []
        
        # Histórico de importação
        self.import_history = None
        
        # Transações processadas
        self.processed_transactions = []
        self.imported_transactions = []
        
        # Models importados dinamicamente
        self.Transaction = None
        self.Category = None
        self._load_models()
    
    def _load_models(self):
        """Carrega models dinamicamente para evitar erro de importação"""
        try:
            from transactions.models import Transaction
            self.Transaction = Transaction
        except ImportError:
            logger.warning("App 'transactions' não encontrado")
            self.Transaction = None
        
        try:
            from categories.models import Category
            self.Category = Category
        except ImportError:
            logger.warning("App 'categories' não encontrado")
            self.Category = None
    
    def import_file(self, file_content: bytes) -> Dict:
        """
        Executa o processo completo de importação
        Retorna dicionário com resultado da operação
        """
        try:
            # Verificar se os models necessários existem
            if not self.Transaction or not self.Category:
                return {
                    'success': False,
                    'error': 'Apps necessários não estão instalados. Execute: python manage.py startapp transactions e python manage.py startapp categories',
                    'status': 'failed',
                    'message': 'Configuração incompleta do sistema'
                }
            
            # Criar registro de importação
            self.import_history = ImportHistory.objects.create(
                user=self.user,
                filename=self.filename,
                bank=self.bank,
                file_format=self.file_format,
                file_size=self.file_size,
                status='processing'
            )
            
            # Step 1: Parse do arquivo
            parsed_transactions = self._parse_file(file_content)
            
            if not parsed_transactions and not self.validation_errors:
                self._finalize_import(
                    status='failed',
                    error_message='Nenhuma transação válida encontrada no arquivo'
                )
                return self._get_result()
            
            if not parsed_transactions:
                self._finalize_import(
                    status='completed_with_errors' if self.records_failed > 0 else 'failed',
                    error_message='Nenhuma transação foi parseada com sucesso'
                )
                return self._get_result()
            
            # Step 2: Validar transações
            validated_transactions = self._validate_transactions(parsed_transactions)
            
            # Step 3: Detectar e remover duplicatas
            deduplicated_transactions = self._remove_duplicates(validated_transactions)
            
            # Step 4: Salvar transações
            self._save_transactions(deduplicated_transactions)
            
            # Finalizar importação
            if self.records_failed > 0 and self.records_imported > 0:
                status = 'completed_with_errors'
            elif self.records_imported > 0:
                status = 'completed'
            else:
                status = 'failed'
            
            self._finalize_import(status)
            
        except Exception as e:
            logger.error(f"Erro ao importar arquivo: {str(e)}")
            logger.error(traceback.format_exc())
            self._finalize_import(
                status='failed',
                error_message=f"Erro ao processar arquivo: {str(e)}"
            )
        
        return self._get_result()
    
    def _parse_file(self, file_content: bytes) -> List[Dict]:
        """Realiza parsing do arquivo"""
        try:
            parser = get_parser(self.bank, self.file_format)
            
            if not parser:
                error_msg = f"Parser não disponível para {self.bank}/{self.file_format}"
                logger.warning(error_msg)
                self.validation_errors.append({
                    'line': 0,
                    'error': error_msg
                })
                return []
            
            transactions = parser.parse(file_content)
            self.total_lines_read = parser.total_lines
            
            # Adicionar erros do parser
            if parser.errors:
                self.validation_errors.extend(parser.errors)
                self.records_failed += len([e for e in parser.errors if e.get('line', 0) > 0])
            
            return transactions
        
        except Exception as e:
            logger.error(f"Erro ao fazer parsing: {str(e)}")
            logger.error(traceback.format_exc())
            self.validation_errors.append({
                'line': 0,
                'error': f"Erro ao fazer parsing: {str(e)}"
            })
            return []
    
    def _validate_transactions(self, transactions: List[Dict]) -> List[Dict]:
        """Valida transações"""
        validated = []
        
        for idx, trans_data in enumerate(transactions):
            is_valid, validated_data, errors = TransactionValidator.validate_transaction_data(trans_data)
            
            if not is_valid:
                self.records_failed += 1
                self.validation_errors.append({
                    'line': idx + 1,
                    'error': '; '.join(errors),
                    'data': str(trans_data)[:500]
                })
                logger.debug(f"Transação inválida (linha {idx + 1}): {errors}")
            else:
                validated.append(validated_data)
        
        return validated
    
    def _remove_duplicates(self, transactions: List[Dict]) -> List[Dict]:
        """Remove duplicatas dentro do batch e no banco de dados"""
        deduplicated = []
        seen_fitids = set()
        seen_composite_keys = set()
        
        try:
            # Verificar duplicatas no banco de dados apenas se os models existem
            if self.Transaction and self.Category:
                existing_fitids = set()
                existing_composite_keys = set()
                
                # Buscar FITID existentes
                existing_metadata = TransactionImportMetadata.objects.filter(
                    transaction__user=self.user
                ).values_list('fitid', 'document_number').distinct()
                
                for fitid, doc_number in existing_metadata:
                    if fitid:
                        existing_fitids.add(fitid)
                    if doc_number:
                        existing_fitids.add(doc_number)
                
                # Verificar duplicatas de chave composta no BD
                existing_trans = self.Transaction.objects.filter(
                    user=self.user
                ).values('date', 'amount', 'description').distinct()
                
                for trans in existing_trans:
                    if trans['date'] and trans['amount'] and trans['description']:
                        key = f"{trans['date']}|{trans['amount']}|{trans['description']}"
                        existing_composite_keys.add(key)
                
                # Processar transações com verificação de BD
                for trans in transactions:
                    # Verificar FITID dentro do batch
                    fitid = DuplicateDetector.get_fitid(trans)
                    if fitid and fitid in seen_fitids:
                        self.duplicates_ignored += 1
                        logger.debug(f"Duplicata por FITID: {fitid}")
                        continue
                    
                    if fitid and fitid in existing_fitids:
                        self.duplicates_ignored += 1
                        logger.debug(f"Duplicata no BD (FITID): {fitid}")
                        continue
                    
                    # Verificar chave composta
                    composite_key = DuplicateDetector.get_composite_key(trans)
                    if composite_key in seen_composite_keys:
                        self.duplicates_ignored += 1
                        logger.debug(f"Duplicata por chave composta: {composite_key}")
                        continue
                    
                    if composite_key in existing_composite_keys:
                        self.duplicates_ignored += 1
                        logger.debug(f"Duplicata no BD (chave composta): {composite_key}")
                        continue
                    
                    # Adicionar aos sets de duplicação
                    if fitid:
                        seen_fitids.add(fitid)
                    seen_composite_keys.add(composite_key)
                    
                    deduplicated.append(trans)
            else:
                # Sem verificação de BD, apenas duplicatas no batch
                for trans in transactions:
                    fitid = DuplicateDetector.get_fitid(trans)
                    composite_key = DuplicateDetector.get_composite_key(trans)
                    
                    if fitid and fitid in seen_fitids:
                        self.duplicates_ignored += 1
                        continue
                    
                    if composite_key in seen_composite_keys:
                        self.duplicates_ignored += 1
                        continue
                    
                    if fitid:
                        seen_fitids.add(fitid)
                    seen_composite_keys.add(composite_key)
                    deduplicated.append(trans)
        
        except Exception as e:
            logger.warning(f"Erro ao verificar duplicatas no BD: {str(e)}")
            # Fallback: apenas duplicatas no batch
            for trans in transactions:
                fitid = DuplicateDetector.get_fitid(trans)
                composite_key = DuplicateDetector.get_composite_key(trans)
                
                if fitid and fitid in seen_fitids:
                    self.duplicates_ignored += 1
                    continue
                
                if composite_key in seen_composite_keys:
                    self.duplicates_ignored += 1
                    continue
                
                if fitid:
                    seen_fitids.add(fitid)
                seen_composite_keys.add(composite_key)
                deduplicated.append(trans)
        
        return deduplicated
    
    def _save_transactions(self, transactions: List[Dict]) -> None:
        """Salva transações no banco de dados"""
        if not transactions:
            return
        
        try:
            # Obter ou criar categoria padrão
            default_category, _ = self.Category.objects.get_or_create(
                user=self.user,
                name='Importadas',
                defaults={'type': 'expense', 'is_default': True}
            )
            
            with db_transaction.atomic():
                for trans_data in transactions:
                    try:
                        # Converter valor para Decimal
                        amount_value = trans_data.get('amount', 0)
                        if isinstance(amount_value, str):
                            amount_value = Decimal(amount_value)
                        elif isinstance(amount_value, (int, float)):
                            amount_value = Decimal(str(amount_value))
                        
                        # Determinar tipo (income/expense)
                        transaction_type = trans_data.get('type', 'expense')
                        
                        # Criar transação
                        trans = self.Transaction.objects.create(
                            user=self.user,
                            category=default_category,
                            date=trans_data.get('date'),
                            amount=abs(amount_value),
                            description=trans_data.get('description', 'Sem descrição')[:200],
                            type=transaction_type,
                            notes=f"Importado de {self.bank.upper()} ({self.file_format.upper()})"
                        )
                        
                        # Criar metadados
                        TransactionImportMetadata.objects.create(
                            transaction=trans,
                            import_history=self.import_history,
                            fitid=trans_data.get('fitid', '')[:255],
                            document_number=trans_data.get('document_number', '')[:255],
                            transaction_type=trans_data.get('transaction_type', 'credit'),
                            bank=self.bank,
                            raw_data=trans_data.get('raw_data', {})
                        )
                        
                        self.records_imported += 1
                        self.imported_transactions.append(trans)
                        
                    except Exception as e:
                        self.records_failed += 1
                        logger.error(f"Erro ao salvar transação: {str(e)}")
                        self.validation_errors.append({
                            'line': len(self.processed_transactions),
                            'error': f'Erro ao salvar: {str(e)}',
                            'data': str(trans_data)[:500]
                        })
        
        except Exception as e:
            logger.error(f"Erro ao salvar transações: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def _finalize_import(self, status: str, error_message: str = None) -> None:
        """Finaliza o registro de importação"""
        if not self.import_history:
            return
        
        self.import_history.status = status
        self.import_history.total_lines_read = self.total_lines_read
        self.import_history.records_imported = self.records_imported
        self.import_history.records_failed = self.records_failed
        self.import_history.duplicates_ignored = self.duplicates_ignored
        self.import_history.error_message = error_message
        self.import_history.validation_errors = self.validation_errors[:100]
        self.import_history.completed_at = timezone.now()
        self.import_history.save()
    
    def _get_result(self) -> Dict:
        """Retorna resultado da importação"""
        return {
            'success': self.records_imported > 0,
            'import_id': self.import_history.id if self.import_history else None,
            'status': self.import_history.status if self.import_history else 'unknown',
            'summary': {
                'total_lines_read': self.total_lines_read,
                'records_imported': self.records_imported,
                'records_failed': self.records_failed,
                'duplicates_ignored': self.duplicates_ignored,
            },
            'validation_errors': self.validation_errors[:20],
            'message': self._build_message()
        }
    
    def _build_message(self) -> str:
        """Constrói mensagem de resultado"""
        parts = []
        
        if self.total_lines_read > 0:
            parts.append(f"Linhas lidas: {self.total_lines_read}")
        
        if self.records_imported > 0:
            parts.append(f"✓ {self.records_imported} transações importadas com sucesso")
        
        if self.duplicates_ignored > 0:
            parts.append(f"⊘ {self.duplicates_ignored} duplicatas ignoradas")
        
        if self.records_failed > 0:
            parts.append(f"✗ {self.records_failed} transações com erro")
        
        if not parts:
            return "Nenhuma transação para importar"
        
        return " | ".join(parts)