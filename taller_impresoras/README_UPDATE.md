# Actualización del Sistema de Gestión de Taller de Impresoras

## Fecha: Junio 2026

Esta actualización agrega nuevas funcionalidades al sistema existente, preservando la estructura actual y el rendimiento en equipos de bajos recursos.

## Funcionalidades Agregadas

### 1. Seguimiento de garantías y reingresos
- Campo `garantia_meses` en órdenes para definir duración de garantía
- Cálculo automático de fecha fin de garantía
- Detección de posibles casos de garantía (mismo dispositivo y problema similar)
- Vinculación de reingresos a órdenes originales
- Indicador en dashboard: "Reingresos en garantía este mes"
- Las órdenes de garantía no descuentan piezas del inventario

### 2. Gestión de proveedores
- Nueva tabla `proveedores` con campos: nombre, contacto, teléfono, tipo (formal/informal)
- Relación `proveedor_id` en tabla `piezas` (mantiene campo texto como respaldo)
- CRUD completo de proveedores
- Reporte de compras por proveedor

### 3. Contratos de mantenimiento periódico
- Nueva tabla `contratos` con frecuencias: semanal, quincenal, mensual, trimestral, semestral, anual
- Cálculo automático de próxima visita según frecuencia
- Lista de "Mantenimientos por vencer esta semana" en dashboard
- Registro de visitas realizadas

### 4. Control de tiempo y productividad de técnicos
- Campos `fecha_inicio_reparacion` y `fecha_fin_reparacion` en órdenes
- Cálculo automático de tiempo de reparación en horas
- Campo `costo_hora` en técnicos para cálculo de costo laboral

### 5. Alertas rápidas en dashboard
- Piezas bajo stock mínimo
- Órdenes estancadas (>3 días en "Recibido" o "En diagnóstico")
- Garantías próximas a vencer (próximos 7 días)
- Mantenimientos por vencer esta semana

### 6. Notas internas en órdenes
- Nueva tabla `orden_notas` con marca de tiempo y usuario
- Visualización cronológica en detalle de orden

### 7. Configuración de moneda dual
- Campos en configuración: `moneda_principal`, `moneda_secundaria`, `tasa_cambio`
- Preparado para reportes con conversión CUP/MLC/USD

## Instrucciones de Instalación

### Paso 1: Copiar archivos
Copie todos los archivos `.py` y plantillas HTML a su instalación existente, manteniendo la estructura de directorios:

```
taller_impresoras/
├── app.py (actualizado)
├── models.py (actualizado)
├── migrate.py (nuevo)
├── routes/
│   ├── proveedores.py (nuevo)
│   └── contratos.py (nuevo)
└── templates/
    ├── proveedores/ (nuevo)
    └── contratos/ (nuevo)
```

### Paso 2: Ejecutar migración de base de datos
```bash
cd taller_impresoras
python migrate.py
```

Este script:
- Crea las nuevas tablas (proveedores, contratos, orden_notas)
- Agrega los nuevos campos a tablas existentes
- Migra proveedores de texto a la nueva tabla
- Configura valores por defecto de moneda

### Paso 3: Verificar instalación
```bash
python -c "from app import app; print('OK')"
```

Si muestra "OK", la instalación fue exitosa.

### Paso 4: Iniciar la aplicación
```bash
python app.py
```

Acceda a http://127.0.0.1:5000

## Nuevas Rutas Disponibles

### Proveedores
- `/proveedores/` - Listado de proveedores
- `/proveedores/nuevo` - Crear proveedor
- `/proveedores/editar/<id>` - Editar proveedor
- `/proveedores/ver/<id>` - Ver detalle
- `/proveedores/api/lista` - API para selects dinámicos

### Contratos
- `/contratos/` - Listado de contratos
- `/contratos/nuevo` - Crear contrato
- `/contratos/editar/<id>` - Editar contrato
- `/contratos/ver/<id>` - Ver detalle con próxima visita
- `/contratos/registrar_visita/<id>` - Registrar visita realizada

## Cambios en la Base de Datos

### Nuevas Tablas
```sql
proveedores (id, nombre, contacto, telefono, tipo, activo, fecha_creacion)
contratos (id, cliente_id, descripcion, frecuencia, fecha_inicio, fecha_fin, activo, precio_mantenimiento, dispositivos_cubiertos, ultima_visita)
orden_notas (id, orden_id, texto, fecha_hora, usuario_id)
```

### Nuevos Campos en Tablas Existentes
```sql
ordenes: garantia_meses, fecha_fin_garantia, orden_original_id, es_reingreso, tipo_orden, fecha_inicio_reparacion, fecha_fin_reparacion
piezas: proveedor_id
tecnicos: costo_hora
movimientos_inventario: proveedor_id
configuracion: moneda_principal, moneda_secundaria, tasa_cambio
```

## Uso de las Nuevas Funcionalidades

### Garantías
1. Al editar una orden, establezca los meses de garantía
2. La fecha fin se calcula automáticamente al entregar
3. Si un cliente regresa con el mismo problema, el sistema detecta la garantía vigente
4. Marque la nueva orden como "Reingreso por garantía" para no cobrar nuevamente

### Proveedores
1. Registre proveedores formales o informales
2. Asocie proveedores a piezas en el inventario
3. Al registrar entradas, seleccione el proveedor

### Contratos de Mantenimiento
1. Cree un contrato con frecuencia definida
2. El sistema calcula automáticamente la próxima visita
3. Registre cada visita realizada
4. Revise en dashboard los mantenimientos por vencer

### Productividad de Técnicos
1. El tiempo de reparación se calcula automáticamente según cambios de estado
2. Configure costo por hora en cada técnico
3. Consulte reportes de productividad por período

## Consideraciones de Rendimiento

- Todas las consultas están optimizadas para SQLite
- Paginación implementada en listados largos
- Índices automáticos en claves foráneas
- No se requieren dependencias adicionales

## Soporte

Para problemas o preguntas, consulte la documentación interna o contacte al administrador del sistema.
