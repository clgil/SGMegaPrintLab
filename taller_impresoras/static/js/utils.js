/**
 * Utilidades de seguridad y UX para el Sistema de Gestión de Taller
 * Confirmaciones, validaciones y mejoras de experiencia de usuario
 */

/**
 * Muestra un diálogo de confirmación personalizado
 * @param {string} mensaje - Mensaje a mostrar
 * @param {string} titulo - Título del diálogo (opcional)
 * @returns {Promise<boolean>} - true si confirma, false si cancela
 */
function confirmarAccion(mensaje, titulo = '¿Está seguro?') {
    return new Promise((resolve) => {
        if (confirm(`${titulo}\n\n${mensaje}`)) {
            resolve(true);
        } else {
            resolve(false);
        }
    });
}

/**
 * Confirma antes de eliminar un recurso
 * @param {string} nombreRecurso - Nombre del recurso a eliminar (ej: "orden", "pieza")
 * @param {string} identificador - Identificador (número, nombre)
 * @returns {Promise<boolean>}
 */
async function confirmarEliminacion(nombreRecurso, identificador) {
    const mensaje = `¿Está seguro de que desea eliminar ${nombreRecurso} "${identificador}"?\n\n⚠️ Esta acción NO se puede deshacer.`;
    return confirmarAccion(mensaje, '⚠️ Confirmar eliminación');
}

/**
 * Previene envíos de formulario duplicados
 * Deshabilita el botón submit mientras se procesa la solicitud
 */
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Procesando...';
            }
        });
    });
});

/**
 * Valida que un número sea positivo
 * @param {number} valor
 * @returns {boolean}
 */
function esNumeroPositivo(valor) {
    const num = parseFloat(valor);
    return !isNaN(num) && num > 0;
}

/**
 * Valida que un email tenga formato válido
 * @param {string} email
 * @returns {boolean}
 */
function esEmailValido(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

/**
 * Formatea un número a moneda CUP
 * @param {number} valor
 * @returns {string}
 */
function formatoMoneda(valor) {
    return new Intl.NumberFormat('es-CU', {
        style: 'currency',
        currency: 'CUP',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(valor);
}

/**
 * Muestra un mensaje de éxito temporal
 * @param {string} mensaje
 * @param {number} duracion - Milisegundos (default: 3000)
 */
function mostrarExito(mensaje, duracion = 3000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show position-fixed';
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        <span class="alert-icon">✓</span>
        <span class="alert-content">${mensaje}</span>
        <button type="button" class="alert-close" data-bs-dismiss="alert">×</button>
    `;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, duracion);
}

/**
 * Muestra un mensaje de error temporal
 * @param {string} mensaje
 * @param {number} duracion - Milisegundos (default: 5000)
 */
function mostrarError(mensaje, duracion = 5000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed';
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        <span class="alert-icon">✕</span>
        <span class="alert-content">${mensaje}</span>
        <button type="button" class="alert-close" data-bs-dismiss="alert">×</button>
    `;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, duracion);
}

/**
 * Habilita validación Bootstrap en tiempo real
 * Valida campos mientras el usuario escribe
 */
function habilitarValidacionEnTiempoReal() {
    const inputs = document.querySelectorAll('input[required], textarea[required], select[required]');
    
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.hasAttribute('type') && this.type === 'number') {
                if (this.value && !esNumeroPositivo(this.value)) {
                    this.classList.add('is-invalid');
                    this.classList.remove('is-valid');
                } else if (this.value) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }
            } else if (this.hasAttribute('type') && this.type === 'email') {
                if (this.value && !esEmailValido(this.value)) {
                    this.classList.add('is-invalid');
                    this.classList.remove('is-valid');
                } else if (this.value) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }
            } else if (this.value) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            }
        });
    });
}

// Inicializar validación al cargar
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', habilitarValidacionEnTiempoReal);
} else {
    habilitarValidacionEnTiempoReal();
}
