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
    'rest_framework',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# CORREÇÃO AQUI: Caminho correto para templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # Opção 1: Se templates estão em frontend/ (fora do backend)
            BASE_DIR.parent / 'frontend' / 'templates',
            
            # Opção 2: Se você mover templates para dentro de backend
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

# Configuração para arquivos estáticos do frontend (se precisar)
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

# ADICIONE ESTAS LINHAS PARA DEBUG:
print("=" * 50)
print("DEBUG: Configurações de Template")
print(f"BASE_DIR: {BASE_DIR}")
print(f"BASE_DIR.parent: {BASE_DIR.parent}")
print(f"Template path: {BASE_DIR.parent / 'frontend' / 'templates'}")
print(f"Template exists: {(BASE_DIR.parent / 'frontend' / 'templates').exists()}")
print("=" * 50)