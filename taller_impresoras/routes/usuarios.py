"""
Rutas de gestión de usuarios para el Sistema de Gestión de Taller de Impresoras
Adaptado a la realidad cubana - Junio 2026

Módulo exclusivo para administradores
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, Usuario, Cliente
from routes.decorators import rol_requerido

usuarios_bp = Blueprint('usuarios', __name__, template_folder='../templates')


@usuarios_bp.route('/')
@rol_requerido(['administrador'])
def index():
    """Listado de todos los usuarios con paginación y búsqueda"""
    pagina = request.args.get('pagina', 1, type=int)
    busqueda = request.args.get('busqueda', '')
    
    query = Usuario.query
    
    if busqueda:
        # Búsqueda por nombre o usuario
        query = query.filter(
            (Usuario.nombre.ilike(f'%{busqueda}%')) | 
            (Usuario.usuario.ilike(f'%{busqueda}%'))
        )
    
    # Paginación de 20 registros
    usuarios_pagina = query.order_by(Usuario.usuario).paginate(page=pagina, per_page=20, error_out=False)
    
    return render_template('usuarios/index.html', 
                         usuarios=usuarios_pagina, 
                         busqueda=busqueda,
                         pagina_actual=pagina)


@usuarios_bp.route('/nuevo', methods=['GET', 'POST'])
@rol_requerido(['administrador'])
def nuevo():
    """Crear nuevo usuario"""
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        usuario_nombre = request.form.get('usuario')
        password = request.form.get('password')
        rol = request.form.get('rol')
        cliente_id = request.form.get('cliente_id', type=int)
        activo = 1 if request.form.get('activo') else 0
        
        # Validaciones
        if not nombre or not usuario_nombre or not password or not rol:
            flash('Todos los campos obligatorios deben ser completados', 'warning')
            return redirect(url_for('usuarios.nuevo'))
        
        if rol not in Usuario.ROLES_VALIDOS:
            flash('El rol seleccionado no es válido', 'warning')
            return redirect(url_for('usuarios.nuevo'))
        
        # Verificar que el nombre de usuario sea único
        if Usuario.query.filter_by(usuario=usuario_nombre).first():
            flash('El nombre de usuario ya está en uso', 'warning')
            return redirect(url_for('usuarios.nuevo'))
        
        # Si el rol es 'cliente', verificar que se haya seleccionado un cliente
        if rol == 'cliente' and not cliente_id:
            flash('Para un usuario tipo cliente, debe seleccionar un cliente existente', 'warning')
            return redirect(url_for('usuarios.nuevo'))
        
        usuario = Usuario(
            nombre=nombre,
            usuario=usuario_nombre,
            rol=rol,
            activo=activo,
            cliente_id=cliente_id if rol == 'cliente' else None
        )
        usuario.set_password(password)
        
        db.session.add(usuario)
        db.session.commit()
        
        flash('Usuario creado correctamente', 'success')
        return redirect(url_for('usuarios.index'))
    
    clientes = Cliente.query.filter_by(activo=1).order_by(Cliente.nombre).all()
    return render_template('usuarios/formulario.html', 
                         usuario=None, 
                         accion='Crear',
                         clientes=clientes)


@usuarios_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@rol_requerido(['administrador'])
def editar(id):
    """Editar usuario existente"""
    usuario = Usuario.query.get_or_404(id)
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        usuario_nombre = request.form.get('usuario')
        password = request.form.get('password')
        rol = request.form.get('rol')
        cliente_id = request.form.get('cliente_id', type=int)
        activo = 1 if request.form.get('activo') else 0
        
        # Validaciones
        if not nombre or not usuario_nombre or not rol:
            flash('Todos los campos obligatorios deben ser completados', 'warning')
            return redirect(url_for('usuarios.editar', id=id))
        
        if rol not in Usuario.ROLES_VALIDOS:
            flash('El rol seleccionado no es válido', 'warning')
            return redirect(url_for('usuarios.editar', id=id))
        
        # Verificar que el nombre de usuario sea único (excepto para el usuario actual)
        usuario_existente = Usuario.query.filter_by(usuario=usuario_nombre).first()
        if usuario_existente and usuario_existente.id != id:
            flash('El nombre de usuario ya está en uso por otro usuario', 'warning')
            return redirect(url_for('usuarios.editar', id=id))
        
        # Actualizar datos
        usuario.nombre = nombre
        usuario.usuario = usuario_nombre
        usuario.rol = rol
        usuario.activo = activo
        
        # Si hay contraseña nueva, actualizarla
        if password:
            usuario.set_password(password)
        
        # Manejar cliente_id según el rol
        if rol == 'cliente':
            usuario.cliente_id = cliente_id
        else:
            usuario.cliente_id = None
        
        db.session.commit()
        
        flash('Usuario actualizado correctamente', 'success')
        return redirect(url_for('usuarios.index'))
    
    clientes = Cliente.query.filter_by(activo=1).order_by(Cliente.nombre).all()
    return render_template('usuarios/formulario.html', 
                         usuario=usuario, 
                         accion='Editar',
                         clientes=clientes)


@usuarios_bp.route('/eliminar/<int:id>', methods=['POST'])
@rol_requerido(['administrador'])
def eliminar(id):
    """Eliminación lógica de usuario (desactivar)"""
    usuario = Usuario.query.get_or_404(id)
    
    # No permitir desactivar el último administrador
    if usuario.rol == 'administrador':
        admins_activos = Usuario.query.filter_by(rol='administrador', activo=1).all()
        if len(admins_activos) <= 1:
            flash('No se puede desactivar el último administrador del sistema', 'error')
            return redirect(url_for('usuarios.index'))
    
    usuario.activo = 0
    db.session.commit()
    
    flash('Usuario desactivado correctamente', 'info')
    return redirect(url_for('usuarios.index'))


@usuarios_bp.route('/cambiar_estado/<int:id>', methods=['POST'])
@rol_requerido(['administrador'])
def cambiar_estado(id):
    """Activar/desactivar usuario"""
    usuario = Usuario.query.get_or_404(id)
    
    # No permitir desactivar el último administrador
    if usuario.activo == 1 and usuario.rol == 'administrador':
        admins_activos = Usuario.query.filter_by(rol='administrador', activo=1).all()
        if len(admins_activos) <= 1:
            flash('No se puede desactivar el último administrador del sistema', 'error')
            return redirect(url_for('usuarios.index'))
    
    usuario.activo = 0 if usuario.activo == 1 else 1
    db.session.commit()
    
    estado = 'activado' if usuario.activo == 1 else 'desactivado'
    flash(f'Usuario {estado} correctamente', 'success')
    return redirect(url_for('usuarios.index'))


@usuarios_bp.route('/api/verificar_usuario')
@rol_requerido(['administrador'])
def api_verificar_usuario():
    """API para verificar si un nombre de usuario ya existe"""
    usuario_nombre = request.args.get('usuario', '')
    excluir_id = request.args.get('excluir_id', type=int)
    
    query = Usuario.query.filter_by(usuario=usuario_nombre)
    
    if excluir_id:
        query = query.filter(Usuario.id != excluir_id)
    
    existe = query.first() is not None
    
    return jsonify({'existe': existe})
