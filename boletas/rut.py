"""Validación y formato de RUT chileno (módulo 11)."""

import re

from django.core.exceptions import ValidationError


def limpiar(rut):
    return re.sub(r"[^0-9kK]", "", rut or "").upper()


def calcular_dv(cuerpo):
    suma, factor = 0, 2
    for digito in reversed(str(cuerpo)):
        suma += int(digito) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - (suma % 11)
    return {11: "0", 10: "K"}.get(resto, str(resto))


def es_valido(rut):
    rut = limpiar(rut)
    if len(rut) < 2 or not rut[:-1].isdigit():
        return False
    return calcular_dv(rut[:-1]) == rut[-1]


def formatear(rut):
    """'123456785' -> '12.345.678-5'. Si no es válido lo devuelve tal cual."""
    limpio = limpiar(rut)
    if not es_valido(limpio):
        return rut
    cuerpo, dv = limpio[:-1], limpio[-1]
    return f"{int(cuerpo):,}".replace(",", ".") + f"-{dv}"


def validar_rut(valor):
    if valor and not es_valido(valor):
        raise ValidationError("RUT inválido. Revisa el dígito verificador.")
