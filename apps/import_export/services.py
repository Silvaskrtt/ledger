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
            logger.info(f"Iniciando import_file para usuário {self.user.username}, banco {self.bank}, formato {self.file_format}")
            
            # Verificar se os models necessários existem
            if not self.Transaction or not self.Category:
                error_response = {
                    'success': False,
                    'error': 'Apps necessários não estão instalados',
                    'status': 'failed',
                    'message': 'Configuração incompleta do sistema'
                }
                logger.error(f"Models não disponíveis: Transaction={self.Transaction}, Category={self.Category}")
                return error_response
            
            # Criar registro de importação
            try:
                self.import_history = ImportHistory.objects.create(
                    user=self.user,
                    filename=self.filename,
                    bank=self.bank,
                    file_format=self.file_format,
                    file_size=self.file_size,
                    status='processing'
                )
                logger.info(f"ImportHistory criado: id={self.import_history.id}")
            except Exception as e:
                logger.error(f"Erro ao criar ImportHistory: {str(e)}")
                return {
                    'success': False,
                    'error': f'Erro ao registrar importação: {str(e)}',
                    'status': 'failed',
                    'message': 'Falha ao iniciar processo de importação'
                }
            
            # Step 1: Parse do arquivo
            parsed_transactions = self._parse_file(file_content)
            logger.info(f"Parse concluído: {len(parsed_transactions)} transações parseadas")
            
            if not parsed_transactions and not self.validation_errors:
                logger.warning("Nenhuma transação válida encontrada no arquivo")
                self._finalize_import(
                    status='failed',
                    error_message='Nenhuma transação válida encontrada no arquivo'
                )
                return self._get_result()
            
            if not parsed_transactions:
                logger.warning("Nenhuma transação foi parseada com sucesso")
                self._finalize_import(
                    status='completed_with_errors' if self.records_failed > 0 else 'failed',
                    error_message='Nenhuma transação foi parseada com sucesso'
                )
                return self._get_result()
            
            # Step 2: Validar transações
            validated_transactions = self._validate_transactions(parsed_transactions)
            logger.info(f"Validação concluída: {len(validated_transactions)} transações válidas")
            
            # Step 3: Detectar e remover duplicatas
            deduplicated_transactions = self._remove_duplicates(validated_transactions)
            logger.info(f"Deduplicação concluída: {len(deduplicated_transactions)} transações para salvar")
            
            # Step 4: Salvar transações
            self._save_transactions(deduplicated_transactions)
            logger.info(f"Gravação concluída: {self.records_imported} importadas, {self.records_failed} falhadas")
            
            # Finalizar importação
            if self.records_failed > 0 and self.records_imported > 0:
                status = 'completed_with_errors'
            elif self.records_imported > 0:
                status = 'completed'
            else:
                status = 'failed'
            
            logger.info(f"Finalizando importação com status: {status}")
            self._finalize_import(status)
            
        except Exception as e:
            logger.error(f"Erro ao importar arquivo: {str(e)}")
            logger.error(traceback.format_exc())
            try:
                self._finalize_import(
                    status='failed',
                    error_message=f"Erro ao processar arquivo: {str(e)[:500]}"
                )
            except:
                logger.error("Falha ao finalizar após erro")
        
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
            logger.info("Nenhuma transação para salvar")
            return
        
        try:
            # Obter ou criar categoria padrão
            if not self.Category:
                logger.warning("Category model não disponível, pulando gravação de transações")
                return
            
            default_category, created = self.Category.objects.get_or_create(
                user=self.user,
                name='Importadas',
                defaults={'type': 'expense', 'is_default': True}
            )
            
            if created:
                logger.info(f"Categoria padrão criada: {default_category.name}")
            
            with db_transaction.atomic():
                for idx, trans_data in enumerate(transactions):
                    try:
                        # Converter valor para Decimal
                        amount_value = trans_data.get('amount')
                        
                        if amount_value is None:
                            logger.warning(f"Transação sem valor (índice {idx}): {trans_data.get('description')}")
                            continue
                        
                        if isinstance(amount_value, str):
                            try:
                                amount_value = Decimal(amount_value.strip().replace(',', '.'))
                            except Exception as e:
                                logger.warning(f"Erro ao converter valor '{amount_value}' (índice {idx}): {e}")
                                continue
                        elif isinstance(amount_value, (int, float)):
                            amount_value = Decimal(str(amount_value))
                        else:
                            try:
                                amount_value = Decimal(str(amount_value))
                            except:
                                logger.warning(f"Tipo de valor desconhecido (índice {idx}): {type(amount_value)}")
                                continue
                        
                        # Validar que amount é diferente de zero
                        if amount_value == 0:
                            logger.warning(f"Valor zerado (índice {idx}): {trans_data.get('description')}")
                            continue
                        
                        # Aceitar valores negativos (será corrigido pelo tipo de transação)
                        amount_value = abs(amount_value)
                        
                        # Determinar tipo (income/expense)
                        transaction_type = trans_data.get('type', 'expense')
                        if transaction_type not in ['income', 'expense']:
                            transaction_type = 'expense'
                        
                        # Obter descrição com valor padrão
                        description = trans_data.get('description', 'Sem descrição')
                        if not description or not str(description).strip():
                            description = 'Transação importada'
                        description = str(description)[:200]
                        
                        # Criar transação
                        trans = self.Transaction.objects.create(
                            user=self.user,
                            category=default_category,
                            date=trans_data.get('date'),
                            amount=abs(amount_value),
                            description=description,
                            type=transaction_type,
                            notes=f"Importado de {self.bank.upper()} ({self.file_format.upper()})"
                        )
                        
                        # Criar metadados
                        try:
                            TransactionImportMetadata.objects.create(
                                transaction=trans,
                                import_history=self.import_history,
                                fitid=str(trans_data.get('fitid', ''))[:255],
                                document_number=str(trans_data.get('document_number', ''))[:255],
                                transaction_type=str(trans_data.get('transaction_type', 'credit'))[:50],
                                bank=self.bank,
                                raw_data=trans_data.get('raw_data', {})
                            )
                        except Exception as e:
                            logger.warning(f"Erro ao salvar metadados: {str(e)}")
                        
                        self.records_imported += 1
                        self.imported_transactions.append(trans)
                        
                    except Exception as e:
                        self.records_failed += 1
                        logger.warning(f"Erro ao salvar transação {idx}: {str(e)}")
                        self.validation_errors.append({
                            'line': idx + 1,
                            'error': f'Erro ao salvar: {str(e)[:100]}',
                            'data': str(trans_data)[:300]
                        })
        
        except Exception as e:
            logger.error(f"Erro crítico ao salvar transações: {str(e)}")
            logger.error(traceback.format_exc())
            self.validation_errors.append({
                'line': 0,
                'error': f'Erro crítico ao salvar: {str(e)[:100]}',
            })
    
    def _finalize_import(self, status: str, error_message: str = None) -> None:
        """Finaliza o registro de importação"""
        if not self.import_history:
            logger.warning("import_history é None ao finalizar importação")
            return
        
        try:
            self.import_history.status = status
            self.import_history.total_lines_read = self.total_lines_read
            self.import_history.records_imported = self.records_imported
            self.import_history.records_failed = self.records_failed
            self.import_history.duplicates_ignored = self.duplicates_ignored
            self.import_history.error_message = error_message
            
            # Validar e serializar validation_errors
            errors_to_save = []
            if self.validation_errors:
                errors_to_save = self.validation_errors[:100]
            
            self.import_history.validation_errors = errors_to_save
            self.import_history.completed_at = timezone.now()
            
            self.import_history.save()
            logger.info(f"Importação finalizada: status={status}, records_imported={self.records_imported}")
        
        except Exception as e:
            logger.error(f"Erro ao finalizar importação: {str(e)}")
            logger.error(traceback.format_exc())
            # Tenta salvar pelo menos o status
            try:
                self.import_history.status = 'failed'
                self.import_history.error_message = f"Erro ao finalizar: {str(e)}"
                self.import_history.save()
            except:
                logger.error("Falha crítica ao salvar import_history")
    
    def _get_result(self) -> Dict:
        """Retorna resultado da importação"""
        try:
            import_id = None
            status = 'unknown'
            
            if self.import_history:
                try:
                    import_id = self.import_history.id
                    status = self.import_history.status or 'unknown'
                except:
                    logger.warning("Erro ao acessar atributos de import_history")
            
            result = {
                'success': self.records_imported > 0,
                'import_id': import_id,
                'status': status,
                'summary': {
                    'total_lines_read': self.total_lines_read,
                    'records_imported': self.records_imported,
                    'records_failed': self.records_failed,
                    'duplicates_ignored': self.duplicates_ignored,
                },
                'validation_errors': self.validation_errors[:20] if self.validation_errors else [],
                'message': self._build_message()
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Erro ao construir resultado: {str(e)}")
            return {
                'success': False,
                'error': f'Erro ao processar resultado: {str(e)[:100]}',
                'status': 'failed',
                'message': 'Erro ao finalizar importação'
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