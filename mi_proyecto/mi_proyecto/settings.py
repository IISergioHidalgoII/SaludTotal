from pathlib import Path

from decouple import Csv, config
from django.contrib.messages import constants as message_constants

# ─────────────────────────────────────────────
#  RUTAS
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────
#  SEGURIDAD  — Cambia SECRET_KEY en producción
# ─────────────────────────────────────────────
SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DJANGO_DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config(
    'DJANGO_ALLOWED_HOSTS',
    default='localhost,127.0.0.1',
    cast=Csv(),
)

# ─────────────────────────────────────────────
#  APLICACIONES
# ─────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # -- Apps del proyecto --
    'core',
    'usuarios',
    'citas',
    'consultas',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Control de acceso por roles (ISO 27001 - A.9)
    'core.middleware.ControlAccesoMiddleware',
]

ROOT_URLCONF = 'mi_proyecto.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # ← Carpeta global de templates
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

WSGI_APPLICATION = 'mi_proyecto.wsgi.application'

# ─────────────────────────────────────────────
#  BASE DE DATOS — MySQL / XAMPP
#  Crear la BD en phpMyAdmin antes de migrar
# ─────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='mi_proyecto_db'),
        'USER': config('DB_USER', default='root'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='127.0.0.1'),
        'PORT': config('DB_PORT', default='3307'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",  # Silencia warning MariaDB
        },
    }
}

# ─────────────────────────────────────────────
#  MODELO DE USUARIO PERSONALIZADO
# ─────────────────────────────────────────────
AUTH_USER_MODEL = 'usuarios.Usuario'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─────────────────────────────────────────────
#  INTERNACIONALIZACIÓN
# ─────────────────────────────────────────────
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Guatemala'  # ← Ajusta a tu zona horaria
USE_I18N = True
USE_TZ = False

# ─────────────────────────────────────────────
#  ARCHIVOS ESTÁTICOS
# ─────────────────────────────────────────────
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─────────────────────────────────────────────
#  AUTENTICACIÓN — URLs de redirección
# ─────────────────────────────────────────────
LOGIN_URL = '/usuarios/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ─────────────────────────────────────────────
#  MENSAJES — Mapeo a clases de Bootstrap
# ─────────────────────────────────────────────
MESSAGE_TAGS = {
    message_constants.DEBUG:   'secondary',
    message_constants.INFO:    'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR:   'danger',
}

# ─────────────────────────────────────────────
#  SEGURIDAD ISO 27001 — Control de sesiones (A.9)
# ─────────────────────────────────────────────

# Expira la sesión al cerrar el navegador
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Tiempo máximo de inactividad: 30 minutos (en segundos)
SESSION_COOKIE_AGE = 60 * 30

# La cookie de sesión no es accesible por JavaScript
SESSION_COOKIE_HTTPONLY = True

# Cabecera anti-clickjacking
X_FRAME_OPTIONS = 'DENY'

# Protección contra MIME-sniffing
SECURE_CONTENT_TYPE_NOSNIFF = True

# Opciones para despliegues HTTPS. En desarrollo local permanecen desactivadas.
SECURE_SSL_REDIRECT = config('DJANGO_SECURE_SSL_REDIRECT', default=False, cast=bool)
SESSION_COOKIE_SECURE = config('DJANGO_SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = config('DJANGO_CSRF_COOKIE_SECURE', default=False, cast=bool)
SECURE_HSTS_SECONDS = config('DJANGO_SECURE_HSTS_SECONDS', default=0, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config(
    'DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS',
    default=False,
    cast=bool,
)
SECURE_HSTS_PRELOAD = config('DJANGO_SECURE_HSTS_PRELOAD', default=False, cast=bool)
CSRF_TRUSTED_ORIGINS = config(
    'DJANGO_CSRF_TRUSTED_ORIGINS',
    default='',
    cast=Csv(),
)

# Handler personalizado para fallos CSRF
CSRF_FAILURE_VIEW = 'core.views.error_csrf'

# ─────────────────────────────────────────────
#  EMAIL — Gmail SMTP (credenciales en .env)
# ─────────────────────────────────────────────
EMAIL_BACKEND   = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST      = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT      = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS   = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER     = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL  = f'Clínica Salud Total <{EMAIL_HOST_USER}>'
