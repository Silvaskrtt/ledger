# 📋 ANÁLISE DE INCOERÊNCIAS E INCONSISTÊNCIAS - SISTEMA LEDGER

## 🔴 CRÍTICAS (Devem ser corrigidas urgentemente)

### 1. **Arquitetura Dupla e Conflitante de Transações**
**Localização:** `transactions/models.py`

**Problema:**
O modelo `Transaction` usa tanto `account_from` e `account_to` quanto `TransactionAccount` para representar contas envolvidas:

```python
# Modelo Transaction (direto)
account_from = models.ForeignKey(Account, related_name='transactions_from')
account_to = models.ForeignKey(Account, related_name='transactions_to')

# Modelo TransactionAccount (muitos-para-muitos)
class TransactionAccount(models.Model):
    role = models.CharField(choices=[('source', 'Source'), ('destination', 'Destination')])
```

**Impacto:**
- Redundância de dados
- Risco de sincronização entre os dois modos
- Não está claro qual é a "fonte da verdade"
- Aumenta complexidade desnecessariamente

**Recomendação:**
Escolher uma arquitetura e descartar a outra:
- **Opção A:** Manter apenas `account_from` e `account_to` (mais simples)
- **Opção B:** Manter apenas `TransactionAccount` (mais flexível para múltiplas contas)

---

### 2. **Inconsistência no Cálculo de Saldo de Cartão de Crédito**
**Localização:** `accounts/models.py` e `transactions/services/balance_service.py`

**Problema:**
Há conflito na lógica do saldo do cartão de crédito:

```python
# Em Account.available_credit:
current_debt = abs(self.balance)  # Assume balance NEGATIVO
available = self.credit_limit - current_debt

# Mas em balance_service.py:
calculated_balance = totals_out - totals_in  # POSITIVO para dívida
```

**Cenário de Erro:**
- Limite: R$ 5.000
- Compras (OUT): R$ 2.000
- `available_credit` usa `abs(balance)` → assume que balance é -2000
- Mas se balance for armazenado como +2000 → `available = 5000 - 2000 = 3000` ✓
- Se balance for -2000 → `available = 5000 - 2000 = 3000` ✓

Apesar de funcionar, **a semântica é confusa**:
- Uma função assume balance NEGATIVO para cartão
- A outra calcula como POSITIVO
- Não está documentado qual é o padrão esperado

**Recomendação:**
Definir claramente:
- **Padrão 1:** Cartões sempre com saldo NEGATIVO (indicando dívida)
- **Padrão 2:** Cartões sempre com saldo POSITIVO (indicando dívida)
- Documentar em todo o código
- Ajustar `available_credit` e `balance_service` para serem consistentes

---

### 3. **Constraint de Taxa de Juros Faltante no InstallmentPlan**
**Localização:** `payments/models.py`

**Problema:**
```python
class InstallmentPlan(models.Model):
    total_amount = models.DecimalField(...)
    installments = models.IntegerField()
    # FALTANDO: interest_rate não está em InstallmentPlan!
```

Mas em `TransactionCreateSerializer`:
```python
interest_rate = serializers.DecimalField(...)  # Aceita juros na criação
```

E em `transaction_service.py`:
```python
def create_transaction_service(..., interest_rate: Decimal = Decimal('0'), ...)
```

**Impacto:**
- Juros aceitos na API mas não armazenados no modelo
- Não há como recuperar a taxa de juros depois
- Cálculo de juros pode estar perdido

**Recomendação:**
Adicionar ao modelo:
```python
class InstallmentPlan(models.Model):
    interest_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[validate_percentage]
    )
```

---

### 4. **Falta de Relacionamento entre Transaction e Tags**
**Localização:** `transactions/models.py` - `TransactionTag`

**Problema:**
O modelo `TransactionTag` existe:
```python
class TransactionTag(models.Model):
    id_transaction = ForeignKey(Transaction)
    id_tag = ForeignKey(Tag)
```

Mas em `Transaction.models.py` **não há many-to-many field**:
```python
class Transaction(models.Model):
    # FALTANDO: tags = ManyToManyField(Tag, through='TransactionTag')
```

**Impacto:**
- Não é possível acessar `transaction.tags.all()` facilmente
- ORM não reconhece a relação
- Difícil filtrar por tags

**Recomendação:**
Adicionar ao modelo Transaction:
```python
tags = models.ManyToManyField(
    Tag,
    through='TransactionTag',
    related_name='transactions'
)
```

---

## 🟠 IMPORTANTES (Devem ser revisadas)

### 5. **Inconsistência de Nomenclatura de Campos de Foreign Key**
**Localização:** Vários modelos

**Problema:**
Alguns ForeignKeys usam padrão `id_*` enquanto Django gera `*_id` automaticamente:

```python
# Inconsistente:
id_user = models.ForeignKey(User, ...)  # Campo: id_user
id_category = models.ForeignKey(Category, ...)  # Campo: id_category
id_account = models.ForeignKey(Account, ...)  # Campo: id_account

# Versus:
user = models.ForeignKey(User, ...)  # Campo: user_id (Django padrão)
```

**Impacto:**
- Código fica verboso e não segue convenção Django
- Em queries, precisa usar `id_user=X` em vez de `user_id=X`
- Confunde novos desenvolvedores
- Inconsistência quando alguns modelos usam padrão (ex: `Account.user`)

**Exemplos de inconsistência:**
- `Transaction.id_user` vs `Account.user` ❌
- `Category.id_user` vs `Account.user` ❌
- `Budget.id_user` vs `Account.user` ❌

**Recomendação:**
Padronizar toda a codebase para usar nomes simples sem `id_`:
```python
user = models.ForeignKey(User, ...)
category = models.ForeignKey(Category, ...)
account = models.ForeignKey(Account, ...)
```

---

### 6. **Soft Delete Incompleto**
**Localização:** `transactions/models.py`

**Problema:**
```python
class Transaction(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    objects = NotDeletedManager()  # Filtra automaticamente
    
    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
```

**Impactos:**
1. **Sem hard delete:** Se chamar `transaction.delete()` diretamente, é soft delete. Mas `Transaction.objects.all().delete()` pode não funcionar corretamente.
2. **Manager customizado:** O `NotDeletedManager()` como default é bom, mas:
   - `Transaction.objects.all()` só retorna não deletadas
   - Para ver deletadas, precisa de queryset especial
   - Pode causar surpresas em relatórios/analytics
3. **Cascata:** Se deletar uma `Category`, as transações são deletadas hard (CASCADE)

**Recomendação:**
1. Override do `delete()` precisa desabilitar hard delete
2. Criar um manager alternativo para ter acesso a deletadas:
```python
all_objects = models.Manager()  # Todas as transações
objects = NotDeletedManager()   # Apenas ativas
```

---

### 7. **Falta de Constraints de Integridade em CreditCardBill**
**Localização:** `accounts/models.py`

**Problema:**
```python
class CreditCardBill(models.Model):
    status = models.CharField(choices=STATUS_CHOICES, default='OPEN')
    paid_amount = models.DecimalField(...)
    total_amount = models.DecimalField(...)
    minimum_payment = models.DecimalField(...)
```

**Faltam validações:**
- `paid_amount` não pode ser > `total_amount`
- `minimum_payment` não pode ser > `total_amount`
- Transição de status precisa ter regras (OPEN → CLOSED → PAID)
- Não pode receber pagamento se já está PAID

**Recomendação:**
Adicionar constraints:
```python
constraints = [
    CheckConstraint(condition=Q(paid_amount__lte=F('total_amount')), name='paid_lte_total'),
    CheckConstraint(condition=Q(minimum_payment__lte=F('total_amount')), name='min_payment_valid'),
    CheckConstraint(condition=Q(paid_amount__gte=0), name='paid_amount_positive'),
]
```

---

### 8. **Falta de Filtro por User em Muitos Endpoints**
**Localização:** Vários `views.py` e `serializers.py`

**Problema:**
```python
# Seguro - filtra por usuário:
class TagListCreateView(generics.ListCreateAPIView):
    def get_queryset(self):
        return Tag.objects.filter(id_user=self.request.user)

# Mas em algumas views, pode não estar filtrando:
class TransactionListCreateView(generics.ListCreateAPIView):
    def get_queryset(self):
        return Transaction.objects.filter(id_user=self.request.user)  # ✓ OK
```

**Risco de segurança:**
- Um usuário poderia potencialmente ver transações de outro usuário se não filtrado
- Especialmente crítico para dados financeiros

**Recomendação:**
Revisar todas as views para garantir filtro por `self.request.user`

---

### 9. **RecurrenceRule sem Ligação com Transactions Criadas**
**Localização:** `recurrence/models.py`

**Problema:**
```python
class RecurrenceRule(models.Model):
    frequency = models.CharField(...)
    next_execution = models.DateField()
    executions_count = models.IntegerField(default=0)
```

**Faltam:**
1. Referência para as transações criadas por essa regra
2. Status da regra (ativa, pausada, completada)
3. Como saber quais transações vieram de uma regra específica

**Impacto:**
- Impossível editaruma regra e aplicar retroativamente às transações
- Sem histórico de execução
- Sem como pausar uma regra específica

**Recomendação:**
Adicionar campos:
```python
class RecurrenceRule(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Ativa'),
        ('PAUSED', 'Pausada'),
        ('COMPLETED', 'Completada'),
        ('CANCELLED', 'Cancelada'),
    ]
    
    status = models.CharField(..., default='ACTIVE')
    last_execution = models.DateField(null=True)
    
    # Vincular transações criadas
    created_transactions = ManyToManyField(Transaction, related_name='recurrence_rules')
```

---

### 10. **Budget não tem Status ou Data de Fim**
**Localização:** `budgets/models.py`

**Problema:**
```python
class Budget(models.Model):
    period_start = models.DateField()
    # FALTANDO: period_end
    # FALTANDO: status (ativo, expirado, etc)
```

**Impacto:**
- Impossível saber quando um orçamento termina
- Sem como determinar se um orçamento ainda está válido
- Sem status de conclusão/atingimento

**Recomendação:**
```python
class Budget(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Ativo'),
        ('COMPLETED', 'Completado'),
        ('EXCEEDED', 'Excedido'),
        ('CANCELLED', 'Cancelado'),
    ]
    
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(..., default='ACTIVE')
```

---

## 🟡 AVISOS (Boas práticas)

### 11. **Imports Duplicados**
**Localização:** `transactions/services/balance_service.py`

```python
from django.db.models import Sum, Q
# ... depois
from django.db.models import Sum  # Duplicado!
```

**Recomendação:**
Remover import duplicado

---

### 12. **Logger não Configurado Corretamente**
**Localização:** `transactions/services/balance_service.py`

```python
from asyncio.log import logger  # ❌ Errado! asyncio.log é interno
logger = logging.getLogger(__name__)  # ✓ Correto

# Mas depois usa:
logger.warning(...)  # Pode não funcionar
```

**Recomendação:**
```python
import logging
logger = logging.getLogger(__name__)
```

---

### 13. **Falta de Cascata Clara em Relacionamentos**
**Localização:** Vários modelos

**Problema:**
```python
# Em Category:
id_parent_category = models.ForeignKey('self', on_delete=models.SET_NULL)
# ✓ Bom - subcategorias órfãs

# Em Transaction:
id_category = models.ForeignKey(Category, on_delete=models.CASCADE)
# ⚠️ Se deletar categoria, deleta todas transações! Talvez usar SET_NULL?

id_payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)
# ⚠️ Mesma situação
```

**Recomendação:**
Decidir: Ao deletar Category/PaymentMethod:
- **CASCADE:** Deleta todas transações relacionadas (perigoso)
- **SET_NULL:** Deixa transações órfãs (melhor para dados históricos)
- **PROTECT:** Impede deletar se houver transações (mais seguro)

---

### 14. **InstallmentPlan com Limite de 10.000 Arbitrário**
**Localização:** `payments/models.py`

```python
constraints = [
    CheckConstraint(condition=Q(total_amount__lt=10000), name='total_amount_max_limit'),
]
```

**Problema:**
- Por que 10.000? Não há justificativa
- Pode ser insuficiente para usuários reais
- Deveria ser configurável por usuário/plano

**Recomendação:**
- Remover constraint hardcoded
- Usar variável de configuração (settings.py)
- Ou validar no serializer com mensagem clara

---

### 15. **Falta de Índices em Queries Frequentes**
**Localização:** Vários modelos

**Problema:**
```python
# Transaction busca frequentemente:
Transaction.objects.filter(id_user=user, occurred_at__gte=date)
# Sem índice composto!

# Goals busca:
FinancialGoal.objects.filter(id_user=user, deadline__gte=today)
# Sem índice composto!
```

**Recomendação:**
Adicionar índices:
```python
class Meta:
    indexes = [
        models.Index(fields=['id_user', 'occurred_at']),
        models.Index(fields=['id_user', 'direction']),
        models.Index(fields=['id_user', '-created_at']),
    ]
```

---

### 16. **Falta de Validação em Transações Entre Contas**
**Localização:** `transaction_service.py`

**Problema:**
Não há validação se `account_from` e `account_to` pertencem ao mesmo usuário:
```python
def create_transaction_service(...):
    # Se account_from é de User1 e account_to é de User2 = ERRO
    # Mas a validação não existe!
```

**Recomendação:**
Adicionar validação:
```python
if account_from.user != account_to.user:
    raise ValidationError("Ambas as contas devem pertencer ao mesmo usuário")
```

---

### 17. **Tags Não Vinculadas a User**
**Localização:** `tags/models.py` - OK, mas duplicado

Tags têm `id_user`, assim como transações têm `id_tag`. Mas em serializers de transaction:
```python
# Não há filtro de tags por usuário no serializer
tags = serializers.ListField(child=serializers.UUIDField(), ...)
```

Potencial risco: Um usuário poderia adicionar tags de outro usuário a suas transações.

**Recomendação:**
Adicionar validação em `TransactionCreateSerializer`:
```python
def validate_tags(self, value):
    user = self.context['request'].user
    for tag_id in value:
        if not Tag.objects.filter(id_tag=tag_id, id_user=user).exists():
            raise serializers.ValidationError(f"Tag {tag_id} não existe para este usuário")
    return value
```

---

### 18. **Falta de Permissões em Algumas Views**
**Localização:** `transactions/views.py`

```python
class ProcessRecurrencesView(generics.GenericAPIView):
    permission_classes = []  # ⚠️ SEM PERMISSÃO!
    
    def post(self, request):
        # Qualquer pessoa pode processar recorrências?
```

**Recomendação:**
```python
permission_classes = [IsAuthenticated]
```

---

## 📊 RESUMO POR SEVERIDADE

| Nível | Quantidade | Exemplos |
|-------|-----------|----------|
| 🔴 **CRÍTICA** | 4 | Dupla arquitetura de contas, inconsistência cartão, constraint faltante, tags não vinculadas |
| 🟠 **IMPORTANTE** | 6 | Nomenclatura, soft delete, CreditCardBill, filtro de user, recurrence rule, budget |
| 🟡 **AVISO** | 8 | Imports, logger, cascata, limites, índices, validações, permissões |

---

## ✅ PRÓXIMOS PASSOS RECOMENDADOS

1. **Fase 1 (Semana 1):**
   - [ ] Resolver duplicidade de Transaction/TransactionAccount
   - [ ] Padronizar cálculo de saldo de cartão
   - [ ] Adicionar interesse_rate a InstallmentPlan
   - [ ] Vincular Tags a Transactions no modelo

2. **Fase 2 (Semana 2):**
   - [ ] Standardizar nomenclatura FK (id_* vs *)
   - [ ] Melhorar soft delete
   - [ ] Adicionar constraints em CreditCardBill
   - [ ] Filtro de user em todos endpoints

3. **Fase 3 (Semana 3):**
   - [ ] Melhorar RecurrenceRule
   - [ ] Melhorar Budget model
   - [ ] Adicionar índices
   - [ ] Remover imports duplicados e corrigir logger

4. **Fase 4 (Contínuo):**
   - [ ] Testes unitários
   - [ ] Testes de integração
   - [ ] Code review
   - [ ] Documentação

