"""
Extensiones de Flask inicializadas a nivel de módulo
Esto permite importarlas en múltiples archivos sin crear dependencias circulares
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def init_extensions(app):
    """Inicializa las extensiones con la aplicación Flask"""
    db.init_app(app)
    login_manager.init_app(app)
    
    # Configurar login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, inicie sesión para acceder.'
    login_manager.login_message_category = 'warning'
    
    return db, login_manager
