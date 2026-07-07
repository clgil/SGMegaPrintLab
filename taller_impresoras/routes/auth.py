"""
Rutas de autenticación para el Sistema de Gestión de Taller de Impresoras
Adaptado a la realidad cubana - Junio 2026
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, Usuario
from werkzeug.security import generate_password_hash
from routes.decorators import rol_requerido

auth_bp = Blueprint('auth', __name__, template_folder='../templates')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Formulario de inicio de sesión"""
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        password = request.form.get('password')
        
        user = Usuario.query.filter_by(usuario=usuario).first()
        
        if user and user.activo == 1 and user.check_password(password):
            login_user(user)
            # Guardar el rol del usuario en la sesión para usarlo en las plantillas
            from flask import session
            session['user_rol'] = user.rol
            next_page = request.args.get('next')
            flash('¡Bienvenido!', 'success')
            return redirect(next_page if next_page else url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    logout_user()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/cambiar_password', methods=['GET', 'POST'])
@login_required
def cambiar_password():
    """Cambiar contraseña del usuario actual"""
    if request.method == 'POST':
        password_actual = request.form.get('password_actual')
        password_nuevo = request.form.get('password_nuevo')
        password_confirm = request.form.get('password_confirm')
        
        if not current_user.check_password(password_actual):
            flash('La contraseña actual es incorrecta', 'danger')
            return redirect(url_for('auth.cambiar_password'))
        
        if password_nuevo != password_confirm:
            flash('Las contraseñas nuevas no coinciden', 'danger')
            return redirect(url_for('auth.cambiar_password'))
        
        if len(password_nuevo) < 4:
            flash('La contraseña debe tener al menos 4 caracteres', 'warning')
            return redirect(url_for('auth.cambiar_password'))
        
        current_user.set_password(password_nuevo)
        db.session.commit()
        flash('Contraseña cambiada correctamente', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('auth/cambiar_password.html')


@auth_bp.route('/configuracion_taller', methods=['GET', 'POST'])
@rol_requerido(['administrador'])
def configuracion_taller():
    """Configuración de datos del taller (acceso directo para el administrador)"""
    from models import Configuracion
    
    if request.method == 'POST':
        # Actualizar configuración
        config_vals = {
            'nombre_taller': request.form.get('nombre_taller'),
            'direccion_taller': request.form.get('direccion_taller'),
            'telefono_taller': request.form.get('telefono_taller'),
            'email_taller': request.form.get('email_taller'),
            'nit_taller': request.form.get('nit_taller'),
            'responsable_taller': request.form.get('responsable_taller')
        }
        
        for clave, valor in config_vals.items():
            config = db.session.get(Configuracion, clave)
            if not config:
                config = Configuracion(clave=clave, valor=valor)
                db.session.add(config)
            else:
                config.valor = valor
        
        db.session.commit()
        
        flash('Configuración actualizada correctamente', 'success')
        return redirect(url_for('auth.configuracion_taller'))
    
    # Cargar configuración actual
    config = {}
    for c in Configuracion.query.all():
        config[c.clave] = c.valor
    
    return render_template('backup/configuracion.html', config=config)
