"""
Blueprints del sistema de gestión de taller de impresoras
"""
from flask import Blueprint

# Importar blueprints
from routes.auth import auth_bp
from routes.clientes import clientes_bp
from routes.dispositivos import dispositivos_bp
from routes.ordenes import ordenes_bp
from routes.inventario import inventario_bp
from routes.usuarios import usuarios_bp
from routes.tecnicos import tecnicos_bp
from routes.proveedores import proveedores_bp
from routes.contratos import contratos_bp
from routes.reportes import reportes_bp
from routes.backup import backup_bp
from routes.ayuda.ayuda import ayuda_bp


def register_blueprints(app):
    """Registra todos los blueprints en la aplicación Flask"""
    
    # Autenticación
    app.register_blueprint(auth_bp)
    
    # Gestión principal
    app.register_blueprint(clientes_bp, url_prefix='/clientes')
    app.register_blueprint(dispositivos_bp, url_prefix='/dispositivos')
    app.register_blueprint(ordenes_bp, url_prefix='/ordenes')
    app.register_blueprint(inventario_bp, url_prefix='/inventario')
    app.register_blueprint(usuarios_bp, url_prefix='/usuarios')
    app.register_blueprint(tecnicos_bp, url_prefix='/tecnicos')
    app.register_blueprint(proveedores_bp, url_prefix='/proveedores')
    app.register_blueprint(contratos_bp, url_prefix='/contratos')
    
    # Reportes y utilidades
    app.register_blueprint(reportes_bp, url_prefix='/reportes')
    app.register_blueprint(backup_bp, url_prefix='/backup')
    app.register_blueprint(ayuda_bp, url_prefix='/ayuda')
