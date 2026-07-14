/**
 * Manejadores para eliminación de inventario y confirmaciones
 */

/**
 * Eliminar una pieza del inventario con confirmación
 * @param {number} piezaId
 * @param {string} nombrePieza
 */
function eliminarPieza(piezaId, nombrePieza) {
    confirmarEliminacion('la pieza', nombrePieza).then(confirmado => {
        if (confirmado) {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = `/inventario/eliminar/${piezaId}`;
            document.body.appendChild(form);
            form.submit();
        }
    });
}

/**
 * Eliminar una categoría con confirmación
 * @param {number} categoriaId
 * @param {string} nombreCategoria
 */
function eliminarCategoria(categoriaId, nombreCategoria) {
    confirmarEliminacion('la categoría', nombreCategoria).then(confirmado => {
        if (confirmado) {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = `/inventario/categorias/eliminar/${categoriaId}`;
            document.body.appendChild(form);
            form.submit();
        }
    });
}

/**
 * Valida campos de entrada numéricos para inventario
 */
function validarCamposInventario() {
    const cantidadInput = document.querySelector('input[name="cantidad"]');
    const precioInput = document.querySelector('input[name="precio_costo"], input[name="precio_venta"]');
    
    if (cantidadInput) {
        cantidadInput.addEventListener('blur', function() {
            if (this.value && !esNumeroPositivo(this.value)) {
                this.classList.add('is-invalid');
                mostrarError('La cantidad debe ser un número mayor a 0');
            } else if (this.value) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            }
        });
    }
    
    if (precioInput) {
        precioInput.addEventListener('blur', function() {
            if (this.value && !esNumeroPositivo(this.value)) {
                this.classList.add('is-invalid');
                mostrarError('El precio debe ser un número mayor a 0');
            } else if (this.value) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            }
        });
    }
}

// Inicializar validaciones al cargar
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', validarCamposInventario);
} else {
    validarCamposInventario();
}
