from django.urls import path
from . import views

app_name = 'dash_calendar'

urlpatterns = [
    path('', views.calendar_page, name='calendar_page'),
]
