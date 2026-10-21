from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db import models, transaction
from django.db.models import Max
from django.urls import reverse
from django.utils import timezone

from .rut import validar_rut

COLORES = [
    ("#2563eb", "Azul EmiteBoleta"),
    ("#1e3a8a", "Azul marino"),
    ("#0f766e", "Verde azulado"),
    ("#7c2d12", "Terracota"),
    ("#4c1d95", "Violeta"),
    ("#111827", "Grafito"),
]


def redondear(valor):
    """Los pesos chilenos no tienen decimales."""
    return int(Decimal(valor).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


class PerfilEmisor(models.Model):
    """Datos de quien emite. Se rellenan una vez y se reutilizan en cada boleta."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil")
    nombre = models.CharField("Nombre o razón social", max_length=120, blank=True)
    rut = models.CharField("RUT", max_length=12, blank=True, validators=[validar_rut])
    giro = models.CharField("Actividad / oficio", max_length=120, blank=True)
    direccion = models.CharField("Dirección", max_length=200, blank=True)
    email = models.EmailField("Email de contacto", blank=True)
    telefono = models.CharField("Teléfono", max_length=30, blank=True)
    datos_pago = models.TextField(
        "Datos para transferencia",
        blank=True,
        help_text="Banco, tipo de cuenta, número. Aparecen al pie de cada boleta.",
    )
    color = models.CharField("Color del documento", max_length=7, choices=COLORES, default=COLORES[0][0])
    # El logo se guarda en la base de datos: Railway/Render tienen disco efímero.
    logo = models.BinaryField(null=True, blank=True, editable=False)
    logo_mime = models.CharField(max_length=30, blank=True)
    siguiente_numero = models.PositiveIntegerField("Próximo número de boleta", default=1)
    retencion_por_defecto = models.DecimalField(
        "Retención por defecto (%)", max_digits=5, decimal_places=2, default=Decimal("0")
    )

    class Meta:
        verbose_name = "perfil de emisor"
        verbose_name_plural = "perfiles de emisor"

    def __str__(self):
        return self.nombre or self.user.get_username()

    @property
    def completo(self):
        return bool(self.nombre and self.rut)

    @property
    def primer_nombre(self):
        return self.nombre.split()[0] if self.nombre else ""

    @property
    def tiene_logo(self):
        return bool(self.logo)

    @classmethod
    def de(cls, user):
        perfil, _ = cls.objects.get_or_create(user=user)
        return perfil


class BoletaQuerySet(models.QuerySet):
    def del_mes(self, fecha=None):
        fecha = fecha or timezone.localdate()
        return self.filter(fecha__year=fecha.year, fecha__month=fecha.month)


class Boleta(models.Model):
    PENDIENTE = "pendiente"
    PAGADA = "pagada"
    ESTADOS = [(PENDIENTE, "Pendiente"), (PAGADA, "Pagada")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="boletas")
    numero = models.PositiveIntegerField(editable=False)
    fecha = models.DateField("Fecha de emisión", default=timezone.localdate)

    # Copia de los datos del emisor al momento de emitir: si el usuario cambia
    # su perfil después, las boletas antiguas no se alteran.
    emisor_nombre = models.CharField(max_length=120, editable=False)
    emisor_rut = models.CharField(max_length=12, editable=False)
    emisor_giro = models.CharField(max_length=120, blank=True, editable=False)
    emisor_direccion = models.CharField(max_length=200, blank=True, editable=False)
    emisor_email = models.EmailField(blank=True, editable=False)
    emisor_telefono = models.CharField(max_length=30, blank=True, editable=False)
    emisor_datos_pago = models.TextField(blank=True, editable=False)

    receptor_nombre = models.CharField("Cliente", max_length=120)
    receptor_rut = models.CharField("RUT del cliente", max_length=12, blank=True, validators=[validar_rut])
    receptor_email = models.EmailField("Email del cliente", blank=True)
    receptor_direccion = models.CharField("Dirección del cliente", max_length=200, blank=True)

    notas = models.TextField("Notas", blank=True)
    retencion_pct = models.DecimalField("Retención (%)", max_digits=5, decimal_places=2, default=Decimal("0"))
    estado = models.CharField(max_length=10, choices=ESTADOS, default=PENDIENTE)
    fecha_pago = models.DateField(null=True, blank=True)

    creada = models.DateTimeField(auto_now_add=True)
    actualizada = models.DateTimeField(auto_now=True)

    objects = BoletaQuerySet.as_manager()

    class Meta:
        ordering = ["-fecha", "-numero"]
        constraints = [models.UniqueConstraint(fields=["user", "numero"], name="numero_unico_por_usuario")]

    def __str__(self):
        return f"Boleta N° {self.numero_fmt} – {self.receptor_nombre}"

    def get_absolute_url(self):
        return reverse("boletas:detalle", args=[self.pk])

    @property
    def numero_fmt(self):
        return f"{self.numero:06d}"

    @property
    def pagada(self):
        return self.estado == self.PAGADA

    @property
    def subtotal(self):
        return sum(item.total for item in self.items.all())

    @property
    def retencion_monto(self):
        return redondear(Decimal(self.subtotal) * self.retencion_pct / 100)

    @property
    def total(self):
        return self.subtotal - self.retencion_monto

    def copiar_emisor(self, perfil):
        self.emisor_nombre = perfil.nombre
        self.emisor_rut = perfil.rut
        self.emisor_giro = perfil.giro
        self.emisor_direccion = perfil.direccion
        self.emisor_email = perfil.email
        self.emisor_telefono = perfil.telefono
        self.emisor_datos_pago = perfil.datos_pago

    def marcar(self, estado):
        self.estado = estado
        self.fecha_pago = timezone.localdate() if estado == self.PAGADA else None

    @transaction.atomic
    def emitir(self, perfil):
        """Asigna el número correlativo y guarda. Debe llamarse una sola vez."""
        perfil = PerfilEmisor.objects.select_for_update().get(pk=perfil.pk)
        ultimo = Boleta.objects.filter(user=perfil.user).aggregate(m=Max("numero"))["m"] or 0
        self.numero = max(perfil.siguiente_numero, ultimo + 1)
        self.user = perfil.user
        self.copiar_emisor(perfil)
        self.save()
        perfil.siguiente_numero = self.numero + 1
        perfil.save(update_fields=["siguiente_numero"])


class Item(models.Model):
    boleta = models.ForeignKey(Boleta, on_delete=models.CASCADE, related_name="items")
    descripcion = models.CharField("Descripción", max_length=255)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1"))
    precio_unitario = models.PositiveBigIntegerField("Precio unitario")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.descripcion

    @property
    def total(self):
        return redondear(self.cantidad * self.precio_unitario)


class ServicioFrecuente(models.Model):
    """Servicio guardado para agregarlo a una boleta con un toque."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="servicios")
    descripcion = models.CharField("Descripción", max_length=255)
    precio_unitario = models.PositiveBigIntegerField("Precio unitario")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["descripcion"]
        verbose_name = "servicio frecuente"
        verbose_name_plural = "servicios frecuentes"

    def __str__(self):
        return self.descripcion
