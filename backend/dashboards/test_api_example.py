# backend/dashboards/test_api_example.py
"""
Exemplo de como testar os endpoints de dashboards usando Python requests

Execução:
    python manage.py shell < dashboards/test_api_example.py

Ou em um script separado:
    python test_api_example.py
"""

import requests
import json
from datetime import datetime, timedelta

# Configuração
BASE_URL = "http://localhost:8000/api"
TOKEN = "seu_token_aqui"  # Token de autenticação do usuário

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}


def print_section(title):
    """Imprime um título de seção"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_card_expenses():
    """Testa o endpoint de gastos por cartão"""
    print_section("1. Dashboard de Gastos por Cartão")
    
    # Sem filtro de data
    response = requests.get(
        f"{BASE_URL}/dashboard/card-expenses/",
        headers=HEADERS
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    # Com filtro de data
    print_section("1.1 Com Filtro de Data")
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    response = requests.get(
        f"{BASE_URL}/dashboard/card-expenses/",
        params={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        headers=HEADERS
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))


def test_category_expenses():
    """Testa o endpoint de gastos por categoria"""
    print_section("2. Dashboard de Gastos por Categoria")
    
    # Sem filtro
    response = requests.get(
        f"{BASE_URL}/dashboard/category-expenses/",
        headers=HEADERS
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    # Com toggle de pendentes
    print_section("2.1 Com Toggle de Pendentes")
    
    response = requests.get(
        f"{BASE_URL}/dashboard/category-expenses/",
        params={
            "include_pending": "true"
        },
        headers=HEADERS
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))


def test_cash_flow():
    """Testa o endpoint de fluxo de caixa"""
    print_section("3. Dashboard de Fluxo de Caixa")
    
    # Ano atual (padrão)
    response = requests.get(
        f"{BASE_URL}/dashboard/cash-flow/",
        headers=HEADERS
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    # Ano específico
    print_section("3.1 Ano Específico (2024)")
    
    response = requests.get(
        f"{BASE_URL}/dashboard/cash-flow/",
        params={"year": 2024},
        headers=HEADERS
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))


def test_error_cases():
    """Testa casos de erro"""
    print_section("4. Testes de Erro")
    
    # Data inválida
    print("4.1 Data Inválida")
    response = requests.get(
        f"{BASE_URL}/dashboard/card-expenses/",
        params={
            "start_date": "invalid-date",
            "end_date": "2024-01-31"
        },
        headers=HEADERS
    )
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    # Ano inválido
    print("\n4.2 Ano Inválido")
    response = requests.get(
        f"{BASE_URL}/dashboard/cash-flow/",
        params={"year": "invalid"},
        headers=HEADERS
    )
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    # Sem autenticação
    print("\n4.3 Sem Autenticação")
    response = requests.get(
        f"{BASE_URL}/dashboard/card-expenses/"
    )
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.text}")


def main():
    """Executa todos os testes"""
    print("\n")
    print("╔" + "═"*58 + "╗")
    print("║" + " "*15 + "TESTES DE DASHBOARDS" + " "*23 + "║")
    print("╚" + "═"*58 + "╝")
    
    try:
        test_card_expenses()
        test_category_expenses()
        test_cash_flow()
        test_error_cases()
        
        print_section("✅ Testes Concluídos com Sucesso!")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Erro: Não foi possível conectar ao servidor.")
        print("   Certifique-se de que o Django está rodando em http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {str(e)}")


if __name__ == "__main__":
    main()
