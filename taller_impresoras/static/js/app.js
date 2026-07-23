/* ============================================
   MegaPrint Lab v2.0 - Modern UI/UX System
   JavaScript personalizado con funcionalidades modernas
   ============================================ */

// Esperar a que el DOM esté cargado
document.addEventListener('DOMContentLoaded', function() {
    
    // ========================================
    // SIDEBAR COLAPSABLE
    // ========================================
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarToggleTop = document.getElementById('sidebarToggleTop');
    
    // Cargar estado del sidebar desde localStorage
    const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (sidebar && sidebarCollapsed) {
        sidebar.classList.add('collapsed');
        if (sidebarToggle) sidebarToggle.innerHTML = '▶';
    }
    
    // Toggle sidebar
    function toggleSidebar() {
        if (sidebar) {
            sidebar.classList.toggle('collapsed');
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed);
            if (sidebarToggle) {
                sidebarToggle.innerHTML = isCollapsed ? '▶' : '◀';
            }
        }
    }
    
    if (sidebarToggle) sidebarToggle.addEventListener('click', toggleSidebar);
    if (sidebarToggleTop) sidebarToggleTop.addEventListener('click', toggleSidebar);
    
    // ========================================
    // MODO OSCURO
    // ========================================
    const themeToggle = document.getElementById('themeToggle');
    
    // Cargar tema preferido
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);
    
    function applyTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
            if (themeToggle) themeToggle.innerHTML = '☀️';
        } else {
            document.documentElement.removeAttribute('data-theme');
            if (themeToggle) themeToggle.innerHTML = '🌙';
        }
        localStorage.setItem('theme', theme);
    }
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
        });
    }
    
    // ========================================
    // COMMAND PALETTE (Ctrl + K)
    // ========================================
    const commandPalette = document.getElementById('commandPalette');
    const commandInput = document.getElementById('commandInput');
    const commandResults = document.getElementById('commandResults');
    const searchGlobal = document.getElementById('searchGlobal');
    
    // Comandos disponibles
    const commands = [
        { id: 'dashboard', title: 'Ir al Dashboard', subtitle: 'Panel principal', icon: '📊', url: '/dashboard' },
        { id: 'ordenes', title: 'Órdenes', subtitle: 'Gestionar órdenes de servicio', icon: '📋', url: '/ordenes' },
        { id: 'clientes', title: 'Clientes', subtitle: 'Administrar clientes', icon: '👥', url: '/clientes' },
        { id: 'dispositivos', title: 'Dispositivos', subtitle: 'Equipos registrados', icon: '🖨️', url: '/dispositivos' },
        { id: 'inventario', title: 'Inventario', subtitle: 'Piezas y repuestos', icon: '📦', url: '/inventario' },
        { id: 'tecnicos', title: 'Técnicos', subtitle: 'Equipo técnico', icon: '🔧', url: '/tecnicos' },
        { id: 'reportes', title: 'Reportes', subtitle: 'Análisis y finanzas', icon: '📈', url: '/reportes' },
        { id: 'usuarios', title: 'Usuarios', subtitle: 'Gestión de usuarios', icon: '👤', url: '/usuarios' },
        { id: 'configuracion', title: 'Configuración', subtitle: 'Ajustes del taller', icon: '⚙️', url: '/configuracion-taller' },
        { id: 'ayuda', title: 'Ayuda', subtitle: 'Documentación y soporte', icon: '📚', url: '/ayuda' },
        { id: 'nueva-orden', title: 'Nueva Orden', subtitle: 'Crear orden de servicio', icon: '➕', url: '/ordenes/nuevo' },
        { id: 'nuevo-cliente', title: 'Nuevo Cliente', subtitle: 'Registrar cliente', icon: '➕', url: '/clientes/nuevo' },
        { id: 'nuevo-dispositivo', title: 'Nuevo Dispositivo', subtitle: 'Registrar equipo', icon: '➕', url: '/dispositivos/nuevo' },
        { id: 'nueva-pieza', title: 'Nueva Pieza', subtitle: 'Agregar pieza al inventario', icon: '➕', url: '/inventario/nuevo' },
        { id: 'nuevo-tecnico', title: 'Nuevo Técnico', subtitle: 'Registrar técnico', icon: '➕', url: '/tecnicos/nuevo' },
        { id: 'nuevo-usuario', title: 'Nuevo Usuario', subtitle: 'Crear usuario', icon: '➕', url: '/usuarios/nuevo' },
        { id: 'nuevo-contrato', title: 'Nuevo Contrato', subtitle: 'Crear contrato', icon: '➕', url: '/contratos/nuevo' },
        { id: 'nuevo-proveedor', title: 'Nuevo Proveedor', subtitle: 'Registrar proveedor', icon: '➕', url: '/proveedores/nuevo' },
    ];
    
    // Abrir command palette con Ctrl+K
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            openCommandPalette();
        }
        if (e.key === 'Escape' && commandPalette && commandPalette.classList.contains('show')) {
            closeCommandPalette();
        }
    });
    
    // Abrir al hacer click en search global
    if (searchGlobal) {
        searchGlobal.addEventListener('click', openCommandPalette);
    }
    
    function openCommandPalette() {
        if (commandPalette) {
            commandPalette.classList.add('show');
            if (commandInput) {
                commandInput.value = '';
                commandInput.focus();
                renderCommands(commands);
            }
        }
    }
    
    function closeCommandPalette() {
        if (commandPalette) {
            commandPalette.classList.remove('show');
        }
    }
    
    // Cerrar al hacer click fuera
    document.addEventListener('click', function(e) {
        if (commandPalette && !commandPalette.contains(e.target) && e.target !== searchGlobal) {
            closeCommandPalette();
        }
    });
    
    // Filtrar comandos
    if (commandInput) {
        commandInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const filtered = commands.filter(cmd => 
                cmd.title.toLowerCase().includes(searchTerm) ||
                cmd.subtitle.toLowerCase().includes(searchTerm)
            );
            renderCommands(filtered);
        });
    }
    
    function renderCommands(cmds) {
        if (!commandResults) return;
        
        if (cmds.length === 0) {
            commandResults.innerHTML = '<div class="empty-state" style="padding: 2rem;"><p>No se encontraron resultados</p></div>';
            return;
        }
        
        commandResults.innerHTML = cmds.map(cmd => `
            <div class="command-item" data-url="${cmd.url}">
                <div class="command-item-icon">${cmd.icon}</div>
                <div class="command-item-text">
                    <div class="command-item-title">${cmd.title}</div>
                    <div class="command-item-subtitle">${cmd.subtitle}</div>
                </div>
            </div>
        `).join('');
        
        // Agregar eventos de click
        commandResults.querySelectorAll('.command-item').forEach(item => {
            item.addEventListener('click', function() {
                const url = this.dataset.url;
                if (url) window.location.href = url;
            });
        });
    }
    
    // ========================================
    // FUNCIONALIDAD EXISTENTE (alertas, etc.)
    // ========================================
    
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
    
    console.log('✅ MegaPrint Lab v2.0 cargado correctamente');
});

// Función para calcular total de orden
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

// Función para agregar pieza a orden
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

// Mostrar toast/notificación
function showToast(message, type = 'info') {
    const container = document.createElement('div');
    container.className = `alert alert-${type} alert-dismissible fade show`;
    container.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 9999; min-width: 300px;';
    container.innerHTML = `
        <span class="alert-icon">${type === 'success' ? '✓' : type === 'danger' ? '✕' : 'ℹ'}</span>
        <span class="alert-content">${message}</span>
        <button type="button" class="alert-close" data-bs-dismiss="alert">×</button>
    `;
    document.body.appendChild(container);
    
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(container);
        bsAlert.close();
    }, 5000);
}
