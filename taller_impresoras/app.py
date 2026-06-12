"""
Sistema de Gestión para Taller de Reparación y Mantenimiento de Impresoras
Adaptado a la realidad cubana - Junio 2026

Punto de entrada de la aplicación Flask
"""
import os
from flask import Flask, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import db

# Inicialización de la aplicación
app = Flask(__name__)
app.config['SECRET_KEY'] = 'taller-impressoras-cuba-2026-clave-secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///taller.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backup')

# Inicialización de extensiones
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, inicie sesión para acceder.'
login_manager.login_message_category = 'warning'

# Importar modelos después de inicializar db
from models import Usuario, Cliente, Dispositivo, Tecnico, CategoriaPieza, Pieza, Orden, OrdenPieza, MovimientoInventario, Configuracion

# Cargar usuario para Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import Usuario
    return db.session.get(Usuario, int(user_id))

# Ruta del dashboard (página principal)
@app.route('/')
@login_required
def dashboard():
    """Panel de control con indicadores básicos"""
    # Contadores
    total_ordenes_activas = Orden.query.filter(Orden.estado.in_(['Recibido', 'En diagnostico', 'Esperando piezas', 'En reparacion', 'Listo para entregar'])).count()
    ordenes_pendientes_diagnostico = Orden.query.filter_by(estado='En diagnostico').count()
    ordenes_listas_entregar = Orden.query.filter_by(estado='Listo para entregar').count()
    piezas_stock_bajo = Pieza.query.filter(Pieza.cantidad <= Pieza.cantidad_minima).count()
    
    # Últimas 5 órdenes actualizadas
    ultimas_ordenes = Orden.query.order_by(Orden.fecha_entrada.desc()).limit(5).all()
    
    # Ingresos del mes actual
    ahora = datetime.now()
    inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ingresos_mes = db.session.query(db.func.sum(Orden.costo_total)).filter(
        Orden.estado == 'Entregado',
        Orden.fecha_entrega >= inicio_mes.strftime('%Y-%m-%d')
    ).scalar() or 0
    
    # Ingresos por mes (últimos 6 meses)
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
    
    return render_template('dashboard.html', 
                         total_ordenes_activas=total_ordenes_activas,
                         ordenes_pendientes_diagnostico=ordenes_pendientes_diagnostico,
                         ordenes_listas_entregar=ordenes_listas_entregar,
                         piezas_stock_bajo=piezas_stock_bajo,
                         ultimas_ordenes=ultimas_ordenes,
                         ingresos_mes=ingresos_mes,
                         ingresos_mensuales=ingresos_mensuales)

# Importar rutas
from routes.auth import auth_bp
from routes.clientes import clientes_bp
from routes.dispositivos import dispositivos_bp
from routes.ordenes import ordenes_bp
from routes.inventario import inventario_bp
from routes.tecnicos import tecnicos_bp
from routes.reportes import reportes_bp
from routes.backup import backup_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(clientes_bp, url_prefix='/clientes')
app.register_blueprint(dispositivos_bp, url_prefix='/dispositivos')
app.register_blueprint(ordenes_bp, url_prefix='/ordenes')
app.register_blueprint(inventario_bp, url_prefix='/inventario')
app.register_blueprint(tecnicos_bp, url_prefix='/tecnicos')
app.register_blueprint(reportes_bp, url_prefix='/reportes')
app.register_blueprint(backup_bp, url_prefix='/backup')

# Rutas API globales para acceso directo desde cualquier template
@app.route('/api/piezas')
@login_required
def api_piezas_global():
    """API global para buscar piezas por nombre (usada en formularios de órdenes)"""
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
@login_required
def api_dispositivos_cliente_global(cliente_id):
    """API global para obtener dispositivos de un cliente"""
    from models import Dispositivo
    from flask import jsonify
    dispositivos = Dispositivo.query.filter_by(cliente_id=cliente_id).all()
    resultado = [{'id': d.id, 'texto': f'{d.marca} {d.modelo} - {d.tipo}'} for d in dispositivos]
    return jsonify(resultado)

# Context processor para hacer disponible el año actual en todos los templates
@app.context_processor
def inject_year():
    return {'current_year': datetime.now().year}

# Agregar el filtro 'zip' a Jinja2 (útil para iterar sobre múltiples listas en templates)
@app.template_filter('zip')
def zip_filter(*args):
    """Filtro para usar zip() en templates Jinja2"""
    return zip(*args)

def crear_datos_iniciales():
    """Crea datos iniciales si no existen"""
    # Crear usuario administrador por defecto
    if not Usuario.query.filter_by(usuario='admin').first():
        admin = Usuario(
            nombre='Administrador',
            usuario='admin',
            password_hash=generate_password_hash('Taller2026'),
            rol='admin',
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
            'responsable_taller': ''
        }
        for clave, valor in config_vals.items():
            config = Configuracion(clave=clave, valor=valor)
            db.session.add(config)
        
        # Crear técnico por defecto
        tecnico = Tecnico(nombre='Técnico General', especialidad='General', activo=1)
        db.session.add(tecnico)
        
        db.session.commit()
        print("Datos iniciales creados correctamente.")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        crear_datos_iniciales()
    # Ejecutar en localhost:5000
    app.run(host='127.0.0.1', port=5000, debug=False)
