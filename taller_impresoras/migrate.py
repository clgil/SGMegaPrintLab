"""
Script de migración para agregar nuevas funcionalidades al Sistema de Gestión de Taller de Impresoras
Adaptado a la realidad cubana - Junio 2026

Este script agrega:
1. Seguimiento de garantías y reingresos
2. Gestión de proveedores
3. Contratos de mantenimiento periódico
4. Control de tiempo y productividad de técnicos
5. Notas internas en órdenes
6. Configuración de moneda y tasa de cambio

Uso: python migrate.py
"""

import sqlite3
from datetime import datetime
import os

# Ruta de la base de datos
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'taller.db')

def obtener_conexion():
    """Obtiene conexión a la base de datos SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ejecutar_sql(conn, sql, params=None):
    """Ejecuta una sentencia SQL"""
    cursor = conn.cursor()
    if params:
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)
    conn.commit()
    return cursor

def verificar_columna_existe(conn, tabla, columna):
    """Verifica si una columna existe en una tabla"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({tabla})")
    columnas = [row[1] for row in cursor.fetchall()]
    return columna in columnas

def verificar_tabla_existe(conn, tabla):
    """Verifica si una tabla existe"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabla,))
    return cursor.fetchone() is not None

def migrar_proveedores_a_tabla(conn):
    """Migra los proveedores de texto a la nueva tabla de proveedores"""
    print("Migrando proveedores de texto a tabla...")
    
    # Obtener todos los proveedores únicos de la tabla piezas
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT proveedor FROM piezas WHERE proveedor IS NOT NULL AND proveedor != ''")
    proveedores_texto = [row[0] for row in cursor.fetchall()]
    
    # Crear un mapeo de nombre de proveedor a ID
    proveedor_map = {}
    
    for proveedor_nombre in proveedores_texto:
        # Determinar si es formal o informal (por defecto informal para los existentes)
        tipo = 'informal'
        
        # Insertar en la tabla proveedores
        cursor.execute("""
            INSERT INTO proveedores (nombre, contacto, telefono, tipo, activo)
            VALUES (?, '', '', ?, 1)
        """, (proveedor_nombre, tipo))
        
        proveedor_id = cursor.lastrowid
        proveedor_map[proveedor_nombre] = proveedor_id
        print(f"  Creado proveedor: {proveedor_nombre} (ID: {proveedor_id})")
    
    conn.commit()
    return proveedor_map

def main():
    """Función principal de migración"""
    print("=" * 70)
    print("Migración de Base de Datos - Taller de Impresoras")
    print("=" * 70)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base de datos: {DB_PATH}")
    print()
    
    if not os.path.exists(DB_PATH):
        print("ERROR: La base de datos no existe. Ejecute primero la aplicación para crearla.")
        return
    
    conn = obtener_conexion()
    
    try:
        # ==========================================
        # 1. TABLA DE PROVEEDORES
        # ==========================================
        print("1. Creando tabla de proveedores...")
        if not verificar_tabla_existe(conn, 'proveedores'):
            ejecutar_sql(conn, """
                CREATE TABLE proveedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    contacto TEXT,
                    telefono TEXT,
                    tipo TEXT DEFAULT 'informal' CHECK(tipo IN ('formal','informal')),
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TEXT DEFAULT CURRENT_DATE
                )
            """)
            print("   ✓ Tabla proveedores creada")
        else:
            print("   ⚠ Tabla proveedores ya existe")
        
        # ==========================================
        # 2. CAMPOS EN TABLA PIEZAS
        # ==========================================
        print("\n2. Agregando campo proveedor_id a piezas...")
        if not verificar_columna_existe(conn, 'piezas', 'proveedor_id'):
            ejecutar_sql(conn, "ALTER TABLE piezas ADD COLUMN proveedor_id INTEGER REFERENCES proveedores(id)")
            print("   ✓ Campo proveedor_id agregado")
            
            # Migrar proveedores de texto a la nueva tabla
            proveedor_map = migrar_proveedores_a_tabla(conn)
            
            # Actualizar las piezas con el nuevo proveedor_id
            for proveedor_nombre, proveedor_id in proveedor_map.items():
                ejecutar_sql(conn, """
                    UPDATE piezas 
                    SET proveedor_id = ? 
                    WHERE proveedor = ?
                """, (proveedor_id, proveedor_nombre))
            print("   ✓ Proveedores migrados correctamente")
        else:
            print("   ⚠ Campo proveedor_id ya existe")
        
        # ==========================================
        # 3. CAMPOS EN TABLA ORDENES (Garantías)
        # ==========================================
        print("\n3. Agregando campos de garantía a ordenes...")
        campos_garantia = [
            ('garantia_meses', "ALTER TABLE ordenes ADD COLUMN garantia_meses INTEGER DEFAULT 0"),
            ('fecha_fin_garantia', "ALTER TABLE ordenes ADD COLUMN fecha_fin_garantia TEXT"),
            ('orden_original_id', "ALTER TABLE ordenes ADD COLUMN orden_original_id INTEGER REFERENCES ordenes(id)"),
            ('es_reingreso', "ALTER TABLE ordenes ADD COLUMN es_reingreso INTEGER DEFAULT 0"),
            ('tipo_orden', "ALTER TABLE ordenes ADD COLUMN tipo_orden TEXT DEFAULT 'reparacion'")
        ]
        
        for campo, sql in campos_garantia:
            if not verificar_columna_existe(conn, 'ordenes', campo):
                ejecutar_sql(conn, sql)
                print(f"   ✓ Campo {campo} agregado")
            else:
                print(f"   ⚠ Campo {campo} ya existe")
        
        # ==========================================
        # 4. CAMPOS EN TABLA ORDENES (Tiempo de reparación)
        # ==========================================
        print("\n4. Agregando campos de tiempo de reparación...")
        campos_tiempo = [
            ('fecha_inicio_reparacion', "ALTER TABLE ordenes ADD COLUMN fecha_inicio_reparacion TEXT"),
            ('fecha_fin_reparacion', "ALTER TABLE ordenes ADD COLUMN fecha_fin_reparacion TEXT")
        ]
        
        for campo, sql in campos_tiempo:
            if not verificar_columna_existe(conn, 'ordenes', campo):
                ejecutar_sql(conn, sql)
                print(f"   ✓ Campo {campo} agregado")
            else:
                print(f"   ⚠ Campo {campo} ya existe")
        
        # ==========================================
        # 5. TABLA DE CONTRATOS
        # ==========================================
        print("\n5. Creando tabla de contratos...")
        if not verificar_tabla_existe(conn, 'contratos'):
            ejecutar_sql(conn, """
                CREATE TABLE contratos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER NOT NULL,
                    descripcion TEXT,
                    frecuencia TEXT NOT NULL CHECK(frecuencia IN ('semanal','quincenal','mensual','trimestral','semestral','anual')),
                    fecha_inicio TEXT NOT NULL,
                    fecha_fin TEXT,
                    activo INTEGER DEFAULT 1,
                    precio_mantenimiento REAL DEFAULT 0,
                    dispositivos_cubiertos INTEGER DEFAULT 1,
                    ultima_visita TEXT,
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
                )
            """)
            print("   ✓ Tabla contratos creada")
        else:
            print("   ⚠ Tabla contratos ya existe")
        
        # ==========================================
        # 6. TABLA DE NOTAS DE ORDENES
        # ==========================================
        print("\n6. Creando tabla de notas de órdenes...")
        if not verificar_tabla_existe(conn, 'orden_notas'):
            ejecutar_sql(conn, """
                CREATE TABLE orden_notas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    orden_id INTEGER NOT NULL,
                    texto TEXT NOT NULL,
                    fecha_hora TEXT NOT NULL,
                    usuario_id INTEGER,
                    FOREIGN KEY (orden_id) REFERENCES ordenes(id),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            """)
            print("   ✓ Tabla orden_notas creada")
        else:
            print("   ⚠ Tabla orden_notas ya existe")
        
        # ==========================================
        # 7. CAMPO EN TABLA TECNICOS (Costo por hora)
        # ==========================================
        print("\n7. Agregando campo costo_hora a tecnicos...")
        if not verificar_columna_existe(conn, 'tecnicos', 'costo_hora'):
            ejecutar_sql(conn, "ALTER TABLE tecnicos ADD COLUMN costo_hora REAL DEFAULT 0")
            print("   ✓ Campo costo_hora agregado")
        else:
            print("   ⚠ Campo costo_hora ya existe")
        
        # ==========================================
        # 8. CONFIGURACION DE MONEDA
        # ==========================================
        print("\n8. Agregando configuración de moneda...")
        cursor = conn.cursor()
        cursor.execute("SELECT clave FROM configuracion WHERE clave IN ('moneda_principal', 'tasa_cambio', 'moneda_secundaria')")
        config_existentes = [row[0] for row in cursor.fetchall()]
        
        if 'moneda_principal' not in config_existentes:
            ejecutar_sql(conn, """
                INSERT OR IGNORE INTO configuracion (clave, valor) VALUES ('moneda_principal', 'CUP')
            """)
            print("   ✓ Moneda principal configurada (CUP)")
        else:
            print("   ⚠ Moneda principal ya configurada")
        
        if 'moneda_secundaria' not in config_existentes:
            ejecutar_sql(conn, """
                INSERT OR IGNORE INTO configuracion (clave, valor) VALUES ('moneda_secundaria', 'MLC')
            """)
            print("   ✓ Moneda secundaria configurada (MLC)")
        else:
            print("   ⚠ Moneda secundaria ya configurada")
        
        if 'tasa_cambio' not in config_existentes:
            ejecutar_sql(conn, """
                INSERT OR IGNORE INTO configuracion (clave, valor) VALUES ('tasa_cambio', '1')
            """)
            print("   ✓ Tasa de cambio configurada (1)")
        else:
            print("   ⚠ Tasa de cambio ya configurada")
        
        # ==========================================
        # 9. CAMPO EN MOVIMIENTOS DE INVITARIO (Proveedor)
        # ==========================================
        print("\n9. Agregando campo proveedor_id a movimientos_inventario...")
        if not verificar_columna_existe(conn, 'movimientos_inventario', 'proveedor_id'):
            ejecutar_sql(conn, "ALTER TABLE movimientos_inventario ADD COLUMN proveedor_id INTEGER REFERENCES proveedores(id)")
            print("   ✓ Campo proveedor_id agregado a movimientos_inventario")
        else:
            print("   ⚠ Campo proveedor_id ya existe en movimientos_inventario")
        
        conn.commit()
        
        print("\n" + "=" * 70)
        print("Migración completada exitosamente!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\nERROR durante la migración: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    main()
