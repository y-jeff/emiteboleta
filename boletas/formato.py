"""Formato chileno para montos, cantidades y fechas."""

from decimal import Decimal

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def clp(monto):
    """1234567 -> '$1.234.567'"""
    monto = int(monto or 0)
    signo = "-" if monto < 0 else ""
    return f"{signo}${abs(monto):,}".replace(",", ".")


def cantidad(valor):
    """Decimal('2.00') -> '2', Decimal('1.50') -> '1,5'"""
    valor = Decimal(valor).normalize()
    texto = f"{valor:f}"
    return texto.replace(".", ",")


def porcentaje(valor):
    return cantidad(valor) + "%"


def fecha_larga(fecha):
    """date(2026, 10, 21) -> '21 de octubre de 2026'"""
    return f"{fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}"


def mes_anio(fecha):
    return f"{MESES[fecha.month - 1].capitalize()} {fecha.year}"
