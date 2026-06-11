#!/bin/bash
# Script de instalacion para Linux
# Sistema de Gestion para Taller de Impresoras
# Adaptado a la realidad cubana - Junio 2026

echo "============================================"
echo "  Instalador del Sistema de Taller"
echo "  Adaptado a la realidad cubana"
echo "============================================"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 no esta instalado"
    echo "Por favor instale Python 3.8 o superior:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "  Fedora: sudo dnf install python3 python3-pip"
    exit 1
fi

echo "[OK] Python encontrado: $(python3 --version)"
echo ""

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: No se pudo crear el entorno virtual"
        exit 1
    fi
    echo "[OK] Entorno virtual creado"
else
    echo "[OK] Entorno virtual ya existe"
fi
echo ""

# Activar entorno virtual e instalar dependencias
echo "Instalando dependencias..."
source venv/bin/activate
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: No se pudieron instalar las dependencias"
    exit 1
fi
echo "[OK] Dependencias instaladas"
echo ""

# Dar permisos de ejecución
chmod +x install.sh

echo "============================================"
echo "  INSTALACION COMPLETADA EXITOSAMENTE"
echo "============================================"
echo ""
echo "Para iniciar el sistema:"
echo "  1. Active el entorno virtual: source venv/bin/activate"
echo "  2. Ejecute: python app.py"
echo "  3. Abra su navegador en: http://localhost:5000"
echo ""
echo "Usuario por defecto: admin"
echo "Contrasena: Taller2026"
echo ""
