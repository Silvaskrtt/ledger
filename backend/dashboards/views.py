# backend/dashboards/views.py

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.dateparse import parse_datetime
from datetime import datetime, timedelta
from decimal import Decimal

from .services import CardExpenseService, CategoryExpenseService, CashFlowService
from .serializers import (
    CardExpenseDataSerializer,
    CategoryExpenseDataSerializer,
    CashFlowDataSerializer,
    DashboardResponseSerializer
)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def card_expenses_dashboard(request):
    """
    Endpoint: GET /api/dashboard/card-expenses/
    
    Retorna gastos agrupados por cartão de crédito
    
    Query Parameters:
        - start_date: Data inicial (YYYY-MM-DD)
        - end_date: Data final (YYYY-MM-DD)
    
    Response:
        {
            "data": [
                {
                    "card_name": "Meu Cartão",
                    "card_type": "CREDIT",
                    "total_spent": 1500.50,
                    "transaction_count": 15
                }
            ],
            "total": 1500.50,
            "metadata": {
                "currency": "BRL"
            }
        }
    """
    try:
        # Obter parâmetros de data
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        start_date = None
        end_date = None
        
        if start_date_str and end_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                end_date = datetime.fromisoformat(end_date_str).replace(
                    hour=23, minute=59, second=59, microsecond=999999
                )
            except ValueError:
                return Response(
                    {"error": "Formato de data inválido. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Obter dados
        data, total = CardExpenseService.get_expenses_by_card(
            user=request.user,
            start_date=start_date,
            end_date=end_date
        )
        
        # Serializar
        serializer = CardExpenseDataSerializer(data, many=True)
        
        response_data = {
            "data": serializer.data,
            "total": str(total),
            "metadata": {
                "currency": "BRL",
                "filtered": bool(start_date and end_date)
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": f"Erro ao processar dashboard: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def category_expenses_dashboard(request):
    """
    Endpoint: GET /api/dashboard/category-expenses/
    
    Retorna gastos agrupados por categoria com percentuais
    
    Query Parameters:
        - include_pending: true/false (padrão: false)
        - start_date: Data inicial (YYYY-MM-DD)
        - end_date: Data final (YYYY-MM-DD)
    
    Response:
        {
            "data": [
                {
                    "category_id": "uuid",
                    "category_name": "Alimentação",
                    "category_color": "#FF5733",
                    "total_spent": 500.00,
                    "percentage": 33.33,
                    "transaction_count": 10
                }
            ],
            "total": 1500.50,
            "metadata": {
                "currency": "BRL",
                "include_pending": false
            }
        }
    """
    try:
        # Obter parâmetros
        include_pending = request.query_params.get('include_pending', 'false').lower() == 'true'
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        start_date = None
        end_date = None
        
        if start_date_str and end_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                end_date = datetime.fromisoformat(end_date_str).replace(
                    hour=23, minute=59, second=59, microsecond=999999
                )
            except ValueError:
                return Response(
                    {"error": "Formato de data inválido. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Obter dados
        data, total = CategoryExpenseService.get_expenses_by_category(
            user=request.user,
            include_pending=include_pending,
            start_date=start_date,
            end_date=end_date
        )
        
        # Serializar
        serializer = CategoryExpenseDataSerializer(data, many=True)
        
        response_data = {
            "data": serializer.data,
            "total": str(total),
            "metadata": {
                "currency": "BRL",
                "include_pending": include_pending,
                "filtered": bool(start_date and end_date)
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": f"Erro ao processar dashboard: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cash_flow_dashboard(request):
    """
    Endpoint: GET /api/dashboard/cash-flow/
    
    Retorna fluxo de caixa mensal (receitas vs despesas)
    
    Query Parameters:
        - year: Ano para filtrar (padrão: ano atual)
    
    Response:
        {
            "data": [
                {
                    "month": "Janeiro",
                    "month_number": 1,
                    "income": 5000.00,
                    "expense": 3000.00,
                    "balance": 2000.00
                }
            ],
            "metadata": {
                "currency": "BRL",
                "year": 2024
            }
        }
    """
    try:
        # Obter parâmetro de ano
        year_str = request.query_params.get('year')
        year = None
        
        if year_str:
            try:
                year = int(year_str)
            except ValueError:
                return Response(
                    {"error": "Ano deve ser um número inteiro"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Obter dados
        data = CashFlowService.get_monthly_cash_flow(
            user=request.user,
            year=year
        )
        
        # Serializar
        serializer = CashFlowDataSerializer(data, many=True)
        
        response_data = {
            "data": serializer.data,
            "metadata": {
                "currency": "BRL",
                "year": year or datetime.now().year
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": f"Erro ao processar dashboard: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
