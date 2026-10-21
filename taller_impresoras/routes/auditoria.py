"""
Rutas de auditoría (bitácora anti-fraude interno) — SGMegaPrintLab

Exposición: /admin/auditoria

SEGURIDAD:
- Acceso restringido al rol 'administrador' mediante el decorador
  @rol_requerido(['administrador']) (además de @login_required).
- La bitácora es SOLO LECTURA por diseño: este blueprint NO define ninguna
  vista POST/PUT/DELETE sobre AuditLog, y el modelo AuditLog no expone
  métodos de edición/eliminación. Un administrador puede CONSULTAR los
  registros de otros, pero no borrar sus propios rastros desde la interfaz.
- Filtros disponibles: usuario, tabla afectada y rango de fechas.
"""
from datetime import datetime

from flask import Blueprint, render_template, request
from flask_login import login_required

from models import db, AuditLog, Usuario
from routes.decorators import rol_requerido

auditoria_bp = Blueprint('auditoria', __name__, template_folder='../templates')

# Tablas que pueden filtrarse (nombre de tabla -> etiqueta visible)
TABLAS_AUDITADAS = {
    'ordenes': 'Órdenes',
    'piezas': 'Piezas (inventario)',
    'movimientos_inventario': 'Movimientos de inventario',
    'orden_piezas': 'Piezas usadas en órdenes',
    'gastos': 'Gastos',
    'proveedores': 'Proveedores',
    'clientes': 'Clientes',
    'dispositivos': 'Dispositivos',
    'tecnicos': 'Técnicos',
    'contratos': 'Contratos',
    'configuracion': 'Configuración',
    'usuarios': 'Usuarios',
    'orden_notas': 'Notas de órdenes',
}


def _parsear_fecha_arg(valor, fin_dia=False):
    """Convierte un 'YYYY-MM-DD' del formulario en datetime acotado.

    Devuelve None si viene vacío o es inválido (el filtro se ignora en vez
    de romper la vista). Si `fin_dia=True` devuelve 23:59:59 para incluir
    todo el día seleccionado.
    """
    if not valor:
        return None
    for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            dt = datetime.strptime(valor.strip(), fmt)
        except ValueError:
            continue
        return dt.replace(hour=23, minute=59, second=59) if fin_dia else dt
    return None


@auditoria_bp.route('/')
@login_required
@rol_requerido(['administrador'])
def index():
    """Listado de la bitácora con filtros por usuario, tabla y fechas."""
    try:
        pagina = int(request.args.get('pagina', 1) or 1)
    except (TypeError, ValueError):
        pagina = 1
    if pagina < 1:
        pagina = 1

    usuario = request.args.get('usuario', '').strip()
    tabla = request.args.get('tabla', '').strip()
    desde = _parsear_fecha_arg(request.args.get('desde', ''))
    hasta = _parsear_fecha_arg(request.args.get('hasta', ''), fin_dia=True)

    consulta = AuditLog.query

    if usuario:
        consulta = consulta.filter(AuditLog.username == usuario)
    if tabla and tabla in TABLAS_AUDITADAS:      # lista blanca anti inyección
        consulta = consulta.filter(AuditLog.table_name == tabla)
    if desde:
        consulta = consulta.filter(AuditLog.timestamp >= desde)
    if hasta:
        consulta = consulta.filter(AuditLog.timestamp <= hasta)

    paginacion = (consulta.order_by(AuditLog.timestamp.desc(), AuditLog.id.desc())
                  .paginate(page=pagina, per_page=50, error_out=False))

    total_registros = AuditLog.query.count()
    usuarios_con_actividad = [u[0] for u in
                              db.session.query(AuditLog.username)
                              .distinct().order_by(AuditLog.username).all() if u[0]]

    return render_template(
        'auditoria/index.html',
        logs=paginacion.items,
        paginacion=paginacion,
        total_registros=total_registros,
        tablas=TABLAS_AUDITADAS,
        usuarios=Usuario.query.order_by(Usuario.usuario).all(),
        usuarios_con_actividad=usuarios_con_actividad,
        f_usuario=usuario, f_tabla=tabla,
        f_desde=request.args.get('desde', ''),
        f_hasta=request.args.get('hasta', ''),
    )


@auditoria_bp.route('/detalle/<int:log_id>')
@login_required
@rol_requerido(['administrador'])
def detalle(log_id):
    """Vista de solo lectura de un registro de auditoría (valores old/new)."""
    log = db.session.get(AuditLog, log_id)
    if log is None:
        from flask import abort
        abort(404)
    return render_template('auditoria/detalle.html', log=log,
                           tablas=TABLAS_AUDITADAS)
