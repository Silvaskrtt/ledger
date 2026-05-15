# import_export/views.py
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
from io import StringIO, BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from .models import ExportHistory, ImportHistory

# Importar modelos de outros apps
try:
    from transactions.models import Transaction
    from categories.models import Category
    HAS_TRANSACTIONS = True
except ImportError:
    HAS_TRANSACTIONS = False

@login_required
def import_export_page(request):
    """Renderiza a página de importação/exportação"""
    return render(request, 'import_export/import_export.html')

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
    """Exporta dados como PDF"""
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
@require_http_methods(["POST"])
@csrf_exempt
def api_import(request):
    """API endpoint para importar dados"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'Nenhum arquivo enviado'}, status=400)
        
        uploaded_file = request.FILES['file']
        filename = uploaded_file.name
        file_extension = filename.split('.')[-1].lower()
        
        if file_extension not in ['json', 'csv']:
            return JsonResponse({'error': 'Formato não suportado. Use JSON ou CSV.'}, status=400)
        
        # Registrar importação
        import_record = ImportHistory.objects.create(
            user=request.user,
            filename=filename,
            format=file_extension,
            status='processing'
        )
        
        try:
            if file_extension == 'json':
                data = json.loads(uploaded_file.read().decode('utf-8'))
                result = process_json_import(request, data)
            else:  # csv
                csv_content = uploaded_file.read().decode('utf-8')
                result = process_csv_import(request, csv_content)
            
            # Atualizar registro
            import_record.status = 'completed'
            import_record.records_imported = result.get('imported', 0)
            import_record.records_failed = result.get('failed', 0)
            import_record.completed_at = timezone.now()
            import_record.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Importação concluída: {result["imported"]} registros importados',
                'details': result
            })
            
        except Exception as e:
            import_record.status = 'failed'
            import_record.error_message = str(e)
            import_record.save()
            raise
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def process_json_import(request, data):
    """Processa importação de JSON"""
    imported = 0
    failed = 0
    
    transactions_data = data.get('data', {}).get('transactions', [])
    
    if not HAS_TRANSACTIONS:
        return {'imported': 0, 'failed': len(transactions_data), 'message': 'App de transações não encontrado'}
    
    for trans_data in transactions_data:
        try:
            # Verificar se já existe (opcional)
            transaction_id = trans_data.get('id')
            if transaction_id and Transaction.objects.filter(id=transaction_id, user=request.user).exists():
                continue  # Pular duplicatas
            
            # Criar transação
            Transaction.objects.create(
                user=request.user,
                description=trans_data.get('description', ''),
                amount=float(trans_data.get('amount', 0)),
                date=trans_data.get('date'),
                type=trans_data.get('type', 'expense'),
                category=trans_data.get('category', ''),
                notes=trans_data.get('notes', '')
            )
            imported += 1
        except Exception as e:
            failed += 1
    
    return {'imported': imported, 'failed': failed}

def process_csv_import(request, csv_content):
    """Processa importação de CSV"""
    imported = 0
    failed = 0
    
    if not HAS_TRANSACTIONS:
        return {'imported': 0, 'failed': 1, 'message': 'App de transações não encontrado'}
    
    reader = csv.DictReader(StringIO(csv_content), delimiter=';')
    
    for row in reader:
        try:
            Transaction.objects.create(
                user=request.user,
                description=row.get('descricao', ''),
                amount=float(row.get('valor', 0).replace(',', '.')),
                date=row.get('data', ''),
                type='income' if row.get('tipo') == 'Receita' else 'expense',
                category=row.get('categoria', ''),
                notes=row.get('observacoes', '')
            )
            imported += 1
        except Exception as e:
            failed += 1
    
    return {'imported': imported, 'failed': failed}

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
    """Retorna histórico de importações"""
    imports = ImportHistory.objects.filter(user=request.user)[:20]
    data = [{
        'filename': i.filename,
        'format': i.format,
        'imported': i.records_imported,
        'failed': i.records_failed,
        'status': i.status,
        'date': i.created_at.isoformat()
    } for i in imports]
    return JsonResponse({'success': True, 'history': data})

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def api_clear_all_data(request):
    """Limpa todos os dados do usuário"""
    try:
        if HAS_TRANSACTIONS:
            deleted_transactions = Transaction.objects.filter(user=request.user).delete()
        
        # Não deletar categorias padrão
        if HAS_TRANSACTIONS:
            Category.objects.filter(user=request.user, is_default=False).delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Todos os dados foram removidos com sucesso'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)