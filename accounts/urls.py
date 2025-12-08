from django.urls import path
from . import views

urlpatterns = [
    path("", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path(
        "zmiana-hasla-pierwsze-logowanie/",
        views.change_password_first,
        name="change_password_first",
    ),
]
