from django.urls import path
from . import views

app_name = 'goals'

urlpatterns = [
    # Page
    path('', views.goals_page, name='goals_page'),
    
    # API endpoints
    path('api/get/', views.get_goals, name='get_goals'),
    path('api/stats/', views.get_goal_stats, name='get_goal_stats'),
    path('api/create/', views.create_goal, name='create_goal'),
    path('api/update/<int:goal_id>/', views.update_goal, name='update_goal'),
    path('api/delete/<int:goal_id>/', views.delete_goal, name='delete_goal'),
    path('api/complete/<int:goal_id>/', views.complete_goal, name='complete_goal'),
]