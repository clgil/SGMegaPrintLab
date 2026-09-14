"""
Sistema de Gestión para Taller de Reparación y Mantenimiento de Impresoras
Adaptado a la realidad cubana - Junio 2026

Punto de entrada de la aplicación Flask
"""
import os
import click
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Importar configuración
from config import config
from services.extensions import db, login_manager, init_extensions

# Importar modelos después de inicializar db
from models import Usuario, Cliente, Dispositivo, Tecnico, CategoriaPieza, Pieza, Orden, OrdenPieza, MovimientoInventario, Configuracion, Gasto, Proveedor, Contrato, OrdenNota


def create_app(config_name=None):
    """Factory function para crear la aplicación Flask"""
    
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    
    # Inicializar extensiones
    init_extensions(app)
    
    # Registrar blueprints
    from routes import register_blueprints
    register_blueprints(app)
    
    # Configurar carga de usuario para Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))
    
    # Registrar rutas principales
    register_main_routes(app)
    
    # Registrar comandos CLI
    register_cli_commands(app)
    
    return app


def register_main_routes(app):
    """Registra las rutas principales de la aplicación"""
    
    @app.route('/')
    @login_required
    def dashboard():
        """Panel de control con indicadores básicos y financieros - Filtrado por rol"""
        from services.dashboard_service import DashboardService
        
        # Obtener parámetros de filtro temporal
        filtro_periodo = request.args.get('periodo', 'este_mes')
        fecha_inicio = request.args.get('fecha_inicio', '')
        fecha_fin = request.args.get('fecha_fin', '')
        
        # Calcular fechas según el período seleccionado
        fechas = DashboardService.calcular_fechas_periodo(filtro_periodo, fecha_inicio, fecha_fin)
        filtro_periodo = fechas['filtro_periodo']
        fecha_inicio = fechas['fecha_inicio']
        fecha_fin = fechas['fecha_fin']
        fecha_inicio_dt = fechas['fecha_inicio_dt']
        fecha_fin_dt = fechas['fecha_fin_dt']
        
        # ==========================================
        # ESTADÍSTICAS SEGÚN ROL DEL USUARIO
        # ==========================================
        rol = current_user.rol
        
        # Inicializar contexto base
        context = {
            'filtro_periodo': filtro_periodo,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'total_ordenes_activas': 0,
            'ordenes_pendientes_diagnostico': 0,
            'ordenes_listas_entregar': 0,
            'piezas_stock_bajo': 0,
            'total_usuarios': 0,
            'usuarios_por_rol': {},
            'ingresos_brutos': 0,
            'inversion_piezas': 0,
            'valor_inventario': 0,
            'ganancia_neta': 0,
            'gastos_operativos': 0,
            'isip_calculado': 0,
            'seguridad_social': 0,
            'total_tributos': 0,
            'ganancia_acumulada_anio': 0,
            'regimen_fiscal': 'general',
            'ingresos_mensuales': [],
            'ultimas_ordenes': [],
            'reingresos_garantia_mes': 0,
            'ordenes_estancadas': [],
            'garantias_por_vencer': [],
            'mantenimientos_por_vencer': [],
            'total_clientes': 0,
            'total_dispositivos': 0,
            'total_tecnicos': 0,
            'total_piezas': 0,
            'mis_ordenes': [],
            'total_ordenes_cliente': 0,
            'total_dispositivos_cliente': 0,
            'ordenes_pendientes_cliente': 0,
            'ordenes_reparacion_cliente': 0,
            'ordenes_completadas_cliente': 0,
        }
        
        if rol == 'administrador':
            # ===== ADMINISTRADOR: Todo sin restricciones =====
            stats = DashboardService.obtener_estadisticas_administrador(
                fecha_inicio, fecha_fin, fecha_inicio_dt, fecha_fin_dt
            )
            
            context.update(stats)
            context['ingresos_mensuales'] = DashboardService.obtener_ingresos_mensuales()
            
            alertas = DashboardService.obtener_indicadores_alertas()
            context.update(alertas)
            
            context['ultimas_ordenes'] = Orden.query.order_by(Orden.fecha_entrada.desc()).limit(5).all()
            context['reingresos_garantia_mes'] = Orden.query.filter(
                Orden.es_reingreso == 1,
                Orden.tipo_orden == 'garantia',
                Orden.fecha_entrada >= fecha_inicio,
                Orden.fecha_entrada <= fecha_fin
            ).count()
            
            # Calcular tributos
            config_data = context.get('config', {})
            regimen_fiscal = context.get('regimen_fiscal', 'general')
            
            if regimen_fiscal == 'simplificado':
                cuota_fija = float(config_data.get('cuota_fija_mensual', 0))
                dias_periodo = (fecha_fin_dt - fecha_inicio_dt).days + 1
                meses_periodo = max(1, dias_periodo / 30)
                context['isip_calculado'] = cuota_fija * meses_periodo
            else:
                # Cálculo ISIP progresivo
                tasas = [
                    (float(config_data.get('limite_isip_1', 10000)), float(config_data.get('tasa_isip_1', 5))),
                    (float(config_data.get('limite_isip_2', 20000)), float(config_data.get('tasa_isip_2', 10))),
                    (float(config_data.get('limite_isip_3', 30000)), float(config_data.get('tasa_isip_3', 15))),
                    (float(config_data.get('limite_isip_4', 40000)), float(config_data.get('tasa_isip_4', 20))),
                    (float(config_data.get('limite_isip_5', 50000)), float(config_data.get('tasa_isip_5', 25))),
                    (float('inf'), float(config_data.get('tasa_isip_6', 30)))
                ]
                
                ganancia_restante = context['ganancia_acumulada_anio']
                limite_anterior = 0
                
                for limite, tasa in tasas:
                    if ganancia_restante <= 0:
                        break
                    tramo = min(ganancia_restante, limite - limite_anterior)
                    if tramo > 0:
                        context['isip_calculado'] += tramo * (tasa / 100)
                    ganancia_restante -= tramo
                    limite_anterior = limite
            
            # Seguridad social
            ss_porcentaje = float(config_data.get('seguridad_social_porcentaje', 5))
            ss_base = config_data.get('seguridad_social_base', 'ganancia')
            base_ss = context['ganancia_neta'] if ss_base == 'ganancia' else context['ingresos_brutos']
            context['seguridad_social'] = base_ss * (ss_porcentaje / 100) if base_ss > 0 else 0
            context['total_tributos'] = context['isip_calculado'] + context['seguridad_social']
        
        elif rol == 'tecnico':
            # ===== TÉCNICO: Solo reparaciones y dispositivos =====
            context['total_ordenes_activas'] = Orden.query.filter(
                Orden.estado.in_(['Recibido', 'En diagnostico', 'Esperando piezas', 'En reparacion', 'Listo para entregar'])
            ).count()
            context['ordenes_pendientes_diagnostico'] = Orden.query.filter_by(estado='En diagnostico').count()
            context['ordenes_listas_entregar'] = Orden.query.filter_by(estado='Listo para entregar').count()
            context['piezas_stock_bajo'] = Pieza.query.filter(Pieza.cantidad <= Pieza.cantidad_minima).count()
            context['total_dispositivos'] = Dispositivo.query.count()
            context['total_piezas'] = Pieza.query.count()
            context['ultimas_ordenes'] = Orden.query.order_by(Orden.fecha_entrada.desc()).limit(5).all()
        
        elif rol == 'proveedor':
            # ===== PROVEEDOR: Solo inventario =====
            context['total_piezas'] = Pieza.query.count()
            context['piezas_stock_bajo'] = Pieza.query.filter(Pieza.cantidad <= Pieza.cantidad_minima).count()
            context['valor_inventario'] = sum(p.cantidad * p.precio_costo for p in Pieza.query.all()) or 0
        
        elif rol == 'cliente':
            # ===== CLIENTE: EXCLUSIVAMENTE sus propios datos =====
            if current_user.cliente_id:
                context['mis_ordenes'] = Orden.query.filter_by(cliente_id=current_user.cliente_id).order_by(Orden.fecha_entrada.desc()).limit(5).all()
                context['total_ordenes_cliente'] = Orden.query.filter_by(cliente_id=current_user.cliente_id).count()
                context['total_dispositivos_cliente'] = Dispositivo.query.filter_by(cliente_id=current_user.cliente_id).count()
                context['ordenes_pendientes_cliente'] = Orden.query.filter_by(cliente_id=current_user.cliente_id, estado='Pendiente').count()
                context['ordenes_reparacion_cliente'] = Orden.query.filter_by(cliente_id=current_user.cliente_id, estado='En reparación').count()
                context['ordenes_completadas_cliente'] = Orden.query.filter_by(cliente_id=current_user.cliente_id, estado='Entregado').count()
                context['total_ordenes_activas'] = Orden.query.filter_by(cliente_id=current_user.cliente_id).filter(Orden.estado.in_(['Recibido', 'En diagnostico', 'Esperando piezas', 'En reparacion', 'Listo para entregar'])).count()
        
        return render_template('dashboard.html', **context)
    
    # Ruta de error 404
    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html', error='Recurso no encontrado'), 404
    
    # Ruta de error 500
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('error.html', error='Error interno del servidor'), 500


def register_cli_commands(app):
    """Registra los comandos CLI de la aplicación"""
    
    @app.cli.command('init-db')
    def init_db_command():
        """Inicializa la base de datos y crea datos iniciales"""
        from models import db, Usuario, Cliente, Dispositivo, Tecnico, CategoriaPieza, Pieza, Configuracion
        
        db.create_all()
        
        # Crear administrador por defecto si no existe
        admin = Usuario.query.filter_by(usuario='admin').first()
        if not admin:
            admin = Usuario(
                nombre='Administrador',
                usuario='admin',
                rol='administrador',
                activo=1
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("✓ Usuario administrador creado (usuario: admin, contraseña: admin123)")
        
        # Crear configuraciones por defecto
        config_vals = {
            'regimen_fiscal': 'general',
            'cuota_fija_mensual': '0',
            'tasa_isip_1': '5',
            'tasa_isip_2': '10',
            'tasa_isip_3': '15',
            'tasa_isip_4': '20',
            'tasa_isip_5': '25',
            'tasa_isip_6': '30',
            'limite_isip_1': '10000',
            'limite_isip_2': '20000',
            'limite_isip_3': '30000',
            'limite_isip_4': '40000',
            'limite_isip_5': '50000',
            'seguridad_social_porcentaje': '5',
            'seguridad_social_base': 'ganancia'
        }
        
        for clave, valor in config_vals.items():
            config = Configuracion.query.filter_by(clave=clave).first()
            if not config:
                config = Configuracion(clave=clave, valor=valor)
                db.session.add(config)
        
        # Crear técnico por defecto
        tecnico = Tecnico.query.filter_by(nombre='Técnico General').first()
        if not tecnico:
            tecnico = Tecnico(nombre='Técnico General', especialidad='General', activo=1)
            db.session.add(tecnico)
            print("✓ Técnico por defecto creado")
        
        db.session.commit()
        print("✓ Base de datos inicializada correctamente.")
    
    @app.cli.command('crear-usuario')
    @click.option('--nombre', prompt='Nombre del usuario', help='Nombre completo del usuario')
    @click.option('--usuario', prompt='Nombre de usuario (login)', help='Nombre de usuario para iniciar sesión')
    @click.option('--password', prompt='Contraseña', hide_input=True, confirmation_prompt=True, help='Contraseña del usuario')
    @click.option('--rol', default='tecnico', type=click.Choice(['administrador', 'tecnico', 'proveedor', 'cliente']), help='Rol del usuario')
    @click.option('--activo', default=True, type=bool, help='Estado activo del usuario')
    def crear_usuario_command(nombre, usuario, password, rol, activo):
        """Crea un nuevo usuario desde la línea de comandos."""
        # Verificar si el usuario ya existe
        existing = Usuario.query.filter_by(usuario=usuario).first()
        if existing:
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


# Crear instancia de la aplicación
app = create_app()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Ejecutar en localhost:5000
    app.run(host='127.0.0.1', port=5000, debug=False)
