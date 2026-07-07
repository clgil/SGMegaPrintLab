"""
Rutas de copia de seguridad y restauración para el Sistema de Gestión de Taller de Impresoras
Adaptado a la realidad cubana - Junio 2026

Funcionalidad crítica para la realidad cubana: permite respaldar datos en USB
"""
import os
import shutil
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app
from flask_login import login_required
from models import db, Configuracion
from routes.decorators import rol_requerido

backup_bp = Blueprint('backup', __name__, template_folder='../templates')


@backup_bp.route('/')
@rol_requerido(['administrador'])
def index():
    """Página principal de respaldo y restauración"""
    # Obtener ruta de la base de datos
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'taller.db')
    
    # Verificar si existe
    db_existe = os.path.exists(db_path)
    
    return render_template('backup/index.html', db_existe=db_existe, db_path=db_path)


@backup_bp.route('/crear', methods=['POST'])
@rol_requerido(['administrador'])
def crear():
    """Crear copia de seguridad de la base de datos"""
    try:
        # Obtener ruta de la base de datos actual
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance', 'taller.db')
        db_path = os.path.abspath(db_path)
        
        if not os.path.exists(db_path):
            flash('No se encontró la base de datos', 'danger')
            return redirect(url_for('backup.index'))
        
        # Generar nombre del archivo de respaldo
        fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = f'taller_backup_{fecha}.db'
        
        # Directorio de backup
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backup')
        os.makedirs(backup_dir, exist_ok=True)
        
        ruta_destino = os.path.join(backup_dir, nombre_archivo)
        
        # Copiar archivo
        shutil.copy2(db_path, ruta_destino)
        
        flash(f'Respaldo creado correctamente: {nombre_archivo}', 'success')
        return redirect(url_for('backup.index'))
    
    except Exception as e:
        flash(f'Error al crear respaldo: {str(e)}', 'danger')
        return redirect(url_for('backup.index'))


@backup_bp.route('/descargar')
@rol_requerido(['administrador'])
def descargar():
    """Descargar copia de seguridad reciente"""
    try:
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backup')
        
        # Buscar el backup más reciente
        if not os.path.exists(backup_dir):
            flash('No hay respaldos disponibles', 'warning')
            return redirect(url_for('backup.index'))
        
        archivos = [f for f in os.listdir(backup_dir) if f.startswith('taller_backup_') and f.endswith('.db')]
        
        if not archivos:
            flash('No hay respaldos disponibles', 'warning')
            return redirect(url_for('backup.index'))
        
        # Ordenar por nombre (que incluye fecha) y tomar el último
        archivos.sort(reverse=True)
        archivo_mas_reciente = archivos[0]
        
        ruta_archivo = os.path.join(backup_dir, archivo_mas_reciente)
        
        return send_file(ruta_archivo, 
                        as_attachment=True, 
                        download_name=archivo_mas_reciente)
    
    except Exception as e:
        flash(f'Error al descargar respaldo: {str(e)}', 'danger')
        return redirect(url_for('backup.index'))


@backup_bp.route('/restaurar', methods=['POST'])
@rol_requerido(['administrador'])
def restaurar():
    """Restaurar base de datos desde un respaldo"""
    try:
        # Verificar que se haya subido un archivo
        if 'archivo' not in request.files:
            flash('No se seleccionó ningún archivo', 'warning')
            return redirect(url_for('backup.index'))
        
        archivo = request.files['archivo']
        
        if archivo.filename == '':
            flash('No se seleccionó ningún archivo', 'warning')
            return redirect(url_for('backup.index'))
        
        # Verificar extensión
        if not archivo.filename.endswith('.db'):
            flash('El archivo debe tener extensión .db', 'danger')
            return redirect(url_for('backup.index'))
        
        # Guardar archivo temporalmente
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backup')
        os.makedirs(backup_dir, exist_ok=True)
        
        ruta_temporal = os.path.join(backup_dir, 'restauracion_temporal.db')
        archivo.save(ruta_temporal)
        
        # Obtener ruta de la base de datos actual
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance', 'taller.db')
        db_path = os.path.abspath(db_path)
        
        # Crear backup automático de la base de datos actual antes de restaurar
        fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_anterior = os.path.join(backup_dir, f'taller_auto_backup_{fecha}.db')
        shutil.copy2(db_path, backup_anterior)
        
        # Reemplazar base de datos actual
        shutil.copy2(ruta_temporal, db_path)
        
        # Eliminar archivo temporal
        os.remove(ruta_temporal)
        
        flash(f'Base de datos restaurada correctamente. Se creó respaldo automático: {os.path.basename(backup_anterior)}', 'success')
        return redirect(url_for('backup.index'))
    
    except Exception as e:
        flash(f'Error al restaurar respaldo: {str(e)}', 'danger')
        return redirect(url_for('backup.index'))


@backup_bp.route('/listar')
@rol_requerido(['administrador'])
def listar():
    """Listar respaldos disponibles"""
    try:
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backup')
        
        if not os.path.exists(backup_dir):
            backups = []
        else:
            archivos = [f for f in os.listdir(backup_dir) if f.startswith('taller_backup_') and f.endswith('.db')]
            archivos.sort(reverse=True)
            
            backups = []
            for archivo in archivos:
                ruta = os.path.join(backup_dir, archivo)
                tamaño = os.path.getsize(ruta)
                fecha_mod = datetime.fromtimestamp(os.path.getmtime(ruta))
                backups.append({
                    'nombre': archivo,
                    'ruta': ruta,
                    'tamaño': tamaño,
                    'fecha': fecha_mod.strftime('%Y-%m-%d %H:%M')
                })
        
        return render_template('backup/listar.html', backups=backups)
    
    except Exception as e:
        flash(f'Error al listar respaldos: {str(e)}', 'danger')
        return redirect(url_for('backup.index'))


@backup_bp.route('/eliminar/<nombre>', methods=['POST'])
@rol_requerido(['administrador'])
def eliminar(nombre):
    """Eliminar un respaldo específico"""
    try:
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backup')
        ruta_archivo = os.path.join(backup_dir, nombre)
        
        if os.path.exists(ruta_archivo):
            os.remove(ruta_archivo)
            flash(f'Respaldo {nombre} eliminado', 'info')
        else:
            flash('El archivo no existe', 'warning')
        
        return redirect(url_for('backup.listar'))
    
    except Exception as e:
        flash(f'Error al eliminar respaldo: {str(e)}', 'danger')
        return redirect(url_for('backup.listar'))


@backup_bp.route('/configuracion', methods=['GET', 'POST'])
@rol_requerido(['administrador'])
def configuracion():
    """Configuración de datos del taller para impresiones"""
    if request.method == 'POST':
        # Actualizar configuración de texto
        config_vals = {
            'nombre_taller': request.form.get('nombre_taller'),
            'direccion_taller': request.form.get('direccion_taller'),
            'telefono_taller': request.form.get('telefono_taller'),
            'email_taller': request.form.get('email_taller'),
            'nit_taller': request.form.get('nit_taller'),
            'responsable_taller': request.form.get('responsable_taller')
        }
        
        for clave, valor in config_vals.items():
            config = db.session.get(Configuracion, clave)
            if not config:
                config = Configuracion(clave=clave, valor=valor)
                db.session.add(config)
            else:
                config.valor = valor
        
        # Manejar subida del logotipo
        if 'logotipo' in request.files:
            archivo_logotipo = request.files['logotipo']
            if archivo_logotipo and archivo_logotipo.filename != '':
                # Verificar que sea una imagen válida
                if archivo_logotipo.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
                    # Crear directorio de uploads si no existe
                    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'uploads')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Guardar el archivo con un nombre único
                    import uuid
                    extension = archivo_logotipo.filename.rsplit('.', 1)[1].lower()
                    nombre_archivo = f'logotipo_taller_{uuid.uuid4().hex}.{extension}'
                    ruta_archivo = os.path.join(upload_dir, nombre_archivo)
                    
                    archivo_logotipo.save(ruta_archivo)
                    
                    # Guardar la ruta relativa en la configuración
                    ruta_relativa = f'static/uploads/{nombre_archivo}'
                    config_logo = db.session.get(Configuracion, 'logotipo_taller')
                    if not config_logo:
                        config_logo = Configuracion(clave='logotipo_taller', valor=ruta_relativa)
                        db.session.add(config_logo)
                    else:
                        config_logo.valor = ruta_relativa
                    
                    flash(f'Logotipo subido correctamente: {archivo_logotipo.filename}', 'success')
        
        db.session.commit()
        
        flash('Configuración actualizada correctamente', 'success')
        return redirect(url_for('backup.configuracion'))
    
    # Cargar configuración actual
    config = {}
    for c in Configuracion.query.all():
        config[c.clave] = c.valor
    
    return render_template('backup/configuracion.html', config=config)
