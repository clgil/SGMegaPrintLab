# Instrucciones para Probar la Nueva Interfaz Móvil

## Resumen de Cambios

Se ha adaptado la interfaz de SGMegaPrintLab para dispositivos móviles con un layout similar a Facebook/X (Twitter), incluyendo:

1. **Barra de navegación superior estilo app** - Con iconos de secciones principales
2. **Menú "Más opciones"** - Desplegable con secciones secundarias
3. **Floating Action Button (FAB)** - Botón flotante para acciones rápidas
4. **Sidebar oculto en móvil** - Reemplazado por la nueva navegación

## Archivos Modificados

### 1. `templates/base.html`
- Se agregó la barra de navegación móvil (`mobile-top-nav`)
- Se implementó el menú desplegable "Más opciones"
- Se añadió el FAB con sus opciones contextuales
- Se incluyó el JavaScript para la interacción de los menús

### 2. `static/css/custom.css`
- Estilos para `.mobile-top-nav` y sus elementos
- Estilos para `.mobile-more-menu` (menú desplegable)
- Estilos para `.mobile-fab` y `.mobile-fab-menu`
- Ajustes responsive para el contenido principal
- Media queries para ocultar elementos móviles en desktop

## Cómo Probar los Cambios

### Método 1: Herramientas de Desarrollo del Navegador (Recomendado)

1. **Abrir la aplicación** en tu navegador (Chrome, Firefox, Edge, etc.)
   ```
   http://localhost:5000  # o la URL correspondiente
   ```

2. **Activar modo dispositivo móvil**:
   - **Chrome/Edge**: Presiona `F12` → Haz clic en el ícono de dispositivo (Ctrl+Shift+M)
   - **Firefox**: Presiona `F12` → Haz clic en el ícono de diseño responsive (Ctrl+Shift+M)

3. **Seleccionar un dispositivo**:
   - iPhone 12/13/14 (390x844)
   - Samsung Galaxy S20 (360x800)
   - iPad Mini (768x1024) - para ver el breakpoint

4. **Recargar la página** (`F5` o `Ctrl+R`)

### Método 2: Abrir en Dispositivo Real

1. Asegúrate de que tu dispositivo móvil esté en la misma red WiFi
2. Accede desde el navegador móvil a la IP de tu servidor:
   ```
   http://192.168.x.x:5000
   ```

## Qué Verificar en Móvil

### 1. Barra de Navegación Superior (Mobile Top Nav)

**Para Administradores:**
- ✅ Icono "Inicio" (Dashboard)
- ✅ Icono "Órdenes"
- ✅ Icono "Clientes"
- ✅ Icono "Más" (despliega menú adicional)

**Para Técnicos:**
- ✅ Icono "Inicio" (Dashboard)
- ✅ Icono "Órdenes"
- ✅ Icono "Equipos" (Dispositivos)
- ✅ Icono "Más" (despliega menú adicional)

**Para Proveedores:**
- ✅ Icono "Inicio" (Dashboard)
- ✅ Icono "Inventario"
- ✅ Icono "Más" (despliega menú adicional)

**Comportamiento esperado:**
- Los iconos deben estar centrados horizontalmente
- El icono activo debe tener fondo azul claro y texto azul
- Al hacer hover/tap, debe haber un cambio visual sutil

### 2. Menú "Más Opciones"

1. **Haz clic en el icono "Más"**
2. **Verifica que se despliegue** desde la esquina superior derecha
3. **Contenido según rol:**

   **Administrador:**
   - Dispositivos
   - Inventario
   - Técnicos
   - Reportes
   - Respaldo
   - Proveedores
   - Contratos
   - Configuración
   - --- (divisor)
   - Cambiar Clave
   - Usuarios
   - Ayuda
   - Cerrar Sesión (en rojo)

   **Técnico:**
   - Inventario
   - --- (divisor)
   - Cambiar Clave
   - Ayuda
   - Cerrar Sesión (en rojo)

   **Proveedor:**
   - Inventario
   - --- (divisor)
   - Cambiar Clave
   - Ayuda
   - Cerrar Sesión (en rojo)

4. **Pruebas de interacción:**
   - ✅ El menú se cierra al hacer clic fuera
   - ✅ El menú se cierra al seleccionar una opción
   - ✅ Las opciones activas tienen resaltado azul
   - ✅ "Cerrar Sesión" tiene color rojo

### 3. Floating Action Button (FAB)

1. **Ubicación**: Esquina inferior derecha, sobre el contenido
2. **Icono**: Debe mostrar "+" inicialmente

**Al hacer clic en el FAB:**
- ✅ El botón gira y muestra una "X"
- ✅ Se despliega el menú hacia arriba
- ✅ Las opciones aparecen con animación suave

**Opciones según rol:**

**Administrador/Técnico:**
- Nueva orden
- Nuevo dispositivo
- Nuevo cliente (solo admin)
- Entrada inventario (si aplica)

**Proveedor:**
- Entrada inventario

**Pruebas de interacción:**
- ✅ El menú se cierra al hacer clic fuera
- ✅ El menú se cierra al seleccionar una opción
- ✅ Cada opción navega a la ruta correcta

### 4. Botón Hamburguesa (Menú Lateral)

1. **Ubicación**: Esquina superior izquierda
2. **Funcionalidad**: Abre el sidebar offcanvas tradicional

**Verificar:**
- ✅ El botón es visible solo en móvil
- ✅ Al abrir, el sidebar aparece desde la izquierda
- ✅ El sidebar comienza debajo de la mobile-top-nav (60px)
- ✅ Las opciones del sidebar cierran el menú al seleccionar

### 5. Contenido Principal

**Verificar:**
- ✅ El contenido no queda oculto detrás de la mobile-top-nav
- ✅ Hay espacio suficiente arriba (padding-top ajustado)
- ✅ El FAB no tapa contenido importante
- ✅ Las tablas y tarjetas son legibles en móvil

### 6. Desktop (Pantallas ≥ 768px)

**Verificar:**
- ✅ La mobile-top-nav NO es visible
- ✅ El FAB NO es visible
- ✅ El botón hamburguesa NO es visible
- ✅ El sidebar tradicional funciona normalmente
- ✅ La navbar superior original se muestra correctamente

## Breakpoints

- **Móvil**: < 768px - Se muestra la nueva interfaz móvil
- **Desktop**: ≥ 768px - Se muestra la interfaz tradicional con sidebar

## Posibles Problemas y Soluciones

### Problema: Los elementos móviles se ven en desktop
**Solución**: Verifica que el ancho de ventana sea menor a 768px. Las clases `d-md-none` de Bootstrap ocultan los elementos en pantallas medianas y grandes.

### Problema: El menú "Más opciones" no se abre
**Solución**: 
1. Abre la consola del navegador (F12)
2. Busca errores de JavaScript
3. Verifica que el ID `moreOptionsBtn` exista en el HTML renderizado

### Problema: El FAB no muestra las opciones correctas
**Solución**: Verifica que el `current_user.rol` sea el correcto. Las opciones se filtran según el rol del usuario.

### Problema: El contenido queda tapado por la barra superior
**Solución**: Verifica que el CSS tenga el padding-top correcto:
```css
.main-content {
    padding-top: calc(60px + var(--space-4));
}
```

## Capturas de Pantalla Recomendadas

Para documentación, captura:
1. Vista general en móvil con la barra superior
2. Menú "Más opciones" desplegado
3. FAB abierto mostrando las acciones
4. Comparativa desktop vs móvil

## Notas Técnicas

- **Iconos**: Se utilizan Bootstrap Icons (bi-*)
- **Animaciones**: Transiciones CSS suaves (200-300ms)
- **Z-index**: 
  - mobile-top-nav: 1048
  - mobile-more-menu: 1047
  - mobile-fab-container: 1046
  - mobile-menu-btn: 1049
  - offcanvas: 1050
- **Colores**: Se usan las variables CSS existentes (--primary, --bg-card, etc.)
- **Responsive**: Mobile-first con media query @media (min-width: 768px) para desktop

## Compatibilidad

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ Navegadores móviles (iOS Safari, Chrome Android)
