#!/usr/bin/env python3
"""
Script de migración para actualizar el sistema del taller con las nuevas funcionalidades financieras.

Este script añade:
1. Tabla 'gastos' para gastos operativos
2. Configuración tributaria para cálculo de impuestos cubanos
3. Actualiza la configuración existente con los nuevos parámetros

Uso: python3 migracion_finanzas.py
"""

import sys
import os

# Añadir el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Configuracion, Gasto

def ejecutar_migracion():
    """Ejecuta todas las migraciones necesarias"""
    
    with app.app_context():
        print("=" * 60)
        print("MIGRACIÓN DE FINANZAS - Taller de Impresoras")
        print("=" * 60)
        
        # 1. Crear tablas nuevas (incluye tabla 'gastos')
        print("\n[1/3] Creando tablas nuevas...")
        try:
            db.create_all()
            print("✓ Tablas creadas correctamente")
        except Exception as e:
            print(f"✗ Error creando tablas: {e}")
            return False
        
        # 2. Insertar configuración tributaria por defecto
        print("\n[2/3] Insertando configuración tributaria...")
        config_vals = {
            'regimen_fiscal': 'general',
            'cuota_fija_mensual': '0',
            'tasa_isip_1': '5',      # Hasta 10,000 CUP
            'tasa_isip_2': '10',     # De 10,001 a 20,000 CUP
            'tasa_isip_3': '15',     # De 20,001 a 30,000 CUP
            'tasa_isip_4': '20',     # De 30,001 a 40,000 CUP
            'tasa_isip_5': '25',     # De 40,001 a 50,000 CUP
            'tasa_isip_6': '30',     # Más de 50,000 CUP
            'limite_isip_1': '10000',
            'limite_isip_2': '20000',
            'limite_isip_3': '30000',
            'limite_isip_4': '40000',
            'limite_isip_5': '50000',
            'seguridad_social_porcentaje': '5',
            'seguridad_social_base': 'ganancia'
        }
        
        configuraciones_añadidas = 0
        for clave, valor in config_vals.items():
            config = Configuracion.query.filter_by(clave=clave).first()
            if not config:
                config = Configuracion(clave=clave, valor=valor)
                db.session.add(config)
                configuraciones_añadidas += 1
            else:
                # Actualizar si ya existe pero tiene valor diferente
                if config.valor != valor:
                    config.valor = valor
        
        db.session.commit()
        print(f"✓ Configuración tributaria guardada ({configuraciones_añadidas} nuevos valores)")
        
        # 3. Verificar que todo esté correcto
        print("\n[3/3] Verificando instalación...")
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'gastos' in tables:
            print("✓ Tabla 'gastos' existe")
        else:
            print("✗ Tabla 'gastos' NO existe")
            return False
        
        # Verificar configuración
        config_count = Configuracion.query.filter(
            Configuracion.clave.in_(list(config_vals.keys()))
        ).count()
        
        if config_count == len(config_vals):
            print(f"✓ Todos los parámetros tributarios configurados ({config_count}/{len(config_vals)})")
        else:
            print(f"⚠ Algunos parámetros faltan ({config_count}/{len(config_vals)})")
        
        print("\n" + "=" * 60)
        print("MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        print("\nNuevas funcionalidades disponibles:")
        print("  • Panel financiero en Dashboard con filtros por período")
        print("  • Cálculo de tributos cubanos (ISIP + Seguridad Social)")
        print("  • Gestión de gastos operativos")
        print("  • Configuración de régimen fiscal (general/simplificado)")
        print("\nPara acceder:")
        print("  • Dashboard: / (página principal)")
        print("  • Gastos: /reportes/gastos")
        print("  • Configuración Tributaria: /reportes/finanzas/configuracion")
        print("")
        
        return True


if __name__ == '__main__':
    exit_code = 0 if ejecutar_migracion() else 1
    sys.exit(exit_code)
