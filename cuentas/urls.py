from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm

app_name = "cuentas"

urlpatterns = [
    path("registro/", views.registro, name="registro"),
    path(
        "ingresar/",
        auth_views.LoginView.as_view(
            template_name="cuentas/login.html",
            authentication_form=LoginForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),
]
