# import_export/tests/test_parsers.py
"""
Testes para os parsers de diferentes bancos e formatos
"""
from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
import json
from io import BytesIO

from import_export.parsers import (
    BancoDosBrasilCSVParser,
    BancoDosBrasilXLSXParser,
    NubankCSVParser,
    get_parser
)
from import_export.validators import TransactionValidator, DuplicateDetector


class BancoDosBrasilCSVParserTest(TestCase):
    """Testes para parser CSV do Banco do Brasil"""
    
    def setUp(self):
        self.parser = BancoDosBrasilCSVParser()
    
    def test_parse_valid_csv(self):
        """Testa parsing de CSV válido"""
        csv_content = b"""Data;Lancamento;Detalhes;N\xc2\xb0 documento;Valor;Tipo Lancamento
17/05/2024;001;Compra mercado;DOC123;-50,00;DEBITO
18/05/2024;002;Salario;DEP456;5000,00;CREDITO"""
        
        result = self.parser.parse(csv_content)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['description'], 'Compra mercado')
        self.assertEqual(float(result[0]['amount']), -50.0)
        self.assertEqual(result[0]['type'], 'expense')
    
    def test_parse_invalid_dates(self):
        """Testa handling de datas inválidas"""
        csv_content = b"""Data;Lancamento;Detalhes;N\xc2\xb0 documento;Valor;Tipo Lancamento
00/00/0000;001;Transacao invalida;DOC123;-50,00;DEBITO"""
        
        result = self.parser.parse(csv_content)
        
        self.assertEqual(len(result), 0)
        self.assertTrue(len(self.parser.errors) > 0)


class TransactionValidatorTest(TestCase):
    """Testes para validador de transações"""
    
    def test_validate_valid_date(self):
        """Testa validação de data válida"""
        valid, date_val, error = TransactionValidator.validate_date('2024-05-17')
        
        self.assertTrue(valid)
        self.assertEqual(date_val, '2024-05-17')
        self.assertIsNone(error)
    
    def test_validate_invalid_date(self):
        """Testa validação de data inválida"""
        valid, date_val, error = TransactionValidator.validate_date('2030-05-17')
        
        self.assertFalse(valid)
        self.assertIsNotNone(error)
    
    def test_validate_valid_amount(self):
        """Testa validação de valor válido"""
        valid, amount, error = TransactionValidator.validate_amount('50.00')
        
        self.assertTrue(valid)
        self.assertEqual(amount, Decimal('50.00'))
    
    def test_validate_zero_amount(self):
        """Testa validação de valor zero"""
        valid, amount, error = TransactionValidator.validate_amount('0')
        
        self.assertFalse(valid)
        self.assertIsNotNone(error)
    
    def test_validate_transaction_data(self):
        """Testa validação completa de transação"""
        transaction_data = {
            'date': '2024-05-17',
            'description': 'Compra teste',
            'amount': '50.00',
            'type': 'expense'
        }
        
        valid, validated, errors = TransactionValidator.validate_transaction_data(transaction_data)
        
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)
        self.assertEqual(validated['description'], 'Compra teste')


class DuplicateDetectorTest(TestCase):
    """Testes para detector de duplicatas"""
    
    def test_detect_by_fitid(self):
        """Testa detecção de duplicata por FITID"""
        trans1 = {'fitid': 'ABC123', 'date': '2024-05-17', 'amount': '50.00'}
        trans2 = {'fitid': 'ABC123', 'date': '2024-05-17', 'amount': '50.00'}
        
        is_dup, identifier = DuplicateDetector.is_duplicate(trans1, [trans2])
        
        self.assertTrue(is_dup)
        self.assertEqual(identifier, 'ABC123')
    
    def test_detect_by_composite_key(self):
        """Testa detecção de duplicata por chave composta"""
        trans1 = {
            'date': '2024-05-17',
            'amount': '50.00',
            'description': 'Compra mercado'
        }
        trans2 = {
            'date': '2024-05-17',
            'amount': '50.00',
            'description': 'Compra mercado',
            'fitid': None
        }
        
        is_dup, identifier = DuplicateDetector.is_duplicate(trans1, [trans2])
        
        self.assertTrue(is_dup)
    
    def test_not_duplicate(self):
        """Testa que transações diferentes não são duplicatas"""
        trans1 = {
            'fitid': 'ABC123',
            'date': '2024-05-17',
            'amount': '50.00'
        }
        trans2 = {
            'fitid': 'XYZ789',
            'date': '2024-05-18',
            'amount': '100.00'
        }
        
        is_dup, identifier = DuplicateDetector.is_duplicate(trans1, [trans2])
        
        self.assertFalse(is_dup)


class ParserFactoryTest(TestCase):
    """Testes para o factory de parsers"""
    
    def test_get_parser_valid(self):
        """Testa obtenção de parser válido"""
        parser = get_parser('bb', 'csv')
        
        self.assertIsNotNone(parser)
        self.assertIsInstance(parser, BancoDosBrasilCSVParser)
    
    def test_get_parser_invalid(self):
        """Testa obtenção de parser inválido"""
        parser = get_parser('invalid_bank', 'csv')
        
        self.assertIsNone(parser)
    
    def test_get_parser_nubank_csv(self):
        """Testa obtenção de parser Nubank CSV"""
        parser = get_parser('nubank', 'csv')
        
        self.assertIsNotNone(parser)
        self.assertIsInstance(parser, NubankCSVParser)
