from io import BytesIO

from django import forms
from django.forms import inlineformset_factory
from PIL import Image, UnidentifiedImageError

from . import rut
from .models import Boleta, Item, PerfilEmisor, ServicioFrecuente

INPUT = (
    "block w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-base "
    "text-slate-900 shadow-sm focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20"
)
LOGO_MAX_BYTES = 1024 * 1024
LOGO_FORMATOS = {"PNG": "image/png", "JPEG": "image/jpeg"}


class EstiloMixin:
    """Aplica las clases de Tailwind a todos los widgets del formulario."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.RadioSelect, forms.FileInput)):
                continue
            widget.attrs.setdefault("class", INPUT)


class RutField(forms.CharField):
    def clean(self, value):
        value = super().clean(value)
        return rut.formatear(value) if value else value


class PerfilForm(EstiloMixin, forms.ModelForm):
    rut = RutField(label="RUT", max_length=12, required=True)
    logo_archivo = forms.FileField(
        label="Logo (PNG o JPG, máx. 1 MB)",
        required=False,
        widget=forms.ClearableFileInput(attrs={"accept": "image/png,image/jpeg"}),
    )
    quitar_logo = forms.BooleanField(label="Quitar logo actual", required=False)

    class Meta:
        model = PerfilEmisor
        fields = [
            "nombre", "rut", "giro", "direccion", "email", "telefono",
            "datos_pago", "color", "siguiente_numero", "retencion_por_defecto",
        ]
        widgets = {
            "datos_pago": forms.Textarea(attrs={"rows": 3, "placeholder": "Banco Estado · Cuenta RUT · 12345678"}),
            "color": forms.RadioSelect,
            "telefono": forms.TextInput(attrs={"inputmode": "tel", "placeholder": "+56 9 1234 5678"}),
            "retencion_por_defecto": forms.NumberInput(attrs={"step": "0.01", "inputmode": "decimal"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nombre"].required = True
        self.fields["rut"].widget.attrs.update(placeholder="12.345.678-5", autocomplete="off")
        self.fields["siguiente_numero"].help_text = (
            "Si ya emitías boletas antes, parte desde tu siguiente número."
        )

    def clean_rut(self):
        valor = self.cleaned_data["rut"]
        rut.validar_rut(valor)
        return valor

    def clean_logo_archivo(self):
        archivo = self.cleaned_data.get("logo_archivo")
        if not archivo:
            return None
        if archivo.size > LOGO_MAX_BYTES:
            raise forms.ValidationError("El logo no puede pesar más de 1 MB.")
        data = archivo.read()
        try:
            with Image.open(BytesIO(data)) as img:
                img.verify()
                formato = img.format
        except (UnidentifiedImageError, OSError):
            raise forms.ValidationError("El archivo no es una imagen válida.")
        if formato not in LOGO_FORMATOS:
            raise forms.ValidationError("Usa un logo en formato PNG o JPG.")
        return data, LOGO_FORMATOS[formato]

    def save(self, commit=True):
        perfil = super().save(commit=False)
        if self.cleaned_data.get("quitar_logo"):
            perfil.logo, perfil.logo_mime = None, ""
        elif self.cleaned_data.get("logo_archivo"):
            perfil.logo, perfil.logo_mime = self.cleaned_data["logo_archivo"]
        if commit:
            perfil.save()
        return perfil


class BoletaForm(EstiloMixin, forms.ModelForm):
    receptor_rut = RutField(label="RUT del cliente", max_length=12, required=False)

    class Meta:
        model = Boleta
        fields = [
            "receptor_nombre", "receptor_rut", "receptor_email", "receptor_direccion",
            "fecha", "retencion_pct", "estado", "folio_sii", "notas",
        ]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "notas": forms.Textarea(attrs={"rows": 2, "placeholder": "Ej: Pago a 30 días. ¡Gracias por tu confianza!"}),
            "retencion_pct": forms.NumberInput(attrs={"step": "0.01", "min": "0", "max": "100", "inputmode": "decimal"}),
            "folio_sii": forms.NumberInput(attrs={"min": "1", "inputmode": "numeric", "placeholder": "Opcional"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["receptor_rut"].widget.attrs.update(placeholder="Opcional", autocomplete="off")
        self.fields["receptor_email"].widget.attrs.update(placeholder="Opcional", inputmode="email")
        self.fields["receptor_direccion"].widget.attrs.update(placeholder="Opcional")

    def clean_receptor_rut(self):
        valor = self.cleaned_data["receptor_rut"]
        rut.validar_rut(valor)
        return valor

    def clean_retencion_pct(self):
        valor = self.cleaned_data["retencion_pct"]
        if valor is None or not 0 <= valor <= 100:
            raise forms.ValidationError("Debe estar entre 0 y 100.")
        return valor


class FolioSiiForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = Boleta
        fields = ["folio_sii"]
        widgets = {"folio_sii": forms.NumberInput(attrs={"min": "1", "inputmode": "numeric", "placeholder": "Ej: 125"})}


class ItemForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = Item
        fields = ["descripcion", "cantidad", "precio_unitario"]
        widgets = {
            "descripcion": forms.TextInput(attrs={"placeholder": "Ej: Clase de guitarra, mantención, diseño de logo…"}),
            "cantidad": forms.NumberInput(attrs={"step": "0.01", "min": "0.01", "inputmode": "decimal", "data-cantidad": ""}),
            "precio_unitario": forms.NumberInput(attrs={"min": "0", "inputmode": "numeric", "placeholder": "0", "data-precio": ""}),
        }

    def clean_cantidad(self):
        valor = self.cleaned_data["cantidad"]
        if valor is None or valor <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor a 0.")
        return valor


ItemFormSet = inlineformset_factory(
    Boleta,
    Item,
    form=ItemForm,
    extra=0,
    min_num=1,
    validate_min=True,
    can_delete=True,
    max_num=50,
)


class ServicioForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = ServicioFrecuente
        fields = ["descripcion", "precio_unitario"]
        widgets = {
            "descripcion": forms.TextInput(attrs={"placeholder": "Ej: Clase de guitarra (1 hora)"}),
            "precio_unitario": forms.NumberInput(attrs={"min": "0", "inputmode": "numeric", "placeholder": "15000"}),
        }
        labels = {"precio_unitario": "Precio ($)"}
