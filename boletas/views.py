from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import BoletaForm, ItemFormSet, PerfilForm, ServicioForm
from .models import Boleta, PerfilEmisor
from .formato import clp
from .pdf import generar_pdf
from .reportes import exportar_csv, resumen_anual


def perfil_requerido(vista):
    """Antes de emitir, el usuario debe haber completado sus datos de emisor."""

    @wraps(vista)
    @login_required
    def envoltura(request, *args, **kwargs):
        request.perfil = PerfilEmisor.de(request.user)
        if not request.perfil.completo:
            messages.info(request, "Primero completa tus datos de emisor. Solo se hace una vez.")
            return redirect(f"{reverse('boletas:perfil')}?{urlencode({'next': request.get_full_path()})}")
        return vista(request, *args, **kwargs)

    return envoltura


def _destino_seguro(request, destino):
    if destino and url_has_allowed_host_and_scheme(destino, {request.get_host()}, request.is_secure()):
        return destino
    return None


def _boleta_del_usuario(request, pk):
    return get_object_or_404(Boleta.objects.prefetch_related("items"), pk=pk, user=request.user)


def home(request):
    if request.user.is_authenticated:
        return redirect("boletas:dashboard")
    return render(request, "home.html")


@login_required
def dashboard(request):
    perfil = PerfilEmisor.de(request.user)
    hoy = timezone.localdate()
    del_mes = list(request.user.boletas.del_mes(hoy).prefetch_related("items"))

    resumen = {
        "emitido": sum(b.total for b in del_mes),
        "pagado": sum(b.total for b in del_mes if b.pagada),
        "pendiente": sum(b.total for b in del_mes if not b.pagada),
        "cantidad": len(del_mes),
    }
    # Pendientes de cualquier mes: es lo que el usuario más necesita cobrar.
    por_cobrar = list(request.user.boletas.filter(estado=Boleta.PENDIENTE).prefetch_related("items")[:5])
    recientes = request.user.boletas.prefetch_related("items")[:5]

    return render(request, "boletas/dashboard.html", {
        "perfil": perfil,
        "hoy": hoy,
        "resumen": resumen,
        "por_cobrar": por_cobrar,
        "recientes": recientes,
    })


def _anio(request, hoy):
    try:
        return int(request.GET.get("anio", hoy.year))
    except ValueError:
        return hoy.year


@login_required
def resumen(request):
    hoy = timezone.localdate()
    anio = _anio(request, hoy)
    boletas = request.user.boletas.filter(fecha__year=anio).prefetch_related("items")
    meses, totales = resumen_anual(boletas)
    anios = sorted({d.year for d in request.user.boletas.dates("fecha", "year")} | {hoy.year}, reverse=True)
    return render(request, "boletas/resumen.html", {
        "anio": anio,
        "anios": anios,
        "meses": meses,
        "totales": totales,
        "mes_actual": hoy.month if anio == hoy.year else None,
    })


@login_required
def exportar(request):
    anio = _anio(request, timezone.localdate())
    boletas = request.user.boletas.filter(fecha__year=anio).order_by("fecha", "numero").prefetch_related("items")
    respuesta = HttpResponse(exportar_csv(boletas), content_type="text/csv; charset=utf-8")
    respuesta["Content-Disposition"] = f'attachment; filename="boletas-{anio}.csv"'
    return respuesta


@login_required
def lista(request):
    boletas = request.user.boletas.prefetch_related("items")
    q = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "")
    if q:
        filtro = Q(receptor_nombre__icontains=q) | Q(receptor_rut__icontains=q) | Q(items__descripcion__icontains=q)
        if q.isdigit():
            filtro |= Q(numero=int(q))
        boletas = boletas.filter(filtro).distinct()
    if estado in dict(Boleta.ESTADOS):
        boletas = boletas.filter(estado=estado)

    pagina = Paginator(boletas, 15).get_page(request.GET.get("page"))
    return render(request, "boletas/lista.html", {"pagina": pagina, "q": q, "estado": estado})


def _clientes_frecuentes(user):
    """Últimos clientes distintos, para autocompletar el formulario."""
    vistos, clientes = set(), []
    campos = ("receptor_nombre", "receptor_rut", "receptor_email", "receptor_direccion")
    for fila in user.boletas.order_by("-creada").values(*campos)[:200]:
        clave = fila["receptor_nombre"].lower()
        if clave not in vistos:
            vistos.add(clave)
            clientes.append(fila)
        if len(clientes) == 30:
            break
    return clientes


def _formulario(request, boleta, es_nueva):
    if request.method == "POST":
        form = BoletaForm(request.POST, instance=boleta)
        items = ItemFormSet(request.POST, instance=boleta)
        if form.is_valid() and items.is_valid():
            with transaction.atomic():
                boleta = form.save(commit=False)
                if "estado" in form.changed_data or es_nueva:
                    boleta.marcar(boleta.estado)
                if es_nueva:
                    boleta.emitir(request.perfil)
                else:
                    boleta.save()
                items.instance = boleta
                items.save()
            accion = "emitida" if es_nueva else "actualizada"
            messages.success(request, f"Boleta N° {boleta.numero_fmt} {accion}.")
            return redirect(boleta)
    else:
        form = BoletaForm(instance=boleta)
        items = ItemFormSet(instance=boleta)

    return render(request, "boletas/formulario.html", {
        "form": form,
        "items": items,
        "boleta": boleta,
        "es_nueva": es_nueva,
        "clientes": _clientes_frecuentes(request.user),
        "catalogo": list(request.user.servicios.values("descripcion", "precio_unitario")),
        "proximo_numero": f"{request.perfil.siguiente_numero:06d}",
    })


@perfil_requerido
def crear(request):
    boleta = Boleta(user=request.user, retencion_pct=request.perfil.retencion_por_defecto)
    return _formulario(request, boleta, es_nueva=True)


@perfil_requerido
def editar(request, pk):
    return _formulario(request, _boleta_del_usuario(request, pk), es_nueva=False)


def _mensaje_whatsapp(boleta):
    partes = [f"Hola {boleta.receptor_nombre}, te envío la nota de cobro N° {boleta.numero_fmt} por {clp(boleta.total)}."]
    if boleta.pagada:
        partes.append("Ya está registrada como pagada. ¡Gracias!")
    elif boleta.emisor_datos_pago:
        partes.append(f"Datos para transferencia:\n{boleta.emisor_datos_pago}")
    partes.append(boleta.emisor_nombre)
    return "\n\n".join(partes)


@login_required
def detalle(request, pk):
    boleta = _boleta_del_usuario(request, pk)
    return render(request, "boletas/detalle.html", {"boleta": boleta, "mensaje_whatsapp": _mensaje_whatsapp(boleta)})


@login_required
def pdf(request, pk):
    boleta = _boleta_del_usuario(request, pk)
    contenido = generar_pdf(boleta, PerfilEmisor.de(request.user))
    respuesta = HttpResponse(contenido, content_type="application/pdf")
    disposicion = "attachment" if request.GET.get("descargar") else "inline"
    respuesta["Content-Disposition"] = f'{disposicion}; filename="nota-de-cobro-{boleta.numero_fmt}.pdf"'
    return respuesta


@login_required
@require_POST
def cambiar_estado(request, pk):
    boleta = _boleta_del_usuario(request, pk)
    boleta.marcar(Boleta.PENDIENTE if boleta.pagada else Boleta.PAGADA)
    boleta.save(update_fields=["estado", "fecha_pago", "actualizada"])
    messages.success(request, f"Boleta N° {boleta.numero_fmt} marcada como {boleta.get_estado_display().lower()}.")
    return redirect(_destino_seguro(request, request.POST.get("next")) or boleta.get_absolute_url())


@perfil_requerido
@require_POST
def duplicar(request, pk):
    original = _boleta_del_usuario(request, pk)
    items = list(original.items.all())
    copia = Boleta(
        receptor_nombre=original.receptor_nombre,
        receptor_rut=original.receptor_rut,
        receptor_email=original.receptor_email,
        receptor_direccion=original.receptor_direccion,
        notas=original.notas,
        retencion_pct=original.retencion_pct,
    )
    with transaction.atomic():
        copia.emitir(request.perfil)
        for item in items:
            item.pk = None
            item.boleta = copia
            item.save()
    messages.success(request, f"Creaste la boleta N° {copia.numero_fmt} a partir de la N° {original.numero_fmt}. Revisa los datos.")
    return redirect("boletas:editar", pk=copia.pk)


@login_required
@require_POST
def eliminar(request, pk):
    boleta = _boleta_del_usuario(request, pk)
    numero = boleta.numero_fmt
    boleta.delete()
    messages.success(request, f"Boleta N° {numero} eliminada.")
    return redirect("boletas:lista")


@login_required
def perfil(request):
    perfil = PerfilEmisor.de(request.user)
    destino = _destino_seguro(request, request.GET.get("next") or request.POST.get("next"))
    if request.method == "POST":
        form = PerfilForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, "Datos de emisor guardados.")
            return redirect(destino or "boletas:perfil")
    else:
        form = PerfilForm(instance=perfil)
    return render(request, "boletas/perfil.html", {"form": form, "perfil": perfil, "next": destino or ""})


@login_required
def logo(request):
    perfil = PerfilEmisor.de(request.user)
    if not perfil.logo:
        raise Http404
    respuesta = HttpResponse(bytes(perfil.logo), content_type=perfil.logo_mime)
    respuesta["Cache-Control"] = "private, max-age=300"
    return respuesta


@login_required
def catalogo(request):
    form = ServicioForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        servicio = form.save(commit=False)
        servicio.user = request.user
        servicio.save()
        messages.success(request, f"«{servicio.descripcion}» quedó guardado en tu catálogo.")
        return redirect("boletas:catalogo")
    return render(request, "boletas/catalogo.html", {
        "form": form,
        "servicios": request.user.servicios.all(),
    })


@login_required
@require_POST
def catalogo_eliminar(request, pk):
    servicio = get_object_or_404(request.user.servicios, pk=pk)
    servicio.delete()
    messages.success(request, f"«{servicio.descripcion}» se quitó de tu catálogo.")
    return redirect("boletas:catalogo")

