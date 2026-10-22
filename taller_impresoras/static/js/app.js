/* ============================================
   MegaPrint Lab v2.0 - Modern UI/UX System
   JavaScript personalizado con funcionalidades modernas
   ============================================ */

// Esperar a que el DOM esté cargado
document.addEventListener('DOMContentLoaded', function() {
    
    // ========================================
    // SIDEBAR
    // ========================================
    // El colapso del sidebar se realiza automáticamente vía media queries
    // en custom.css (@media max-width: 1024px). Ya no existe botón de toggle
    // en escritorio ni estado persistido en localStorage.
    
    // ========================================
    // MODO OSCURO
    // ========================================
    const themeToggle = document.getElementById('themeToggle');
    
    // Cargar tema preferido
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);
    
    function applyTheme(theme) {
        if (theme === 'dark') {
            document.body.classList.add('dark-mode');
            if (themeToggle) themeToggle.innerHTML = '☀️';
        } else {
            document.body.classList.remove('dark-mode');
            if (themeToggle) themeToggle.innerHTML = '🌙';
        }
        localStorage.setItem('theme', theme);
    }
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const newTheme = document.body.classList.contains('dark-mode') ? 'light' : 'dark';
            applyTheme(newTheme);
        });
    }
    
    // ========================================
    // COMMAND PALETTE (Ctrl + K / Cmd + K)
    // Estilo VS Code / Notion / Linear
    // ========================================
    initCommandPalette();
    
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

// ============================================
// COMMAND PALETTE - Implementación completa
// (Ctrl+K / Cmd+K, búsqueda fuzzy, navegación por teclado,
//  roles de usuario, agrupación por categoría y accesibilidad)
// ============================================
function initCommandPalette() {
    const palette = document.getElementById('commandPalette');
    const input = document.getElementById('commandInput');
    const results = document.getElementById('commandResults');
    const searchGlobal = document.getElementById('searchGlobal');
    
    if (!palette || !input || !results) return;
    
    // ---- Inyección del rol desde Jinja2 (base.html define window.USER_ROLE) ----
    // Fallback: si no se inyecta, tratar como invitado (solo comandos públicos).
    const userRole = (typeof window.USER_ROLE === 'string' && window.USER_ROLE) ? window.USER_ROLE : '';
    
    // ---- Catálogo de comandos ----
    // category: agrupación en la UI | roles: roles permitidos (ausente = todos)
    const commands = [
        // Navegación
        { id: 'dashboard',        title: 'Ir al Dashboard',          subtitle: 'Panel principal',            category: 'Navegación', icon: '📊', url: '/',      roles: ['administrador', 'tecnico', 'proveedor', 'cliente'] },
        { id: 'ordenes',          title: 'Órdenes',                  subtitle: 'Gestionar órdenes de servicio', category: 'Navegación', icon: '📋', url: '/ordenes',     roles: ['administrador', 'tecnico', 'proveedor', 'cliente'] },
        { id: 'clientes',         title: 'Clientes',                 subtitle: 'Administrar clientes',          category: 'Navegación', icon: '👥', url: '/clientes',     roles: ['administrador', 'tecnico'] },
        { id: 'dispositivos',     title: 'Dispositivos',             subtitle: 'Equipos registrados',           category: 'Navegación', icon: '🖨️', url: '/dispositivos', roles: ['administrador', 'tecnico', 'cliente'] },
        { id: 'inventario',       title: 'Inventario',               subtitle: 'Piezas y repuestos',            category: 'Navegación', icon: '📦', url: '/inventario',   roles: ['administrador', 'tecnico'] },
        { id: 'tecnicos',         title: 'Técnicos',                 subtitle: 'Equipo técnico',                category: 'Navegación', icon: '🔧', url: '/tecnicos',     roles: ['administrador'] },
        { id: 'contratos',        title: 'Contratos',                subtitle: 'Contratos de servicio',         category: 'Navegación', icon: '📝', url: '/contratos',    roles: ['administrador'] },
        { id: 'proveedores',      title: 'Proveedores',              subtitle: 'Gestión de proveedores',        category: 'Navegación', icon: '🚚', url: '/proveedores',  roles: ['administrador', 'proveedor'] },
        { id: 'reportes',         title: 'Reportes',                 subtitle: 'Análisis y finanzas',           category: 'Navegación', icon: '📈', url: '/reportes',     roles: ['administrador', 'tecnico'] },
        { id: 'usuarios',         title: 'Usuarios',                 subtitle: 'Gestión de usuarios',           category: 'Navegación', icon: '👤', url: '/usuarios',     roles: ['administrador'] },
        { id: 'auditoria',        title: 'Auditoría',                subtitle: 'Registro de actividad',         category: 'Navegación', icon: '🔍', url: '/admin/auditoria',    roles: ['administrador'] },
        { id: 'configuracion',    title: 'Configuración',            subtitle: 'Ajustes del taller',            category: 'Navegación', icon: '⚙️', url: '/configuracion_taller', roles: ['administrador'] },
        { id: 'ayuda',            title: 'Ayuda',                    subtitle: 'Documentación y soporte',       category: 'Navegación', icon: '📚', url: '/ayuda' },
        
        // Crear
        { id: 'nueva-orden',      title: 'Nueva Orden',              subtitle: 'Crear orden de servicio',       category: 'Crear', icon: '➕', url: '/ordenes/nuevo',      roles: ['administrador', 'tecnico'] },
        { id: 'nuevo-cliente',    title: 'Nuevo Cliente',            subtitle: 'Registrar cliente',             category: 'Crear', icon: '➕', url: '/clientes/nuevo',     roles: ['administrador'] },
        { id: 'nuevo-dispositivo',title: 'Nuevo Dispositivo',        subtitle: 'Registrar equipo',              category: 'Crear', icon: '➕', url: '/dispositivos/nuevo', roles: ['administrador', 'tecnico'] },
        { id: 'nueva-pieza',      title: 'Nueva Pieza',              subtitle: 'Agregar pieza al inventario',   category: 'Crear', icon: '➕', url: '/inventario/nuevo',   roles: ['administrador'] },
        { id: 'nuevo-tecnico',    title: 'Nuevo Técnico',            subtitle: 'Registrar técnico',             category: 'Crear', icon: '➕', url: '/tecnicos/nuevo',     roles: ['administrador'] },
        { id: 'nuevo-usuario',    title: 'Nuevo Usuario',            subtitle: 'Crear usuario',                 category: 'Crear', icon: '➕', url: '/usuarios/nuevo',     roles: ['administrador'] },
        { id: 'nuevo-contrato',   title: 'Nuevo Contrato',           subtitle: 'Crear contrato',                category: 'Crear', icon: '➕', url: '/contratos/nuevo',    roles: ['administrador'] },
        { id: 'nuevo-proveedor',  title: 'Nuevo Proveedor',          subtitle: 'Registrar proveedor',           category: 'Crear', icon: '➕', url: '/proveedores/nuevo',  roles: ['administrador'] },
        
        // Acciones (ejecutadas en el cliente)
        { id: 'modo-oscuro',      title: 'Alternar modo oscuro',     subtitle: 'Cambiar tema claro/oscuro',     category: 'Acciones', icon: '🌗', action: 'toggleTheme' },
        { id: 'salir',            title: 'Cerrar sesión',            subtitle: 'Salir del sistema',             category: 'Acciones', icon: '🚪', url: '/logout' },
    ];
    
    // ---- Filtrar comandos disponibles según el rol del usuario ----
    const availableCommands = commands.filter(cmd => !cmd.roles || cmd.roles.includes(userRole));
    
    // ---- Estado ----
    const MAX_VISIBLE = 8;          // alturas visibles aprox. (el resto con scroll)
    let filtered = [];              // resultados actuales
    let activeIndex = -1;           // comando resaltado
    let lastFocused = null;         // elemento enfocado antes de abrir (para restaurar)
    let isOpen = false;
    
    // ---- Accesibilidad: atributos ARIA ----
    palette.setAttribute('role', 'dialog');
    palette.setAttribute('aria-modal', 'true');
    palette.setAttribute('aria-labelledby', 'commandPaletteTitle');
    palette.setAttribute('aria-hidden', 'true');
    input.setAttribute('role', 'combobox');
    input.setAttribute('aria-expanded', 'false');
    input.setAttribute('aria-controls', 'commandResults');
    input.setAttribute('aria-autocomplete', 'list');
    results.setAttribute('role', 'listbox');
    results.setAttribute('id', 'commandResults');
    
    // Ocultar el diálogo para lectores de pantalla cuando está cerrado
    if (!palette.querySelector('.visually-hidden')) {
        const label = document.createElement('span');
        label.id = 'commandPaletteTitle';
        label.className = 'visually-hidden';
        label.textContent = 'Paleta de comandos';
        palette.insertBefore(label, palette.firstChild);
    }
    
    // ---- Búsqueda fuzzy ----
    // Devuelve { score, indices } si todas las letras de `query` aparecen
    // en `text` en orden (subsequence match), o null si no hay coincidencia.
    function fuzzyMatch(text, query) {
        if (!query) return { score: 0, indices: [] };
        text = text.toLowerCase();
        query = query.toLowerCase();
        
        // Coincidencia exacta de prefijo/palabra: puntaje alto
        if (text.startsWith(query)) {
            return { score: 1000 + query.length * 10, indices: Array.from({ length: query.length }, (_, i) => i) };
        }
        
        // Subsequence match con bonus por consecutividad y posición inicial
        let ti = 0, score = 0, lastIdx = -2;
        const indices = [];
        for (let qi = 0; qi < query.length; qi++) {
            const ch = query[qi];
            const found = text.indexOf(ch, ti);
            if (found === -1) return null;
            indices.push(found);
            score += 10;
            if (found === lastIdx + 1) score += 15;               // caracteres consecutivos
            if (found === 0 || /[\s_-]/.test(text[found - 1])) score += 20; // inicio de palabra
            score -= Math.floor(found / 4);                        // penalizar coincidencias tardías
            lastIdx = found;
            ti = found + 1;
        }
        return { score, indices };
    }
    
    // Resaltar las coincidencias dentro del texto (escapando HTML primero)
    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
    
    function highlight(text, indices) {
        const safe = escapeHtml(text);
        if (!indices || indices.length === 0) return safe;
        let out = '', idx = 0;
        for (const i of indices) {
            out += safe.slice(idx, i) + '<mark class="cp-highlight">' + safe[i] + '</mark>';
            idx = i + 1;
        }
        return out + safe.slice(idx);
    }
    
    // ---- Filtrado y ordenamiento ----
    function filterCommands(query) {
        if (!query.trim()) {
            return availableCommands.map(cmd => ({ cmd, score: 0, titleIndices: [], subIndices: [] }));
        }
        const scored = [];
        for (const cmd of availableCommands) {
            const mTitle = fuzzyMatch(cmd.title, query);
            const mSub = fuzzyMatch(cmd.subtitle, query);
            const mCat = fuzzyMatch(cmd.category || '', query);
            if (mTitle || mSub || mCat) {
                const best = Math.max(
                    mTitle ? mTitle.score : -Infinity,
                    mSub ? mSub.score + 5 : -Infinity,   // ligero bonus si coincide título
                    mCat ? mCat.score - 30 : -Infinity
                );
                scored.push({
                    cmd,
                    score: best,
                    titleIndices: mTitle ? mTitle.indices : [],
                    subIndices: mSub ? mSub.indices : []
                });
            }
        }
        scored.sort((a, b) => b.score - a.score);
        return scored;
    }
    
    // ---- Renderizado (agrupado por categoría) ----
    function render(query) {
        filtered = filterCommands(query);
        activeIndex = filtered.length > 0 ? 0 : -1;
        
        if (filtered.length === 0) {
            results.innerHTML = '<div class="cp-empty">No se encontraron comandos para “' + escapeHtml(query) + '”</div>';
            input.setAttribute('aria-expanded', 'false');
            return;
        }
        
        // Agrupar manteniendo el orden por puntaje
        const groups = {};
        const groupOrder = [];
        filtered.forEach((item, globalIndex) => {
            item.globalIndex = globalIndex;
            const cat = item.cmd.category || 'Otros';
            if (!groups[cat]) { groups[cat] = []; groupOrder.push(cat); }
            groups[cat].push(item);
        });
        
        let html = '';
        for (const cat of groupOrder) {
            html += '<div class="cp-group-label" role="presentation">' + escapeHtml(cat) + '</div>';
            for (const item of groups[cat]) {
                const cmd = item.cmd;
                html += `
                    <div class="command-item${item.globalIndex === activeIndex ? ' active' : ''}"
                         role="option" aria-selected="${item.globalIndex === activeIndex}"
                         data-index="${item.globalIndex}" data-url="${escapeHtml(cmd.url || '')}" data-action="${escapeHtml(cmd.action || '')}" tabindex="-1">
                        <div class="command-item-icon">${cmd.icon}</div>
                        <div class="command-item-text">
                            <div class="command-item-title">${highlight(cmd.title, item.titleIndices)}</div>
                            <div class="command-item-subtitle">${highlight(cmd.subtitle, item.subIndices)}</div>
                        </div>
                        <kbd class="cp-kbd">Enter</kbd>
                    </div>`;
            }
        }
        results.innerHTML = html;
        input.setAttribute('aria-expanded', 'true');
        updateActiveDescendant();
        
        // Eventos de click (delegación)
        results.querySelectorAll('.command-item').forEach(item => {
            item.addEventListener('click', () => executeCommand(parseInt(item.dataset.index, 10)));
            item.addEventListener('mousemove', () => setActive(parseInt(item.dataset.index, 10), false));
        });
        
        ensureVisible();
    }
    
    // ---- Selección activa ----
    function setActive(index, scroll = true) {
        if (filtered.length === 0) return;
        index = ((index % filtered.length) + filtered.length) % filtered.length;
        const prev = results.querySelector('.command-item.active');
        if (prev) {
            prev.classList.remove('active');
            prev.setAttribute('aria-selected', 'false');
        }
        activeIndex = index;
        const next = results.querySelector(`.command-item[data-index="${index}"]`);
        if (next) {
            next.classList.add('active');
            next.setAttribute('aria-selected', 'true');
            if (scroll) ensureVisible();
        }
        updateActiveDescendant();
    }
    
    function updateActiveDescendant() {
        const active = results.querySelector('.command-item.active');
        input.setAttribute('aria-activedescendant', active ? '' : '');
        if (active) {
            if (!active.id) active.id = 'cp-option-' + active.dataset.index;
            input.setAttribute('aria-activedescendant', active.id);
        }
    }
    
    // Mantener el ítem activo visible (scroll máximo ~8 resultados)
    function ensureVisible() {
        const active = results.querySelector('.command-item.active');
        if (!active) return;
        if (typeof active.scrollIntoView === 'function') {
            active.scrollIntoView({ block: 'nearest' });
        } else {
            // Fallback para navegadores/entornos sin scrollIntoView
            const itemTop = active.offsetTop, itemBottom = itemTop + active.offsetHeight;
            const viewTop = results.scrollTop, viewBottom = viewTop + results.clientHeight;
            if (itemTop < viewTop) results.scrollTop = itemTop;
            else if (itemBottom > viewBottom) results.scrollTop = itemBottom - results.clientHeight;
        }
    }
    
    // ---- Ejecución de comandos ----
    function executeCommand(index) {
        const item = filtered[index];
        if (!item) return;
        const cmd = item.cmd;
        closeCommandPalette();
        if (cmd.action) {
            runAction(cmd.action);
        } else if (cmd.url) {
            window.location.href = cmd.url;
        }
    }
    
    function runAction(action) {
        switch (action) {
            case 'toggleTheme': {
                const toggle = document.getElementById('themeToggle');
                if (toggle) toggle.click();
                break;
            }
        }
    }
    
    // ---- Abrir / Cerrar ----
    function openCommandPalette() {
        if (isOpen) return;
        isOpen = true;
        lastFocused = document.activeElement;
        palette.classList.add('show');
        palette.setAttribute('aria-hidden', 'false');
        input.value = '';
        render('');
        input.focus();
    }
    
    function closeCommandPalette() {
        if (!isOpen) return;
        isOpen = false;
        palette.classList.remove('show');
        palette.setAttribute('aria-hidden', 'true');
        input.setAttribute('aria-expanded', 'false');
        if (lastFocused && typeof lastFocused.focus === 'function') {
            lastFocused.focus();
        }
        lastFocused = null;
    }
    
    function toggleCommandPalette() {
        isOpen ? closeCommandPalette() : openCommandPalette();
    }
    
    // ---- Atajos globales: Ctrl+K / Cmd+K y Escape ----
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
            e.preventDefault();
            toggleCommandPalette();
            return;
        }
        if (e.key === 'Escape' && isOpen) {
            e.preventDefault();
            e.stopPropagation();
            closeCommandPalette();
        }
    });
    
    // ---- Navegación con teclado dentro de la paleta ----
    input.addEventListener('keydown', (e) => {
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                setActive(activeIndex + 1);
                break;
            case 'ArrowUp':
                e.preventDefault();
                setActive(activeIndex - 1);
                break;
            case 'Enter':
                e.preventDefault();
                executeCommand(activeIndex);
                break;
            case 'Home':
                if (e.ctrlKey) { e.preventDefault(); setActive(0); }
                break;
            case 'End':
                if (e.ctrlKey) { e.preventDefault(); setActive(filtered.length - 1); }
                break;
        }
    });
    
    // También capturar flechas/Enter si el foco está en la lista
    palette.addEventListener('keydown', (e) => {
        if (e.target === input) return;
        if (e.key === 'ArrowDown') { e.preventDefault(); setActive(activeIndex + 1); }
        if (e.key === 'ArrowUp')   { e.preventDefault(); setActive(activeIndex - 1); }
        if (e.key === 'Enter')     { e.preventDefault(); executeCommand(activeIndex); }
    });
    
    // ---- Filtrado en vivo mientras se escribe ----
    input.addEventListener('input', function() {
        render(this.value);
    });
    
    // ---- Abrir al hacer click/foco en el buscador global ----
    if (searchGlobal) {
        // El buscador global es un input decorativo: se vuelve readonly para
        // que no reciba teclado y delegue toda la búsqueda en la paleta.
        searchGlobal.setAttribute('readonly', 'readonly');
        searchGlobal.setAttribute('aria-label', 'Abrir paleta de comandos (Ctrl+K)');
        const openFromSearch = () => openCommandPalette();
        searchGlobal.addEventListener('click', openFromSearch);
        searchGlobal.addEventListener('focus', openFromSearch);
    }
    
    // ---- Cerrar al hacer click fuera ----
    document.addEventListener('click', function(e) {
        if (isOpen && !palette.contains(e.target) && e.target !== searchGlobal) {
            closeCommandPalette();
        }
    });
    
    // ---- Focus trap: mantener el foco dentro del modal mientras está abierto ----
    // Se intercepta Tab antes de que ocurra el movimiento de foco; si el siguiente
    // elemento enfocado quedaría fuera del diálogo, se devuelve el foco al input.
    palette.addEventListener('keydown', function(e) {
        if (e.key !== 'Tab' || !isOpen) return;
        const focusables = Array.from(palette.querySelectorAll(
            'input, [tabindex]:not([tabindex="-1"])'
        )).filter(el => !el.disabled && el.offsetParent !== null);
        if (focusables.length === 0) { e.preventDefault(); input.focus(); return; }
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        const current = document.activeElement;
        if (e.shiftKey && (current === first || !palette.contains(current))) {
            e.preventDefault();
            last.focus();
        } else if (!e.shiftKey && (current === last || !palette.contains(current))) {
            e.preventDefault();
            first.focus();
        }
    });
    
    // Red de seguridad: si por cualquier motivo el foco escapa del diálogo,
    // devolverlo al input de la paleta.
    document.addEventListener('focusin', (e) => {
        if (isOpen && !palette.contains(e.target) && e.target !== document.body) {
            input.focus();
        }
    });
    
    // Exponer para pruebas/debugging
    window.__commandPalette = { open: openCommandPalette, close: closeCommandPalette, toggle: toggleCommandPalette };
}

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
