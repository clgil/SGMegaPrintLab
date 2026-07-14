/**
 * Manejadores específicos para formularios de órdenes
 * Incluye validaciones, confirmaciones y cálculos dinámicos
 */

/**
 * Eliminar una orden con confirmación
 * @param {number} ordenId
 * @param {string} numeroOrden
 */
function eliminarOrden(ordenId, numeroOrden) {
    confirmarEliminacion('la orden', numeroOrden).then(confirmado => {
        if (confirmado) {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = `/ordenes/eliminar/${ordenId}`;
            document.body.appendChild(form);
            form.submit();
        }
    });
}

/**
 * Cambiar estado de orden con validación
 * @param {number} ordenId
 * @param {string} estadoNuevo
 */
function cambiarEstadoOrden(ordenId, estadoNuevo) {
    const mensajeEstados = {
        'Entregado': '¿Desea marcar esta orden como ENTREGADA? El cliente recibirá notificación.',
        'Cancelado': '¿Desea CANCELAR esta orden? Las piezas serán devueltas al inventario.',
        'En reparacion': '¿Desea pasar esta orden a REPARACIÓN?'
    };
    
    const mensaje = mensajeEstados[estadoNuevo] || `¿Cambiar estado a "${estadoNuevo}"?`;
    
    confirmarAccion(mensaje, `Cambiar estado de orden`).then(confirmado => {
        if (confirmado) {
            // Enviar solicitud AJAX
            fetch(`/ordenes/${ordenId}/cambiar-estado`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ estado: estadoNuevo })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    mostrarExito(`Orden actualizada a estado: ${estadoNuevo}`);
                    setTimeout(() => location.reload(), 1000);
                } else {
                    mostrarError(data.message || 'Error al actualizar orden');
                }
            })
            .catch(error => {
                mostrarError('Error de conexión: ' + error);
            });
        }
    });
}

/**
 * Calcula el costo total de la orden en tiempo real
 * @param {number} costoManoObra
 * @returns {number}
 */
function calcularCostoTotal(costoManoObra = 0) {
    // Obtener tabla de piezas si existe
    const piezasTable = document.querySelector('.piezas-tabla tbody');
    let totalPiezas = 0;
    
    if (piezasTable) {
        const filas = piezasTable.querySelectorAll('tr');
        filas.forEach(fila => {
            const cantidad = parseFloat(fila.querySelector('[data-cantidad]')?.dataset.cantidad || 0);
            const precio = parseFloat(fila.querySelector('[data-precio]')?.dataset.precio || 0);
            totalPiezas += cantidad * precio;
        });
    }
    
    const costoMano = parseFloat(costoManoObra) || 0;
    const total = totalPiezas + costoMano;
    
    const elementoTotal = document.querySelector('[data-costo-total]');
    if (elementoTotal) {
        elementoTotal.textContent = formatoMoneda(total);
        elementoTotal.dataset.costoTotal = total;
    }
    
    return total;
}

/**
 * Valida que todas las piezas tengan cantidad válida
 * @returns {boolean}
 */
function validarPiezas() {
    const piezasTable = document.querySelector('.piezas-tabla tbody');
    if (!piezasTable) return true;
    
    const filas = piezasTable.querySelectorAll('tr');
    let todasValidas = true;
    
    filas.forEach(fila => {
        const cantidadInput = fila.querySelector('input[data-cantidad]');
        if (cantidadInput && (!cantidadInput.value || parseFloat(cantidadInput.value) <= 0)) {
            cantidadInput.classList.add('is-invalid');
            todasValidas = false;
        }
    });
    
    return todasValidas;
}

/**
 * Valida el formulario de orden antes de enviar
 * @returns {boolean}
 */
function validarFormuarioOrden() {
    // Validar que exista cliente
    const clienteSelect = document.querySelector('select[name="cliente_id"]');
    if (!clienteSelect || !clienteSelect.value) {
        mostrarError('Debe seleccionar un cliente');
        return false;
    }
    
    // Validar que exista problema
    const problemaInput = document.querySelector('textarea[name="problema_reportado"]');
    if (!problemaInput || !problemaInput.value.trim()) {
        mostrarError('Debe ingresar el problema reportado');
        return false;
    }
    
    // Validar piezas
    if (!validarPiezas()) {
        mostrarError('Todas las piezas deben tener cantidad válida (> 0)');
        return false;
    }
    
    return true;
}

// Event listeners al cargar
document.addEventListener('DOMContentLoaded', function() {
    // Calcular costo al cambiar mano de obra
    const costoManoInput = document.querySelector('input[name="mano_obra_costo"]');
    if (costoManoInput) {
        costoManoInput.addEventListener('change', function() {
            calcularCostoTotal(this.value);
        });
    }
    
    // Validar formulario antes de enviar
    const formularioOrden = document.querySelector('form.orden-form');
    if (formularioOrden) {
        formularioOrden.addEventListener('submit', function(e) {
            if (!validarFormuarioOrden()) {
                e.preventDefault();
            }
        });
    }
    
    // Calcular costo inicial
    calcularCostoTotal();
});
