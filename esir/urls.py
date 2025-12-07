from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', include('accounts.urls')),
    path('', include('core.urls')),
]
