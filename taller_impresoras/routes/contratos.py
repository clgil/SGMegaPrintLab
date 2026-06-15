"""
Rutas de gestión de contratos de mantenimiento para el Sistema de Gestión de Taller de Impresoras
Adaptado a la realidad cubana - Junio 2026
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from models import db, Contrato, Cliente
from datetime import datetime

contratos_bp = Blueprint('contratos', __name__, template_folder='../templates')


@contratos_bp.route('/')
@login_required
def index():
    """Listado de contratos activos"""
    pagina = request.args.get('pagina', 1, type=int)
    mostrar_inactivos = request.args.get('inactivos', '')
    
    query = Contrato.query
    
    if not mostrar_inactivos:
        query = query.filter_by(activo=1)
    
    # Paginación de 20 registros
    contratos_pagina = query.order_by(Contrato.fecha_inicio.desc()).paginate(page=pagina, per_page=20, error_out=False)
    
    return render_template('contratos/index.html', 
                         contratos=contratos_pagina,
                         mostrar_inactivos=mostrar_inactivos,
                         pagina_actual=pagina)


@contratos_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    """Crear nuevo contrato de mantenimiento"""
    if request.method == 'POST':
        cliente_id = request.form.get('cliente_id')
        descripcion = request.form.get('descripcion')
        frecuencia = request.form.get('frecuencia')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin') if request.form.get('fecha_fin') else None
        precio_mantenimiento = float(request.form.get('precio_mantenimiento') or 0)
        dispositivos_cubiertos = int(request.form.get('dispositivos_cubiertos') or 1)
        
        if not cliente_id or not frecuencia or not fecha_inicio:
            flash('Cliente, frecuencia y fecha de inicio son obligatorios', 'warning')
            return redirect(url_for('contratos.nuevo'))
        
        contrato = Contrato(
            cliente_id=cliente_id,
            descripcion=descripcion,
            frecuencia=frecuencia,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            activo=1,
            precio_mantenimiento=precio_mantenimiento,
            dispositivos_cubiertos=dispositivos_cubiertos
        )
        
        db.session.add(contrato)
        db.session.commit()
        
        flash(f'Contrato de mantenimiento creado correctamente', 'success')
        return redirect(url_for('contratos.index'))
    
    clientes = Cliente.query.filter_by(activo=1).order_by(Cliente.nombre).all()
    frecuencias = ['semanal', 'quincenal', 'mensual', 'trimestral', 'semestral', 'anual']
    
    return render_template('contratos/formulario.html', 
                         contrato=None, 
                         clientes=clientes,
                         frecuencias=frecuencias,
                         accion='Crear')


@contratos_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Editar contrato existente"""
    contrato = Contrato.query.get_or_404(id)
    
    if request.method == 'POST':
        contrato.cliente_id = request.form.get('cliente_id')
        contrato.descripcion = request.form.get('descripcion')
        contrato.frecuencia = request.form.get('frecuencia')
        contrato.fecha_inicio = request.form.get('fecha_inicio')
        contrato.fecha_fin = request.form.get('fecha_fin') if request.form.get('fecha_fin') else None
        contrato.precio_mantenimiento = float(request.form.get('precio_mantenimiento') or 0)
        contrato.dispositivos_cubiertos = int(request.form.get('dispositivos_cubiertos') or 1)
        
        db.session.commit()
        
        flash(f'Contrato actualizado correctamente', 'success')
        return redirect(url_for('contratos.index'))
    
    clientes = Cliente.query.filter_by(activo=1).order_by(Cliente.nombre).all()
    frecuencias = ['semanal', 'quincenal', 'mensual', 'trimestral', 'semestral', 'anual']
    
    return render_template('contratos/formulario.html', 
                         contrato=contrato, 
                         clientes=clientes,
                         frecuencias=frecuencias,
                         accion='Editar')


@contratos_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    """Eliminar contrato (baja lógica)"""
    contrato = Contrato.query.get_or_404(id)
    
    # Baja lógica
    contrato.activo = 0
    db.session.commit()
    
    flash('Contrato eliminado correctamente', 'info')
    return redirect(url_for('contratos.index'))


@contratos_bp.route('/ver/<int:id>')
@login_required
def ver(id):
    """Ver detalle de contrato"""
    contrato = Contrato.query.get_or_404(id)
    proxima_visita = contrato.calcular_proxima_visita()
    
    return render_template('contratos/detalle.html', 
                         contrato=contrato,
                         proxima_visita=proxima_visita)


@contratos_bp.route('/registrar_visita/<int:id>', methods=['POST'])
@login_required
def registrar_visita(id):
    """Registrar visita de mantenimiento realizada"""
    contrato = Contrato.query.get_or_404(id)
    fecha_visita = request.form.get('fecha_visita', datetime.now().strftime('%Y-%m-%d'))
    
    contrato.ultima_visita = fecha_visita
    db.session.commit()
    
    flash(f'Visita registrada para {contrato.cliente.nombre}', 'success')
    return redirect(url_for('contratos.ver', id=id))


@contratos_bp.route('/api/cliente/<int:cliente_id>')
@login_required
def api_cliente(cliente_id):
    """API para obtener contratos activos de un cliente"""
    contratos = Contrato.query.filter_by(cliente_id=cliente_id, activo=1).all()
    
    resultado = [{
        'id': c.id,
        'descripcion': c.descripcion,
        'frecuencia': c.frecuencia,
        'precio': c.precio_mantenimiento,
        'proxima_visita': c.calcular_proxima_visita()
    } for c in contratos]
    
    return jsonify(resultado)
