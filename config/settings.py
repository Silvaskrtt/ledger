import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Define o diretório base do projeto (dois níveis acima deste arquivo)
BASE_DIR = Path(__file__).resolve().parent.parent

# Adiciona o diretório 'apps' ao PATH do Python para permitir importações dos apps customizados
sys.path.insert(0, str(BASE_DIR / 'apps'))

# ============================================================================
# CONFIGURAÇÕES PRINCIPAIS DO DJANGO
# ============================================================================

# Chave secreta da aplicação (obtida das variáveis de ambiente)
SECRET_KEY = os.getenv("SECRET_KEY")

# Modo de depuração (True apenas em desenvolvimento)
DEBUG = True

# Hosts permitidos para acessar a aplicação (vazio em desenvolvimento)
ALLOWED_HOSTS = []

# ============================================================================
# APPS INSTALADOS
# ============================================================================

INSTALLED_APPS = [
    # Apps nativos do Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    
    # django-allauth - Autenticação social e gerenciamento de contas
    'django.contrib.sites',  # Framework de sites do Django (requerido pelo allauth)
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    
    # Apps customizados do projeto (adicionar abaixo)
    'accounts',
    'categories.apps.CategoriesConfig',
]

# ============================================================================
# MIDDLEWARES
# ============================================================================

MIDDLEWARE = [
    # Middlewares nativos do Django
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Middleware do django-allauth (gerencia autenticação e contas)
    'allauth.account.middleware.AccountMiddleware',
]

# Configuração das URLs raiz do projeto
ROOT_URLCONF = 'config.urls'

# ============================================================================
# TEMPLATES (VIEWS)
# ============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',  # Diretório global de templates do projeto
        ],
        'APP_DIRS': True,  # Habilita busca de templates dentro de cada app
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',  # Adiciona request ao contexto
                'django.contrib.auth.context_processors.auth',  # Adiciona user ao contexto
                'django.contrib.messages.context_processors.messages',  # Adiciona messages ao contexto
            ],
        },
    },
]

# Configuração WSGI para servidores de produção
WSGI_APPLICATION = 'config.wsgi.application'

# ============================================================================
# BANCO DE DADOS
# ============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',  # SGBD: PostgreSQL
        'NAME': os.getenv('DB_NAME'),               # Nome do banco de dados
        'USER': os.getenv('DB_USER'),               # Usuário do banco
        'PASSWORD': os.getenv('DB_PASSWORD'),       # Senha do banco
        'HOST': os.getenv('DB_HOST'),               # Host do banco de dados
        'PORT': os.getenv('DB_PORT'),               # Porta do banco
        'OPTIONS': {
            'client_encoding': 'UTF8',              # Codificação UTF-8 para compatibilidade com caracteres acentuados
        },
    }
}

# ============================================================================
# VALIDAÇÃO DE SENHAS
# ============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',  # Impede senha similar aos atributos do usuário
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',  # Exige comprimento mínimo de senha
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',  # Bloqueia senhas comuns
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',  # Impede senha composta apenas por números
    },
]

# ============================================================================
# INTERNACIONALIZAÇÃO E LOCALIZAÇÃO
# ============================================================================

# Idioma padrão: Português Brasileiro
LANGUAGE_CODE = 'pt-br'

# Fuso horário padrão
TIME_ZONE = 'America/Sao_Paulo'

# Habilita sistema de internacionalização
USE_I18N = True

# Habilita suporte a timezone
USE_TZ = True

# ============================================================================
# ARQUIVOS ESTÁTICOS (CSS, JavaScript, Imagens)
# ============================================================================
SITE_ID = 1

LANGUAGE_CODE = 'pt-br'
USE_L10N = True

ACCOUNT_FORMS = {
    'add_email': 'allauth.account.forms.AddEmailForm',
    'change_password': 'allauth.account.forms.ChangePasswordForm',
    'confirm_login_code': 'allauth.account.forms.ConfirmLoginCodeForm',
    'login': 'allauth.account.forms.LoginForm',
    'request_login_code': 'allauth.account.forms.RequestLoginCodeForm',
    'reset_password': 'allauth.account.forms.ResetPasswordForm',
    'reset_password_from_key': 'allauth.account.forms.ResetPasswordKeyForm',
    'set_password': 'allauth.account.forms.SetPasswordForm',
    'signup': 'allauth.account.forms.SignupForm',
    'user_token': 'allauth.account.forms.UserTokenForm',
}

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

LOGIN_REDIRECT_URL = '/'
ACCOUNT_SIGNUP_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]
ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_LOGOUT_ON_GET = True

# URL base para acesso aos arquivos estáticos
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

APPEND_SLASH = True