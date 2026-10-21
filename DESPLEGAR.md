# 🚀 SGMegaPrintLab — Guía de Despliegue e Instalación

**Sistema de Gestión para Taller de Reparación y Mantenimiento de Impresoras**
*Adaptado a la realidad cubana · Octubre 2026*

Esta guía contiene las **instrucciones exactas, paso a paso y explicadas**, para:

1. Instalar y desplegar el sistema **en local** (Windows y Linux), de forma 100 % offline.
2. Desplegarlo en un **hosting/servidor** (VPS con Ubuntu/Debian) usando **Gunicorn + Nginx + systemd**.
3. Actualizar una instalación existente **sin perder datos**, gracias a las migraciones de base de datos con **Flask-Migrate (Alembic)**.

> ⚠️ Regla de oro del proyecto: **el esquema de la base de datos SOLO se gestiona con `flask db upgrade`**. Está prohibido usar `db.create_all()` o crear tablas "a mano": eso rompería el control de versiones de Alembic y ocultaría migraciones pendientes en futuras actualizaciones.

---

## 📋 Índice

- [0. Conceptos previos](#0-conceptos-previos)
- [1. Requisitos](#1-requisitos)
- [2. Despliegue en LOCAL (Windows)](#2-despliegue-en-local-windows)
- [3. Despliegue en LOCAL (Linux)](#3-despliegue-en-local-linux)
- [4. Instalación manual (ambos sistemas)](#4-instalación-manual-ambos-sistemas)
- [5. Verificación post-instalación](#5-verificación-post-instalación)
- [6. Configuración (.env)](#6-configuración-env)
- [7. Despliegue en un HOSTING / servidor](#7-despliegue-en-un-hosting--servidor)
- [8. Cómo actualizar el software sin perder datos](#8-cómo-actualizar-el-software-sin-perder-datos)
- [9. Respaldos (backup)](#9-respaldos-backup)
- [10. Solución de problemas](#10-solución-de-problemas)
- [11. Referencia rápida de comandos](#11-referencia-rápida-de-comandos)

---

## 0. Conceptos previos

| Concepto | Qué es y por qué importa aquí |
|---|---|
| **Entorno virtual (`venv`)** | Carpeta aislada con sus propias librerías Python. Cada taller instala Flask, SQLAlchemy, etc. dentro de `venv/` sin tocar el Python del sistema. |
| **SQLite (`instance/taller.db`)** | La base de datos es UN solo archivo. Por eso el sistema es portable y offline: respaldar = copiar ese archivo. Flask lo crea/ubica automáticamente en la carpeta `instance/`. |
| **Flask-Migrate / Alembic** | Versiona la *estructura* de la BD (tablas y columnas). El código vive en `migrations/`; la migración inicial es `112a730df0d5` (esquema completo de los 14 modelos). La tabla `alembic_version` dentro de la BD registra en qué versión está. |
| **`flask db upgrade`** | Aplica **solo las migraciones pendientes**. Crea las tablas si la BD está vacía, o altera la estructura si ya existe, **sin borrar nunca los datos**. Es lo que ejecutan los instaladores. |
| **`flask init-db`** | Comando CLI propio que **SOLO inserta datos iniciales**: usuario administrador, configuraciones por defecto del taller y técnico general. **Ya NO llama a `db.create_all()`**; si no detecta esquema, aborta indicando que primero se ejecute `flask db upgrade`. Es idempotente: ejecutarlo dos veces no duplica nada. |
| **`.env`** | Archivo de variables de entorno (clave secreta, modo producción, URL de BD). Se crea a partir de `.env.example` y **nunca** se sube al repositorio. |

**Credenciales iniciales** (creadas por `flask init-db`):

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `admin123` | Administrador |

> 🔴 Cambie esta contraseña tras el primer inicio de sesión (ver [Solución de problemas](#10-solución-de-problemas)).

---

## 1. Requisitos

### Hardware mínimo
- PC de escritorio o portátil (o VPS de 1 vCPU / 1 GB RAM para hosting).
- RAM: 1 GB mínimo (recomendado 2 GB).
- Almacenamiento: 500 MB libres + espacio para respaldos.

### Software
- **Python 3.8 o superior** (probado con 3.10–3.12) — [python.org](https://www.python.org/downloads/)
- En Windows: marcar la casilla **"Add Python to PATH"** durante la instalación de Python.
- Solo para generar PDFs con WeasyPrint en **Linux**, hacen falta librerías del sistema:
  ```bash
  sudo apt-get install libpango1.0-dev libharfbuzz-dev libffi-dev
  ```
  (El script `install.sh` lo detecta y ofrece instalarlas.)

### Dependencias Python (fijadas en `requirements.txt`)
Flask 3.0.0 · Flask-SQLAlchemy 3.1.1 · **Flask-Migrate 4.1.0 · Alembic 1.16.5 · Mako 1.3.10** · Flask-Login 0.6.3 · bcrypt 4.1.2 · Werkzeug 3.0.1 · python-dotenv 1.0.0 · reportlab · fpdf2 · WeasyPrint 62.0

### Instalación totalmente OFFLINE (wheelhouse)
Si el equipo del taller no tiene Internet, prepare en otra máquina con conexión un "paquete" de librerías:

```bash
# En la máquina CON internet (mismo Python/SO que el destino):
pip download -r requirements.txt -d wheelhouse/

# Copie el proyecto + la carpeta wheelhouse/ al equipo destino (USB) y allí:
python -m venv venv && source venv/bin/activate        # Windows: venv\Scripts\activate
pip install --no-index --find-links=wheelhouse -r requirements.txt
```

Después continúe con los pasos de migración e init-db ([Sección 4](#4-instalación-manual-ambos-sistemas)).

---

## 2. Despliegue en LOCAL (Windows)

### Paso 1 — Obtener el código
Copie la carpeta del proyecto (por ejemplo `taller_impresoras/`) a `C:\SGMegaPrintLab`, o descomprima el ZIP/USB entregado. **La carpeta `migrations/` debe estar incluida**: sin ella `flask db upgrade` fallará.

### Paso 2 — Ejecutar el instalador
Abra **CMD o PowerShell** en la carpeta del proyecto y ejecute:

```bat
cd C:\SGMegaPrintLab\taller_impresoras
install.bat
```

### ¿Qué hace `install.bat`, exactamente y en orden?
1. **Verifica Python** (`python --version`). Si no lo encuentra, aborta con instrucciones.
2. **Crea el entorno virtual** `venv\` (si no existe) y lo activa.
3. **Instala dependencias**: `pip install --upgrade pip` y `pip install -r requirements.txt`.
4. **Actualiza el esquema de la BD**:
   ```bat
   set FLASK_APP=app.py
   flask db upgrade
   ```
   - Si la BD no existe → Alembic ejecuta la migración inicial `112a730df0d5` y crea las 14 tablas + `alembic_version` en `instance\taller.db`.
   - Si la BD ya existía de una versión anterior → aplica **solo las migraciones pendientes** conservando todos los datos.
   - Si falla, el script muestra la solución para BDs legadas (`flask db stamp 112a730df0d5 && flask db upgrade`) y **aborta sin continuar** (así no se instala "a medias").
5. **Crea los datos iniciales**: `flask init-db` → usuario `admin`, configuraciones del taller y técnico general. No toca tablas ni duplica registros.
6. Muestra el resumen final con las credenciales.

### Paso 3 — Iniciar la aplicación

```bat
venv\Scripts\activate
python app.py
```

Abra el navegador en **http://localhost:5000** e inicie sesión con `admin` / `admin123`.

> 💡 `python app.py` ya **no** crea tablas al arrancar; si detecta que la BD no está migrada, simplemente imprime un aviso recordándole ejecutar `flask db upgrade`.

---

## 3. Despliegue en LOCAL (Linux)

### Paso 1 — Obtener el código
```bash
# Desde Git:
git clone <url-del-repositorio> && cd taller_impresoras
# O copie la carpeta desde USB:
cp -r /media/usb/taller_impresoras ~/SGMegaPrintLab && cd ~/SGMegaPrintLab/taller_impresoras
```

### Paso 2 — Ejecutar el instalador
```bash
chmod +x install.sh
./install.sh
```

### ¿Qué hace `install.sh`, exactamente y en orden?
1. **Verifica `python3`** y su versión; aborta con el comando `apt`/`dnf` adecuado si falta.
2. **Crea y activa el entorno virtual** `venv/` (si no existe).
3. Comprueba las **dependencias del sistema para WeasyPrint** (`libpango1.0-dev`, `libharfbuzz-dev`, `libffi-dev`) y ofrece instalarlas vía `sudo apt-get` si faltan.
4. **Instala las dependencias Python**: `pip install -r requirements.txt`.
5. **Actualiza el esquema de la BD**:
   ```bash
   export FLASK_APP=app.py
   flask db upgrade
   ```
   Igual que en Windows: crea las tablas si es instalación nueva, o aplica solo los cambios pendientes sobre la BD existente del taller. Ante cualquier error, **sale con `exit 1`** y sugiere el `flask db stamp` para BDs legadas.
6. **Crea los datos iniciales**: `flask init-db` (admin + configuraciones; idempotente).
7. Imprime el resumen final.

### Paso 3 — Iniciar la aplicación
```bash
source venv/bin/activate
python app.py
```
Navegador: **http://localhost:5000** → `admin` / `admin123`.

---

## 4. Instalación manual (ambos sistemas)

Si prefiere controlar cada paso (o para instalar offline con wheelhouse), la secuencia **exacta** es:

```bash
# 1) Entorno virtual
python3 -m venv venv                 # Windows: python -m venv venv
source venv/bin/activate             # Windows: venv\Scripts\activate

# 2) Dependencias
pip install -r requirements.txt      # offline: pip install --no-index --find-links=wheelhouse -r requirements.txt

# 3) (Opcional pero recomendado) Variables de entorno
cp .env.example .env                 # Windows: copy .env.example .env  → edite SECRET_KEY

# 4) ESQUEMA de la base de datos (¡antes que cualquier dato!)
export FLASK_APP=app.py              # Windows: set FLASK_APP=app.py
flask db upgrade

# 5) DATOS iniciales (admin + configuraciones) — requiere el esquema del paso 4
flask init-db

# 6) Arranque
python app.py
```

**¿Por qué este orden?** Porque `init-db` ya no crea tablas: verifica que `usuarios` y `configuracion` existan (creadas por Alembic) y, si no, se niega a actuar indicándole correr `flask db upgrade` primero. Así queda garantizado que toda BD del proyecto tenga siempre su versionado correcto.

**BD legada (creada antes de adoptar Flask-Migrate):** si el taller ya tenía `instance/taller.db` con datos y tablas creadas por el antiguo `db.create_all()`, dígaselo a Alembic sin recrear nada:

```bash
flask db stamp 112a730df0d5    # marca la BD como "ya en la versión inicial"
flask db upgrade               # a partir de aquí, todo queda bajo control de versiones
```

---

## 5. Verificación post-instalación

Ejecute estas comprobaciones desde la carpeta del proyecto, con el venv activado y `FLASK_APP=app.py`:

```bash
# a) ¿La BD quedó migrada? Debe imprimir '112a730df0d5'
flask db current

# b) ¿Hay migraciones pendientes? Debe decir: Database is up to date, needs no upgrade
flask db upgrade

# c) Tablas existentes (14 de negocio + alembic_version)
python - <<'EOF'
from app import app, db
from sqlalchemy import inspect
with app.app_context():
    print(sorted(inspect(db.engine).get_table_names()))
EOF

# d) Login de prueba: abra http://localhost:5000 y entre con admin/admin123
```

Todo correcto ⇒ la instalación está lista para producción local.

---

## 6. Configuración (.env)

El proyecto lee variables de entorno (via `python-dotenv`/`os.getenv`). Copie la plantilla y edítela:

```bash
cp .env.example .env          # Windows: copy .env.example .env
```

| Variable | Valor por defecto | Producción recomendada | Explicación |
|---|---|---|---|
| `SECRET_KEY` | clave de desarrollo | `python -c "import secrets; print(secrets.token_hex(32))"` | Firma las cookies de sesión. Si `FLASK_ENV=production` y no la cambia, la app imprime una **advertencia crítica de seguridad** al arrancar. |
| `FLASK_ENV` | `development` | `production` | Selecciona `ProductionConfig` (DEBUG apagado). |
| `FLASK_DEBUG` | — | `False` | Nunca deje el depurador expuesto. |
| `DATABASE_URL` | `sqlite:///taller.db` | igual (o `postgresql://...` si migra de motor) | Ruta de la BD. Con SQLite relativa, el archivo real se guarda en `instance/taller.db`. |
| `MAINTENANCE_MODE` | `False` | según necesite | Flag para modo mantenimiento. |

> 🔒 **NUNCA** haga commit de `.env` (ya está excluido vía `.gitignore`). Solo versione `.env.example`.

---

## 7. Despliegue en un HOSTING / servidor

> 📌 **Aclaración importante:** este es un sistema **offline pensado para un solo taller**. Los "hostings compartidos baratos" (cPanel tipo PHP) **no sirven**: necesitan Python 3.8+, procesos persistentes (WSGI) y permisos de escritura sobre `instance/`. Lo soportado oficialmente es un **VPS/cloud propio** (Ubuntu/Debian, desde 1 GB RAM). Para el caso típico de un taller local, se recomienda mantener la instalación en local y, si se desea acceso remoto, exponerla por VPN o proxy inverso como se describe abajo.

### 7.1 Servir con Gunicorn + Nginx + systemd (VPS Ubuntu 22.04/Debian 12)

**Paso 1 — Preparar el servidor (una vez):**
```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-pip nginx ufw libpango1.0-dev libharfbuzz-dev libffi-dev git
sudo ufw allow OpenSSH && sudo ufw allow 'Nginx Full' && sudo ufw enable
```

**Paso 2 — Crear usuario de servicio y desplegar el código:**
```bash
sudo useradd -m -s /bin/bash sgapp
sudo mkdir -p /opt/sgmegaprintlab && sudo chown sgapp:sgapp /opt/sgmegaprintlab
sudo -u sgapp git clone <url-repo> /opt/sgmegaprintlab/app     # o copie el ZIP a /opt/sgmegaprintlab/app
```

**Paso 3 — Entorno, dependencias y migración (como usuario `sgapp`):**
```bash
sudo -u sgapp -H bash
cd /opt/sgmegaprintlab/app/taller_impresoras

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn                 # servidor WSGI de producción

cp .env.example .env                 # y edite: SECRET_KEY nueva, FLASK_ENV=production

export FLASK_APP=app.py
flask db upgrade                     # ← ESQUEMA: crea/migra instance/taller.db en el servidor
flask init-db                        # ← DATOS: admin + configuraciones iniciales
deactivate
```

**Paso 4 — Servicio systemd (arranque automático + reinicio ante fallos).** Cree `/etc/systemd/system/sgmegaprintlab.service`:

```ini
[Unit]
Description=SGMegaPrintLab (Flask + Gunicorn)
After=network.target

[Service]
User=sgapp
Group=www-data
WorkingDirectory=/opt/sgmegaprintlab/app/taller_impresoras
Environment="PATH=/opt/sgmegaprintlab/app/taller_impresoras/venv/bin"
EnvironmentFile=/opt/sgmegaprintlab/app/taller_impresoras/.env
ExecStart=/opt/sgmegaprintlab/app/taller_impresoras/venv/bin/gunicorn \
    --workers 3 --bind 127.0.0.1:8000 --timeout 120 "app:create_app()"
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

> Nota: se apunta a la **factory** `app:create_app()` (no al objeto global `app`), que es la forma correcta con Gunicorn. Con 1 GB de RAM use `--workers 2`.

Actívelo:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now sgmegaprintlab
sudo systemctl status sgmegaprintlab        # debe estar "active (running)"
journalctl -u sgmegaprintlab -f             # ver logs en vivo
```

**Paso 5 — Proxy inverso Nginx.** Cree `/etc/nginx/sites-available/sgmegaprintlab`:

```nginx
server {
    listen 80;
    server_name sutaller.example.cu;        # o la IP pública si aún no hay dominio

    client_max_body_size 16M;               # coincide con MAX_CONTENT_LENGTH de la app

    location /static/ {
        alias /opt/sgmegaprintlab/app/taller_impresoras/static/;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/sgmegaprintlab /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

Prueba: navegue a `http://sutaller.example.cu` → página de login.

**Paso 6 (recomendado) — HTTPS con Let's Encrypt:**
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d sutaller.example.cu
```

**Permisos sobre la BD (crítico con SQLite):** el proceso (usuario `sgapp`) necesita escribir sobre `instance/` y su archivo:
```bash
sudo chown -R sgapp:www-data /opt/sgmegaprintlab/app/taller_impresoras/instance
sudo chmod 750 /opt/sgmegaprintlab/app/taller_impresoras/instance
sudo chmod 640 /opt/sgmegaprintlab/app/taller_impresoras/instance/taller.db
```
SQLite escribe un diario/journal junto al archivo `.db`; si el directorio no es escribible, obtendrá `attempting to write a read-only database`.

### 7.2 Alternativa ligera sin Nginx (uso interno del taller)
Para que otros PCs del taller accedan sin montar Nginx, arranque Gunicorn escuchando en la LAN:
```bash
venv/bin/gunicorn --workers 2 --bind 0.0.0.0:8000 "app:create_app()"
```
Y cada equipo abre `http://IP-del-servidor:8000`. Restrinja el puerto por firewall a la red local:
```bash
sudo ufw allow from 192.168.1.0/24 to any port 8000 proto tcp
```

### 7.3 Hosting compartido clásico (cPanel/GoDaddy tipo PHP) — NO recomendado
Estos hostings no permiten procesos WSGI persistentes ni garantizan escritura en `instance/`. Si aun así quiere intentarlo donde exista "Python Application Manager" (Passenger/uWSGI): suba el código, cree el venv desde el panel, instale `requirements.txt`, y ejecute **manualmente** `flask db upgrade && flask init-db` por consola antes de apuntar el punto de entrada WSGI a `app:create_app()`. Toda la lógica de respaldo sigue siendo el archivo `instance/taller.db`.

---

## 8. Cómo actualizar el software sin perder datos

Este es el flujo diseñado para los talleres (funciona igual en local y en hosting):

```bash
# 0) RESPALDE antes de actualizar (copie la BD tal como está ahora)
cp instance/taller.db backup/taller_pre_actualizacion_$(date +%F).db

# 1) Traiga el código nuevo (git pull, o descomprima el ZIP nuevo encima,
#    SIN borrar la carpeta instance/ ni el .env)

# 2) Actualice dependencias si cambiaron
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3) Aplique SOLO los cambios de estructura pendientes (los datos intactos)
export FLASK_APP=app.py             # Windows: set FLASK_APP=app.py
flask db upgrade

# 4) Datos nuevos que traiga la versión (nuevas claves de config, etc.)
flask init-db                       # idempotente: no duplica admin ni configuraciones

# 5) Reinicie la aplicación (en hosting: sudo systemctl restart sgmegaprintlab)
```

**¿Por qué es seguro?** Alembic lee la tabla `alembic_version` de la BD del taller, compara con las revisiones en `migrations/versions/` y ejecuta únicamente las diferencias, siempre con `ALTER TABLE`/`CREATE TABLE` generados por usted al desarrollar. `flask db downgrade` permite revertir una revisión si algo sale mal (haga antes un `cp instance/taller.db ...`).

**Usted, como desarrollador, al modificar `models.py`:**
```bash
flask db migrate -m "descripcion del cambio"   # genera la nueva revisión en migrations/versions/
flask db upgrade                                # pruébela contra su BD de desarrollo
# entregue la carpeta migrations/ actualizada junto al código: los talleres solo corren el instalador
```

> ⚠️ Si alguna vez restauró una BD de respaldo antigua, vuelva a correr `flask db upgrade` antes de usar la app: el archivo puede quedar "atrás" respecto al código instalado.

---

## 9. Respaldos (backup)

- **Desde la interfaz:** módulo **Respaldo** → *Crear Respaldo* genera `taller_backup_YYYYMMDD_HHMMSS.db` en `backup/` (o en la ruta definida por `UPLOAD_FOLDER`). *Restaurar Respaldo* crea antes un respaldo automático de seguridad.
- **Desde consola (con la app detenida):**
  ```bash
  cp instance/taller.db /ruta/usb/taller_$(date +%F).db
  ```
- **En el servidor**, respalde también `.env` (contiene SECRET_KEY):
  ```bash
  tar czf sg_respaldo_$(date +%F).tar.gz instance/taller.db .env
  ```
- Frecuencia sugerida: diaria automática + **siempre antes de actualizar** (sección 8) o ante inestabilidad eléctrica.

---

## 10. Solución de problemas

| Síntoma | Causa | Solución exacta |
|---|---|---|
| `Error: Failed to find Flask application...` al correr `flask db ...` | Falta `FLASK_APP` | `export FLASK_APP=app.py` (Linux) / `set FLASK_APP=app.py` (Windows), o ejecute el instalador que ya lo define. |
| `Could not locate a migrations folder` | No copió `migrations/` | Vuelva a copiar el proyecto completo; esa carpeta es parte del despliegue. |
| `init-db` imprime *"La base de datos aún no tiene esquema"* | Orden incorrecto | Corra primero `flask db upgrade`, luego `flask init-db`. |
| `flask db upgrade` falla en una BD antigua con datos ("table already exists") | BD legada creada con el viejo `db.create_all()` | `flask db stamp 112a730df0d5 && flask db upgrade` (marca la versión sin tocar datos). |
| `attempting to write a read-only database` (en hosting) | Permisos | Aplique los `chown/chmod` de la sección 7.1 paso 6 al directorio `instance/`. |
| WeasyPrint lanza `OSError: cannot load library ... pango` | Faltan libs del sistema | `sudo apt-get install libpango1.0-dev libharfbuzz-dev libffi-dev`. |
| Puerto 5000 ocupado | Otra app lo usa | Edite el `app.run(..., port=5001)` final de `app.py`, o use otro puerto en Gunicorn. |
| No recuerda la contraseña de admin | — | Con venv activado: `python -c "from app import app, db; from models import Usuario; from werkzeug.security import generate_password_hash; ctx=app.app_context(); ctx.push(); u=Usuario.query.filter_by(usuario='admin').first(); u.set_password('NuevaClave123'); db.session.commit()"` |
| Pantalla en blanco / error 500 genérico | Depuración oculta en producción | Revise `journalctl -u sgmegaprintlab -f` (servidor) o la terminal donde corre `python app.py`. |

---

## 11. Referencia rápida de comandos

```bash
# === Instalación / despliegue ===
./install.sh                        # Linux: todo (venv + deps + db upgrade + init-db)
install.bat                         # Windows: lo mismo
flask db upgrade                    # aplica esquema/migraciones pendientes
flask init-db                       # datos iniciales (admin/configs) — sin create_all
flask db stamp 112a730df0d5         # adoptar BD legada sin recrear tablas

# === Desarrollo de nuevas versiones ===
flask db migrate -m "cambio X"      # generar nueva revisión desde models.py
flask db current                    # versión en que está la BD
flask db history                    # historial de revisiones
flask db downgrade                  # revertir la última revisión (¡respaldo antes!)

# === Arranque ===
python app.py                       # desarrollo/local (127.0.0.1:5000)
gunicorn --workers 3 --bind 127.0.0.1:8000 "app:create_app()"   # producción
sudo systemctl restart sgmegaprintlab                            # reinicio en hosting
```

---

**Resumen mental del despliegue correcto:**
`código + migrations/` → `venv` → `pip install` → **`flask db upgrade`** (esquema) → **`flask init-db`** (datos) → `python app.py` / Gunicorn.
Los datos del taller viven en `instance/taller.db`; las migraciones jamás lo destruyen: lo hacen evolucionar.
