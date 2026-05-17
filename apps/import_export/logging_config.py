# import_export/logging_config.py
"""
Configuração de logging para o sistema de importação
"""
import logging

# Criar logger para o módulo
logger = logging.getLogger('import_export')

def setup_import_logger():
    """Configura logger para importação"""
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger

# Configuração para usar em settings.py
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'import_export_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/import_export.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'import_export': {
            'handlers': ['console', 'import_export_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'import_export.services': {
            'handlers': ['console', 'import_export_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'import_export.parsers': {
            'handlers': ['console', 'import_export_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'import_export.validators': {
            'handlers': ['console', 'import_export_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
