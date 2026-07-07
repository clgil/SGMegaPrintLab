"""
Script de migración para actualizar el campo tipo_cliente en la tabla clientes
Junio 2026

Este script actualiza los valores antiguos del campo tipo_cliente a los nuevos valores:
- 'Particular' -> 'Persona natural'
- 'Empresa estatal' -> 'Empresa Estatal'
- 'Cuentapropista' -> Se distribuye entre TCP, Mypyme, PDL según corresponda (por defecto: TCP)

También establece el valor por defecto como 'Persona natural' para registros NULL.
"""
import sqlite3
from pathlib import Path

# Ruta a la base de datos
DB_PATH = Path(__file__).parent / 'instance' / 'taller.db'

def migrar_tipo_cliente():
    """Ejecuta la migración del campo tipo_cliente"""
    
    if not DB_PATH.exists():
        print(f"Error: La base de datos no existe en {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clientes'")
        if not cursor.fetchone():
            print("Error: La tabla 'clientes' no existe")
            return False
        
        # Verificar si el campo tipo_cliente existe
        cursor.execute("PRAGMA table_info(clientes)")
        columnas = [col[1] for col in cursor.fetchall()]
        
        if 'tipo_cliente' not in columnas:
            print("Añadiendo columna tipo_cliente...")
            cursor.execute("ALTER TABLE clientes ADD COLUMN tipo_cliente TEXT DEFAULT 'Persona natural'")
            conn.commit()
            print("Columna tipo_cliente añadida correctamente")
        else:
            print("La columna tipo_cliente ya existe")
        
        # Actualizar valores antiguos a nuevos valores
        # Mapeo de conversión
        conversiones = {
            'Particular': 'Persona natural',
            'Empresa estatal': 'Empresa Estatal',
            'cuentapropista': 'TCP',  # Por defecto, se puede ajustar manualmente después
        }
        
        for antiguo, nuevo in conversiones.items():
            cursor.execute("""
                UPDATE clientes 
                SET tipo_cliente = ? 
                WHERE LOWER(tipo_cliente) = LOWER(?) AND tipo_cliente IS NOT NULL
            """, (nuevo, antiguo))
            filas_afectadas = cursor.rowcount
            if filas_afectadas > 0:
                print(f"Actualizados {filas_afectadas} registros de '{antiguo}' a '{nuevo}'")
        
        # Establecer valor por defecto para registros NULL o vacíos
        cursor.execute("""
            UPDATE clientes 
            SET tipo_cliente = 'Persona natural' 
            WHERE tipo_cliente IS NULL OR tipo_cliente = ''
        """)
        filas_nulas = cursor.rowcount
        if filas_nulas > 0:
            print(f"Establecido 'Persona natural' para {filas_nulas} registros sin tipo")
        
        # Validar que todos los valores sean correctos
        cursor.execute("SELECT DISTINCT tipo_cliente FROM clientes WHERE tipo_cliente IS NOT NULL")
        valores_actuales = [row[0] for row in cursor.fetchall()]
        valores_validos = ['TCP', 'Mypyme', 'PDL', 'Empresa Estatal', 'CNA', 'CPA', 'Persona natural']
        
        valores_invalidos = [v for v in valores_actuales if v not in valores_validos]
        if valores_invalidos:
            print(f"\nAdvertencia: Existen valores no válidos en la base de datos: {valores_invalidos}")
            print("Estos registros deberán ser corregidos manualmente.")
        else:
            print("\nTodos los valores de tipo_cliente son válidos")
        
        conn.commit()
        print("\n=== Migración completada exitosamente ===")
        
        # Mostrar resumen
        cursor.execute("SELECT tipo_cliente, COUNT(*) as cantidad FROM clientes GROUP BY tipo_cliente ORDER BY cantidad DESC")
        print("\nResumen de tipos de cliente:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]} registros")
        
        return True
        
    except Exception as e:
        print(f"Error durante la migración: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == '__main__':
    print("=" * 60)
    print("Migración de campo tipo_cliente")
    print("=" * 60)
    migrar_tipo_cliente()
