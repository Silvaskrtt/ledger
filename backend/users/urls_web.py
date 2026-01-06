# backend/users/urls_web.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]