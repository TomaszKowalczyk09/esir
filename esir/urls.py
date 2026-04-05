from django.contrib import admin
from django.urls import path, include
from core.views import custom_404

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", include("accounts.urls")),
    path("", include("core.urls")),
]

handler404 = custom_404

# --- Static files in development (DEBUG=True) ---
from django.conf import settings  # noqa: E402
from django.conf.urls.static import static  # noqa: E402

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
