# Actualización Financiera - Taller de Impresoras

Esta actualización añade funcionalidades financieras avanzadas adaptadas al régimen tributario cubano para trabajadores por cuenta propia (autónomos).

## 📋 Nuevas Funcionalidades

### 1. Panel Financiero en Dashboard
- **Inversión en piezas**: Costo de ventas del período seleccionado
- **Valor del inventario**: Valor actual del stock (cantidad × costo)
- **Ingresos brutos**: Total facturado en el período
- **Ganancia neta**: Ingresos - piezas - gastos operativos

### 2. Filtros Temporales
Selector de período en el dashboard con opciones:
- Hoy
- Este Mes (por defecto)
- Este Año
- Personalizado (rango de fechas específico)

### 3. Cálculo de Tributos Cubanos
Estimación de impuestos según el régimen general de autónomos:

**ISIP (Impuesto sobre Ingresos Personales)** - Escala progresiva:
| Tramo de Ganancia Acumulada (CUP) | Tasa |
|-----------------------------------|------|
| Hasta 10,000                      | 5%   |
| De 10,001 a 20,000                | 10%  |
| De 20,001 a 30,000                | 15%  |
| De 30,001 a 40,000                | 20%  |
| De 40,001 a 50,000                | 25%  |
| Más de 50,000                     | 30%  |

**Seguridad Social**: 5% sobre la ganancia (configurable)

**Régimen Simplificado**: Opción de cuota fija mensual configurable

### 4. Gestión de Gastos Operativos
Nueva tabla `gastos` para registrar:
- Electricidad
- Agua
- Alquiler
- Otros gastos en efectivo

La ganancia neta se calcula restando estos gastos operativos.

## 🚀 Instrucciones de Instalación

### Paso 1: Aplicar la migración

Ejecuta el script de migración desde la carpeta del proyecto:

```bash
cd /workspace/taller_impresoras
python3 migracion_finanzas.py
```

Este script:
1. Crea la tabla `gastos` si no existe
2. Inserta la configuración tributaria por defecto
3. Verifica que todo esté correcto

### Paso 2: Reiniciar la aplicación

Si tienes el servidor en ejecución, reinícialo:

```bash
# Detener (Ctrl+C si está en foreground)
# Luego iniciar nuevamente
python3 app.py
```

## 📁 Archivos Modificados/Creados

### Modelos (`models.py`)
- Añadida clase `Gasto` para gastos operativos

### Aplicación Principal (`app.py`)
- Ruta `/` (dashboard) ampliada con métricas financieras y cálculo de tributos
- Configuración tributaria por defecto en inicialización

### Rutas de Reportes (`routes/reportes.py`)
- Nueva ruta `/gastos` - Gestión de gastos operativos
- Nueva ruta `/gastos/eliminar/<id>` - Eliminar gasto
- Nueva ruta `/finanzas/configuracion` - Configuración tributaria

### Templates
- `templates/dashboard.html` - Rediseñado con panel financiero completo
- `templates/base.html` - Menú actualizado ("Reportes y Finanzas")
- `templates/reportes/index.html` - Página principal de reportes actualizada
- `templates/reportes/gastos.html` - Gestión de gastos (NUEVO)
- `templates/reportes/config_financiera.html` - Configuración tributaria (NUEVO)

### Scripts
- `migracion_finanzas.py` - Script de migración (NUEVO)

## 🔧 Configuración Tributaria

Para acceder a la configuración:

1. Ir a **Reportes y Finanzas** en el menú
2. Click en **Configuración Tributaria**
3. Modificar los parámetros según necesite:
   - Tipo de régimen (General/Simplificado)
   - Cuota fija mensual (si es simplificado)
   - Tasas ISIP por tramo
   - Porcentaje de seguridad social
   - Base de cálculo para seguridad social

## 📊 Uso del Dashboard Financiero

### Filtrar por Período

1. En la parte superior del dashboard, seleccionar el período:
   - **Hoy**: Métricas del día actual
   - **Este Mes**: Desde el día 1 hasta hoy
   - **Este Año**: Desde enero 1 hasta hoy
   - **Personalizado**: Especificar fecha inicio y fin

2. Click en **Aplicar Filtro**

### Interpretar las Métricas

| Indicador | Descripción |
|-----------|-------------|
| Inversión en Piezas | Costo de las piezas usadas en órdenes entregadas |
| Valor Inventario | Valor actual del stock disponible |
| Ingresos Brutos | Total facturado en el período |
| Ganancia Neta | Ingresos - piezas - gastos operativos |
| ISIP | Impuesto estimado sobre ingresos personales |
| Seguridad Social | Contribución estimada |
| Total a Pagar | Suma de ISIP + Seguridad Social |

⚠️ **Nota**: Los cálculos de tributos son estimaciones basadas en la configuración. Siempre verificar con la normativa oficial vigente.

## 🗄️ Estructura de la Tabla `gastos`

```sql
CREATE TABLE gastos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descripcion TEXT NOT NULL,
    monto REAL NOT NULL,
    fecha TEXT NOT NULL DEFAULT (date('now','localtime'))
);
```

## 🔄 Compatibilidad

- ✅ Totalmente compatible con la instalación existente
- ✅ No modifica datos existentes
- ✅ Offline - sin dependencias externas
- ✅ Stack original: Python/Flask/SQLite/Bootstrap local

## 📞 Soporte

Para dudas o problemas con esta actualización, revisar:
1. Que la migración se haya ejecutado correctamente
2. Que todas las tablas existan en la base de datos
3. Que la configuración tributaria esté cargada

---

**Versión**: 2.0 - Módulo Financiero  
**Fecha**: Junio 2026  
**Adaptado para**: República de Cuba
