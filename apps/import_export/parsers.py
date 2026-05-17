# import_export/parsers.py
"""
Parsers específicos para cada banco e formato de arquivo
"""
import csv
import json
from datetime import datetime
from decimal import Decimal
from io import StringIO, BytesIO
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple


class BankParser(ABC):
    """Classe base para parsers de banco"""
    
    def __init__(self):
        self.transactions = []
        self.errors = []
        self.total_lines = 0
    
    @abstractmethod
    def parse(self, file_content: bytes) -> List[Dict]:
        """Parse o arquivo e retorna lista de transações normalizadas"""
        pass
    
    @staticmethod
    def normalize_date(date_str: str, formats: List[str] = None) -> Optional[str]:
        """Converte string de data para formato YYYY-MM-DD"""
        if not date_str or not str(date_str).strip():
            return None
        
        if formats is None:
            formats = [
                '%d/%m/%Y',
                '%Y-%m-%d',
                '%d-%m-%Y',
                '%m/%d/%Y',
                '%d.%m.%Y',
                '%Y/%m/%d',
            ]
        
        date_str = str(date_str).strip()
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None
    
    @staticmethod
    def parse_decimal(value: str) -> Optional[Decimal]:
        """Converte string para Decimal numérico"""
        if not value:
            return None
        
        try:
            # Remove caracteres de moeda e espaços
            value_str = str(value).strip().replace('R$', '').strip()
            
            # Identifica se usa , ou . como separador decimal
            if ',' in value_str and '.' in value_str:
                # Tem ambos, assume que o último é decimal
                if value_str.rfind(',') > value_str.rfind('.'):
                    value_str = value_str.replace('.', '').replace(',', '.')
                else:
                    value_str = value_str.replace(',', '')
            elif ',' in value_str:
                # Só tem vírgula - pode ser 1000,00 ou 1,00
                if value_str.count(',') == 1:
                    value_str = value_str.replace(',', '.')
                else:
                    # Múltiplas vírgulas - assume última é decimal
                    parts = value_str.split(',')
                    value_str = '.'.join(parts)
            
            result = Decimal(value_str)
            return result if result != 0 else None
        except:
            return None


class BancoDosBrasilCSVParser(BankParser):
    """Parser para CSV do Banco do Brasil"""
    
    def parse(self, file_content: bytes) -> List[Dict]:
        """
        Esperado: Data, Lançamento, Detalhes, N° documento, Valor, Tipo Lançamento
        """
        self.transactions = []
        self.errors = []
        
        try:
            content_str = file_content.decode('utf-8')
            reader = csv.DictReader(StringIO(content_str), delimiter=';')
            
            for line_num, row in enumerate(reader, start=2):
                self.total_lines += 1
                try:
                    # Mapeamento de campos
                    date_str = row.get('Data', '').strip()
                    description = row.get('Detalhes', '').strip()
                    document_no = row.get('N° documento', '').strip()
                    value_str = row.get('Valor', '').strip()
                    type_str = row.get('Tipo Lançamento', '').strip().upper()
                    
                    # Validações básicas
                    if not date_str or not value_str or not description:
                        self.errors.append({
                            'line': line_num,
                            'error': 'Campos obrigatórios ausentes (Data, Valor, Detalhes)'
                        })
                        continue
                    
                    # Parse da data
                    date = self.normalize_date(date_str, ['%d/%m/%Y'])
                    if not date:
                        self.errors.append({
                            'line': line_num,
                            'error': f'Data inválida: {date_str}'
                        })
                        continue
                    
                    # Parse do valor
                    amount = self.parse_decimal(value_str)
                    if amount is None:
                        self.errors.append({
                            'line': line_num,
                            'error': f'Valor inválido: {value_str}'
                        })
                        continue
                    
                    # Determina tipo (crédito/débito)
                    is_credit = type_str in ['DÉBITO', 'SAÍDA', 'DESPESA']
                    if is_credit:
                        amount = abs(amount) * -1
                    else:
                        amount = abs(amount)
                    
                    self.transactions.append({
                        'date': date,
                        'description': description,
                        'amount': str(amount),
                        'type': 'expense' if is_credit else 'income',
                        'document_number': document_no,
                        'transaction_type': 'debit' if is_credit else 'credit',
                        'bank': 'bb',
                        'raw_data': dict(row)
                    })
                
                except Exception as e:
                    self.errors.append({
                        'line': line_num,
                        'error': str(e)
                    })
        
        except Exception as e:
            self.errors.append({
                'line': 0,
                'error': f'Erro ao processar arquivo: {str(e)}'
            })
        
        return self.transactions


class BancoDosBrasilPDFParser(BankParser):
    """Parser para PDF do Banco do Brasil"""
    
    def parse(self, file_content: bytes) -> List[Dict]:
        """
        Esperado: Dia, Lote, Documento, Histórico, Valor
        """
        try:
            import PyPDF2
        except ImportError:
            self.errors.append({
                'line': 0,
                'error': 'PyPDF2 não instalado. Instale com: pip install PyPDF2'
            })
            return []
        
        self.transactions = []
        self.errors = []
        
        try:
            pdf_file = BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            for page_num, page in enumerate(pdf_reader.pages, start=1):
                text = page.extract_text()
                lines = text.split('\n')
                
                for line_num, line in enumerate(lines, start=1):
                    line = line.strip()
                    if not line or len(line) < 10:
                        continue
                    
                    try:
                        # Regex simplificado para extrair padrão: data valor
                        parts = line.split()
                        if len(parts) < 3:
                            continue
                        
                        # Tenta extrair data (primeiro campo)
                        date_str = parts[0]
                        date = self.normalize_date(date_str, ['%d/%m/%Y', '%d/%m'])
                        
                        if not date:
                            continue
                        
                        # Tenta encontrar valor numérico
                        value_str = None
                        for part in parts:
                            if self.parse_decimal(part):
                                value_str = part
                                break
                        
                        if not value_str:
                            continue
                        
                        amount = self.parse_decimal(value_str)
                        if not amount:
                            continue
                        
                        # Descrição é o resto do texto
                        description = ' '.join(parts[1:-1]) if len(parts) > 2 else line
                        
                        # Completar dia com mês/ano se necessário
                        if len(date.split('-')[-1]) == 4:  # Tem ano
                            pass
                        else:
                            # Adicionar ano atual se não tiver
                            from datetime import datetime
                            year = datetime.now().year
                            date = f"{date}-{year}"
                        
                        self.transactions.append({
                            'date': date,
                            'description': description[:200],
                            'amount': str(amount),
                            'type': 'income' if amount > 0 else 'expense',
                            'transaction_type': 'credit' if amount > 0 else 'debit',
                            'bank': 'bb',
                            'raw_data': {'pdf_line': line, 'page': page_num}
                        })
                    
                    except Exception as e:
                        self.errors.append({
                            'line': page_num,
                            'error': f'Erro ao processar linha PDF: {str(e)}'
                        })
        
        except Exception as e:
            self.errors.append({
                'line': 0,
                'error': f'Erro ao processar PDF: {str(e)}'
            })
        
        return self.transactions


class BancoDosBrasilXLSXParser(BankParser):
    """Parser para XLSX do Banco do Brasil"""
    
    def parse(self, file_content: bytes) -> List[Dict]:
        """XLSX com campos: Data, Lançamento, Detalhes, N° documento, Valor, Tipo Lançamento"""
        try:
            import openpyxl
        except ImportError:
            self.errors.append({
                'line': 0,
                'error': 'openpyxl não instalado. Instale com: pip install openpyxl'
            })
            return []
        
        self.transactions = []
        self.errors = []
        
        try:
            workbook = openpyxl.load_workbook(BytesIO(file_content))
            sheet = workbook.active
            
            # Assumir que a primeira linha é cabeçalho
            headers = []
            for cell in sheet[1]:
                headers.append(cell.value)
            
            for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                self.total_lines += 1
                try:
                    row_dict = {headers[i]: row[i] if i < len(row) else None for i in range(len(headers))}
                    
                    # Mesmo formato do CSV
                    date_str = str(row_dict.get('Data', '')).strip() if row_dict.get('Data') else ''
                    description = str(row_dict.get('Detalhes', '')).strip() if row_dict.get('Detalhes') else ''
                    document_no = str(row_dict.get('N° documento', '')).strip() if row_dict.get('N° documento') else ''
                    value_str = str(row_dict.get('Valor', '')).strip() if row_dict.get('Valor') else ''
                    type_str = str(row_dict.get('Tipo Lançamento', '')).strip().upper() if row_dict.get('Tipo Lançamento') else ''
                    
                    if not date_str or not value_str or not description:
                        self.errors.append({
                            'line': row_num,
                            'error': 'Campos obrigatórios ausentes'
                        })
                        continue
                    
                    date = self.normalize_date(date_str, ['%d/%m/%Y'])
                    if not date:
                        self.errors.append({
                            'line': row_num,
                            'error': f'Data inválida: {date_str}'
                        })
                        continue
                    
                    amount = self.parse_decimal(value_str)
                    if amount is None:
                        self.errors.append({
                            'line': row_num,
                            'error': f'Valor inválido: {value_str}'
                        })
                        continue
                    
                    is_credit = type_str in ['DÉBITO', 'SAÍDA', 'DESPESA']
                    if is_credit:
                        amount = abs(amount) * -1
                    else:
                        amount = abs(amount)
                    
                    self.transactions.append({
                        'date': date,
                        'description': description,
                        'amount': str(amount),
                        'type': 'expense' if is_credit else 'income',
                        'document_number': document_no,
                        'transaction_type': 'debit' if is_credit else 'credit',
                        'bank': 'bb',
                        'raw_data': dict(row_dict)
                    })
                
                except Exception as e:
                    self.errors.append({
                        'line': row_num,
                        'error': str(e)
                    })
        
        except Exception as e:
            self.errors.append({
                'line': 0,
                'error': f'Erro ao processar XLSX: {str(e)}'
            })
        
        return self.transactions


class BancoDosBrasilOFXParser(BankParser):
    """Parser para OFX do Banco do Brasil"""
    
    def parse(self, file_content: bytes) -> List[Dict]:
        """OFX com STMTTRN, TRNTYPE, DTPOSTED, TRNAMT, FITID, NAME, MEMO"""
        try:
            from ofxparse import OfxFile
        except ImportError:
            self.errors.append({
                'line': 0,
                'error': 'ofxparse não instalado. Instale com: pip install ofxparse'
            })
            return []
        
        self.transactions = []
        self.errors = []
        
        try:
            ofx = OfxFile(BytesIO(file_content))
            
            for account in ofx.accounts:
                for statement in account.statements:
                    for transaction in statement.transactions:
                        self.total_lines += 1
                        try:
                            date = transaction.date.strftime('%Y-%m-%d') if hasattr(transaction.date, 'strftime') else str(transaction.date)
                            
                            # TRNAMT: valor (negativo para débito, positivo para crédito)
                            amount = Decimal(str(transaction.amount))
                            
                            # Descrição vem de NAME ou MEMO
                            description = (transaction.payee or '') or (transaction.memo or '')
                            description = description.strip()[:200] if description else 'Sem descrição'
                            
                            self.transactions.append({
                                'date': date,
                                'description': description,
                                'amount': str(amount),
                                'type': 'income' if amount > 0 else 'expense',
                                'transaction_type': 'credit' if amount > 0 else 'debit',
                                'fitid': str(getattr(transaction, 'id', '')),
                                'bank': 'bb',
                                'raw_data': {
                                    'trntype': getattr(transaction, 'type', ''),
                                    'fitid': getattr(transaction, 'id', ''),
                                    'memo': getattr(transaction, 'memo', '')
                                }
                            })
                        
                        except Exception as e:
                            self.errors.append({
                                'line': self.total_lines,
                                'error': f'Erro ao processar transação OFX: {str(e)}'
                            })
        
        except Exception as e:
            self.errors.append({
                'line': 0,
                'error': f'Erro ao processar OFX: {str(e)}'
            })
        
        return self.transactions


class BancoDosBrasilBBTParser(BankParser):
    """Parser para BBT (formato próprio do Banco do Brasil)"""
    
    def parse(self, file_content: bytes) -> List[Dict]:
        """BBT delimitado por ponto e vírgula"""
        self.transactions = []
        self.errors = []
        
        try:
            content_str = file_content.decode('utf-8')
            lines = content_str.split('\n')
            
            # Assumir primeira linha como cabeçalho
            if not lines:
                return []
            
            for line_num, line in enumerate(lines, start=1):
                line = line.strip()
                if not line or line_num == 1:  # Pular cabeçalho e linhas vazias
                    continue
                
                self.total_lines += 1
                try:
                    parts = line.split(';')
                    if len(parts) < 5:
                        self.errors.append({
                            'line': line_num,
                            'error': f'Formato inválido: esperado 6 campos, encontrado {len(parts)}'
                        })
                        continue
                    
                    date_str = parts[0].strip()
                    # lançamento = parts[1].strip()  # Ignorar por enquanto
                    description = parts[2].strip()
                    document_no = parts[3].strip()
                    value_str = parts[4].strip()
                    type_str = parts[5].strip().upper() if len(parts) > 5 else 'CRÉDITO'
                    
                    date = self.normalize_date(date_str, ['%d/%m/%Y'])
                    if not date:
                        self.errors.append({
                            'line': line_num,
                            'error': f'Data inválida: {date_str}'
                        })
                        continue
                    
                    amount = self.parse_decimal(value_str)
                    if amount is None:
                        self.errors.append({
                            'line': line_num,
                            'error': f'Valor inválido: {value_str}'
                        })
                        continue
                    
                    is_credit = type_str in ['DÉBITO', 'SAÍDA', 'DESPESA']
                    if is_credit:
                        amount = abs(amount) * -1
                    else:
                        amount = abs(amount)
                    
                    self.transactions.append({
                        'date': date,
                        'description': description,
                        'amount': str(amount),
                        'type': 'expense' if is_credit else 'income',
                        'document_number': document_no,
                        'transaction_type': 'debit' if is_credit else 'credit',
                        'bank': 'bb',
                        'raw_data': {'line': line}
                    })
                
                except Exception as e:
                    self.errors.append({
                        'line': line_num,
                        'error': str(e)
                    })
        
        except Exception as e:
            self.errors.append({
                'line': 0,
                'error': f'Erro ao processar BBT: {str(e)}'
            })
        
        return self.transactions


class BancoDosBrasilTXTParser(BankParser):
    """Parser para TXT (formato colunar com espaços fixos)"""
    
    def parse(self, file_content: bytes) -> List[Dict]:
        """TXT com colunas: Data, Lançamento, Detalhes, N° documento, Valor, Tipo Lançamento"""
        self.transactions = []
        self.errors = []
        
        try:
            content_str = file_content.decode('utf-8')
            lines = content_str.split('\n')
            
            for line_num, line in enumerate(lines, start=1):
                if not line.strip() or line_num == 1:  # Pular cabeçalho e linhas vazias
                    continue
                
                self.total_lines += 1
                try:
                    # Formato colunar - posições fixas estimadas
                    # Assumindo: Data (0-10), Lançamento (11-30), Detalhes (31-70), Doc (71-85), Valor (86-100), Tipo (101+)
                    
                    date_str = line[0:10].strip() if len(line) > 10 else ''
                    # lancamento = line[11:30].strip() if len(line) > 30 else ''
                    description = line[31:70].strip() if len(line) > 70 else ''
                    document_no = line[71:85].strip() if len(line) > 85 else ''
                    value_str = line[86:100].strip() if len(line) > 100 else ''
                    type_str = line[101:].strip().upper() if len(line) > 101 else 'CRÉDITO'
                    
                    if not date_str or not value_str:
                        self.errors.append({
                            'line': line_num,
                            'error': 'Data ou valor ausentes'
                        })
                        continue
                    
                    date = self.normalize_date(date_str, ['%d/%m/%Y'])
                    if not date:
                        self.errors.append({
                            'line': line_num,
                            'error': f'Data inválida: {date_str}'
                        })
                        continue
                    
                    amount = self.parse_decimal(value_str)
                    if amount is None:
                        self.errors.append({
                            'line': line_num,
                            'error': f'Valor inválido: {value_str}'
                        })
                        continue
                    
                    is_credit = type_str in ['DÉBITO', 'SAÍDA', 'DESPESA']
                    if is_credit:
                        amount = abs(amount) * -1
                    else:
                        amount = abs(amount)
                    
                    self.transactions.append({
                        'date': date,
                        'description': description or 'Sem descrição',
                        'amount': str(amount),
                        'type': 'expense' if is_credit else 'income',
                        'document_number': document_no,
                        'transaction_type': 'debit' if is_credit else 'credit',
                        'bank': 'bb',
                        'raw_data': {'line': line}
                    })
                
                except Exception as e:
                    self.errors.append({
                        'line': line_num,
                        'error': str(e)
                    })
        
        except Exception as e:
            self.errors.append({
                'line': 0,
                'error': f'Erro ao processar TXT: {str(e)}'
            })
        
        return self.transactions


# Parsers para Itaú
class ItauPDFParser(BankParser):
    """Parser para PDF do Itaú"""
    
    def parse(self, file_content: bytes) -> List[Dict]:
        """PDF com campos: data, lançamento, valor (R$), saldo (R$)"""
        try:
            import PyPDF2
        except ImportError:
            self.errors.append({
                'line': 0,
                'error': 'PyPDF2 não instalado'
            })
            return []
        
        self.transactions = []
        self.errors = []
        
        try:
            pdf_file = BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            for page_num, page in enumerate(pdf_reader.pages, start=1):
                text = page.extract_text()
                lines = text.split('\n')
                
                for line_num, line in enumerate(lines, start=1):
                    line = line.strip()
                    if not line or len(line) < 10:
                        continue
                    
                    try:
                        parts = line.split()
                        if len(parts) < 3:
                            continue
                        
                        date_str = parts[0]
                        date = self.normalize_date(date_str, ['%d/%m', '%d/%m/%Y'])
                        
                        if not date:
                            continue
                        
                        # Procurar valor com R$
                        value_str = None
                        for part in parts:
                            if 'R$' in part or self.parse_decimal(part):
                                value_str = part
                                break
                        
                        if not value_str:
                            continue
                        
                        amount = self.parse_decimal(value_str)
                        if not amount:
                            continue
                        
                        description = ' '.join(parts[1:]) if len(parts) > 1 else line
                        
                        self.transactions.append({
                            'date': date,
                            'description': description[:200],
                            'amount': str(amount),
                            'type': 'income' if amount > 0 else 'expense',
                            'transaction_type': 'credit' if amount > 0 else 'debit',
                            'bank': 'itau',
                            'raw_data': {'pdf_line': line, 'page': page_num}
                        })
                    
                    except Exception as e:
                        self.errors.append({
                            'line': page_num,
                            'error': f'Erro ao processar linha: {str(e)}'
                        })
        
        except Exception as e:
            self.errors.append({
                'line': 0,
                'error': f'Erro ao processar PDF Itaú: {str(e)}'
            })
        
        return self.transactions


# Parsers para Nubank
class NubankCSVParser(BankParser):
    """Parser para CSV do Nubank"""
    
    def parse(self, file_content: bytes) -> List[Dict]:
        """CSV com campos: Data, Valor, Identificador, Descrição"""
        self.transactions = []
        self.errors = []
        
        try:
            content_str = file_content.decode('utf-8')
            reader = csv.DictReader(StringIO(content_str), delimiter=',')
            
            for line_num, row in enumerate(reader, start=2):
                self.total_lines += 1
                try:
                    date_str = row.get('Data', '').strip()
                    value_str = row.get('Valor', '').strip()
                    identifier = row.get('Identificador', '').strip()
                    description = row.get('Descrição', '').strip()
                    
                    if not date_str or not value_str or not description:
                        self.errors.append({
                            'line': line_num,
                            'error': 'Campos obrigatórios ausentes'
                        })
                        continue
                    
                    date = self.normalize_date(date_str)
                    if not date:
                        self.errors.append({
                            'line': line_num,
                            'error': f'Data inválida: {date_str}'
                        })
                        continue
                    
                    amount = self.parse_decimal(value_str)
                    if amount is None:
                        self.errors.append({
                            'line': line_num,
                            'error': f'Valor inválido: {value_str}'
                        })
                        continue
                    
                    self.transactions.append({
                        'date': date,
                        'description': description,
                        'amount': str(amount),
                        'type': 'income' if amount > 0 else 'expense',
                        'fitid': identifier,
                        'transaction_type': 'credit' if amount > 0 else 'debit',
                        'bank': 'nubank',
                        'raw_data': dict(row)
                    })
                
                except Exception as e:
                    self.errors.append({
                        'line': line_num,
                        'error': str(e)
                    })
        
        except Exception as e:
            self.errors.append({
                'line': 0,
                'error': f'Erro ao processar CSV Nubank: {str(e)}'
            })
        
        return self.transactions


class NubankOFXParser(BankParser):
    """Parser para OFX do Nubank"""
    
    def parse(self, file_content: bytes) -> List[Dict]:
        """OFX com STMTTRN, TRNTYPE, DTPOSTED, TRNAMT, FITID, MEMO"""
        try:
            from ofxparse import OfxFile
        except ImportError:
            self.errors.append({
                'line': 0,
                'error': 'ofxparse não instalado'
            })
            return []
        
        self.transactions = []
        self.errors = []
        
        try:
            ofx = OfxFile(BytesIO(file_content))
            
            for account in ofx.accounts:
                for statement in account.statements:
                    for transaction in statement.transactions:
                        self.total_lines += 1
                        try:
                            date = transaction.date.strftime('%Y-%m-%d') if hasattr(transaction.date, 'strftime') else str(transaction.date)
                            amount = Decimal(str(transaction.amount))
                            description = (transaction.payee or '') or (transaction.memo or '')
                            description = description.strip()[:200] if description else 'Sem descrição'
                            
                            self.transactions.append({
                                'date': date,
                                'description': description,
                                'amount': str(amount),
                                'type': 'income' if amount > 0 else 'expense',
                                'transaction_type': 'credit' if amount > 0 else 'debit',
                                'fitid': str(getattr(transaction, 'id', '')),
                                'bank': 'nubank',
                                'raw_data': {
                                    'trntype': getattr(transaction, 'type', ''),
                                    'fitid': getattr(transaction, 'id', ''),
                                    'memo': getattr(transaction, 'memo', '')
                                }
                            })
                        
                        except Exception as e:
                            self.errors.append({
                                'line': self.total_lines,
                                'error': f'Erro ao processar transação: {str(e)}'
                            })
        
        except Exception as e:
            self.errors.append({
                'line': 0,
                'error': f'Erro ao processar OFX Nubank: {str(e)}'
            })
        
        return self.transactions


# Factory para criar parser apropriado
def get_parser(bank: str, file_format: str) -> Optional[BankParser]:
    """Retorna parser apropriado para banco e formato"""
    
    parsers_map = {
        ('bb', 'csv'): BancoDosBrasilCSVParser,
        ('bb', 'xlsx'): BancoDosBrasilXLSXParser,
        ('bb', 'pdf'): BancoDosBrasilPDFParser,
        ('bb', 'ofx'): BancoDosBrasilOFXParser,
        ('bb', 'bbt'): BancoDosBrasilBBTParser,
        ('bb', 'txt'): BancoDosBrasilTXTParser,
        ('itau', 'pdf'): ItauPDFParser,
        ('nubank', 'csv'): NubankCSVParser,
        ('nubank', 'ofx'): NubankOFXParser,
    }
    
    parser_class = parsers_map.get((bank, file_format))
    return parser_class() if parser_class else None
