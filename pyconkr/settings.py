"""
Django settings for pyconkr project.

Generated by 'django-admin startproject' using Django 1.9.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os
import datetime

from django.utils import timezone

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'b6&$e@3d_5xorj*ipg-%=bbsy#a3bryr)^45jnhhik%yjm*sqk'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition
SITE_ID = 1

INSTALLED_APPS = (
    # django apps
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.flatpages',
    'django.contrib.humanize',
) + (
    # thirt-party apps
    'django_summernote',
    'rosetta',
    'crispy_forms',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.twitter',
    'sorl.thumbnail',
    'constance',
    'constance.backends.database',
    'django_csv_exports',
) + (
    # local apps
    'pyconkr',
    'registration',
)

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

ROOT_URLCONF = 'pyconkr.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, "pyconkr/templates"),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'pyconkr.context_processors.default',
                'pyconkr.context_processors.sponsors',
                'pyconkr.context_processors.profile',
                'constance.context_processors.config',
            ],
        },
    },
]


WSGI_APPLICATION = 'pyconkr.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.9/topics/i18n/

ugettext = lambda s: s
LANGUAGES = (
    ('ko', ugettext('Korean')),
    ('en', ugettext('English')),
)
LANGUAGE_CODE = 'ko'
MODELTRANSLATION_FALLBACK_LANGUAGES = {
    'default': ('ko', 'en'),
}

TIME_ZONE = 'Asia/Seoul'

USE_I18N = True

USE_L10N = True

USE_TZ = True

FORCE_SCRIPT_NAME = ''


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

# STATICFILES_DIRS = (
#     os.path.join(BASE_DIR, "pyconkr/static"),
# )
STATIC_ROOT = os.path.join(BASE_DIR, 'collected_static')
STATIC_URL = '/static/'


# Media files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
)

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/profile/'
ACCOUNT_EMAIL_REQUIRED = True

DOMAIN = ''

EMAIL_LOGIN_TITLE = ugettext("PyCon Korea 2017 one-time login token")
EMAIL_SENDER = ugettext("PyCon Korea 2017") + "<registration@pycon.kr>"
EMAIL_USE_TLS = True
EMAIL_HOST = ''
EMAIL_PORT = 587
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''

CRISPY_TEMPLATE_PACK = 'bootstrap3'

def static_url(url):
    return os.path.join(STATIC_URL, url)

SUMMERNOTE_CONFIG = {
    'width': '100%',
    'toolbar': [
        ['style', ['style']],
        ['font', ['bold', 'italic', 'underline', 'superscript', 'subscript',
                  'strikethrough', 'clear']],
        ['fontsize', ['fontsize']],
        ['color', ['color']],
        ['para', ['ul', 'ol', 'paragraph']],
        ['height', ['height']],
        ['table', ['table']],
        ['insert', ['link', 'picture', 'video', 'hr']],
        ['view', ['fullscreen', 'codeview']],
        ['help', ['help']],
    ],
    'css': (
        static_url('css/pyconkr.css'),
        static_url('css/pyconkr-summernote.css'),
    ),
}

SPEAKER_IMAGE_MAXIMUM_FILESIZE_IN_MB = 5
SPEAKER_IMAGE_MINIMUM_DIMENSION = (500, 500)

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'

CONSTANCE_CONFIG = {
        'TOTAL_TICKET': (1800, 'How many ticket to sold'),
        'IMP_USER_CODE': ('', 'iamport user code'),
        'IMP_API_KEY': ('', 'iamport api key'),
        'IMP_API_SECRET': ('', 'iamport api secret'),
        'SHOW_SLIDE_DATA': (False, 'Show slide data on schedule table and program detail'),
}
