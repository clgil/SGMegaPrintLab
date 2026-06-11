"""
Rutas de gestión de técnicos para el Sistema de Gestión de Taller de Impresoras
Adaptado a la realidad cubana - Junio 2026
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import db, Tecnico

tecnicos_bp = Blueprint('tecnicos', __name__, template_folder='../templates')


@tecnicos_bp.route('/')
@login_required
def index():
    """Listado de técnicos"""
    tecnicos = Tecnico.query.order_by(Tecnico.nombre).all()
    return render_template('tecnicos/index.html', tecnicos=tecnicos)


@tecnicos_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    """Crear nuevo técnico"""
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        especialidad = request.form.get('especialidad')
        
        if not nombre:
            flash('El nombre es obligatorio', 'warning')
            return redirect(url_for('tecnicos.nuevo'))
        
        tecnico = Tecnico(
            nombre=nombre,
            especialidad=especialidad,
            activo=1
        )
        
        db.session.add(tecnico)
        db.session.commit()
        
        flash('Técnico registrado correctamente', 'success')
        return redirect(url_for('tecnicos.index'))
    
    return render_template('tecnicos/formulario.html', tecnico=None, accion='Crear')


@tecnicos_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Editar técnico existente"""
    tecnico = Tecnico.query.get_or_404(id)
    
    if request.method == 'POST':
        tecnico.nombre = request.form.get('nombre')
        tecnico.especialidad = request.form.get('especialidad')
        tecnico.activo = 1 if request.form.get('activo') else 0
        
        db.session.commit()
        
        flash('Técnico actualizado correctamente', 'success')
        return redirect(url_for('tecnicos.index'))
    
    return render_template('tecnicos/formulario.html', tecnico=tecnico, accion='Editar')


@tecnicos_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    """Eliminar técnico (solo si no tiene órdenes asociadas)"""
    tecnico = Tecnico.query.get_or_404(id)
    
    # Verificar si tiene órdenes asociadas
    if tecnico.ordenes:
        flash('No se puede eliminar: el técnico tiene órdenes asociadas', 'danger')
        return redirect(url_for('tecnicos.index'))
    
    db.session.delete(tecnico)
    db.session.commit()
    
    flash('Técnico eliminado correctamente', 'info')
    return redirect(url_for('tecnicos.index'))


@tecnicos_bp.route('/api/lista')
@login_required
def api_lista():
    """API para obtener lista de técnicos activos (usada en selects dinámicos)"""
    tecnicos = Tecnico.query.filter_by(activo=1).order_by(Tecnico.nombre).all()
    from flask import jsonify
    resultado = [{'id': t.id, 'nombre': t.nombre} for t in tecnicos]
    return jsonify(resultado)
