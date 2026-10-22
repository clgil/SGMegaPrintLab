# SGMegaPrintLab

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-Lightweight-orange.svg)
![License](https://img.shields.io/badge/License-Internal-red.svg)

**Sistema de Gestión para Taller de Reparación y Mantenimiento de Impresoras**

*Adaptado a la realidad cubana - Junio 2026*

> 🚀 **¿Quieres instalarlo o desplegarlo?** Consulta la guía completa con instrucciones exactas y explicadas: **[DESPLEGAR.md](DESPLEGAR.md)** (instalación local en Windows/Linux, despliegue en hosting con Gunicorn + Nginx + systemd, actualizaciones seguras con `flask db upgrade` y respaldos).

[Características](#-características-principales) • [Instalación](#-instalación) • [Uso](#-uso-del-sistema) • [Módulos](#-módulos-disponibles) • [Documentación](#-documentación)

</div>

---

## 📋 Descripción

SGMegaPrintLab es un sistema informático **100% offline** diseñado para automatizar la gestión integral de talleres independientes de reparación y mantenimiento de impresoras. Desarrollado específicamente para las condiciones operativas, económicas y logísticas de Cuba, ofrece una solución robusta, ligera y fácil de usar.

### 🎯 Objetivos

- Automatizar el flujo de trabajo del taller
- Controlar inventario de piezas y consumibles
- Gestionar órdenes de servicio de principio a fin
- Generar reportes financieros y operativos
- Funcionar sin conexión a Internet
- Operar en equipos con recursos limitados

---

## ✨ Características Principales

| Característica | Descripción |
|---------------|-------------|
| 🌐 **100% Offline** | No requiere conexión a Internet para funcionar |
| 💾 **Bajos Recursos** | Funciona en equipos con 1-4 GB de RAM |
| 🗄️ **SQLite** | Base de datos ligera, portable y sin configuración |
| 🖥️ **Interfaz Simple** | Botones grandes, navegación clara e intuitiva |
| 💰 **Moneda CUP** | Todos los precios en pesos cubanos |
| 🔒 **Respaldo USB** | Copia de seguridad sencilla en memoria externa |
| 📊 **Reportes CSV** | Exportación de datos para análisis externo |
| 🔐 **Seguridad** | Contraseñas con hash bcrypt y sesiones protegidas |

---

## 🛠️ Requisitos del Sistema

### Hardware Mínimo

| Componente | Requisito | Recomendado |
|-----------|-----------|-------------|
| **Procesador** | Intel Core i3 / AMD equivalente | Intel Core i5 o superior |
| **RAM** | 1 GB | 2-4 GB |
| **Almacenamiento** | 500 MB libres | 1 GB o más |
| **Resolución** | 1024x768 | 1366x768 o superior |

### Software

- **Python**: 3.8 o superior
- **Sistema Operativo**: 
  - Windows 7/10/11
  - Linux (Ubuntu, Nova)
- **Navegador**: Chrome, Firefox, Edge (para interfaz web)

---

## 📦 Instalación

### Opción Rápida (Recomendada)

#### En Windows

```batch
# Abrir CMD o PowerShell en la carpeta del proyecto
cd taller_impresoras
install.bat
```

#### En Linux

```bash
# Abrir terminal en la carpeta del proyecto
cd taller_impresoras
chmod +x install.sh
./install.sh
```

Los scripts automáticos realizarán:
1. ✅ Verificación de Python instalado
2. ✅ Creación de entorno virtual
3. ✅ Instalación de dependencias
4. ✅ Inicialización de base de datos
5. ✅ Inicio del servidor

### Instalación Manual

```bash
# 1. Navegar al directorio del proyecto
cd taller_impresoras

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Configurar variables de entorno (opcional pero recomendado)
cp ../.env.example .env
# Editar .env y establecer SECRET_KEY segura

# 6. Iniciar la aplicación
python app.py
```

### Configuración de Variables de Entorno

Para entornos de producción, configure un archivo `.env` basado en `.env.example`:

```env
SECRET_KEY=tu-clave-secreta-muy-segura-aqui
FLASK_ENV=production
FLASK_DEBUG=False
DATABASE_URL=sqlite:///taller.db
```

> ⚠️ **Importante**: Nunca haga commit del archivo `.env` real. Use siempre `.env.example` como plantilla.

---

## 🚀 Uso del Sistema

### Acceso Inicial

1. Abra su navegador web preferido
2. Navegue a: `http://localhost:5000`
3. Inicie sesión con las credenciales por defecto:

| Campo | Valor |
|-------|-------|
| **Usuario** | `admin` |
| **Contraseña** | `admin123` |

> 🔒 **Recomendación de Seguridad**: Cambie la contraseña inmediatamente después del primer acceso (menú lateral → **Cambiar Clave**). La contraseña por defecto `admin123` reemplazó a la anterior `Taller2026` desde octubre de 2026.

### Módulos Disponibles

#### 📊 Panel de Control
- Vista general de órdenes activas
- Alertas de stock bajo en tiempo real
- Ingresos del mes actual
- Gráficos de ingresos mensuales
- Filtros por período (hoy, este mes, este año, personalizado)
- Estadísticas diferenciadas por rol (administrador, técnico, proveedor, cliente)

#### 📋 Órdenes de Reparación
- Creación de órdenes con numeración automática (OT-AA-0001)
- Asignación de técnicos responsables
- Registro detallado de piezas utilizadas
- Cálculo automático de costos (mano de obra + piezas)
- Flujo de estados: Recibido → Diagnóstico → Reparación → Listo → Entregado
- Generación e impresión de recibos
- Notas internas en órdenes
- Reingresos por garantía

#### 👥 Clientes
- Registro de clientes con clasificación:
  - TCP (Trabajador por Cuenta Propia)
  - Mypyme
  - PDL (Persona con Derecho a Lucro)
  - Empresa Estatal
  - CNA (Cooperativa No Agropecuaria)
  - CPA (Cooperativa de Producción Agropecuaria)
  - Persona natural
- Búsqueda rápida por nombre o teléfono
- Historial completo de dispositivos y órdenes
- Información de contacto detallada

#### 🖨️ Dispositivos
- Registro de impresoras por cliente
- Tipos soportados:
  - Láser
  - Inyección de tinta
  - Matricial
  - Multifuncional
- Historial de problemas frecuentes
- Especificaciones técnicas del equipo

#### 📦 Inventario
- Catálogo completo de piezas y consumibles
- Control de stock con alertas de mínimo configurable
- Entradas y salidas automáticas vinculadas a órdenes
- Categorías personalizables
- Historial detallado de movimientos
- Gestión de proveedores

#### 🔧 Técnicos
- Registro de técnicos del taller
- Asignación a órdenes de reparación
- Seguimiento de carga de trabajo

#### 📈 Reportes
- Ingresos por período (exportable a CSV)
- Órdenes por estado y técnico
- Piezas más utilizadas
- Clientes activos y frecuencia de servicio
- Gastos operativos
- Tributos calculados (ISIP, seguridad social)

#### 🤝 Contratos de Mantenimiento
- Gestión de contratos recurrentes con clientes
- Frecuencias configurables (semanal, quincenal, mensual, trimestral)
- Seguimiento de visitas programadas
- Alertas de mantenimientos próximos

#### 👥 Usuarios
- Administración de usuarios del sistema
- Roles: administrador, técnico, proveedor, cliente
- Control de acceso basado en permisos
- Activación/desactivación de usuarios

#### 💾 Respaldo y Restauración
- Crear copia de seguridad de la base de datos
- Restaurar desde respaldo anterior
- Configurar datos del taller para impresiones
- Procedimiento simplificado para USB

#### 📝 Auditoría (solo administradores)
- Bitácora anti-fraude de todas las acciones sobre los datos (`/admin/auditoria`)
- Registro automático de creación, edición y eliminación por tabla
- Solo lectura desde la interfaz: nadie puede borrar sus propios rastros
- Filtros por usuario, tabla afectada y rango de fechas
- Purga de registros antiguos solo por línea de comandos (`flask purge-audit-log`)

#### ❓ Ayuda contextual
- Documentación de uso integrada por módulo (`/ayuda`)

#### 📱 PWA / Acceso móvil
- Manifiest PWA e instalable como aplicación en el teléfono
- Service Worker para uso offline de la interfaz
- Interfaz responsive para tablets y móviles

---

## 🔄 Procedimiento de Respaldo y Restauración

### Crear Respaldo

1. Navegue al módulo **"Respaldo"** en el menú lateral
2. Haga clic en **"Crear Respaldo"**
3. El sistema generará un archivo `taller_backup_YYYYMMDD_HHMMSS.db`
4. Copie este archivo a una memoria USB para mayor seguridad

### Restaurar Respaldo

1. Vaya al módulo **"Respaldo"**
2. Seleccione **"Restaurar Respaldo"**
3. Elija el archivo `.db` de respaldo deseado
4. Confirme la operación (se creará un respaldo automático previo)

> ⚡ **Consejo**: Realice respaldos regularmente, especialmente antes de actualizaciones o en zonas con inestabilidad eléctrica frecuente.

---

## 📁 Estructura del Proyecto

```
workspace/
├── .env.example              # Plantilla de variables de entorno
├── .gitignore               # Archivos ignorados por Git
├── LICENSE                  # Licencia del proyecto
├── README.md                # Este archivo
├── SECURITY.md              # Políticas de seguridad
├── PULL_REQUEST.md          # Guía para contribuciones
├── DESPLEGAR.md             # Guía completa de instalación y despliegue
├── INSTRUCCIONES_PRUEBAS_MOVIL.md  # Pruebas de acceso móvil/PWA
│
└── taller_impresoras/       # Directorio principal de la aplicación
    ├── app.py               # Punto de entrada (factory create_app + CLI)
    ├── models.py            # Modelos de BD, auditoría y helpers de fechas
    ├── requirements.txt     # Dependencias de Python
    ├── install.bat          # Script de instalación (Windows)
    ├── install.sh           # Script de instalación (Linux)
    ├── migrate.py           # Migración histórica de columnas (legado)
    ├── migracion_finanzas.py# Migración histórica de gastos/tributos (legado)
    │
    ├── config/              # Configuración por entorno
    │   └── __init__.py      # Development / Production / Testing
    │
    ├── services/            # Lógica de negocio y extensiones
    │   ├── extensions.py    # db, login_manager, migrate (Flask-Migrate)
    │   ├── dashboard_service.py  # Estadísticas del panel
    │   └── pdf_service.py   # Generación de PDFs (fpdf2 + DejaVu Sans)
    │
    ├── migrations/          # Migraciones Alembic (esquema de BD versionado)
    │   └── versions/        # esquema inicial + audit_log
    │
    ├── routes/              # Módulos de rutas (blueprints)
    │   ├── auth.py          # Autenticación, registro, cambio de clave
    │   ├── clientes.py      # Gestión de clientes
    │   ├── dispositivos.py  # Gestión de dispositivos
    │   ├── ordenes.py       # Órdenes de reparación
    │   ├── inventario.py    # Inventario de piezas
    │   ├── tecnicos.py      # Gestión de técnicos
    │   ├── reportes.py      # Reportes, finanzas y exportación CSV/PDF
    │   ├── backup.py        # Respaldo y restauración
    │   ├── proveedores.py   # Gestión de proveedores
    │   ├── contratos.py     # Contratos de mantenimiento
    │   ├── usuarios.py      # Gestión de usuarios
    │   ├── auditoria.py     # Bitácora de auditoría (solo admin)
    │   ├── decorators.py    # Decoradores de roles (@rol_requerido)
    │   ├── validators.py    # Validadores de datos
    │   └── ayuda/           # Módulo de ayuda contextual
    │
    ├── static/              # Archivos estáticos
    │   ├── css/             # Hojas de estilo
    │   ├── js/              # JavaScript del frontend
    │   ├── fonts/           # Fuentes DejaVu Sans (PDFs Unicode)
    │   ├── icons/           # Íconos PWA
    │   ├── uploads/         # Archivos subidos
    │   ├── manifest.json    # Manifiesto PWA
    │   └── sw.js            # Service Worker (offline)
    │
    ├── templates/           # Plantillas HTML
    │   ├── base.html        # Layout principal
    │   ├── dashboard.html   # Panel de control
    │   ├── login.html       # Inicio de sesión
    │   ├── error.html       # Páginas de error
    │   ├── macros.html      # Macros reutilizables
    │   ├── auth/            # Plantillas de autenticación
    │   ├── clientes/        # Plantillas de clientes
    │   ├── dispositivos/    # Plantillas de dispositivos
    │   ├── ordenes/         # Plantillas de órdenes
    │   ├── inventario/      # Plantillas de inventario
    │   ├── tecnicos/        # Plantillas de técnicos
    │   ├── reportes/        # Plantillas de reportes
    │   ├── proveedores/     # Plantillas de proveedores
    │   ├── contratos/       # Plantillas de contratos
    │   ├── usuarios/        # Plantillas de usuarios
    │   ├── auditoria/       # Plantillas de auditoría
    │   ├── backup/          # Plantillas de respaldo
    │   └── ayuda/           # Plantillas de ayuda
    │
    └── instance/            # Base de datos SQLite (auto-generada)
        └── taller.db
```

### Comandos CLI disponibles

Ejecutados desde `taller_impresoras/` con el entorno virtual activado:

| Comando | Descripción |
|---------|-------------|
| `flask db upgrade` | Aplica el esquema/migraciones de la base de datos (Alembic) |
| `flask init-db` | Crea los datos iniciales (admin por defecto, configuración tributaria). Ya **no** crea tablas |
| `flask crear-usuario` | Crea un usuario desde la terminal (útil para restablecer accesos) |
| `flask purge-audit-log --dias N [--si]` | Purga la bitácora de auditoría más antigua a N días (única vía de borrado) |
| `flask fix-dates [--dry-run]` | Convierte fechas históricas en texto a tipos date/datetime nativos |

---

## 🔧 Solución de Problemas Comunes

### La aplicación no inicia

1. Verifique que Python 3.8+ esté instalado:
   ```bash
   python --version
   ```
2. Asegúrese de que el entorno virtual esté activado
3. Reinstale las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

### Error de base de datos

1. Elimine el archivo `instance/taller.db`
2. Reinicie la aplicación (se creará automáticamente)
3. Restaure desde un respaldo si tiene datos importantes

### Puerto ya en uso

El puerto 5000 está siendo utilizado por otra aplicación. Soluciones:

**Opción A**: Cambiar el puerto en `app.py`:
```python
app.run(host='127.0.0.1', port=5001, debug=False)
```

**Opción B**: Liberar el puerto 5000:
- Windows: `netstat -ano | findstr :5000` y matar el proceso
- Linux: `sudo lsof -ti:5000 | xargs kill`

### Dependencias no se instalan

Actualice pip e intente nuevamente:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### WeasyPrint no se instala correctamente (Linux)

> ℹ️ **Actualización octubre 2026**: WeasyPrint fue **eliminado** del proyecto. La generación de PDFs usa únicamente **fpdf2** (Python puro), por lo que este error **ya no debería ocurrir** y **no se requieren dependencias nativas** (`libpango`, `libharfbuzz`, etc.). Este apartado queda solo como referencia para instalaciones antiguas:

```bash
# (Obsoleto) Ubuntu/Debian
sudo apt-get install libpango1.0-dev libharfbuzz-dev libffi-dev

# (Obsoleto) Fedora
sudo dnf install pango-devel harfbuzz-devel libffi-devel
```

---

## 🔐 Seguridad

- ✅ Contraseñas almacenadas con hash **bcrypt**
- ✅ Sesiones protegidas con clave secreta configurable
- ✅ Protección contra CSRF en formularios
- ✅ Validación de entrada de datos
- ✅ Control de acceso basado en roles
- ✅ Decoradores de permisos por ruta

### Cambio de Contraseña de Administrador

**Método 1**: Desde la interfaz: inicie sesión → menú lateral → **Cambiar Clave** (ruta `/auth/cambiar_password`).

**Método 2**: Vía consola de Python (si perdió el acceso):
```python
from app import create_app
from services.extensions import db
from models import Usuario

app = create_app()
with app.app_context():
    user = Usuario.query.filter_by(usuario='admin').first()
    user.set_password('NuevaContraseña')   # aplica hash automáticamente
    db.session.commit()
    print("Contraseña actualizada exitosamente")
```

**Método 3**: Cree un usuario administrativo nuevo desde la terminal:
```bash
flask crear-usuario --nombre "Admin" --usuario admin2 --rol administrador
```

---

## 📝 Dependencias Principales

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| Flask | 3.0.0 | Framework web |
| Flask-SQLAlchemy | 3.1.1 | ORM de base de datos |
| Flask-Migrate | 4.1.0 | Migraciones de esquema (comandos `flask db`) |
| alembic | 1.16.5 | Motor de migraciones subyacente |
| Mako | 1.3.10 | Plantillas de Alembic |
| Flask-Login | 0.6.3 | Gestión de sesiones |
| bcrypt | 4.1.2 | Hash de contraseñas |
| Werkzeug | 3.0.1 | Utilidades web |
| python-dotenv | 1.0.0 | Variables de entorno |
| fpdf2 | 2.8.7 | Generación de PDFs (única librería de PDF del proyecto) |

> ℹ️ **Nota (octubre 2026)**: `reportlab` y `WeasyPrint` fueron **eliminados** de las dependencias. Toda la generación de PDFs (recibos de órdenes y reportes) se centralizó en `services/pdf_service.py` usando exclusivamente **fpdf2** (Python puro, sin dependencias nativas del sistema).

---

## 📞 Soporte y Mantenimiento

Este sistema es **autocontenido** y está diseñado para operar sin soporte externo. El código fuente está completamente comentado en español para facilitar modificaciones o ampliaciones por parte del personal técnico del taller.

### Para Personal Técnico

- Revise los archivos en `routes/` para entender la lógica de cada módulo
- Los modelos de datos están definidos en `models.py`
- Las plantillas HTML utilizan Jinja2 como motor de renderizado
- Consulte la documentación adicional en `taller_impresoras/README.md`

---

## 📄 Licencia

Sistema desarrollado para **uso interno** de talleres independientes en Cuba.

---

## 🙏 Créditos

Desarrollado adaptándose a la realidad cubana - 2026

---

<div align="center">

**¿Necesitas ayuda?** Consulta la documentación interna en `taller_impresoras/README.md` o revisa los comentarios en el código fuente.

⌨️ Hecho con ❤️ para los talleres cubanos

</div>
