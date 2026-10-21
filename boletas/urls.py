from django.urls import path

from . import views

app_name = "boletas"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("boletas/", views.lista, name="lista"),
    path("resumen/", views.resumen, name="resumen"),
    path("resumen/exportar/", views.exportar, name="exportar"),
    path("boletas/nueva/", views.crear, name="crear"),
    path("boletas/<int:pk>/", views.detalle, name="detalle"),
    path("boletas/<int:pk>/editar/", views.editar, name="editar"),
    path("boletas/<int:pk>/pdf/", views.pdf, name="pdf"),
    path("boletas/<int:pk>/estado/", views.cambiar_estado, name="estado"),
    path("boletas/<int:pk>/sii/", views.registrar_sii, name="registrar_sii"),
    path("boletas/<int:pk>/duplicar/", views.duplicar, name="duplicar"),
    path("boletas/<int:pk>/eliminar/", views.eliminar, name="eliminar"),
    path("catalogo/", views.catalogo, name="catalogo"),
    path("catalogo/<int:pk>/eliminar/", views.catalogo_eliminar, name="catalogo_eliminar"),
    path("perfil/", views.perfil, name="perfil"),
    path("perfil/logo/", views.logo, name="logo"),
]
