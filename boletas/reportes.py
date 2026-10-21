"""Resúmenes por período y exportación del historial."""

import csv
from io import StringIO

from .formato import MESES, cantidad


def resumen_anual(boletas):
    """Agrupa las boletas de un año por mes. Devuelve (meses, totales)."""
    meses = [
        {"numero": n, "nombre": MESES[n - 1].capitalize(), "cantidad": 0,
         "bruto": 0, "retencion": 0, "liquido": 0, "pagado": 0, "pendiente": 0}
        for n in range(1, 13)
    ]
    for boleta in boletas:
        mes = meses[boleta.fecha.month - 1]
        mes["cantidad"] += 1
        mes["bruto"] += boleta.subtotal
        mes["retencion"] += boleta.retencion_monto
        mes["liquido"] += boleta.total
        mes["pagado" if boleta.pagada else "pendiente"] += boleta.total

    claves = ("cantidad", "bruto", "retencion", "liquido", "pagado", "pendiente")
    totales = {clave: sum(mes[clave] for mes in meses) for clave in claves}
    maximo = max((mes["bruto"] for mes in meses), default=0) or 1
    for mes in meses:
        mes["porcentaje"] = round(mes["bruto"] * 100 / maximo)
    return meses, totales


COLUMNAS = [
    "N°", "Fecha", "Cliente", "RUT cliente", "Servicios", "Monto bruto",
    "Retención %", "Retención", "Líquido", "Estado", "Fecha de pago",
]


def exportar_csv(boletas):
    """CSV pensado para abrirse con doble clic en Excel configurado en español."""
    salida = StringIO()
    salida.write("﻿")  # BOM: Excel detecta UTF-8 y muestra bien los acentos
    escritor = csv.writer(salida, delimiter=";")
    escritor.writerow(COLUMNAS)
    for b in boletas:
        escritor.writerow([
            b.numero,
            b.fecha.strftime("%d-%m-%Y"),
            b.receptor_nombre,
            b.receptor_rut,
            " | ".join(item.descripcion for item in b.items.all()),
            b.subtotal,
            cantidad(b.retencion_pct),
            b.retencion_monto,
            b.total,
            b.get_estado_display(),
            b.fecha_pago.strftime("%d-%m-%Y") if b.fecha_pago else "",
        ])
    return salida.getvalue()
