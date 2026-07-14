"""
Sistema de Gestión para Taller de Reparación y Mantenimiento de Impresoras
Adaptado a la realidad cubana - Junio 2026

Punto de entrada de la aplicación Flask
"""
import os
import click
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import db

# Cargar variables de entorno
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv no instalado, usar solo variables de entorno del sistema

# Inicialización de la aplicación
app = Flask(__name__)

# ============================================================
# CONFIGURACIÓN SEGURA
# ============================================================
# Usar variable de entorno para SECRET_KEY
app.config['SECRET_KEY'] = os.getenv(
    'SECRET_KEY',
    'dev-key-cambiar-en-produccion-generar-con-secrets.token_hex(32)'
)

# Advertencia si se usa clave por defecto en producción
if os.getenv('FLASK_ENV') == 'production' and app.config['SECRET_KEY'] == 'dev-key-cambiar-en-produccion-generar-con-secrets.token_hex(32)':
    print("\n" + "="*60)
    print("⚠️  ADVERTENCIA CRÍTICA DE SEGURIDAD")
    print("="*60)
    print("SECRET_KEY no está configurada en producción.")
    print("Esto expone la aplicación a ataques de sesión.")
    print("\nAcciones requeridas:")
    print("1. Generar clave: python -c \"import secrets; print(secrets.token_hex(32))\"")
    print("2. Configurar en variable de entorno: export SECRET_KEY=<valor-generado>")
    print("="*60 + "\n")

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'sqlite:///taller.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backup')

# Inicialización de extensiones
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, inicie sesión para acceder.'
login_manager.login_message_category = 'warning'

# Importar modelos después de inicializar db
from models import Usuario, Cliente, Dispositivo, Tecnico, CategoriaPieza, Pieza, Orden, OrdenPieza, MovimientoInventario, Configuracion, Gasto, Proveedor, Contrato, OrdenNota

# Cargar usuario para Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import Usuario
    return db.session.get(Usuario, int(user_id))

# Ruta del dashboard (página principal)
@app.route('/')
@login_required
def dashboard():
    """Panel de control con indicadores básicos y financieros - Filtrado por rol"""
    from datetime import datetime, timedelta
    
    # Obtener parámetros de filtro temporal
    filtro_periodo = request.args.get('periodo', 'este_mes')
    fecha_inicio = request.args.get('fecha_inicio', '')
    fecha_fin = request.args.get('fecha_fin', '')
    
    # Calcular fechas según el período seleccionado
    ahora = datetime.now()
    if filtro_periodo == 'hoy':
        fecha_inicio_dt = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
        fecha_fin_dt = ahora
        fecha_inicio = fecha_inicio_dt.strftime('%Y-%m-%d')
        fecha_fin = ahora.strftime('%Y-%m-%d')
    elif filtro_periodo == 'este_mes':
        fecha_inicio_dt = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        fecha_fin_dt = ahora
        fecha_inicio = fecha_inicio_dt.strftime('%Y-%m-%d')
        fecha_fin = ahora.strftime('%Y-%m-%d')
    elif filtro_periodo == 'este_anio':
        fecha_inicio_dt = ahora.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        fecha_fin_dt = ahora
        fecha_inicio = fecha_inicio_dt.strftime('%Y-%m-%d')
        fecha_fin = ahora.strftime('%Y-%m-%d')
    elif filtro_periodo == 'personalizado' and fecha_inicio and fecha_fin:
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
    else:
        # Por defecto: este mes
        filtro_periodo = 'este_mes'
        fecha_inicio_dt = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        fecha_fin_dt = ahora
        fecha_inicio = fecha_inicio_dt.strftime('%Y-%m-%d')
        fecha_fin = ahora.strftime('%Y-%m-%d')
    
    # ==========================================
    # ESTADÍSTICAS SEGÚN ROL DEL USUARIO
    # ==========================================
    rol = current_user.rol
    
    # Inicializar contexto base
    total_ordenes_activas = 0
    ordenes_pendientes_diagnostico = 0
    ordenes_listas_entregar = 0
    piezas_stock_bajo = 0
    total_usuarios = 0
    usuarios_por_rol = {}
    ingresos_brutos = 0
    inversion_piezas = 0
    valor_inventario = 0
    ganancia_neta = 0
    gastos_operativos = 0
    isip_calculado = 0
    seguridad_social = 0
    total_tributos = 0
    ganancia_acumulada_anio = 0
    regimen_fiscal = 'general'
    ingresos_mensuales = []
    ultimas_ordenes = []
    reingresos_garantia_mes = 0
    ordenes_estancadas = []
    garantias_por_vencer = []
    mantenimientos_por_vencer = []
    total_clientes = 0
    total_dispositivos = 0
    total_tecnicos = 0
    total_piezas = 0
    
    # Variables específicas para cliente
    mis_ordenes = []
    total_ordenes_cliente = 0
    total_dispositivos_cliente = 0
    ordenes_pendientes_cliente = 0
    ordenes_reparacion_cliente = 0
    ordenes_completadas_cliente = 0
    
    if rol == 'administrador':
        # ===== ADMINISTRADOR: Todo sin restricciones =====
        total_ordenes_activas = Orden.query.filter(Orden.estado.in_(['Recibido', 'En diagnostico', 'Esperando piezas', 'En reparacion', 'Listo para entregar'])).count()
        ordenes_pendientes_diagnostico = Orden.query.filter_by(estado='En diagnostico').count()
        ordenes_listas_entregar = Orden.query.filter_by(estado='Listo para entregar').count()
        piezas_stock_bajo = Pieza.query.filter(Pieza.cantidad <= Pieza.cantidad_minima).count()
        
        # Estadísticas de órdenes para tarjetas del dashboard
        total_ordenes = Orden.query.count()
        ordenes_completadas = Orden.query.filter_by(estado='Entregado').count()
        ordenes_pendientes = Orden.query.filter(Orden.estado.in_(['Recibido', 'En diagnostico', 'Esperando piezas', 'En reparacion', 'Listo para entregar'])).count()
        
        # Estadísticas de usuarios
        total_usuarios = Usuario.query.count()
        usuarios_por_rol = {
            'administrador': Usuario.query.filter_by(rol='administrador', activo=1).count(),
            'tecnico': Usuario.query.filter_by(rol='tecnico', activo=1).count(),
            'proveedor': Usuario.query.filter_by(rol='proveedor', activo=1).count(),
            'cliente': Usuario.query.filter_by(rol='cliente', activo=1).count()
        }
        
        total_clientes = Cliente.query.count()
        total_dispositivos = Dispositivo.query.count()
        total_tecnicos = Tecnico.query.count()
        total_piezas = Pieza.query.count()
        
        # Métricas financieras
        ordenes_entregadas = Orden.query.filter(
            Orden.estado == 'Entregado',
            Orden.fecha_entrega >= fecha_inicio,
            Orden.fecha_entrega <= fecha_fin
        ).all()
        
        ingresos_brutos = sum(o.costo_total for o in ordenes_entregadas) or 0
        
        inversion_piezas = 0
        for orden in ordenes_entregadas:
            for op in orden.piezas_usadas:
                if op.pieza_rel:
                    inversion_piezas += op.cantidad * op.pieza_rel.precio_costo
        
        valor_inventario = sum(p.cantidad * p.precio_costo for p in Pieza.query.all()) or 0
        
        gastos_operativos = db.session.query(db.func.sum(Gasto.monto)).filter(
            Gasto.fecha >= fecha_inicio,
            Gasto.fecha <= fecha_fin
        ).scalar() or 0
        
        ganancia_neta = ingresos_brutos - inversion_piezas - gastos_operativos
        
        # Cálculo de tributos
        config = {}
        for c in Configuracion.query.all():
            config[c.clave] = c.valor
        
        regimen_fiscal = config.get('regimen_fiscal', 'general')
        
        inicio_anio = ahora.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d')
        ordenes_anio = Orden.query.filter(
            Orden.estado == 'Entregado',
            Orden.fecha_entrega >= inicio_anio,
            Orden.fecha_entrega <= ahora.strftime('%Y-%m-%d')
        ).all()
        
        ingresos_anio = sum(o.costo_total for o in ordenes_anio) or 0
        inversion_piezas_anio = 0
        for orden in ordenes_anio:
            for op in orden.piezas_usadas:
                if op.pieza_rel:
                    inversion_piezas_anio += op.cantidad * op.pieza_rel.precio_costo
        
        gastos_anio = db.session.query(db.func.sum(Gasto.monto)).filter(
            Gasto.fecha >= inicio_anio,
            Gasto.fecha <= ahora.strftime('%Y-%m-%d')
        ).scalar() or 0
        
        ganancia_acumulada_anio = ingresos_anio - inversion_piezas_anio - gastos_anio
        
        if regimen_fiscal == 'simplificado':
            cuota_fija = float(config.get('cuota_fija_mensual', 0))
            dias_periodo = (fecha_fin_dt - fecha_inicio_dt).days + 1
            meses_periodo = max(1, dias_periodo / 30)
            isip_calculado = cuota_fija * meses_periodo
        else:
            tasas = [
                (float(config.get('limite_isip_1', 10000)), float(config.get('tasa_isip_1', 5))),
                (float(config.get('limite_isip_2', 20000)), float(config.get('tasa_isip_2', 10))),
                (float(config.get('limite_isip_3', 30000)), float(config.get('tasa_isip_3', 15))),
                (float(config.get('limite_isip_4', 40000)), float(config.get('tasa_isip_4', 20))),
                (float(config.get('limite_isip_5', 50000)), float(config.get('tasa_isip_5', 25))),
                (float('inf'), float(config.get('tasa_isip_6', 30)))
            ]
            
            ganancia_restante = ganancia_acumulada_anio
            limite_anterior = 0
            
            for limite, tasa in tasas:
                if ganancia_restante <= 0:
                    break
                tramo = min(ganancia_restante, limite - limite_anterior)
                if tramo > 0:
                    isip_calculado += tramo * (tasa / 100)
                ganancia_restante -= tramo
                limite_anterior = limite
        
        ss_porcentaje = float(config.get('seguridad_social_porcentaje', 5))
        ss_base = config.get('seguridad_social_base', 'ganancia')
        base_ss = ganancia_neta if ss_base == 'ganancia' else ingresos_brutos
        seguridad_social = base_ss * (ss_porcentaje / 100) if base_ss > 0 else 0
        
        total_tributos = isip_calculado + seguridad_social
        
        # Ingresos mensuales
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
            ingreso = db.session.query(db.func.sum(Orden.costo_total)).filter(
                Orden.estado == 'Entregado',
                Orden.fecha_entrega >= inicio,
                Orden.fecha_entrega < fin
            ).scalar() or 0
            nombres_meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
            ingresos_mensuales.append({'mes': nombres_meses[mes-1], 'ingreso': ingreso})
        
        # Últimas órdenes y otros indicadores
        ultimas_ordenes = Orden.query.order_by(Orden.fecha_entrada.desc()).limit(5).all()
        
        reingresos_garantia_mes = Orden.query.filter(
            Orden.es_reingreso == 1,
            Orden.tipo_orden == 'garantia',
            Orden.fecha_entrada >= fecha_inicio,
            Orden.fecha_entrada <= fecha_fin
        ).count()
        
        dias_estancia = 3
        fecha_limite = (ahora - timedelta(days=dias_estancia)).strftime('%Y-%m-%d')
        ordenes_estancadas = Orden.query.filter(
            Orden.estado.in_(['Recibido', 'En diagnostico']),
            Orden.fecha_entrada < fecha_limite
        ).all()
        
        fecha_proxima_vencimiento = (ahora + timedelta(days=7)).strftime('%Y-%m-%d')
        garantias_por_vencer = Orden.query.filter(
            Orden.fecha_fin_garantia != None,
            Orden.fecha_fin_garantia <= fecha_proxima_vencimiento,
            Orden.fecha_fin_garantia >= ahora.strftime('%Y-%m-%d'),
            Orden.es_reingreso == 0
        ).all()
        
        contratos_activos = Contrato.query.filter_by(activo=1).all()
        mantenimientos_por_vencer = []
        for contrato in contratos_activos:
            proxima = contrato.calcular_proxima_visita()
            if proxima:
                try:
                    proxima_dt = datetime.strptime(proxima, '%Y-%m-%d')
                    if proxima_dt <= ahora + timedelta(days=7):
                        mantenimientos_por_vencer.append({
                            'cliente': contrato.cliente.nombre,
                            'proxima_visita': proxima,
                            'frecuencia': contrato.frecuencia
                        })
                except:
                    pass
    
    elif rol == 'tecnico':
        # ===== TÉCNICO: Solo reparaciones y dispositivos =====
        total_ordenes_activas = Orden.query.filter(Orden.estado.in_(['Recibido', 'En diagnostico', 'Esperando piezas', 'En reparacion', 'Listo para entregar'])).count()
        ordenes_pendientes_diagnostico = Orden.query.filter_by(estado='En diagnostico').count()
        ordenes_listas_entregar = Orden.query.filter_by(estado='Listo para entregar').count()
        piezas_stock_bajo = Pieza.query.filter(Pieza.cantidad <= Pieza.cantidad_minima).count()
        total_dispositivos = Dispositivo.query.count()
        total_piezas = Pieza.query.count()
        
        # Últimas órdenes (para ver el flujo de trabajo)
        ultimas_ordenes = Orden.query.order_by(Orden.fecha_entrada.desc()).limit(5).all()
        
        # NO incluye: financiero, tributos, usuarios, clientes
    
    elif rol == 'proveedor':
        # ===== PROVEEDOR: Solo inventario =====
        total_piezas = Pieza.query.count()
        piezas_stock_bajo = Pieza.query.filter(Pieza.cantidad <= Pieza.cantidad_minima).count()
        valor_inventario = sum(p.cantidad * p.precio_costo for p in Pieza.query.all()) or 0
        
        # NO incluye: órdenes, clientes, dispositivos, financiero, usuarios
    
    elif rol == 'cliente':
        # ===== CLIENTE: EXCLUSIVAMENTE sus propios datos =====
        # FILTRO CRÍTICO: solo sus datos usando current_user.cliente_id
        if current_user.cliente_id:
            mis_ordenes = Orden.query.filter_by(cliente_id=current_user.cliente_id).order_by(Orden.fecha_entrada.desc()).limit(5).all()
            total_ordenes_cliente = Orden.query.filter_by(cliente_id=current_user.cliente_id).count()
            total_dispositivos_cliente = Dispositivo.query.filter_by(cliente_id=current_user.cliente_id).count()
            ordenes_pendientes_cliente = Orden.query.filter_by(cliente_id=current_user.cliente_id, estado='Pendiente').count()
            ordenes_reparacion_cliente = Orden.query.filter_by(cliente_id=current_user.cliente_id, estado='En reparación').count()
            ordenes_completadas_cliente = Orden.query.filter_by(cliente_id=current_user.cliente_id, estado='Entregado').count()
            
            # Contar órdenes activas del cliente
            total_ordenes_activas = Orden.query.filter_by(cliente_id=current_user.cliente_id).filter(
                Orden.estado.in_(['Recibido', 'En diagnostico', 'Esperando piezas', 'En reparacion', 'Listo para entregar'])
            ).count()
        else:
            # Si no tiene cliente_id asociado, mostrar ceros
            mis_ordenes = []
            total_ordenes_cliente = 0
            total_dispositivos_cliente = 0
            ordenes_pendientes_cliente = 0
            ordenes_reparacion_cliente = 0
            ordenes_completadas_cliente = 0
            total_ordenes_activas = 0
        
        # NO incluye: nada global, financiero, tributos, usuarios, otros clientes
    
    return render_template('dashboard.html', 
                         total_ordenes_activas=total_ordenes_activas,
                         ordenes_pendientes_diagnostico=ordenes_pendientes_diagnostico,
                         ordenes_listas_entregar=ordenes_listas_entregar,
                         piezas_stock_bajo=piezas_stock_bajo,
                         # Estadísticas de usuarios
                         total_usuarios=total_usuarios,
                         usuarios_por_rol=usuarios_por_rol,
                         ultimas_ordenes=ultimas_ordenes,
                         ingresos_mes=ingresos_brutos,
                         ingresos_mensuales=ingresos_mensuales,
                         # Métricas financieras
                         inversion_piezas=inversion_piezas,
                         valor_inventario=valor_inventario,
                         ingresos_brutos=ingresos_brutos,
                         ganancia_neta=ganancia_neta,
                         gastos_operativos=gastos_operativos,
                         # Tributos
                         isip_calculado=isip_calculado,
                         seguridad_social=seguridad_social,
                         total_tributos=total_tributos,
                         ganancia_acumulada_anio=ganancia_acumulada_anio,
                         regimen_fiscal=regimen_fiscal,
                         # Filtros
                         filtro_periodo=filtro_periodo,
                         fecha_inicio=fecha_inicio,
                         fecha_fin=fecha_fin,
                         # Nuevos indicadores
                         reingresos_garantia_mes=reingresos_garantia_mes,
                         ordenes_estancadas=ordenes_estancadas,
                         garantias_por_vencer=garantias_por_vencer,
                         mantenimientos_por_vencer=mantenimientos_por_vencer,
                         # Datos específicos por rol
                         total_clientes=total_clientes,
                         total_dispositivos=total_dispositivos,
                         total_tecnicos=total_tecnicos,
                         total_piezas=total_piezas,
                         # Estadísticas de órdenes para administrador
                         total_ordenes=total_ordenes,
                         ordenes_completadas=ordenes_completadas,
                         ordenes_pendientes=ordenes_pendientes,
                         # Datos específicos para cliente
                         mis_ordenes=mis_ordenes,
                         total_ordenes_cliente=total_ordenes_cliente,
                         total_dispositivos_cliente=total_dispositivos_cliente,
                         ordenes_pendientes_cliente=ordenes_pendientes_cliente,
                         ordenes_reparacion_cliente=ordenes_reparacion_cliente,
                         ordenes_completadas_cliente=ordenes_completadas_cliente)

# Importar rutas
from routes.auth import auth_bp
from routes.clientes import clientes_bp
from routes.dispositivos import dispositivos_bp
from routes.ordenes import ordenes_bp
from routes.inventario import inventario_bp
from routes.tecnicos import tecnicos_bp
from routes.reportes import reportes_bp
from routes.backup import backup_bp
from routes.ayuda.ayuda import ayuda_bp
from routes.proveedores import proveedores_bp
from routes.contratos import contratos_bp
from routes.usuarios import usuarios_bp

# Importar decorador de roles
from routes.decorators import rol_requerido

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(clientes_bp, url_prefix='/clientes')
app.register_blueprint(dispositivos_bp, url_prefix='/dispositivos')
app.register_blueprint(ordenes_bp, url_prefix='/ordenes')
app.register_blueprint(inventario_bp, url_prefix='/inventario')
app.register_blueprint(tecnicos_bp, url_prefix='/tecnicos')
app.register_blueprint(reportes_bp, url_prefix='/reportes')
app.register_blueprint(backup_bp, url_prefix='/backup')
app.register_blueprint(ayuda_bp, url_prefix='/ayuda')
app.register_blueprint(proveedores_bp, url_prefix='/proveedores')
app.register_blueprint(contratos_bp, url_prefix='/contratos')
app.register_blueprint(usuarios_bp, url_prefix='/usuarios')

# Rutas API globales para acceso directo desde cualquier template
@app.route('/api/piezas')
@rol_requerido(['administrador', 'tecnico', 'proveedor'])
def api_piezas_global():
    """API global para buscar piezas por nombre (usada en formularios de órdenes)
    
    Acceso restringido a administradores, técnicos y proveedores.
    """
    from models import Pieza
    from flask import jsonify, request
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
        'stock': p.cantidad
    } for p in piezas]
    return jsonify(resultado)


@app.route('/api/clientes/<int:cliente_id>/dispositivos')
@rol_requerido(['administrador', 'tecnico'])
def api_dispositivos_cliente_global(cliente_id):
    """API global para obtener dispositivos de un cliente
    
    Acceso restringido a administradores y técnicos.
    """
    from models import Dispositivo
    from flask import jsonify
    dispositivos = Dispositivo.query.filter_by(cliente_id=cliente_id).all()
    resultado = [{'id': d.id, 'texto': f'{d.marca} {d.modelo} - {d.tipo}'} for d in dispositivos]
    return jsonify(resultado)

# Context processor para hacer disponible el año actual en todos los templates
@app.context_processor
def inject_year():
    return {'current_year': datetime.now().year}


@app.context_processor
def inject_configuracion_taller():
    """Inyecta la configuración del taller en todas las plantillas"""
    config = {}
    for c in Configuracion.query.all():
        config[c.clave] = c.valor
    return {'config_taller': config}

# Agregar el filtro 'zip' a Jinja2 (útil para iterar sobre múltiples listas en templates)
@app.template_filter('zip')
def zip_filter(*args):
    """Filtro para usar zip() en templates Jinja2"""
    return zip(*args)

def crear_datos_iniciales():
    """Crea datos iniciales si no existen"""
    # Crear usuario administrador por defecto
    if not Usuario.query.filter_by(usuario='admin').first():
        print("\n" + "="*60)
        print("⚠️  PRIMERA INSTALACIÓN - CONFIGURACIÓN INICIAL")
        print("="*60)
        print("\nCreando usuario administrador por defecto...")
        print("Usuario: admin")
        print("Contraseña: Taller2026")
        print("\n🔒 ACCIÓN REQUERIDA:")
        print("   1. Inicie sesión con estas credenciales")
        print("   2. Vaya a 'Cambiar Clave' inmediatamente")
        print("   3. Cambie la contraseña a una contraseña fuerte")
        print("      Requisitos:")
        print("      - Mínimo 8 caracteres")
        print("      - Incluir mayúsculas, minúsculas, números")
        print("\n" + "="*60 + "\n")
        
        admin = Usuario(
            nombre='Administrador',
            usuario='admin',
            password_hash=generate_password_hash('Taller2026'),
            rol='administrador',
            activo=1
        )
        db.session.add(admin)
        
        # Crear categorías de piezas típicas
        categorias = ['Cartucho', 'Tóner', 'Cinta', 'Fusor', 'Rodillo', 'Chip', 'Placa electrónica', 'Otro']
        for cat in categorias:
            categoria = CategoriaPieza(nombre=cat)
            db.session.add(categoria)
        
        # Crear configuración por defecto
        config_vals = {
            'nombre_taller': 'Taller de Impresoras',
            'direccion_taller': 'Dirección del taller',
            'telefono_taller': '00000000',
            'email_taller': '',
            'nit_taller': '',
            'responsable_taller': '',
            # Configuración tributaria (régimen general de autónomos en Cuba)
            'regimen_fiscal': 'general',  # 'general' o 'simplificado'
            'cuota_fija_mensual': '0',
            'tasa_isip_1': '5',      # Hasta 10,000 CUP
            'tasa_isip_2': '10',     # De 10,001 a 20,000 CUP
            'tasa_isip_3': '15',     # De 20,001 a 30,000 CUP
            'tasa_isip_4': '20',     # De 30,001 a 40,000 CUP
            'tasa_isip_5': '25',     # De 40,001 a 50,000 CUP
            'tasa_isip_6': '30',     # Más de 50,000 CUP
            'limite_isip_1': '10000',
            'limite_isip_2': '20000',
            'limite_isip_3': '30000',
            'limite_isip_4': '40000',
            'limite_isip_5': '50000',
            'seguridad_social_porcentaje': '5',
            'seguridad_social_base': 'ganancia'  # 'ganancia' o 'ingreso'
        }
        for clave, valor in config_vals.items():
            config = Configuracion(clave=clave, valor=valor)
            db.session.add(config)
        
        # Crear técnico por defecto
        tecnico = Tecnico(nombre='Técnico General', especialidad='General', activo=1)
        db.session.add(tecnico)
        
        db.session.commit()
        print("✓ Datos iniciales creados correctamente.")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        crear_datos_iniciales()
    # Ejecutar en localhost:5000
    app.run(host='127.0.0.1', port=5000, debug=False)


# Comando CLI para crear usuarios desde consola
@app.cli.command('crear-usuario')
@click.option('--nombre', prompt='Nombre del usuario', help='Nombre completo del usuario')
@click.option('--usuario', prompt='Nombre de usuario (login)', help='Nombre de usuario para iniciar sesión')
@click.option('--password', prompt='Contraseña', hide_input=True, confirmation_prompt=True, help='Contraseña del usuario')
@click.option('--rol', default='tecnico', type=click.Choice(['administrador', 'tecnico', 'proveedor', 'cliente']), help='Rol del usuario')
@click.option('--activo', default=True, type=bool, help='Estado activo del usuario')
def crear_usuario(nombre, usuario, password, rol, activo):
    """Crea un nuevo usuario desde la línea de comandos."""
    from models import Usuario
    
    # Verificar si el usuario ya existe
    if Usuario.query.filter_by(usuario=usuario).first():
        click.echo(click.style(f'Error: El usuario "{usuario}" ya existe.', fg='red'))
        return
    
    # Crear el nuevo usuario
    nuevo_usuario = Usuario(
        nombre=nombre,
        usuario=usuario,
        rol=rol,
        activo=1 if activo else 0
    )
    nuevo_usuario.set_password(password)
    
    db.session.add(nuevo_usuario)
    db.session.commit()
    
    click.echo(click.style(f'Usuario "{usuario}" creado exitosamente con rol "{rol}".', fg='green'))


# Función auxiliar para crear usuarios programáticamente (para usar con python -c)
def crear_usuario_console(nombre, usuario, password, rol='tecnico', activo=True):
    """
    Crea un usuario desde la consola de Python.
    
    Uso: python -c "from app import app, crear_usuario_console; app.app_context().push(); crear_usuario_console('Juan Perez', 'juan', 'password123', 'tecnico')"
    
    Args:
        nombre: Nombre completo del usuario
        usuario: Nombre de usuario para login
        password: Contraseña del usuario
        rol: Rol del usuario ('administrador', 'tecnico', 'proveedor', 'cliente')
        activo: Estado activo del usuario (True/False)
    """
    from models import Usuario
    
    with app.app_context():
        # Verificar si el usuario ya existe
        if Usuario.query.filter_by(usuario=usuario).first():
            print(f'Error: El usuario "{usuario}" ya existe.')
            return None
        
        # Crear el nuevo usuario
        nuevo_usuario = Usuario(
            nombre=nombre,
            usuario=usuario,
            rol=rol,
            activo=1 if activo else 0
        )
        nuevo_usuario.set_password(password)
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        print(f'Usuario "{usuario}" creado exitosamente con rol "{rol}".')
        return nuevo_usuario
