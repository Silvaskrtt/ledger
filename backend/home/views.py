# backend/home/views.py

from django.shortcuts import render

def teste_html_view(request):
    # View para renderizar o template de teste de HTML.
    return render(request, 'home/home.html', {})