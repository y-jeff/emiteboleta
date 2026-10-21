from datetime import timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw

from boletas.models import Boleta, Item, PerfilEmisor, ServicioFrecuente

EMAIL = "demo@example.com"
CLAVE = "demo-emiteboleta"

# (días atrás, cliente, rut, [(descripción, cantidad, precio)], retención %, pagada)
BOLETAS = [
    (160, "3R Labs SpA", "", [("Diseño de logotipo", 1, 180000)], "15.25", True),
    (140, "Panadería Doña Rosa", "", [("Diseño de carta de menú", 2, 45000)], "0", True),
    (118, "Constructora Andes Ltda.", "77.654.321-K", [("Señalética para obra", 6, 12000), ("Instalación", 1, 35000)], "15.25", True),
    (95, "Juan Pérez", "", [("Clase particular de diseño", 4, 20000)], "0", True),
    (75, "3R Labs SpA", "", [("Gestión de redes sociales (mes)", 1, 150000)], "15.25", True),
    (52, "Ferretería Los Aromos", "", [("Fotografía de productos", 30, 4000)], "0", True),
    (40, "3R Labs SpA", "", [("Gestión de redes sociales (mes)", 1, 150000)], "15.25", True),
    (33, "Panadería Doña Rosa", "", [("Diseño de bolsas y etiquetas", 1, 95000)], "0", True),
    (20, "Constructora Andes Ltda.", "77.654.321-K", [("Diseño de folleto de proyecto", 1, 210000)], "15.25", False),
    (9, "3R Labs SpA", "", [("Gestión de redes sociales (mes)", 1, 150000)], "15.25", True),
    (4, "Juan Pérez", "", [("Clase particular de diseño", Decimal("1.5"), 20000)], "0", False),
    (1, "Ferretería Los Aromos", "", [("Diseño de catálogo", 1, 220000), ("Ajustes adicionales", 2, 15000)], "0", False),
]


def logo_demo():
    """Isotipo simple dibujado con Pillow, para no depender de archivos externos."""
    img = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((0, 0, 400, 400), fill="#2563eb")
    d.ellipse((90, 90, 310, 310), fill="#7dd3fc")
    d.rectangle((200, 90, 310, 200), fill="#2563eb")
    buffer = BytesIO()
    img.save(buffer, "PNG")
    return buffer.getvalue()


SERVICIOS = [
    ("Diseño de logotipo", 180000),
    ("Gestión de redes sociales (mes)", 150000),
    ("Mantención web (mes)", 45000),
    ("Clase particular de diseño", 20000),
]


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
        perfil.color = "#2563eb"
        perfil.logo, perfil.logo_mime = logo_demo(), "image/png"
        perfil.save()

        for descripcion, precio in SERVICIOS:
            ServicioFrecuente.objects.create(user=user, descripcion=descripcion, precio_unitario=precio)

        hoy = timezone.localdate()
        folio = 100  # las boletas antiguas ya tienen su boleta de honorarios emitida en el SII
        for dias, cliente, rut, items, retencion, pagada in BOLETAS:
            boleta = Boleta(
                fecha=hoy - timedelta(days=dias), receptor_nombre=cliente, receptor_rut=rut,
                retencion_pct=Decimal(retencion),
            )
            if dias >= 30:
                folio += 1
                boleta.folio_sii = folio
            boleta.emitir(perfil)
            for descripcion, cantidad, precio in items:
                Item.objects.create(boleta=boleta, descripcion=descripcion, cantidad=cantidad, precio_unitario=precio)
            if pagada:
                boleta.marcar(Boleta.PAGADA)
                boleta.save()

        self.stdout.write(self.style.SUCCESS(f"Cuenta demo lista. Email: {EMAIL} - Clave: {CLAVE}"))
