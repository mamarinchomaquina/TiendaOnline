# Hello/settings.py

from pathlib import Path
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

BASE_DIR = Path(__file__).resolve().parent.parent

# ==========================================
# 🔥 SEGURIDAD - VARIABLES DE ENTORNO
# ==========================================
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-tu-secret-key-aqui')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Para Render
if 'RENDER' in os.environ:
    ALLOWED_HOSTS.append('.onrender.com')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'Home',
]

# ==========================================
# 🔥 MODELO DE USUARIO PERSONALIZADO
# ==========================================
AUTH_USER_MODEL = 'Home.Usuario'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ✅ WhiteNoise para archivos estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Hello.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'Home' / 'templates'],
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

WSGI_APPLICATION = 'Hello.wsgi.application'

# ==========================================
# 🔥 CONFIGURACIÓN SQLITE PARA AUTH (Django Admin)
# ==========================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ==========================================
# 🔥 CONFIGURACIÓN MONGODB ATLAS CON PYMONGO
# ==========================================
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://mamarin:mamarin30@cluster0.hhtibs9.mongodb.net/')
MONGODB_NAME = os.environ.get('MONGODB_NAME', 'Tienda_Online')

# Cliente de MongoDB con manejo de errores
try:
    mongo_client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000,
    )
    # Verificar conexión
    mongo_client.admin.command('ping')
    mongo_db = mongo_client[MONGODB_NAME]
    
    # Mostrar colecciones disponibles
    collections = mongo_db.list_collection_names()
    print(f"✅ Conectado a MongoDB Atlas: {MONGODB_NAME}")
    print(f"📦 Colecciones: {collections if collections else 'Base de datos vacía'}")
    
except ServerSelectionTimeoutError:
    print("❌ ERROR: No se pudo conectar a MongoDB Atlas (Timeout)")
    print("🔍 Verifica tu connection string y las reglas de IP en MongoDB Atlas")
    mongo_client = None
    mongo_db = None
    
except ConnectionFailure as e:
    print(f"❌ ERROR de conexión a MongoDB: {e}")
    mongo_client = None
    mongo_db = None
    
except Exception as e:
    print(f"❌ ERROR inesperado con MongoDB: {e}")
    mongo_client = None
    mongo_db = None

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# ==========================================
# 🔥 ARCHIVOS ESTÁTICOS (WhiteNoise)
# ==========================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'Home' / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'index'
LOGOUT_REDIRECT_URL = 'index'

# Messages
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# ==========================================
# 🔥 CONFIGURACIÓN DE SEGURIDAD (PRODUCCIÓN)
# ==========================================
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True