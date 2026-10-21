"""
Modelos de base de datos para el Sistema de Gestión de Taller de Impresoras
Adaptado a la realidad cubana - Junio 2026

Define todas las tablas según el esquema SQLite especificado en el PRD

Seguridad (anti-fraude interno): al final de este módulo se registran los
eventos `after_insert` / `after_update` / `after_delete` de SQLAlchemy sobre
los modelos críticos (Orden, Pieza, MovimientoInventario, ...) que escriben
automáticamente cada cambio en la tabla inmutable `audit_log`.
"""
import json
from datetime import date, datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event
from sqlalchemy.orm import object_session

# Importar la instancia db única desde extensions para evitar múltiples instancias
from services.extensions import db


def _add_months(ref: datetime, meses: int) -> datetime:
    """Suma N meses a una fecha preservando el día (ajusta al último día del mes)."""
    total = (ref.month - 1) + meses
    anio, mes = ref.year + total // 12, total % 12 + 1
    dia = min(ref.day, [31, 29 if anio % 4 == 0 and (anio % 100 != 0 or anio % 400 == 0)
                        else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mes - 1])
    return ref.replace(year=anio, month=mes, day=dia)


# ----------------------------------------------------------------------
# Utilidades de fechas para formularios (parseo string HTML -> date/datetime)
# ----------------------------------------------------------------------
def parsear_fecha_form(valor, tipo='date'):
    """Convierte el valor crudo de un input HTML en date/datetime nativo.

    - <input type="date">     -> 'YYYY-MM-DD'
    - <input type="datetime"> -> 'YYYY-MM-DDTHH:MM[:SS]'
    Devuelve None si viene vacío; lanza ValueError si el formato es inválido,
    para que la ruta rechace el submit y NO guarde basura en SQLite.
    """
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date() if tipo == 'date' else valor
    if isinstance(valor, date):
        return valor if tipo == 'date' else datetime(valor.year, valor.month, valor.day)

    valor = str(valor).strip()
    if not valor:
        return None

    formatos_fecha = ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y')
    formatos_datetime = ('%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S',
                         '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S')

    if tipo == 'date':
        for f in formatos_fecha:
            try:
                return datetime.strptime(valor, f).date()
            except ValueError:
                continue
    else:
        for f in formatos_datetime + formatos_fecha:
            try:
                return datetime.strptime(valor, f)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(valor)
        except ValueError:
            pass

    raise ValueError(f"Formato de fecha inválido: '{valor}'")


def fecha_input(value):
    """Serializa date/datetime -> 'YYYY-MM-DD' para <input type=date> en Jinja."""
    if value is None:
        return ''
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d')
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def datetime_input(value):
    """Serializa datetime -> 'YYYY-MM-DDTHH:MM' para <input type=datetime-local>."""
    if value is None:
        return ''
    if isinstance(value, (datetime, date)):
        return value.strftime('%Y-%m-%dT%H:%M') if isinstance(value, datetime) \
            else value.isoformat()
    return str(value)


def fmt_fecha(value):
    """Formatea date/datetime/str legada -> 'DD/MM/YYYY' para mostrar en plantillas."""
    if value is None:
        return ''
    if isinstance(value, (datetime, date)):
        return value.strftime('%d/%m/%Y')
    try:  # datos históricos sin normalizar (strings)
        return parsear_fecha_form(value, tipo='date').strftime('%d/%m/%Y')
    except ValueError:
        return str(value)


def fmt_fecha_hora(value):
    """Formatea datetime/date/str legada -> 'DD/MM/YYYY HH:MM' para mostrar en plantillas."""
    if value is None:
        return ''
    if isinstance(value, datetime):
        return value.strftime('%d/%m/%Y %H:%M')
    if isinstance(value, date):
        return value.strftime('%d/%m/%Y') + ' 00:00'
    try:  # datos históricos sin normalizar (strings)
        return parsear_fecha_form(value, tipo='datetime').strftime('%d/%m/%Y %H:%M')
    except ValueError:
        return str(value)

class Usuario(UserMixin, db.Model):
    """Tabla de usuarios con roles y autenticación"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.Text, nullable=False)
    usuario = db.Column(db.Text, unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    rol = db.Column(db.Text, default='administrador')
    activo = db.Column(db.Integer, default=1)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=True)
    
    # Relación con Cliente (solo para usuarios con rol 'cliente')
    cliente = db.relationship('Cliente', backref='usuario')
    
    # Roles válidos en el sistema
    ROLES_VALIDOS = ['administrador', 'tecnico', 'proveedor', 'cliente']
    
    # Mapeo de roles a permisos
    PERMISOS_POR_ROL = {
        'administrador': ['ver_dashboard', 'gestionar_ordenes', 'gestionar_clientes', 
                          'gestionar_inventario', 'gestionar_tecnicos', 'gestionar_proveedores',
                          'gestionar_contratos', 'ver_reportes', 'gestionar_usuarios',
                          'gestionar_configuracion', 'gestionar_backup'],
        'tecnico': ['ver_dashboard', 'gestionar_ordenes', 'ver_clientes', 
                    'ver_inventario', 'ver_reportes'],
        'proveedor': ['ver_dashboard', 'ver_ordenes', 'gestionar_productos'],
        'cliente': ['ver_dashboard', 'ver_ordenes_propias', 'ver_dispositivos_propios']
    }
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def tiene_permiso(self, permiso):
        """Verifica si el usuario tiene un permiso específico según su rol."""
        if not self.rol or self.rol not in self.PERMISOS_POR_ROL:
            return False
        permisos_usuario = self.PERMISOS_POR_ROL.get(self.rol, [])
        return permiso in permisos_usuario
    
    def es_administrador(self):
        """Verifica si el usuario tiene rol de administrador"""
        return self.rol == 'administrador'


class Cliente(db.Model):
    """Tabla de clientes del taller"""
    __tablename__ = 'clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.Text, nullable=False)
    telefono = db.Column(db.Text)
    direccion = db.Column(db.Text)
    tipo_cliente = db.Column(db.Text, nullable=False, default='Persona natural')
    activo = db.Column(db.Integer, default=1)
    
    # Valores válidos para tipo_cliente
    TIPOS_CLIENTE_VALIDOS = ['TCP', 'Mypyme', 'PDL', 'Empresa Estatal', 'CNA', 'CPA', 'Persona natural']
    
    # Relaciones
    dispositivos = db.relationship('Dispositivo', backref='cliente', lazy=True)
    ordenes = db.relationship('Orden', backref='cliente', lazy=True)
    
    def __repr__(self):
        return f'<Cliente {self.nombre}>'
    
    @classmethod
    def es_tipo_valido(cls, tipo):
        """Verifica si un tipo de cliente es válido"""
        return tipo in cls.TIPOS_CLIENTE_VALIDOS


class Dispositivo(db.Model):
    """Tabla de dispositivos (impresoras) de los clientes"""
    __tablename__ = 'dispositivos'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    marca = db.Column(db.Text)
    modelo = db.Column(db.Text)
    numero_serie = db.Column(db.Text)
    tipo = db.Column(db.Text)  # Láser, Inyección de tinta, Matricial, Multifuncional
    problema_frecuente = db.Column(db.Text)
    observaciones = db.Column(db.Text)
    
    # Relaciones
    ordenes = db.relationship('Orden', backref='dispositivo', lazy=True)
    
    def __repr__(self):
        return f'<Dispositivo {self.marca} {self.modelo}>'


class Tecnico(db.Model):
    """Tabla de técnicos del taller"""
    __tablename__ = 'tecnicos'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.Text, nullable=False)
    especialidad = db.Column(db.Text)
    activo = db.Column(db.Integer, default=1)
    costo_hora = db.Column(db.Float, default=0)  # Costo por hora para cálculo de productividad
    
    # Relaciones
    ordenes = db.relationship('Orden', backref='tecnico', lazy=True)
    
    def __repr__(self):
        return f'<Técnico {self.nombre}>'


class CategoriaPieza(db.Model):
    """Tabla de categorías de piezas"""
    __tablename__ = 'categorias_piezas'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.Text, nullable=False)
    
    # Relaciones
    piezas = db.relationship('Pieza', backref='categoria', lazy=True)
    
    def __repr__(self):
        return f'<Categoría {self.nombre}>'


class Pieza(db.Model):
    """Tabla de piezas y consumibles del inventario"""
    __tablename__ = 'piezas'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.Text, nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias_piezas.id'))
    codigo_interno = db.Column(db.Text)
    modelos_compatibles = db.Column(db.Text)
    cantidad = db.Column(db.Float, default=0)
    cantidad_minima = db.Column(db.Float, default=1)
    unidad = db.Column(db.Text, default='unidad')
    precio_costo = db.Column(db.Float, default=0)
    precio_venta = db.Column(db.Float, default=0)
    proveedor = db.Column(db.Text)  # Campo de texto legacy (respaldo)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'))  # Nueva relación
    
    # Relaciones
    movimientos = db.relationship('MovimientoInventario', backref='pieza', lazy=True)
    orden_piezas = db.relationship('OrdenPieza', back_populates='pieza_rel', lazy=True)
    
    def __repr__(self):
        return f'<Pieza {self.nombre}>'
    
    @property
    def stock_bajo(self):
        """Indica si la pieza está por debajo del stock mínimo"""
        return self.cantidad <= self.cantidad_minima
    
    @property
    def proveedor_nombre(self):
        """Obtiene el nombre del proveedor (de la relación o del campo texto)"""
        if self.proveedor_rel:
            return self.proveedor_rel.nombre
        return self.proveedor or 'N/A'


class Orden(db.Model):
    """Tabla de órdenes de reparación"""
    __tablename__ = 'ordenes'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_orden = db.Column(db.Text, unique=True, nullable=False)
    # Fechas tipadas: db.Date para fechas puras y db.DateTime para marcas de tiempo.
    # SQLAlchemy serializa/deserializa automáticamente contra el TEXT nativo de SQLite.
    fecha_entrada = db.Column(db.Date, nullable=False, default=date.today)
    fecha_prevista = db.Column(db.Date)
    fecha_entrega = db.Column(db.Date)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    dispositivo_id = db.Column(db.Integer, db.ForeignKey('dispositivos.id'))
    problema_reportado = db.Column(db.Text)
    diagnostico = db.Column(db.Text)
    estado = db.Column(db.Text, default='Recibido')
    tecnico_id = db.Column(db.Integer, db.ForeignKey('tecnicos.id'))
    mano_obra_desc = db.Column(db.Text)
    mano_obra_costo = db.Column(db.Float, default=0)
    costo_total = db.Column(db.Float, default=0)
    notas_internas = db.Column(db.Text)
    notas_cliente = db.Column(db.Text)
    
    # Campos de garantía
    garantia_meses = db.Column(db.Integer, default=0)  # Duración de garantía en meses
    fecha_fin_garantia = db.Column(db.Date)  # Fecha calculada de fin de garantía
    orden_original_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'))  # Para reingresos
    es_reingreso = db.Column(db.Integer, default=0)  # Indica si es reingreso por garantía
    tipo_orden = db.Column(db.Text, default='reparacion')  # reparacion, mantenimiento, garantia
    
    # Campos de tiempo de reparación (marcas de tiempo completas)
    fecha_inicio_reparacion = db.Column(db.DateTime)  # Cuando pasa a "En reparación"
    fecha_fin_reparacion = db.Column(db.DateTime)  # Cuando pasa a "Listo para entregar" o "Entregado"
    
    # Relaciones
    piezas_usadas = db.relationship('OrdenPieza', backref='orden', lazy=True, cascade='all, delete-orphan')
    notas = db.relationship('OrdenNota', backref='orden', lazy=True, order_by='OrdenNota.fecha_hora.desc()')
    orden_original = db.relationship('Orden', remote_side=[id], backref='reingresos')
    
    def __repr__(self):
        return f'<Orden {self.numero_orden}>'
    
    def calcular_total(self):
        """Calcula el costo total de la orden"""
        total_piezas = sum(op.cantidad * op.precio_unitario for op in self.piezas_usadas)
        self.costo_total = total_piezas + (self.mano_obra_costo or 0)
        return self.costo_total
    
    @property
    def tiempo_reparacion_horas(self):
        """Calcula el tiempo de reparación en horas (decimal).

        Trabaja directamente con objetos datetime nativos: SQLAlchemy ya
        convierte la columna db.DateTime al deserializar el registro.
        """
        inicio = self.fecha_inicio_reparacion
        fin = self.fecha_fin_reparacion
        if not isinstance(inicio, datetime) or not isinstance(fin, datetime):
            return None
        return round((fin - inicio).total_seconds() / 3600, 2)
    
    @property
    def garantia_vigente(self):
        """Verifica si la orden tiene garantía vigente.

        Compara date.today() contra la columna db.Date fecha_fin_garantia,
        sin necesidad de strptime ni bloques try/except.
        """
        fin_garantia = self.fecha_fin_garantia
        if not isinstance(fin_garantia, date):
            return False
        # La garantía cubre todo el día de vencimiento
        return date.today() <= fin_garantia
    
    def activar_garantia_desde_entrega(self):
        """Calcula fecha_fin_garantia a partir de la entrega y garantia_meses."""
        if self.fecha_entrega and self.garantia_meses:
            ref = self.fecha_entrega
            if isinstance(ref, datetime):
                ref = ref.date()
            self.fecha_fin_garantia = _add_months(datetime(ref.year, ref.month, ref.day),
                                                  self.garantia_meses).date()


class OrdenPieza(db.Model):
    """Tabla intermedia: piezas usadas en una orden"""
    __tablename__ = 'orden_piezas'
    
    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'), nullable=False)
    pieza_id = db.Column(db.Integer, db.ForeignKey('piezas.id'), nullable=True)  # Nullable para piezas manuales
    cantidad = db.Column(db.Float, nullable=False, default=1)
    precio_unitario = db.Column(db.Float, nullable=False)
    
    # Relación con Pieza (puede ser None para piezas manuales)
    pieza_rel = db.relationship('Pieza', back_populates='orden_piezas', foreign_keys=[pieza_id])
    
    def __repr__(self):
        return f'<OrdenPieza Orden:{self.orden_id} Pieza:{self.pieza_id}>'


class MovimientoInventario(db.Model):
    """Tabla de movimientos de inventario (entradas y salidas)"""
    __tablename__ = 'movimientos_inventario'
    
    id = db.Column(db.Integer, primary_key=True)
    pieza_id = db.Column(db.Integer, db.ForeignKey('piezas.id'), nullable=False)
    tipo = db.Column(db.Text, nullable=False)
    cantidad = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    concepto = db.Column(db.Text)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'))
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'))  # Proveedor de la entrada
    
    def __repr__(self):
        return f'<Movimiento {self.tipo} {self.cantidad} {self.pieza_id}>'


class Configuracion(db.Model):
    """Tabla de configuración del taller"""
    __tablename__ = 'configuracion'
    
    clave = db.Column(db.Text, primary_key=True)
    valor = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Configuración {self.clave}={self.valor}>'


class Gasto(db.Model):
    """Tabla de gastos operativos del taller (agua, electricidad, alquiler, etc.)"""
    __tablename__ = 'gastos'
    
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.Text, nullable=False)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    
    def __repr__(self):
        return f'<Gasto {self.descripcion} - ${self.monto}>'


class Proveedor(db.Model):
    """Tabla de proveedores de piezas y consumibles"""
    __tablename__ = 'proveedores'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.Text, nullable=False)
    contacto = db.Column(db.Text)
    telefono = db.Column(db.Text)
    tipo = db.Column(db.Text, default='informal', server_default='informal')  # formal o informal
    activo = db.Column(db.Integer, default=1)
    fecha_creacion = db.Column(db.Date, default=date.today)
    
    # Relaciones
    piezas = db.relationship('Pieza', backref='proveedor_rel', lazy=True)
    movimientos = db.relationship('MovimientoInventario', backref='proveedor_rel', lazy=True)
    
    def __repr__(self):
        return f'<Proveedor {self.nombre}>'


class Contrato(db.Model):
    """Tabla de contratos de mantenimiento periódico con clientes"""
    __tablename__ = 'contratos'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    descripcion = db.Column(db.Text)
    frecuencia = db.Column(db.Text, nullable=False)  # semanal, quincenal, mensual, trimestral, semestral, anual
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date)
    activo = db.Column(db.Integer, default=1)
    precio_mantenimiento = db.Column(db.Float, default=0)
    dispositivos_cubiertos = db.Column(db.Integer, default=1)
    ultima_visita = db.Column(db.Date)
    
    # Relación con cliente
    cliente = db.relationship('Cliente', backref='contratos')
    
    def __repr__(self):
        return f'<Contrato Cliente:{self.cliente_id} Frecuencia:{self.frecuencia}>'
    
    def calcular_proxima_visita(self):
        """Calcula la fecha de la próxima visita según la frecuencia.

        Opera con objetos date nativos (columnas db.Date), sin strptime.
        Devuelve un objeto date (Jinja2 lo renderiza como 'YYYY-MM-DD' y
        las comparaciones del dashboard funcionan directamente).
        """
        from datetime import timedelta
        if not isinstance(self.ultima_visita, date):
            return self.fecha_inicio
        
        dias = {
            'semanal': 7,
            'quincenal': 15,
            'mensual': 30,
            'trimestral': 90,
            'semestral': 180,
            'anual': 365
        }.get(self.frecuencia, 30)
        
        return self.ultima_visita + timedelta(days=dias)


class OrdenNota(db.Model):
    """Tabla de notas internas en órdenes de reparación"""
    __tablename__ = 'orden_notas'
    
    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    fecha_hora = db.Column(db.DateTime, nullable=False, default=datetime.now)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    
    # Relación con usuario
    usuario = db.relationship('Usuario', backref='notas')
    
    def __repr__(self):
        return f'<Nota Orden:{self.orden_id} {self.fecha_hora}>'


# ======================================================================
# AUDITORÍA (anti-fraude interno) — bitácora inmutable append-only
# ======================================================================
class AuditLog(db.Model):
    """Registro inmutable de auditoría (append-only).

    Cada creación, actualización o eliminación sobre un modelo crítico
    (Orden, Pieza, MovimientoInventario, ...) genera automáticamente una
    fila aquí mediante los eventos ORM `after_insert` / `after_update` /
    `after_delete` registrados más abajo (con la fotografía previa del
    evento `before_flush` para poder reconstruir `old_values`).

    SEGURIDAD:
    - La clase NO define ningún método de edición ni eliminación: la
      bitácora es solo lectura. El blueprint `/admin/auditoria` únicamente
      consulta; no existe ninguna vista POST/PUT/DELETE para alterar logs.
    - `username` se guarda desnormalizado: sobrevive aunque borren la
      cuenta del usuario auditado.
    - `old_values` / `new_values` se serializan como String JSON.
    """
    __tablename__ = 'audit_log'

    ACCIONES_VALIDAS = ['CREATE', 'UPDATE', 'DELETE']

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    username = db.Column(db.Text)                    # copia del login al momento del cambio
    action = db.Column(db.Text, nullable=False)      # CREATE | UPDATE | DELETE
    table_name = db.Column(db.Text, nullable=False)  # tabla afectada (p.ej. 'ordenes')
    record_id = db.Column(db.Text)                   # PK del registro (texto: soporta PK compuestas)
    old_values = db.Column(db.Text)                  # JSON valores anteriores (UPDATE/DELETE)
    new_values = db.Column(db.Text)                  # JSON valores nuevos (CREATE/UPDATE)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    ip_address = db.Column(db.Text)

    def __repr__(self):
        return f'<AuditLog {self.action} {self.table_name}:{self.record_id} por {self.username}>'

    # --- Utilidades de SOLO LECTURA para la vista ---------------------
    def valores_antiguos(self):
        """Decodifica old_values (JSON -> dict)."""
        try:
            return json.loads(self.old_values) if self.old_values else {}
        except (ValueError, TypeError):
            return {}

    def valores_nuevos(self):
        """Decodifica new_values (JSON -> dict)."""
        try:
            return json.loads(self.new_values) if self.new_values else {}
        except (ValueError, TypeError):
            return {}

    def resumen_cambios(self):
        """[(campo, valor_antes, valor_despues)] para mostrar en la tabla."""
        if self.action == 'CREATE':
            return [(k, None, v) for k, v in sorted(self.valores_nuevos().items())]
        if self.action == 'DELETE':
            return [(k, v, None) for k, v in sorted(self.valores_antiguos().items())]
        antes, despues = self.valores_antiguos(), self.valores_nuevos()
        return [(k, antes.get(k), despues.get(k))
                for k in sorted(set(antes) | set(despues))
                if antes.get(k) != despues.get(k)]


# ----------------------------------------------------------------------
# Hooks de SQLAlchemy: captura automática de cambios en modelos críticos
# ----------------------------------------------------------------------
# Modelos cuyas mutaciones deben quedar registradas (fraude interno:
# borrar órdenes, manipular stock, alterar facturación, etc.).
MODELOS_AUDITADOS = (
    'Orden', 'Pieza', 'MovimientoInventario', 'OrdenPieza', 'Gasto',
    'Proveedor', 'Cliente', 'Dispositivo', 'Tecnico', 'Contrato',
    'Configuracion', 'Usuario', 'OrdenNota',
)

# Campos que NUNCA se copian al log (material de autenticación).
CAMPOS_SENSIBLES = {'password_hash'}


def _valor_serializable(valor):
    """Convierte un valor de columna a algo JSON-serializable."""
    if isinstance(valor, datetime):
        return valor.isoformat(sep=' ', timespec='seconds')
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, (int, float, str, bool)) or valor is None:
        return valor
    return str(valor)


def _valores_actuales(mapper, target):
    """Fotografía los valores corrientes de todas las columnas del objeto."""
    vals = {}
    for prop in mapper.column_attrs:
        clave = prop.key
        if clave in CAMPOS_SENSIBLES:
            continue
        try:
            raw = getattr(target, clave, None)
        except Exception:
            raw = None
        vals[clave] = _valor_serializable(raw)
    return vals


def _contexto_usuario():
    """Identifica al usuario/IP responsables del cambio.

    Devuelve (user_id, username, ip). Fuera de contexto de request (CLI,
    scripts de migración) registra 'sistema'.
    """
    user_id, username, ip = None, 'sistema', None
    try:
        from flask import has_request_context, request
        from flask_login import current_user
        if has_request_context():
            ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            if ip:
                ip = ip.split(',')[0].strip()
            try:
                if current_user.is_authenticated:
                    user_id = current_user.id
                    username = current_user.usuario
            except Exception:
                pass
    except Exception:
        pass
    return user_id, username, ip


def _record_id_de(mapper, target):
    """PK del registro como texto (soporta claves primarias compuestas)."""
    try:
        partes = []
        for col in mapper.primary_key:
            # resolver la columna -> atributo ORM por su nombre de columna;
            # si no hay atributo directo, leer el valor desde la identidad.
            attr = None
            for a in mapper.attrs:
                if getattr(a, 'key', None) == col.key or getattr(a, 'key', None) == col.name:
                    attr = a
                    break
            if attr is not None:
                valor = getattr(target, attr.key, None)
            else:
                valor = getattr(target, col.key, None)
            partes.append('' if valor is None else str(valor))
        return ','.join(partes)
    except Exception:
        return ''


def _historial_update(mapper, target):
    """Reconstruye (old, new) de un UPDATE desde la historia de atributos.

    Los hooks after_* se ejecutan DESPUÉS de que SQLAlchemy aplicó los
    cambios en la BD y limpió la historia; por eso `before_flush` guarda
    una copia del historial por clave primaria (ver `_auditar_before_flush`).
    Si no hay copia (p.ej. flush sin paso previo), se degrada con gracia:
    `new_values` = estado actual y `old_values` = None.
    """
    state_key = None
    try:
        ident = db.inspect(target).identity
        if ident is not None:
            state_key = ','.join(str(v) for v in (ident if isinstance(ident, tuple) else (ident,)))
    except Exception:
        state_key = None
    snapshot = _SNAPSHOTS_UPDATE.pop(state_key, None) if state_key else None
    if snapshot:
        return snapshot
    # Fallback: solo valores nuevos (no poderemos saber los antiguos)
    return None, _valores_actuales(mapper, target)


# Copia temporal del historial de atributos tomada en before_flush:
#   {record_id: (old_values_dict, new_values_dict)}
# Se consume en after_update (mismo flush) y se descarta si hay rollback.
_SNAPSHOTS_UPDATE = {}


@event.listens_for(db.session, 'before_flush')
def _auditar_before_flush(session, flush_context, instances):
    """Fotografía ANTES del flush el historial old/new de cada objeto dirty.

    Necesario porque after_update corre después de que SQLAlchemy limpia
    la `AttributeHistory`; sin esta copia no podríamos llenar old_values.
    """
    _SNAPSHOTS_UPDATE.clear()
    for obj in list(session.dirty):
        if not session.is_modified(obj, include_collections=False):
            continue
        mapper = db.inspect(type(obj))
        if mapper.class_.__name__ not in MODELOS_AUDITADOS:
            continue
        old, new = {}, {}
        for prop in mapper.column_attrs:
            clave = prop.key
            if clave in CAMPOS_SENSIBLES:
                continue
            hist_state = db.inspect(obj).attrs[clave].history
            if hist_state.has_changes():
                antes = hist_state.deleted[0] if hist_state.deleted else None
                despues = hist_state.added[0] if hist_state.added else None
                old[clave] = _valor_serializable(antes)
                new[clave] = _valor_serializable(despues)
        if old or new:
            ident = db.inspect(obj).identity
            if ident is not None:
                rid = ','.join(str(v) for v in (ident if isinstance(ident, tuple) else (ident,)))
                _SNAPSHOTS_UPDATE[rid] = (old, new)


@event.listens_for(db.session, 'after_rollback')
def _auditar_tras_rollback(session):
    """Si el cambio auditado se revirtió, descartamos su instantánea."""
    _SNAPSHOTS_UPDATE.clear()


def _escribir_log(action, target, mapper, old=None, new=None):
    """Inserta la fila de auditoría en la MISMA transacción del cambio.

    Usa connection.execute() con un INSERT de nivel Core (no ORM) para:
    1) mantener el log atómicamente unido al cambio auditado (si el commit
       falla, el log tampoco existe; si alguien borra el dato, la prueba
       queda escrita en el mismo COMMIT), y
    2) evitar recursión sobre los propios listeners de AuditLog.
    """
    user_id, username, ip = _contexto_usuario()
    session = object_session(target) or db.session
    conn = session.connection()
    stmt = AuditLog.__table__.insert().values(
        user_id=user_id,
        username=username,
        action=action,
        table_name=mapper.local_table.name,
        record_id=_record_id_de(mapper, target),
        old_values=json.dumps(old, ensure_ascii=False, default=str) if old is not None else None,
        new_values=json.dumps(new, ensure_ascii=False, default=str) if new is not None else None,
        timestamp=datetime.now(),
        ip_address=ip,
    )
    conn.execute(stmt)


# --- Hooks por modelo crítico -----------------------------------------
# Un listener por evento se registra sobre la CLASE BASE (db.Model) y se
# filtra por nombre de modelo: así cubrimos Orden, Pieza,
# MovimientoInventario y el resto de MODELOS_AUDITADOS con un solo juego
# de eventos, tal como exige la política anti-fraude.

@event.listens_for(db.Model, 'after_insert', propagate=True)
def _audit_after_insert(mapper, connection, target):
    """CREATE: guarda la fotografía completa del registro nuevo."""
    if type(target).__name__ in MODELOS_AUDITADOS:
        _escribir_log('CREATE', target, mapper, old=None,
                      new=_valores_actuales(mapper, target))


@event.listens_for(db.Model, 'after_update', propagate=True)
def _audit_after_update(mapper, connection, target):
    """UPDATE: guarda SOLO los campos que cambiaron (old -> new)."""
    if type(target).__name__ not in MODELOS_AUDITADOS:
        return
    old, new = _historial_update(mapper, target)
    if old is None and new is None:
        return
    _escribir_log('UPDATE', target, mapper, old=old, new=new)


@event.listens_for(db.Model, 'after_delete', propagate=True)
def _audit_after_delete(mapper, connection, target):
    """DELETE: conserva el contenido íntegro del registro borrado.

    Clave contra el fraude interno (ej. técnico que elimina una orden):
    incluso si el borrado es físico, la bitácora permite reconstruirlo.
    """
    if type(target).__name__ in MODELOS_AUDITADOS:
        _escribir_log('DELETE', target, mapper,
                      old=_valores_actuales(mapper, target), new=None)
