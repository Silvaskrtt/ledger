#!/usr/bin/env python
import requests
import re

# Fazer uma requisição para obter o HTML
session = requests.Session()
response = session.get('http://127.0.0.1:8000/transactions/new/')
print('Página carregada com sucesso (status:', response.status_code, ')')

# Verificar se há contas na página
if '9c72955e-b61c-4e0f-8d1c-bfe5b3be3d25' in response.text:
    print('✓ UUID da conta encontrado no HTML')
else:
    print('✗ UUID da conta NÃO encontrado no HTML')
    # Ver o que há de contas
    matches = re.findall(r'<option value="([^"]+)">', response.text)
    print('Options encontrados:')
    for match in matches[:20]:
        print(f'  - {match}')

# Procurar especificamente pelo select id_account
if 'id="id_account"' in response.text:
    print('\n✓ Select id_account encontrado')
    # Extrair o conteúdo do select
    start = response.text.find('id="id_account"')
    end = response.text.find('</select>', start)
    select_html = response.text[start:end+10]
    print('HTML do select:')
    print(select_html[:500])
