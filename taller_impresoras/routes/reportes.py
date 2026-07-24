"""
Rutas de reportes para el Sistema de Gestión de Taller de Impresoras
Adaptado a la realidad cubana - Junio 2026
"""
from flask import Blueprint, render_template, request, make_response, jsonify, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from models import db, Orden, Pieza, MovimientoInventario, Cliente, Gasto, Configuracion
from datetime import datetime
import io
from routes.decorators import rol_requerido

reportes_bp = Blueprint('reportes', __name__, template_folder='../templates')


@reportes_bp.route('/')
@rol_requerido(['administrador'])
def index():
    """Página principal de reportes"""
    return render_template('reportes/index.html')


@reportes_bp.route('/gastos', methods=['GET', 'POST'])
@rol_requerido(['administrador'])
def gastos():
    """Gestión de gastos operativos"""
    if request.method == 'POST':
        # Añadir nuevo gasto
        descripcion = request.form.get('descripcion')
        monto = float(request.form.get('monto', 0))
        fecha = request.form.get('fecha', datetime.now().strftime('%Y-%m-%d'))
        
        if not descripcion or monto <= 0:
            flash('Descripción y monto válido son obligatorios', 'warning')
            return redirect(url_for('reportes.gastos'))
        
        nuevo_gasto = Gasto(descripcion=descripcion, monto=monto, fecha=fecha)
        db.session.add(nuevo_gasto)
        db.session.commit()
        
        flash('Gasto registrado correctamente', 'success')
        return redirect(url_for('reportes.gastos'))
    
    # Listar gastos (últimos 50)
    gastos_lista = Gasto.query.order_by(Gasto.fecha.desc()).limit(50).all()
    total_gastos = sum(g.monto for g in gastos_lista)
    fecha_actual = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('reportes/gastos.html', gastos=gastos_lista, total_gastos=total_gastos, fecha_actual=fecha_actual)


@reportes_bp.route('/gastos/eliminar/<int:id>', methods=['POST'])
@rol_requerido(['administrador'])
def eliminar_gasto(id):
    """Eliminar un gasto"""
    gasto = Gasto.query.get_or_404(id)
    db.session.delete(gasto)
    db.session.commit()
    flash('Gasto eliminado correctamente', 'info')
    return redirect(url_for('reportes.gastos'))


@reportes_bp.route('/finanzas/configuracion', methods=['GET', 'POST'])
@rol_requerido(['administrador'])
def configuracion_financiera():
    """Configuración de parámetros tributarios"""
    if request.method == 'POST':
        # Guardar configuración tributaria
        config_keys = [
            'regimen_fiscal', 'cuota_fija_mensual',
            'tasa_isip_1', 'tasa_isip_2', 'tasa_isip_3', 'tasa_isip_4', 'tasa_isip_5', 'tasa_isip_6',
            'limite_isip_1', 'limite_isip_2', 'limite_isip_3', 'limite_isip_4', 'limite_isip_5',
            'seguridad_social_porcentaje', 'seguridad_social_base'
        ]
        
        for clave in config_keys:
            valor = request.form.get(clave, '')
            if valor:
                config = Configuracion.query.filter_by(clave=clave).first()
                if config:
                    config.valor = valor
                else:
                    config = Configuracion(clave=clave, valor=valor)
                    db.session.add(config)
        
        db.session.commit()
        flash('Configuración tributaria guardada correctamente', 'success')
        return redirect(url_for('reportes.configuracion_financiera'))
    
    # Cargar configuración actual
    config = {}
    for c in Configuracion.query.all():
        config[c.clave] = c.valor
    
    return render_template('reportes/config_financiera.html', config=config)


@reportes_bp.route('/ingresos', methods=['GET', 'POST'])
@rol_requerido(['administrador'])
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
@rol_requerido(['administrador'])
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
@rol_requerido(['administrador'])
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
@rol_requerido(['administrador'])
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
@rol_requerido(['administrador'])
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


@reportes_bp.route('/exportar_pdf/<tipo>')
@rol_requerido(['administrador'])
def exportar_pdf(tipo):
    """Exportar reporte a PDF usando fpdf2"""
    from fpdf import FPDF, XPos, YPos
    from sqlalchemy import func
    
    if tipo == 'ingresos':
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        ordenes = Orden.query.filter(
            Orden.estado == 'Entregado',
            Orden.fecha_entrega >= fecha_inicio,
            Orden.fecha_entrega <= fecha_fin
        ).all()
        
        # Crear PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 16)
        pdf.cell(0, 10, 'Reporte de Ingresos', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.set_font('Helvetica', '', 12)
        pdf.cell(0, 10, f'Periodo: {fecha_inicio} a {fecha_fin}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(10)
        
        # Tabla de encabezados
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(40, 8, 'Numero Orden', border=1)
        pdf.cell(30, 8, 'Fecha', border=1)
        pdf.cell(80, 8, 'Cliente', border=1)
        pdf.cell(40, 8, 'Total', border=1)
        pdf.ln()
        
        # Datos
        pdf.set_font('Helvetica', '', 9)
        total_general = 0
        for o in ordenes:
            pdf.cell(40, 7, o.numero_orden, border=1)
            pdf.cell(30, 7, str(o.fecha_entrega), border=1)
            # Truncar nombre si es muy largo
            nombre_cliente = o.cliente.nombre[:35] if len(o.cliente.nombre) > 35 else o.cliente.nombre
            pdf.cell(80, 7, nombre_cliente, border=1)
            pdf.cell(40, 7, f'{o.costo_total:.2f}', border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            total_general += o.costo_total
        
        pdf.ln(5)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(150, 8, 'TOTAL GENERAL:', align='R')
        pdf.cell(40, 8, f'{total_general:.2f}', border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Guardar en buffer
        output = io.BytesIO()
        pdf_bytes = pdf.output()
        output.write(pdf_bytes)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'ingresos_{fecha_inicio}_{fecha_fin}.pdf'
        )
    
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
        
        # Crear PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 16)
        pdf.cell(0, 10, 'Reporte de Piezas Utilizadas', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.set_font('Helvetica', '', 12)
        pdf.cell(0, 10, f'Periodo: {fecha_inicio} a {fecha_fin}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(10)
        
        # Tabla de encabezados
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(100, 8, 'Pieza', border=1)
        pdf.cell(50, 8, 'Unidad', border=1)
        pdf.cell(40, 8, 'Cantidad Total', border=1)
        pdf.ln()
        
        # Datos
        pdf.set_font('Helvetica', '', 9)
        for r in resultados:
            nombre_pieza = r.nombre[:45] if len(r.nombre) > 45 else r.nombre
            pdf.cell(100, 7, nombre_pieza, border=1)
            pdf.cell(50, 7, r.unidad, border=1)
            pdf.cell(40, 7, str(r.cantidad_total), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Guardar en buffer
        output = io.BytesIO()
        pdf_bytes = pdf.output()
        output.write(pdf_bytes)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'piezas_{fecha_inicio}_{fecha_fin}.pdf'
        )
    
    elif tipo == 'clientes':
        # Clientes más activos
        resultados = db.session.query(
            Cliente.id,
            Cliente.nombre,
            Cliente.telefono,
            func.count(Orden.id).label('total_ordenes')
        ).join(Orden).group_by(Cliente.id).order_by(func.count(Orden.id).desc()).limit(50).all()
        
        # Crear PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 16)
        pdf.cell(0, 10, 'Reporte de Clientes Activos', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.ln(10)
        
        # Tabla de encabezados
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(15, 8, '#', border=1)
        pdf.cell(90, 8, 'Cliente', border=1)
        pdf.cell(50, 8, 'Telefono', border=1)
        pdf.cell(35, 8, 'Total Ordenes', border=1)
        pdf.ln()
        
        # Datos
        pdf.set_font('Helvetica', '', 9)
        for i, r in enumerate(resultados, 1):
            nombre_cliente = r.nombre[:35] if len(r.nombre) > 35 else r.nombre
            pdf.cell(15, 7, str(i), border=1)
            pdf.cell(90, 7, nombre_cliente, border=1)
            pdf.cell(50, 7, r.telefono or '', border=1)
            pdf.cell(35, 7, str(r.total_ordenes), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Guardar en buffer
        output = io.BytesIO()
        pdf_bytes = pdf.output()
        output.write(pdf_bytes)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='clientes_activos.pdf'
        )
    
    flash('Tipo de reporte no válido', 'danger')
    return redirect(url_for('reportes.index'))
