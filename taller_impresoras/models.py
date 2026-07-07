"""
Modelos de base de datos para el Sistema de Gestión de Taller de Impresoras
Adaptado a la realidad cubana - Junio 2026

Define todas las tablas según el esquema SQLite especificado en el PRD
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

def init_db(app):
    """Inicializa la base de datos con la aplicación Flask"""
    db.init_app(app)

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
        """Verifica si el usuario tiene un permiso específico según su rol"""
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
    tipo_cliente = db.Column(db.Text, default='Particular')
    activo = db.Column(db.Integer, default=1)
    
    # Relaciones
    dispositivos = db.relationship('Dispositivo', backref='cliente', lazy=True)
    ordenes = db.relationship('Orden', backref='cliente', lazy=True)
    
    def __repr__(self):
        return f'<Cliente {self.nombre}>'


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
    fecha_entrada = db.Column(db.Text, nullable=False, default=datetime.now().strftime('%Y-%m-%d'))
    fecha_prevista = db.Column(db.Text)
    fecha_entrega = db.Column(db.Text)
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
    fecha_fin_garantia = db.Column(db.Text)  # Fecha calculada de fin de garantía
    orden_original_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'))  # Para reingresos
    es_reingreso = db.Column(db.Integer, default=0)  # Indica si es reingreso por garantía
    tipo_orden = db.Column(db.Text, default='reparacion')  # reparacion, mantenimiento, garantia
    
    # Campos de tiempo de reparación
    fecha_inicio_reparacion = db.Column(db.Text)  # Cuando pasa a "En reparación"
    fecha_fin_reparacion = db.Column(db.Text)  # Cuando pasa a "Listo para entregar" o "Entregado"
    
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
        """Calcula el tiempo de reparación en horas (decimal)"""
        if not self.fecha_inicio_reparacion or not self.fecha_fin_reparacion:
            return None
        try:
            inicio = datetime.strptime(self.fecha_inicio_reparacion, '%Y-%m-%d %H:%M:%S')
            fin = datetime.strptime(self.fecha_fin_reparacion, '%Y-%m-%d %H:%M:%S')
            delta = fin - inicio
            return round(delta.total_seconds() / 3600, 2)
        except:
            return None
    
    @property
    def garantia_vigente(self):
        """Verifica si la orden tiene garantía vigente"""
        if not self.fecha_fin_garantia:
            return False
        try:
            fin_garantia = datetime.strptime(self.fecha_fin_garantia, '%Y-%m-%d')
            return datetime.now() <= fin_garantia
        except:
            return False


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
    fecha = db.Column(db.Text, nullable=False, default=datetime.now().strftime('%Y-%m-%d'))
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
    fecha = db.Column(db.Text, nullable=False, default=datetime.now().strftime('%Y-%m-%d'))
    
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
    fecha_creacion = db.Column(db.Text, default=datetime.now().strftime('%Y-%m-%d'))
    
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
    fecha_inicio = db.Column(db.Text, nullable=False)
    fecha_fin = db.Column(db.Text)
    activo = db.Column(db.Integer, default=1)
    precio_mantenimiento = db.Column(db.Float, default=0)
    dispositivos_cubiertos = db.Column(db.Integer, default=1)
    ultima_visita = db.Column(db.Text)
    
    # Relación con cliente
    cliente = db.relationship('Cliente', backref='contratos')
    
    def __repr__(self):
        return f'<Contrato Cliente:{self.cliente_id} Frecuencia:{self.frecuencia}>'
    
    def calcular_proxima_visita(self):
        """Calcula la fecha de la próxima visita según la frecuencia"""
        from datetime import timedelta
        if not self.ultima_visita:
            return self.fecha_inicio
        
        try:
            ultima = datetime.strptime(self.ultima_visita, '%Y-%m-%d')
        except:
            return self.fecha_inicio
        
        dias = {
            'semanal': 7,
            'quincenal': 15,
            'mensual': 30,
            'trimestral': 90,
            'semestral': 180,
            'anual': 365
        }.get(self.frecuencia, 30)
        
        proxima = ultima + timedelta(days=dias)
        return proxima.strftime('%Y-%m-%d')


class OrdenNota(db.Model):
    """Tabla de notas internas en órdenes de reparación"""
    __tablename__ = 'orden_notas'
    
    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    fecha_hora = db.Column(db.Text, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    
    # Relación con usuario
    usuario = db.relationship('Usuario', backref='notas')
    
    def __repr__(self):
        return f'<Nota Orden:{self.orden_id} {self.fecha_hora}>'
