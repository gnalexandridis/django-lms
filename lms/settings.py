import os
from pathlib import Path

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(str, "dev-insecure"),
    ALLOWED_HOSTS=(list, []),
    E2E_TEST_LOGIN=(bool, False),
    KEYCLOAK_BASE_URL=(str, ""),
    KEYCLOAK_REALM=(str, ""),
    OIDC_RP_CLIENT_ID=(str, ""),
    OIDC_RP_CLIENT_SECRET=(str, ""),
    KEYCLOAK_ADMIN_CLIENT_ID=(str, ""),
    KEYCLOAK_ADMIN_CLIENT_SECRET=(str, ""),
)
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

DEBUG = env("DEBUG")
SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
E2E_TEST_LOGIN = env("E2E_TEST_LOGIN")
KEYCLOAK_BASE_URL = env("KEYCLOAK_BASE_URL")
KEYCLOAK_REALM = env("KEYCLOAK_REALM")
OIDC_RP_CLIENT_ID = env("OIDC_RP_CLIENT_ID")
OIDC_RP_CLIENT_SECRET = env("OIDC_RP_CLIENT_SECRET")
KEYCLOAK_ADMIN_CLIENT_ID = env("KEYCLOAK_ADMIN_CLIENT_ID")
KEYCLOAK_ADMIN_CLIENT_SECRET = env("KEYCLOAK_ADMIN_CLIENT_SECRET")
OIDC_RP_SIGN_ALGO = env("OIDC_RP_SIGN_ALGO")

# Explicit endpoints for mozilla-django-oidc (Keycloak)
_KC_OIDC_BASE = f"{KEYCLOAK_BASE_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect"
OIDC_OP_AUTHORIZATION_ENDPOINT = f"{_KC_OIDC_BASE}/auth"
OIDC_OP_TOKEN_ENDPOINT = f"{_KC_OIDC_BASE}/token"
OIDC_OP_USER_ENDPOINT = f"{_KC_OIDC_BASE}/userinfo"
OIDC_OP_JWKS_ENDPOINT = f"{_KC_OIDC_BASE}/certs"
OIDC_OP_LOGOUT_ENDPOINT = f"{_KC_OIDC_BASE}/logout"
OIDC_OP_LOGOUT_URL_METHOD = "lms_users.views.provider_logout"
OIDC_STORE_ID_TOKEN = False
OIDC_STORE_ACCESS_TOKEN = False
OIDC_VERIFY_SSL = False  # dev only

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "mozilla_django_oidc",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # project apps
    "lms",
    "lms_users",
    "lms_courses",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "lms_users.auth_backends.KeycloakOIDCBackend",
    "django.contrib.auth.backends.ModelBackend",
]

ROOT_URLCONF = "lms.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "lms_users.context_processors.roles",
            ],
        },
    },
]

WSGI_APPLICATION = "lms.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",  # αλλάζει σε Postgres αργότερα
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "el-gr"
TIME_ZONE = "Europe/Athens"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "lms_users.User"
LOGIN_URL = "/users/test-login/" if E2E_TEST_LOGIN else "/users/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
