"""
Extensiones de Flask inicializadas a nivel de módulo
Esto permite importarlas en múltiples archivos sin crear dependencias circulares

Flask-Migrate (Alembic) gestiona el versionado del esquema de la base de datos:
los talleres pueden actualizar el software a futuras versiones sin perder sus
datos, aplicando los cambios de estructura con `flask db upgrade`.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def init_extensions(app):
    """Inicializa las extensiones con la aplicación Flask"""
    db.init_app(app)
    login_manager.init_app(app)
    # Bind de la app y la instancia db para los comandos `flask db init/migrate/upgrade`
    migrate.init_app(app, db)

    # Configurar login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, inicie sesión para acceder.'
    login_manager.login_message_category = 'warning'

    return db, login_manager, migrate
