from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Goal(models.Model):
    """
    Modelo para metas financeiras do usuário
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    
    title = models.CharField('Título', max_length=200)
    description = models.TextField('Descrição', blank=True, null=True)
    target = models.DecimalField('Valor Alvo', max_digits=12, decimal_places=2)
    current = models.DecimalField('Valor Atual', max_digits=12, decimal_places=2, default=0)
    deadline = models.DateField('Data Limite')
    icon = models.CharField('Ícone', max_length=10, default='🎯')
    completed = models.BooleanField('Concluída', default=False)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Meta'
        verbose_name_plural = 'Metas'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    @property
    def progress_percentage(self):
        """Calcula o percentual de progresso da meta"""
        if self.target > 0:
            return min((self.current / self.target) * 100, 100)
        return 0
    
    @property
    def remaining_amount(self):
        """Retorna o valor que falta para atingir a meta"""
        return max(self.target - self.current, 0)
    
    @property
    def is_completable(self):
        """Verifica se a meta pode ser concluída (valor atual >= valor alvo)"""
        return self.current >= self.target and not self.completed
    
    @property
    def days_remaining(self):
        """Retorna os dias restantes para o prazo"""
        if self.deadline:
            delta = self.deadline - timezone.now().date()
            return delta.days
        return None
    
    @property
    def deadline_status(self):
        """Retorna o status do prazo: overdue, urgent ou normal"""
        days = self.days_remaining
        if days is None:
            return 'normal'
        if days < 0:
            return 'overdue'
        if days < 30:
            return 'urgent'
        return 'normal'
    
    @property
    def deadline_text(self):
        """Retorna texto formatado do prazo"""
        days = self.days_remaining
        if days is None:
            return 'Sem prazo definido'
        if days < 0:
            return f'Atrasado há {abs(days)} dias'
        if days == 0:
            return 'Vence hoje'
        if days == 1:
            return 'Vence amanhã'
        return f'{days} dias restantes'