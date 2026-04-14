from django.contrib import admin
from django.urls import path, include
from core.views import custom_404

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", include("accounts.urls")),
    path("", include("core.urls")),
]

handler404 = custom_404

from django.conf import settings  
from django.conf.urls.static import static  

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
