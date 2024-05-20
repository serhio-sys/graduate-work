from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

BASE_URL = ""

urlpatterns = [
    path(BASE_URL + 'admin/', admin.site.urls),
    path(BASE_URL + '', include('users.urls')),
    path(BASE_URL + 'game/', include('game.urls')),
    path(BASE_URL + 'accounts/', include('allauth.urls')),
    path(BASE_URL + "__debug__/", include("debug_toolbar.urls")),
    path(BASE_URL + 'i18n/', include('django.conf.urls.i18n')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)