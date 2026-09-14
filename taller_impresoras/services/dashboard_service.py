"""
Servicios de negocio para el sistema de gestión de taller
Estos servicios encapsulan la lógica de negocio separándola de las rutas
"""
from datetime import datetime, timedelta
from models import db, Orden, Pieza, Gasto, Configuracion, Cliente, Dispositivo, Tecnico, Usuario


class DashboardService:
    """Servicio para obtener estadísticas y datos del dashboard"""
    
    @staticmethod
    def calcular_fechas_periodo(filtro_periodo, fecha_inicio=None, fecha_fin=None):
        """Calcula las fechas de inicio y fin según el período seleccionado"""
        ahora = datetime.now()
        
        if filtro_periodo == 'hoy':
            fecha_inicio_dt = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
            fecha_fin_dt = ahora
        elif filtro_periodo == 'este_mes':
            fecha_inicio_dt = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            fecha_fin_dt = ahora
        elif filtro_periodo == 'este_anio':
            fecha_inicio_dt = ahora.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            fecha_fin_dt = ahora
        elif filtro_periodo == 'personalizado' and fecha_inicio and fecha_fin:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
        else:
            # Por defecto: este mes
            filtro_periodo = 'este_mes'
            fecha_inicio_dt = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            fecha_fin_dt = ahora
        
        return {
            'filtro_periodo': filtro_periodo,
            'fecha_inicio': fecha_inicio_dt.strftime('%Y-%m-%d'),
            'fecha_fin': fecha_fin_dt.strftime('%Y-%m-%d'),
            'fecha_inicio_dt': fecha_inicio_dt,
            'fecha_fin_dt': fecha_fin_dt
        }
    
    @staticmethod
    def obtener_estadisticas_administrador(fecha_inicio, fecha_fin, fecha_inicio_dt, fecha_fin_dt):
        """Obtiene todas las estadísticas para administrador"""
        ahora = datetime.now()
        
        # Estadísticas básicas
        stats = {
            'total_ordenes_activas': Orden.query.filter(
                Orden.estado.in_(['Recibido', 'En diagnostico', 'Esperando piezas', 'En reparacion', 'Listo para entregar'])
            ).count(),
            'ordenes_pendientes_diagnostico': Orden.query.filter_by(estado='En diagnostico').count(),
            'ordenes_listas_entregar': Orden.query.filter_by(estado='Listo para entregar').count(),
            'piezas_stock_bajo': Pieza.query.filter(Pieza.cantidad <= Pieza.cantidad_minima).count(),
            'total_usuarios': Usuario.query.count(),
            'total_clientes': Cliente.query.count(),
            'total_dispositivos': Dispositivo.query.count(),
            'total_tecnicos': Tecnico.query.count(),
            'total_piezas': Pieza.query.count(),
        }
        
        # Usuarios por rol
        stats['usuarios_por_rol'] = {
            'administrador': Usuario.query.filter_by(rol='administrador', activo=1).count(),
            'tecnico': Usuario.query.filter_by(rol='tecnico', activo=1).count(),
            'proveedor': Usuario.query.filter_by(rol='proveedor', activo=1).count(),
            'cliente': Usuario.query.filter_by(rol='cliente', activo=1).count()
        }
        
        # Estadísticas de órdenes
        total_ordenes = Orden.query.count()
        ordenes_completadas = Orden.query.filter_by(estado='Entregado').count()
        ordenes_pendientes = Orden.query.filter(
            Orden.estado.in_(['Recibido', 'En diagnostico', 'Esperando piezas', 'En reparacion', 'Listo para entregar'])
        ).count()
        stats['total_ordenes'] = total_ordenes
        stats['ordenes_completadas'] = ordenes_completadas
        stats['ordenes_pendientes'] = ordenes_pendientes
        
        # Métricas financieras
        ordenes_entregadas = Orden.query.filter(
            Orden.estado == 'Entregado',
            Orden.fecha_entrega >= fecha_inicio,
            Orden.fecha_entrega <= fecha_fin
        ).all()
        
        stats['ingresos_brutos'] = sum(o.costo_total for o in ordenes_entregadas) or 0
        
        inversion_piezas = 0
        for orden in ordenes_entregadas:
            for op in orden.piezas_usadas:
                if op.pieza_rel:
                    inversion_piezas += op.cantidad * op.pieza_rel.precio_costo
        stats['inversion_piezas'] = inversion_piezas
        
        stats['valor_inventario'] = sum(p.cantidad * p.precio_costo for p in Pieza.query.all()) or 0
        
        gastos_operativos = db.session.query(db.func.sum(Gasto.monto)).filter(
            Gasto.fecha >= fecha_inicio,
            Gasto.fecha <= fecha_fin
        ).scalar() or 0
        stats['gastos_operativos'] = gastos_operativos
        
        stats['ganancia_neta'] = stats['ingresos_brutos'] - inversion_piezas - gastos_operativos
        
        # Cálculo de tributos
        config = {c.clave: c.valor for c in Configuracion.query.all()}
        stats['regimen_fiscal'] = config.get('regimen_fiscal', 'general')
        
        # Ingresos anuales para cálculo de ISIP
        inicio_anio = ahora.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d')
        ordenes_anio = Orden.query.filter(
            Orden.estado == 'Entregado',
            Orden.fecha_entrega >= inicio_anio,
            Orden.fecha_entrega <= ahora.strftime('%Y-%m-%d')
        ).all()
        
        ingresos_anio = sum(o.costo_total for o in ordenes_anio) or 0
        inversion_piezas_anio = sum(
            op.cantidad * op.pieza_rel.precio_costo 
            for o in ordenes_anio 
            for op in o.piezas_usadas 
            if op.pieza_rel
        ) or 0
        
        gastos_anio = db.session.query(db.func.sum(Gasto.monto)).filter(
            Gasto.fecha >= inicio_anio,
            Gasto.fecha <= ahora.strftime('%Y-%m-%d')
        ).scalar() or 0
        
        stats['ganancia_acumulada_anio'] = ingresos_anio - inversion_piezas_anio - gastos_anio
        stats['config'] = config
        
        return stats
    
    @staticmethod
    def obtener_ingresos_mensuales():
        """Obtiene los ingresos de los últimos 6 meses"""
        ahora = datetime.now()
        ingresos_mensuales = []
        nombres_meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        
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
            
            ingresos_mensuales.append({'mes': nombres_meses[mes-1], 'ingreso': ingreso})
        
        return ingresos_mensuales
    
    @staticmethod
    def obtener_indicadores_alertas(ahora=None):
        """Obtiene indicadores de alertas (órdenes estancadas, garantías, mantenimientos)"""
        if ahora is None:
            ahora = datetime.now()
        
        alertas = {}
        
        # Órdenes estancadas
        dias_estancia = 3
        fecha_limite = (ahora - timedelta(days=dias_estancia)).strftime('%Y-%m-%d')
        alertas['ordenes_estancadas'] = Orden.query.filter(
            Orden.estado.in_(['Recibido', 'En diagnostico']),
            Orden.fecha_entrada < fecha_limite
        ).all()
        
        # Garantías por vencer
        fecha_proxima_vencimiento = (ahora + timedelta(days=7)).strftime('%Y-%m-%d')
        alertas['garantias_por_vencer'] = Orden.query.filter(
            Orden.fecha_fin_garantia != None,
            Orden.fecha_fin_garantia <= fecha_proxima_vencimiento,
            Orden.fecha_fin_garantia >= ahora.strftime('%Y-%m-%d'),
            Orden.es_reingreso == 0
        ).all()
        
        # Mantenimientos por vencer
        from models import Contrato
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
        alertas['mantenimientos_por_vencer'] = mantenimientos_por_vencer
        
        return alertas
