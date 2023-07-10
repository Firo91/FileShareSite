"""
Django settings for FileShare project.

Generated by 'django-admin startproject' using Django 4.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import os

import environ

env = environ.Env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = env.bool('DJANGO_DEBUG', default=True)

# Allowed Hosts Definition
if DEBUG:
    # If Debug is True, allow all.
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['example.com'])

SECRET_KEY = env('DJANGO_SECRET_KEY')

CSRF_TRUSTED_ORIGINS = env.list('DJANGO_CSRF_TRUSTED_ORIGINS', default=[])

MEDIA_S3_ACCESS_KEY_ID = env('MEDIA_S3_ACCESS_KEY_ID', default=None)
MEDIA_S3_SECRET_ACCESS_KEY = env('MEDIA_S3_SECRET_ACCESS_KEY', default=None)
MEDIA_S3_BUCKET_NAME = env('MEDIA_S3_BUCKET_NAME', default=None)

STATIC_S3_ACCESS_KEY_ID = env('STATIC_S3_ACCESS_KEY_ID', default=None)
STATIC_S3_SECRET_ACCESS_KEY = env('STATIC_S3_SECRET_ACCESS_KEY', default=None)
STATIC_S3_BUCKET_NAME = env('STATIC_S3_BUCKET_NAME', default=None)

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'UpDownShare',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTH_USER_MODEL = 'UpDownShare.CustomUser'

ROOT_URLCONF = 'FileShare.urls'

CSRF_TRUSTED_ORIGINS = [
    'https://ccterminals.applikuapp.com/', 'http://ccterminals.applikuapp.com/'
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'UpDownShare' / 'templates' / 'UpDownShare'],
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

WSGI_APPLICATION = 'FileShare.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Databases
DATABASES = {
    "default": env.db("DATABASE_URL")
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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

SESSION_COOKIE_AGE = 900  # 30 minutes in seconds
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

MEDIA_ROOT = 'media'
MEDIA_URL = f'https://{MEDIA_S3_BUCKET_NAME}.s3.amazonaws.com/'
MEDIA_HOST = f'{MEDIA_S3_BUCKET_NAME}.s3.amazonaws.com'
CUSTOM_MEDIA_DOMAIN = env('CUSTOM_MEDIA_DOMAIN', default=None)

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

if CUSTOM_MEDIA_DOMAIN:
    MEDIA_HOST = CUSTOM_MEDIA_DOMAIN

MEDIA_URL = f'https://{MEDIA_HOST}/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
STORAGES = {
    "default": {
        "BACKEND": 'FileShare.storages.PrivateMediaStorage',
    },
    "staticfiles": {
        "BACKEND": 'FileShare.storages.StaticStorage',
    }
}

WHITENOISE_USE_FINDERS = True
