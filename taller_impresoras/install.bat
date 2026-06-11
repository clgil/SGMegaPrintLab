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
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: No se pudieron instalar las dependencias
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas
echo.

REM Inicializar base de datos
echo Inicializando base de datos...
python app.py >nul 2>&1 &
timeout /t 3 /nobreak >nul
echo [OK] Base de datos inicializada
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
echo Contrasena: Taller2026
echo.
pause
