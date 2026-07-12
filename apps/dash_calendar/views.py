from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def calendar_page(request):
    return render(request, 'calendar/calendar.html')
