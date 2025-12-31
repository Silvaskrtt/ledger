"""
Django settings for config project.
"""

from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent  # Isso aponta para: /caminho/ledger/backend

# Quick-start development settings - unsuitable for production
SECRET_KEY = 'django-insecure-c#!9a6+!yxdl^n4)du%qjeheh$g7nw3w8pi8n@#(&iukp)2x4x'
DEBUG = True
ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'config',
    # Apps customizados
    'users',
    'transactions',
    'categories',
    'budgets',
    'payments',
    'tags',
    'recurrence',
    'goals',
    'accounts',
    
    # Apps do Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'rest_framework',
    
    # Allauth apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # 'allauth.socialaccount.providers.google',  # Para login social
]

# Allauth 
SITE_ID = 1

# MÃ©todos de autenticaÃ§Ã£o
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_AUTHENTICATION_METHOD = 'email' # Login com email
# ACCOUNT_USERNAME_REQUIRED = False  # Substituído por ACCOUNT_SIGNUP_FIELDS
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_VERIFICATION = 'none'  # 'mandatory' para produção
ACCOUNT_EMAIL_REQUIRED = True   # Email é obrigatório, mas não verifica
ACCOUNT_LOGIN_ON_SIGNUP = True       # Faz login automaticamente após cadastro

# Desabilita confirmações por email
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 0
ACCOUNT_EMAIL_CONFIRMATION_HMAC = False
ACCOUNT_EMAIL_CONFIRMATION_COOLDOWN = 0

# Redirecionamentos
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Permite cadastro com qualquer email
ACCOUNT_ADAPTER = 'allauth.account.adapter.DefaultAccountAdapter'

# Backends de autenticação
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

MIDDLEWARE = [
    'allauth.account.middleware.AccountMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# CORREÃ‡ÃƒO AQUI: Caminho correto para templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # OpÃ§Ã£o 1: Se templates estÃ£o em frontend/ (fora do backend)
            BASE_DIR.parent / 'frontend' / 'templates',
            
            # OpÃ§Ã£o 2: Se vocÃª mover templates para dentro de backend
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

WSGI_APPLICATION = 'config.wsgi.application'

# Database
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

# Password validation
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

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR.parent / 'frontend' / 'static',  # Se tiver static no frontend
]

# Django REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
}

ACCOUNT_FORMS = {
    'signup': 'users.forms.CustomSignupForm',
}