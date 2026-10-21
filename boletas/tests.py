from datetime import date
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from . import formato, rut
from .models import Boleta, Item, PerfilEmisor
from .pdf import generar_pdf

User = get_user_model()


def crear_usuario(email="ana@ejemplo.cl", completo=True):
    user = User.objects.create_user(username=email, email=email, password="clave-segura-123")
    perfil = PerfilEmisor.de(user)
    if completo:
        perfil.nombre, perfil.rut = "Ana Pérez", "12.345.678-5"
        perfil.datos_pago = "Banco Estado\nCuenta RUT 12345678"
        perfil.save()
    return user, perfil


def emitir(perfil, items=((1, 10000),), **kwargs):
    boleta = Boleta(receptor_nombre="Cliente SpA", **kwargs)
    boleta.emitir(perfil)
    for cant, precio in items:
        Item.objects.create(boleta=boleta, descripcion="Servicio", cantidad=Decimal(cant), precio_unitario=precio)
    return boleta


def datos_formulario(**extra):
    datos = {
        "receptor_nombre": "Panadería Doña Rosa",
        "receptor_rut": "11111111-1",
        "receptor_email": "",
        "receptor_direccion": "",
        "fecha": "2026-10-21",
        "retencion_pct": "0",
        "estado": "pendiente",
        "notas": "",
        "items-TOTAL_FORMS": "2",
        "items-INITIAL_FORMS": "0",
        "items-MIN_NUM_FORMS": "1",
        "items-MAX_NUM_FORMS": "50",
        "items-0-descripcion": "Mantención de horno",
        "items-0-cantidad": "1",
        "items-0-precio_unitario": "45000",
        "items-1-descripcion": "Repuesto",
        "items-1-cantidad": "2",
        "items-1-precio_unitario": "7500",
    }
    datos.update(extra)
    return datos


class RutTests(TestCase):
    def test_valida_digito_verificador(self):
        self.assertTrue(rut.es_valido("12.345.678-5"))
        self.assertTrue(rut.es_valido("11111111-1"))
        self.assertTrue(rut.es_valido("10.000.013-k"))
        self.assertFalse(rut.es_valido("12.345.678-9"))
        self.assertFalse(rut.es_valido("abc"))

    def test_formatea(self):
        self.assertEqual(rut.formatear("123456785"), "12.345.678-5")
        self.assertEqual(rut.formatear("10000013k"), "10.000.013-K")


class FormatoTests(TestCase):
    def test_clp(self):
        self.assertEqual(formato.clp(1234567), "$1.234.567")
        self.assertEqual(formato.clp(0), "$0")
        self.assertEqual(formato.clp(-500), "-$500")

    def test_cantidad_y_fecha(self):
        self.assertEqual(formato.cantidad(Decimal("2.00")), "2")
        self.assertEqual(formato.cantidad(Decimal("1.50")), "1,5")
        self.assertEqual(formato.fecha_larga(date(2026, 10, 21)), "21 de octubre de 2026")


class BoletaModelTests(TestCase):
    def setUp(self):
        self.user, self.perfil = crear_usuario()

    def test_numeracion_correlativa(self):
        numeros = [emitir(self.perfil).numero for _ in range(3)]
        self.assertEqual(numeros, [1, 2, 3])
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.siguiente_numero, 4)

    def test_numeracion_parte_desde_numero_configurado(self):
        self.perfil.siguiente_numero = 120
        self.perfil.save()
        self.assertEqual(emitir(self.perfil).numero, 120)

    def test_numeracion_no_repite_si_el_contador_retrocede(self):
        emitir(self.perfil)
        emitir(self.perfil)
        PerfilEmisor.objects.filter(pk=self.perfil.pk).update(siguiente_numero=1)
        self.assertEqual(emitir(self.perfil).numero, 3)

    def test_numeracion_independiente_por_usuario(self):
        _, otro = crear_usuario("beto@ejemplo.cl")
        emitir(self.perfil)
        self.assertEqual(emitir(otro).numero, 1)

    def test_totales_con_retencion(self):
        boleta = emitir(self.perfil, items=[(1, 100000), ("1.5", 3333)], retencion_pct=Decimal("15.25"))
        self.assertEqual(boleta.subtotal, 105000)  # 3333 * 1.5 = 4999.5 -> 5000
        self.assertEqual(boleta.retencion_monto, 16013)  # 16012.5 -> 16013
        self.assertEqual(boleta.total, 88987)

    def test_guarda_copia_del_emisor(self):
        boleta = emitir(self.perfil)
        self.perfil.nombre = "Nombre nuevo"
        self.perfil.save()
        boleta.refresh_from_db()
        self.assertEqual(boleta.emisor_nombre, "Ana Pérez")

    def test_marcar_pagada_registra_fecha(self):
        boleta = emitir(self.perfil)
        boleta.marcar(Boleta.PAGADA)
        self.assertIsNotNone(boleta.fecha_pago)
        boleta.marcar(Boleta.PENDIENTE)
        self.assertIsNone(boleta.fecha_pago)


class PdfTests(TestCase):
    def test_genera_pdf_valido_con_logo_y_sello(self):
        user, perfil = crear_usuario()
        buffer = BytesIO()
        Image.new("RGB", (300, 100), "navy").save(buffer, "PNG")
        perfil.logo, perfil.logo_mime = buffer.getvalue(), "image/png"
        perfil.save()
        boleta = emitir(perfil, items=[(1, 50000)] * 40, notas="Gracias por preferirnos")
        boleta.marcar(Boleta.PAGADA)
        boleta.save()

        contenido = generar_pdf(boleta, perfil)
        self.assertTrue(contenido.startswith(b"%PDF"))
        self.assertGreater(len(contenido), 3000)


class VistasTests(TestCase):
    def setUp(self):
        self.user, self.perfil = crear_usuario()
        self.client.force_login(self.user)

    def test_requiere_login(self):
        self.client.logout()
        respuesta = self.client.get(reverse("boletas:dashboard"))
        self.assertRedirects(respuesta, f"{reverse('cuentas:login')}?next={reverse('boletas:dashboard')}")

    def test_landing_publica(self):
        self.client.logout()
        self.assertContains(self.client.get(reverse("home")), "Crear mi cuenta gratis")

    def test_paginas_renderizan(self):
        boleta = emitir(self.perfil)
        for url in (
            reverse("boletas:dashboard"), reverse("boletas:lista"), reverse("boletas:crear"),
            reverse("boletas:perfil"), boleta.get_absolute_url(), reverse("boletas:editar", args=[boleta.pk]),
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_crear_boleta_con_varios_items(self):
        respuesta = self.client.post(reverse("boletas:crear"), datos_formulario())
        boleta = Boleta.objects.get()
        self.assertRedirects(respuesta, boleta.get_absolute_url())
        self.assertEqual(boleta.numero, 1)
        self.assertEqual(boleta.items.count(), 2)
        self.assertEqual(boleta.total, 60000)
        self.assertEqual(boleta.receptor_rut, "11.111.111-1")
        self.assertEqual(boleta.emisor_rut, "12.345.678-5")

    def test_rechaza_rut_invalido(self):
        respuesta = self.client.post(reverse("boletas:crear"), datos_formulario(receptor_rut="11111111-2"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "RUT inválido")
        self.assertFalse(Boleta.objects.exists())

    def test_crear_sin_perfil_redirige_a_completar_datos(self):
        user, _ = crear_usuario("nuevo@ejemplo.cl", completo=False)
        self.client.force_login(user)
        respuesta = self.client.get(reverse("boletas:crear"))
        self.assertRedirects(respuesta, f"{reverse('boletas:perfil')}?next=%2Fapp%2Fboletas%2Fnueva%2F")

    def test_no_puede_ver_boletas_de_otro_usuario(self):
        _, otro = crear_usuario("beto@ejemplo.cl")
        ajena = emitir(otro)
        for nombre in ("detalle", "editar", "pdf"):
            self.assertEqual(self.client.get(reverse(f"boletas:{nombre}", args=[ajena.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("boletas:eliminar", args=[ajena.pk])).status_code, 404)
        self.assertTrue(Boleta.objects.filter(pk=ajena.pk).exists())

    def test_descargar_pdf(self):
        boleta = emitir(self.perfil)
        respuesta = self.client.get(reverse("boletas:pdf", args=[boleta.pk]) + "?descargar=1")
        self.assertEqual(respuesta["Content-Type"], "application/pdf")
        self.assertIn('attachment; filename="boleta-000001.pdf"', respuesta["Content-Disposition"])

    def test_cambiar_estado(self):
        boleta = emitir(self.perfil)
        self.client.post(reverse("boletas:estado", args=[boleta.pk]))
        boleta.refresh_from_db()
        self.assertTrue(boleta.pagada)

    def test_duplicar(self):
        original = emitir(self.perfil, items=[(2, 5000), (1, 1000)])
        self.client.post(reverse("boletas:duplicar", args=[original.pk]))
        copia = Boleta.objects.exclude(pk=original.pk).get()
        self.assertEqual(copia.numero, 2)
        self.assertEqual(copia.total, original.total)

    def test_dashboard_totales_del_mes(self):
        emitir(self.perfil, items=[(1, 30000)])
        pagada = emitir(self.perfil, items=[(1, 20000)])
        pagada.marcar(Boleta.PAGADA)
        pagada.save()
        resumen = self.client.get(reverse("boletas:dashboard")).context["resumen"]
        self.assertEqual(resumen, {"emitido": 50000, "pagado": 20000, "pendiente": 30000, "cantidad": 2})

    def test_buscar(self):
        emitir(self.perfil)
        respuesta = self.client.get(reverse("boletas:lista"), {"q": "cliente", "estado": "pendiente"})
        self.assertEqual(len(respuesta.context["pagina"]), 1)

    def test_subir_logo(self):
        buffer = BytesIO()
        Image.new("RGB", (120, 40), "red").save(buffer, "PNG")
        archivo = SimpleUploadedFile("logo.png", buffer.getvalue(), content_type="image/png")
        datos = {
            "nombre": "Ana Pérez", "rut": "123456785", "color": "#0f766e",
            "siguiente_numero": "1", "retencion_por_defecto": "0", "logo_archivo": archivo,
        }
        self.client.post(reverse("boletas:perfil"), datos)
        self.perfil.refresh_from_db()
        self.assertTrue(self.perfil.tiene_logo)
        self.assertEqual(self.perfil.rut, "12.345.678-5")
        self.assertEqual(self.client.get(reverse("boletas:logo"))["Content-Type"], "image/png")

    def test_rechaza_logo_que_no_es_imagen(self):
        archivo = SimpleUploadedFile("logo.png", b"no soy una imagen", content_type="image/png")
        datos = {"nombre": "Ana", "rut": "12.345.678-5", "color": "#0f766e",
                 "siguiente_numero": "1", "retencion_por_defecto": "0", "logo_archivo": archivo}
        respuesta = self.client.post(reverse("boletas:perfil"), datos)
        self.assertContains(respuesta, "no es una imagen válida")


class CuentasTests(TestCase):
    def test_registro_e_ingreso_con_email(self):
        respuesta = self.client.post(reverse("cuentas:registro"), {
            "email": "Nueva@Ejemplo.cl", "password1": "una-clave-larga-99", "password2": "una-clave-larga-99",
        })
        self.assertRedirects(respuesta, reverse("boletas:perfil"))
        self.client.logout()
        respuesta = self.client.post(reverse("cuentas:login"), {"username": "NUEVA@ejemplo.cl", "password": "una-clave-larga-99"})
        self.assertRedirects(respuesta, reverse("boletas:dashboard"))

    def test_email_duplicado(self):
        crear_usuario("ana@ejemplo.cl")
        respuesta = self.client.post(reverse("cuentas:registro"), {
            "email": "ANA@ejemplo.cl", "password1": "una-clave-larga-99", "password2": "una-clave-larga-99",
        })
        self.assertContains(respuesta, "Ya existe una cuenta")
