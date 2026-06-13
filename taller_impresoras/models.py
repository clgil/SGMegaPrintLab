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
    rol = db.Column(db.Text, default='admin')
    activo = db.Column(db.Integer, default=1)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


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
    proveedor = db.Column(db.Text)
    
    # Relaciones
    movimientos = db.relationship('MovimientoInventario', backref='pieza', lazy=True)
    orden_piezas = db.relationship('OrdenPieza', back_populates='pieza_rel', lazy=True)
    
    def __repr__(self):
        return f'<Pieza {self.nombre}>'
    
    @property
    def stock_bajo(self):
        """Indica si la pieza está por debajo del stock mínimo"""
        return self.cantidad <= self.cantidad_minima


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
    
    # Relaciones
    piezas_usadas = db.relationship('OrdenPieza', backref='orden', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Orden {self.numero_orden}>'
    
    def calcular_total(self):
        """Calcula el costo total de la orden"""
        total_piezas = sum(op.cantidad * op.precio_unitario for op in self.piezas_usadas)
        self.costo_total = total_piezas + (self.mano_obra_costo or 0)
        return self.costo_total


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
