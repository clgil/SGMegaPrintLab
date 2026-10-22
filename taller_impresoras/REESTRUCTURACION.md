# Estructura del Proyecto Reestructurado

## Nueva Organización de Archivos

```
taller_impresoras/
├── app.py                      # Punto de entrada principal (refactorizado con factory pattern)
├── models.py                   # Modelos de base de datos (sin cambios mayores)
├── config/                     # Configuración de la aplicación
│   ├── __init__.py            # Clases de configuración (Development, Production, Testing)
│   └── settings.py            # (Opcional) Configuraciones adicionales
├── services/                   # Lógica de negocio y servicios
│   ├── __init__.py
│   ├── extensions.py          # Extensiones de Flask (db, login_manager)
│   └── dashboard_service.py   # Servicio para estadísticas del dashboard
├── routes/                     # Blueprints de rutas
│   ├── __init__.py            # Registro centralizado de blueprints
│   ├── auth.py                # Autenticación
│   ├── clientes.py            # Gestión de clientes
│   ├── dispositivos.py        # Gestión de dispositivos
│   ├── ordenes.py             # Gestión de órdenes
│   ├── inventario.py          # Gestión de inventario
│   ├── usuarios.py            # Gestión de usuarios
│   ├── tecnicos.py            # Gestión de técnicos
│   ├── proveedores.py         # Gestión de proveedores
│   ├── contratos.py           # Gestión de contratos
│   ├── reportes.py            # Reportes
│   ├── backup.py              # Backup y restauración
│   ├── decorators.py          # Decoradores personalizados
│   ├── validators.py          # Validadores
│   └── ayuda/                 # Módulo de ayuda
│       ├── __init__.py
│       └── ayuda.py
├── utils/                      # Utilidades y funciones helper
│   ├── __init__.py
│   └── helpers.py             # Funciones utilitarias comunes
├── migrations/                 # Migraciones de base de datos (futuro)
│   └── __init__.py
├── static/                     # Archivos estáticos (CSS, JS, imágenes)
├── templates/                  # Plantillas Jinja2
├── instance/                   # Instancia de la aplicación (SQLite, uploads)
├── backup/                     # Archivos de backup
├── requirements.txt            # Dependencias
└── README.md                   # Documentación
```

## Cambios Principales Realizados

### 1. **Factory Pattern para la Aplicación Flask**
   - Se implementó `create_app()` en `app.py` para permitir múltiples instancias de la aplicación
   - Facilita las pruebas y diferentes configuraciones por entorno

### 2. **Configuración Modular** (`config/`)
   - Separación de configuraciones por entorno (development, production, testing)
   - Uso de variables de entorno para configuración sensible
   - Advertencias de seguridad automáticas en producción

### 3. **Servicios de Negocio** (`services/`)
   - `extensions.py`: Centraliza la inicialización de extensiones de Flask (db, login_manager)
   - `dashboard_service.py`: Encapsula la lógica de negocio para estadísticas, separándola de las rutas
   - Permite mejor testabilidad y reutilización de código

### 4. **Blueprints Centralizados** (`routes/__init__.py`)
   - Registro centralizado de todos los blueprints
   - Mejor organización y visibilidad de las rutas disponibles

### 5. **Utilidades Comunes** (`utils/helpers.py`)
   - Funciones helper reutilizables
   - Reduce código duplicado en diferentes módulos

### 6. **Separación de Responsabilidades**
   - **Models**: Solo definición de esquemas de base de datos
   - **Services**: Lógica de negocio y reglas
   - **Routes**: Manejo de requests y responses
   - **Config**: Configuración de la aplicación

## Beneficios de la Reestructuración

1. **Mantenibilidad**: Código más fácil de mantener y entender
2. **Testabilidad**: Componentes aislados facilitan las pruebas unitarias
3. **Escalabilidad**: Nueva funcionalidad se agrega en módulos específicos
4. **Seguridad**: Configuración separada por entornos
5. **Reutilización**: Servicios y utilidades compartidas
6. **Claridad**: Cada módulo tiene una responsabilidad única

## Comandos CLI Disponibles

```bash
# Aplicar el esquema de base de datos (Flask-Migrate/Alembic) — necesario la primera vez
flask db upgrade

# Inicializar datos por defecto (admin/admin123 + configuración tributaria).
# NOTA: init-db ya NO crea tablas; requiere `flask db upgrade` previo.
flask init-db

# Crear usuario
flask crear-usuario

# Purgar bitácora de auditoría más antigua a N días (única vía de borrado)
flask purge-audit-log --dias 365

# Normalizar fechas históricas en texto a tipos date/datetime nativos
flask fix-dates [--dry-run]

# Ejecutar aplicación
python app.py
```

## Migración desde la Versión Anterior

La aplicación mantiene compatibilidad con:
- La misma base de datos SQLite
- Las mismas plantillas HTML
- Los mismos archivos estáticos
- Las mismas rutas URL

No se requieren cambios en la base de datos o en las plantillas existentes.

## Próximos Pasos Sugeridos

1. Implementar tests unitarios para los servicios
2. ~~Agregar migraciones de base de datos con Flask-Migrate~~ ✅ **Implementado**: `migrations/` con Alembic (esquema inicial `112a730df0d5` + auditoría `b7c31d92e4a1`); el esquema se aplica con `flask db upgrade` y `init-db` solo crea datos
3. Documentar API interna de los servicios
4. Considerar mover validadores a `utils/validators.py`
5. Implementar logging estructurado

## Novedades Consolidadas (octubre 2026)

- **Auditoría anti-fraude**: modelo `AuditLog`, blueprint `routes/auditoria.py` (`/admin/auditoria`, solo administrador, solo lectura) y comando `flask purge-audit-log`.
- **Servicio PDF centralizado**: `services/pdf_service.py` exclusivamente con fpdf2 (reportlab y WeasyPrint eliminados).
- **PWA**: `static/manifest.json`, `static/sw.js` e íconos instalables.
- **Contraseña por defecto**: `admin` / `admin123` (antes `Taller2026`).
- **Nota**: la carpeta `utils/` propuesta originalmente no llegó a materializarse; los helpers viven en `models.py` (fechas) y `routes/validators.py` (validaciones).
