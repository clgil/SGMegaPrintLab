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
from datetime import date, datetime

# Importar configuración
from config import config
from services.extensions import db, login_manager, migrate, init_extensions

# Importar modelos después de inicializar db
from models import Usuario, Cliente, Dispositivo, Tecnico, CategoriaPieza, Pieza, Orden, OrdenPieza, MovimientoInventario, Configuracion, Gasto, Proveedor, Contrato, OrdenNota, AuditLog

# Re-exportar el parser desde models para mantener una única implementación
from models import parsear_fecha_form as parsear_datetime_form


def create_app(config_name=None):
    """Factory function para crear la aplicación Flask"""
    
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    
    # Inicializar extensiones (SQLAlchemy, Flask-Login y Flask-Migrate/Alembic).
    # migrate.init_app() se ejecuta dentro de init_extensions: los comandos
    # `flask db init | migrate | upgrade | downgrade` quedan disponibles.
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
    
    # Registrar context processor para configuración del taller
    @app.context_processor
    def inject_configuracion_taller():
        """Inyecta la configuración del taller en todas las plantillas"""
        from models import Configuracion
        config = {}
        try:
            for c in Configuracion.query.all():
                config[c.clave] = c.valor
        except:
            pass  # Si falla, usar config vacía
        return {'config_taller': config}

    # Helpers de fechas disponibles en TODAS las plantillas sin pasarlos por render_template
    from models import fecha_input, datetime_input, fmt_fecha, fmt_fecha_hora

    @app.context_processor
    def inject_fecha_helpers():
        """Expone serializadores/formateadores de fecha a nivel de plantilla."""
        return {
            'fecha_input': fecha_input,       # date -> 'YYYY-MM-DD' (<input type=date>)
            'datetime_input': datetime_input, # datetime -> 'YYYY-MM-DDTHH:MM' (datetime-local)
            'fmt_fecha': fmt_fecha,           # visualización DD/MM/YYYY
            'fmt_fecha_hora': fmt_fecha_hora, # visualización DD/MM/YYYY HH:MM
        }

    app.template_filter('fecha')(fmt_fecha)
    app.template_filter('fecha_hora')(fmt_fecha_hora)
    # Alias con prefijo fmt_ (usado por templates/auditoria/*.html): sin este
    # registro el uso como filtro {{ x | fmt_fecha_hora }} lanza
    # TemplateAssertionError: No filter named 'fmt_fecha_hora'.
    app.template_filter('fmt_fecha')(fmt_fecha)
    app.template_filter('fmt_fecha_hora')(fmt_fecha_hora)
    app.template_filter('fecha_input')(fecha_input)
    app.template_filter('datetime_input')(datetime_input)

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
        """Crea los datos iniciales: usuario admin y configuraciones por defecto.

        NOTA IMPORTANTE: este comando YA NO llama a db.create_all().
        La estructura (esquema) de la base de datos se gestiona de forma
        exclusiva con Flask-Migrate/Alembic mediante `flask db upgrade`, para
        que las futuras versiones del software puedan evolucionar el esquema
        SIN perder los datos existentes de los talleres.
        """
        from models import db, Usuario, Cliente, Dispositivo, Tecnico, CategoriaPieza, Pieza, Configuracion
        
        # Verificar que el esquema ya fue creado por las migraciones
        from sqlalchemy import inspect
        tablas = set(inspect(db.engine).get_table_names())
        if 'usuarios' not in tablas or 'configuracion' not in tablas:
            print("✗ La base de datos aún no tiene esquema (tablas inexistentes).")
            print("  Ejecute primero:  flask db upgrade")
            print("  (init-db solo crea datos iniciales, ya NO crea tablas)")
            return

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
    
    @app.cli.command('purge-audit-log')
    @click.option('--dias', default=365, type=int,
                  help='Conservar solo los registros de auditoría de los últimos N días (defecto: 365)')
    @click.option('--si', is_flag=True, default=False,
                  help='Omitir la confirmación interactiva (uso en cron/automatización)')
    def purge_audit_log_command(dias, si):
        """Purga la bitácora de auditoría (mantenimiento por retención).

        ÚNICA vía autorizada para eliminar AuditLog: línea de comandos del
        servidor, fuera del alcance de cualquier rol desde la interfaz web.
        Así un administrador malintencionado no puede borrar sus propios
        rastros por HTTP; necesitaría acceso al sistema de archivos/servidor.
        """
        from datetime import timedelta
        from models import AuditLog
        corte = datetime.now() - timedelta(days=dias)
        antiguos = AuditLog.query.filter(AuditLog.timestamp < corte).count()
        if antiguos == 0:
            click.echo(f'No hay registros de auditoría anteriores a {dias} días.')
            return
        if not si and not click.confirm(
                f'¿Eliminar DEFINITIVAMENTE {antiguos} registro(s) de auditoría '
                f'más antiguos a {corte:%d/%m/%Y %H:%M}?'):
            click.echo('Operación cancelada. La bitácora NO se modificó.')
            return
        AuditLog.query.filter(AuditLog.timestamp < corte).delete()
        db.session.commit()
        click.echo(f'✓ Purga completa: {antiguos} registro(s) eliminados (retención {dias} días).')

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

    # ------------------------------------------------------------------
    # MIGRACIÓN DE DATOS: db.Text -> db.Date / db.DateTime
    # ------------------------------------------------------------------
    # Tabla -> {columna: 'date' | 'datetime'}
    COLUMNAS_FECHA = {
        'ordenes': {
            'fecha_entrada': 'date',
            'fecha_prevista': 'date',
            'fecha_entrega': 'date',
            'fecha_fin_garantia': 'date',
            'fecha_inicio_reparacion': 'datetime',
            'fecha_fin_reparacion': 'datetime',
        },
        'movimientos_inventario': {'fecha': 'date'},
        'gastos': {'fecha': 'date'},
        'proveedores': {'fecha_creacion': 'date'},
        'contratos': {
            'fecha_inicio': 'date',
            'fecha_fin': 'date',
            'ultima_visita': 'date',
        },
        'orden_notas': {'fecha_hora': 'datetime'},
    }

    @app.cli.command('fix-dates')
    @click.option('--dry-run', is_flag=True, default=False,
                  help='Solo muestra qué se convertiría, sin escribir en la BD.')
    def fix_dates_command(dry_run):
        """Convierte los strings de fecha/hora históricos a date/datetime nativos.

        SQLite almacena db.Date/db.DateTime como TEXT en formato ISO, por lo que
        NO se necesita ALTER TABLE (migración "in-place"): este comando reescribe
        cada fila para que SQLAlchemy pueda deserializarlas como objetos date y
        datetime. Es idempotente: puede ejecutarse varias veces sin dañar datos.
        """
        from sqlalchemy import inspect, text

        def _parse(valor, tipo):
            """Acepta los formatos legados observados en producción."""
            if valor is None:
                return None
            if isinstance(valor, (date, datetime)):  # ya migrada
                return valor
            s = str(valor).strip()
            if not s or s.upper() in ('NONE', 'NULL'):
                return None
            candidatos = (
                '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M',
                '%Y-%m-%dT%H:%M', '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y-%m',
            )
            for f in candidatos:
                try:
                    dt = datetime.strptime(s, f)
                    return dt.date() if tipo == 'date' else dt
                except ValueError:
                    continue
            try:  # último recurso: ISO con microsegundos/timezone-less
                dt = datetime.fromisoformat(s)
                return dt.date() if tipo == 'date' and not s.count(':') else dt
            except ValueError:
                raise ValueError(f"Valor no convertible: '{valor}'")

        def _serializar(v):
            """Cómo queda el valor en SQLite tras la migración."""
            if v is None:
                return None
            if isinstance(v, datetime):
                return v.isoformat(sep=' ', timespec='seconds')
            return v.isoformat()  # date -> 'YYYY-MM-DD'

        engine = db.engine
        tablas_existentes = set(inspect(engine).get_table_names())
        total_actualizados, total_validos, total_invalidos = 0, 0, 0
        estilo = click.style

        for tabla, columnas in COLUMNAS_FECHA.items():
            if tabla not in tablas_existentes:
                click.echo(estilo(f'– Tabla "{tabla}" no existe, se omite.', fg='yellow'))
                continue

            # Solo columnas que realmente sean TEXT en el esquema legado
            cols_reales = {c['name']: c for c in inspect(engine).get_columns(tabla)}
            col_pk = next((c['name'] for c in cols_reales.values() if c['primary_key']), 'id')

            a_convertir = {}
            for col, tipo in columnas.items():
                if col not in cols_reales:
                    click.echo(estilo(f'– {tabla}.{col} no existe, se omite.', fg='yellow'))
                    continue
                tipo_sql = (cols_reales[col]['type'] or '').upper()
                if tipo_sql in ('DATE', 'DATETIME', 'TIMESTAMP'):
                    click.echo(estilo(f'✓ {tabla}.{col} ya está tipada ({tipo_sql}).', fg='green'))
                    total_validos += 1
                    continue
                a_convertir[col] = tipo

            if not a_convertir:
                continue

            filas = engine.execute(text(f'SELECT * FROM "{tabla}"')).mappings().all()
            click.echo(f'\n→ Migrando tabla "{tabla}" ({len(filas)} filas, '
                       f'columnas: {", ".join(a_convertir)})')

            for fila in filas:
                cambios = {}
                for col, tipo in a_convertir.items():
                    try:
                        convertido = _parse(fila[col], tipo)
                    except ValueError as e:
                        total_invalidos += 1
                        click.echo(estilo(
                            f'  ✗ {tabla}#{fila[col_pk]}.{col}: {e} (se conserva el valor original)',
                            fg='red'))
                        continue
                    original = fila[col]
                    if isinstance(original, (date, datetime)) or original == _serializar(convertido):
                        continue  # ya tiene forma ISO correcta
                    cambios[col] = _serializar(convertido)

                if cambios:
                    total_actualizados += 1
                    if dry_run:
                        click.echo(f'  [dry-run] #{fila[col_pk]} -> '
                                   + ', '.join(f'{k}={v}' for k, v in cambios.items()))
                    else:
                        sets = ', '.join(f'"{c}" = :{c}' for c in cambios)
                        params = dict(cambios)
                        params['_pk'] = fila[col_pk]
                        engine.execute(
                            text(f'UPDATE "{tabla}" SET {sets} WHERE "{col_pk}" = :_pk'),
                            params)

        if dry_run:
            db.session.rollback()
            click.echo(estilo(f'\n[dry-run] Sin cambios escritos. Filas que se '
                              f'actualizarían: {total_actualizados}', fg='cyan'))
        else:
            # SQLAlchemy 2.x: el commit se hace a través de la conexión de la sesión
            db.session.commit()
            click.echo(estilo(f'\n✓ Migración fix-dates completada: '
                              f'{total_actualizados} filas actualizadas, '
                              f'{total_validos} columnas ya tipadas, '
                              f'{total_invalidos} valores ilegibles conservados.',
                              fg='green'))
            click.echo('Nota: verifique que el modelo use db.Date/db.DateTime y '
                       'ejecute `flask db-upgrade` si adopta Flask-Migrate.')


# Crear instancia de la aplicación
app = create_app()


if __name__ == '__main__':
    # El esquema de la BD se gestiona con Flask-Migrate (`flask db upgrade`).
    # Ya NO se llama a db.create_all() aquí: crear tablas "a mano" rompería
    # el control de versiones de Alembic y ocultaría migraciones pendientes.
    from sqlalchemy import inspect
    with app.app_context():
        if 'alembic_version' not in set(inspect(db.engine).get_table_names()):
            print("⚠  ADVERTENCIA: la base de datos no parece estar migrada.")
            print("   Ejecute:  flask db upgrade   (ver install.sh / install.bat)")

    # Ejecutar en localhost:5000
    app.run(host='127.0.0.1', port=5000, debug=False)
