"""
Rutas de gestión de proveedores para el Sistema de Gestión de Taller de Impresoras
Adaptado a la realidad cubana - Junio 2026
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from models import db, Proveedor, Pieza, MovimientoInventario
from datetime import datetime

proveedores_bp = Blueprint('proveedores', __name__, template_folder='../templates')


@proveedores_bp.route('/')
@login_required
def index():
    """Listado de proveedores activos"""
    pagina = request.args.get('pagina', 1, type=int)
    tipo = request.args.get('tipo', '')
    
    query = Proveedor.query
    
    if tipo:
        query = query.filter_by(tipo=tipo)
    
    # Paginación de 20 registros
    proveedores_pagina = query.order_by(Proveedor.nombre).paginate(page=pagina, per_page=20, error_out=False)
    
    return render_template('proveedores/index.html', 
                         proveedores=proveedores_pagina,
                         tipo_seleccionado=tipo,
                         pagina_actual=pagina)


@proveedores_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    """Crear nuevo proveedor"""
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        contacto = request.form.get('contacto')
        telefono = request.form.get('telefono')
        tipo = request.form.get('tipo', 'informal')
        
        if not nombre:
            flash('El nombre es obligatorio', 'warning')
            return redirect(url_for('proveedores.nuevo'))
        
        proveedor = Proveedor(
            nombre=nombre,
            contacto=contacto,
            telefono=telefono,
            tipo=tipo,
            activo=1
        )
        
        db.session.add(proveedor)
        db.session.commit()
        
        flash(f'Proveedor {nombre} registrado correctamente', 'success')
        return redirect(url_for('proveedores.index'))
    
    return render_template('proveedores/formulario.html', proveedor=None, accion='Crear')


@proveedores_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Editar proveedor existente"""
    proveedor = Proveedor.query.get_or_404(id)
    
    if request.method == 'POST':
        proveedor.nombre = request.form.get('nombre')
        proveedor.contacto = request.form.get('contacto')
        proveedor.telefono = request.form.get('telefono')
        proveedor.tipo = request.form.get('tipo', 'informal')
        
        db.session.commit()
        
        flash(f'Proveedor {proveedor.nombre} actualizado correctamente', 'success')
        return redirect(url_for('proveedores.index'))
    
    return render_template('proveedores/formulario.html', proveedor=proveedor, accion='Editar')


@proveedores_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    """Eliminar proveedor (baja lógica)"""
    proveedor = Proveedor.query.get_or_404(id)
    
    # Verificar si tiene piezas asociadas
    if proveedor.piezas:
        flash('No se puede eliminar: el proveedor tiene piezas asociadas', 'danger')
        return redirect(url_for('proveedores.index'))
    
    # Baja lógica
    proveedor.activo = 0
    db.session.commit()
    
    flash('Proveedor eliminado correctamente', 'info')
    return redirect(url_for('proveedores.index'))


@proveedores_bp.route('/ver/<int:id>')
@login_required
def ver(id):
    """Ver detalle de proveedor con sus piezas"""
    proveedor = Proveedor.query.get_or_404(id)
    piezas = Pieza.query.filter_by(proveedor_id=id).all()
    
    # Entradas de inventario de este proveedor
    entradas = MovimientoInventario.query.filter_by(
        proveedor_id=id, 
        tipo='entrada'
    ).order_by(MovimientoInventario.fecha.desc()).limit(50).all()
    
    return render_template('proveedores/detalle.html', 
                         proveedor=proveedor, 
                         piezas=piezas,
                         entradas=entradas)


@proveedores_bp.route('/api/lista')
@login_required
def api_lista():
    """API para obtener lista de proveedores (usada en selects dinámicos)"""
    busqueda = request.args.get('q', '')
    query = Proveedor.query.filter_by(activo=1)
    
    if busqueda:
        query = query.filter(Proveedor.nombre.ilike(f'%{busqueda}%'))
    
    proveedores = query.limit(50).all()
    
    resultado = [{
        'id': p.id, 
        'texto': f"{p.nombre} ({p.tipo})"
    } for p in proveedores]
    return jsonify(resultado)
