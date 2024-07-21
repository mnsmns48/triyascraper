import logging.config

logger_config_dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'std_format': {
            'format':  '{asctime} {message}',
            'datefmt': "%Y-%m-%d %H:%M:%S",
            'style': '{'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'std_format'
        },
        'logfile': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'filename': 'logfile.log',
            'encoding': 'utf-8',
            'mode': 'a',
            'formatter': 'std_format'
        }
    },
    'loggers': {
        'logger': {
            'level': 'DEBUG',
            'handlers': [
                'console', 'logfile'
            ]
            # 'propagate': False
        }
    },
    'filters': {},
    'root': {}
}

logging.config.dictConfig(logger_config_dict)
logger = logging.getLogger('logger')