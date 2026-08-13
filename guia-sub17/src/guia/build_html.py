"""Motor_HTML: sitio estático de la Guia_Extensa (`build_html.py`).

Escribe un **HTML por capítulo** más un `index.html` y un `estilo.css`,
consumiendo el mismo `Modelo_Paginas` (lista de `PaginaRender`) que produce el
paginador y que consume el Motor_PDF (`build_pdf.py`). Ningún motor conoce el
catálogo: `build_html` solo sabe leer `PaginaRender`, `ElementoRender` y
`Anotacion` (ver `layout.py`).

A diferencia del PDF, el HTML **reflowea**: no respeta los saltos de página del
paginador, sino que agrupa las páginas por capítulo y concatena sus elementos
en un solo documento de una columna. Lo que sí se conserva es el **conjunto de
capítulos** (ids de bloque de contenido), de modo que el validador puede
comparar la paridad entre los dos artefactos (ver `ids_capitulos`).

Decisiones (ver design.md, "Estrategia de HTML"):

* **Estático, sin JavaScript** (Req 2.4): navegación con `<a>`, tablas con
  `<table>`. No se emite ningún `<script>` ni atributo de evento `on*`.
* **Responsive a 360 px** (Req 2.5): `<meta name="viewport">` con
  `width=device-width`, tipografía base `clamp(16px, 4.2vw, 19px)`, una sola
  columna, `max-width: 44rem`, sin anchos fijos en píxeles. Las tablas anchas
  se envuelven en `<div class="scroll-x">` con `overflow-x:auto`.
* **SVG inline** (Req 9.10): cada diagrama se emite con `viewBox` y
  `role="img"` vía `viz.render_svg`, sin dimensiones absolutas. Los códigos QR
  se emiten como **SVG de rectángulos** (un `<rect>` por módulo oscuro), no como
  PNG.
* **Escapado**: todo texto del catálogo pasa por `html.escape(texto,
  quote=True)`. Los archivos se escriben en UTF-8 con
  `open(ruta, 'w', encoding='utf-8', newline='\\n')`.
* **Descarga del PDF** (Req 2.7): banda al inicio de `index.html` y de cada
  capítulo con un enlace `download` al PDF y su tamaño en MB obtenido con
  `os.stat(...).st_size`. Si el PDF aún no existe, la banda se emite sin el
  tamaño (el build del PDF puede no haber corrido todavía).
* **Impresión**: `@media print` oculta la navegación y la banda de descarga.

Sin `assert` en producción y sin concatenación de strings en bucle: los
fragmentos se acumulan en `list[str]` y se unen con `''.join(...)`.
"""

from __future__ import annotations

import html
import os
import re

from . import paleta, viz
from .layout import PaginaRender, TipoElemento

__all__ = [
    "PDF_NOMBRE",
    "PDF_HREF",
    "META_VIEWPORT",
    "META_VIEWPORT_SITIO",
    "nombre_archivo_capitulo",
    "ids_capitulos",
    "estilo_css",
    "documento_a_html",
    "escribir_html",
]


# --------------------------------------------------------------------------- #
# Constantes de salida
# --------------------------------------------------------------------------- #

#: Nombre del artefacto PDF principal (ver design.md, "Estructura de carpetas").
PDF_NOMBRE: str = "Guia_Extensa_Sub17.pdf"

#: Ruta relativa por defecto desde `dist/web/*.html` hacia el PDF (un nivel
#: arriba de la carpeta del sitio).
PDF_HREF: str = "../" + PDF_NOMBRE

# Tema CLARO de alto contraste, reservado al bloque `@media print` (el PDF y la
# impresión de la web usan tinta oscura sobre fondo claro, Req 9.9).
_ROSA: str = paleta.ROSA
_NEGRO: str = "#111111"
_FONDO: str = paleta.FONDO
_GRIS: str = "#5A5A5A"
_ROSA_SUAVE: str = "#F3D9E6"

# Tema WEB oscuro (glass / futurista minimalista) para la pantalla.
_WEB_FONDO: str = paleta.WEB_FONDO
_WEB_SUPERFICIE: str = paleta.WEB_SUPERFICIE
_WEB_BORDE: str = paleta.WEB_BORDE
_WEB_MAGENTA: str = paleta.WEB_MAGENTA
_WEB_CORAL: str = paleta.WEB_CORAL
_WEB_TEXTO: str = paleta.WEB_TEXTO
_WEB_TEXTO_ATENUADO: str = paleta.WEB_TEXTO_ATENUADO

# Neones de la direccion de arte futurista (tarea 33.4). Se AÑADEN al tema
# oscuro; no sustituyen al magenta ni al coral, que siguen siendo el acento
# principal de titulos y botones.
_WEB_CIAN: str = paleta.WEB_CIAN
_WEB_VIOLETA: str = paleta.WEB_VIOLETA
_WEB_VERDE: str = paleta.WEB_VERDE

# Tokens del visor 3D del hero (tarea 34.2/34.3). Se AÑADEN: `WEB_FONDO` sigue
# valiendo exactamente `#0A0A0F` (hay pruebas que afirman esa cadena), y el tono
# más hondo del hero entra como token propio.
_WEB_AZUL: str = paleta.WEB_AZUL_CLARO
_WEB_FONDO_PROFUNDO: str = paleta.WEB_FONDO_PROFUNDO

#: Contenido EXACTO del `<meta name="viewport">` de todos los destinos web.
#: `maximum-scale=5` permite ampliar hasta cinco veces; nunca se escribe
#: `user-scalable=no`, que bloquearía el zoom y es una falta de accesibilidad.
META_VIEWPORT: str = "width=device-width, initial-scale=1, maximum-scale=5"

#: Contenido EXACTO del `<meta name="viewport">` del **Target_Web** y solo de el
#: (criterio 15.11). `viewport-fit=cover` es lo que deja al relleno de
#: `env(safe-area-inset-*)` alcanzar la muesca y la barra de gestos del telefono.
#:
#: Se AÑADE en vez de tocar `META_VIEWPORT`, que sigue sirviendo a las paginas de
#: capitulo y a la publicacion sin cambiar un byte. Quitar `maximum-scale` no
#: bloquea el zoom: lo amplia, porque el navegador deja de tener techo. Nunca se
#: escribe `user-scalable=no`.
META_VIEWPORT_SITIO: str = "width=device-width, initial-scale=1, viewport-fit=cover"

#: Lado minimo de un objetivo tactil, en pixeles CSS (Req 14.4).
LADO_TOQUE_PX: int = 44

#: Medida maxima de linea de lectura (caracteres por linea).
MEDIDA_MAX_CH: int = 65

#: Alto de la barra superior del overlay del Visor_Ampliado, en pixeles CSS. Es
#: fija: el titulo y el cierre no se mueven al desplazar el cuerpo.
ALTO_BARRA_MODAL: int = 56

#: Alto maximo del contenedor de la ilustracion dentro del overlay. Se expresa en
#: `svh` (small viewport height) a proposito: es la altura de ventana **con** la
#: barra de direcciones desplegada, asi que en el navegador incrustado de Android
#: no cambia a media lectura, que es justo lo que el criterio 15.10 persigue.
ALTO_MAX_LIENZO: str = "60svh"

#: Desenfoque del velo del overlay.
DESENFOQUE_MODAL: str = "8px"

#: Capa del overlay: por encima de la interfaz del hero (capa 3) y de la
#: navegacion `sticky`, que no declara `z-index`.
CAPA_MODAL: int = 999

#: Cuántos módulos de "zona de silencio" rodean el QR en su SVG.
_QR_MARGEN: int = 2


# --------------------------------------------------------------------------- #
# Utilidades de escapado y nombres de archivo
# --------------------------------------------------------------------------- #


def _esc(texto: object) -> str:
    """Escapa `texto` para insertarlo con seguridad en el HTML (comillas incl.)."""
    return html.escape("" if texto is None else str(texto), quote=True)


#: Aliases de segmentos para que los nombres de salida coincidan con el diseño
#: (p. ej. `cap20_pos_portera` -> `20-posiciones-portera.html`).
_ALIAS_SEGMENTO: dict[str, str] = {"pos": "posiciones"}

_RE_CAPITULO = re.compile(r"^cap0*(\d+)_(.+)$")


def _slug(texto: str) -> str:
    """Convierte `texto` en un slug con guiones (minúsculas, sin subrayados)."""
    limpio = texto.strip().lower().replace("_", "-").replace(" ", "-")
    limpio = re.sub(r"[^a-z0-9-]+", "", limpio)
    limpio = re.sub(r"-+", "-", limpio).strip("-")
    return limpio or "seccion"


def nombre_archivo_capitulo(capitulo_id: str) -> str:
    """Nombre del archivo HTML de un capítulo, con prefijo numérico y guiones.

    Convierte el id del módulo fuente (que lleva prefijo `cap` porque un módulo
    de Python no puede empezar por dígito) en una URL con guiones. Ejemplos:

        cap00_portada       -> 00-portada.html
        cap10_fundamentos   -> 10-fundamentos.html
        cap20_pos_portera   -> 20-posiciones-portera.html
        cap80_apendices     -> 80-apendices.html

    Si `capitulo_id` no sigue el patrón `capNN_*`, se degrada a un slug del id
    completo con sufijo `.html`, de modo que siempre produce un nombre válido.
    """
    m = _RE_CAPITULO.match(capitulo_id or "")
    if m is None:
        return f"{_slug(capitulo_id or 'seccion')}.html"
    numero = m.group(1)
    if len(numero) < 2:
        numero = numero.zfill(2)
    resto = m.group(2)
    segmentos = [_ALIAS_SEGMENTO.get(s, s) for s in resto.split("_") if s]
    cola = _slug("-".join(segmentos)) if segmentos else "seccion"
    return f"{numero}-{cola}.html"


# --------------------------------------------------------------------------- #
# Agrupado del Modelo_Paginas por capítulo (reflow)
# --------------------------------------------------------------------------- #


class _Capitulo:
    """Un capítulo reflowed: id, título, nombre de archivo y sus páginas."""

    __slots__ = ("id", "titulo", "archivo", "paginas")

    def __init__(self, capitulo_id: str, titulo: str) -> None:
        self.id: str = capitulo_id
        self.titulo: str = titulo
        self.archivo: str = nombre_archivo_capitulo(capitulo_id)
        self.paginas: list[PaginaRender] = []


def _agrupar_por_capitulo(paginas: list[PaginaRender]) -> list[_Capitulo]:
    """Agrupa las páginas por `capitulo_id` conservando el orden de aparición."""
    capitulos: list[_Capitulo] = []
    indice: dict[str, _Capitulo] = {}
    for pagina in paginas:
        cid = pagina.capitulo_id or ""
        cap = indice.get(cid)
        if cap is None:
            cap = _Capitulo(cid, pagina.capitulo_titulo or cid or "Sección")
            indice[cid] = cap
            capitulos.append(cap)
        elif not cap.titulo and pagina.capitulo_titulo:
            cap.titulo = pagina.capitulo_titulo
        cap.paginas.append(pagina)
    return capitulos


def ids_capitulos(paginas: list[PaginaRender]) -> tuple[str, ...]:
    """Ids de capítulo (bloques de contenido) en orden de aparición, sin repetir.

    El Motor_PDF y el Motor_HTML consumen el mismo `Modelo_Paginas`, así que
    este conjunto es idéntico entre ambos artefactos: es la base de la
    comprobación de **paridad de ids de bloque de contenido** del validador.
    """
    vistos: list[str] = []
    conjunto: set[str] = set()
    for pagina in paginas:
        cid = pagina.capitulo_id or ""
        if cid not in conjunto:
            conjunto.add(cid)
            vistos.append(cid)
    return tuple(vistos)


# --------------------------------------------------------------------------- #
# Render de elementos a HTML
# --------------------------------------------------------------------------- #


def _es_negrita(fuente: object) -> bool:
    return isinstance(fuente, str) and fuente.lower().endswith("bold")


def _render_texto(elem: object, partes: list[str]) -> None:
    """Texto/párrafo -> `<p>` (destacado si la fuente es negrita)."""
    datos = getattr(elem, "datos", None)
    texto = getattr(datos, "texto", None)
    if not texto:
        return
    tipo = getattr(elem, "tipo", None)
    clase = ""
    if tipo is TipoElemento.TEXTO and _es_negrita(getattr(datos, "fuente", "")):
        clase = ' class="destacado"'
    partes.append(f"<p{clase}>{_esc(texto)}</p>")


def _es_postura(spec: object) -> bool:
    """`True` si el spec es una ilustracion de tecnica (clase POSTURA).

    Se comprueba por el **valor** de la clase y no importando el `Enum`, para no
    acoplar el Motor_HTML al modulo de specs mas de lo que ya esta.
    """
    clase = getattr(spec, "clase", None)
    return str(getattr(clase, "value", clase) or "") == "postura"


def _render_diagrama(elem: object, partes: list[str]) -> None:
    """Diagrama -> SVG inline con `viewBox` y `role="img"` (vía `viz`).

    Las ilustraciones de tecnica (clase POSTURA) salen en `figure.ilustracion`
    con `data-postura="1"`, de modo que el CSS las trate como la zona visual
    principal y que su presencia sea contable de forma mecanica en el artefacto.
    El SVG que emite `viz` ya trae `viewBox`, `role="img"`, `<title>` y `<desc>`
    y **no** lleva dimensiones absolutas en la etiqueta de apertura.
    """
    datos = getattr(elem, "datos", None)
    spec = getattr(datos, "spec", None)
    if spec is None:
        return
    titulo = getattr(datos, "titulo", None)
    svg = viz.render_svg(spec)
    if _es_postura(spec):
        partes.append('<figure class="ilustracion" data-postura="1">')
    else:
        partes.append('<figure class="diagrama">')
    partes.append(svg)
    if titulo:
        partes.append(f"<figcaption>{_esc(titulo)}</figcaption>")
    partes.append("</figure>")


def _qr_a_svg(matriz: object, titulo: str) -> str:
    """Convierte una `MatrizQR` en un SVG de rectángulos (un `<rect>` por módulo).

    El SVG es responsive (sin `width`/`height` absolutos, `viewBox` en módulos)
    y accesible (`role="img"` + `<title>`). Rodea el patrón con una zona de
    silencio de `_QR_MARGEN` módulos para que sea legible por un lector.
    """
    lado = int(getattr(matriz, "lado", 0))
    if lado <= 0:
        return ""
    total = lado + 2 * _QR_MARGEN
    modulo = getattr(matriz, "modulo", None)
    partes: list[str] = []
    partes.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total} {total}" '
        f'style="width:100%;height:auto" role="img" '
        f'preserveAspectRatio="xMidYMid meet" class="qr">'
    )
    partes.append(f"<title>{_esc(titulo)}</title>")
    partes.append(
        f'<rect x="0" y="0" width="{total}" height="{total}" fill="#FFFFFF" />'
    )
    if callable(modulo):
        for fila in range(lado):
            y = fila + _QR_MARGEN
            for col in range(lado):
                if modulo(fila, col):
                    x = col + _QR_MARGEN
                    partes.append(
                        f'<rect x="{x}" y="{y}" width="1" height="1" '
                        f'fill="#111111" />'
                    )
    partes.append("</svg>")
    return "".join(partes)


def _render_qr(elem: object, partes: list[str]) -> None:
    """Código QR -> SVG de rectángulos con su enlace clicable."""
    datos = getattr(elem, "datos", None)
    url = getattr(datos, "url", None)
    matriz = getattr(datos, "matriz", None)
    if matriz is None and url:
        from . import qr

        matriz = qr.codificar(url)
    if matriz is None:
        return
    svg = _qr_a_svg(matriz, url or "Código QR")
    if not svg:
        return
    partes.append('<figure class="qr-figura">')
    partes.append(svg)
    if url:
        partes.append(
            f'<figcaption><a href="{_esc(url)}" target="_blank" '
            f'rel="noopener noreferrer">{_esc(url)}</a></figcaption>'
        )
    partes.append("</figure>")


def _render_linea(_elem: object, partes: list[str]) -> None:
    """Línea separadora -> `<hr>`."""
    partes.append("<hr>")


def _fila_tabla_html(datos: object, partes: list[str]) -> None:
    """Emite una fila `<tr>` con `<th>`/`<td>` según sea cabecera."""
    celdas = getattr(datos, "celdas", ())
    es_cabecera = bool(getattr(datos, "es_cabecera", False))
    etiqueta = "th" if es_cabecera else "td"
    partes.append("<tr>")
    for celda in celdas:
        partes.append(f"<{etiqueta}>{_esc(celda)}</{etiqueta}>")
    partes.append("</tr>")


def _render_tabla(filas: list[object], partes: list[str]) -> None:
    """Grupo de filas consecutivas -> una `<table>` dentro de `div.scroll-x`.

    Las filas marcadas como cabecera van en `<thead>`; el resto en `<tbody>`.
    El envoltorio `div.scroll-x` permite el desplazamiento horizontal en
    pantallas estrechas sin romper el flujo de una columna (Req 2.5).
    """
    if not filas:
        return
    partes.append('<div class="scroll-x">')
    partes.append("<table>")
    cabeceras = [f for f in filas if getattr(f, "es_cabecera", False)]
    cuerpo = [f for f in filas if not getattr(f, "es_cabecera", False)]
    if cabeceras:
        partes.append("<thead>")
        # La cabecera se repite en el PDF por página; en HTML basta una vez.
        _fila_tabla_html(cabeceras[0], partes)
        partes.append("</thead>")
    partes.append("<tbody>")
    for fila in cuerpo:
        _fila_tabla_html(fila, partes)
    partes.append("</tbody>")
    partes.append("</table>")
    partes.append("</div>")


def _render_elementos(cap: _Capitulo, partes: list[str]) -> None:
    """Renderiza en orden los elementos de todas las páginas de un capítulo.

    Agrupa filas de tabla consecutivas en una sola `<table>`; el resto de tipos
    se despachan uno a uno. Los tipos puramente decorativos del PDF (RECT de
    fondo) no aportan al HTML reflowed y se omiten.
    """
    buffer_tabla: list[object] = []

    def _vaciar_tabla() -> None:
        if buffer_tabla:
            _render_tabla(buffer_tabla, partes)
            buffer_tabla.clear()

    for pagina in cap.paginas:
        for elem in pagina.elementos:
            tipo = getattr(elem, "tipo", None)
            if tipo is TipoElemento.TABLA:
                buffer_tabla.append(getattr(elem, "datos", None))
                continue
            _vaciar_tabla()
            if tipo in (TipoElemento.TEXTO, TipoElemento.PARRAFO):
                _render_texto(elem, partes)
            elif tipo is TipoElemento.DIAGRAMA:
                _render_diagrama(elem, partes)
            elif tipo is TipoElemento.QR:
                _render_qr(elem, partes)
            elif tipo is TipoElemento.LINEA:
                _render_linea(elem, partes)
            # RECT y otros decorativos se omiten en el reflow HTML.
    _vaciar_tabla()


# --------------------------------------------------------------------------- #
# CSS y andamiaje del documento
# --------------------------------------------------------------------------- #


#: Las NUEVE reglas `:hover` de la Hoja_Estilo, tal cual, sin una coma de cambio.
#:
#: El criterio 15.13 exige que **toda** regla que use `:hover` viva dentro de
#: `@media (hover: hover)`, porque en un telefono la pseudoclase se dispara con
#: un toque y deja el estado pegado. La resolucion no reescribe ninguna: las
#: envuelve. Las pruebas vigentes afirman varias de estas cadenas con `assertIn`
#: (`.zona:hover,.zona:focus-within,.zona:active`,
#: `.chip:hover,.chip:focus-within,.chip:active` y
#: `.btn-video:hover,.btn-video:focus-visible,.btn-video:active`), y siguen
#: presentes literalmente dentro de la consulta.
_REGLAS_HOVER: tuple[str, ...] = (
    "a:hover{color:var(--azul-profundo);"
    "border-bottom-color:var(--azul-profundo);}",
    "figure:hover{transform:translateY(-2px);border-color:var(--azul-linea);}",
    "tbody tr:hover{background:var(--azul-cielo);}",
    "nav.sitio a:hover{color:var(--azul-profundo);background:var(--azul-cielo);}",
    ".descarga a:hover{color:var(--azul-linea);}",
    ".indice-capitulos a:hover{transform:translateY(-2px);"
    "border-color:var(--azul-linea);color:var(--azul-profundo);}",
    ".zona:hover,.zona:focus-within,.zona:active{"
    "transform:translateZ(18px) rotateX(1.2deg) rotateY(-1.2deg);"
    "border-color:var(--cian);box-shadow:var(--halo);}",
    ".chip:hover,.chip:focus-within,.chip:active{"
    "transform:translateZ(12px);border-color:var(--verde);}",
    ".btn-video:hover,.btn-video:focus-visible,.btn-video:active{"
    "transform:translateY(-2px);filter:brightness(1.08);"
    "color:var(--azul-profundo);}",
)


def _reglas_hover() -> str:
    """Las nueve reglas `:hover` concatenadas, para envolverlas en su consulta."""
    return "".join(_REGLAS_HOVER)


def _reglas_estado_tactil() -> str:
    """Los estados de toque y de teclado, en reglas propias FUERA de la consulta.

    Tres de las nueve reglas `:hover` llevan pegadas sus variantes
    `:focus-within`, `:focus-visible` y `:active`, que **si** existen en un
    telefono y con teclado. Envolverlas en `@media (hover: hover)` las apagaria en
    el dispositivo donde mas hacen falta, asi que se **duplican** aqui como reglas
    propias sin `:hover`: la cadena original sigue intacta dentro de la consulta y
    el estado sobrevive al toque.
    """
    return "".join(
        (
            ".zona:focus-within,.zona:active{"
            "transform:translateZ(18px) rotateX(1.2deg) rotateY(-1.2deg);"
            "border-color:var(--cian);box-shadow:var(--halo);}\n",
            ".chip:focus-within,.chip:active{"
            "transform:translateZ(12px);border-color:var(--verde);}\n",
            ".btn-video:focus-visible,.btn-video:active{"
            "transform:translateY(-2px);filter:brightness(1.08);"
            "color:var(--azul-profundo);}\n",
            "a:focus-visible,figure:focus-within,"
            "nav.sitio a:focus-visible,.descarga a:focus-visible,"
            ".indice-capitulos a:focus-visible{color:var(--azul-profundo);"
            "border-color:var(--azul-linea);}\n",
        )
    )


def estilo_css() -> str:
    """Devuelve el único `estilo.css` del sitio (también inlineado en cada página).

    Estética futurista minimalista: fondo casi negro, tarjetas tipo vidrio
    (`backdrop-filter: blur`) con borde fino de 1px, degradados magenta/coral en
    acentos y títulos, tipografía con stack del sistema (sin fuentes externas),
    números grandes y mucho espacio en blanco. Microanimaciones **solo CSS**
    (`transition`/`@keyframes`), desactivadas bajo
    `@media (prefers-reduced-motion: reduce)`.

    Cumple los requisitos responsive: tipografía `clamp(16px, 4.2vw, 19px)`, una
    sola columna, `max-width: 44rem`, sin anchos fijos en píxeles, tablas anchas
    con `overflow-x:auto`. El bloque `@media print` conmuta al tema CLARO de alto
    contraste (fondo `#FFF8FB`, tinta oscura) para imprimir.

    No emite `<script>`, ni atributos `on*`, ni `@import url(...)`, ni fuentes
    remotas: todo es estático y autónomo.
    """
    from . import diagramas_postura, mundo_hero, secciones_guia, vistas_figura

    partes: list[str] = []

    # ------------------------------------------------------------------ #
    # 1. Tokens: Paleta_Guia primero, tema oscuro conservado detras
    # ------------------------------------------------------------------ #
    #
    # Los SIETE tokens de la Paleta_Guia salen de `paleta.PALETA_GUIA`, que es la
    # unica fuente de verdad de sus valores (criterios 16.1 y 16.2). Los tokens
    # del tema oscuro NO se borran (criterio 16.17): siguen declarados aqui con su
    # valor exacto, `--azul` (`#7EC8FF`) queda restringido a las aristas, los
    # acentos y el halo del visor 3D (criterio 16.18) y `--fondo` /
    # `--fondo-profundo` quedan como fondo del hero en Modo_Oscuro.
    tokens_guia: str = "".join(
        f"{token}:{color};" for token, color in paleta.PALETA_GUIA.items()
    )
    partes.append(
        ":root{"
        + tokens_guia
        # Toda sombra de la Hoja_Estilo usa este color y ningun otro (16.14).
        + f"--sombra:{paleta.SOMBRA_GUIA};"
        + "--halo:0 0 0 1px var(--sombra);"
        + f"--fondo:{_WEB_FONDO};"
        f"--superficie:{_WEB_SUPERFICIE};"
        f"--borde:{_WEB_BORDE};"
        # Velo del overlay del Visor_Ampliado. Es un token de la Paleta_Guia y no
        # un color suelto: el `color-mix` que lo usa mezcla `--azul-profundo` con
        # transparente, asi que el velo nunca sale de los siete colores.
        "--fondo-modal:var(--azul-profundo);"
        f"--magenta:{_WEB_MAGENTA};"
        f"--coral:{_WEB_CORAL};"
        f"--texto:{_WEB_TEXTO};"
        f"--texto-atenuado:{_WEB_TEXTO_ATENUADO};"
        f"--cian:{_WEB_CIAN};"
        f"--violeta:{_WEB_VIOLETA};"
        f"--verde:{_WEB_VERDE};"
        f"--azul:{_WEB_AZUL};"
        f"--fondo-profundo:{_WEB_FONDO_PROFUNDO};"
        "--vidrio:rgba(11,44,77,0.04);"
        "--acento:linear-gradient(135deg,var(--rosa-acento),var(--coral-alerta));"
        "--linea:linear-gradient(90deg,var(--azul-linea),transparent);"
        "--radio:16px;"
        f"--toque:{LADO_TOQUE_PX}px;"
        f"--medida:{MEDIDA_MAX_CH}ch;"
        "--profundidad:1100px;"
        "}\n"
    )

    # Base y tipografía.
    partes.append("*{box-sizing:border-box;}\n")
    partes.append("html{-webkit-text-size-adjust:100%;}\n")
    # Sin scroll horizontal fantasma en Android (tarea 34.4). `overflow-x:hidden`
    # es la regla que exige el requisito; donde existe `clip` se prefiere, porque
    # `hidden` convierte el elemento en contenedor de scroll y puede romper el
    # `position:sticky` de la navegación.
    partes.append("html,body{overflow-x:hidden;}\n")
    partes.append("@supports (overflow:clip){html,body{overflow-x:clip;}}\n")
    # ------------------------------------------------------------------ #
    # 2. Tema claro de la Paleta_Guia (criterios 16.3 a 16.6)
    # ------------------------------------------------------------------ #
    #
    # Fondo de pagina en `--blanco-suave` y TODO el texto de cuerpo en
    # `--azul-profundo`: 12.6 : 1 de contraste, muy por encima del 4.5 que pide el
    # criterio 16.7. El relleno de los cuatro bordes de pantalla usa las cuatro
    # funciones `env(safe-area-inset-*)` (criterio 15.12) y el tamano de cuerpo es
    # `clamp(16px, 4.2vw, 19px)`, asi que nunca baja de 16 px (criterio 15.8).
    partes.append(
        "body{margin:0;background:var(--blanco-suave);color:var(--azul-profundo);"
        'font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;'
        "font-size:clamp(16px, 4.2vw, 19px);line-height:1.65;"
        "letter-spacing:0.01em;-webkit-font-smoothing:antialiased;"
        "padding-top:env(safe-area-inset-top);"
        "padding-right:env(safe-area-inset-right);"
        "padding-bottom:env(safe-area-inset-bottom);"
        "padding-left:env(safe-area-inset-left);}\n"
    )
    partes.append("main{max-width:44rem;margin:0 auto;padding:2.5rem 1.25rem 5rem;}\n")
    partes.append("img,svg{max-width:100%;height:auto;}\n")
    # Texto de cuerpo: una sola declaracion para los elementos de lectura, de modo
    # que ningun descendiente herede otro color (criterio 16.3).
    partes.append(
        "p,li,dd,dt,td,th,figcaption,blockquote,label,summary{"
        "color:var(--azul-profundo);}\n"
    )

    # ------------------------------------------------------------------ #
    # 3. Celular primero: el Ancho_Base manda (Requisito 15)
    # ------------------------------------------------------------------ #
    #
    # Todo lo de este bloque es la BASE, sin ninguna consulta de medios: los
    # cambios de pantalla ancha viven mas abajo, dentro de `min-width` (15.1).
    # Ningun `width` ni `min-width` en pixeles pasa de 360; los unicos valores en
    # pixeles son los 44 del lado minimo de las Zona_Tactil y los 8 de su
    # separacion (15.2, 15.6 y 15.7).
    partes.append("section,main,article,aside,header,footer{max-width:100%;min-width:0;}\n")
    partes.append("input,select,textarea,button{font-size:16px;}\n")
    zonas: str = ",".join(
        (
            f".{secciones_guia.CLASE_TACTIL}",
            "nav.sitio a",
            ".btn-solid",
            ".btn-outline",
            ".btn-video",
            ".descarga a",
            ".indice-capitulos a",
            ".chip",
            f".{secciones_guia.CLASE_AMPLIAR}",
            f".{secciones_guia.CLASE_CERRAR}",
        )
    )
    partes.append(
        f"{zonas}{{min-height:{LADO_TOQUE_PX}px;min-width:{LADO_TOQUE_PX}px;"
        "display:inline-flex;align-items:center;}\n"
    )
    contenedores: str = ",".join(
        (
            ".acciones",
            "nav.sitio",
            ".indice-capitulos",
            ".filtros",
            ".descargas",
            ".chips",
            ".hero-acciones",
            f".{secciones_guia.CLASE_INDICE}",
        )
    )
    partes.append(f"{contenedores}{{display:flex;flex-wrap:wrap;gap:8px;}}\n")
    # Alturas relativas a la ventana SIEMPRE en `dvh`, nunca en `vh` (15.10): en
    # Android la barra de direcciones cambia `vh` a media lectura.
    partes.append(".hero{min-height:72dvh;}\n")

    # Títulos con degradado magenta/coral (números y títulos grandes).
    # Titulos en tinta solida con el subrayado en `--rosa-acento` (criterio 16.9).
    # El rosa es el filete, nunca la letra: sobre `--blanco-suave` da 3.12 : 1, que
    # cumple el 3 : 1 de elemento grafico pero no el 4.5 : 1 de texto (16.10).
    partes.append(
        "h1{font-size:clamp(2rem, 9vw, 3.25rem);line-height:1.05;"
        "font-weight:800;letter-spacing:-0.03em;margin:0 0 1.75rem;"
        "color:var(--azul-profundo);}\n"
    )
    partes.append(
        'h1::after{content:"";display:block;width:3.5rem;height:4px;'
        "margin-top:0.6rem;border-radius:999px;background:var(--rosa-acento);}\n"
    )
    partes.append(
        "h2{font-size:clamp(1.4rem, 5.5vw, 2rem);font-weight:700;"
        "letter-spacing:-0.01em;margin:3rem 0 1rem;color:var(--azul-profundo);}\n"
    )
    partes.append(
        'h2::before{content:"";display:block;width:2.75rem;height:3px;'
        "margin-bottom:0.75rem;border-radius:999px;background:var(--rosa-acento);}\n"
    )
    partes.append("h3,h4{color:var(--azul-profundo);}\n")
    partes.append("p{margin:0 0 1.15rem;}\n")
    partes.append(
        "p.destacado{font-weight:700;font-size:1.12em;color:var(--azul-profundo);}\n"
    )
    partes.append("strong,b{color:var(--azul-profundo);}\n")

    # Enlaces con microtransición. `--azul-linea` sobre los tres fondos claros
    # llega a 4.5 : 1, asi que sirve como texto de cuerpo (criterio 16.7).
    #
    # ARRASTRE ANOTADO Y SIN TOCAR: el par `--azul-linea` (`#1E6FA8`) sobre
    # `--azul-cielo` (`#DCEEFF`) da **4.549 : 1**, con un margen de 0.049 sobre el
    # umbral de 4.5. Los dos valores estan congelados por el Requisito 16 y por las
    # pruebas que afirman sus literales, y la Propiedad 34 los mide con el umbral
    # tal cual. Ese par no admite ningun retoque de tono: aclarar el azul linea o
    # oscurecer el cielo lo tira por debajo de 4.5. Si algun dia hay que darle
    # aire, se cambia el REQUISITO, no el CSS.
    partes.append(
        "a{color:var(--azul-linea);text-decoration:none;"
        "border-bottom:1px solid transparent;"
        "transition:color .2s ease,border-color .2s ease;}\n"
    )

    # Tarjetas de vidrio (figuras: diagramas y QR).
    partes.append(
        "figure{margin:1.75rem 0;padding:1.1rem;border-radius:var(--radio);"
        "background:var(--azul-cielo);border:1px solid var(--borde);"
        "backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);"
        "box-shadow:var(--halo);"
        "transition:transform .25s ease,border-color .25s ease;}\n"
    )
    partes.append(
        "figure.diagrama svg,figure.qr-figura svg.qr{max-width:100%;height:auto;}\n"
    )
    partes.append("figure.qr-figura{max-width:16rem;}\n")
    partes.append(
        "figcaption{color:var(--azul-profundo);font-size:0.85em;"
        "word-break:break-all;margin-top:0.65rem;}\n"
    )
    partes.append(
        "hr{border:0;height:1px;margin:2.5rem 0;background:var(--borde);}\n"
    )

    # Tablas anchas en tarjeta clara con scroll horizontal.
    partes.append(
        ".scroll-x{overflow-x:auto;-webkit-overflow-scrolling:touch;"
        "margin:1.75rem 0;border-radius:var(--radio);background:var(--blanco-suave);"
        "border:1px solid var(--borde);box-shadow:var(--halo);"
        "backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);}\n"
    )
    partes.append("table{border-collapse:collapse;min-width:100%;}\n")
    partes.append(
        "th,td{border-bottom:1px solid var(--borde);"
        "padding:0.8rem 1rem;text-align:left;}\n"
    )
    partes.append(
        "th{background:var(--azul-medio);color:var(--azul-profundo);font-weight:700;"
        "text-transform:uppercase;font-size:0.78em;letter-spacing:0.06em;}\n"
    )
    partes.append("td{font-variant-numeric:tabular-nums;}\n")
    partes.append("tbody tr{transition:background .2s ease;}\n")

    # Navegación tipo "pill" anclada ABAJO en celular (criterio 15.20): siempre
    # `position:sticky`, jamas `position:fixed`, que en el navegador incrustado de
    # Android pelea con el desplazamiento. El relleno inferior suma
    # `env(safe-area-inset-bottom)` para librar la barra de gestos.
    partes.append(
        "nav.sitio{position:sticky;bottom:0;top:auto;z-index:10;display:flex;"
        "flex-wrap:wrap;gap:8px;padding:0.5rem 0.75rem;"
        "padding-bottom:calc(8px + env(safe-area-inset-bottom));"
        "background:var(--azul-cielo);"
        "backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);"
        "border-top:1px solid var(--borde);}\n"
    )
    partes.append(
        "nav.sitio a{color:var(--azul-profundo);padding:0.5rem 0.85rem;"
        "border-radius:999px;text-decoration:none;font-size:0.9rem;"
        "border-bottom:0;transition:color .2s ease,background .2s ease;}\n"
    )

    # Banda de descarga sobre fondo de la Paleta_Guia.
    partes.append(
        ".descarga{display:flex;align-items:center;gap:8px;flex-wrap:wrap;"
        "margin:0;padding:1rem 1.25rem;color:var(--azul-profundo);"
        "background:var(--azul-medio);}\n"
    )
    partes.append(
        ".descarga a{color:var(--azul-profundo);font-weight:700;border-bottom:0;}\n"
    )
    partes.append(".peso{opacity:0.85;font-size:0.9em;}\n")

    # Índice de capítulos como tarjetas de vidrio.
    partes.append(
        ".indice-capitulos{list-style:none;padding:0;margin:1.75rem 0;"
        "display:grid;gap:0.75rem;}\n"
    )
    partes.append(".indice-capitulos li{margin:0;}\n")
    partes.append(
        ".indice-capitulos a{display:block;padding:1.1rem 1.25rem;"
        "border-radius:var(--radio);background:var(--blanco-suave);"
        "border:1px solid var(--borde);box-shadow:var(--halo);"
        "backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);"
        "color:var(--azul-profundo);font-weight:600;"
        "transition:transform .2s ease,border-color .2s ease,color .2s ease;}\n"
    )

    # ------------------------------------------------------------------ #
    # Direccion de arte futurista y composicion editorial (tarea 33.4)
    # ------------------------------------------------------------------ #
    #
    # Profundidad SIMULADA solo con CSS (`perspective`, `transform-style`,
    # `rotateX/rotateY`, `translateZ`) y capas de sombra de color: cero recursos
    # externos, cero imagenes. Todo efecto tiene su equivalente tactil
    # (`:focus-visible` / `:active`) y muere bajo `prefers-reduced-motion`.

    # Capas de fondo: dos halos muy tenues (violeta y cian) sobre el fondo
    # oscuro profundo. Nunca negro absoluto y sin tapar el texto.
    partes.append(
        "body{background-image:"
        "radial-gradient(60rem 30rem at 15% -10%,var(--azul-cielo),transparent),"
        "radial-gradient(50rem 26rem at 95% 8%,var(--azul-medio),transparent);"
        "background-attachment:scroll;background-repeat:no-repeat;}\n"
    )

    # Medida de lectura: nunca mas de ~65 caracteres por linea.
    partes.append("p,li,dd,figcaption{max-width:var(--medida);}\n")

    # Foco visible en todo elemento enfocable (navegacion con teclado).
    partes.append(
        "a:focus-visible,button:focus-visible,input:focus-visible,"
        "select:focus-visible,summary:focus-visible,.zona:focus-visible{"
        "outline:2px solid var(--cian);outline-offset:3px;border-radius:6px;}\n"
    )

    # Objetivos tactiles de 44px como minimo (Req 14.4).
    partes.append(
        "nav.sitio a,.descarga a,.chip,.btn-video,.indice-capitulos a{"
        "min-height:var(--toque);display:inline-flex;align-items:center;}\n"
    )

    # Escena con perspectiva: las tarjetas de zona viven en 3D simulado.
    partes.append(
        ".ficha{perspective:var(--profundidad);margin:3.5rem 0 0;"
        "padding-top:1.5rem;border-top:1px solid var(--borde);}\n"
    )
    partes.append(
        ".zona{position:relative;transform-style:preserve-3d;"
        "border:1px solid var(--borde);border-radius:var(--radio);"
        "background:var(--blanco-suave);padding:1.15rem 1.25rem;margin:0 0 1rem;"
        "backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);"
        "transition:transform .3s ease,border-color .3s ease,box-shadow .3s ease;}\n"
    )
    # Linea fina tipo interfaz deportiva sobre cada zona.
    partes.append(
        '.zona::before{content:"";position:absolute;left:1.25rem;right:1.25rem;'
        "top:0;height:1px;background:var(--linea);}\n"
    )
    partes.append(
        ".zona-etiqueta{margin:0 0 .5rem;font-size:0.72em;font-weight:700;"
        "letter-spacing:0.16em;text-transform:uppercase;color:var(--azul-linea);}\n"
    )
    partes.append(
        ".zona h3{margin:0 0 .75rem;font-size:1.05em;letter-spacing:0.01em;"
        "color:var(--azul-profundo);}\n"
    )

    # Encabezado de ficha: numero grande en capa propia, sin cuadricula de
    # tarjetas identicas (composicion editorial, no dashboard).
    partes.append(
        ".zona-encabezado{display:grid;grid-template-columns:auto minmax(0,1fr);"
        "gap:0 1.25rem;align-items:start;background:transparent;border:0;"
        "backdrop-filter:none;-webkit-backdrop-filter:none;padding:0;}\n"
    )
    partes.append(".zona-encabezado::before{display:none;}\n")
    # El numero de ficha es un icono de logro tipografico de 2.4 rem o mas, asi que
    # el rosa cumple el 3 : 1 que le corresponde (criterios 16.9 y 16.10).
    partes.append(
        ".numero-ficha{grid-row:span 3;font-size:clamp(2.4rem,9vw,4rem);"
        "font-weight:800;line-height:0.9;letter-spacing:-0.04em;"
        "color:var(--rosa-acento);transform:translateZ(30px);}\n"
    )
    partes.append(
        ".meta-ficha{margin:0 0 .35rem;display:flex;flex-wrap:wrap;gap:8px;"
        "font-size:0.78em;letter-spacing:0.12em;text-transform:uppercase;"
        "color:var(--azul-profundo);}\n"
    )
    partes.append(
        ".meta-ficha span{border:1px solid var(--borde);border-radius:999px;"
        "padding:.15rem .7rem;}\n"
    )
    partes.append(
        ".objetivo{font-size:1.05em;color:var(--azul-profundo);"
        "margin:.35rem 0 .6rem;}\n"
    )

    # Zona visual: la ilustracion manda, ocupa el ancho y se levanta en Z.
    partes.append(
        ".zona-visual{padding:1rem;background:var(--azul-cielo);"
        "border-color:var(--violeta);}\n"
    )
    partes.append(
        "figure.ilustracion{margin:0 0 1rem;padding:.75rem;"
        "border:1px solid var(--cian);border-radius:var(--radio);"
        "background:var(--blanco-suave);transform:translateZ(24px);}\n"
    )
    partes.append("figure.ilustracion svg{width:100%;height:auto;}\n")
    partes.append(
        "figure.ilustracion figcaption{color:var(--azul-profundo);opacity:.9;}\n"
    )

    # Pasos numerados: un paso por linea, con su numero en capa cian.
    partes.append(
        ".pasos{list-style:none;counter-reset:paso;padding:0;margin:0;}\n"
    )
    partes.append(
        ".pasos li{counter-increment:paso;position:relative;"
        "padding:0 0 .85rem 2.4rem;}\n"
    )
    # Numeracion de pasos en `--rosa-acento` (criterio 16.9). El contenedor va
    # sobre `--blanco-suave` y NO sobre `--azul-cielo`: ahi el rosa da 2.7 : 1 y
    # sobre blanco suave 3.12 : 1, que es lo que cumple el 3 : 1 de elemento
    # grafico del criterio 16.8. El arrastre se cierra cambiando el FONDO, no el
    # rosa, que esta congelado por el criterio 16.1.
    partes.append(".pasos{background:var(--blanco-suave);}\n")
    partes.append(
        '.pasos li::before{content:counter(paso);position:absolute;left:0;top:0;'
        "min-width:1.7rem;height:1.7rem;display:inline-flex;align-items:center;"
        "justify-content:center;border-radius:999px;font-size:.8rem;"
        "font-weight:700;color:var(--rosa-acento);"
        "background:var(--blanco-suave);border:2px solid var(--rosa-acento);}\n"
    )

    # Listas de puntos clave y errores: el significado nunca va solo por color,
    # cada item lleva su rotulo de texto.
    partes.append(".lista-zona{list-style:none;padding:0;margin:0;}\n")
    partes.append(
        ".lista-zona li{padding:0 0 .6rem 1.1rem;position:relative;}\n"
    )
    partes.append(
        '.lista-zona li::before{content:"";position:absolute;left:0;top:.62em;'
        "width:.42rem;height:.42rem;border-radius:2px;background:var(--verde);}\n"
    )
    partes.append(
        ".zona-errores .lista-zona li::before{background:var(--coral-alerta);}\n"
    )
    # Texto de error en `--coral-alerta` SOLO sobre `--blanco-suave`: ahi da
    # 4.7 : 1 y cumple el 4.5 de texto de cuerpo (criterios 16.12 y 16.13).
    partes.append(
        ".marca-error{font-weight:700;color:var(--coral-alerta);"
        "background:var(--blanco-suave);"
        "text-transform:uppercase;font-size:.72em;letter-spacing:.12em;"
        "margin-right:.4rem;}\n"
    )
    partes.append(
        ".marca-correccion{font-weight:700;color:var(--azul-linea);"
        "text-transform:uppercase;font-size:.72em;letter-spacing:.12em;"
        "margin-right:.4rem;}\n"
    )

    # Chips grandes de dosis, progresion y medicion (tactiles en celular).
    partes.append(
        ".chips{list-style:none;padding:0;margin:0;display:flex;"
        "flex-wrap:wrap;gap:8px;}\n"
    )
    partes.append(
        ".chip{flex:1 1 9rem;min-height:var(--toque);display:flex;"
        "flex-direction:column;justify-content:center;gap:.15rem;"
        "padding:.6rem .9rem;border:1px solid var(--borde);"
        "border-radius:var(--radio);background:var(--blanco-suave);"
        "transform-style:preserve-3d;"
        "transition:transform .25s ease,border-color .25s ease;}\n"
    )
    partes.append(
        ".chip b{font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;"
        "color:var(--azul-profundo);}\n"
    )
    partes.append(".chip span{font-size:.95rem;color:var(--azul-profundo);}\n")
    partes.append(
        ".zona-medicion .chip b,.zona-progresion .chip b{color:var(--azul-linea);}\n"
    )
    partes.append("dl.datos{margin:0;}\n")
    partes.append(
        "dl.datos dt{font-size:.72rem;letter-spacing:.14em;"
        "text-transform:uppercase;color:var(--azul-linea);margin-top:.5rem;}\n"
    )
    partes.append("dl.datos dd{margin:.15rem 0 .5rem;}\n")

    # Zona de video: QR visible y su enlace legible debajo (nada tras hover).
    partes.append(
        ".zona-video{display:grid;gap:1rem;"
        "grid-template-columns:minmax(0,1fr);}\n"
    )
    partes.append(
        ".btn-video{padding:.7rem 1.1rem;border-radius:999px;font-weight:700;"
        "color:var(--azul-profundo);background:var(--azul-cielo);"
        "border:1px solid var(--azul-linea);"
        "transition:transform .2s ease,filter .2s ease;}\n"
    )
    partes.append(".enlace-visible{word-break:break-all;font-size:.82em;}\n")
    # Botones solidos y de contorno de la cabecera del sitio.
    partes.append(
        ".btn-solid{padding:.7rem 1.1rem;border-radius:999px;font-weight:700;"
        "color:var(--azul-profundo);background:var(--azul-medio);"
        "border:1px solid var(--azul-linea);border-bottom:1px solid var(--azul-linea);}\n"
    )
    partes.append(
        ".btn-outline{padding:.7rem 1.1rem;border-radius:999px;font-weight:700;"
        "color:var(--azul-profundo);background:var(--blanco-suave);"
        "border:1px solid var(--azul-linea);border-bottom:1px solid var(--azul-linea);}\n"
    )

    # ------------------------------------------------------------------ #
    # 4. Bloque de los Diagrama_Postura (criterios 4.5 a 4.7 y 15.3)
    # ------------------------------------------------------------------ #
    #
    # El bloque lo emite `diagramas_postura.bloque_css()`, que es su dueno: aqui
    # solo se concatena en su sitio de la cascada y se le anaden los colores de la
    # Paleta_Guia, que son responsabilidad del tema.
    partes.append(diagramas_postura.bloque_css())
    partes.append("\n")
    partes.append(
        f".{diagramas_postura.CLASE_BLOQUE}{{background:var(--blanco-suave);}}\n"
    )
    partes.append(
        f".{diagramas_postura.CLASE_MARCO}{{background:var(--azul-cielo);"
        "box-shadow:var(--halo);}\n"
    )
    # ARRASTRE QUE SE CIERRA AQUI: el contenedor de la lista de pasos va sobre
    # `--blanco-suave` y NO sobre `--azul-cielo`. El marcador `--rosa-acento` da
    # 2.7 : 1 sobre cielo y 3.12 : 1 sobre blanco suave, que es lo que cumple el
    # 3 : 1 de elemento grafico del criterio 16.8. El rosa esta congelado por el
    # criterio 16.1: lo que cambia es el fondo.
    partes.append(
        f".{diagramas_postura.CLASE_PASOS},.{diagramas_postura.CLASE_FASES}"
        "{background:var(--blanco-suave);}\n"
    )
    partes.append(
        f".{diagramas_postura.CLASE_PASOS} li::marker,"
        f".{diagramas_postura.CLASE_FASES} li::marker"
        "{color:var(--rosa-acento);font-weight:700;}\n"
    )
    # Texto de error en `--coral-alerta` sobre `--blanco-suave`: 4.7 : 1, que es lo
    # unico que cumple el 4.5 de texto de cuerpo (criterios 16.12 y 16.13).
    partes.append(
        f".{diagramas_postura.CLASE_ERROR}{{color:var(--coral-alerta);"
        "background:var(--blanco-suave);}\n"
    )
    partes.append(
        f".{diagramas_postura.CLASE_CREDITO}{{color:var(--azul-profundo);}}\n"
    )

    # ------------------------------------------------------------------ #
    # Hero con visor 3D y glassmorphism (tarea 34.3)
    # ------------------------------------------------------------------ #
    #
    # El modelo va DETRÁS de la interfaz por `z-index` (nunca con
    # `position:fixed`, que en el WebView de Android pelea con el scroll): capa 0
    # el visor, capa 1 el velo de oscurecimiento que garantiza el contraste del
    # texto, capa 2 la interfaz de vidrio y capa 3 un borde de neón inerte.
    #
    # En el sitio de un archivo la capa 0 es un `<canvas>` que el visor de JS
    # anima. En las páginas por capítulo es el MISMO dibujo pero en SVG estático,
    # movido solo con CSS: ahí no puede haber JavaScript (Req 2.4).
    # Degradado vertical de `--azul-cielo` arriba a `--azul-medio` abajo
    # (criterio 6.1). El azul saturado `#7EC8FF` queda fuera: no pertenece a la
    # Paleta_Guia y el criterio 16.18 lo restringe a las aristas y al halo del
    # visor 3D.
    partes.append(
        ".hero{position:relative;isolation:isolate;overflow:hidden;"
        "margin:0 0 2.25rem;max-width:100%;"
        "border-radius:calc(var(--radio) + 6px);"
        "border:1px solid var(--cian);"
        "background:linear-gradient(180deg,var(--azul-cielo),var(--azul-medio));"
        "box-shadow:var(--halo);}\n"
    )
    partes.append(
        ".hero-visor{position:absolute;inset:0;z-index:0;overflow:hidden;"
        "perspective:var(--profundidad);transform-style:preserve-3d;"
        "touch-action:pan-y pinch-zoom;}\n"
    )
    partes.append(
        ".hero-lienzo{position:absolute;inset:0;display:block;width:100%;"
        "height:100%;touch-action:pan-y;}\n"
    )
    partes.append(
        ".hero-lienzo:focus-visible{outline:2px solid var(--azul);"
        "outline-offset:-4px;}\n"
    )
    partes.append(
        ".hero-reserva{position:absolute;left:50%;top:46%;width:88%;"
        "max-width:32rem;transform:translate(-50%,-50%);"
        "transform-style:preserve-3d;}\n"
    )
    partes.append(
        ".hero-reserva .hero-svg{display:block;width:100%;height:auto;"
        "transform:translateZ(26px);"
        "animation:hero-giro 24s ease-in-out infinite alternate;}\n"
    )
    # `.hero-velo` deja de oscurecer y pasa a ser el halo blanco difuso centrado
    # con opacidad 0.35, dentro de la ventana [0.30, 0.40] del criterio 6.2.
    # Conserva su `linear-gradient(` literal, que una prueba vigente afirma.
    partes.append(
        ".hero-velo{position:absolute;inset:0;z-index:1;pointer-events:none;"
        "opacity:0.35;"
        "background:linear-gradient(180deg,var(--blanco-suave),"
        "var(--azul-cielo) 56%,transparent);}\n"
    )
    partes.append(
        ".hero-ui{position:relative;z-index:2;margin:0;max-width:100%;"
        "padding:2.5rem 1.25rem 1.5rem;color:var(--azul-profundo);"
        "background:var(--azul-cielo);"
        "backdrop-filter:blur(18px) saturate(135%);"
        "-webkit-backdrop-filter:blur(18px) saturate(135%);"
        "border-top:1px solid var(--violeta);}\n"
    )
    partes.append(".hero-ui>*{max-width:var(--medida);min-width:0;}\n")
    partes.append(".hero-ui h1{margin:0 0 .9rem;}\n")
    # Kicker, H1, lede y linea de ayuda del hero, todos en `--azul-profundo`
    # (criterio 6.3). Ningun blanco como color de texto dentro del hero (6.5).
    partes.append(
        ".hero-ui p,.hero-ui h1,.hero-ui .destacado,.hero-ui .hero-lede{"
        "color:var(--azul-profundo);}\n"
    )
    partes.append(
        ".hero-ayuda{margin:.6rem 0 0;color:var(--azul-profundo);font-size:.85em;"
        "letter-spacing:.03em;}\n"
    )
    # Toda sombra de la Hoja_Estilo lleva `rgba(11,44,77,0.12)` (criterio 16.14):
    # el filo del hero pasa a declararse con `var(--sombra)`.
    partes.append(
        ".hero-borde{position:absolute;inset:0;z-index:3;pointer-events:none;"
        "border-radius:inherit;"
        "box-shadow:inset 0 0 0 1px var(--sombra),"
        "inset 0 0 42px var(--sombra);}\n"
    )
    partes.append(
        "@keyframes hero-giro{"
        "from{transform:translateZ(26px) rotateY(-13deg) rotateX(2deg);}"
        "to{transform:translateZ(26px) rotateY(13deg) rotateX(-2deg);}}\n"
    )

    # Nada de anchos fijos mayores que el viewport: `min-width:0` en los hijos de
    # grid y flex, que es la causa real del desborde horizontal en Android.
    partes.append(
        ".ficha,.zona,.hero,.ficha-columnas,.col-visual,.col-datos{"
        "max-width:100%;}\n"
    )
    partes.append(
        ".ficha-columnas>*,.zona-encabezado>*,.chips>*,.buscador>*,"
        ".acciones>*,.descargas>*,.indice-capitulos>*,nav.sitio>*{"
        "min-width:0;}\n"
    )

    # Microanimación de entrada (solo CSS).
    partes.append(
        "@keyframes aparecer{from{opacity:0;transform:translateY(10px);}"
        "to{opacity:1;transform:none;}}\n"
    )
    partes.append("main>*{animation:aparecer .5s ease both;}\n")

    # ------------------------------------------------------------------ #
    # 5. Mundo_Hero, multi-vista, Balon_Esfera y Modo_Inerte
    # ------------------------------------------------------------------ #
    #
    # Lo emite `mundo_hero`, que es su dueno. Aqui entra `css_sin_modos()`: las
    # capas con su vaiven, la Figura_Girable con sus diez Vista_Figura y su
    # Sombra_Contacto, el Balon_Esfera con su degradacion de dos dimensiones y el
    # Modo_Inerte. Movimiento_Reducido e impresion del Mundo_Hero se funden mas
    # abajo con los bloques finales, para respetar el orden obligado del criterio
    # 11.7.
    partes.append(mundo_hero.css_sin_modos())
    partes.append("\n")

    # ------------------------------------------------------------------ #
    # 6. Visor_Ampliado como overlay modal (15.20, 28.5, 28.13, 28.16, 28.21)
    # ------------------------------------------------------------------ #
    #
    # ESTA es la UNICA regla `position:fixed` de toda la Hoja_Estilo, y el
    # criterio 28.5 la acota a este selector: el overlay del Visor_Ampliado. Todo
    # lo demas sigue como estaba --el hero va detras por `z-index`, la navegacion
    # inferior por `position:sticky`-- porque `position:fixed` en un contenedor de
    # lectura pelea con el desplazamiento en el navegador incrustado de Android.
    # Aqui no hay pelea posible: mientras el overlay esta abierto no hay nada que
    # desplazar detras (el `<body>` lleva `overflow:hidden`), y el unico scroll
    # vivo es el del cuerpo del propio overlay.
    #
    # El `touch-action:none` va PRIMERO en la regla y es el unico de la hoja: es
    # lo que deja al Arrastre_Rotacion leer el gesto en los dos ejes sin que el
    # navegador se lo robe. El hero conserva su `touch-action:pan-y`.
    partes.append(
        f".{secciones_guia.CLASE_VISOR}{{touch-action:none;position:fixed;"
        f"inset:0;z-index:{CAPA_MODAL};display:flex;flex-direction:column;"
        "max-width:100%;min-width:0;"
        "background:color-mix(in srgb, var(--fondo-modal) 85%, transparent);"
        f"backdrop-filter:blur({DESENFOQUE_MODAL});"
        f"-webkit-backdrop-filter:blur({DESENFOQUE_MODAL});}}\n"
    )
    # Mejora progresiva en tres reglas y en este orden exacto:
    #
    # 1. `[hidden]` oculta el overlay recien emitido, que es el estado de reposo;
    # 2. `:target` lo destapa **sin JavaScript**, porque va detras con la misma
    #    especificidad y gana la cascada: el ancla `#<id>-ampliada` sigue llevando
    #    a contenido legible y el cierre es un `<a>` que cambia el destino;
    # 3. con el Script_Unico vivo, `<html>` lleva la clase `con-modal` y esta
    #    ultima regla (mas especifica) devuelve el mando al atributo `hidden`, que
    #    es lo que `abrirModal` y `cerrarModal` alternan.
    partes.append(f".{secciones_guia.CLASE_VISOR}[hidden]{{display:none;}}\n")
    partes.append(f".{secciones_guia.CLASE_VISOR}:target{{display:flex;}}\n")
    partes.append(
        f".{secciones_guia.CLASE_CON_JS} "
        f".{secciones_guia.CLASE_VISOR}[hidden]{{display:none;}}\n"
    )
    # Barra superior fija de 56 px: titulo a la izquierda truncado a una linea,
    # cierre a la derecha.
    partes.append(
        f".{secciones_guia.CLASE_BARRA}{{flex:0 0 {ALTO_BARRA_MODAL}px;"
        f"height:{ALTO_BARRA_MODAL}px;display:flex;"
        "justify-content:space-between;align-items:center;gap:8px;"
        "padding:0 .6rem;min-width:0;background:var(--azul-cielo);"
        "border-bottom:1px solid var(--borde);}\n"
    )
    partes.append(
        f".{secciones_guia.CLASE_TITULO_VISOR}{{flex:1 1 auto;min-width:0;"
        "margin:0;padding:0;font-size:1.05rem;line-height:1.2;"
        "color:var(--azul-profundo);"
        "text-overflow:ellipsis;white-space:nowrap;overflow:hidden;}\n"
    )
    # El filete rosa de `h2::before` es para los titulos de seccion; en la barra
    # del overlay estorbaria al truncado.
    partes.append(
        f".{secciones_guia.CLASE_TITULO_VISOR}::before{{content:none;}}\n"
    )
    # Cuerpo: el UNICO scroll vivo mientras el overlay esta abierto, y con
    # `overscroll-behavior:contain` para que el gesto no se propague al documento.
    partes.append(
        f".{secciones_guia.CLASE_CUERPO_VISOR}{{flex:1 1 auto;"
        "overflow-y:auto;overscroll-behavior:contain;"
        "-webkit-overflow-scrolling:touch;display:flex;align-items:center;"
        "justify-content:center;padding:1rem;min-width:0;"
        "background:var(--blanco-suave);}\n"
    )
    # Ilustracion CONTENIDA: relacion de aspecto declarada por el `style` en linea
    # del propio contenedor, alto maximo relativo a la ventana pequena y contenido
    # centrado con flex. Nunca pisa el titulo ni sale del recuadro.
    partes.append(
        f".{secciones_guia.CLASE_LIENZO}{{position:relative;width:100%;"
        "max-width:100%;min-width:0;margin:0 auto;"
        f"aspect-ratio:var({diagramas_postura.VARIABLE_RELACION},"
        f"{diagramas_postura.RELACION_POR_DEFECTO});"
        f"max-height:{ALTO_MAX_LIENZO};"
        "display:flex;align-items:center;justify-content:center;}\n"
    )
    partes.append(
        f".{secciones_guia.CLASE_LIENZO} img,"
        f".{secciones_guia.CLASE_LIENZO} svg{{width:100%;height:100%;"
        "object-fit:contain;}\n"
    )
    partes.append(
        f".{secciones_guia.CLASE_LIENZO} .{vistas_figura.CLASE_GIRABLE}"
        "{width:100%;height:100%;}\n"
    )
    # Bloqueo de desplazamiento del documento mientras el overlay esta abierto. Se
    # cuelga de una CLASE y no de un estilo en linea: el Script_Unico solo tiene
    # permitido escribir `transform`, `opacity`, `visibility` y `will-change` en
    # linea (criterio 10.3), asi que el `overflow` vive aqui.
    partes.append(
        f"body.{secciones_guia.CLASE_CUERPO_FIJO}{{overflow:hidden;}}\n"
    )
    # Cierre circular de 44 px con el icono centrado.
    partes.append(
        f".{secciones_guia.CLASE_CERRAR}{{min-height:{LADO_TOQUE_PX}px;"
        f"min-width:{LADO_TOQUE_PX}px;display:inline-flex;align-items:center;"
        "justify-content:center;flex:0 0 auto;border-radius:999px;"
        "border:1px solid var(--azul-linea);border-bottom:1px solid "
        "var(--azul-linea);"
        "color:var(--azul-profundo);background:var(--azul-cielo);}\n"
    )
    partes.append(
        f".{secciones_guia.CLASE_ICONO}{{width:24px;height:24px;"
        "pointer-events:none;}\n"
    )
    partes.append(
        f".{secciones_guia.CLASE_AMPLIAR}{{color:var(--azul-profundo);"
        "background:var(--azul-medio);border-radius:999px;"
        "padding:.5rem .9rem;border-bottom:0;}\n"
    )

    # ------------------------------------------------------------------ #
    # 7. `@media (hover: hover)`: TODAS las reglas `:hover` (criterio 15.13)
    # ------------------------------------------------------------------ #
    #
    # Las nueve reglas se ENVUELVEN sin reescribir su texto, asi que las cadenas
    # que las pruebas vigentes afirman con `assertIn` siguen presentes literalmente
    # dentro de la consulta. En un telefono `(hover: hover)` no se cumple, asi que
    # ninguna de las nueve se activa por un toque accidental.
    partes.append(f"@media (hover: hover){{{_reglas_hover()}}}\n")
    # Los estados que SI existen al toque y con teclado van fuera de la consulta,
    # en reglas propias: sin esto, envolver las nueve se llevaria por delante el
    # `:focus-within` de las tarjetas y el `:focus-visible` de los botones.
    partes.append(_reglas_estado_tactil())

    # ------------------------------------------------------------------ #
    # 8. Pantalla ancha: los unicos cambios respecto de la base (criterio 15.1)
    # ------------------------------------------------------------------ #
    partes.append(
        "@media (min-width: 48rem){.hero{min-height:80dvh;}"
        ".hero-ui{padding:4.5rem 2rem 2rem;}"
        # Sobre 768 px la navegacion vuelve arriba: el borde inferior de la
        # ventana ya no es la zona comoda del pulgar.
        "nav.sitio{position:sticky;top:0;bottom:auto;border-top:0;"
        "border-bottom:1px solid var(--borde);}}\n"
    )
    # Escritorio: dos columnas, ilustracion grande a la izquierda e
    # instrucciones y metrica a la derecha. En celular hereda una columna con la
    # ilustracion primero (el orden del HTML ya es ese).
    partes.append(
        "@media (min-width: 64rem){"
        "main{max-width:76rem;}"
        ".ficha-columnas{display:grid;gap:1.25rem;"
        "grid-template-columns:minmax(0,1.05fr) minmax(0,1fr);"
        "align-items:start;}"
        ".col-visual{position:sticky;top:4.5rem;}"
        ".indice-capitulos{grid-template-columns:repeat(2,minmax(0,1fr));}"
        "}\n"
    )

    # ------------------------------------------------------------------ #
    # 9. Modo_Oscuro (criterios 16.15 y 16.16)
    # ------------------------------------------------------------------ #
    #
    # Fondo `#0B1F33` y texto `#DCEEFF`: 14.1 : 1 de contraste, valido en cuerpo y
    # en texto grande. Los tokens del tema oscuro que el criterio 16.17 conserva
    # encuentran aqui su uso: el hero pasa a un degradado profundo.
    partes.append(
        "@media (prefers-color-scheme: dark){"
        f"body{{background:{paleta.OSCURO_FONDO};color:{paleta.OSCURO_TEXTO};}}"
        f"section,article{{background:{paleta.OSCURO_FONDO};}}"
        f"p,li,dd,dt,td,th,figcaption,h1,h2,h3,h4{{color:{paleta.OSCURO_TEXTO};}}"
        "body{background-image:none;}"
        ".hero{background:linear-gradient(180deg,var(--fondo-profundo),"
        "var(--fondo));}"
        "}\n"
    )

    # ------------------------------------------------------------------ #
    # 10. Movimiento_Reducido (criterios 11.4, 11.6, 11.8, 11.9 y 15.1)
    # ------------------------------------------------------------------ #
    #
    # Respeto por quien prefiere menos movimiento: sin animaciones, sin
    # transiciones y sin transformaciones 3D. La informacion no depende de
    # ninguna de las tres. El cuerpo del Mundo_Hero se funde aqui dentro, en vez
    # de abrir una segunda consulta igual mas arriba.
    partes.append(
        "@media (prefers-reduced-motion: reduce){"
        "*{animation-duration:0.001ms !important;animation-iteration-count:1 !important;"
        "transition-duration:0.001ms !important;scroll-behavior:auto !important;}"
        "main>*{animation:none;}"
        ".ficha{perspective:none;}"
        ".hero-visor{perspective:none;}"
        ".hero-reserva .hero-svg{animation:none !important;}"
        # Sin ninguna variante `:hover` en la lista: el criterio 15.13 exige que
        # toda regla con `:hover` viva dentro de `@media (hover: hover)`, y aqui
        # sobran, porque `transform:none !important` sobre el selector base gana a
        # cualquier `transform` del estado por muy especifico que sea.
        ".zona,.zona:focus-within,.zona:active,"
        ".chip,.chip:focus-within,.chip:active,"
        ".numero-ficha,figure,figure.ilustracion,"
        ".hero-reserva .hero-svg,"
        ".btn-video,.btn-video:focus-visible,.btn-video:active,"
        ".indice-capitulos a{transform:none !important;}"
        # Ampliacion: capas, objetos y giros del Mundo_Hero congelados con
        # opacidad 1, animaciones de Vista_Figura, Gajo_Balon, Sombra_Contacto y
        # Balon_Esfera apagadas, y visible exactamente `az-000`.
        + mundo_hero.css_reduccion_cuerpo()
        + "}\n"
    )

    # ------------------------------------------------------------------ #
    # 11. Impresion, la ULTIMA (criterio 11.7)
    # ------------------------------------------------------------------ #
    #
    # Va detras del bloque de Movimiento_Reducido a proposito: asi gana por cascada
    # y el Mundo_Hero no se imprime ni con movimiento reducido activo. Version
    # CLARA de alto contraste (fondo #FFF8FB, tinta oscura) para el papel.
    partes.append(mundo_hero.css_impresion())
    partes.append("\n")
    partes.append(
        "@media print{"
        "nav.sitio,.descarga{display:none;}"
        f"body{{background:{_FONDO};color:{_NEGRO};font-size:12pt;}}"
        "main{max-width:none;margin:0;padding:0;}"
        f"h1{{background:none;-webkit-background-clip:border-box;"
        f"background-clip:border-box;color:{_ROSA};"
        "-webkit-text-fill-color:currentColor;}"
        f"h2{{color:{_ROSA};break-before:page;page-break-before:always;}}"
        f"h2::before{{background:{_ROSA};}}"
        f"p,td,figcaption,.indice-capitulos a{{color:{_NEGRO};}}"
        f"figure,.scroll-x,.indice-capitulos a,.zona,.chip{{background:{_FONDO};"
        f"border:1px solid {_GRIS};"
        "backdrop-filter:none;-webkit-backdrop-filter:none;box-shadow:none;}"
        "body{background-image:none;}"
        ".ficha{perspective:none;}"
        ".hero-velo,.hero-borde{display:none;}"
        f".hero{{background:{_FONDO};border:1px solid {_GRIS};box-shadow:none;"
        "min-height:0;}"
        ".hero-visor{position:static;perspective:none;height:auto;}"
        ".hero-reserva{position:static;left:auto;top:auto;width:100%;"
        "transform:none;margin:0 auto 1rem;}"
        ".hero-reserva .hero-svg{animation:none;transform:none;}"
        f".hero-ui{{background:{_FONDO};padding:0;border-top:0;"
        "backdrop-filter:none;-webkit-backdrop-filter:none;}"
        f".hero-ayuda{{color:{_NEGRO};}}"
        ".zona,.chip,.numero-ficha,figure.ilustracion{transform:none;}"
        f".zona-etiqueta,.chip b,dl.datos dt{{color:{_NEGRO};}}"
        f".numero-ficha{{background:none;-webkit-background-clip:border-box;"
        f"background-clip:border-box;color:{_ROSA};"
        "-webkit-text-fill-color:currentColor;}"
        f".pasos li::before{{background:{_ROSA_SUAVE};color:{_NEGRO};}}"
        f".lista-zona li::before{{background:{_NEGRO};}}"
        f".marca-error,.marca-correccion{{color:{_NEGRO};}}"
        f".btn-video{{background:none;color:{_NEGRO};"
        f"border:1px solid {_GRIS};}}"
        ".ficha-columnas{display:block;}"
        f"th{{background:{_ROSA_SUAVE};color:{_NEGRO};}}"
        f"th,td{{border:1px solid {_GRIS};}}"
        f"a{{color:{_NEGRO};border-bottom:0;}}"
        f"hr{{background:{_ROSA};}}"
        "}\n"
    )

    return "".join(partes)


def _banda_descarga(pdf_href: str, tam_mb: float | None) -> str:
    """Banda con el enlace `download` al PDF y, si se conoce, su tamaño en MB."""
    if tam_mb is not None:
        tamano = f' <span class="peso">({tam_mb:.1f} MB)</span>'
    else:
        tamano = ""
    return (
        '<div class="descarga">'
        f'<a href="{_esc(pdf_href)}" download>Descargar el PDF completo</a>'
        f"{tamano}</div>"
    )


def _nav(capitulos: list[_Capitulo], activo: str | None) -> str:
    """Navegación del sitio: enlace al índice y a cada capítulo."""
    partes: list[str] = ['<nav class="sitio">']
    partes.append('<a href="index.html">Índice</a>')
    for cap in capitulos:
        if cap.id == activo:
            partes.append(f"<a href=\"{_esc(cap.archivo)}\">&#9656; {_esc(cap.titulo)}</a>")
        else:
            partes.append(f'<a href="{_esc(cap.archivo)}">{_esc(cap.titulo)}</a>')
    partes.append("</nav>")
    return "".join(partes)


#: Línea de apoyo del hero, en español de México. No comunica nada por color.
_HERO_AYUDA_ESTATICA: str = (
    "El modelo gira solo. En esta página se mueve con CSS: no hay JavaScript, "
    "para que el capítulo se lea completo sin ejecutar nada."
)


def _hero_capitulo(kicker: str, titulo: str) -> str:
    """Hero del capítulo: el MISMO modelo 3D, pero SIN JavaScript (Req 2.4).

    Desviación honesta respecto a lo que se pidió: aquí no puede ir el visor
    interactivo. `test_build_html::test_sin_javascript` y
    `::test_html_sin_atributos_de_evento` prohíben cualquier `<script>` y
    cualquier atributo `on*` en estas páginas, y esas pruebas defienden el
    Req 2.4 ("HTML estático que se muestre completo sin ejecutar JavaScript").
    Lo que sí se puede es lo que hay: la misma malla proyectada a SVG inline por
    `escena3d.svg_estatico()`, con la animación y la profundidad hechas solo con
    CSS (`@keyframes`, `perspective`, `translateZ`) sobre el mismo tema de
    vidrio. El visor con canvas, swipe y pinch vive únicamente en el sitio de un
    archivo, que sí admite un `<script>` propio.
    """
    from . import escena3d

    partes: list[str] = []
    partes.append('<section class="hero">')
    partes.append('<div class="hero-visor">')
    partes.append('<div class="hero-reserva">')
    partes.append(escena3d.svg_estatico())
    partes.append("</div>")
    partes.append("</div>")
    partes.append('<div class="hero-velo"></div>')
    partes.append('<div class="hero-ui">')
    partes.append(f'<p class="destacado">{_esc(kicker)}</p>')
    partes.append(f"<h1>{_esc(titulo)}</h1>")
    partes.append(f'<p class="hero-ayuda">{_esc(_HERO_AYUDA_ESTATICA)}</p>')
    partes.append("</div>")
    partes.append('<div class="hero-borde"></div>')
    partes.append("</section>")
    return "".join(partes)


def _envolver_documento(
    titulo: str, css: str, cuerpo: str, *, viewport: str = META_VIEWPORT
) -> str:
    """Ensambla un documento HTML completo con `<meta viewport>` y CSS embebido.

    `viewport` es `META_VIEWPORT` por defecto, que es lo que llevan las paginas
    de capitulo y la publicacion. El Target_Web pasa `META_VIEWPORT_SITIO`
    (criterio 15.11): es el unico destino con `viewport-fit=cover`.
    """
    partes: list[str] = []
    partes.append("<!DOCTYPE html>")
    partes.append('<html lang="es-MX">')
    partes.append("<head>")
    partes.append('<meta charset="utf-8">')
    partes.append(f'<meta name="viewport" content="{viewport}">')
    partes.append(f"<title>{_esc(titulo)}</title>")
    partes.append(f"<style>{css}</style>")
    partes.append("</head>")
    partes.append("<body>")
    partes.append(cuerpo)
    partes.append("</body>")
    partes.append("</html>")
    return "\n".join(partes)


# --------------------------------------------------------------------------- #
# Construcción de páginas del sitio
# --------------------------------------------------------------------------- #


def _html_indice(
    capitulos: list[_Capitulo], titulo: str, css: str, pdf_href: str, tam_mb: float | None
) -> str:
    """`index.html`: banda de descarga, navegación y lista de capítulos."""
    cuerpo: list[str] = []
    cuerpo.append(_banda_descarga(pdf_href, tam_mb))
    cuerpo.append(_nav(capitulos, None))
    cuerpo.append("<main>")
    cuerpo.append(f"<h1>{_esc(titulo)}</h1>")
    cuerpo.append('<ul class="indice-capitulos">')
    for cap in capitulos:
        cuerpo.append(
            f'<li><a href="{_esc(cap.archivo)}">{_esc(cap.titulo)}</a></li>'
        )
    cuerpo.append("</ul>")
    cuerpo.append("</main>")
    return _envolver_documento(titulo, css, "".join(cuerpo))


def _html_capitulo(
    cap: _Capitulo,
    capitulos: list[_Capitulo],
    titulo_sitio: str,
    css: str,
    pdf_href: str,
    tam_mb: float | None,
) -> str:
    """HTML de un capítulo: banda de descarga, navegación y contenido reflowed."""
    cuerpo: list[str] = []
    cuerpo.append(_banda_descarga(pdf_href, tam_mb))
    cuerpo.append(_nav(capitulos, cap.id))
    cuerpo.append(f'<main data-capitulo="{_esc(cap.id)}">')
    cuerpo.append(_hero_capitulo(titulo_sitio, cap.titulo))
    _render_elementos(cap, cuerpo)
    cuerpo.append("</main>")
    titulo_doc = f"{cap.titulo} · {titulo_sitio}"
    return _envolver_documento(titulo_doc, css, "".join(cuerpo))


def _tam_mb(pdf_ruta: str | None) -> float | None:
    """Tamaño del PDF en MB con `os.stat`, o `None` si no existe todavía."""
    if not pdf_ruta:
        return None
    try:
        tam = os.stat(pdf_ruta).st_size
    except OSError:
        return None
    return tam / (1024.0 * 1024.0)


# --------------------------------------------------------------------------- #
# API pública
# --------------------------------------------------------------------------- #


def documento_a_html(
    paginas: list[PaginaRender],
    *,
    titulo: str = "Guía Extensa de Entrenamiento Femenil Sub-17",
    pdf_href: str = PDF_HREF,
    pdf_ruta: str | None = None,
) -> dict[str, str]:
    """Genera el sitio en memoria: `{nombre_archivo: contenido}`.

    Incluye `index.html`, `estilo.css` y un HTML por capítulo con nombre de
    salida numérico y con guiones. No toca el disco (útil para pruebas). El
    tamaño del PDF de la banda de descarga se obtiene de `pdf_ruta` con
    `os.stat` si se proporciona y existe; si no, la banda se emite sin tamaño.
    """
    capitulos = _agrupar_por_capitulo(paginas)
    css = estilo_css()
    tam_mb = _tam_mb(pdf_ruta)

    salida: dict[str, str] = {}
    salida["estilo.css"] = css
    salida["index.html"] = _html_indice(capitulos, titulo, css, pdf_href, tam_mb)
    for cap in capitulos:
        salida[cap.archivo] = _html_capitulo(
            cap, capitulos, titulo, css, pdf_href, tam_mb
        )
    return salida


def escribir_html(
    paginas: list[PaginaRender],
    dir_salida: str,
    *,
    titulo: str = "Guía Extensa de Entrenamiento Femenil Sub-17",
    pdf_href: str = PDF_HREF,
    pdf_ruta: str | None = None,
) -> list[str]:
    """Escribe el sitio HTML completo en `dir_salida`. Devuelve las rutas escritas.

    Crea `dir_salida` si no existe. Cada archivo se escribe en UTF-8 con
    `newline='\\n'` para bytes estables entre sistemas. Punto de entrada del
    Motor_HTML para el Orquestador_Build.
    """
    os.makedirs(dir_salida, exist_ok=True)
    documentos = documento_a_html(
        paginas, titulo=titulo, pdf_href=pdf_href, pdf_ruta=pdf_ruta
    )
    escritas: list[str] = []
    for nombre, contenido in documentos.items():
        ruta = os.path.join(dir_salida, nombre)
        with open(ruta, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(contenido)
        escritas.append(ruta)
    return escritas
