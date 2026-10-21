from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .forms import LoginForm, NuevaClaveForm, RecuperarForm

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
    path(
        "recuperar/",
        auth_views.PasswordResetView.as_view(
            template_name="cuentas/recuperar.html",
            form_class=RecuperarForm,
            email_template_name="cuentas/email_recuperar.txt",
            subject_template_name="cuentas/email_recuperar_asunto.txt",
            success_url=reverse_lazy("cuentas:recuperar_enviado"),
        ),
        name="recuperar",
    ),
    path(
        "recuperar/enviado/",
        auth_views.PasswordResetDoneView.as_view(template_name="cuentas/recuperar_enviado.html"),
        name="recuperar_enviado",
    ),
    path(
        "recuperar/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="cuentas/nueva_clave.html",
            form_class=NuevaClaveForm,
            success_url=reverse_lazy("cuentas:recuperar_listo"),
        ),
        name="recuperar_confirmar",
    ),
    path(
        "recuperar/listo/",
        auth_views.PasswordResetCompleteView.as_view(template_name="cuentas/recuperar_listo.html"),
        name="recuperar_listo",
    ),
]
