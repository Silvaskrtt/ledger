# backend/dashboards/views_web.py

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    View para renderizar a página de dashboards
    """
    template_name = 'dashboards.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Dashboards'
        return context
