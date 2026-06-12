"""
Rutas de gestión de órdenes de reparación para el Sistema de Gestión de Taller de Impresoras
Adaptado a la realidad cubana - Junio 2026

Este es el módulo principal del sistema, maneja el ciclo completo de las órdenes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Orden, Cliente, Dispositivo, Tecnico, Pieza, OrdenPieza, MovimientoInventario
from datetime import datetime

ordenes_bp = Blueprint('ordenes', __name__, template_folder='../templates')


def generar_numero_orden():
    """Genera número de orden único con formato OT-AA-0001"""
    anio = datetime.now().year % 100  # Últimos 2 dígitos del año
    ultima_orden = Orden.query.filter(Orden.numero_orden.like(f'OT-{anio:02d}-%')).order_by(Orden.id.desc()).first()
    
    if ultima_orden:
        try:
            ultimo_numero = int(ultima_orden.numero_orden.split('-')[2])
            nuevo_numero = ultimo_numero + 1
        except:
            nuevo_numero = 1
    else:
        nuevo_numero = 1
    
    return f'OT-{anio:02d}-{nuevo_numero:04d}'


@ordenes_bp.route('/')
@login_required
def index():
    """Listado de órdenes con filtros por estado"""
    pagina = request.args.get('pagina', 1, type=int)
    estado = request.args.get('estado', '')
    cliente_id = request.args.get('cliente_id', type=int)
    busqueda = request.args.get('busqueda', '')
    
    query = Orden.query
    
    if estado:
        query = query.filter_by(estado=estado)
    
    if cliente_id:
        query = query.filter_by(cliente_id=cliente_id)
    
    if busqueda:
        # Búsqueda por número de orden o nombre de cliente
        query = query.join(Cliente).filter(
            (Orden.numero_orden.ilike(f'%{busqueda}%')) |
            (Cliente.nombre.ilike(f'%{busqueda}%'))
        )
    
    # Paginación de 20 registros
    ordenes_pagina = query.order_by(Orden.fecha_entrada.desc()).paginate(page=pagina, per_page=20, error_out=False)
    
    estados = ['Recibido', 'En diagnostico', 'Esperando piezas', 'En reparacion', 'Listo para entregar', 'Entregado', 'Cancelado']
    clientes = Cliente.query.filter_by(activo=1).order_by(Cliente.nombre).all()
    
    return render_template('ordenes/index.html', 
                         ordenes=ordenes_pagina, 
                         estados=estados,
                         estado_seleccionado=estado,
                         clientes=clientes,
                         cliente_seleccionado=cliente_id,
                         busqueda=busqueda,
                         pagina_actual=pagina)


@ordenes_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    """Crear nueva orden de reparación"""
    if request.method == 'POST':
        cliente_id = request.form.get('cliente_id')
        dispositivo_id = request.form.get('dispositivo_id') if request.form.get('dispositivo_id') else None
        problema_reportado = request.form.get('problema_reportado')
        tecnico_id = request.form.get('tecnico_id') if request.form.get('tecnico_id') else None
        fecha_prevista = request.form.get('fecha_prevista')
        notas_cliente = request.form.get('notas_cliente')
        
        if not cliente_id or not problema_reportado:
            flash('El cliente y el problema reportado son obligatorios', 'warning')
            return redirect(url_for('ordenes.nuevo'))
        
        numero_orden = generar_numero_orden()
        
        orden = Orden(
            numero_orden=numero_orden,
            cliente_id=cliente_id,
            dispositivo_id=dispositivo_id,
            problema_reportado=problema_reportado,
            tecnico_id=tecnico_id,
            fecha_prevista=fecha_prevista,
            estado='Recibido',
            notas_cliente=notas_cliente,
            fecha_entrada=datetime.now().strftime('%Y-%m-%d')
        )
        
        db.session.add(orden)
        db.session.commit()
        
        flash(f'Orden {numero_orden} creada correctamente', 'success')
        return redirect(url_for('ordenes.editar', id=orden.id))
    
    clientes = Cliente.query.filter_by(activo=1).order_by(Cliente.nombre).all()
    tecnicos = Tecnico.query.filter_by(activo=1).order_by(Tecnico.nombre).all()
    
    return render_template('ordenes/formulario.html', 
                         orden=None, 
                         clientes=clientes,
                         tecnicos=tecnicos,
                         accion='Crear')


@ordenes_bp.route('/ver/<int:id>')
@login_required
def ver(id):
    """Ver detalle completo de una orden"""
    orden = Orden.query.get_or_404(id)
    return render_template('ordenes/detalle.html', orden=orden)


@ordenes_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Editar orden de reparación - formulario completo con piezas y mano de obra"""
    orden = Orden.query.get_or_404(id)
    
    if request.method == 'POST':
        # Actualizar datos básicos
        orden.cliente_id = request.form.get('cliente_id')
        orden.dispositivo_id = request.form.get('dispositivo_id') if request.form.get('dispositivo_id') else None
        orden.problema_reportado = request.form.get('problema_reportado')
        orden.diagnostico = request.form.get('diagnostico')
        orden.estado = request.form.get('estado')
        orden.tecnico_id = request.form.get('tecnico_id') if request.form.get('tecnico_id') else None
        orden.fecha_prevista = request.form.get('fecha_prevista')
        orden.mano_obra_desc = request.form.get('mano_obra_desc')
        orden.mano_obra_costo = float(request.form.get('mano_obra_costo') or 0)
        orden.notas_internas = request.form.get('notas_internas')
        orden.notas_cliente = request.form.get('notas_cliente')
        
        # Si se marca como entregada, registrar fecha de entrega
        if orden.estado == 'Entregado' and not orden.fecha_entrega:
            orden.fecha_entrega = datetime.now().strftime('%Y-%m-%d')
        
        # Procesar piezas usadas (enviadas como JSON desde el frontend)
        piezas_json = request.form.get('piezas_usadas', '[]')
        import json
        piezas_data = json.loads(piezas_json)
        
        # Verificar si la orden está siendo concluida (cambio a estado final)
        estado_anterior = Orden.query.get(orden.id).estado
        estados_finales = ['Entregado', 'Listo para entregar']
        orden_concluida = (orden.estado in estados_finales) and (estado_anterior not in estados_finales)
        
        # Eliminar piezas anteriores y devolver al stock SOLO si la orden ya había sido concluida previamente
        # Esto permite editar órdenes que aún no están en estado final sin afectar el inventario
        if estado_anterior in estados_finales:
            for op in orden.piezas_usadas:
                if op.pieza_id:  # Solo para piezas reales del inventario
                    pieza = Pieza.query.get(op.pieza_id)
                    if pieza:
                        pieza.cantidad += op.cantidad  # Devolver al stock
        
        # Limpiar piezas anteriores
        orden.piezas_usadas = []
        
        # Agregar nuevas piezas y descontar del stock solo si la orden está siendo concluida
        for item in piezas_data:
            pieza_id = item.get('id')
            cantidad = float(item.get('cantidad', 1))
            precio_unitario = float(item.get('precio', 0))
            
            if pieza_id and cantidad > 0:
                # Ignorar piezas manuales (ID negativo)
                if pieza_id < 0:
                    # Para piezas manuales, solo registrar en la orden sin afectar inventario
                    orden_pieza = OrdenPieza(
                        orden_id=orden.id,
                        pieza_id=None,  # No hay referencia a pieza real
                        cantidad=cantidad,
                        precio_unitario=precio_unitario
                    )
                    db.session.add(orden_pieza)
                    continue
                
                pieza = Pieza.query.get(pieza_id)
                if pieza:
                    # Descontar del stock SOLO si la orden está pasando a estado final por primera vez
                    if orden_concluida:
                        # Descontar del stock
                        pieza.cantidad -= cantidad
                        
                        # Registrar movimiento de salida
                        movimiento = MovimientoInventario(
                            pieza_id=pieza.id,
                            tipo='salida',
                            cantidad=cantidad,
                            concepto=f'Usada en orden {orden.numero_orden}',
                            orden_id=orden.id,
                            fecha=datetime.now().strftime('%Y-%m-%d')
                        )
                        db.session.add(movimiento)
                    
                    # Agregar a la orden (siempre, independientemente del estado)
                    orden_pieza = OrdenPieza(
                        orden_id=orden.id,
                        pieza_id=pieza.id,
                        cantidad=cantidad,
                        precio_unitario=precio_unitario
                    )
                    db.session.add(orden_pieza)
        
        # Calcular total
        orden.calcular_total()
        
        db.session.commit()
        
        flash(f'Orden {orden.numero_orden} actualizada correctamente', 'success')
        return redirect(url_for('ordenes.ver', id=orden.id))
    
    clientes = Cliente.query.filter_by(activo=1).order_by(Cliente.nombre).all()
    tecnicos = Tecnico.query.filter_by(activo=1).order_by(Tecnico.nombre).all()
    dispositivos = Dispositivo.query.filter_by(cliente_id=orden.cliente_id).all() if orden.cliente_id else []
    
    # Preparar piezas usadas en formato JSON para el frontend
    import json
    piezas_usadas_json = json.dumps([{
        'id': op.pieza_id,
        'nombre': op.pieza_rel.nombre if op.pieza_rel else 'Pieza manual',
        'cantidad': op.cantidad,
        'precio': op.precio_unitario,
        'unidad': op.pieza_rel.unidad if op.pieza_rel else 'unidad'
    } for op in orden.piezas_usadas])
    
    return render_template('ordenes/formulario_edicion.html', 
                         orden=orden, 
                         clientes=clientes,
                         tecnicos=tecnicos,
                         dispositivos=dispositivos,
                         piezas_usadas_json=piezas_usadas_json,
                         accion='Editar')


@ordenes_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    """Eliminar orden (solo si está en estado inicial)"""
    orden = Orden.query.get_or_404(id)
    
    if orden.estado not in ['Recibido', 'Cancelado']:
        flash('Solo se pueden eliminar órdenes en estado "Recibido" o "Cancelado"', 'warning')
        return redirect(url_for('ordenes.index'))
    
    # Devolver piezas al stock si hay
    for op in orden.piezas_usadas:
        pieza = Pieza.query.get(op.pieza_id)
        if pieza:
            pieza.cantidad += op.cantidad
    
    db.session.delete(orden)
    db.session.commit()
    
    flash('Orden eliminada correctamente', 'info')
    return redirect(url_for('ordenes.index'))


@ordenes_bp.route('/imprimir/<int:id>')
@login_required
def imprimir(id):
    """Vista para impresión de recibo/comprobante"""
    orden = Orden.query.get_or_404(id)
    
    # Obtener configuración del taller
    from models import Configuracion
    config = {}
    for c in Configuracion.query.all():
        config[c.clave] = c.valor
    
    return render_template('ordenes/recibo.html', orden=orden, config=config)


@ordenes_bp.route('/api/dispositivos/<int:cliente_id>')
@login_required
def api_dispositivos(cliente_id):
    """API para obtener dispositivos de un cliente"""
    dispositivos = Dispositivo.query.filter_by(cliente_id=cliente_id).all()
    resultado = [{'id': d.id, 'texto': f'{d.marca} {d.modelo} - {d.tipo}'} for d in dispositivos]
    return jsonify(resultado)


@ordenes_bp.route('/api/piezas')
@login_required
def api_piezas():
    """API para buscar piezas disponibles"""
    busqueda = request.args.get('q', '')
    query = Pieza.query.filter(Pieza.cantidad > 0)
    
    if busqueda:
        query = query.filter(Pieza.nombre.ilike(f'%{busqueda}%'))
    
    piezas = query.limit(50).all()
    
    resultado = [{
        'id': p.id,
        'texto': f'{p.nombre} (Stock: {p.cantidad} {p.unidad}) - ${p.precio_venta:.2f}',
        'precio': p.precio_venta,
        'unidad': p.unidad
    } for p in piezas]
    return jsonify(resultado)


@ordenes_bp.route('/api/ordenes/<int:orden_id>/piezas')
@login_required
def api_orden_piezas(orden_id):
    # API para obtener las piezas de una orden
    orden = Orden.query.get_or_404(orden_id)
    resultado = [{
        'id': op.id,
        'pieza_id': op.pieza_id,
        'nombre': op.pieza_rel.nombre if op.pieza_rel else 'Pieza manual',
        'cantidad': op.cantidad,
        'costo_unitario': op.precio_unitario
    } for op in orden.piezas_usadas]
    return jsonify(resultado)


@ordenes_bp.route('/api/ordenes/<int:orden_id>/historial')
@login_required
def api_orden_historial(orden_id):
    """API para obtener el historial de estados de una orden"""
    # Nota: El modelo HistorialOrden no existe en models.py
    # Se devuelve un array vacío como fallback
    return jsonify([])


@ordenes_bp.route('/estadisticas')
@login_required
def estadisticas():
    """Reporte de estadísticas de órdenes"""
    from sqlalchemy import func
    
    # Órdenes por estado
    ordenes_por_estado = db.session.query(Orden.estado, func.count(Orden.id)).group_by(Orden.estado).all()
    
    # Órdenes por técnico
    ordenes_por_tecnico = db.session.query(Tecnico.nombre, func.count(Orden.id)).join(Orden, Orden.tecnico_id == Tecnico.id).group_by(Tecnico.nombre).all()
    
    # Ingresos por mes (últimos 6 meses)
    from datetime import datetime
    ahora = datetime.now()
    ingresos_mensuales = []
    for i in range(5, -1, -1):
        mes = ahora.month - i
        anio = ahora.year
        if mes <= 0:
            mes += 12
            anio -= 1
        inicio = f"{anio}-{mes:02d}-01"
        if mes == 12:
            fin = f"{anio+1}-01-01"
        else:
            fin = f"{anio}-{mes+1:02d}-01"
        ingreso = db.session.query(func.sum(Orden.costo_total)).filter(
            Orden.estado == 'Entregado',
            Orden.fecha_entrega >= inicio,
            Orden.fecha_entrega < fin
        ).scalar() or 0
        nombres_meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        ingresos_mensuales.append({'mes': nombres_meses[mes-1], 'ingreso': ingreso})
    
    return render_template('ordenes/estadisticas.html',
                         ordenes_por_estado=ordenes_por_estado,
                         ordenes_por_tecnico=ordenes_por_tecnico,
                         ingresos_mensuales=ingresos_mensuales)
