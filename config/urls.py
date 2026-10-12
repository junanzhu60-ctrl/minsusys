from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from listings import admin_views
from listings.media_views import cloud_media
from .views import health

urlpatterns = [
    path("health/", health, name="health"),
    path("admin/finance/", admin.site.admin_view(admin_views.finance_report), name="finance_report"),
    path("admin/finance/export/", admin.site.admin_view(admin_views.finance_export), name="finance_export"),
    path("admin/", admin.site.urls),
    path("", include("listings.urls")),
]

if settings.STORAGES["default"]["BACKEND"] == "listings.storage.DatabaseImageStorage":
    urlpatterns += [path("media/<path:name>", cloud_media, name="cloud_media")]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
