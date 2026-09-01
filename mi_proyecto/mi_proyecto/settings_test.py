"""Configuración aislada para ejecutar la suite de pruebas."""

import os


os.environ.setdefault('SECRET_KEY', 'test-key-only-not-for-production-1234567890')
os.environ.setdefault('EMAIL_HOST_USER', 'tests@example.com')
os.environ.setdefault('EMAIL_HOST_PASSWORD', 'test-password')

from .settings import *  # noqa: E402,F403


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

