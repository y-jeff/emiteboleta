from datetime import timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw

from boletas.models import Boleta, Item, PerfilEmisor

EMAIL = "demo@example.com"
CLAVE = "demo-emiteboleta"

# (días atrás, cliente, rut, [(descripción, cantidad, precio)], pagada)
BOLETAS = [
    (40, "Café El Puerto SpA", "76.123.456-0", [("Diseño de logotipo", 1, 180000)], True),
    (33, "Panadería Doña Rosa", "", [("Diseño de carta de menú", 2, 45000)], True),
    (20, "Constructora Andes Ltda.", "77.654.321-K", [("Señalética para obra", 6, 12000), ("Instalación", 1, 35000)], False),
    (9, "Café El Puerto SpA", "76.123.456-0", [("Gestión de redes sociales (mes)", 1, 150000)], True),
    (4, "Juan Pérez", "", [("Clase particular de diseño", Decimal("1.5"), 20000)], False),
    (1, "Ferretería Los Aromos", "", [("Diseño de catálogo", 1, 220000), ("Ajustes adicionales", 2, 15000)], False),
]


def logo_demo():
    """Isotipo simple dibujado con Pillow, para no depender de archivos externos."""
    img = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((0, 0, 400, 400), fill="#0f766e")
    d.ellipse((90, 90, 310, 310), fill="#5eead4")
    d.rectangle((200, 90, 310, 200), fill="#0f766e")
    buffer = BytesIO()
    img.save(buffer, "PNG")
    return buffer.getvalue()


class Command(BaseCommand):
    help = f"Crea (o reinicia) la cuenta demo {EMAIL} con boletas de ejemplo."

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        User.objects.filter(username=EMAIL).delete()
        user = User.objects.create_user(username=EMAIL, email=EMAIL, password=CLAVE)

        perfil = PerfilEmisor.de(user)
        perfil.nombre = "Camila Rojas Fuentes"
        perfil.rut = "12.345.678-5"
        perfil.giro = "Diseño gráfico y web"
        perfil.direccion = "Av. Brasil 1234, Valparaíso"
        perfil.email = "camila@ejemplo.cl"
        perfil.telefono = "+56 9 8765 4321"
        perfil.datos_pago = "Banco Estado · Cuenta RUT\nN° 12345678"
        perfil.color = "#0f766e"
        perfil.logo, perfil.logo_mime = logo_demo(), "image/png"
        perfil.save()

        hoy = timezone.localdate()
        for dias, cliente, rut, items, pagada in BOLETAS:
            boleta = Boleta(fecha=hoy - timedelta(days=dias), receptor_nombre=cliente, receptor_rut=rut)
            boleta.emitir(perfil)
            for descripcion, cantidad, precio in items:
                Item.objects.create(boleta=boleta, descripcion=descripcion, cantidad=cantidad, precio_unitario=precio)
            if pagada:
                boleta.marcar(Boleta.PAGADA)
                boleta.save()

        self.stdout.write(self.style.SUCCESS(f"Cuenta demo lista. Email: {EMAIL} - Clave: {CLAVE}"))
