"""
Ruta de ayuda para el Sistema de Gestión de Taller de Impresoras
Adaptado a la realidad cubana - Junio 2026
"""
from flask import Blueprint, render_template
from flask_login import login_required

ayuda_bp = Blueprint('ayuda', __name__, template_folder='../templates')


@ayuda_bp.route('/')
@login_required
def index():
    """Página de ayuda del sistema"""
    return render_template('ayuda/index.html')
