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

# Convención de nombres para constraints: necesario para que Alembic pueda
# generar migraciones correctas (DROP CONSTRAINT con nombre) en SQLite.
import sqlalchemy as sa
naming_convention = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}
metadata = sa.MetaData(naming_convention=naming_convention)

db = SQLAlchemy(metadata=metadata)
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
