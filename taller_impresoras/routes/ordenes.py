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
    2. Las piezas se descuentan del inventario INMEDIATAMENTE al ser agregadas a la orden
    3. Si se edita una orden y se eliminan piezas, estas se devuelven al stock
    4. Si se cancela o elimina la orden, todas las piezas se devuelven al stock
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
        
        # PASO 4: Determinar si la orden fue cancelada o eliminada
        orden_cancelada = (orden.estado == 'Cancelado') and (estado_anterior != 'Cancelado')
        
        # PASO 5: Gestionar piezas anteriores - DEVOLVER TODAS al stock primero
        for op in list(orden.piezas_usadas):
            if op.pieza_id:
                pieza = db.session.get(Pieza, op.pieza_id)
                if pieza:
                    # Devolver al stock la cantidad anterior
                    pieza.cantidad += op.cantidad
                    # Registrar movimiento de devolución
                    movimiento = MovimientoInventario(
                        pieza_id=pieza.id,
                        tipo='entrada',
                        cantidad=op.cantidad,
                        concepto=f'Devolución por edición/cancelación - Orden {orden.numero_orden}',
                        orden_id=orden.id,
                        fecha=datetime.now().strftime('%Y-%m-%d')
                    )
                    db.session.add(movimiento)
            db.session.delete(op)  # Eliminar registro de OrdenPieza
        
        db.session.flush()  # Confirmar eliminación de piezas anteriores antes de agregar nuevas
        
        # PASO 6: Agregar nuevas piezas y gestionar inventario
        total_piezas = 0.0
        errores_stock = []
        
        # Primero validar que hay suficiente stock para todas las piezas
        for item in piezas_data:
            pieza_id = item.get('id')
            cantidad = float(item.get('cantidad', 1))
            
            # Ignorar validación de stock para piezas manuales (ID negativo o None)
            if pieza_id is None or pieza_id < 0:
                continue
            
            pieza = db.session.get(Pieza, pieza_id)
            if pieza and cantidad > pieza.cantidad:
                errores_stock.append(f'Pieza "{pieza.nombre}": cantidad solicitada ({cantidad}) > stock disponible ({pieza.cantidad})')
        
        # Si hay errores de stock, retornar error
        if errores_stock:
            db.session.rollback()
            flash('Error: No hay suficiente stock para las siguientes piezas:\\n' + '\\n'.join(errores_stock), 'danger')
            return redirect(url_for('ordenes.editar', id=orden.id))
        
        # Ahora procesar las piezas (ya validadas)
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
                    # Descontar del stock INMEDIATAMENTE al agregar a la orden
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
                    
                    # Agregar a la orden
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
    """Descargar orden de reparación como PDF con el mismo formato que la vista de impresión"""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from io import BytesIO
    from flask import send_file, url_for
    import os
    
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
    
    # Colores corporativos que coinciden con el CSS
    COLOR_PRIMARIO = colors.HexColor('#3498db')
    COLOR_SECUNDARIO = colors.HexColor('#667eea')
    COLOR_GRADIENTE = colors.HexColor('#764ba2')
    COLOR_TEXTO = colors.HexColor('#2c3e50')
    COLOR_TEXTO_CLARO = colors.HexColor('#7f8c8d')
    COLOR_BORDE = colors.HexColor('#ecf0f1')
    COLOR_HEADER_TABLA = colors.HexColor('#34495e')
    COLOR_TOTAL_BG = colors.HexColor('#667eea')
    COLOR_NOTAS_BG = colors.HexColor('#fff9e6')
    COLOR_NOTAS_BORDE = colors.HexColor('#f39c12')
    COLOR_TOTAL_TEXTO = colors.white
    
    # Estilos que coinciden con el CSS del recibo
    styles = getSampleStyleSheet()
    
    # Estilo para el nombre del taller (18pt, bold, uppercase)
    taller_nombre_style = ParagraphStyle(
        'TallerNombre',
        parent=styles['Normal'],
        fontSize=18,
        textColor=COLOR_TEXTO,
        fontName='Helvetica-Bold',
        textTransform='uppercase',
        letterSpacing=0.5,
        spaceAfter=3
    )
    
    # Estilo para detalles del taller (9pt, gris)
    taller_detalles_style = ParagraphStyle(
        'TallerDetalles',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLOR_TEXTO_CLARO,
        spaceAfter=0
    )
    
    # Estilo para email del taller (8pt, azul)
    taller_email_style = ParagraphStyle(
        'TallerEmail',
        parent=styles['Normal'],
        fontSize=8,
        textColor=COLOR_PRIMARIO,
        spaceAfter=0,
        spaceBefore=2
    )
    
    # Estilo para badge label (7pt, bold)
    badge_label_style = ParagraphStyle(
        'BadgeLabel',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.white,
        fontName='Helvetica-Bold',
        letterSpacing=1,
        textTransform='uppercase',
        spaceAfter=0
    )
    
    # Estilo para badge number (14pt, bold)
    badge_number_style = ParagraphStyle(
        'BadgeNumber',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.white,
        fontName='Helvetica-Bold',
        spaceAfter=0
    )
    
    # Estilo para fecha/estado (9pt)
    fecha_estado_style = ParagraphStyle(
        'FechaEstado',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLOR_TEXTO,
        spaceAfter=2
    )
    
    # Estilo para titulos de seccion (9pt, bold, uppercase)
    box_title_style = ParagraphStyle(
        'BoxTitle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLOR_TEXTO,
        fontName='Helvetica-Bold',
        textTransform='uppercase',
        letterSpacing=0.5,
        spaceAfter=8,
        spaceBefore=0
    )
    
    # Estilo para contenido de info (9pt)
    info_content_style = ParagraphStyle(
        'InfoContent',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLOR_TEXTO,
        spaceAfter=3
    )
    
    # Estilo para nombre cliente/dispositivo (10pt, bold)
    nombre_destacado_style = ParagraphStyle(
        'NombreDestacado',
        parent=styles['Normal'],
        fontSize=10,
        textColor=COLOR_TEXTO,
        fontName='Helvetica-Bold',
        spaceAfter=3
    )
    
    # Estilo para titulos de detalle (9pt, bold, uppercase)
    detalle_title_style = ParagraphStyle(
        'DetalleTitle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLOR_TEXTO,
        fontName='Helvetica-Bold',
        textTransform='uppercase',
        letterSpacing=0.5,
        spaceAfter=5,
        spaceBefore=0
    )
    
    # Estilo para texto de detalle (9pt, justificado)
    detalle_texto_style = ParagraphStyle(
        'DetalleTexto',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLOR_TEXTO,
        spaceAfter=0,
        alignment=TA_LEFT,
        leading=13
    )
    
    # Estilo para headers de tabla (7pt, bold, uppercase, blanco)
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.white,
        fontName='Helvetica-Bold',
        textTransform='uppercase',
        letterSpacing=0.5,
        spaceAfter=0
    )
    
    # Estilo para celdas de tabla (8pt)
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=8,
        textColor=COLOR_TEXTO,
        spaceAfter=0
    )
    
    # Estilo para subtotal
    subtotal_style = ParagraphStyle(
        'Subtotal',
        parent=styles['Normal'],
        fontSize=8,
        textColor=COLOR_TEXTO,
        fontName='Helvetica-Bold',
        spaceAfter=0
    )
    
    # Estilo para labels de totales (9pt, bold)
    total_label_style = ParagraphStyle(
        'TotalLabel',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.white,
        fontName='Helvetica-Bold',
        spaceAfter=0
    )
    
    # Estilo para valores de totales (9pt, bold)
    total_value_style = ParagraphStyle(
        'TotalValue',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.white,
        fontName='Helvetica-Bold',
        spaceAfter=0
    )
    
    # Estilo para total principal label (10pt, bold)
    total_principal_label_style = ParagraphStyle(
        'TotalPrincipalLabel',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.white,
        fontName='Helvetica-Bold',
        letterSpacing=0.5,
        spaceAfter=0
    )
    
    # Estilo para total principal valor (16pt, bold)
    total_principal_value_style = ParagraphStyle(
        'TotalPrincipalValue',
        parent=styles['Normal'],
        fontSize=16,
        textColor=colors.white,
        fontName='Helvetica-Bold',
        spaceAfter=0
    )
    
    # Estilo para descripcion mano de obra (7pt)
    mano_obra_desc_style = ParagraphStyle(
        'ManoObraDesc',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.white,
        spaceAfter=0
    )
    
    # Estilo para titulo de notas (9pt, bold, uppercase)
    notas_title_style = ParagraphStyle(
        'NotasTitle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLOR_TEXTO,
        fontName='Helvetica-Bold',
        textTransform='uppercase',
        spaceAfter=5
    )
    
    # Estilo para texto de notas (9pt)
    notas_texto_style = ParagraphStyle(
        'NotasTexto',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLOR_TEXTO,
        spaceAfter=0,
        leading=13
    )
    
    # Estilo para firma label (9pt, bold, uppercase)
    firma_label_style = ParagraphStyle(
        'FirmaLabel',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLOR_TEXTO,
        fontName='Helvetica-Bold',
        textTransform='uppercase',
        spaceAfter=0
    )
    
    # Estilo para firma sublabel (7pt, gris)
    firma_sublabel_style = ParagraphStyle(
        'FirmaSublabel',
        parent=styles['Normal'],
        fontSize=7,
        textColor=COLOR_TEXTO_CLARO,
        spaceAfter=0,
        spaceBefore=3
    )
    
    # Estilo para footer (8pt, gris)
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=COLOR_TEXTO_CLARO,
        alignment=TA_CENTER,
        spaceAfter=3
    )
    
    # Estilo para footer NIT (7pt, bold)
    footer_nit_style = ParagraphStyle(
        'FooterNit',
        parent=styles['Normal'],
        fontSize=7,
        textColor=COLOR_TEXTO,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=0
    )
    
    # Construir contenido del PDF
    story = []
    
    # === ENCABEZADO CORPORATIVO ===
    header_data = []
    
    # Lado izquierdo: logo + info taller
    left_content = []
    
    # Verificar si hay logotipo
    logotipo_path = config.get('logotipo_taller')
    if logotipo_path and os.path.exists(logotipo_path):
        try:
            img = Image(logotipo_path, width=1.2*inch, height=0.8*inch, kind='proportional')
            left_content.append(img)
        except:
            pass
    
    # Nombre del taller
    nombre_taller = config.get('nombre_taller', 'Taller de Impresoras')
    left_content.append(Paragraph(nombre_taller, taller_nombre_style))
    
    # Direccion y telefono
    direccion = config.get('direccion_taller', '')
    telefono = config.get('telefono_taller', '')
    if direccion or telefono:
        detalles = []
        if direccion:
            detalles.append(direccion)
        if telefono:
            detalles.append(f"Tel: {telefono}")
        left_content.append(Paragraph(" | ".join(detalles), taller_detalles_style))
    
    # Email
    email = config.get('email_taller', '')
    if email:
        left_content.append(Paragraph(email, taller_email_style))
    
    # Lado derecho: badge de orden + fecha/estado
    right_content = []
    
    # Badge con gradiente simulado (usando color solido)
    badge_data = [
        [Paragraph("ORDEN DE REPARACIÓN", badge_label_style)],
        [Paragraph(f"#{orden.numero_orden}", badge_number_style)]
    ]
    badge_table = Table(badge_data, colWidths=[2.5*inch])
    badge_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_SECUNDARIO),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
    ]))
    right_content.append(badge_table)
    right_content.append(Spacer(1, 0.1*inch))
    
    # Fecha y estado
    right_content.append(Paragraph(f"<b>Fecha:</b> {orden.fecha_entrada}", fecha_estado_style))
    right_content.append(Paragraph(f"<b>Estado:</b> {orden.estado}", fecha_estado_style))
    
    # Tabla principal del header
    header_table = Table([[left_content, right_content]], colWidths=[4.5*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    
    # Linea divisoria azul
    divider_line = Table([['']], colWidths=[7.4*inch])
    divider_line.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, 0), 3, COLOR_PRIMARIO),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
    ]))
    story.append(divider_line)
    story.append(Spacer(1, 0.15*inch))
    
    # === INFORMACION DEL CLIENTE Y DISPOSITIVO ===
    cliente_data = []
    dispositivo_data = []
    
    # Box cliente
    cliente_data.append([Paragraph("📋 DATOS DEL CLIENTE", box_title_style)])
    cliente_data.append([Paragraph(f"<b>{orden.cliente.nombre}</b>", nombre_destacado_style)])
    cliente_data.append([Paragraph(f"Teléfono: {orden.cliente.telefono}", info_content_style)])
    
    # Box dispositivo
    if orden.dispositivo:
        dispositivo_data.append([Paragraph("🖨️ EQUIPO", box_title_style)])
        dispositivo_data.append([Paragraph(f"<b>{orden.dispositivo.tipo} - {orden.dispositivo.marca} {orden.dispositivo.modelo}</b>", nombre_destacado_style)])
        if orden.dispositivo.numero_serie:
            dispositivo_data.append([Paragraph(f"No. Serie: {orden.dispositivo.numero_serie}", info_content_style)])
    
    # Crear tablas individuales para cada box
    tabla_cliente = Table(cliente_data, colWidths=[3.5*inch])
    tabla_cliente.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEWIDTH', (0, 0), (0, -1), 4, COLOR_PRIMARIO),
        ('LINEBEFORE', (0, 0), (0, -1), 4, COLOR_PRIMARIO),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    tabla_dispositivo = Table(dispositivo_data, colWidths=[3.5*inch])
    tabla_dispositivo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEWIDTH', (0, 0), (0, -1), 4, COLOR_PRIMARIO),
        ('LINEBEFORE', (0, 0), (0, -1), 4, COLOR_PRIMARIO),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    info_grid = Table([[tabla_cliente, tabla_dispositivo]], colWidths=[3.5*inch, 3.5*inch])
    info_grid.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(info_grid)
    story.append(Spacer(1, 0.15*inch))
    
    # === PROBLEMA REPORTADO ===
    story.append(Paragraph("⚠️ PROBLEMA REPORTADO", detalle_title_style))
    problema_text = orden.problema_reportado or '-'
    story.append(Paragraph(problema_text, detalle_texto_style))
    story.append(Spacer(1, 0.1*inch))
    
    # === DIAGNOSTICO ===
    if orden.diagnostico:
        story.append(Paragraph("🔍 DIAGNÓSTICO TÉCNICO", detalle_title_style))
        story.append(Paragraph(orden.diagnostico, detalle_texto_style))
        story.append(Spacer(1, 0.1*inch))
    
    # === TECNICO RESPONSABLE ===
    if orden.tecnico:
        story.append(Paragraph("👨‍🔧 TÉCNICO RESPONSABLE", detalle_title_style))
        story.append(Paragraph(orden.tecnico.nombre, info_content_style))
        story.append(Spacer(1, 0.1*inch))
    
    # === PIEZAS UTILIZADAS ===
    subtotal_piezas = 0
    if orden.piezas_usadas:
        story.append(Paragraph("📦 REPUESTOS UTILIZADOS", detalle_title_style))
        
        datos_piezas = [[
            Paragraph("DESCRIPCIÓN", table_header_style),
            Paragraph("CANT.", table_header_style),
            Paragraph("PRECIO UNIT.", table_header_style),
            Paragraph("SUBTOTAL", table_header_style)
        ]]
        
        for op in orden.piezas_usadas:
            nombre_pieza = op.pieza_rel.nombre if op.pieza_rel else 'Pieza manual'
            subtotal = op.cantidad * op.precio_unitario
            subtotal_piezas += subtotal
            datos_piezas.append([
                Paragraph(nombre_pieza, table_cell_style),
                Paragraph(str(op.cantidad), table_cell_style),
                Paragraph(f"${op.precio_unitario:.2f}", table_cell_style),
                Paragraph(f"${subtotal:.2f}", table_cell_style)
            ])
        
        tabla_piezas = Table(datos_piezas, colWidths=[3.7*inch, 0.7*inch, 1.5*inch, 1.5*inch])
        tabla_piezas.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_HEADER_TABLA),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDE),
            ('LINEBELOW', (0, 0), (-1, 0), 1, COLOR_HEADER_TABLA),
        ]))
        story.append(tabla_piezas)
        
        # Subtotal repuestos
        subtotal_row = Table([[
            Paragraph("<b>SUBTOTAL REPUESTOS:</b>", subtotal_style),
            Paragraph(f"${subtotal_piezas:.2f}", subtotal_style)
        ]], colWidths=[5.9*inch, 1.5*inch])
        subtotal_row.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ]))
        story.append(subtotal_row)
        story.append(Spacer(1, 0.15*inch))
    
    # === TOTALES ===
    mano_obra = orden.mano_obra_costo or 0
    costo_total = orden.costo_total or 0
    
    totales_container_data = []
    
    # Mano de obra
    mano_obra_row = []
    mano_obra_row.append(Paragraph("MANO DE OBRA:", total_label_style))
    mano_obra_row.append(Paragraph(f"${mano_obra:.2f}", total_value_style))
    if orden.mano_obra_desc:
        mano_obra_row.append(Paragraph(f"({orden.mano_obra_desc})", mano_obra_desc_style))
    totales_container_data.append(mano_obra_row)
    
    # Separador
    totales_container_data.append([Paragraph("", styles['Normal'])])
    
    # Total principal
    total_row = []
    total_row.append(Paragraph("TOTAL A PAGAR:", total_principal_label_style))
    total_row.append(Paragraph(f"${costo_total:.2f}", total_principal_value_style))
    totales_container_data.append(total_row)
    
    # Crear tabla de totales con fondo degradado simulado
    totales_table = Table(totales_container_data, colWidths=[4*inch, 2*inch])
    totales_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_SECUNDARIO),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LINEBELOW', (0, 1), (-1, 1), 2, colors.HexColor('rgba(255,255,255,0.3)')),
        ('TOPPADDING', (0, 2), (-1, 2), 5),
        ('BOTTOMPADDING', (0, 2), (-1, 2), 5),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ]))
    story.append(totales_table)
    story.append(Spacer(1, 0.15*inch))
    
    # === NOTAS ADICIONALES ===
    if orden.notas_cliente:
        notas_data = [[
            Paragraph("📝 OBSERVACIONES", notas_title_style),
            Paragraph(orden.notas_cliente, notas_texto_style)
        ]]
        tabla_notas = Table(notas_data, colWidths=[7.4*inch])
        tabla_notas.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), COLOR_NOTAS_BG),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINEWIDTH', (0, 0), (0, -1), 4, COLOR_NOTAS_BORDE),
            ('LINEBEFORE', (0, 0), (0, -1), 4, COLOR_NOTAS_BORDE),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(tabla_notas)
        story.append(Spacer(1, 0.15*inch))
    
    # === FIRMAS ===
    story.append(Spacer(1, 0.2*inch))
    
    firma_left_data = [
        [Paragraph("__________________________", ParagraphStyle('FirmaLinea', parent=styles['Normal'], fontSize=12, textColor=COLOR_TEXTO, alignment=TA_CENTER))],
        [Paragraph("FIRMA DEL TÉCNICO", firma_label_style)],
        [Paragraph("Responsable del servicio", firma_sublabel_style)]
    ]
    tabla_firma_izq = Table(firma_left_data, colWidths=[3.2*inch])
    tabla_firma_izq.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    firma_right_data = [
        [Paragraph("__________________________", ParagraphStyle('FirmaLinea2', parent=styles['Normal'], fontSize=12, textColor=COLOR_TEXTO, alignment=TA_CENTER))],
        [Paragraph("FIRMA DEL CLIENTE", firma_label_style)],
        [Paragraph("Conformidad del servicio", firma_sublabel_style)]
    ]
    tabla_firma_der = Table(firma_right_data, colWidths=[3.2*inch])
    tabla_firma_der.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    firmas_grid = Table([[tabla_firma_izq, tabla_firma_der]], colWidths=[3.2*inch, 3.2*inch])
    firmas_grid.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(firmas_grid)
    
    # === FOOTER ===
    story.append(Spacer(1, 0.2*inch))
    
    footer_text = "Gracias por confiar en nuestros servicios. Este documento es su comprobante de reparación."
    story.append(Paragraph(footer_text, footer_style))
    
    nit = config.get('nit_taller', '')
    if nit:
        story.append(Paragraph(f"NIT/CI: {nit}", footer_nit_style))
    
    # Linea superior del footer
    footer_line = Table([['']], colWidths=[7.4*inch])
    footer_line.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 2, COLOR_BORDE),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
    ]))
    story.insert(-3, footer_line)  # Insertar antes del texto del footer
    
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
