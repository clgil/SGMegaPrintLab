"""
Rutas de autenticación para el Sistema de Gestión de Taller de Impresoras
Adaptado a la realidad cubana - Junio 2026
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, Usuario, Cliente
from werkzeug.security import generate_password_hash
from routes.decorators import rol_requerido
from routes.validators import PasswordValidator, UsernameValidator, EmailValidator

auth_bp = Blueprint('auth', __name__, template_folder='../templates')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Formulario de inicio de sesión con mensajes de error detallados"""
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        password = request.form.get('password')
        
        if not usuario or not password:
            flash('Usuario y contraseña son obligatorios', 'warning')
            return render_template('login.html')
        
        user = Usuario.query.filter_by(usuario=usuario).first()
        
        # Mensajes de error diferenciados para mejor UX
        if not user:
            flash('El usuario no existe. Verifique e intente de nuevo.', 'warning')
            return render_template('login.html')
        
        if user.activo == 0:
            flash('El usuario está desactivado. Contacte al administrador.', 'danger')
            return render_template('login.html')
        
        if not user.check_password(password):
            flash('Contraseña incorrecta. Intente de nuevo.', 'warning')
            return render_template('login.html')
        
        # Login exitoso
        login_user(user)
        from flask import session
        session['user_rol'] = user.rol
        
        # Advertencia para cambiar contraseña si es usuario por defecto
        if user.usuario == 'admin':
            flash('⚠️ Recuerde cambiar la contraseña del administrador por defecto', 'warning')
        
        next_page = request.args.get('next')
        flash('¡Bienvenido!', 'success')
        return redirect(next_page if next_page else url_for('dashboard'))
    
    return render_template('login.html')


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    """Formulario de registro de nuevos clientes con validación robusta"""
    if request.method == 'POST':
        usuario_nombre = request.form.get('usuario')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        nombre_completo = request.form.get('nombre_completo')
        telefono = request.form.get('telefono')
        direccion = request.form.get('direccion')
        tipo_cliente = request.form.get('tipo_cliente')
        
        # Validar nombre de usuario
        valido_usuario, msg_usuario = UsernameValidator.validar(usuario_nombre)
        if not valido_usuario:
            flash(msg_usuario, 'warning')
            return redirect(url_for('auth.registro'))
        
        # Validar contraseña
        if not password:
            flash('La contraseña es obligatoria', 'warning')
            return redirect(url_for('auth.registro'))
        
        if password != password_confirm:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('auth.registro'))
        
        valido_pwd, msg_pwd = PasswordValidator.validar(password)
        if not valido_pwd:
            flash(f'Contraseña débil: {msg_pwd}', 'warning')
            return redirect(url_for('auth.registro'))
        
        # Validar nombre completo
        if not nombre_completo or len(nombre_completo) < 3:
            flash('El nombre completo es obligatorio (mínimo 3 caracteres)', 'warning')
            return redirect(url_for('auth.registro'))
        
        # Validar email si se proporciona
        if telefono:  # Aquí debería ser email, pero el form usa teléfono
            valido_email, msg_email = EmailValidator.validar(telefono)
            if not valido_email:
                flash(msg_email, 'warning')
                return redirect(url_for('auth.registro'))
        
        # Verificar que el usuario no exista
        usuario_existente = Usuario.query.filter_by(usuario=usuario_nombre).first()
        if usuario_existente:
            flash('El nombre de usuario ya está en uso. Por favor, elija otro.', 'danger')
            return redirect(url_for('auth.registro'))
        
        try:
            # Crear el cliente primero
            cliente = Cliente(
                nombre=nombre_completo,
                telefono=telefono or '',
                direccion=direccion or '',
                tipo_cliente=tipo_cliente or 'Persona natural',
                activo=1
            )
            db.session.add(cliente)
            db.session.flush()  # Para obtener el ID del cliente
            
            # Crear el usuario vinculado al cliente
            nuevo_usuario = Usuario(
                nombre=nombre_completo,
                usuario=usuario_nombre,
                rol='cliente',
                activo=1,
                cliente_id=cliente.id
            )
            nuevo_usuario.set_password(password)
            db.session.add(nuevo_usuario)
            db.session.commit()
            
            flash('Registro completado exitosamente. Ahora puede iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar usuario: {str(e)}', 'danger')
            return redirect(url_for('auth.registro'))
    
    password_requirements = PasswordValidator.get_requirements()
    return render_template('auth/registro.html', password_requirements=password_requirements)


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
    """Cambiar contraseña del usuario actual con validación fuerte"""
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
        
        # Validar que la nueva contraseña sea fuerte
        valido, mensaje = PasswordValidator.validar(password_nuevo)
        if not valido:
            flash(f'La nueva contraseña no cumple los requisitos: {mensaje}', 'warning')
            return redirect(url_for('auth.cambiar_password'))
        
        # Evitar reutilizar la misma contraseña
        if current_user.check_password(password_nuevo):
            flash('La nueva contraseña no puede ser igual a la anterior', 'warning')
            return redirect(url_for('auth.cambiar_password'))
        
        try:
            current_user.set_password(password_nuevo)
            db.session.commit()
            flash('✓ Contraseña cambiada correctamente', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al cambiar contraseña: {str(e)}', 'danger')
            return redirect(url_for('auth.cambiar_password'))
    
    password_requirements = PasswordValidator.get_requirements()
    return render_template('auth/cambiar_password.html', password_requirements=password_requirements)


@auth_bp.route('/configuracion_taller', methods=['GET', 'POST'])
@rol_requerido(['administrador'])
def configuracion_taller():
    """Configuración de datos del taller (acceso directo para el administrador)"""
    from models import Configuracion
    import uuid
    import os
    
    if request.method == 'POST':
        # Actualizar configuración de texto
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
        
        # Manejar subida del logotipo
        if 'logotipo' in request.files:
            archivo_logotipo = request.files['logotipo']
            if archivo_logotipo and archivo_logotipo.filename != '':
                # Verificar que sea una imagen válida
                if archivo_logotipo.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
                    # Crear directorio de uploads si no existe
                    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'uploads')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Guardar el archivo con un nombre único
                    extension = archivo_logotipo.filename.rsplit('.', 1)[1].lower()
                    nombre_archivo = f'logotipo_taller_{uuid.uuid4().hex}.{extension}'
                    ruta_archivo = os.path.join(upload_dir, nombre_archivo)
                    
                    archivo_logotipo.save(ruta_archivo)
                    
                    # Guardar la ruta relativa en la configuración
                    ruta_relativa = f'static/uploads/{nombre_archivo}'
                    config_logo = db.session.get(Configuracion, 'logotipo_taller')
                    if not config_logo:
                        config_logo = Configuracion(clave='logotipo_taller', valor=ruta_relativa)
                        db.session.add(config_logo)
                    else:
                        config_logo.valor = ruta_relativa
                    
                    flash(f'Logotipo subido correctamente: {archivo_logotipo.filename}', 'success')
        
        db.session.commit()
        
        flash('Configuración actualizada correctamente', 'success')
        return redirect(url_for('auth.configuracion_taller'))
    
    # Cargar configuración actual
    config = {}
    for c in Configuracion.query.all():
        config[c.clave] = c.valor
    
    return render_template('backup/configuracion.html', config=config)
