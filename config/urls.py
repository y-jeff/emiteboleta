from django.contrib import admin
from django.urls import include, path

from boletas import views as boletas_views

urlpatterns = [
    path("", boletas_views.home, name="home"),
    path("cuenta/", include("cuentas.urls")),
    path("app/", include("boletas.urls")),
    path("admin/", admin.site.urls),
]
