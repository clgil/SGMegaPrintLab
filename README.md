# SGMegaPrintLab

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-Lightweight-orange.svg)
![License](https://img.shields.io/badge/License-Internal-red.svg)

**Sistema de Gestión para Taller de Reparación y Mantenimiento de Impresoras**

*Adaptado a la realidad cubana - Junio 2026*

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
install.bat
```

#### En Linux

```bash
# Abrir terminal en la carpeta del proyecto
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
| **Contraseña** | `Taller2026` |

> 🔒 **Recomendación de Seguridad**: Cambie la contraseña inmediatamente después del primer acceso.

### Módulos Disponibles

#### 📊 Panel de Control
- Vista general de órdenes activas
- Alertas de stock bajo en tiempo real
- Ingresos del mes actual
- Gráficos de ingresos mensuales
- Filtros por período (hoy, este mes, este año, personalizado)

#### 📋 Órdenes de Reparación
- Creación de órdenes con numeración automática (OT-AA-0001)
- Asignación de técnicos responsables
- Registro detallado de piezas utilizadas
- Cálculo automático de costos (mano de obra + piezas)
- Flujo de estados: Recibido → Diagnóstico → Reparación → Listo → Entregado
- Generación e impresión de recibos

#### 👥 Clientes
- Registro de clientes con clasificación:
  - Particular
  - Empresa estatal
  - Cuentapropista
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

#### 💾 Respaldo y Restauración
- Crear copia de seguridad de la base de datos
- Restaurar desde respaldo anterior
- Configurar datos del taller para impresiones
- Procedimiento simplificado para USB

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
│
└── taller_impresoras/       # Directorio principal de la aplicación
    ├── app.py               # Punto de entrada (Flask)
    ├── models.py            # Modelos de base de datos
    ├── requirements.txt     # Dependencias de Python
    ├── install.bat          # Script de instalación (Windows)
    ├── install.sh           # Script de instalación (Linux)
    │
    ├── routes/              # Módulos de rutas
    │   ├── auth.py          # Autenticación de usuarios
    │   ├── clientes.py      # Gestión de clientes
    │   ├── dispositivos.py  # Gestión de dispositivos
    │   ├── ordenes.py       # Órdenes de reparación
    │   ├── inventario.py    # Inventario de piezas
    │   ├── tecnicos.py      # Gestión de técnicos
    │   ├── reportes.py      # Reportes y estadísticas
    │   └── backup.py        # Respaldo y restauración
    │
    ├── static/              # Archivos estáticos
    │   ├── css/             # Hojas de estilo
    │   └── js/              # JavaScript del frontend
    │
    ├── templates/           # Plantillas HTML
    │   ├── base.html        # Layout principal
    │   ├── dashboard.html   # Panel de control
    │   ├── login.html       # Inicio de sesión
    │   ├── clientes/        # Plantillas de clientes
    │   ├── dispositivos/    # Plantillas de dispositivos
    │   ├── ordenes/         # Plantillas de órdenes
    │   ├── inventario/      # Plantillas de inventario
    │   ├── tecnicos/        # Plantillas de técnicos
    │   └── reportes/        # Plantillas de reportes
    │
    ├── instance/            # Base de datos SQLite (auto-generada)
    │   └── taller.db
    │
    └── backup/              # Respaldos de base de datos
```

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

---

## 🔐 Seguridad

- ✅ Contraseñas almacenadas con hash **bcrypt**
- ✅ Sesiones protegidas con clave secreta configurable
- ✅ Protección contra CSRF en formularios
- ✅ Validación de entrada de datos
- ✅ Control de acceso basado en roles

### Cambio de Contraseña de Administrador

**Método 1**: Desde la interfaz (en desarrollo)

**Método 2**: Vía consola de Python:
```python
from app import app, db
from models import Usuario
from werkzeug.security import generate_password_hash

with app.app_context():
    user = Usuario.query.filter_by(usuario='admin').first()
    user.password_hash = generate_password_hash('NuevaContraseña')
    db.session.commit()
    print("Contraseña actualizada exitosamente")
```

---

## 📝 Dependencias Principales

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| Flask | 3.0.0 | Framework web |
| Flask-SQLAlchemy | 3.1.1 | ORM de base de datos |
| Flask-Login | 0.6.3 | Gestión de sesiones |
| bcrypt | 4.1.2 | Hash de contraseñas |
| Werkzeug | 3.0.1 | Utilidades web |
| python-dotenv | 1.0.0 | Variables de entorno |
| reportlab | 5.0.0 | Generación de PDFs |

---

## 📞 Soporte y Mantenimiento

Este sistema es **autocontenido** y está diseñado para operar sin soporte externo. El código fuente está completamente comentado en español para facilitar modificaciones o ampliaciones por parte del personal técnico del taller.

### Para Personal Técnico

- Revise los archivos en `routes/` para entender la lógica de cada módulo
- Los modelos de datos están definidos en `models.py`
- Las plantillas HTML utilizan Jinja2 como motor de renderizado

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
