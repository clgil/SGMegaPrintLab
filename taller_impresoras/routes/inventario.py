"""
Rutas de gestión de inventario para el Sistema de Gestión de Taller de Impresoras
Adaptado a la realidad cubana - Junio 2026
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from models import db, Pieza, CategoriaPieza, MovimientoInventario
from datetime import datetime
from routes.decorators import rol_requerido

inventario_bp = Blueprint('inventario', __name__, template_folder='../templates')


@inventario_bp.route('/')
@rol_requerido(['administrador', 'tecnico'])
def index():
    """Listado de piezas con filtro por categoría, stock bajo y búsqueda por nombre"""
    pagina = request.args.get('pagina', 1, type=int)
    categoria_id = request.args.get('categoria_id', type=int)
    mostrar_stock_bajo = request.args.get('stock_bajo', '')
    busqueda_nombre = request.args.get('busqueda', '')
    
    query = Pieza.query
    
    if categoria_id:
        query = query.filter_by(categoria_id=categoria_id)
    
    if mostrar_stock_bajo:
        # Mostrar solo piezas con stock bajo
        query = query.filter(Pieza.cantidad <= Pieza.cantidad_minima)
    
    if busqueda_nombre:
        # Filtrar por nombre de pieza
        query = query.filter(Pieza.nombre.ilike(f'%{busqueda_nombre}%'))
    
    # Paginación de 20 registros
    piezas_pagina = query.order_by(Pieza.nombre).paginate(page=pagina, per_page=20, error_out=False)
    
    categorias = CategoriaPieza.query.order_by(CategoriaPieza.nombre).all()
    
    return render_template('inventario/index.html', 
                         piezas=piezas_pagina, 
                         categorias=categorias,
                         categoria_seleccionada=categoria_id,
                         mostrar_stock_bajo=mostrar_stock_bajo,
                         busqueda_nombre=busqueda_nombre,
                         pagina_actual=pagina)


@inventario_bp.route('/nuevo', methods=['GET', 'POST'])
@rol_requerido(['administrador'])
def nuevo():
    """Crear nueva pieza"""
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        categoria_id = request.form.get('categoria_id')
        codigo_interno = request.form.get('codigo_interno')
        modelos_compatibles = request.form.get('modelos_compatibles')
        cantidad = float(request.form.get('cantidad') or 0)
        cantidad_minima = float(request.form.get('cantidad_minima') or 1)
        unidad = request.form.get('unidad')
        precio_costo = float(request.form.get('precio_costo') or 0)
        precio_venta = float(request.form.get('precio_venta') or 0)
        proveedor = request.form.get('proveedor')
        
        if not nombre:
            flash('El nombre es obligatorio', 'warning')
            return redirect(url_for('inventario.nuevo'))
        
        pieza = Pieza(
            nombre=nombre,
            categoria_id=categoria_id if categoria_id else None,
            codigo_interno=codigo_interno,
            modelos_compatibles=modelos_compatibles,
            cantidad=cantidad,
            cantidad_minima=cantidad_minima,
            unidad=unidad or 'unidad',
            precio_costo=precio_costo,
            precio_venta=precio_venta,
            proveedor=proveedor
        )
        
        db.session.add(pieza)
        # Es necesario hacer commit aquí para que la pieza tenga un ID asignado por la BD
        # antes de crear el movimiento que lo referencia como clave foránea
        db.session.commit()
        
        # Registrar movimiento de entrada inicial si hay cantidad
        if cantidad > 0:
            movimiento = MovimientoInventario(
                pieza_id=pieza.id,  # Ahora pieza.id ya tiene un valor válido
                tipo='entrada',
                cantidad=cantidad,
                concepto='Stock inicial',
                fecha=datetime.now().strftime('%Y-%m-%d')
            )
            db.session.add(movimiento)
            db.session.commit()
        
        flash('Pieza registrada correctamente', 'success')
        return redirect(url_for('inventario.index'))
    
    categorias = CategoriaPieza.query.order_by(CategoriaPieza.nombre).all()
    unidades = ['unidad', 'juego', 'ml', 'metro', 'caja']
    
    return render_template('inventario/formulario.html', 
                         pieza=None, 
                         categorias=categorias,
                         unidades=unidades,
                         accion='Crear')


@inventario_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@rol_requerido(['administrador'])
def editar(id):
    """Editar pieza existente"""
    pieza = Pieza.query.get_or_404(id)
    
    if request.method == 'POST':
        pieza.nombre = request.form.get('nombre')
        pieza.categoria_id = request.form.get('categoria_id') if request.form.get('categoria_id') else None
        pieza.codigo_interno = request.form.get('codigo_interno')
        pieza.modelos_compatibles = request.form.get('modelos_compatibles')
        pieza.cantidad = float(request.form.get('cantidad') or 0)
        pieza.cantidad_minima = float(request.form.get('cantidad_minima') or 1)
        pieza.unidad = request.form.get('unidad')
        pieza.precio_costo = float(request.form.get('precio_costo') or 0)
        pieza.precio_venta = float(request.form.get('precio_venta') or 0)
        pieza.proveedor = request.form.get('proveedor')
        
        db.session.commit()
        
        flash('Pieza actualizada correctamente', 'success')
        return redirect(url_for('inventario.index'))
    
    categorias = CategoriaPieza.query.order_by(CategoriaPieza.nombre).all()
    unidades = ['unidad', 'juego', 'ml', 'metro', 'caja']
    
    return render_template('inventario/formulario.html', 
                         pieza=pieza, 
                         categorias=categorias,
                         unidades=unidades,
                         accion='Editar')


@inventario_bp.route('/eliminar/<int:id>', methods=['POST'])
@rol_requerido(['administrador'])
def eliminar(id):
    """Eliminar pieza (solo si no tiene movimientos)"""
    pieza = Pieza.query.get_or_404(id)
    
    if pieza.movimientos:
        flash('No se puede eliminar: la pieza tiene movimientos registrados', 'danger')
        return redirect(url_for('inventario.index'))
    
    db.session.delete(pieza)
    db.session.commit()
    
    flash('Pieza eliminada correctamente', 'info')
    return redirect(url_for('inventario.index'))


@inventario_bp.route('/entrada/<int:id>', methods=['GET', 'POST'])
@rol_requerido(['administrador'])
def entrada(id):
    """Registrar entrada de pieza al inventario"""
    pieza = Pieza.query.get_or_404(id)
    
    if request.method == 'POST':
        cantidad = float(request.form.get('cantidad'))
        costo_unitario = float(request.form.get('costo_unitario') or pieza.precio_costo)
        proveedor = request.form.get('proveedor')
        concepto = request.form.get('concepto', 'Compra')
        
        if cantidad <= 0:
            flash('La cantidad debe ser mayor a 0', 'warning')
            return redirect(url_for('inventario.entrada', id=id))
        
        # Actualizar cantidad y precio de costo
        pieza.cantidad += cantidad
        pieza.precio_costo = costo_unitario
        pieza.proveedor = proveedor
        
        # Registrar movimiento
        movimiento = MovimientoInventario(
            pieza_id=pieza.id,
            tipo='entrada',
            cantidad=cantidad,
            concepto=f'{concepto} - {proveedor}',
            fecha=datetime.now().strftime('%Y-%m-%d')
        )
        
        db.session.add(movimiento)
        db.session.commit()
        
        flash(f'Entrada de {cantidad} {pieza.unidad}(s) registrada correctamente', 'success')
        return redirect(url_for('inventario.ver', id=id))
    
    return render_template('inventario/entrada.html', pieza=pieza)


@inventario_bp.route('/ver/<int:id>')
@rol_requerido(['administrador', 'tecnico'])
def ver(id):
    """Ver detalle de una pieza con su historial de movimientos"""
    pieza = Pieza.query.get_or_404(id)
    movimientos = MovimientoInventario.query.filter_by(pieza_id=id).order_by(MovimientoInventario.fecha.desc()).all()
    
    return render_template('inventario/detalle.html', pieza=pieza, movimientos=movimientos)


@inventario_bp.route('/api/lista')
@rol_requerido(['administrador', 'tecnico'])
def api_lista():
    """API para obtener lista de piezas (usada en selects dinámicos de órdenes)"""
    busqueda = request.args.get('q', '')
    query = Pieza.query
    
    if busqueda:
        query = query.filter(Pieza.nombre.ilike(f'%{busqueda}%'))
    
    piezas = query.limit(50).all()
    
    resultado = [{
        'id': p.id, 
        'nombre': p.nombre,
        'cantidad': p.cantidad,
        'precio_venta': p.precio_venta,
        'unidad': p.unidad,
        'texto': f"{p.nombre} ({p.unidad}) - ${p.precio_venta:.2f}"
    } for p in piezas]
    return jsonify(resultado)


@inventario_bp.route('/api/piezas')
@rol_requerido(['administrador', 'tecnico'])
def api_piezas():
    """API para buscar piezas por nombre (usada en formulario de órdenes)"""
    busqueda = request.args.get('q', '')
    query = Pieza.query
    
    if busqueda:
        query = query.filter(Pieza.nombre.ilike(f'%{busqueda}%'))
    
    piezas = query.limit(50).all()
    
    resultado = [{
        'id': p.id, 
        'texto': f"{p.nombre} ({p.unidad}) - Stock: {p.cantidad}",
        'precio': p.precio_venta,
        'unidad': p.unidad,
        'stock': p.cantidad,
        'stock_bajo': p.stock_bajo
    } for p in piezas]
    return jsonify(resultado)


@inventario_bp.route('/categorias')
@rol_requerido(['administrador'])
def categorias():
    """Gestión de categorías de piezas"""
    categorias = CategoriaPieza.query.order_by(CategoriaPieza.nombre).all()
    return render_template('inventario/categorias.html', categorias=categorias)


@inventario_bp.route('/categorias/nuevo', methods=['POST'])
@rol_requerido(['administrador'])
def categorias_nuevo():
    """Crear nueva categoría"""
    nombre = request.form.get('nombre')
    
    if not nombre:
        flash('El nombre es obligatorio', 'warning')
        return redirect(url_for('inventario.categorias'))
    
    categoria = CategoriaPieza(nombre=nombre)
    db.session.add(categoria)
    db.session.commit()
    
    flash('Categoría creada correctamente', 'success')
    return redirect(url_for('inventario.categorias'))


@inventario_bp.route('/categorias/eliminar/<int:id>', methods=['POST'])
@rol_requerido(['administrador'])
def categorias_eliminar(id):
    """Eliminar categoría"""
    categoria = CategoriaPieza.query.get_or_404(id)
    
    # Verificar si tiene piezas asociadas
    if categoria.piezas:
        flash('No se puede eliminar: la categoría tiene piezas asociadas', 'danger')
        return redirect(url_for('inventario.categorias'))
    
    db.session.delete(categoria)
    db.session.commit()
    
    flash('Categoría eliminada correctamente', 'info')
    return redirect(url_for('inventario.categorias'))
