"""
Rutas de gestión de dispositivos (impresoras) para el Sistema de Gestión de Taller de Impresoras
Adaptado a la realidad cubana - Junio 2026
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from models import db, Dispositivo, Cliente
from routes.decorators import rol_requerido

dispositivos_bp = Blueprint('dispositivos', __name__, template_folder='../templates')


@dispositivos_bp.route('/')
@rol_requerido(['administrador', 'tecnico'])
def index():
    """Listado de dispositivos con filtro por cliente y búsqueda por nombre"""
    pagina = request.args.get('pagina', 1, type=int)
    cliente_id = request.args.get('cliente_id', type=int)
    nombre = request.args.get('nombre', type=str)
    
    query = Dispositivo.query
    
    if cliente_id:
        query = query.filter_by(cliente_id=cliente_id)
    
    if nombre:
        # Buscar por marca o modelo que contengan el texto buscado
        query = query.filter(
            db.or_(
                Dispositivo.marca.ilike(f'%{nombre}%'),
                Dispositivo.modelo.ilike(f'%{nombre}%')
            )
        )
    
    # Paginación de 20 registros
    dispositivos_pagina = query.order_by(Dispositivo.marca).paginate(page=pagina, per_page=20, error_out=False)
    
    clientes = Cliente.query.filter_by(activo=1).order_by(Cliente.nombre).all()
    
    return render_template('dispositivos/index.html', 
                         dispositivos=dispositivos_pagina, 
                         clientes=clientes,
                         cliente_seleccionado=cliente_id,
                         nombre_busqueda=nombre,
                         pagina_actual=pagina)


@dispositivos_bp.route('/nuevo', methods=['GET', 'POST'])
@rol_requerido(['administrador', 'tecnico'])
def nuevo():
    """Crear nuevo dispositivo"""
    if request.method == 'POST':
        cliente_id = request.form.get('cliente_id')
        marca = request.form.get('marca')
        modelo = request.form.get('modelo')
        numero_serie = request.form.get('numero_serie')
        tipo = request.form.get('tipo')
        problema_frecuente = request.form.get('problema_frecuente')
        observaciones = request.form.get('observaciones')
        
        if not cliente_id or not marca:
            flash('El cliente y la marca son obligatorios', 'warning')
            return redirect(url_for('dispositivos.nuevo'))
        
        dispositivo = Dispositivo(
            cliente_id=cliente_id,
            marca=marca,
            modelo=modelo,
            numero_serie=numero_serie,
            tipo=tipo,
            problema_frecuente=problema_frecuente,
            observaciones=observaciones
        )
        
        db.session.add(dispositivo)
        db.session.commit()
        
        flash('Dispositivo registrado correctamente', 'success')
        return redirect(url_for('dispositivos.index'))
    
    clientes = Cliente.query.filter_by(activo=1).order_by(Cliente.nombre).all()
    tipos = ['Láser', 'Inyección de tinta', 'Matricial', 'Multifuncional']
    
    return render_template('dispositivos/formulario.html', 
                         dispositivo=None, 
                         clientes=clientes,
                         tipos=tipos,
                         accion='Crear')


@dispositivos_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@rol_requerido(['administrador', 'tecnico'])
def editar(id):
    """Editar dispositivo existente"""
    dispositivo = Dispositivo.query.get_or_404(id)
    
    if request.method == 'POST':
        dispositivo.cliente_id = request.form.get('cliente_id')
        dispositivo.marca = request.form.get('marca')
        dispositivo.modelo = request.form.get('modelo')
        dispositivo.numero_serie = request.form.get('numero_serie')
        dispositivo.tipo = request.form.get('tipo')
        dispositivo.problema_frecuente = request.form.get('problema_frecuente')
        dispositivo.observaciones = request.form.get('observaciones')
        
        db.session.commit()
        
        flash('Dispositivo actualizado correctamente', 'success')
        return redirect(url_for('dispositivos.index'))
    
    clientes = Cliente.query.filter_by(activo=1).order_by(Cliente.nombre).all()
    tipos = ['Láser', 'Inyección de tinta', 'Matricial', 'Multifuncional']
    
    return render_template('dispositivos/formulario.html', 
                         dispositivo=dispositivo, 
                         clientes=clientes,
                         tipos=tipos,
                         accion='Editar')


@dispositivos_bp.route('/eliminar/<int:id>', methods=['POST'])
@rol_requerido(['administrador', 'tecnico'])
def eliminar(id):
    """Eliminar dispositivo"""
    dispositivo = Dispositivo.query.get_or_404(id)
    
    db.session.delete(dispositivo)
    db.session.commit()
    
    flash('Dispositivo eliminado correctamente', 'info')
    return redirect(url_for('dispositivos.index'))


@dispositivos_bp.route('/por_cliente/<int:cliente_id>')
@rol_requerido(['administrador', 'tecnico'])
def por_cliente(cliente_id):
    """Obtener dispositivos de un cliente específico (para AJAX)"""
    dispositivos = Dispositivo.query.filter_by(cliente_id=cliente_id).all()
    resultado = [{'id': d.id, 'descripcion': f'{d.marca} {d.modelo} ({d.tipo})'} for d in dispositivos]
    return jsonify(resultado)


@dispositivos_bp.route('/api/dispositivos/<int:cliente_id>')
@rol_requerido(['administrador', 'tecnico'])
def api_dispositivos(cliente_id):
    """API para obtener dispositivos de un cliente (usada en formulario de órdenes)"""
    dispositivos = Dispositivo.query.filter_by(cliente_id=cliente_id, activo=1).all()
    resultado = [{'id': d.id, 'texto': f"{d.tipo} - {d.marca} {d.modelo} ({d.numero_serie})"} for d in dispositivos]
    return jsonify(resultado)
