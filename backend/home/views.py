from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from services.summary_service import SummaryService  # IMPORT

@login_required
def home_view(request):
    """
    View principal do dashboard
    """
    # Toda a lógica complexa está no SummaryService
    context = SummaryService.get_summary_data(request.user)
    
    return render(request, 'home/home.html', context)