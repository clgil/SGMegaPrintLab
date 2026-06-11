/* JavaScript personalizado para el Taller de Impresoras */
/* Adaptado a la realidad cubana - Junio 2026 */

// Esperar a que el DOM esté cargado
document.addEventListener('DOMContentLoaded', function() {
    
    // Auto-cerrar alertas después de 5 segundos
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Confirmación para eliminaciones
    const deleteForms = document.querySelectorAll('.delete-form');
    deleteForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!confirm('¿Está seguro de que desea eliminar este registro? Esta acción no se puede deshacer.')) {
                e.preventDefault();
            }
        });
    });
    
    // Búsqueda dinámica en selects (si existe la funcionalidad)
    const searchSelects = document.querySelectorAll('.search-select');
    searchSelects.forEach(function(select) {
        select.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const options = this.querySelectorAll('option');
            options.forEach(function(option) {
                const text = option.textContent.toLowerCase();
                option.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    });
    
    // Calcular totales en tiempo real en formularios de órdenes
    const cantidadInputs = document.querySelectorAll('.cantidad-input, .precio-input');
    cantidadInputs.forEach(function(input) {
        input.addEventListener('change', calcularTotalOrden);
        input.addEventListener('input', calcularTotalOrden);
    });
    
    // Validación de formularios antes de enviar
    const forms = document.querySelectorAll('form.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Manejo de modal de confirmación
    const confirmModals = document.querySelectorAll('[data-confirm]');
    confirmModals.forEach(function(element) {
        element.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
    
    // Actualizar hora actual en tiempo real (opcional)
    const clockElement = document.getElementById('clock');
    if (clockElement) {
        setInterval(function() {
            const now = new Date();
            clockElement.textContent = now.toLocaleString('es-CU');
        }, 1000);
    }
    
    console.log('Sistema de Taller de Impresoras cargado correctamente');
});

// Función para calcular total de orden (implementación básica)
function calcularTotalOrden() {
    const totalElement = document.getElementById('total-orden');
    if (!totalElement) return;
    
    let total = 0;
    
    // Sumar piezas
    const filasPiezas = document.querySelectorAll('.fila-pieza');
    filasPiezas.forEach(function(fila) {
        const cantidad = parseFloat(fila.querySelector('.cantidad-input')?.value) || 0;
        const precio = parseFloat(fila.querySelector('.precio-input')?.value) || 0;
        total += cantidad * precio;
    });
    
    // Sumar mano de obra
    const manoObraCosto = parseFloat(document.getElementById('mano-obra-costo')?.value) || 0;
    total += manoObraCosto;
    
    totalElement.textContent = '$' + total.toFixed(2) + ' CUP';
}

// Función para agregar pieza a orden (usada en formulario dinámico)
function agregarPiezaAOrden(id, nombre, precio, unidad) {
    const contenedor = document.getElementById('piezas-seleccionadas');
    if (!contenedor) return;
    
    const fila = document.createElement('div');
    fila.className = 'row mb-2 fila-pieza';
    fila.innerHTML = `
        <div class="col-md-4">
            <input type="hidden" name="pieza_id[]" value="${id}">
            <span class="nombre-pieza">${nombre}</span>
        </div>
        <div class="col-md-2">
            <input type="number" class="form-control form-control-sm cantidad-input" name="cantidad[]" value="1" min="0.1" step="0.1">
        </div>
        <div class="col-md-2">
            <input type="number" class="form-control form-control-sm precio-input" name="precio[]" value="${precio}" min="0" step="0.01">
        </div>
        <div class="col-md-2">
            <span class="text-muted">${unidad}</span>
        </div>
        <div class="col-md-2">
            <button type="button" class="btn btn-sm btn-danger" onclick="this.parentElement.parentElement.remove(); calcularTotalOrden();">Eliminar</button>
        </div>
    `;
    
    contenedor.appendChild(fila);
    calcularTotalOrden();
}

// Función para imprimir recibo
function imprimirRecibo(ordenId) {
    window.open('/ordenes/imprimir/' + ordenId, '_blank');
}

// Exportar tabla a CSV
function exportarTablaCSV(tablaId, nombreArchivo) {
    const tabla = document.getElementById(tablaId);
    if (!tabla) return;
    
    let csv = [];
    const filas = tabla.querySelectorAll('tr');
    
    filas.forEach(function(fila) {
        const columnas = fila.querySelectorAll('th, td');
        const filaData = [];
        columnas.forEach(function(columna) {
            filaData.push('"' + columna.textContent.replace(/"/g, '""') + '"');
        });
        csv.push(filaData.join(','));
    });
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = nombreArchivo + '.csv';
    link.click();
}
