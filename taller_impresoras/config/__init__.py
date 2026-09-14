"""
Configuración de la aplicación Flask
"""
import os
from datetime import timedelta

class Config:
    """Clase base de configuración"""
    
    # Clave secreta para sesiones y seguridad
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-cambiar-en-produccion-generar-con-secrets.token_hex(32)')
    
    # Configuración de base de datos
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///taller.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de archivos
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backup')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB máximo
    
    # Configuración de sesión
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    @classmethod
    def verify_secret_key(cls):
        """Verifica si SECRET_KEY está configurada correctamente en producción"""
        if os.getenv('FLASK_ENV') == 'production' and cls.SECRET_KEY == 'dev-key-cambiar-en-produccion-generar-con-secrets.token_hex(32)':
            print("\n" + "="*60)
            print("⚠️  ADVERTENCIA CRÍTICA DE SEGURIDAD")
            print("="*60)
            print("SECRET_KEY no está configurada en producción.")
            print("Esto expone la aplicación a ataques de sesión.")
            print("\nAcciones requeridas:")
            print("1. Generar clave: python -c \"import secrets; print(secrets.token_hex(32))\"")
            print("2. Configurar en variable de entorno: export SECRET_KEY=<valor-generado>")
            print("="*60 + "\n")


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    FLASK_ENV = 'development'


class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    FLASK_ENV = 'production'
    
    @classmethod
    def init_app(cls, app):
        Config.verify_secret_key()


class TestingConfig(Config):
    """Configuración para pruebas"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Diccionario de configuraciones disponibles
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
