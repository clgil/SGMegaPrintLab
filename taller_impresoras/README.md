# Sistema de Gestión para Taller de Reparación y Mantenimiento de Impresoras

**Adaptado a la realidad cubana - Junio 2026**

## Descripción

Sistema informático offline para automatizar la gestión de un taller independiente de reparación y mantenimiento de impresoras. Diseñado específicamente para las condiciones operativas, económicas y logísticas de Cuba.

## Características Principales

- ✅ **100% Offline**: No requiere conexión a Internet
- ✅ **Bajos recursos**: Funciona en equipos con 1-4 GB RAM
- ✅ **SQLite**: Base de datos ligera y portable
- ✅ **Interfaz simple**: Botones grandes, navegación clara
- ✅ **Moneda CUP**: Precios en pesos cubanos
- ✅ **Respaldo USB**: Copia de seguridad sencilla

## Requisitos del Sistema

### Hardware
- PC de escritorio o portátil
- RAM: 1 GB mínimo (recomendado 2 GB)
- Almacenamiento: 500 MB libres
- Resolución: 1024x768 o superior

### Software
- Python 3.8 o superior
- Windows 7/10 o Linux (Ubuntu, Nova)

## Instalación

### En Windows

1. Abra una terminal (CMD o PowerShell) en la carpeta del proyecto
2. Ejecute el script de instalación:
   ```batch
   install.bat
   ```
3. El script hará lo siguiente:
   - Verificará que Python esté instalado
   - Creará un entorno virtual
   - Instalará las dependencias
   - Inicializará la base de datos
   - Iniciará el servidor

### En Linux

1. Abra una terminal en la carpeta del proyecto
2. Ejecute el script de instalación:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

### Instalación Manual

Si prefiere instalar manualmente:

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Iniciar la aplicación
python app.py
```

## Uso del Sistema

### Acceso Inicial

1. Abra su navegador web
2. Navegue a: `http://localhost:5000`
3. Inicie sesión con:
   - **Usuario**: `admin`
   - **Contraseña**: `Taller2026`

### Módulos Disponibles

#### 📊 Panel de Control
- Vista general de órdenes activas
- Alertas de stock bajo
- Ingresos del mes
- Gráfico de ingresos mensuales

#### 📋 Órdenes de Reparación
- Crear nuevas órdenes con número automático (OT-AA-0001)
- Asignar técnicos
- Registrar piezas utilizadas
- Calcular costos automáticamente
- Cambiar estados: Recibido → Diagnóstico → Reparación → Listo → Entregado
- Imprimir recibos

#### 👥 Clientes
- Registrar clientes (Particular, Empresa estatal, Cuentapropista)
- Buscar por nombre o teléfono
- Historial de dispositivos y órdenes

#### 🖨️ Dispositivos
- Registrar impresoras por cliente
- Tipos: Láser, Inyección, Matricial, Multifuncional
- Historial de problemas frecuentes

#### 📦 Inventario
- Catálogo de piezas y consumibles
- Control de stock con alertas de mínimo
- Entradas y salidas automáticas
- Categorías personalizables
- Historial de movimientos

#### 🔧 Técnicos
- Registro de técnicos del taller
- Asignación a órdenes

#### 📈 Reportes
- Ingresos por período (exportable a CSV)
- Órdenes por estado
- Piezas más utilizadas
- Clientes activos

#### 💾 Respaldo
- Crear copia de seguridad de la base de datos
- Restaurar desde respaldo
- Configurar datos del taller para impresiones

## Procedimiento de Respaldo y Restauración

### Crear Respaldo

1. Vaya al módulo "Respaldo" en el menú lateral
2. Haga clic en "Crear Respaldo"
3. El sistema generará un archivo `taller_backup_YYYYMMDD_HHMMSS.db`
4. Copie este archivo a una memoria USB para mayor seguridad

### Restaurar Respaldo

1. Vaya al módulo "Respaldo"
2. Seleccione "Restaurar Respaldo"
3. Elija el archivo `.db` de respaldo
4. Confirme la operación (se creará un respaldo automático previo)

**Importante**: Realice respaldos regularmente, especialmente antes de actualizaciones o en caso de inestabilidad eléctrica.

## Estructura del Proyecto

```
taller_impresoras/
├── app.py                  # Punto de entrada principal
├── models.py               # Modelos de base de datos
├── requirements.txt        # Dependencias de Python
├── routes/                 # Rutas de la aplicación
│   ├── auth.py            # Autenticación
│   ├── clientes.py        # Gestión de clientes
│   ├── dispositivos.py    # Gestión de dispositivos
│   ├── ordenes.py         # Órdenes de reparación
│   ├── inventario.py      # Inventario de piezas
│   ├── tecnicos.py        # Gestión de técnicos
│   ├── reportes.py        # Reportes y estadísticas
│   └── backup.py          # Respaldo y restauración
├── static/                 # Archivos estáticos
│   ├── css/               # Hojas de estilo
│   └── js/                # JavaScript
├── templates/              # Plantillas HTML
│   ├── base.html          # Layout principal
│   ├── dashboard.html     # Panel de control
│   ├── login.html         # Inicio de sesión
│   ├── clientes/          # Plantillas de clientes
│   ├── dispositivos/      # Plantillas de dispositivos
│   ├── ordenes/           # Plantillas de órdenes
│   ├── inventario/        # Plantillas de inventario
│   ├── tecnicos/          # Plantillas de técnicos
│   └── reportes/          # Plantillas de reportes
├── backup/                 # Respaldos de base de datos
└── instance/               # Base de datos SQLite (auto-generada)
    └── taller.db
```

## Solución de Problemas

### La aplicación no inicia

1. Verifique que Python 3.8+ esté instalado: `python --version`
2. Asegúrese de que el entorno virtual esté activado
3. Reinstale las dependencias: `pip install -r requirements.txt`

### Error de base de datos

1. Elimine el archivo `instance/taller.db`
2. Reinicie la aplicación (se creará automáticamente)
3. Restaure desde un respaldo si tiene datos importantes

### Puerto ya en uso

El puerto 5000 está siendo usado por otra aplicación. Puede cambiar el puerto en `app.py`:

```python
app.run(host='127.0.0.1', port=5001, debug=False)
```

## Seguridad

- Las contraseñas se almacenan con hash bcrypt
- Sesiones protegidas con clave secreta
- Se recomienda cambiar la contraseña por defecto después de la primera instalación

## Actualización de Contraseña

Para cambiar la contraseña del administrador:

1. Inicie sesión como admin
2. Vaya a Configuración (en desarrollo)
3. O directamente en la consola de Python:

```python
from app import app, db, Usuario
from werkzeug.security import generate_password_hash

with app.app_context():
    user = Usuario.query.filter_by(usuario='admin').first()
    user.password_hash = generate_password_hash('NuevaContraseña')
    db.session.commit()
```

## Soporte y Mantenimiento

Este sistema es autocontenido y no requiere soporte externo. Para modificaciones o ampliaciones, consulte el código fuente comentado en español.

## Licencia

Sistema desarrollado para uso interno de talleres independientes en Cuba.

---

**Desarrollado adaptándose a la realidad cubana - 2026**
