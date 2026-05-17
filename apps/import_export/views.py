from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core import serializers
from django.db.models import Sum, Count
from django.utils import timezone
import json
import csv
import logging
from io import StringIO, BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from .models import ExportHistory, ImportHistory, TransactionImportMetadata
from .forms import BankStatementImportForm
from .services import BankStatementImportService

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def api_import_debug(request):
    """Endpoint de diagnóstico para identificar o erro 500"""
    import traceback
    try:
        print("=" * 50)
        print("DEBUG: Iniciando importação de diagnóstico")
        print(f"POST data: {request.POST}")
        print(f"FILES: {request.FILES}")
        print(f"Method: {request.method}")
        
        # Verificar arquivo
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'Nenhum arquivo enviado'}, status=400)
        
        uploaded_file = request.FILES['file']
        print(f"Arquivo recebido: {uploaded_file.name}, tamanho: {uploaded_file.size}")
        
        # Verificar parâmetros
        bank = request.POST.get('bank', '')
        file_format = request.POST.get('file_format', '')
        print(f"Bank: {bank}, Format: {file_format}")
        
        # Teste 1: Verificar se consegue ler o arquivo
        file_content = uploaded_file.read()
        print(f"Arquivo lido com sucesso: {len(file_content)} bytes")
        
        # Teste 2: Verificar importação dos models
        try:
            from transactions.models import Transaction
            print("✓ Model Transaction importado com sucesso")
        except ImportError as e:
            print(f"✗ Erro ao importar Transaction: {e}")
            return JsonResponse({
                'error': f'App transactions não encontrado: {str(e)}',
                'solution': 'Execute: python manage.py startapp transactions'
            }, status=500)
        
        try:
            from categories.models import Category
            print("✓ Model Category importado com sucesso")
        except ImportError as e:
            print(f"✗ Erro ao importar Category: {e}")
            return JsonResponse({
                'error': f'App categories não encontrado: {str(e)}',
                'solution': 'Execute: python manage.py startapp categories'
            }, status=500)
        
        # Teste 3: Verificar o serviço
        try:
            from .services import BankStatementImportService
            print("✓ Service importado com sucesso")
        except ImportError as e:
            print(f"✗ Erro ao importar Service: {e}")
            traceback.print_exc()
            return JsonResponse({'error': f'Erro no service: {str(e)}'}, status=500)
        
        # Teste 4: Executar importação
        try:
            import_service = BankStatementImportService(
                user=request.user,
                bank=bank,
                file_format=file_format,
                filename=uploaded_file.name,
                file_size=uploaded_file.size
            )
            print("✓ Service instanciado com sucesso")
            
            result = import_service.import_file(file_content)
            print(f"✓ Importação concluída: {result}")
            
            return JsonResponse(result)
            
        except Exception as e:
            print(f"✗ Erro na execução do service: {str(e)}")
            traceback.print_exc()
            return JsonResponse({
                'error': f'Erro no service: {str(e)}',
                'traceback': traceback.format_exc()
            }, status=500)
        
    except Exception as e:
        print(f"✗ Erro geral: {str(e)}")
        traceback.print_exc()
        return JsonResponse({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)

# Importar modelos de outros apps
try:
    from transactions.models import Transaction
    from categories.models import Category
    HAS_TRANSACTIONS = True
except ImportError:
    HAS_TRANSACTIONS = False

logger = logging.getLogger(__name__)

@login_required
def import_export_page(request):
    """Renderiza a página de importação/exportação"""
    return render(request, 'import_export/import_export.html')


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def api_import(request):
    """API endpoint para importar extratos bancários de múltiplos bancos e formatos"""
    try:
        # Validar arquivo
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Nenhum arquivo enviado'
            }, status=400)
        
        uploaded_file = request.FILES['file']
        
        # Obter parâmetros - tentar tanto POST quanto FormData
        bank = request.POST.get('bank', '')
        file_format = request.POST.get('file_format', '')
        
        # Se não veio por POST, tentar via request body (JSON)
        if not bank and request.body:
            try:
                body_data = json.loads(request.body)
                bank = body_data.get('bank', '')
                file_format = body_data.get('file_format', '')
            except:
                pass
        
        # Se ainda não tem, tentar inferir pela extensão
        if not file_format:
            filename = uploaded_file.name.lower()
            if '.' in filename:
                file_format = filename.split('.')[-1]
        
        # Validações básicas
        if not bank:
            return JsonResponse({
                'success': False,
                'error': 'Banco não informado. Selecione um banco (bb, itau, nubank, generic)'
            }, status=400)
        
        if not file_format:
            return JsonResponse({
                'success': False,
                'error': 'Formato de arquivo não identificado'
            }, status=400)
        
        # Normalizar formatos
        valid_formats = ['csv', 'xlsx', 'xls', 'pdf', 'ofx', 'bbt', 'txt', 'json']
        file_format = file_format.lower()
        
        if file_format not in valid_formats:
            return JsonResponse({
                'success': False,
                'error': f'Formato não suportado: {file_format}. Formatos válidos: {", ".join(valid_formats)}'
            }, status=400)
        
        # Normalizar xls para xlsx
        if file_format == 'xls':
            file_format = 'xlsx'
        
        # Ler conteúdo do arquivo
        file_content = uploaded_file.read()
        
        if not file_content:
            return JsonResponse({
                'success': False,
                'error': 'Arquivo vazio'
            }, status=400)
        
        logger.info(f"Iniciando importação: bank={bank}, format={file_format}, file={uploaded_file.name}, size={uploaded_file.size}")
        
        # Usar serviço de importação
        import_service = BankStatementImportService(
            user=request.user,
            bank=bank,
            file_format=file_format,
            filename=uploaded_file.name,
            file_size=uploaded_file.size
        )
        
        result = import_service.import_file(file_content)
        
        # Garantir que result tenha os campos esperados pelo frontend
        if 'success' not in result:
            result['success'] = result.get('records_imported', 0) > 0
        
        # Retornar resultado
        status_code = 200 if result.get('success') else 400
        return JsonResponse(result, status=status_code)
    
    except Exception as e:
        logger.error(f"Erro ao importar arquivo: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'status': 'failed',
            'message': f'Erro ao processar importação: {str(e)}'
        }, status=500)


@login_required
def api_export(request):
    """API endpoint para exportar dados"""
    try:
        format_type = request.GET.get('format', 'json')
        data_type = request.GET.get('type', 'all')
        
        # Coletar dados
        export_data = {
            'export_date': timezone.now().isoformat(),
            'version': '1.0',
            'user': request.user.username,
            'data': {}
        }
        
        # Buscar transações
        if HAS_TRANSACTIONS and data_type in ['all', 'transactions']:
            transactions = Transaction.objects.filter(user=request.user)
            export_data['data']['transactions'] = list(transactions.values(
                'id', 'description', 'amount', 'date', 'type', 'notes'
            ))
            for t in export_data['data']['transactions']:
                if 'date' in t and t['date']:
                    t['date'] = t['date'].isoformat()
        
        # Buscar categorias
        if HAS_TRANSACTIONS and data_type in ['all', 'categories']:
            categories = Category.objects.filter(user=request.user)
            export_data['data']['categories'] = list(categories.values(
                'id', 'name', 'type', 'icon', 'color', 'budget', 'is_default'
            ))
        
        # Estatísticas
        if HAS_TRANSACTIONS:
            total_income = Transaction.objects.filter(
                user=request.user, type='income'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            total_expense = Transaction.objects.filter(
                user=request.user, type='expense'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            export_data['data']['stats'] = {
                'total_transactions': Transaction.objects.filter(user=request.user).count(),
                'total_income': float(total_income),
                'total_expense': float(total_expense),
                'balance': float(total_income - total_expense)
            }
        
        # Exportar no formato solicitado
        if format_type == 'json':
            return export_as_json(request, export_data)
        elif format_type == 'csv':
            return export_as_csv(request, export_data)
        elif format_type == 'pdf':
            return export_as_pdf(request, export_data)
        else:
            return JsonResponse({'error': 'Formato não suportado'}, status=400)
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


def export_as_json(request, data):
    """Exporta dados como JSON"""
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    # Registrar no histórico
    ExportHistory.objects.create(
        user=request.user,
        format='json',
        records_count=len(data.get('data', {}).get('transactions', [])),
        file_size=len(json_str.encode('utf-8'))
    )
    
    response = HttpResponse(json_str, content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="myledger_export_{timezone.now().date()}.json"'
    return response


def export_as_csv(request, data):
    """Exporta dados como CSV"""
    output = StringIO()
    transactions = data.get('data', {}).get('transactions', [])
    
    if not transactions:
        return JsonResponse({'error': 'Nenhuma transação para exportar'}, status=400)
    
    # Definir cabeçalhos
    fieldnames = ['id', 'data', 'descricao', 'valor', 'tipo', 'categoria', 'observacoes']
    writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=';')
    writer.writeheader()
    
    # Escrever dados
    for t in transactions:
        writer.writerow({
            'id': t.get('id'),
            'data': t.get('date'),
            'descricao': t.get('description'),
            'valor': t.get('amount'),
            'tipo': 'Receita' if t.get('type') == 'income' else 'Despesa',
            'categoria': t.get('category', ''),
            'observacoes': t.get('notes', '')
        })
    
    csv_content = output.getvalue()
    output.close()
    
    # Registrar no histórico
    ExportHistory.objects.create(
        user=request.user,
        format='csv',
        records_count=len(transactions),
        file_size=len(csv_content.encode('utf-8'))
    )
    
    response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="myledger_export_{timezone.now().date()}.csv"'
    return response


def export_as_pdf(request, data):
    """Exporta dados como PDF (mantendo a implementação original com reportlab)"""
    from reportlab.lib import fonts
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    # Registrar fonte para suporte a português
    try:
        pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
        font_name = 'DejaVu'
    except:
        font_name = 'Helvetica'
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="myledger_export_{timezone.now().date()}.pdf"'
    
    # Criar PDF
    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilo personalizado
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#8A4FFF'),
        alignment=1,  # Centralizado
        fontName=font_name
    )
    
    # Título
    elements.append(Paragraph(f"MyLedger - Relatório de Dados", title_style))
    elements.append(Spacer(1, 30))
    
    # Estatísticas
    stats = data.get('data', {}).get('stats', {})
    stats_data = [
        ['Data de Exportação', data.get('export_date', '')[:10]],
        ['Usuário', data.get('user', '')],
        ['Total de Transações', str(stats.get('total_transactions', 0))],
        ['Total de Receitas', f"R$ {stats.get('total_income', 0):.2f}"],
        ['Total de Despesas', f"R$ {stats.get('total_expense', 0):.2f}"],
        ['Saldo', f"R$ {stats.get('balance', 0):.2f}"],
    ]
    
    stats_table = Table(stats_data, colWidths=[5*cm, 8*cm])
    stats_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 20))
    
    # Transações
    transactions = data.get('data', {}).get('transactions', [])
    if transactions:
        elements.append(Paragraph("Transações Recentes", styles['Heading2']))
        elements.append(Spacer(1, 10))
        
        # Dados da tabela
        table_data = [['Data', 'Descrição', 'Valor', 'Tipo']]
        for t in transactions[:50]:  # Limitar a 50 transações
            table_data.append([
                t.get('date', '')[:10],
                t.get('description', '')[:30],
                f"R$ {t.get('amount', 0):.2f}",
                'Receita' if t.get('type') == 'income' else 'Despesa'
            ])
        
        trans_table = Table(table_data, colWidths=[3*cm, 6*cm, 3*cm, 3*cm])
        trans_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8A4FFF')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(trans_table)
    
    # Registrar exportação
    ExportHistory.objects.create(
        user=request.user,
        format='pdf',
        records_count=len(transactions),
        file_size=0  # PDF size hard to calculate
    )
    
    doc.build(elements)
    return response


@login_required
def api_export_history(request):
    """Retorna histórico de exportações"""
    exports = ExportHistory.objects.filter(user=request.user)[:20]
    data = [{
        'format': e.format,
        'records': e.records_count,
        'date': e.created_at.isoformat(),
        'file_size': e.file_size
    } for e in exports]
    return JsonResponse({'success': True, 'history': data})


@login_required
def api_import_history(request):
    """Retorna histórico de importações com detalhes"""
    try:
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        bank = request.GET.get('bank', '')
        status = request.GET.get('status', '')
        
        queryset = ImportHistory.objects.filter(user=request.user)
        
        if bank:
            queryset = queryset.filter(bank=bank)
        if status:
            queryset = queryset.filter(status=status)
        
        total = queryset.count()
        start = (page - 1) * per_page
        end = start + per_page
        
        imports = queryset[start:end]
        
        data = []
        for imp in imports:
            import_data = {
                'id': imp.id,
                'filename': imp.filename,
                'bank': imp.get_bank_display(),
                'format': imp.get_file_format_display(),
                'status': imp.get_status_display(),
                'total_lines': imp.total_lines_read,
                'imported': imp.records_imported,
                'failed': imp.records_failed,
                'duplicates': imp.duplicates_ignored,
                'date': imp.created_at.isoformat(),
                'error': imp.error_message
            }
            data.append(import_data)
        
        return JsonResponse({
            'success': True,
            'total': total,
            'page': page,
            'per_page': per_page,
            'history': data
        })
    
    except Exception as e:
        logger.error(f"Erro ao buscar histórico: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def api_import_detail(request, import_id):
    """Retorna detalhes de uma importação específica"""
    try:
        imp = ImportHistory.objects.get(id=import_id, user=request.user)
        
        # Transações importadas
        imported_transactions = TransactionImportMetadata.objects.filter(
            import_history=imp
        ).select_related('transaction')[:100]
        
        transactions_data = []
        for metadata in imported_transactions:
            trans = metadata.transaction
            transactions_data.append({
                'id': trans.id,
                'date': trans.date.isoformat(),
                'description': trans.description,
                'amount': float(trans.amount),
                'type': trans.get_type_display(),
                'document_number': metadata.document_number,
                'fitid': metadata.fitid
            })
        
        return JsonResponse({
            'success': True,
            'import': {
                'id': imp.id,
                'filename': imp.filename,
                'bank': imp.get_bank_display(),
                'format': imp.get_file_format_display(),
                'status': imp.get_status_display(),
                'total_lines': imp.total_lines_read,
                'imported': imp.records_imported,
                'failed': imp.records_failed,
                'duplicates': imp.duplicates_ignored,
                'date': imp.created_at.isoformat(),
                'completed_at': imp.completed_at.isoformat() if imp.completed_at else None,
                'error': imp.error_message,
                'validation_errors': imp.validation_errors[:20]
            },
            'transactions': transactions_data
        })
    
    except ImportHistory.DoesNotExist:
        return JsonResponse({'error': 'Importação não encontrada'}, status=404)
    except Exception as e:
        logger.error(f"Erro ao buscar detalhes: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def api_import_banks_formats(request):
    """Retorna bancos e formatos suportados"""
    return JsonResponse({
        'success': True,
        'banks': [
            {'code': 'bb', 'name': 'Banco do Brasil', 'formats': ['csv', 'xlsx', 'pdf', 'ofx', 'bbt', 'txt']},
            {'code': 'itau', 'name': 'Itaú', 'formats': ['pdf']},
            {'code': 'nubank', 'name': 'Nubank', 'formats': ['csv', 'ofx', 'pdf']},
            {'code': 'generic', 'name': 'Genérico', 'formats': ['csv', 'json']},
        ],
        'formats': [
            {'code': 'csv', 'name': 'CSV', 'extension': '.csv', 'description': 'Valores Separados por Vírgula'},
            {'code': 'xlsx', 'name': 'Excel', 'extension': '.xlsx', 'description': 'Microsoft Excel'},
            {'code': 'pdf', 'name': 'PDF', 'extension': '.pdf', 'description': 'Arquivo PDF'},
            {'code': 'ofx', 'name': 'OFX', 'extension': '.ofx', 'description': 'Open Financial Exchange'},
            {'code': 'bbt', 'name': 'BBT', 'extension': '.bbt', 'description': 'Formato Banco do Brasil'},
            {'code': 'txt', 'name': 'TXT', 'extension': '.txt', 'description': 'Arquivo de Texto'},
            {'code': 'json', 'name': 'JSON', 'extension': '.json', 'description': 'JSON'},
        ]
    })


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def api_clear_all_data(request):
    """Limpa todos os dados do usuário (NOVA FUNÇÃO ADICIONADA)"""
    try:
        # Importar modelos
        try:
            from transactions.models import Transaction
            from categories.models import Category
            
            # Deletar transações (não as categorias padrão)
            deleted_transactions = Transaction.objects.filter(user=request.user).delete()
            
            # Deletar categorias que não são padrão
            deleted_categories = Category.objects.filter(user=request.user, is_default=False).delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Todos os dados foram removidos com sucesso',
                'deleted': {
                    'transactions': str(deleted_transactions[0]) if deleted_transactions else 0,
                    'categories': str(deleted_categories[0]) if deleted_categories else 0
                }
            })
        except ImportError:
            # Se o app transactions não estiver disponível
            return JsonResponse({
                'success': True,
                'message': 'App de transações não encontrado, nenhum dado removido'
            })
            
    except Exception as e:
        logger.error(f"Erro ao limpar dados: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)