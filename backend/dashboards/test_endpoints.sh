#!/bin/bash
# backend/dashboards/test_endpoints.sh
# Script para testar os endpoints de dashboards

# Configuração
BASE_URL="http://localhost:8000"
TOKEN="seu_token_aqui"  # Substitua pelo seu token de autenticação

echo "================================"
echo "Testando Endpoints de Dashboards"
echo "================================"
echo ""

# 1. Dashboard de Gastos por Cartão
echo "1. Dashboard de Gastos por Cartão"
echo "-----------------------------------"
curl -X GET "$BASE_URL/api/dashboard/card-expenses/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  | python -m json.tool
echo ""
echo ""

# 2. Dashboard de Gastos por Cartão com filtro de data
echo "2. Dashboard de Gastos por Cartão (com filtro de data)"
echo "-------------------------------------------------------"
curl -X GET "$BASE_URL/api/dashboard/card-expenses/?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  | python -m json.tool
echo ""
echo ""

# 3. Dashboard de Gastos por Categoria
echo "3. Dashboard de Gastos por Categoria"
echo "------------------------------------"
curl -X GET "$BASE_URL/api/dashboard/category-expenses/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  | python -m json.tool
echo ""
echo ""

# 4. Dashboard de Gastos por Categoria com toggle
echo "4. Dashboard de Gastos por Categoria (incluir pendentes)"
echo "--------------------------------------------------------"
curl -X GET "$BASE_URL/api/dashboard/category-expenses/?include_pending=true" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  | python -m json.tool
echo ""
echo ""

# 5. Dashboard de Fluxo de Caixa
echo "5. Dashboard de Fluxo de Caixa"
echo "------------------------------"
curl -X GET "$BASE_URL/api/dashboard/cash-flow/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  | python -m json.tool
echo ""
echo ""

# 6. Dashboard de Fluxo de Caixa com ano específico
echo "6. Dashboard de Fluxo de Caixa (ano específico)"
echo "----------------------------------------------"
curl -X GET "$BASE_URL/api/dashboard/cash-flow/?year=2024" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  | python -m json.tool
echo ""
echo ""

echo "================================"
echo "Testes Concluídos!"
echo "================================"
