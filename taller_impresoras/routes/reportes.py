"""
Rutas de reportes para el Sistema de Gestión de Taller de Impresoras
Adaptado a la realidad cubana - Junio 2026
"""
from flask import Blueprint, render_template, request, make_response, jsonify
from flask_login import login_required
from models import db, Orden, Pieza, MovimientoInventario, Cliente
from datetime import datetime
import io

reportes_bp = Blueprint('reportes', __name__, template_folder='../templates')


@reportes_bp.route('/')
@login_required
def index():
    """Página principal de reportes"""
    return render_template('reportes/index.html')


@reportes_bp.route('/ingresos', methods=['GET', 'POST'])
@login_required
def ingresos():
    """Reporte de ingresos por rango de fechas"""
    if request.method == 'POST':
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            flash('Ambas fechas son obligatorias', 'warning')
            return redirect(url_for('reportes.ingresos'))
        
        # Consultar órdenes entregadas en el rango
        ordenes = Orden.query.filter(
            Orden.estado == 'Entregado',
            Orden.fecha_entrega >= fecha_inicio,
            Orden.fecha_entrega <= fecha_fin
        ).order_by(Orden.fecha_entrega.desc()).all()
        
        total_ingresos = sum(o.costo_total for o in ordenes)
        
        return render_template('reportes/ingresos.html', 
                             ordenes=ordenes, 
                             total_ingresos=total_ingresos,
                             fecha_inicio=fecha_inicio,
                             fecha_fin=fecha_fin)
    
    return render_template('reportes/ingresos_form.html')


@reportes_bp.route('/ordenes_estado')
@login_required
def ordenes_estado():
    """Reporte de órdenes agrupadas por estado"""
    from sqlalchemy import func
    
    # Órdenes por estado
    resultados = db.session.query(Orden.estado, func.count(Orden.id)).group_by(Orden.estado).all()
    
    # Total de órdenes
    total = sum(r[1] for r in resultados)
    
    return render_template('reportes/ordenes_estado.html', 
                         resultados=resultados, 
                         total=total)


@reportes_bp.route('/piezas_utilizadas', methods=['GET', 'POST'])
@login_required
def piezas_utilizadas():
    """Reporte de piezas más utilizadas en un período"""
    if request.method == 'POST':
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            flash('Ambas fechas son obligatorias', 'warning')
            return redirect(url_for('reportes.piezas_utilizadas'))
        
        # Consultar movimientos de salida en el rango
        from sqlalchemy import func
        
        resultados = db.session.query(
            Pieza.nombre,
            Pieza.unidad,
            func.sum(MovimientoInventario.cantidad).label('cantidad_total')
        ).join(MovimientoInventario).join(Orden).filter(
            MovimientoInventario.tipo == 'salida',
            Orden.fecha_entrega >= fecha_inicio,
            Orden.fecha_entrega <= fecha_fin
        ).group_by(Pieza.id).order_by(func.sum(MovimientoInventario.cantidad).desc()).limit(50).all()
        
        return render_template('reportes/piezas_utilizadas.html', 
                             resultados=resultados,
                             fecha_inicio=fecha_inicio,
                             fecha_fin=fecha_fin)
    
    return render_template('reportes/piezas_utilizadas.html')


@reportes_bp.route('/clientes_activos')
@login_required
def clientes_activos():
    """Reporte de clientes con más órdenes"""
    from sqlalchemy import func
    
    resultados = db.session.query(
        Cliente.nombre,
        Cliente.telefono,
        func.count(Orden.id).label('total_ordenes')
    ).join(Orden).group_by(Cliente.id).order_by(func.count(Orden.id).desc()).limit(50).all()
    
    return render_template('reportes/clientes_activos.html', resultados=resultados)


@reportes_bp.route('/exportar_csv/<tipo>')
@login_required
def exportar_csv(tipo):
    """Exportar reporte a CSV"""
    from sqlalchemy import func
    
    if tipo == 'ingresos':
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        ordenes = Orden.query.filter(
            Orden.estado == 'Entregado',
            Orden.fecha_entrega >= fecha_inicio,
            Orden.fecha_entrega <= fecha_fin
        ).all()
        
        # Crear CSV
        output = io.StringIO()
        output.write('Número Orden,Fecha,Cliente,Total\n')
        for o in ordenes:
            output.write(f'{o.numero_orden},{o.fecha_entrega},{o.cliente.nombre},{o.costo_total:.2f}\n')
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=ingresos_{fecha_inicio}_{fecha_fin}.csv'
        return response
    
    elif tipo == 'piezas':
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        resultados = db.session.query(
            Pieza.nombre,
            Pieza.unidad,
            func.sum(MovimientoInventario.cantidad).label('cantidad_total')
        ).join(MovimientoInventario).join(Orden).filter(
            MovimientoInventario.tipo == 'salida',
            Orden.fecha_entrega >= fecha_inicio,
            Orden.fecha_entrega <= fecha_fin
        ).group_by(Pieza.id).order_by(func.sum(MovimientoInventario.cantidad).desc()).all()
        
        # Crear CSV
        output = io.StringIO()
        output.write('Pieza,Unidad,Cantidad Total\n')
        for r in resultados:
            output.write(f'{r.nombre},{r.unidad},{r.cantidad_total}\n')
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=piezas_{fecha_inicio}_{fecha_fin}.csv'
        return response
    
    flash('Tipo de reporte no válido', 'danger')
    return redirect(url_for('reportes.index'))
