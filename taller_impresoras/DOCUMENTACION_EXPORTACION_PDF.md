# Documentación: Funcionalidad de Exportación a PDF

## Resumen
Se ha añadido funcionalidad completa de exportación a PDF para los reportes del sistema SGMegaPrintLab, utilizando la biblioteca **fpdf2**.

## Bibliotecas Añadidas

### 1. fpdf2 (v2.8.7)
- **Propósito**: Generación de documentos PDF de forma nativa en Python
- **Ventajas**: 
  - No requiere dependencias externas complejas
  - Funciona 100% offline
  - Ligera y rápida
  - Compatible con el objetivo de recursos limitados del proyecto
  - API moderna con enums XPos/YPos

### 2. WeasyPrint (v62.0) - Opcional/Futuro
- **Propósito**: Conversión de HTML/CSS a PDF
- **Uso potencial**: Para reportes más complejos que requieran formato avanzado
- **Nota**: Requiere dependencias adicionales (Pango, Cairo)

## Archivos Modificados

### 1. `requirements.txt`
```txt
fpdf2==2.8.7
WeasyPrint==62.0
```

### 2. `routes/reportes.py`
- **Nueva ruta**: `/exportar_pdf/<tipo>`
- **Tipos soportados**:
  - `ingresos`: Reporte de ingresos por período
  - `piezas`: Reporte de piezas utilizadas
  - `clientes`: Reporte de clientes activos

### 3. Templates actualizados
- `templates/reportes/ingresos.html`
- `templates/reportes/piezas_utilizadas.html`
- `templates/reportes/clientes_activos.html`

Cada template ahora incluye un botón "Exportar PDF" junto al existente "Exportar CSV".

## Características de los PDFs Generados

### Reporte de Ingresos
- Título centrado: "Reporte de Ingresos"
- Período seleccionado
- Tabla con columnas:
  - Número de Orden
  - Fecha de Entrega
  - Cliente (truncado a 35 caracteres si es muy largo)
  - Total
- Total general al final
- Nombre de archivo: `ingresos_{fecha_inicio}_{fecha_fin}.pdf`

### Reporte de Piezas Utilizadas
- Título centrado: "Reporte de Piezas Utilizadas"
- Período seleccionado
- Tabla con columnas:
  - Pieza (truncada a 45 caracteres si es muy larga)
  - Unidad
  - Cantidad Total
- Nombre de archivo: `piezas_{fecha_inicio}_{fecha_fin}.pdf`

### Reporte de Clientes Activos
- Título centrado: "Reporte de Clientes Activos"
- Tabla con columnas:
  - # (número secuencial)
  - Cliente (truncado a 35 caracteres si es muy largo)
  - Teléfono
  - Total de Órdenes
- Nombre de archivo: `clientes_activos.pdf`

## Instalación

### En el servidor/equipo local:
```bash
cd /workspace/taller_impresoras
pip install -r requirements.txt
```

### Instalación individual (si es necesario):
```bash
pip install fpdf2==2.8.7
pip install WeasyPrint==62.0
```

## Uso

1. **Desde la interfaz web**:
   - Navegar a Reportes → Ingresos/Piezas/Clientes
   - Generar el reporte con los filtros deseados
   - Click en "Exportar PDF"
   - El navegador descargará automáticamente el archivo PDF

2. **Acceso directo por URL** (solo administradores):
   ```
   /reportes/exportar_pdf/ingresos?fecha_inicio=2025-01-01&fecha_fin=2025-12-31
   /reportes/exportar_pdf/piezas?fecha_inicio=2025-01-01&fecha_fin=2025-12-31
   /reportes/exportar_pdf/clientes
   ```

## Consideraciones Técnicas

### Codificación de Caracteres
- fpdf2 usa fuentes core (Helvetica) que soportan caracteres básicos Latin-1
- Los nombres con caracteres especiales (ñ, acentos) pueden requerir tratamiento especial
- Para soporte completo de UTF-8, se puede usar una fuente TrueType personalizada

### Formato de Página
- Tamaño: Carta (Letter) - 8.5" x 11"
- Márgenes: Estándar (aproximadamente 1 pulgada)
- Orientación: Vertical (Portrait)

### Fuentes
- Helvetica (fuente core estándar, reemplazo de Arial)
- Tamaños utilizados:
  - Títulos: 16pt Bold
  - Subtítulos: 12pt Regular
  - Encabezados de tabla: 10pt Bold
  - Datos de tabla: 9pt Regular

### API Moderna de fpdf2
- Se utilizan los enums `XPos` e `YPos` en lugar de parámetros deprecated
- `border=1` en lugar de valores numéricos para bordes
- `pdf.output()` devuelve bytes directamente (sin parámetro `dest`)

### Rendimiento
- Los PDFs se generan en memoria (BytesIO buffer)
- No se crean archivos temporales en el disco
- Adecuado para equipos con recursos limitados

## Comparación con reportlab (existente)

| Característica | reportlab (existente) | fpdf2 (nuevo) |
|---------------|----------------------|---------------|
| Complejidad | Alta | Baja |
| Curva de aprendizaje | Empinada | Suave |
| Dependencias | Múltiples | Mínimas |
| Flexibilidad | Muy alta | Media |
| Ideal para | Documentos complejos | Reportes simples |
| Offline | Sí | Sí |

**Decisión**: Se mantiene reportlab para las órdenes de reparación (documento complejo con membrete, logos, etc.) y se usa fpdf2 para reportes administrativos simples (tablas de datos).

## Futuras Mejoras Potenciales

1. **Soporte UTF-8 completo**: Implementar fuentes personalizadas para caracteres especiales
2. **Membrete institucional**: Añadir logo y datos del taller en todos los PDFs
3. **Gráficos**: Incorporar gráficos simples para reportes visuales
4. **WeasyPrint**: Para reportes que requieran formato HTML/CSS avanzado
5. **Exportación múltiple**: Permitir seleccionar varios reportes y generar un PDF combinado

## Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'fpdf'"
```bash
pip install fpdf2==2.8.7
```

### Error con caracteres especiales
Los caracteres como ñ, á, é, í, ó, ú pueden no mostrarse correctamente. Soluciones:
1. Usar fuentes TrueType con soporte UTF-8
2. Reemplazar caracteres especiales antes de generar el PDF
3. Migrar a WeasyPrint para esos reportes específicos

### Error: "Permission denied" al descargar
Verificar que la ruta de descarga del navegador tenga permisos de escritura.

## Pruebas Recomendadas

1. **Prueba básica**: Generar cada tipo de reporte con datos de ejemplo
2. **Prueba de límites**: Reportes con muchos registros (>100 filas)
3. **Prueba de caracteres**: Nombres de clientes con acentos y ñ
4. **Prueba offline**: Desconectar internet y verificar que funcione
5. **Prueba de rendimiento**: Medir tiempo de generación en equipo lento

## Contacto y Soporte

Para dudas o problemas relacionados con esta funcionalidad, consultar la documentación oficial:
- fpdf2: https://py-pdf.github.io/fpdf2/
- WeasyPrint: https://weasyprint.org/
