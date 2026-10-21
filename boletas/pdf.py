"""
Generación del PDF de una boleta con ReportLab.

La idea es que el documento se vea como hecho por un diseñador y no por un
formulario: mucho aire, una sola tipografía con jerarquía clara, un color de
acento elegido por el usuario y detalles como el sello de "PAGADA".
"""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)
from xml.sax.saxutils import escape

from .formato import cantidad, clp, fecha_larga, porcentaje

ANCHO, ALTO = A4
MARGEN = 18 * mm
UTIL = ANCHO - 2 * MARGEN

TINTA = colors.HexColor("#0f172a")
GRIS = colors.HexColor("#64748b")
GRIS_CLARO = colors.HexColor("#e2e8f0")
FONDO = colors.HexColor("#f8fafc")
VERDE = colors.HexColor("#15803d")
AMBAR = colors.HexColor("#b45309")


def _estilos(acento):
    base = dict(fontName="Helvetica", fontSize=9, leading=13, textColor=TINTA)
    return {
        "emisor": ParagraphStyle("emisor", **{**base, "fontName": "Helvetica-Bold", "fontSize": 15, "leading": 19}),
        "dato": ParagraphStyle("dato", **{**base, "fontSize": 8.5, "leading": 12, "textColor": GRIS}),
        "etiqueta": ParagraphStyle(
            "etiqueta", **{**base, "fontName": "Helvetica-Bold", "fontSize": 7, "leading": 10, "textColor": GRIS}
        ),
        "doc": ParagraphStyle(
            "doc", **{**base, "fontName": "Helvetica-Bold", "fontSize": 8, "textColor": acento, "alignment": TA_RIGHT}
        ),
        "numero": ParagraphStyle(
            "numero", **{**base, "fontName": "Helvetica-Bold", "fontSize": 24, "leading": 28, "alignment": TA_RIGHT}
        ),
        "derecha": ParagraphStyle("derecha", **{**base, "alignment": TA_RIGHT}),
        "dato_der": ParagraphStyle("dato_der", **{**base, "fontSize": 8.5, "textColor": GRIS, "alignment": TA_RIGHT}),
        "cliente": ParagraphStyle("cliente", **{**base, "fontName": "Helvetica-Bold", "fontSize": 11, "leading": 15}),
        "celda": ParagraphStyle("celda", **base),
        "celda_der": ParagraphStyle("celda_der", **{**base, "alignment": TA_RIGHT}),
        "th": ParagraphStyle("th", **{**base, "fontName": "Helvetica-Bold", "fontSize": 7.5, "textColor": GRIS}),
        "th_der": ParagraphStyle(
            "th_der", **{**base, "fontName": "Helvetica-Bold", "fontSize": 7.5, "textColor": GRIS, "alignment": TA_RIGHT}
        ),
        "total_label": ParagraphStyle(
            "total_label", **{**base, "fontName": "Helvetica-Bold", "fontSize": 10, "textColor": colors.white}
        ),
        "total_valor": ParagraphStyle(
            "total_valor",
            **{**base, "fontName": "Helvetica-Bold", "fontSize": 15, "leading": 18,
               "textColor": colors.white, "alignment": TA_RIGHT},
        ),
        "nota": ParagraphStyle("nota", **{**base, "fontSize": 8.5, "leading": 12.5, "alignment": TA_LEFT}),
    }


def _p(texto, estilo):
    """Paragraph con el texto escapado y saltos de línea respetados."""
    return Paragraph(escape(str(texto)).replace("\n", "<br/>"), estilo)


def _logo(data, max_ancho=42 * mm, max_alto=20 * mm):
    reader = ImageReader(BytesIO(data))
    w, h = reader.getSize()
    escala = min(max_ancho / w, max_alto / h)
    img = Image(BytesIO(data), width=w * escala, height=h * escala)
    img.hAlign = "LEFT"
    return img


def _cabecera(boleta, logo, est):
    izquierda = []
    if logo:
        izquierda += [_logo(logo), Spacer(1, 4 * mm)]
    izquierda.append(_p(boleta.emisor_nombre, est["emisor"]))
    lineas = [f"RUT {boleta.emisor_rut}", boleta.emisor_giro, boleta.emisor_direccion,
              " · ".join(filter(None, [boleta.emisor_email, boleta.emisor_telefono]))]
    izquierda += [_p(linea, est["dato"]) for linea in lineas if linea]

    derecha = [
        _p("BOLETA DE SERVICIOS", est["doc"]),
        Spacer(1, 1 * mm),
        _p(f"N° {boleta.numero_fmt}", est["numero"]),
        Spacer(1, 2 * mm),
        _p(f"Emitida el {fecha_larga(boleta.fecha)}", est["dato_der"]),
    ]
    tabla = Table([[izquierda, derecha]], colWidths=[UTIL * 0.58, UTIL * 0.42])
    tabla.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return tabla


def _cliente(boleta, est):
    datos = [_p("FACTURADO A", est["etiqueta"]), Spacer(1, 1.5 * mm), _p(boleta.receptor_nombre, est["cliente"])]
    lineas = [f"RUT {boleta.receptor_rut}" if boleta.receptor_rut else "", boleta.receptor_direccion, boleta.receptor_email]
    datos += [_p(linea, est["dato"]) for linea in lineas if linea]

    estado_color = VERDE if boleta.pagada else AMBAR
    estado_txt = "PAGADA" if boleta.pagada else "PENDIENTE DE PAGO"
    estado = [
        _p("ESTADO", ParagraphStyle("e", parent=est["etiqueta"], alignment=TA_RIGHT)),
        Spacer(1, 1.5 * mm),
        _p(estado_txt, ParagraphStyle("estado", parent=est["derecha"], fontName="Helvetica-Bold", textColor=estado_color)),
    ]
    if boleta.pagada and boleta.fecha_pago:
        estado.append(_p(f"el {fecha_larga(boleta.fecha_pago)}", est["dato_der"]))

    tabla = Table([[datos, estado]], colWidths=[UTIL * 0.62, UTIL * 0.38])
    tabla.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), FONDO),
        ("LEFTPADDING", (0, 0), (-1, -1), 5 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 4 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
        ("ROUNDEDCORNERS", [3, 3, 3, 3]),
    ]))
    return tabla


def _items(boleta, est, acento):
    filas = [[
        _p("DESCRIPCIÓN", est["th"]), _p("CANT.", est["th_der"]),
        _p("PRECIO UNIT.", est["th_der"]), _p("TOTAL", est["th_der"]),
    ]]
    for item in boleta.items.all():
        filas.append([
            _p(item.descripcion, est["celda"]),
            _p(cantidad(item.cantidad), est["celda_der"]),
            _p(clp(item.precio_unitario), est["celda_der"]),
            _p(clp(item.total), est["celda_der"]),
        ])
    tabla = Table(filas, colWidths=[UTIL * 0.52, UTIL * 0.12, UTIL * 0.18, UTIL * 0.18], repeatRows=1)
    tabla.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 1.2, acento),
        ("LINEBELOW", (0, 1), (-1, -1), 0.5, GRIS_CLARO),
        ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 0),
    ]))
    return tabla


def _totales(boleta, est, acento):
    filas = [[_p("Subtotal", est["celda"]), _p(clp(boleta.subtotal), est["celda_der"])]]
    if boleta.retencion_pct:
        filas.append([
            _p(f"Retención {porcentaje(boleta.retencion_pct)}", est["celda"]),
            _p(f"-{clp(boleta.retencion_monto)}", est["celda_der"]),
        ])
    filas.append([_p("Total a pagar", est["total_label"]), _p(clp(boleta.total), est["total_valor"])])

    ultima = len(filas) - 1
    tabla = Table(filas, colWidths=[UTIL * 0.22, UTIL * 0.20])
    tabla.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
        ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
        ("BACKGROUND", (0, ultima), (-1, ultima), acento),
        ("TOPPADDING", (0, ultima), (-1, ultima), 3.5 * mm),
        ("BOTTOMPADDING", (0, ultima), (-1, ultima), 3.5 * mm),
        ("ROUNDEDCORNERS", [3, 3, 3, 3]),
    ]))
    tabla.hAlign = "RIGHT"
    return tabla


def _bloque(titulo, texto, est):
    return [_p(titulo, est["etiqueta"]), Spacer(1, 1.5 * mm), _p(texto, est["nota"]), Spacer(1, 6 * mm)]


def _fondo(boleta, acento):
    """Se dibuja antes del contenido: franja superior y pie de página."""

    def dibujar(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(acento)
        canvas.rect(0, ALTO - 5 * mm, ANCHO, 5 * mm, stroke=0, fill=1)

        canvas.setStrokeColor(GRIS_CLARO)
        canvas.setLineWidth(0.5)
        canvas.line(MARGEN, 14 * mm, ANCHO - MARGEN, 14 * mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(GRIS)
        canvas.drawString(
            MARGEN, 10 * mm,
            "Comprobante de prestación de servicios. No reemplaza a la boleta de honorarios electrónica del SII.",
        )
        canvas.drawRightString(ANCHO - MARGEN, 10 * mm, f"N° {boleta.numero_fmt} · Página {doc.page}")
        canvas.restoreState()

    return dibujar


def _sello(boleta):
    """Se dibuja después del contenido, para que el sello quede encima."""

    def dibujar(canvas, doc):
        if not (boleta.pagada and doc.page == 1):
            return
        canvas.saveState()
        canvas.translate(ANCHO - MARGEN - 40 * mm, ALTO - 62 * mm)
        canvas.rotate(12)
        canvas.setStrokeColor(VERDE)
        canvas.setFillColor(VERDE)
        canvas.setFillAlpha(0.8)
        canvas.setStrokeAlpha(0.8)
        canvas.setLineWidth(2)
        canvas.roundRect(-4 * mm, -3 * mm, 40 * mm, 12 * mm, 2 * mm, stroke=1, fill=0)
        canvas.setFont("Helvetica-Bold", 18)
        canvas.drawCentredString(16 * mm, 0.6 * mm, "PAGADA")
        canvas.restoreState()

    return dibujar


def generar_pdf(boleta, perfil=None):
    """Devuelve los bytes del PDF de la boleta."""
    acento = colors.HexColor(perfil.color if perfil else "#1e3a8a")
    logo = bytes(perfil.logo) if perfil and perfil.logo else None
    est = _estilos(acento)

    buffer = BytesIO()
    doc = BaseDocTemplate(
        buffer,
        pagesize=A4,
        title=f"Boleta N° {boleta.numero_fmt}",
        author=boleta.emisor_nombre,
        subject=f"Boleta de servicios para {boleta.receptor_nombre}",
        creator="EmiteBoleta",
    )
    inferior = 22 * mm
    superior = MARGEN + 2 * mm
    marco = Frame(
        MARGEN, inferior, UTIL, ALTO - superior - inferior,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    doc.addPageTemplates(PageTemplate(frames=[marco], onPage=_fondo(boleta, acento), onPageEnd=_sello(boleta)))

    historia = [
        _cabecera(boleta, logo, est),
        Spacer(1, 10 * mm),
        _cliente(boleta, est),
        Spacer(1, 8 * mm),
        _items(boleta, est, acento),
        Spacer(1, 6 * mm),
        _totales(boleta, est, acento),
        Spacer(1, 10 * mm),
    ]
    if boleta.notas:
        historia += _bloque("NOTAS", boleta.notas, est)
    if boleta.emisor_datos_pago:
        historia += _bloque("DATOS PARA TRANSFERENCIA", boleta.emisor_datos_pago, est)

    doc.build(historia)
    return buffer.getvalue()
