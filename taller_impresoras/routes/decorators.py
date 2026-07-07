"""
Decoradores para control de acceso basado en roles
Sistema de Gestión de Taller de Impresoras
"""
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user


def rol_requerido(roles_permitidos):
    """
    Decorador que verifica que el usuario autenticado tenga uno de los roles permitidos.
    
    Args:
        roles_permitidos: Lista de roles que tienen acceso a la ruta decorada.
                         Ejemplo: ['administrador', 'tecnico']
    
    Uso:
        @app.route('/admin')
        @rol_requerido(['administrador'])
        def vista_admin():
            return "Solo administradores"
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verificar que el usuario está autenticado
            if not current_user.is_authenticated:
                flash('Por favor, inicie sesión para acceder.', 'warning')
                return redirect(url_for('auth.login'))
            
            # Verificar que el rol del usuario está en la lista de roles permitidos
            if not hasattr(current_user, 'rol') or current_user.rol not in roles_permitidos:
                flash('No tiene permisos suficientes para acceder a esta página.', 'error')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
