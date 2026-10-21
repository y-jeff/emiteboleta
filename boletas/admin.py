from django.contrib import admin

from .models import Boleta, Item, PerfilEmisor


class ItemInline(admin.TabularInline):
    model = Item
    extra = 0


@admin.register(Boleta)
class BoletaAdmin(admin.ModelAdmin):
    list_display = ("numero", "user", "receptor_nombre", "fecha", "estado")
    list_filter = ("estado", "fecha")
    search_fields = ("receptor_nombre", "receptor_rut", "user__username")
    readonly_fields = ("numero",)
    inlines = [ItemInline]


@admin.register(PerfilEmisor)
class PerfilEmisorAdmin(admin.ModelAdmin):
    list_display = ("user", "nombre", "rut", "siguiente_numero")
    search_fields = ("nombre", "rut", "user__username")
