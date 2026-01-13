"""
Django settings for config project.
Configurações principais do backend (Django).
"""

from pathlib import Path
from dotenv import load_dotenv
import os

# Carrega variáveis de ambiente a partir do arquivo .env
load_dotenv()

# Diretório base do projeto
# Aponta para: /ledger/backend
BASE_DIR = Path(__file__).resolve().parent.parent

# =====================================================
# Configurações básicas (DESENVOLVIMENTO)
# =====================================================

# Chave secreta do Django (NUNCA usar esta em produção)
SECRET_KEY = os.getenv('SECRET_KEY')
# Se não houver, gerar nova:
if not SECRET_KEY:
    from django.core.management.utils import get_random_secret_key
    SECRET_KEY = get_random_secret_key()

# Debug ativado apenas em ambiente de desenvolvimento
DEBUG = os.getenv('DEBUG', 'True') == 'True'  # Usar variável de ambiente

# Hosts permitidos (vazio em desenvolvimento)
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# =====================================================
# Aplicações instaladas
# =====================================================

INSTALLED_APPS = [
    # Apps do domínio da aplicação
    'users',           # Usuários e autenticação
    'transactions',    # Transações financeiras
    'categories',      # Categorias de transações
    'budgets',         # Orçamentos
    'payments',        # Métodos de pagamento
    'tags',            # Tags de organização
    'recurrence',      # Transações recorrentes
    'goals',           # Metas financeiras
    'accounts',        # Contas bancárias / carteiras

    # Apps padrão do Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Necessário para o django-allauth
    
    'django.contrib.humanize',

    # Django REST Framework
    'rest_framework',

    # Autenticação (django-allauth)
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # 'allauth.socialaccount.providers.google',  # Login social (opcional)
]

# =====================================================
# Configuração do django-allauth
# =====================================================

# ID do site (obrigatório para o allauth)
SITE_ID = 1

# Métodos de autenticação permitidos
ACCOUNT_LOGIN_METHODS = {'email'}

# Campos obrigatórios no cadastro
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']

# Email deve ser único
ACCOUNT_UNIQUE_EMAIL = True

# Autenticação exclusivamente por email
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_USER_MODEL_USERNAME_FIELD = None

# Configurações de verificação de email
ACCOUNT_EMAIL_VERIFICATION = 'none'  # Em produção, usar 'mandatory'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_LOGIN_ON_SIGNUP = True  # Login automático após cadastro

# Desabilita completamente confirmação por email (ambiente local)
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 0
ACCOUNT_EMAIL_CONFIRMATION_HMAC = False
ACCOUNT_EMAIL_CONFIRMATION_COOLDOWN = 0

# URLs de redirecionamento após login/logout
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Adapter padrão do allauth
ACCOUNT_ADAPTER = 'allauth.account.adapter.DefaultAccountAdapter'

# Backends de autenticação
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# =====================================================
# Middlewares
# =====================================================

MIDDLEWARE = [
    'allauth.account.middleware.AccountMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'users.middleware.RedirectToLoginMiddleware',  # Middleware customizado
    'payments.middleware.EnsurePaymentMethodsMiddleware', # Middleware customizado
]

# Arquivo principal de rotas
ROOT_URLCONF = 'config.urls'

# =====================================================
# Templates
# =====================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # Templates centralizados no frontend
            BASE_DIR.parent / 'frontend' / 'templates',

            # Alternativa caso templates estejam dentro do backend
            # BASE_DIR / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Aplicação WSGI
WSGI_APPLICATION = 'config.wsgi.application'

# =====================================================
# Banco de Dados (PostgreSQL)
# =====================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

# =====================================================
# Validação de senhas
# =====================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# =====================================================
# Internacionalização
# =====================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# =====================================================
# Arquivos estáticos
# =====================================================

STATIC_URL = 'static/'

# Diretórios adicionais de arquivos estáticos
STATICFILES_DIRS = [
    BASE_DIR.parent / 'frontend' / 'static',
]

# =====================================================
# Django REST Framework
# =====================================================

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
}

# =====================================================
# Formulários customizados
# =====================================================

ACCOUNT_FORMS = {
    'signup': 'users.forms.CustomSignupForm',
}

# =====================================================
# Autenticação e redirecionamentos
# =====================================================

# URL para usuários não autenticados
LOGIN_URL = '/accounts/login/'

# =====================================================
# Logs do sistema
# =====================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/django.log',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'transactions': {  # Seu app
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}