from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def goals_page(request):
    return render(request, "financial_goals/goals.html")
