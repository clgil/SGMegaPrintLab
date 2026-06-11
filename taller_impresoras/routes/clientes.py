"""
Rutas de gestión de clientes para el Sistema de Gestión de Taller de Impresoras
Adaptado a la realidad cubana - Junio 2026
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Cliente

clientes_bp = Blueprint('clientes', __name__, template_folder='../templates')


@clientes_bp.route('/')
@login_required
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
@login_required
def nuevo():
    """Crear nuevo cliente"""
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        telefono = request.form.get('telefono')
        direccion = request.form.get('direccion')
        tipo_cliente = request.form.get('tipo_cliente')
        
        if not nombre:
            flash('El nombre es obligatorio', 'warning')
            return redirect(url_for('clientes.nuevo'))
        
        cliente = Cliente(
            nombre=nombre,
            telefono=telefono,
            direccion=direccion,
            tipo_cliente=tipo_cliente or 'Particular',
            activo=1
        )
        
        db.session.add(cliente)
        db.session.commit()
        
        flash('Cliente registrado correctamente', 'success')
        return redirect(url_for('clientes.index'))
    
    return render_template('clientes/formulario.html', cliente=None, accion='Crear')


@clientes_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Editar cliente existente"""
    cliente = Cliente.query.get_or_404(id)
    
    if request.method == 'POST':
        cliente.nombre = request.form.get('nombre')
        cliente.telefono = request.form.get('telefono')
        cliente.direccion = request.form.get('direccion')
        cliente.tipo_cliente = request.form.get('tipo_cliente')
        
        db.session.commit()
        
        flash('Cliente actualizado correctamente', 'success')
        return redirect(url_for('clientes.index'))
    
    return render_template('clientes/formulario.html', cliente=cliente, accion='Editar')


@clientes_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    """Eliminación lógica de cliente (desactivar)"""
    cliente = Cliente.query.get_or_404(id)
    cliente.activo = 0
    
    db.session.commit()
    
    flash('Cliente eliminado correctamente', 'info')
    return redirect(url_for('clientes.index'))


@clientes_bp.route('/api/lista')
@login_required
def api_lista():
    """API para obtener lista de clientes (usada en selects dinámicos)"""
    busqueda = request.args.get('q', '')
    query = Cliente.query.filter_by(activo=1)
    
    if busqueda:
        query = query.filter(Cliente.nombre.ilike(f'%{busqueda}%'))
    
    clientes = query.limit(20).all()
    
    resultado = [{'id': c.id, 'nombre': c.nombre, 'telefono': c.telefono} for c in clientes]
    return jsonify(resultado)
