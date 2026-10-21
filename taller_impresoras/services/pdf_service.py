"""
Servicio centralizado de generación de PDFs para SGMegaPrintLab
================================================================

Estandariza TODA la renderización de PDFs sobre **fpdf2** (Python puro,
sin dependencias nativas del sistema operativo), lo que permite despliegues
offline tanto en Linux como en Windows sin instalar librerías C (libpango,
cairo, pangoft2, etc.) como exigiría WeasyPrint, ni mantener una segunda
API distinta como reportlab.

Responsabilidades del servicio:
    * Creación de documentos con márgenes A4 estandarizados.
    * Registro de fuentes Unicode (DejaVu Sans) para soportar correctamente
      los caracteres del español (á, é, í, ó, ú, ñ, ¿, ¡) y el símbolo ¥.
      Incluye fallback escalonado si el sistema no trae esas fuentes.
    * Helpers de maquetación reutilizables (encabezado, tabla con zebra,
      fila total, pie de página con numeración).
    * Manejo centralizado de errores: cualquier fallo devuelve ``None`` y
      queda registrado en el log de la aplicación; las rutas deciden cómo
      notificar al usuario.

Uso típico desde una ruta::

    from services.pdf_service import pdf_service

    buffer = pdf_service.generar_tabla(
        titulo='Reporte de Ingresos',
        subtitulo='Periodo: 2026-01-01 a 2026-01-31',
        encabezados=['Numero Orden', 'Fecha', 'Cliente', 'Total'],
        filas=[['OT-26-0001', '2026-01-10', 'Juan Pérez', '150.00'], ...],
        anchos=[40, 30, 80, 40],
        fila_total=('TOTAL GENERAL:', '1500.00'),
    )
    if buffer is None:
        flash('No se pudo generar el PDF', 'danger')
        return redirect(...)
    return send_file(buffer, mimetype='application/pdf', ...)
"""

from __future__ import annotations

import io
import logging
import os
import platform
from typing import Optional, Sequence

try:
    from fpdf import FPDF, XPos, YPos
except ImportError as exc:  # pragma: no cover - error de entorno
    raise RuntimeError(
        "La dependencia 'fpdf2' es obligatoria para el servicio de PDF. "
        "Instálala con: pip install fpdf2==2.8.7"
    ) from exc

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes de estilo corporativo (mismos tonos usados en el recibo HTML)
# ---------------------------------------------------------------------------
RGB_TEXTO = (44, 62, 80)          # #2c3e50
RGB_TEXTO_CLARO = (127, 140, 141)  # #7f8c8d
RGB_PRIMARIO = (52, 152, 219)     # #3498db
RGB_SECUNDARIO = (102, 126, 234)  # #667eea
RGB_HEADER_TABLA = (52, 73, 94)   # #34495e
RGB_FILA_ZEBRA = (248, 249, 250)  # #f8f9fa
RGB_BORDE_SUAVE = (236, 240, 241)  # #ecf0f1
BLANCO = (255, 255, 255)

# Márgenes estándar del sistema (en mm)
MARGEN_IZQUIERDA = 12.7
MARGEN_DERECHA = 12.7
MARGEN_SUPERIOR = 12.7
MARGEN_INFERIOR = 15.0


class PdfServiceError(Exception):
    """Error específico del servicio de PDFs."""


def _rutas_fuentes_dejavu() -> list[tuple[str, str]]:
    """Devuelve pares ``(regular, bold)`` candidatos para DejaVu Sans.

    Se buscan en este orden:
      1. Carpeta ``static/fonts`` del proyecto (portable / offline).
      2. Ubidades típicas de Linux (/usr/share/fonts/...).
      3. Ubicaciones típicas de Windows (C:\\Windows\\Fonts, %LOCALAPPDATA%).
    """
    candidatos: list[tuple[str, str]] = []

    # 1) Fuentes empaquetadas con la aplicación (recomendado para offline)
    base_static = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', 'static', 'fonts')
    )
    candidatos.append((
        os.path.join(base_static, 'DejaVuSans.ttf'),
        os.path.join(base_static, 'DejaVuSans-Bold.ttf'),
    ))

    # 2) Linux
    if platform.system() == 'Linux':
        for sub in (
            'truetype/dejavu',
            'dejavu',
            'truetype',
        ):
            d = os.path.join('/usr/share/fonts', sub)
            candidatos.append((
                os.path.join(d, 'DejaVuSans.ttf'),
                os.path.join(d, 'DejaVuSans-Bold.ttf'),
            ))

    # 3) Windows
    windir = os.environ.get('WINDIR', r'C:\Windows')
    candidatos.append((
        os.path.join(windir, 'Fonts', 'DejaVuSans.ttf'),
        os.path.join(windir, 'Fonts', 'DejaVuSans-Bold.ttf'),
    ))
    local_appdata = os.environ.get('LOCALAPPDATA')
    if local_appdata:
        d = os.path.join(local_appdata, 'Microsoft', 'Windows', 'Fonts')
        candidatos.append((
            os.path.join(d, 'DejaVuSans.ttf'),
            os.path.join(d, 'DejaVuSans-Bold.ttf'),
        ))

    return [(r, b) for r, b in candidatos if os.path.isfile(r) and os.path.isfile(b)]


class SGMFPDF(FPDF):
    """Subclase de FPDF con pie de página numerado opcional."""

    def __init__(self, *args, pie_pagina: bool = False, texto_pie: str = '', **kwargs):
        super().__init__(*args, **kwargs)
        self.pie_pagina = pie_pagina
        self.texto_pie = texto_pie

    def footer(self):
        if not self.pie_pagina:
            return
        # Guardar/restaurar: el footer no debe alterar el estado de fuente activo
        familia, estilo, tamano = self.font_family, self.font_style, self.font_size_pt
        self.set_y(-12)
        self.set_font(familia, '', 8)
        self.set_text_color(*RGB_TEXTO_CLARO)
        if self.texto_pie:
            self.cell(0, 4, self.texto_pie, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.cell(0, 4, f'Página {self.page_no()}', align='C')
        self.set_font(familia, estilo, tamano)


class PdfService:
    """Fachada única de renderizado PDF del sistema (basada en fpdf2)."""

    ANCHO_UTIL_A4 = 210 - MARGEN_IZQUIERDA - MARGEN_DERECHA  # 184.6 mm

    # ------------------------------------------------------------------
    # Construcción de documentos
    # ------------------------------------------------------------------
    def crear_documento(
        self,
        *,
        orientacion: str = 'P',
        formato: str = 'A4',
        pie_pagina: bool = True,
        texto_pie: str = '',
    ) -> SGMFPDF:
        """Crea un documento con márgenes estándar y fuente Unicode registrada.

        Raises:
            PdfServiceError: si fpdf2 no puede inicializar el documento.
        """
        try:
            pdf = SGMFPDF(orientation=orientacion, unit='mm', format=formato)
            pdf.set_margins(MARGEN_IZQUIERDA, MARGEN_SUPERIOR, MARGEN_DERECHA)
            pdf.set_auto_page_break(auto=True, margin=MARGEN_INFERIOR)
            pdf.pie_pagina = pie_pagina
            pdf.texto_pie = texto_pie
            self._registrar_fuentes(pdf)
            return pdf
        except Exception as exc:
            logger.exception('Fallo al inicializar el documento PDF')
            raise PdfServiceError(f'No se pudo inicializar el PDF: {exc}') from exc

    @staticmethod
    def _registrar_fuentes(pdf: SGMFPDF) -> None:
        """Registra una familia Unicode (negrita incluida) o hace fallback.

        Los caracteres del español (á, é, í, ó, ú, ñ, ¿, ¡) no se renderizan
        de forma fiable con las fuentes core Helvetica, por eso se prioriza
        DejaVu Sans (TTF). Si no se encuentra ningún TTF en el sistema, se
        degrada a Helvetica y los textos se sanitizan con ``latin-1`` para
        evitar errores de codificación en tiempo de ejecución.
        """
        for regular, bold in _rutas_fuentes_dejavu():
            try:
                pdf.add_font('Unicode', style='', fname=regular)
                pdf.add_font('Unicode', style='B', fname=bold)
                logger.debug('Fuente Unicode registrada desde %s', regular)
                return
            except Exception:
                logger.warning(
                    'No se pudo registrar la fuente %s; probando siguiente candidato', regular
                )

        logger.warning(
            'No se encontraron fuentes TTF Unicode; se usará Helvetica (latin-1). '
            'Para soporte completo del español coloque DejaVuSans.ttf y '
            'DejaVuSans-Bold.ttf en static/fonts/.'
        )

    def _fuente(self, pdf: SGMFPDF) -> str:
        """Devuelve la familia activa: 'Unicode' si hay TTF registrado, si no 'Helvetica'.

        fpdf2 normaliza las claves internas a minúsculas (``pdf.fonts`` usa la
        clave ``'unicode'`` cuando la familia fue registrada vía ``add_font``).
        """
        if 'unicode' in getattr(pdf, 'fonts', {}):
            return 'Unicode'
        return 'Helvetica'

    def _sanitizar(self, texto: str, familia: str) -> str:
        """Garantiza que el texto sea codificable con la fuente activa."""
        if familia == 'Unicode':
            return texto
        return str(texto).encode('latin-1', errors='replace').decode('latin-1')

    # ------------------------------------------------------------------
    # Bloques de maquetación reutilizables
    # ------------------------------------------------------------------
    def agregar_encabezado(
        self,
        pdf: SGMFPDF,
        titulo: str,
        subtitulo: str = '',
        tamano_titulo: int = 16,
    ) -> None:
        """Añade una página nueva con título centrado y subtítulo opcional."""
        familia = self._fuente(pdf)
        pdf.add_page()
        pdf.set_font(familia, 'B', tamano_titulo)
        pdf.set_text_color(*RGB_TEXTO)
        pdf.cell(
            0, 10, self._sanitizar(titulo, familia),
            new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C',
        )
        if subtitulo:
            pdf.set_font(familia, '', 11)
            pdf.set_text_color(*RGB_TEXTO_CLARO)
            pdf.cell(
                0, 8, self._sanitizar(subtitulo, familia),
                new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C',
            )
        pdf.ln(4)

    def agregar_tabla(
        self,
        pdf: SGMFPDF,
        encabezados: Sequence[str],
        filas: Sequence[Sequence[str]],
        anchos: Sequence[float],
        alineaciones: Optional[Sequence[str]] = None,
        alto_encabezado: float = 8,
        alto_fila: float = 7,
        tamano: float = 9,
    ) -> None:
        """Dibuja una tabla con cabecera coloreada y filas alternas (zebra)."""
        familia = self._fuente(pdf)
        alineaciones = alineaciones or ['L'] * len(encabezados)

        # Cabecera
        pdf.set_font(familia, 'B', tamano)
        pdf.set_fill_color(*RGB_HEADER_TABLA)
        pdf.set_text_color(*BLANCO)
        for txt, ancho, alin in zip(encabezados, anchos, alineaciones):
            pdf.cell(ancho, alto_encabezado, self._sanitizar(txt, familia),
                     border=1, fill=True, align=alin)
        pdf.ln()

        # Datos
        pdf.set_font(familia, '', tamano)
        pdf.set_text_color(*RGB_TEXTO)
        for i, fila in enumerate(filas):
            relleno = i % 2 == 1
            pdf.set_fill_color(*RGB_FILA_ZEBRA)
            for valor, ancho, alin in zip(fila, anchos, alineaciones):
                pdf.cell(ancho, alto_fila, self._sanitizar(valor, familia),
                         border=1, fill=relleno, align=alin)
            pdf.ln()

    def agregar_fila_total(
        self,
        pdf: SGMFPDF,
        etiqueta: str,
        valor: str,
        ancho_etiqueta: float,
        ancho_valor: float,
    ) -> None:
        """Resalta una fila de totales con fondo corporativo."""
        familia = self._fuente(pdf)
        pdf.ln(2)
        pdf.set_font(familia, 'B', 10)
        pdf.set_fill_color(*RGB_SECUNDARIO)
        pdf.set_text_color(*BLANCO)
        pdf.cell(ancho_etiqueta, 9, self._sanitizar(etiqueta, familia),
                 align='R', fill=True)
        pdf.cell(ancho_valor, 9, self._sanitizar(valor, familia),
                 border=1, align='R', fill=True,
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ------------------------------------------------------------------
    # Generadores de alto nivel
    # ------------------------------------------------------------------
    def generar_tabla(
        self,
        *,
        titulo: str,
        encabezados: Sequence[str],
        filas: Sequence[Sequence[str]],
        anchos: Sequence[float],
        subtitulo: str = '',
        alineaciones: Optional[Sequence[str]] = None,
        fila_total: Optional[tuple[str, str]] = None,
        texto_pie: str = 'SGMegaPrintLab - Reporte generado automáticamente',
    ) -> Optional[io.BytesIO]:
        """Genera un reporte tabular simple y devuelve un buffer listo para ``send_file``.

        Devuelve ``None`` si ocurre cualquier error (queda registrado en el log).
        """
        try:
            pdf = self.crear_documento(pie_pagina=True, texto_pie=texto_pie)
            self.agregar_encabezado(pdf, titulo, subtitulo)
            self.agregar_tabla(pdf, encabezados, filas, anchos, alineaciones)
            if fila_total:
                self.agregar_fila_total(
                    pdf, fila_total[0], fila_total[1],
                    ancho_etiqueta=sum(anchos[:-1]), ancho_valor=anchos[-1],
                )
            return self._finalizar(pdf)
        except PdfServiceError:
            return None
        except Exception:
            logger.exception('Error inesperado generando el PDF "%s"', titulo)
            return None

    def _texto(self, pdf: SGMFPDF, texto: str, tamano: int, *,
               bold: bool = False, color: tuple = RGB_TEXTO, alto: float = 5,
               align: str = 'L', ancho: Optional[float] = None) -> None:
        """Escribe una línea de texto con la fuente Unicode activa.

        ``ancho`` limita el ancho del multi_cell (para columnas dentro de
        cajas o badges); por defecto ocupa todo el ancho útil de página.
        """
        familia = self._fuente(pdf)
        pdf.set_font(familia, 'B' if bold else '', tamano)
        pdf.set_text_color(*color)
        pdf.multi_cell(ancho if ancho is not None else 0, alto,
                       self._sanitizar(texto, familia),
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=align)

    @staticmethod
    def _rect(pdf: SGMFPDF, x: float, y: float, w: float, h: float, relleno: tuple,
              borde_rgb: Optional[tuple] = None, grosor_borde: float = 0) -> None:
        """Dibuja un rectángulo (con relleno y borde opcionales)."""
        pdf.set_fill_color(*relleno)
        if borde_rgb is not None and grosor_borde > 0:
            pdf.set_draw_color(*borde_rgb)
            pdf.rect(x, y, w, h, style='FD')
        else:
            pdf.rect(x, y, w, h, style='F')

    def generar_recibo_orden(self, orden, config: dict) -> Optional[io.BytesIO]:
        """Genera el PDF del recibo/orden de reparación (documento complejo).

        Reemplaza al antiguo generador basado en reportlab. Recrea el mismo
        lenguaje visual del recibo HTML: membrete con badge de orden, cajas de
        cliente/equipo, problema reportado, diagnóstico, técnico, tabla de
        repuestos, bloque de totales, observaciones, firmas y pie de página.

        Args:
            orden: instancia ``models.Orden`` (con relaciones ya cargadas).
            config: dict de ``Configuracion`` (clave -> valor) del taller.

        Returns:
            Buffer binario listo para ``send_file``, o ``None`` si falla.
        """
        try:
            pdf = self.crear_documento(pie_pagina=True,
                                       texto_pie='SGMegaPrintLab - Comprobante de reparación')
            margen = MARGEN_IZQUIERDA
            ancho_util = self.ANCHO_UTIL_A4

            pdf.add_page()

            # === MEMBRETE ===
            y0 = pdf.get_y()
            nombre_taller = (config.get('nombre_taller') or 'Taller de Impresoras').upper()
            direccion = config.get('direccion_taller', '')
            telefono = config.get('telefono_taller', '')
            email = config.get('email_taller', '')

            partes_detalles = [p for p in (direccion, f'Tel: {telefono}' if telefono else '') if p]
            detalles = ' | '.join(partes_detalles)

            # Badge "ORDEN DE REPARACIÓN #OT-xx-xxxx" a la derecha
            ancho_badge = 62.0
            bx = margen + ancho_util - ancho_badge
            by = y0
            alto_badge = 20
            self._rect(pdf, bx, by, ancho_badge, alto_badge, RGB_SECUNDARIO)
            pdf.set_xy(bx, by + 2)
            self._texto(pdf, 'ORDEN DE REPARACIÓN', 7, bold=True, color=BLANCO,
                        align='C', alto=4, ancho=ancho_badge)
            pdf.set_xy(bx, by + 9)
            self._texto(pdf, f'#{orden.numero_orden}', 13, bold=True, color=BLANCO,
                        align='C', alto=8, ancho=ancho_badge)

            # Columna izquierda: nombre + datos del taller
            col_izq_ancho = ancho_util - ancho_badge - 4
            pdf.set_xy(margen, y0)
            self._texto(pdf, nombre_taller, 15, bold=True, color=RGB_TEXTO,
                        alto=7, ancho=col_izq_ancho)
            if detalles:
                pdf.set_xy(margen, pdf.get_y())
                self._texto(pdf, detalles, 8.5, color=RGB_TEXTO_CLARO,
                            alto=4.5, ancho=col_izq_ancho)
            if email:
                pdf.set_xy(margen, pdf.get_y())
                self._texto(pdf, email, 8, color=RGB_PRIMARIO, alto=4.5, ancho=col_izq_ancho)

            # Fecha / estado bajo el badge
            pdf.set_xy(bx, by + alto_badge + 2)
            self._texto(pdf, f'Fecha: {orden.fecha_entrada or ""}', 8.5,
                        color=RGB_TEXTO, alto=4.5, ancho=ancho_badge)
            pdf.set_xy(bx, pdf.get_y())
            self._texto(pdf, f'Estado: {orden.estado or ""}', 8.5,
                        color=RGB_TEXTO, alto=4.5, ancho=ancho_badge)

            # Línea divisoria corporativa
            y_div = max(y0 + alto_badge + 16, pdf.get_y() + 4)
            self._rect(pdf, margen, y_div, ancho_util, 1.2, RGB_PRIMARIO)
            pdf.set_y(y_div + 5)

            # === CAJAS CLIENTE / EQUIPO ===
            cliente = getattr(orden, 'cliente', None)
            dispositivo = getattr(orden, 'dispositivo', None)
            tecnico = getattr(orden, 'tecnico', None)

            def caja_cliente():
                lineas = [('DATOS DEL CLIENTE', True)]
                lineas.append((getattr(cliente, 'nombre', '') or 'Sin cliente', True))
                tel = getattr(cliente, 'telefono', '')
                if tel:
                    lineas.append((f'Teléfono: {tel}', False))
                dir_cli = getattr(cliente, 'direccion', '')
                if dir_cli:
                    lineas.append((self.truncar(dir_cli, 60), False))
                return lineas

            def caja_equipo():
                lineas = [('EQUIPO', True)]
                if dispositivo:
                    modelo = ' '.join(x for x in [dispositivo.tipo, dispositivo.marca,
                                                  dispositivo.modelo] if x)
                    lineas.append((self.truncar(modelo, 60) or 'Sin datos', True))
                    if dispositivo.numero_serie:
                        lineas.append((f'No. Serie: {dispositivo.numero_serie}', False))
                else:
                    lineas.append(('Sin equipo registrado', False))
                return lineas

            ancho_caja = ancho_util / 2 - 2
            alto_caja = 34
            yc = pdf.get_y()
            for j, contenido in enumerate([caja_cliente(), caja_equipo()]):
                cx = margen + j * (ancho_caja + 4)
                self._rect(pdf, cx, yc, ancho_caja, alto_caja, RGB_FILA_ZEBRA)
                self._rect(pdf, cx, yc, 1.4, alto_caja, RGB_PRIMARIO)  # barra lateral
                pdf.set_xy(cx + 5, yc + 3)
                for i, (txt, destacado) in enumerate(contenido):
                    es_seccion = i == 0
                    self._texto(pdf, txt, 8.5 if destacado else 8,
                                bold=destacado,
                                color=RGB_TEXTO if not es_seccion else RGB_TEXTO_CLARO,
                                alto=4.2, ancho=ancho_caja - 8)
                    pdf.set_xy(cx + 5, pdf.get_y() + (1.5 if es_seccion else 0.5))
            pdf.set_y(yc + alto_caja + 6)

            # === BLOQUES DE TEXTO ===
            def bloque(titulo_bloque: str, texto_bloque):
                if not texto_bloque:
                    return
                self._texto(pdf, titulo_bloque.upper(), 9, bold=True, color=RGB_TEXTO, alto=5)
                pdf.set_xy(margen, pdf.get_y() + 0.5)
                self._texto(pdf, str(texto_bloque), 8.5, color=RGB_TEXTO, alto=4.2,
                            ancho=ancho_util)
                pdf.ln(4)

            bloque('Problema reportado', orden.problema_reportado or '-')
            bloque('Diagnóstico técnico', getattr(orden, 'diagnostico', None))
            if tecnico:
                bloque('Técnico responsable', getattr(tecnico, 'nombre', ''))

            # === TABLA DE REPUESTOS ===
            subtotal_piezas = 0.0
            piezas = list(getattr(orden, 'piezas_usadas', []) or [])
            if piezas:
                self._texto(pdf, 'REPUESTOS UTILIZADOS', 9, bold=True, color=RGB_TEXTO)
                pdf.ln(1)
                anchos_rep = [ancho_util - 60, 14, 23, 23]
                filas_rep = []
                for op in piezas:
                    nombre_pieza = op.pieza_rel.nombre if op.pieza_rel else 'Pieza manual'
                    subtotal = op.cantidad * op.precio_unitario
                    subtotal_piezas += subtotal
                    filas_rep.append([
                        self.truncar(nombre_pieza, 45),
                        f'{op.cantidad:g}',
                        f'${op.precio_unitario:.2f}',
                        f'${subtotal:.2f}',
                    ])
                self.agregar_tabla(
                    pdf,
                    ['DESCRIPCIÓN', 'CANT.', 'PRECIO UNIT.', 'SUBTOTAL'],
                    filas_rep,
                    anchos_rep,
                    alineaciones=['L', 'C', 'R', 'R'],
                )
                # Subtotal de repuestos
                pdf.set_font(self._fuente(pdf), 'B', 8.5)
                pdf.set_fill_color(*RGB_FILA_ZEBRA)
                pdf.set_text_color(*RGB_TEXTO)
                pdf.cell(anchos_rep[0] + anchos_rep[1] + anchos_rep[2], 7,
                         'SUBTOTAL REPUESTOS:', align='R', fill=True)
                pdf.cell(anchos_rep[3], 7, f'${subtotal_piezas:.2f}', border=1,
                         align='R', fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(5)

            # === BLOQUE DE TOTALES ===
            mano_obra = orden.mano_obra_costo or 0
            costo_total = orden.costo_total or 0
            alto_totales = 30
            yt = pdf.get_y()
            self._rect(pdf, margen, yt, ancho_util, alto_totales, RGB_SECUNDARIO)
            pdf.set_xy(margen + 6, yt + 3)
            mo_txt = f'MANO DE OBRA: ${mano_obra:.2f}'
            if getattr(orden, 'mano_obra_desc', None):
                mo_txt += f'  ({orden.mano_obra_desc})'
            self._texto(pdf, mo_txt, 8, color=BLANCO)
            pdf.set_xy(margen + 6, yt + 10)
            self._texto(pdf, 'TOTAL A PAGAR', 9, bold=True, color=BLANCO)
            pdf.set_xy(margen + 6, yt + 16)
            self._texto(pdf, f'${costo_total:.2f}', 15, bold=True, color=BLANCO)
            pdf.set_y(yt + alto_totales + 6)

            # === OBSERVACIONES ===
            if getattr(orden, 'notas_cliente', None):
                RGB_NOTAS_BG = (255, 249, 230)
                RGB_NOTAS_BORDE = (243, 156, 18)
                y_notas = pdf.get_y()
                # Altura aproximada según líneas del texto
                n_lineas = max(1, len(str(orden.notas_cliente)) // 95 + str(orden.notas_cliente).count('\n') + 1)
                h_notas = 10 + 4.2 * n_lineas
                self._rect(pdf, margen, y_notas, ancho_util, min(h_notas, 40), RGB_NOTAS_BG)
                self._rect(pdf, margen, y_notas, 1.4, min(h_notas, 40), RGB_NOTAS_BORDE)
                pdf.set_xy(margen + 5, y_notas + 2.5)
                self._texto(pdf, 'OBSERVACIONES', 8.5, bold=True, color=RGB_TEXTO)
                pdf.set_xy(margen + 5, pdf.get_y() + 0.5)
                pdf.set_font(self._fuente(pdf), '', 8.5)
                pdf.set_text_color(*RGB_TEXTO)
                pdf.multi_cell(ancho_util - 10, 4.2,
                               self._sanitizar(str(orden.notas_cliente), self._fuente(pdf)),
                               new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_y(max(pdf.get_y(), y_notas + min(h_notas, 40)) + 6)

            # === FIRMAS ===
            if pdf.get_y() > 215:
                pdf.add_page()
            pdf.ln(12)
            y_firma = pdf.get_y()
            ancho_col = ancho_util / 2
            for j, etiqueta in enumerate(['FIRMA DEL TÉCNICO', 'FIRMA DEL CLIENTE']):
                fx = margen + j * ancho_col
                pdf.set_draw_color(*RGB_TEXTO)
                pdf.line(fx + 8, y_firma, fx + ancho_col - 16, y_firma)
                pdf.set_xy(fx + 8, y_firma + 1.5)
                self._texto(pdf, etiqueta, 8, bold=True, color=RGB_TEXTO)
                pdf.set_xy(fx + 8, pdf.get_y())
                sublabel = 'Responsable del servicio' if j == 0 else 'Conformidad del servicio'
                self._texto(pdf, sublabel, 7, color=RGB_TEXTO_CLARO)
            pdf.ln(10)

            # === PIE DOCUMENTO ===
            nit = config.get('nit_taller', '')
            self._texto(pdf,
                        'Gracias por confiar en nuestros servicios. '
                        'Este documento es su comprobante de reparación.',
                        8, color=RGB_TEXTO_CLARO, align='C')
            if nit:
                self._texto(pdf, f'NIT/CI: {nit}', 7.5, bold=True, color=RGB_TEXTO, align='C')

            return self._finalizar(pdf)
        except PdfServiceError:
            return None
        except Exception:
            logger.exception('Error inesperado generando el recibo de la orden %s',
                             getattr(orden, 'numero_orden', '?'))
            return None

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def _finalizar(self, pdf: SGMFPDF) -> io.BytesIO:
        """Serializa el documento a un buffer binario posicionado al inicio."""
        datos = pdf.output()
        buffer = io.BytesIO(bytes(datos))
        buffer.seek(0)
        return buffer

    @staticmethod
    def truncar(texto: Optional[str], largo: int) -> str:
        """Recorta un texto a ``largo`` caracteres (evita desbordes de celda)."""
        texto = '' if texto is None else str(texto)
        return texto[:largo]

    @staticmethod
    def limpiar_nombre_archivo(nombre: str) -> str:
        """Normaliza cadenas para usarlas como nombre de archivo seguro."""
        limpio = ''.join(c for c in nombre if c.isalnum() or c in ' -_').strip()
        return limpio.replace(' ', '_') or 'documento'


# Instancia única compartida por toda la aplicación
pdf_service = PdfService()
