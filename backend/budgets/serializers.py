# backend/budgets/serializers.py
from rest_framework import serializers
from .models import Budget, BudgetCategoryLimit
from categories.models import Category
from categories.serializers import CategorySerializer
from .services import get_or_create_current_month_budget
from datetime import date
from django.db.models import Sum
from django.utils.timezone import make_aware
from datetime import datetime,timedelta

class BudgetSerializer(serializers.ModelSerializer):
    period_start_display = serializers.SerializerMethodField()
    period_end_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Budget
        fields = [
            'budget', 'user', 'period_type', 'period_start', 
            'period_end', 'status', 'period_start_display',
            'period_end_display', 'created_at'
        ]
        read_only_fields = ['budget', 'user', 'created_at', 'updated_at']
    
    def get_period_start_display(self, obj):
        return obj.period_start.strftime('%B %Y') if obj.period_start else ''
    
    def get_period_end_display(self, obj):
        return obj.period_end.strftime('%B %Y') if obj.period_end else ''

class BudgetCategoryLimitSerializer(serializers.ModelSerializer):
    category_details = CategorySerializer(source='category', read_only=True)
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True
    )
    spent = serializers.SerializerMethodField()
    percent = serializers.SerializerMethodField()
    remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = BudgetCategoryLimit
        fields = [
            'id', 'budget', 'category', 'category_details',
            'limit_amount', 'spent', 'percent', 'remaining'
        ]
        read_only_fields = ['id', 'budget', 'spent', 'percent', 'remaining']
    
    def get_spent(self, obj):
        from transactions.models import Transaction
        from django.utils.timezone import make_aware
        
        today = date.today()
        # Calcular primeiro e último dia do mês
        first_day = today.replace(day=1)
        if today.month == 12:
            last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        
        # Criar datetimes com timezone
        start_datetime = make_aware(datetime.combine(first_day, datetime.min.time()))
        end_datetime = make_aware(datetime.combine(last_day, datetime.max.time()))
        
        # Query usando occurred_at
        spent = Transaction.objects.filter(
            user=obj.budget.user,
            category=obj.category,
            occurred_at__gte=start_datetime,
            occurred_at__lte=end_datetime,
            direction='OUT',
            is_deleted=False
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return float(spent)
    
    def get_percent(self, obj):
        spent = self.get_spent(obj)
        limit_amount = float(obj.limit_amount)
        
        if limit_amount > 0:
            return min((spent / limit_amount) * 100, 100)
        return 0
    
    def get_remaining(self, obj):
        spent = self.get_spent(obj)
        limit_amount = float(obj.limit_amount)
        return limit_amount - spent
    
    def create(self, validated_data):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is required")
        
        budget = get_or_create_current_month_budget(request.user)
        category = validated_data['category']
        
        # Verificar se já existe limite para esta categoria
        existing_limit = BudgetCategoryLimit.objects.filter(
            budget=budget,
            category=category
        ).first()
        
        if existing_limit:
            # Atualizar valor existente
            existing_limit.limit_amount = validated_data['limit_amount']
            existing_limit.save()
            return existing_limit
        
        return BudgetCategoryLimit.objects.create(
            budget=budget,
            **validated_data
        )