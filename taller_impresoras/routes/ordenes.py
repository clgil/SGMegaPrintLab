"""
Rutas de gestión de órdenes de reparación para el Sistema de Gestión de Taller de Impresoras
Adaptado a la realidad cubana - Junio 2026

Este es el módulo principal del sistema, maneja el ciclo completo de las órdenes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Orden, Cliente, Dispositivo, Tecnico, Pieza, OrdenPieza, MovimientoInventario
from datetime import datetime
from routes.decorators import rol_requerido

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
@rol_requerido(['administrador', 'tecnico'])
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
@rol_requerido(['administrador', 'tecnico'])
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
@rol_requerido(['administrador', 'tecnico'])
def ver(id):
    """Ver detalle completo de una orden"""
    orden = Orden.query.get_or_404(id)
    return render_template('ordenes/detalle.html', orden=orden)


@ordenes_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@rol_requerido(['administrador', 'tecnico'])
def editar(id):
    """Editar orden de reparación - formulario completo con piezas y mano de obra
    
    Workflow de estados y gestión de inventario:
    1. Recibido → En diagnostico → Esperando piezas → En reparacion → Listo para entregar → Entregado
    2. Las piezas se descuentan del inventario SOLO cuando la orden pasa a "Entregado"
    3. Si se edita una orden ya entregada, las piezas se devuelven y vuelven a descontar
    """
    orden = Orden.query.get_or_404(id)
    
    if request.method == 'POST':
        # PASO 1: Capturar el estado actual ANTES de hacer cambios
        estado_anterior = orden.estado
        
        # PASO 2: Actualizar datos básicos
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
        
        # PASO 3: Procesar piezas usadas (enviadas como JSON desde el frontend)
        piezas_json = request.form.get('piezas_usadas', '[]')
        import json
        piezas_data = json.loads(piezas_json)
        
        # PASO 4: Determinar si la orden está siendo concluida por primera vez
        estados_finales = ['Entregado', 'Listo para entregar']
        orden_concluida = (orden.estado in estados_finales) and (estado_anterior not in estados_finales)
        orden_reactivada = (estado_anterior in estados_finales) and (orden.estado not in estados_finales)
        
        # PASO 5: Gestionar piezas anteriores
        # Si la orden estaba concluida y ahora no lo está, devolver piezas al stock
        for op in list(orden.piezas_usadas):
            if op.pieza_id and estado_anterior in estados_finales:
                pieza = db.session.get(Pieza, op.pieza_id)
                if pieza:
                    pieza.cantidad += op.cantidad  # Devolver al stock
                    # Registrar movimiento de devolución
                    movimiento = MovimientoInventario(
                        pieza_id=pieza.id,
                        tipo='entrada',
                        cantidad=op.cantidad,
                        concepto=f'Devolución por cambio de estado - Orden {orden.numero_orden}',
                        orden_id=orden.id,
                        fecha=datetime.now().strftime('%Y-%m-%d')
                    )
                    db.session.add(movimiento)
            db.session.delete(op)  # Eliminar registro de OrdenPieza
        
        db.session.flush()  # Confirmar eliminación de piezas anteriores antes de agregar nuevas
        
        # PASO 6: Agregar nuevas piezas y gestionar inventario
        total_piezas = 0.0
        for item in piezas_data:
            pieza_id = item.get('id')
            cantidad = float(item.get('cantidad', 1))
            precio_unitario = float(item.get('precio', 0))
            
            if cantidad > 0:
                # Ignorar piezas manuales (ID negativo o None)
                if pieza_id is None or pieza_id < 0:
                    # Para piezas manuales, solo registrar en la orden sin afectar inventario
                    orden_pieza = OrdenPieza(
                        orden_id=orden.id,
                        pieza_id=None,  # No hay referencia a pieza real
                        cantidad=cantidad,
                        precio_unitario=precio_unitario
                    )
                    db.session.add(orden_pieza)
                    total_piezas += cantidad * precio_unitario
                    continue
                
                pieza = db.session.get(Pieza, pieza_id)
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
                    total_piezas += cantidad * precio_unitario
        
        # PASO 7: Calcular total: piezas + mano de obra
        mano_obra = float(orden.mano_obra_costo) if orden.mano_obra_costo else 0.0
        orden.costo_total = total_piezas + mano_obra
        
        # PASO 8: Guardar cambios
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
@rol_requerido(['administrador', 'tecnico'])
def eliminar(id):
    """Eliminar orden (solo si está en estado inicial)
    
    IMPORTANTE: Se muestra una confirmación JavaScript antes de ejecutar
    """
    orden = Orden.query.get_or_404(id)
    
    if orden.estado not in ['Recibido', 'Cancelado']:
        flash('Solo se pueden eliminar órdenes en estado "Recibido" o "Cancelado"', 'warning')
        return redirect(url_for('ordenes.index'))
    
    # Devolver piezas al stock si hay
    for op in orden.piezas_usadas:
        pieza = db.session.get(Pieza, op.pieza_id)
        if pieza:
            pieza.cantidad += op.cantidad
    
    db.session.delete(orden)
    db.session.commit()
    
    flash('Orden eliminada correctamente', 'info')
    return redirect(url_for('ordenes.index'))


@ordenes_bp.route('/imprimir/<int:id>')
@rol_requerido(['administrador', 'tecnico'])
def imprimir(id):
    """Vista para impresión de recibo/comprobante"""
    orden = Orden.query.get_or_404(id)
    
    # Obtener configuración del taller
    from models import Configuracion
    config = {}
    for c in Configuracion.query.all():
        config[c.clave] = c.valor
    
    return render_template('ordenes/recibo.html', orden=orden, config=config)


@ordenes_bp.route('/descargar/<int:id>')
@rol_requerido(['administrador', 'tecnico'])
def descargar(id):
    """Descargar orden de reparación como PDF"""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from io import BytesIO
    from flask import send_file
    
    orden = Orden.query.get_or_404(id)
    
    # Obtener configuración del taller
    from models import Configuracion
    config = {}
    for c in Configuracion.query.all():
        config[c.clave] = c.valor
    
    # Crear nombre del archivo: numero_orden_tipo_equipo_(nombre_cliente).pdf
    tipo_equipo = orden.dispositivo.tipo if orden.dispositivo else 'SinEquipo'
    nombre_cliente = orden.cliente.nombre if orden.cliente else 'SinCliente'
    # Limpiar caracteres no válidos para nombres de archivo
    tipo_equipo_limpio = "".join(c for c in tipo_equipo if c.isalnum() or c in ' -_').strip().replace(' ', '_')
    nombre_cliente_limpio = "".join(c for c in nombre_cliente if c.isalnum() or c in ' -_').strip().replace(' ', '_')
    nombre_archivo = f"{orden.numero_orden}_{tipo_equipo_limpio}_({nombre_cliente_limpio}).pdf"
    
    # Crear buffer para el PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.4*inch, leftMargin=0.4*inch, topMargin=0.4*inch, bottomMargin=0.4*inch)
    
    # Estilos modernos y limpios
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1a5276'),
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.HexColor('#2e86c1'),
        spaceAfter=4,
        spaceBefore=4,
        fontName='Helvetica-Bold'
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=2,
        leading=11
    )
    small_style = ParagraphStyle(
        'SmallStyle',
        parent=normal_style,
        fontSize=8,
        textColor=colors.grey,
        spaceAfter=1
    )
    
    # Construir contenido del PDF
    story = []
    
    # Encabezado compacto
    nombre_taller = config.get('nombre_taller', 'Taller de Impresoras')
    story.append(Paragraph(nombre_taller, title_style))
    
    direccion = config.get('direccion_taller', '')
    telefono = config.get('telefono_taller', '')
    email = config.get('email_taller', '')
    info_contacto = f"{direccion} | Tel: {telefono}" if direccion and telefono else ""
    if email:
        info_contacto += f" | {email}" if info_contacto else email
    if info_contacto:
        story.append(Paragraph(info_contacto, small_style))
    
    story.append(Spacer(1, 0.15*inch))
    
    # Número de orden y estado en una línea
    orden_header = f"ORDEN DE REPARACIÓN #{orden.numero_orden}"
    estado_badge = f"Estado: {orden.estado}"
    header_data = [[Paragraph(orden_header, heading_style), Paragraph(estado_badge, normal_style)]]
    header_table = Table(header_data, colWidths=[4*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(header_table)
    story.append(Paragraph(f"Fecha de entrada: {orden.fecha_entrada}", small_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Información del cliente y dispositivo en tabla compacta
    datos_cliente = [
        [Paragraph("DATOS DEL CLIENTE", heading_style), Paragraph("EQUIPO", heading_style)],
        [Paragraph(f"<b>Nombre:</b> {orden.cliente.nombre}", normal_style), 
         Paragraph(f"<b>Tipo:</b> {tipo_equipo}", normal_style)],
        [Paragraph(f"<b>Teléfono:</b> {orden.cliente.telefono}", normal_style), 
         Paragraph(f"<b>Marca:</b> {orden.dispositivo.marca if orden.dispositivo else '-'}", normal_style)],
        [Paragraph("", normal_style), 
         Paragraph(f"<b>Modelo:</b> {orden.dispositivo.modelo if orden.dispositivo else '-'}", normal_style)],
        [Paragraph("", normal_style), 
         Paragraph(f"<b>No. Serie:</b> {orden.dispositivo.numero_serie if orden.dispositivo and orden.dispositivo.numero_serie else '-'}", normal_style)]
    ]
    tabla_datos = Table(datos_cliente, colWidths=[3.2*inch, 3.2*inch])
    tabla_datos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#aed6f1')),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.HexColor('#1a5276')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d6eaf8')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (1, 0), 1, colors.HexColor('#1a5276')),
    ]))
    story.append(tabla_datos)
    story.append(Spacer(1, 0.12*inch))
    
    # Problema reportado y diagnóstico
    problema_text = orden.problema_reportado or '-'
    diagnostico_text = orden.diagnostico or 'No registrado'
    
    story.append(Paragraph("PROBLEMA REPORTADO", heading_style))
    story.append(Paragraph(problema_text, normal_style))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("DIAGNÓSTICO TÉCNICO", heading_style))
    story.append(Paragraph(diagnostico_text, normal_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Técnico responsable
    if orden.tecnico:
        story.append(Paragraph(f"<b>TÉCNICO RESPONSABLE:</b> {orden.tecnico.nombre}", normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Piezas utilizadas - tabla compacta
    if orden.piezas_usadas:
        story.append(Paragraph("REPUESTOS UTILIZADOS", heading_style))
        datos_piezas = [[Paragraph("DESCRIPCIÓN", heading_style), 
                        Paragraph("CANT.", heading_style), 
                        Paragraph("PRECIO", heading_style), 
                        Paragraph("SUBTOTAL", heading_style)]]
        subtotal_piezas = 0
        for op in orden.piezas_usadas:
            nombre_pieza = op.pieza_rel.nombre if op.pieza_rel else 'Pieza manual'
            subtotal = op.cantidad * op.precio_unitario
            subtotal_piezas += subtotal
            datos_piezas.append([
                Paragraph(nombre_pieza, normal_style),
                Paragraph(str(op.cantidad), normal_style),
                Paragraph(f"${op.precio_unitario:.2f}", normal_style),
                Paragraph(f"${subtotal:.2f}", normal_style)
            ])
        
        tabla_piezas = Table(datos_piezas, colWidths=[3.5*inch, 0.7*inch, 1.1*inch, 1.1*inch])
        tabla_piezas.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#aed6f1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d6eaf8')),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#1a5276')),
        ]))
        story.append(tabla_piezas)
        story.append(Spacer(1, 0.08*inch))
        story.append(Paragraph(f"<b>SUBTOTAL REPUESTOS:</b> ${subtotal_piezas:.2f}", normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Totales en tabla compacta
    mano_obra = orden.mano_obra_costo or 0
    costo_total = orden.costo_total or 0
    
    totales_data = [
        [Paragraph("RESUMEN DE COSTOS", heading_style), ""]
    ]
    
    if subtotal_piezas > 0:
        totales_data.append([Paragraph("Repuestos:", normal_style), Paragraph(f"${subtotal_piezas:.2f}", normal_style)])
    
    totales_data.append([Paragraph("Mano de obra:", normal_style), Paragraph(f"${mano_obra:.2f}", normal_style)])
    
    if orden.mano_obra_desc:
        totales_data.append([Paragraph(f"  ({orden.mano_obra_desc})", small_style), ""])
    
    totales_data.append([Paragraph("<b>TOTAL A PAGAR:</b>", ParagraphStyle('TotalBold', parent=normal_style, fontSize=12, textColor=colors.HexColor('#c0392b'), fontName='Helvetica-Bold')), 
                        Paragraph(f"<b>${costo_total:.2f}</b>", ParagraphStyle('TotalBold', parent=normal_style, fontSize=12, textColor=colors.HexColor('#c0392b'), fontName='Helvetica-Bold'))])
    
    tabla_totales = Table(totales_data, colWidths=[4.5*inch, 1.9*inch])
    tabla_totales.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#c0392b')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fdebd0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#d35400')),
    ]))
    story.append(tabla_totales)
    story.append(Spacer(1, 0.15*inch))
    
    # Notas adicionales
    if orden.notas_cliente:
        story.append(Paragraph("OBSERVACIONES", heading_style))
        story.append(Paragraph(orden.notas_cliente, normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Firmas compactas
    story.append(Spacer(1, 0.2*inch))
    firmas_data = [
        [Paragraph("__________________________", normal_style), Paragraph("__________________________", normal_style)],
        [Paragraph("FIRMA DEL TÉCNICO", small_style), Paragraph("FIRMA DEL CLIENTE", small_style)],
        [Paragraph("Responsable del servicio", small_style), Paragraph("Conformidad del servicio", small_style)]
    ]
    tabla_firmas = Table(firmas_data, colWidths=[3.2*inch, 3.2*inch])
    tabla_firmas.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(tabla_firmas)
    
    # Footer compacto
    story.append(Spacer(1, 0.2*inch))
    nit = config.get('nit_taller', '')
    footer_text = "Gracias por confiar en nuestros servicios. Este documento es su comprobante de reparación."
    if nit:
        footer_text += f" NIT/CI: {nit}"
    story.append(Paragraph(footer_text, ParagraphStyle(
        'Footer',
        parent=small_style,
        fontSize=7,
        textColor=colors.grey,
        alignment=TA_CENTER
    )))
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=nombre_archivo
    )


@ordenes_bp.route('/api/dispositivos/<int:cliente_id>')
@rol_requerido(['administrador', 'tecnico'])
def api_dispositivos(cliente_id):
    """API para obtener dispositivos de un cliente"""
    dispositivos = Dispositivo.query.filter_by(cliente_id=cliente_id).all()
    resultado = [{'id': d.id, 'texto': f'{d.marca} {d.modelo} - {d.tipo}'} for d in dispositivos]
    return jsonify(resultado)


@ordenes_bp.route('/api/piezas')
@rol_requerido(['administrador', 'tecnico'])
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
@rol_requerido(['administrador', 'tecnico'])
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
@rol_requerido(['administrador', 'tecnico'])
def api_orden_historial(orden_id):
    """API para obtener el historial de estados de una orden
    
    NOTA: El modelo HistorialOrden no existe en models.py
    Se devuelve un array vacío como fallback
    """
    return jsonify([])


@ordenes_bp.route('/estadisticas')
@rol_requerido(['administrador', 'tecnico'])
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
