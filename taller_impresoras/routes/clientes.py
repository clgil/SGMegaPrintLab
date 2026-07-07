"""
Rutas de gestión de clientes para el Sistema de Gestión de Taller de Impresoras
Adaptado a la realidad cubana - Junio 2026
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Cliente
from routes.decorators import rol_requerido

clientes_bp = Blueprint('clientes', __name__, template_folder='../templates')


@clientes_bp.route('/')
@rol_requerido(['administrador', 'tecnico'])
def index():
    """Listado de clientes con paginación y búsqueda"""
    pagina = request.args.get('pagina', 1, type=int)
    busqueda = request.args.get('busqueda', '')
    
    query = Cliente.query.filter_by(activo=1)
    
    if busqueda:
        # Búsqueda por nombre o teléfono
        query = query.filter(
            (Cliente.nombre.ilike(f'%{busqueda}%')) | 
            (Cliente.telefono.ilike(f'%{busqueda}%'))
        )
    
    # Paginación de 20 registros
    clientes_pagina = query.order_by(Cliente.nombre).paginate(page=pagina, per_page=20, error_out=False)
    
    return render_template('clientes/index.html', 
                         clientes=clientes_pagina, 
                         busqueda=busqueda,
                         pagina_actual=pagina)


@clientes_bp.route('/nuevo', methods=['GET', 'POST'])
@rol_requerido(['administrador'])
def nuevo():
    """Crear nuevo cliente"""
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        telefono = request.form.get('telefono')
        direccion = request.form.get('direccion')
        tipo_cliente = request.form.get('tipo_cliente')
        
        # Validaciones
        if not nombre:
            flash('El nombre es obligatorio', 'warning')
            return redirect(url_for('clientes.nuevo'))
        
        # Validar que el tipo de cliente sea válido
        if not Cliente.es_tipo_valido(tipo_cliente):
            flash('Tipo de cliente no válido. Seleccione una opción válida.', 'warning')
            return redirect(url_for('clientes.nuevo'))
        
        cliente = Cliente(
            nombre=nombre,
            telefono=telefono,
            direccion=direccion,
            tipo_cliente=tipo_cliente or 'Persona natural',
            activo=1
        )
        
        db.session.add(cliente)
        db.session.commit()
        
        flash('Cliente registrado correctamente', 'success')
        return redirect(url_for('clientes.index'))
    
    return render_template('clientes/formulario.html', cliente=None, accion='Crear', tipos_cliente=Cliente.TIPOS_CLIENTE_VALIDOS)


@clientes_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@rol_requerido(['administrador'])
def editar(id):
    """Editar cliente existente"""
    cliente = Cliente.query.get_or_404(id)
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        telefono = request.form.get('telefono')
        direccion = request.form.get('direccion')
        tipo_cliente = request.form.get('tipo_cliente')
        
        # Validaciones
        if not nombre:
            flash('El nombre es obligatorio', 'warning')
            return redirect(url_for('clientes.editar', id=id))
        
        # Validar que el tipo de cliente sea válido
        if not Cliente.es_tipo_valido(tipo_cliente):
            flash('Tipo de cliente no válido. Seleccione una opción válida.', 'warning')
            return redirect(url_for('clientes.editar', id=id))
        
        cliente.nombre = nombre
        cliente.telefono = telefono
        cliente.direccion = direccion
        cliente.tipo_cliente = tipo_cliente or 'Persona natural'
        
        db.session.commit()
        
        flash('Cliente actualizado correctamente', 'success')
        return redirect(url_for('clientes.index'))
    
    return render_template('clientes/formulario.html', cliente=cliente, accion='Editar', tipos_cliente=Cliente.TIPOS_CLIENTE_VALIDOS)


@clientes_bp.route('/eliminar/<int:id>', methods=['POST'])
@rol_requerido(['administrador'])
def eliminar(id):
    """Eliminación lógica de cliente (desactivar)"""
    cliente = Cliente.query.get_or_404(id)
    cliente.activo = 0
    
    db.session.commit()
    
    flash('Cliente eliminado correctamente', 'info')
    return redirect(url_for('clientes.index'))


@clientes_bp.route('/api/lista')
@rol_requerido(['administrador', 'tecnico'])
def api_lista():
    """API para obtener lista de clientes (usada en selects dinámicos)"""
    busqueda = request.args.get('q', '')
    query = Cliente.query.filter_by(activo=1)
    
    if busqueda:
        query = query.filter(Cliente.nombre.ilike(f'%{busqueda}%'))
    
    clientes = query.limit(20).all()
    
    resultado = [{'id': c.id, 'nombre': c.nombre, 'telefono': c.telefono} for c in clientes]
    return jsonify(resultado)


@clientes_bp.route('/api/clientes/<int:cliente_id>/dispositivos')
@rol_requerido(['administrador', 'tecnico'])
def api_dispositivos_cliente(cliente_id):
    """API para obtener dispositivos de un cliente específico"""
    from models import Dispositivo
    
    dispositivos = Dispositivo.query.filter_by(cliente_id=cliente_id, activo=1).all()
    
    resultado = [{'id': d.id, 'texto': f"{d.tipo} - {d.marca} {d.modelo} ({d.serial})", 'tipo': d.tipo, 'marca': d.marca, 'modelo': d.modelo, 'serial': d.serial} for d in dispositivos]
    return jsonify(resultado)
