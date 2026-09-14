"""
Utilidades para el sistema de gestión de taller
Funciones helper y utilidades comunes
"""
import os
import secrets
from datetime import datetime
from functools import wraps
from flask import session, redirect, url_for


def generar_numero_orden():
    """Genera un número de orden único basado en la fecha y hora"""
    ahora = datetime.now()
    return f"ORD-{ahora.strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3)}"


def formatear_moneda(monto, moneda='CUP'):
    """Formatea un monto como moneda"""
    if monto is None:
        monto = 0
    return f"{moneda} ${monto:,.2f}"


def parsear_fecha(fecha_str, formato='%Y-%m-%d'):
    """Convierte una cadena de fecha a objeto datetime"""
    if not fecha_str:
        return None
    try:
        return datetime.strptime(fecha_str, formato)
    except (ValueError, TypeError):
        return None


def calcular_diferencia_dias(fecha1, fecha2):
    """Calcula la diferencia en días entre dos fechas"""
    if not fecha1 or not fecha2:
        return None
    
    if isinstance(fecha1, str):
        fecha1 = parsear_fecha(fecha1)
    if isinstance(fecha2, str):
        fecha2 = parsear_fecha(fecha2)
    
    if fecha1 and fecha2:
        delta = fecha2 - fecha1
        return delta.days
    return None


def es_bisiesto(anio):
    """Verifica si un año es bisiesto"""
    return anio % 4 == 0 and (anio % 100 != 0 or anio % 400 == 0)


def obtener_primer_y_ultimo_dia_mes(fecha=None):
    """Obtiene el primer y último día del mes de una fecha dada"""
    if fecha is None:
        fecha = datetime.now()
    
    primer_dia = fecha.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    if fecha.month == 12:
        ultimo_dia = fecha.replace(year=fecha.year+1, month=1, day=1) - timedelta(days=1)
    else:
        ultimo_dia = fecha.replace(month=fecha.month+1, day=1) - timedelta(days=1)
    
    return primer_dia, ultimo_dia


def validar_email(email):
    """Valida un formato básico de email"""
    import re
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None


def limpiar_string(cadena):
    """Limpia un string eliminando espacios extras y caracteres no válidos"""
    if not cadena:
        return ''
    return ' '.join(cadena.split())


def safe_int(valor, default=0):
    """Convierte un valor a entero de forma segura"""
    try:
        return int(valor)
    except (ValueError, TypeError):
        return default


def safe_float(valor, default=0.0):
    """Convierte un valor a float de forma segura"""
    try:
        return float(valor)
    except (ValueError, TypeError):
        return default


def crear_directorio_si_no_existe(ruta):
    """Crea un directorio si no existe"""
    if not os.path.exists(ruta):
        os.makedirs(ruta)
    return ruta
