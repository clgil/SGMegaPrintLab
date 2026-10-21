@echo off
REM Script de instalacion para Windows
REM Sistema de Gestion para Taller de Impresoras
REM Adaptado a la realidad cubana - Junio 2026

echo ============================================
echo   Instalador del Sistema de Taller
echo   Adaptado a la realidad cubana
echo ============================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en el PATH
    echo Por favor instale Python 3.8 o superior desde https://python.org
    pause
    exit /b 1
)

echo [OK] Python encontrado
echo.

REM Crear entorno virtual si no existe
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: No se pudo crear el entorno virtual
        pause
        exit /b 1
    )
    echo [OK] Entorno virtual creado
) else (
    echo [OK] Entorno virtual ya existe
)
echo.

REM Activar entorno virtual e instalar dependencias
echo Instalando dependencias...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: No se pudieron instalar las dependencias
    echo Para WeasyPrint en Linux, instale: libpango1.0-dev libharfbuzz-dev libffi-dev
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas
echo.

REM ------------------------------------------------------------------
REM Actualizar el esquema de la base de datos con Flask-Migrate (Alembic).
REM Crea las tablas si es una instalacion nueva, o aplica solo los cambios
REM pendientes si el taller ya tenia datos (NUNCA borra informacion).
REM ------------------------------------------------------------------
echo Actualizando esquema de la base de datos (flask db upgrade)...
set FLASK_APP=app.py
flask db upgrade
if errorlevel 1 (
    echo ERROR: No se pudo actualizar el esquema de la base de datos.
    echo Revise que exista el directorio migrations\ y que DATABASE_URL sea valido.
    echo Si es una BD legada sin tabla alembic_version, ejecute primero:
    echo   flask db stamp 112a730df0d5 ^&^& flask db upgrade
    pause
    exit /b 1
)
echo [OK] Base de datos al ultimo esquema
echo.

REM Datos iniciales: usuario admin y configuraciones por defecto
REM (init-db ya NO crea tablas; es idempotente y no toca datos existentes)
echo Creando datos iniciales (admin y configuraciones)...
flask init-db
if errorlevel 1 (
    echo ADVERTENCIA: No se pudieron crear los datos iniciales.
    echo Puede ejecutarlos manualmente despues con: flask init-db
) else (
    echo [OK] Datos iniciales listos
)
echo.

echo ============================================
echo   INSTALACION COMPLETADA EXITOSAMENTE
echo ============================================
echo.
echo Para iniciar el sistema:
echo   1. Active el entorno virtual: venv\Scripts\activate
echo   2. Ejecute: python app.py
echo   3. Abra su navegador en: http://localhost:5000
echo.
echo Usuario por defecto: admin
echo Contrasena: admin123   ^(cambiarla tras el primer acceso^)
echo.
echo NOTA: Si WeasyPrint falla en Linux, instale las dependencias del sistema:
echo       sudo apt-get install libpango1.0-dev libharfbuzz-dev libffi-dev
echo.
pause
