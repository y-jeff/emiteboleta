from django import template

from .. import formato

register = template.Library()


@register.filter
def clp(monto):
    return formato.clp(monto)


@register.filter
def cantidad(valor):
    return formato.cantidad(valor)


@register.filter
def porcentaje(valor):
    return formato.porcentaje(valor)


@register.filter
def mes_anio(fecha):
    return formato.mes_anio(fecha)
