# import_export/validators.py
"""
Validadores para dados de importação de extratos bancários
"""
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Tuple, Optional


class TransactionValidator:
    """Validador para transações importadas"""
    
    VALID_TYPES = ['income', 'expense']
    VALID_TRANSACTION_TYPES = ['credit', 'debit']
    
    @staticmethod
    def validate_date(date_str: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Valida formato de data (esperado YYYY-MM-DD)
        Retorna: (é_válido, data_normalizada, mensagem_erro)
        """
        if not date_str:
            return False, None, "Data não fornecida"
        
        try:
            # Assumir que já vem em YYYY-MM-DD do parser
            dt = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Validar se data é razoável (últimos 10 anos até hoje)
            today = date.today()
            min_date = date(today.year - 10, 1, 1)
            
            if dt < min_date:
                return False, None, f"Data fora do intervalo permitido: {date_str}"
            
            if dt > today:
                return False, None, f"Data no futuro não permitida: {date_str}"
            
            return True, date_str, None
        
        except ValueError as e:
            return False, None, f"Formato de data inválido: {date_str}"
    
    @staticmethod
    def validate_amount(amount_str: str) -> Tuple[bool, Optional[Decimal], Optional[str]]:
        """
        Valida valor da transação
        Retorna: (é_válido, valor_decimal, mensagem_erro)
        """
        if not amount_str:
            return False, None, "Valor não fornecido"
        
        try:
            amount = Decimal(str(amount_str).strip())
            
            # Valor não pode ser zero
            if amount == 0:
                return False, None, "Valor não pode ser zero"
            
            # Validar limites (não permite valores absurdamente grandes)
            if abs(amount) > Decimal('999999.99'):
                return False, None, f"Valor muito grande: {amount}"
            
            return True, amount, None
        
        except:
            return False, None, f"Valor não é numérico válido: {amount_str}"
    
    @staticmethod
    def validate_description(description: str, max_length: int = 200) -> Tuple[bool, str, Optional[str]]:
        """
        Valida descrição da transação
        Retorna: (é_válido, descrição_normalizada, mensagem_erro)
        """
        if not description or not str(description).strip():
            return False, None, "Descrição não fornecida"
        
        desc = str(description).strip()
        
        if len(desc) > max_length:
            desc = desc[:max_length]
        
        if len(desc) == 0:
            return False, None, "Descrição vazia"
        
        return True, desc, None
    
    @staticmethod
    def validate_type(transaction_type: str) -> Tuple[bool, str, Optional[str]]:
        """
        Valida tipo de transação (income/expense)
        Retorna: (é_válido, tipo, mensagem_erro)
        """
        if not transaction_type:
            return False, None, "Tipo de transação não fornecido"
        
        trans_type = str(transaction_type).lower().strip()
        
        if trans_type not in TransactionValidator.VALID_TYPES:
            return False, None, f"Tipo inválido: {transaction_type}. Valores válidos: {TransactionValidator.VALID_TYPES}"
        
        return True, trans_type, None
    
    @staticmethod
    def validate_transaction_type(trans_type: str) -> Tuple[bool, str, Optional[str]]:
        """
        Valida tipo de transação bancária (credit/debit)
        Retorna: (é_válido, tipo, mensagem_erro)
        """
        if trans_type and str(trans_type).lower().strip() in TransactionValidator.VALID_TRANSACTION_TYPES:
            return True, str(trans_type).lower().strip(), None
        
        return True, 'credit' if Decimal(0) >= 0 else 'debit', None
    
    @staticmethod
    def validate_transaction_data(transaction_data: Dict) -> Tuple[bool, Dict, List[str]]:
        """
        Valida todos os campos de uma transação
        Retorna: (é_válido, dados_validados, lista_erros)
        """
        errors = []
        validated = {}
        
        # Validar data
        valid, date_val, error = TransactionValidator.validate_date(transaction_data.get('date', ''))
        if not valid:
            errors.append(f"Data: {error}")
        else:
            validated['date'] = date_val
        
        # Validar valor
        valid, amount_val, error = TransactionValidator.validate_amount(transaction_data.get('amount', ''))
        if not valid:
            errors.append(f"Valor: {error}")
        else:
            validated['amount'] = amount_val
        
        # Validar descrição
        valid, desc_val, error = TransactionValidator.validate_description(transaction_data.get('description', ''))
        if not valid:
            errors.append(f"Descrição: {error}")
        else:
            validated['description'] = desc_val
        
        # Validar tipo
        valid, type_val, error = TransactionValidator.validate_type(transaction_data.get('type', 'expense'))
        if not valid:
            errors.append(f"Tipo: {error}")
        else:
            validated['type'] = type_val
        
        # Validar transaction_type (opcional)
        if 'transaction_type' in transaction_data:
            valid, trans_type_val, error = TransactionValidator.validate_transaction_type(transaction_data.get('transaction_type'))
            if valid:
                validated['transaction_type'] = trans_type_val
        
        # Campos opcionais
        validated['document_number'] = transaction_data.get('document_number', '')
        validated['bank'] = transaction_data.get('bank', 'generic')
        validated['fitid'] = transaction_data.get('fitid', '')
        validated['raw_data'] = transaction_data.get('raw_data', {})
        
        return len(errors) == 0, validated, errors


class DuplicateDetector:
    """Detecta duplicatas de transações"""
    
    @staticmethod
    def get_fitid(transaction_data: Dict) -> Optional[str]:
        """Extrai FITID de dados de transação"""
        return transaction_data.get('fitid') or transaction_data.get('document_number')
    
    @staticmethod
    def get_composite_key(transaction_data: Dict) -> str:
        """
        Gera chave composta para deduplicação: data+valor+descrição
        Usada quando FITID/document_number não está disponível
        """
        return f"{transaction_data.get('date', '')}|{transaction_data.get('amount', '')}|{transaction_data.get('description', '')}"
    
    @staticmethod
    def is_duplicate(transaction_data: Dict, existing_transactions: List) -> Tuple[bool, Optional[str]]:
        """
        Verifica se transação é duplicata
        Retorna: (é_duplicata, identificador_existente)
        """
        # Primeiro tentar por FITID
        fitid = DuplicateDetector.get_fitid(transaction_data)
        if fitid:
            for existing in existing_transactions:
                existing_fitid = DuplicateDetector.get_fitid(existing)
                if existing_fitid == fitid:
                    return True, fitid
        
        # Fallback para chave composta (data+valor+descrição)
        composite_key = DuplicateDetector.get_composite_key(transaction_data)
        for existing in existing_transactions:
            existing_key = DuplicateDetector.get_composite_key(existing)
            if composite_key == existing_key:
                return True, composite_key
        
        return False, None
