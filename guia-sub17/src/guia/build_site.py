"""Motor del sitio de un solo archivo (`build_site.py`, Addendum A, tarea 19).

Emite un **único** `dist/index.html` **autocontenido** para la feature "Entrena
como las grandes" (Target_Web, decision C3 del diseno): CSS embebido, SVG de
cancha inline, codigos QR como SVG de rectangulos, enlaces de video clicables y
**cero recursos externos** (sin CDN, sin `<link rel=stylesheet>`, sin `<script>`
de terceros ni remoto, sin imagenes remotas): el unico `<script>` es propio y va
embebido. Abre por doble clic desde un USB, sin internet.

Diferencias con `build_html.py`
------------------------------

`build_html.py` genera el sitio **multi-archivo** de la Guia_Extensa (un HTML por
capitulo) a partir del `Modelo_Paginas`. Este modulo genera el sitio de **un solo
archivo** directamente desde el `Catalogo_JSON` (`contenido/ejercicios.json`), las
15 Ficha_JSON reales, sin pasar por el paginador. Ambos conviven (C3).

Buscador/filtros con mejora progresiva (tarea 20)
-------------------------------------------------

El sitio incluye un buscador por texto y filtros por `categoria` y `nivel`
implementados con un `<script>` **propio y minimo** embebido al final del cuerpo
(cero librerias, cero CDN, cero red). Es **mejora progresiva**: sin JavaScript
ninguna ficha se oculta (no llevan `hidden` de origen), el indice de anclas sigue
funcionando y todos los enlaces y codigos QR quedan accesibles. Este `<script>`
vive solo en el sitio de un archivo de `build_site.py`; el Motor_HTML por capitulo
(`build_html.py`) sigue **sin** `<script>`.

Reutilizacion de la estetica (rediseño de la tarea 33.4)
-------------------------------------------------------

La estetica no se redefine aqui: se **reutiliza** la de `build_html`, que en la
tarea 33.4 paso a la direccion de arte futurista (neones cian/violeta/verde
añadidos a `paleta.py`, lineas finas de interfaz, profundidad simulada solo con
CSS y `prefers-reduced-motion` respetado). Este modulo consume:

* el CSS es exactamente `build_html.estilo_css()` (mismo tema oscuro glass, con
  su `@media print` claro para imprimir);
* el escapado usa `build_html._esc` (`html.escape(..., quote=True)`);
* el andamiaje del documento usa `build_html._envolver_documento` (DOCTYPE,
  `<meta charset>`, `<meta viewport>`, `<title>`, `<style>` inline);
* los codigos QR se dibujan con `build_html._qr_a_svg` (un `<rect>` por modulo).

No se toca `viz.py` ni `draw.py`: la ilustracion de tecnica de cada ficha se
rinde con el **mismo** `viz.render_svg` que el diagrama de cancha, porque las
figuras de `figuras.py` son `DiagramaSpec` de clase POSTURA. Asi la paridad
web/PDF y la Property 12 (todo color de la paleta) salen gratis.

Estructura del documento
------------------------

Portada/encabezado (kicker + H1 + lede) -> navegacion en pagina (enlaces
`#ancla`, sin JS) -> indice de las fichas -> seccion de periodizacion practica
(plan de 12 semanas) -> las fichas, cada una compuesta en las **nueve zonas** de
`zonas.py` (encabezado, zona visual con ilustracion y cancha, "Hazlo asi",
puntos clave, errores comunes, dosis, progresion, medicion y video con su QR)
-> apendice de enlaces. La guia muestra SOLO contenido practico y los
enlaces de video utiles de las fichas: nunca fuentes, bibliografia, referencias,
autores ni URLs de metodologia (esas son referencia interna de diseno).

Convenciones del proyecto: solo libreria estandar; sin `assert` (los invariantes
que aplican viven en los modulos reutilizados y usan `raise ErrorBuild`);
`from __future__ import annotations`; type hints; sin concatenacion de strings en
bucle (se acumula en `list[str]` y se une con `''.join(...)`); escritura con
`open(..., 'w', encoding='utf-8', newline='\\n')` y publicacion **atomica** desde
`dist/.tmp/` con `os.replace` (con degradacion a escritura directa).

Descargas (tarea 24)
--------------------

El header lleva dos botones principales con enlaces RELATIVOS: `.btn-solid`
(magenta) descarga la guia (`guia.pdf`) y `.btn-outline` descarga las laminas
(`laminas.pdf`). Ademas hay un bloque de descargas con los tres artefactos:
`guia.pdf`, `laminas.pdf` (ambos en el mismo `dist/`) y el Catalogo_JSON crudo
`ejercicios.json` (que `build.py` copia a `dist/ejercicios.json`). Los PDF usan
`download`; el JSON crudo tambien. Cero JavaScript de terceros, cero CDN.

_Requirements: 12.2, 12.4, 13.1, 13.2, 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_
"""

from __future__ import annotations

import os
from typing import Any

from . import build_html, escena3d, figuras, paleta, periodizacion, qr, viz, zonas
from . import diagramas_postura as dp
from . import mundo_hero as mh
from . import secciones_guia
from . import vistas_figura as vf
from .contenido import cap10_fundamentos
from .diagram_spec import desde_cancha_json
from .schema_json import cargar_catalogo

__all__ = [
    "TITULO_SITIO",
    "NOMBRE_INDICE",
    "dir_dist_por_defecto",
    "fundamentos_omitidos",
    "html_sitio",
    "escribir_sitio",
]


# --------------------------------------------------------------------------- #
# Constantes de la portada y del artefacto
# --------------------------------------------------------------------------- #

#: Titulo del sitio (portada y `<title>` del documento).
TITULO_SITIO: str = "Entrena como las grandes"

#: Kicker en mayusculas de la portada (tratado con `.destacado` del CSS).
_KICKER: str = "Guia de entrenamiento femenil Sub-17"

#: Lede introductorio de la portada.
_LEDE: str = (
    "Quince ejercicios reales para entrenar con lo que hay: un balon, una pared "
    "y ganas. Cada ficha trae el diagrama de la cancha, el paso a paso, la dosis "
    "y un enlace de video con su codigo QR para verlo desde el celular."
)

#: Nombre del unico archivo emitido.
NOMBRE_INDICE: str = "index.html"

#: Ancla del apendice de enlaces (navegacion en pagina, sin JS).
_ANCLA_APENDICE: str = "apendice"

#: Ancla del bloque de descargas (navegacion en pagina, sin JS).
_ANCLA_DESCARGAS: str = "descargas"

#: Ancla de la portada/indice.
_ANCLA_TOPE: str = "top"

# --------------------------------------------------------------------------- #
# Descargas (Req 13.1, 13.2): enlaces RELATIVOS a los tres artefactos.
# --------------------------------------------------------------------------- #

#: Enlace relativo al PDF de la guia (mismo `dist/` que este `index.html`).
_HREF_GUIA_PDF: str = "guia.pdf"

#: Enlace relativo al PDF de laminas verticales (mismo `dist/`).
_HREF_LAMINAS_PDF: str = "laminas.pdf"

#: Enlace relativo al Catalogo_JSON crudo, que el build copia a `dist/`.
_HREF_JSON: str = "ejercicios.json"

#: Ids de los controles del buscador (compartidos entre HTML y `<script>`).
_ID_BUSCAR: str = "gb-q"
_ID_CATEGORIA: str = "gb-cat"
_ID_NIVEL: str = "gb-niv"
_ID_VACIO: str = "gb-vacio"

#: Ids del hero con visor 3D (compartidos entre HTML y `<script>`).
_ID_VISOR: str = "gb-visor"
_ID_LIENZO: str = "gb-lienzo"
_ID_RESERVA: str = "gb-reserva"

#: Línea de apoyo del hero, en español de México. Nombra las dos formas de
#: interactuar; el hero no comunica nada solo por color.
_HERO_AYUDA: str = (
    "Arrastra un dedo sobre el modelo para girarlo y junta dos dedos para "
    "acercarlo. Con ratón, el modelo sigue el cursor. El desplazamiento "
    "vertical de la página nunca se bloquea."
)

#: Id de la Zona_Tactil "Activar movimiento" del hero (criterio 9.10). El
#: manejador del permiso de orientacion se engancha aqui y en ningun otro sitio.
_ID_MOVIMIENTO: str = "gb-movimiento"

#: Texto visible de las dos Zona_Tactil del hero (criterios 19.2 y 9.10).
_TEXTO_EMPEZAR: str = "Empezar"
_TEXTO_MOVIMIENTO: str = "Activar movimiento"

#: Etiqueta legible del badge segun el `tipo` del Media_Item.
_BADGE_TIPO: dict[str, str] = {
    "youtube": "VIDEO",
    "tiktok": "VIDEO",
    "instagram_reel": "VIDEO",
    "facebook_reel": "VIDEO",
    "web": "WEB",
    "busqueda": "BUSCAR",
}

#: Texto FIJO del ancla de cada Media_Item. El titulo del media se rinde como
#: texto plano al lado del badge; el enlace siempre dice lo mismo, asi la accion
#: queda clara y ningun enlace se presenta como fuente ni bibliografia.
_TEXTO_ENLACE_MEDIA: str = "Ver demostracion"


# --------------------------------------------------------------------------- #
# Localizacion de rutas
# --------------------------------------------------------------------------- #


def _raiz_proyecto() -> str:
    """Ruta absoluta a `guia-sub17/` (dos niveles sobre `src/guia/build_site.py`)."""
    aqui = os.path.dirname(os.path.abspath(__file__))  # .../src/guia
    src = os.path.dirname(aqui)  # .../src
    return os.path.dirname(src)  # .../guia-sub17


def dir_dist_por_defecto() -> str:
    """Directorio `dist/` por defecto, relativo a la raiz del proyecto."""
    return os.path.join(_raiz_proyecto(), "dist")


# --------------------------------------------------------------------------- #
# Carga del Catalogo_JSON (15 fichas reales)
# --------------------------------------------------------------------------- #


def _cargar_fichas() -> list[dict[str, Any]]:
    """Carga y valida las 15 Ficha_JSON reales con la ruta robusta del proyecto.

    Reutiliza `cap10_fundamentos.ruta_catalogo()` (que localiza
    `contenido/ejercicios.json` subiendo desde el paquete) y
    `schema_json.cargar_catalogo(...)` (que parsea y valida el esquema JSON).
    No cambia el esquema, ni los enlaces, ni el campo `cancha`.
    """
    return cargar_catalogo(cap10_fundamentos.ruta_catalogo())


# --------------------------------------------------------------------------- #
# Render de una ficha
# --------------------------------------------------------------------------- #


def _abrir_zona(nombre: str, clase: str, partes: list[str]) -> None:
    """Abre una de las nueve zonas de la ficha con su marca `data-zona`."""
    partes.append(f'<section class="zona {clase}" data-zona="{nombre}">')


def _render_ilustracion(
    ficha: dict[str, Any], postura: object, partes: list[str]
) -> None:
    """Ilustracion de tecnica -> SVG inline accesible, si la ficha lleva una.

    El SVG lo emite `viz.render_svg` sobre el `DiagramaSpec` de `figuras.py`: ya
    trae `viewBox`, `role="img"`, `<title>` y `<desc>`, y **no** lleva `width` ni
    `height` absolutos en la etiqueta de apertura. El `figcaption` repite el texto
    alternativo en la pagina, para quien no usa lector de pantalla.
    """
    if postura is None:
        return
    svg = viz.render_svg(postura)
    alternativo = zonas.texto_alternativo(ficha, postura)
    partes.append('<figure class="ilustracion" data-postura="1">')
    partes.append(svg)
    if alternativo:
        partes.append(f"<figcaption>{build_html._esc(alternativo)}</figcaption>")
    partes.append("</figure>")


def _render_diagrama(ficha: dict[str, Any], partes: list[str]) -> None:
    """Diagrama de cancha -> SVG inline (via `viz.render_svg`), si la ficha lo tiene."""
    cancha = ficha.get("cancha")
    if not isinstance(cancha, dict) or not cancha:
        return
    spec = desde_cancha_json(cancha)
    if spec is None:
        return
    svg = viz.render_svg(spec)
    partes.append('<figure class="diagrama">')
    partes.append(svg)
    titulo = cancha.get("titulo")
    if titulo:
        partes.append(f"<figcaption>{build_html._esc(titulo)}</figcaption>")
    partes.append("</figure>")


def _render_lista(
    lineas: tuple[str, ...], partes: list[str], *, marcar_errores: bool = False
) -> None:
    """Lista de puntos con su rotulo de texto (nunca solo por color).

    Cuando `marcar_errores` es cierto, cada linea que viene del panel de error de
    la ilustracion se rotula con la palabra `Error` o `Corrige`, de modo que el
    significado se lee tambien sin ver el color rojo.
    """
    if not lineas:
        return
    partes.append('<ul class="lista-zona">')
    for linea in lineas:
        texto = build_html._esc(linea)
        if marcar_errores:
            bajo = linea.strip().lower()
            if bajo.startswith("corrige"):
                partes.append(
                    f'<li><span class="marca-correccion">Corrige</span>{texto}</li>'
                )
                continue
            partes.append(f'<li><span class="marca-error">Error</span>{texto}</li>')
            continue
        partes.append(f"<li>{texto}</li>")
    partes.append("</ul>")


def _render_chips(pares: tuple[tuple[str, str], ...], partes: list[str]) -> None:
    """Pares (rotulo, valor) como chips grandes, tactiles en celular."""
    if not pares:
        return
    partes.append('<ul class="chips">')
    for rotulo, valor in pares:
        partes.append(
            f'<li class="chip"><b>{build_html._esc(rotulo)}</b>'
            f"<span>{build_html._esc(valor)}</span></li>"
        )
    partes.append("</ul>")


def _render_datos(pares: tuple[tuple[str, str], ...], partes: list[str]) -> None:
    """Pares (rotulo, texto largo) como lista de definiciones legible."""
    if not pares:
        return
    partes.append('<dl class="datos">')
    for rotulo, texto in pares:
        partes.append(f"<dt>{build_html._esc(rotulo)}</dt>")
        partes.append(f"<dd>{build_html._esc(texto)}</dd>")
    partes.append("</dl>")


def _render_media(ficha: dict[str, Any], partes: list[str]) -> None:
    """Cada Media_Item -> QR (SVG de rectangulos) + enlace clicable `target=_blank`.

    El pie de cada QR lleva el badge del tipo, el **titulo del media como texto**
    (por ejemplo "Video de ejemplo") y un ancla con el texto FIJO
    `Ver demostracion`. Los enlaces son contenido practico de la ficha; nunca se
    presentan como fuente, bibliografia ni referencia.
    """
    media = ficha.get("media") or []
    if not media:
        return
    partes.append(f"<h3>{build_html._esc(zonas.TITULO_VIDEO)}</h3>")
    for item in media:
        url = item.get("url")
        if not url:
            continue
        titulo = item.get("titulo") or url
        tipo = item.get("tipo") or "web"
        matriz = qr.codificar(url)
        svg = build_html._qr_a_svg(matriz, titulo)
        etiqueta = _BADGE_TIPO.get(tipo, tipo.upper())
        partes.append('<figure class="qr-figura">')
        if svg:
            partes.append(svg)
        # El QR queda visible y su enlace legible debajo: nada importante vive
        # detras de un `hover`, y el texto del boton es siempre el mismo.
        partes.append(
            "<figcaption>"
            f"<strong>{build_html._esc(etiqueta)}</strong> "
            f"{build_html._esc(titulo)} "
            f'<a class="btn-video" href="{build_html._esc(url)}" target="_blank" '
            f'rel="noopener noreferrer">{_TEXTO_ENLACE_MEDIA}</a>'
            f'<span class="enlace-visible">{build_html._esc(url)}</span>'
            "</figcaption>"
        )
        partes.append("</figure>")


def _texto_buscable(ficha: dict[str, Any]) -> str:
    """Texto plano concatenado de la ficha para el buscador (progresivo, con JS).

    Se acumula en una lista y se une con `''.join(...)` para no concatenar
    strings en bucle. El JS normaliza acentos y mayusculas en ambos extremos, asi
    que aqui basta con volcar el texto tal cual; sin este atributo (sin JS) la
    ficha se muestra igual.
    """
    piezas: list[str] = [
        str(ficha.get("numero", "")),
        str(ficha.get("titulo", "")),
        str(ficha.get("subtitulo", "")),
        str(ficha.get("categoria", "")),
        str(ficha.get("nivel", "")),
        str(ficha.get("contexto", "")),
    ]
    for paso in ficha.get("pasos") or []:
        piezas.append(str(paso))
    for obs in ficha.get("que_mira_la_companera") or []:
        piezas.append(str(obs))
    return " ".join(piezas)


def _render_ficha(ficha: dict[str, Any], partes: list[str]) -> None:
    """Renderiza una `article.ficha` completa con su ancla `#ficha-<id>`.

    Composicion editorial en **nueve zonas**, en este orden: encabezado, zona
    visual, "Hazlo asi", puntos clave, errores comunes, dosis, progresion,
    medicion y video (ver `zonas.ZONAS`). En escritorio la zona visual queda a la
    izquierda y las instrucciones y la metrica a la derecha (`.ficha-columnas`);
    en celular todo cae a una columna con la ilustracion primero, porque ese es
    el orden del HTML.
    """
    fid = ficha["id"]
    numero = ficha["numero"]
    categoria = ficha["categoria"]
    nivel = ficha["nivel"]
    titulo = ficha["titulo"]
    subtitulo = ficha["subtitulo"]
    contexto = ficha["contexto"]
    postura = figuras.para_ficha(ficha)

    # Atributos de datos que consume el buscador con JS (mejora progresiva).
    # Sin JS, `article.ficha` no lleva `hidden` y se ve igual que las demas.
    partes.append(
        '<article class="ficha"'
        f' id="ficha-{build_html._esc(fid)}"'
        f' data-categoria="{build_html._esc(categoria)}"'
        f' data-nivel="{build_html._esc(nivel)}"'
        f' data-buscar="{build_html._esc(_texto_buscable(ficha))}">'
    )

    # --- Zona 1: encabezado ---------------------------------------------- #
    _abrir_zona("encabezado", "zona-encabezado", partes)
    partes.append(f'<p class="numero-ficha">{build_html._esc(numero)}</p>')
    partes.append(
        '<p class="meta-ficha">'
        f"<span>{build_html._esc(categoria)}</span>"
        f"<span>{build_html._esc(nivel)}</span>"
        "</p>"
    )
    partes.append(f"<h2>{build_html._esc(titulo)}</h2>")
    partes.append(f'<p class="objetivo">{build_html._esc(subtitulo)}</p>')
    partes.append(f"<p>{build_html._esc(contexto)}</p>")
    partes.append("</section>")

    partes.append('<div class="ficha-columnas">')

    # --- Zona 2: zona visual (ilustracion grande + diagrama de cancha) ---- #
    partes.append('<div class="col-visual">')
    _abrir_zona("visual", "zona-visual", partes)
    partes.append('<p class="zona-etiqueta">Zona visual</p>')
    _render_ilustracion(ficha, postura, partes)
    _render_diagrama(ficha, partes)
    partes.append("</section>")
    partes.append("</div>")

    partes.append('<div class="col-datos">')

    # --- Zona 3: "Hazlo asi" --------------------------------------------- #
    pasos = zonas.pasos_hazlo_asi(ficha)
    if pasos:
        _abrir_zona("hazlo-asi", "zona-pasos", partes)
        partes.append(f"<h3>{build_html._esc(zonas.TITULO_HAZLO_ASI)}</h3>")
        partes.append('<ol class="pasos">')
        for paso in pasos:
            partes.append(f"<li>{build_html._esc(paso)}</li>")
        partes.append("</ol>")
        partes.append("</section>")

    # --- Zona 4: puntos clave -------------------------------------------- #
    clave = zonas.puntos_clave(ficha, postura)
    if clave:
        _abrir_zona("puntos-clave", "zona-clave", partes)
        partes.append(f"<h3>{build_html._esc(zonas.TITULO_PUNTOS_CLAVE)}</h3>")
        _render_lista(clave, partes)
        partes.append("</section>")

    # --- Zona 5: errores comunes ----------------------------------------- #
    errores = zonas.errores_comunes(ficha, postura)
    if errores:
        _abrir_zona("errores", "zona-errores", partes)
        partes.append(f"<h3>{build_html._esc(zonas.TITULO_ERRORES)}</h3>")
        _render_lista(errores, partes, marcar_errores=postura is not None)
        partes.append("</section>")

    # --- Zona 6: dosis ---------------------------------------------------- #
    chips = zonas.dosis_chips(ficha)
    if chips:
        _abrir_zona("dosis", "zona-dosis", partes)
        partes.append(f"<h3>{build_html._esc(zonas.TITULO_DOSIS)}</h3>")
        _render_chips(chips, partes)
        partes.append("</section>")

    # --- Zona 7: progresion ---------------------------------------------- #
    fases = zonas.progresion(ficha)
    if fases:
        _abrir_zona("progresion", "zona-progresion", partes)
        partes.append(f"<h3>{build_html._esc(zonas.TITULO_PROGRESION)}</h3>")
        _render_datos(fases, partes)
        partes.append("</section>")

    # --- Zona 8: medicion ------------------------------------------------ #
    metrica = zonas.medicion(ficha)
    if metrica:
        _abrir_zona("medicion", "zona-medicion", partes)
        partes.append(f"<h3>{build_html._esc(zonas.TITULO_MEDICION)}</h3>")
        _render_datos(metrica, partes)
        partes.append("</section>")

    partes.append("</div>")
    partes.append("</div>")

    # --- Zona 9: video de ejemplo ---------------------------------------- #
    _abrir_zona("video", "zona-video", partes)
    _render_media(ficha, partes)
    partes.append("</section>")

    partes.append("</article>")


# --------------------------------------------------------------------------- #
# Portada, navegacion en pagina, indice y apendice
# --------------------------------------------------------------------------- #


def _hero(titulo: str, partes: list[str]) -> None:
    """Hero con el visor 3D propio detras de la interfaz de vidrio (tarea 34.3).

    Capas, de atras hacia adelante: `.hero-visor` (el modelo), `.hero-velo` (el
    oscurecimiento que garantiza el contraste del texto sobre cualquier fotograma
    del modelo), `.hero-ui` (la interfaz de vidrio con el kicker, el titulo, el
    lede y la linea de ayuda) y `.hero-borde` (el filo de neon, inerte).

    Mejora progresiva de verdad: el `<canvas>` arranca con `hidden` y el dibujo
    que se ve es el SVG estatico de `escena3d.svg_estatico()`. Solo cuando el
    visor consigue un contexto 2D real destapa el canvas y oculta la reserva. Si
    el `<script>` se retira o el navegador no ejecuta JavaScript, lo que queda es
    el SVG: el hero sigue teniendo dibujo y texto, no un hueco.
    """
    partes.append(
        f'<section class="hero" id="{secciones_guia.ANCLA_HERO}">'
    )
    _mundo_hero(partes)
    partes.append(f'<div class="hero-visor" id="{_ID_VISOR}">')
    partes.append(
        f'<canvas class="hero-lienzo" id="{_ID_LIENZO}" role="img" tabindex="0"'
        f' aria-label="{build_html._esc(escena3d.ETIQUETA_ACCESIBLE)}" hidden>'
        "</canvas>"
    )
    partes.append(f'<div class="hero-reserva" id="{_ID_RESERVA}">')
    partes.append(escena3d.svg_estatico())
    partes.append("</div>")
    partes.append("</div>")
    partes.append('<div class="hero-velo"></div>')
    partes.append('<div class="hero-ui">')
    partes.append(f'<p class="destacado">{build_html._esc(_KICKER)}</p>')
    partes.append(f"<h1>{build_html._esc(titulo)}</h1>")
    partes.append(f"<p>{build_html._esc(_LEDE)}</p>")
    partes.append(f'<p class="hero-ayuda">{build_html._esc(_HERO_AYUDA)}</p>')
    _zonas_tactiles_hero(partes)
    partes.append("</div>")
    partes.append('<div class="hero-borde"></div>')
    partes.append("</section>")


def _mundo_hero(partes: list[str]) -> None:
    """Punto de insercion del Mundo_Hero, primer hijo de `.hero`.

    `mundo_hero.py` es la pieza del bloque 8 de esta ampliacion y **todavia no
    existe**. El import es diferido y la ausencia degrada limpiamente: sin el
    modulo el hero queda exactamente como estaba (visor 3D, velo, interfaz de
    vidrio y filo), con las siete capas y los 13 elementos congelados intactos
    (criterios 6.7 y 6.9). En cuanto el modulo aparezca, sus capas se pintan aqui,
    **antes** de `.hero-visor`, que es lo que las deja detras del modelo dentro
    del mismo plano `z-index:0`.
    """
    try:
        from . import mundo_hero
    except ImportError:
        return
    render = getattr(mundo_hero, "render_mundo", None)
    if render is None:
        return
    render(partes)


def _zonas_tactiles_hero(partes: list[str]) -> None:
    """Las dos Zona_Tactil del hero: "Empezar" (19.2) y "Activar movimiento" (9.10).

    "Empezar" es un enlace de ancla al indice de la guia: funciona sin JavaScript.
    "Activar movimiento" es un `<button type="button">`, inerte mientras el
    Script_Unico no le engancha el permiso de orientacion; su ausencia no rompe
    nada porque el parallax de desplazamiento y las animaciones CSS siguen
    (criterio 9.12).
    """
    partes.append('<p class="hero-acciones">')
    partes.append(
        f'<a class="{secciones_guia.CLASE_TACTIL} hero-empezar" '
        f'href="#{secciones_guia.ANCLA_INDICE}">'
        f"{build_html._esc(_TEXTO_EMPEZAR)}</a>"
    )
    partes.append(
        f'<button type="button" class="{secciones_guia.CLASE_TACTIL} '
        f'hero-movimiento" id="{_ID_MOVIMIENTO}">'
        f"{build_html._esc(_TEXTO_MOVIMIENTO)}</button>"
    )
    partes.append("</p>")


def _nav(partes: list[str]) -> None:
    """Navegacion en pagina (enlaces `#ancla`, sin JS), ultimo hijo de `<main>`.

    Se emite al final del cuerpo para que la regla `position:sticky;bottom:0` del
    criterio 15.20 la ancle al borde inferior en pantallas angostas. Ninguna
    prueba vigente afirma su posicion ni la cadena de su regla.

    Anade los enlaces a `anatomia-base`, `tecnica-en-imagenes` y `creditos`
    (criterios 3.7 y 18.7) sin quitar ninguno de los cuatro que ya tenia.
    """
    partes.append('<nav class="sitio">')
    partes.append(f'<a href="#{_ANCLA_TOPE}">Indice</a>')
    for ancla, texto in secciones_guia.enlaces_navegacion():
        partes.append(
            f'<a href="#{build_html._esc(ancla)}">{build_html._esc(texto)}</a>'
        )
    partes.append(f'<a href="#{_ANCLA_DESCARGAS}">Descargas</a>')
    partes.append('<a href="#plan-12-semanas">Periodizacion</a>')
    partes.append(f'<a href="#{_ANCLA_APENDICE}">Enlaces</a>')
    partes.append("</nav>")


def _acciones_header(partes: list[str]) -> None:
    """Dos botones principales del header con enlaces RELATIVOS (Req 13.2).

    `.btn-solid` (magenta) descarga la guia (`guia.pdf`) y `.btn-outline`
    descarga las laminas (`laminas.pdf`); ambos con el atributo `download` y
    rutas relativas al mismo `dist/` que este `index.html`. Sin JavaScript ni
    recursos externos.
    """
    partes.append('<div class="acciones">')
    partes.append(
        f'<a class="btn-solid" href="{build_html._esc(_HREF_GUIA_PDF)}" '
        "download>Descargar la guia (PDF)</a>"
    )
    partes.append(
        f'<a class="btn-outline" href="{build_html._esc(_HREF_LAMINAS_PDF)}" '
        "download>Laminas para WhatsApp (PDF)</a>"
    )
    partes.append("</div>")


def _descargas(partes: list[str]) -> None:
    """Bloque de descargas con los tres artefactos (Req 13.1).

    Enlaces RELATIVOS a `guia.pdf`, `laminas.pdf` (ambos en el mismo `dist/`) y
    al Catalogo_JSON crudo `ejercicios.json` (que el build copia a `dist/`). Los
    dos PDF usan `download`; el JSON crudo se ofrece tambien como descarga. Todo
    funciona sin JavaScript ni recursos externos.
    """
    partes.append(f'<h2 id="{_ANCLA_DESCARGAS}">Descargas</h2>')
    partes.append(
        "<p>Baja la guia completa, las laminas para WhatsApp y el catalogo "
        "crudo de ejercicios en un solo lugar.</p>"
    )
    partes.append('<ul class="descargas">')
    partes.append(
        f'<li><a href="{build_html._esc(_HREF_GUIA_PDF)}" download>'
        "Guia completa (guia.pdf)</a></li>"
    )
    partes.append(
        f'<li><a href="{build_html._esc(_HREF_LAMINAS_PDF)}" download>'
        "Laminas verticales (laminas.pdf)</a></li>"
    )
    partes.append(
        f'<li><a href="{build_html._esc(_HREF_JSON)}" download>'
        "Catalogo crudo (ejercicios.json)</a></li>"
    )
    partes.append("</ul>")


def _indice(fichas: list[dict[str, Any]], partes: list[str]) -> None:
    """Indice del plan de secciones y de las fichas, con enlaces de ancla.

    Primero una Zona_Tactil por seccion del plan (criterio 19.3) y luego la
    rejilla de tarjetas de las fichas, que ya estaba. La `<section>` lleva el
    ancla `indice-guia`, que es la segunda del plan (criterio 19.1).
    """
    partes.append(
        f'<section class="indice-guia" id="{secciones_guia.ANCLA_INDICE}">'
    )
    partes.append(
        f"<h2>{build_html._esc(secciones_guia.titulo_de(secciones_guia.ANCLA_INDICE))}</h2>"
    )
    secciones_guia.render_indice_secciones(partes)
    partes.append("</section>")
    partes.append("<h2>Indice de ejercicios</h2>")
    partes.append('<ul class="indice-capitulos">')
    for ficha in fichas:
        fid = ficha["id"]
        etiqueta = f"{ficha['numero']}. {ficha['titulo']}"
        partes.append(
            f'<li data-indice-de="{build_html._esc(fid)}">'
            f'<a href="#ficha-{build_html._esc(fid)}">'
            f"{build_html._esc(etiqueta)}</a></li>"
        )
    partes.append("</ul>")


def _valores_unicos(fichas: list[dict[str, Any]], campo: str) -> list[str]:
    """Valores distintos de `campo` en orden de aparicion (para poblar los select)."""
    vistos: dict[str, None] = {}
    for ficha in fichas:
        valor = ficha.get(campo)
        if isinstance(valor, str) and valor and valor not in vistos:
            vistos[valor] = None
    return list(vistos.keys())


def _estilo_buscador(partes: list[str]) -> None:
    """CSS minimo funcional del buscador y del ocultamiento (estetica CONGELADA).

    No redefine la paleta ni los tokens: **reutiliza** las variables ya
    declaradas por `build_html.estilo_css()` (`--borde`, `--vidrio`, `--texto`,
    `--texto-atenuado`, `--radio`). Solo aporta la disposicion de los controles y
    la regla `[hidden]` que oculta/muestra fichas al filtrar. Sin este bloque
    (sin JS) nada se oculta y todas las fichas se ven.
    """
    partes.append("<style>")
    partes.append(
        ".buscador{display:flex;flex-wrap:wrap;gap:0.75rem;align-items:end;"
        "margin:1.75rem 0;}"
        ".buscador .campo{display:flex;flex-direction:column;gap:0.3rem;"
        "flex:1 1 12rem;}"
        ".buscador label{font-size:0.8em;color:var(--texto-atenuado);"
        "text-transform:uppercase;letter-spacing:0.06em;}"
        ".buscador input,.buscador select{font:inherit;color:var(--texto);"
        "padding:0.6rem 0.8rem;border-radius:var(--radio);"
        "border:1px solid var(--borde);background:var(--vidrio);}"
        "[hidden]{display:none !important;}"
    )
    # Botones principales del header (`.btn-solid` magenta + `.btn-outline`) y
    # bloque de descargas (Req 13.1, 13.2). No redefine la paleta: reutiliza las
    # variables ya declaradas por `build_html.estilo_css()` (`--magenta`,
    # `--coral`, `--vidrio`, `--borde`, `--texto`, `--radio`).
    partes.append(
        ".acciones{display:flex;flex-wrap:wrap;gap:0.75rem;margin:0 0 1.75rem;}"
        ".btn-solid,.btn-outline{display:inline-block;padding:0.75rem 1.25rem;"
        "border-radius:var(--radio);font-weight:700;text-decoration:none;"
        "border:1px solid var(--magenta);"
        "transition:transform .2s ease,background .2s ease,color .2s ease;}"
        ".btn-solid{background:var(--magenta);color:#fff;}"
        ".btn-solid:hover{transform:translateY(-2px);color:#fff;"
        "border-color:var(--magenta);}"
        ".btn-outline{background:transparent;color:var(--magenta);}"
        ".btn-outline:hover{transform:translateY(-2px);background:var(--vidrio);"
        "color:#fff;border-color:var(--coral);}"
        ".descargas{list-style:none;padding:0;margin:1.25rem 0;display:flex;"
        "flex-wrap:wrap;gap:0.75rem;}"
        ".descargas li{margin:0;}"
        ".descargas a{display:inline-block;padding:0.6rem 1rem;"
        "border-radius:var(--radio);background:var(--vidrio);"
        "border:1px solid var(--borde);color:var(--texto);font-weight:600;}"
        ".descargas a:hover{border-color:var(--magenta);color:#fff;}"
    )
    partes.append("</style>")


def _buscador(fichas: list[dict[str, Any]], partes: list[str]) -> None:
    """Buscador por texto + filtros por categoria y nivel (mejora progresiva).

    Se emite como formulario inerte: sin JS los controles no filtran nada y las
    fichas se ven completas. El `<script>` de `_script` engancha los eventos.
    """
    categorias = _valores_unicos(fichas, "categoria")
    niveles = _valores_unicos(fichas, "nivel")

    partes.append('<section class="buscador" aria-label="Buscar y filtrar fichas">')

    partes.append('<div class="campo">')
    partes.append(f'<label for="{_ID_BUSCAR}">Buscar</label>')
    partes.append(
        f'<input type="search" id="{_ID_BUSCAR}" autocomplete="off" '
        'placeholder="Palabra, equipo, objetivo...">'
    )
    partes.append("</div>")

    partes.append('<div class="campo">')
    partes.append(f'<label for="{_ID_CATEGORIA}">Categoria</label>')
    partes.append(f'<select id="{_ID_CATEGORIA}">')
    partes.append('<option value="">Todas</option>')
    for categoria in categorias:
        partes.append(
            f'<option value="{build_html._esc(categoria)}">'
            f"{build_html._esc(categoria)}</option>"
        )
    partes.append("</select>")
    partes.append("</div>")

    partes.append('<div class="campo">')
    partes.append(f'<label for="{_ID_NIVEL}">Nivel</label>')
    partes.append(f'<select id="{_ID_NIVEL}">')
    partes.append('<option value="">Todos</option>')
    for nivel in niveles:
        partes.append(
            f'<option value="{build_html._esc(nivel)}">'
            f"{build_html._esc(nivel)}</option>"
        )
    partes.append("</select>")
    partes.append("</div>")

    partes.append("</section>")

    # Mensaje "sin resultados": arranca oculto (`hidden`), asi sin JS nunca aparece.
    partes.append(
        f'<p id="{_ID_VACIO}" hidden>No hay fichas que coincidan con la busqueda.</p>'
    )


def _js_hero_visor() -> str:
    """Pieza del visor 3D del Script_Unico: malla, proyeccion y dibujado.

    Es el codigo que antes vivia en `_js_visor()`, con **dos** cambios y ninguno
    mas:

    * El visor ya no aborta el script entero cuando falta el `<canvas>` o el
      contexto 2D: se queda con `ctx` en nulo y el Mundo_Hero, el
      Conmutador_Vista y el Arrastre_Rotacion siguen vivos. Antes el `return`
      temprano se llevaba por delante todo lo que viniera detras.
    * El bucle y los escuchadores salen de aqui: viven en `_js_hero_bucle()` y en
      `_js_hero_entradas()`, porque el bucle es **uno solo** y lo comparten el
      visor, el Mundo_Hero, el Conmutador_Vista y el Arrastre_Rotacion
      (criterios 10.5, 10.17 y 29.1).

    Tecnica, sin cambios: Canvas 2D, matrices de giro propias (yaw/pitch),
    proyeccion en perspectiva, cubetas de profundidad preasignadas para que las
    aristas del fondo salgan mas apagadas y escalado por `devicePixelRatio` via
    `ctx.setTransform`.
    """
    datos = escena3d.datos_json()
    azul = paleta.WEB_AZUL_CLARO
    return (
        "var cv=document.getElementById('" + _ID_LIENZO + "');"
        "var visor=document.getElementById('" + _ID_VISOR + "');"
        "var reserva=document.getElementById('" + _ID_RESERVA + "');"
        "var ctx=(cv&&visor&&cv.getContext)?cv.getContext('2d'):null;"
        "var M=" + datos + ";"
        "var AZUL='" + azul + "';"
        "var TOPE_DPR=2.5;var DIST=3.4;var FOCO=2.2;var BANDAS=5;"
        "var PITCH0=0.2;var GIRO=0.22;var TAU=6.283185;"
        "var nv=(M.v.length/3)|0;var na=(M.a.length/2)|0;var NG=M.g.length;"
        "var Flo=(typeof Float32Array==='function')?Float32Array:Array;"
        "var Ent=(typeof Int32Array==='function')?Int32Array:Array;"
        # Malla en arreglos tipados: se copia una vez, nunca por fotograma.
        "var vx=new Flo(nv),vy=new Flo(nv),vz=new Flo(nv);"
        "for(var i=0;i<nv;i++){vx[i]=M.v[i*3];vy[i]=M.v[i*3+1];vz[i]=M.v[i*3+2];}"
        "var px=new Flo(nv),py=new Flo(nv),pz=new Flo(nv);"
        "var ai=new Ent(na),aj=new Ent(na),ag=new Ent(na);"
        "for(var e=0;e<na;e++){ai[e]=M.a[e*2];aj[e]=M.a[e*2+1];}"
        "var gGrosor=new Flo(NG),gBrillo=new Flo(NG);"
        "for(var g=0;g<NG;g++){var fila=M.g[g];"
        "gGrosor[g]=fila[5];gBrillo[g]=fila[6];"
        "for(var k=fila[3];k<fila[4];k++){ag[k]=g;}}"
        # Una cubeta por banda de profundidad y grupo, preasignada: el bucle de
        # dibujo no crea ni un objeto.
        "var NC=BANDAS*NG;var cubeta=[];var cuenta=new Ent(NC);"
        "for(var b=0;b<NC;b++){cubeta.push(new Ent(na));}"
        "var yaw=-0.62,pitch=PITCH0,zoom=1;"
        "var yawGiro=-0.62,desvioX=0,desvioY=0,zoomMeta=1;"
        "var ancho=0,alto=0,dpr=1,remedir=true,sucio=true;"
        "var rafId=0,previo=0,enPantalla=true,tocando=false;"
        "var reducido=false;"
        "if(window.matchMedia){"
        "reducido=!!window.matchMedia('(prefers-reduced-motion: reduce)').matches;}"
        # Medicion: solo cuando la caja cambia de tamano, no cada fotograma. Vive
        # fuera del bucle a proposito: el cuerpo de `bucle` no lee geometria.
        "function medir(){"
        "if(!visor||!ctx){remedir=false;return;}"
        "var caja=visor.getBoundingClientRect();"
        "var w=Math.max(1,Math.round(caja.width));"
        "var h=Math.max(1,Math.round(caja.height));"
        "var d=window.devicePixelRatio||1;"
        "if(d>TOPE_DPR){d=TOPE_DPR;}"
        "ancho=w;alto=h;dpr=d;"
        "cv.width=Math.round(w*d);cv.height=Math.round(h*d);"
        "ctx.setTransform(d,0,0,d,0,0);"
        "remedir=false;}"
        "function proyectar(){"
        "var cy=Math.cos(yaw),sy=Math.sin(yaw);"
        "var cp=Math.cos(pitch),sp=Math.sin(pitch);"
        "var esc=Math.min(ancho,alto)*0.44*zoom;"
        "var ox=ancho*0.5,oy=alto*0.5;"
        "for(var i=0;i<nv;i++){"
        "var x=vx[i],y=vy[i],z=vz[i];"
        "var x1=x*cy+z*sy;var z1=z*cy-x*sy;"
        "var y1=y*cp-z1*sp;var z2=z1*cp+y*sp;"
        "var lej=DIST+z2;if(lej<0.25){lej=0.25;}"
        "var f=esc*FOCO/lej;"
        "px[i]=ox+x1*f;py[i]=oy-y1*f;pz[i]=z2;}}"
        "function dibujar(){"
        "if(!ctx){return;}"
        "if(remedir){medir();}"
        "proyectar();"
        "ctx.clearRect(0,0,ancho,alto);"
        "for(var c=0;c<NC;c++){cuenta[c]=0;}"
        "var lo=1e9,hi=-1e9;"
        "for(var e=0;e<na;e++){"
        "var m=(pz[ai[e]]+pz[aj[e]])*0.5;"
        "if(m<lo){lo=m;}if(m>hi){hi=m;}}"
        "var rango=hi-lo;if(rango<1e-6){rango=1;}"
        "for(var e2=0;e2<na;e2++){"
        "var m2=(pz[ai[e2]]+pz[aj[e2]])*0.5;"
        "var bd=Math.floor((m2-lo)/rango*BANDAS);"
        "if(bd<0){bd=0;}if(bd>=BANDAS){bd=BANDAS-1;}"
        "var ic=bd*NG+ag[e2];"
        "cubeta[ic][cuenta[ic]++]=e2;}"
        "ctx.lineCap='round';ctx.lineJoin='round';"
        "ctx.strokeStyle=AZUL;ctx.shadowColor=AZUL;"
        # De la banda mas lejana a la mas cercana: el fondo queda apagado y sin
        # halo, y el frente brillante y con halo.
        "for(var bb=0;bb<BANDAS;bb++){"
        "var t=(bb+0.5)/BANDAS;"
        "for(var gg=0;gg<NG;gg++){"
        "var idx=bb*NG+gg;var cn=cuenta[idx];"
        "if(cn===0){continue;}"
        "var alfa=(0.13+t*0.87)*gBrillo[gg];"
        "if(alfa>1){alfa=1;}"
        "ctx.globalAlpha=alfa;"
        "ctx.lineWidth=(0.5+t*1.3)*gGrosor[gg];"
        "ctx.shadowBlur=(bb>=BANDAS-2)?9*gBrillo[gg]:0;"
        "ctx.beginPath();"
        "var lista=cubeta[idx];"
        "for(var q=0;q<cn;q++){var ee=lista[q];"
        "ctx.moveTo(px[ai[ee]],py[ai[ee]]);"
        "ctx.lineTo(px[aj[ee]],py[aj[ee]]);}"
        "ctx.stroke();}}"
        "ctx.globalAlpha=1;ctx.shadowBlur=0;}"
        # Escritorio: el modelo sigue al cursor con suavizado exponencial.
        "function parallax(ev){"
        "if(reducido||tocando){return;}"
        "var caja=visor.getBoundingClientRect();"
        "if(!caja.width||!caja.height){return;}"
        "var rx=(ev.clientX-caja.left)/caja.width-0.5;"
        "var ry=(ev.clientY-caja.top)/caja.height-0.5;"
        "desvioX=rx*0.9;desvioY=-ry*0.5;}"
        "function reposo(){desvioX=0;desvioY=0;}"
        "function separacion(ts){"
        "var dx=ts[0].clientX-ts[1].clientX;"
        "var dy=ts[0].clientY-ts[1].clientY;"
        "return Math.sqrt(dx*dx+dy*dy);}"
        "var t0x=0,t0y=0,pinza=0,zoom0=1;"
        "function alTocar(ev){"
        "var ts=ev.touches;if(!ts){return;}"
        "tocando=true;"
        "if(ts.length>1){pinza=separacion(ts);zoom0=zoomMeta;}"
        "else{t0x=ts[0].clientX;t0y=ts[0].clientY;}"
        "arrancar();}"
        "function alMover(ev){"
        "var ts=ev.touches;if(!ts){return;}"
        "if(ts.length>1){"
        # Con dos dedos, y SOLO con dos, se toma el control del gesto: es el
        # unico caso en que se llama a preventDefault, para no secuestrar el
        # desplazamiento vertical de la pagina.
        "ev.preventDefault();"
        "if(pinza>0){"
        "var z=zoom0*(separacion(ts)/pinza);"
        "if(z<0.7){z=0.7;}if(z>2.4){z=2.4;}"
        "zoomMeta=z;}"
        "return;}"
        "var dx=ts[0].clientX-t0x;var dy=ts[0].clientY-t0y;"
        "t0x=ts[0].clientX;t0y=ts[0].clientY;"
        "yawGiro+=dx*0.008;"
        "var p=desvioY-dy*0.004;"
        "if(p>0.5){p=0.5;}if(p<-0.4){p=-0.4;}"
        "desvioY=p;}"
        "function alSoltar(ev){"
        "var ts=ev.touches;"
        "if(!ts||ts.length===0){tocando=false;pinza=0;}}"
    )


def _js_hero_mundo() -> str:
    """Pieza del Mundo_Hero: sus capas, el Progreso_Scroll y `aplicarMundo()`.

    `MUNDO` es el literal JSON de `mundo_hero.datos_json()`: el **unico** puente
    hacia Python. Ninguna constante se repite aqui a mano (criterios 8.2 y 10.10).

    `aplicarMundo()` es el presupuesto de escrituras del criterio 10.13 escrito
    tal cual: **una** asignacion a `style.transform`, **una** a `style.opacity` y
    **una** a `style.willChange` por capa y por fotograma, y ninguna lectura de
    geometria. `window.innerHeight` no es una lectura de geometria de nodo: es el
    tamano de la ventana, y es lo que el Progreso_Scroll necesita (criterio 8.4).

    `will-change` vuelve a `auto` en cuanto la opacidad llega a 0 (criterio 10.7),
    y con Movimiento_Reducido se omite toda escritura de `transform` y de
    `opacity` (criterio 11.5).
    """
    ids_capa: str = ",".join(f"'{mh.id_de_capa(capa)}'" for capa in mh.CAPAS)
    return (
        "var MUNDO=" + mh.datos_json() + ";"
        "var CL_VISTA='" + vf.CLASE_VISTA + "';"
        "var CL_ACTIVA='" + vf.CLASE_ACTIVA + "';"
        "var CL_GIRABLE='" + vf.CLASE_GIRABLE + "';"
        "var CL_INERTE='" + mh.CLASE_INERTE + "';"
        "var CL_OBJETO='" + mh.CLASE_OBJETO + "';"
        "var CL_BALON='" + mh.CLASE_BALON + "';"
        "var CL_VISOR='" + secciones_guia.CLASE_VISOR + "';"
        "var SEL_ANIMADAS='.hero,.'+CL_VISOR;"
        "var hero=document.getElementById('" + secciones_guia.ANCLA_HERO + "');"
        "var mundo=document.getElementById('" + mh.ID_MUNDO + "');"
        "var capas=[];"
        "var idsCapa=[" + ids_capa + "];"
        "for(var ci=0;ci<idsCapa.length;ci++){"
        "var nodoCapa=document.getElementById(idsCapa[ci]);"
        "if(nodoCapa){capas.push(nodoCapa);}}"
        # Los Elemento_Fondo, con su opacidad declarada guardada aparte: la
        # degradacion de pantalla angosta la restaura sin volver a calcularla.
        "var objetos=[],marcados=[],resto=[];"
        "if(mundo){"
        "var crudos=mundo.querySelectorAll('.'+CL_OBJETO);"
        "for(var oi=0;oi<crudos.length;oi++){"
        "var nd=crudos[oi];"
        "var filaObj={nodo:nd,id:nd.getAttribute('data-id'),"
        "tipo:nd.getAttribute('data-tipo'),base:nd.style.opacity,"
        "x:parseFloat(nd.style.left),y:parseFloat(nd.style.top),"
        "marcado:nd.getAttribute('data-angosto')==='1'};"
        "if(filaObj.marcado){marcados.push(filaObj);}else{resto.push(filaObj);}}"
        "objetos=marcados.concat(resto);}"
        "var scrollActual=0,curX=0,curY=0,curMetaX=0,curMetaY=0;"
        "var angosto=null,inerteActivo=false,visible={};"
        "function acotar(v,lo,hi){"
        "if(v<lo){return lo;}if(v>hi){return hi;}return v;}"
        "function progresoHero(){"
        "var h=window.innerHeight||0;"
        "if(h<=0){return 0;}"
        "return acotar(scrollActual/h,0,1);}"
        "function aplicarMundo(){"
        "if(!mundo){return;}"
        "var p=progresoHero();"
        "var op=1-p;if(op<0){op=0;}"
        "var frio=(op===0);"
        "if(frio!==inerteActivo){inerteActivo=frio;"
        "if(frio){mundo.classList.add(CL_INERTE);}"
        "else{mundo.classList.remove(CL_INERTE);}}"
        "for(var i=0;i<capas.length;i++){"
        "var c=capas[i];"
        "c.style.willChange=frio?'auto':'transform';"
        "if(frio||reducido){continue;}"
        "var ty=-scrollActual*MUNDO.f[i]+curY;"
        "var es=1+(MUNDO.e[i]-1)*p;"
        "c.style.transform='translate3d('+curX.toFixed(2)+'px,'+ty.toFixed(2)+"
        "'px,'+MUNDO.z[i]+'px) scale('+es.toFixed(4)+')';"
        "c.style.opacity=op.toFixed(3);}}"
    )


def _js_hero_toque() -> str:
    """Entradas del Mundo_Hero: cursor, toque del hero y permiso de orientacion.

    Tres piezas, cada una con su criterio:

    * **Cursor** (9.4, 9.5, 9.6): el objetivo es el signo **opuesto** al del
      cursor, acotado a `MUNDO.tope` por eje, y `suavizarCursor()` lo persigue con
      el coeficiente `MUNDO.k` dentro del bucle. Al salir del hero el objetivo
      pasa a `(0, 0)` y la misma interpolacion devuelve el fondo al centro.
    * **Toque** (9.8, 9.9, 28.1): el escuchador vive en el **contenedor** `.hero`,
      nunca en un Elemento_Fondo, asi que `pointer-events:none` del Mundo_Hero
      queda intacto. Resuelve el blanco mas cercano dentro de `MUNDO.radio` con
      las coordenadas declaradas de `MUNDO.balones` y las de las Figura_Girable
      de `MUNDO.figuras`, y le aplica el rebote durante `MUNDO.rebote` mas el
      Giro_Impulso de `MUNDO.girarMs`.
    * **Permiso** (9.11, 9.12, 28.20): `DeviceOrientationEvent.requestPermission`
      se pide en **un solo lugar**, el manejador de la Zona_Tactil "Activar
      movimiento". Ninguna guarda de ese permiso envuelve el parallax de scroll,
      la flotacion, el giro ni el Arrastre_Rotacion: si se deniega, lo unico que
      no llega es el desvio por giroscopio.

    El rebote se escribe sobre el nodo que **no** lleva animacion CSS de
    `transform`: el `<svg class="balon-esfera">` en los balones (la vuelta la
    anima su envoltorio `.hero-giro`) y el `<div class="figura-girable">` en las
    siluetas. Asi una asignacion en linea sin `!important` gana limpiamente, y la
    unica propiedad escrita sigue siendo `transform`.
    """
    return (
        "var golpeNodo=null,golpeT0=0,golpeVivo=false,impFig=-1,impT0=0;"
        "var blancos=[];"
        "function objetoDe(id){"
        "for(var bo=0;bo<objetos.length;bo++){"
        "if(objetos[bo].id===id){return objetos[bo];}}"
        "return null;}"
        "function primerHijo(nodo,clase){"
        "if(!nodo){return null;}"
        "var hallados=nodo.querySelectorAll('.'+clase);"
        "return hallados.length?hallados[0]:null;}"
        "for(var bi=0;bi<MUNDO.balones.length;bi++){"
        "var filaBal=MUNDO.balones[bi];"
        "var objBal=objetoDe(filaBal[0]);"
        "if(objBal){blancos.push({x:filaBal[1],y:filaBal[2],"
        "nodo:primerHijo(objBal.nodo,CL_BALON)||objBal.nodo,fig:-1});}}"
        "for(var fi=0;fi<MUNDO.figuras.length;fi++){"
        "var filaFig=MUNDO.figuras[fi];"
        "var objFig=objetoDe(filaFig[0]);"
        "if(objFig){blancos.push({x:objFig.x,y:objFig.y,"
        "nodo:primerHijo(objFig.nodo,CL_GIRABLE)||objFig.nodo,fig:fi});}}"
        "function alMoverCursor(ev){"
        "var w=window.innerWidth||1,h=window.innerHeight||1;"
        "var rx=(ev.clientX/w-0.5)*2;"
        "var ry=(ev.clientY/h-0.5)*2;"
        "curMetaX=acotar(-rx*MUNDO.tope,-MUNDO.tope,MUNDO.tope);"
        "curMetaY=acotar(-ry*MUNDO.tope,-MUNDO.tope,MUNDO.tope);}"
        "function alSalirCursor(){curMetaX=0;curMetaY=0;}"
        "function suavizarCursor(){"
        "var mx=angosto?0:curMetaX;"
        "var my=angosto?0:curMetaY;"
        "curX+=(mx-curX)*MUNDO.k;"
        "curY+=(my-curY)*MUNDO.k;}"
        "function alTocarHero(ev){"
        "if(!hero){return;}"
        "var ts=ev.touches;if(!ts||!ts.length){return;}"
        "var caja=hero.getBoundingClientRect();"
        "if(!caja.width||!caja.height){return;}"
        "var xp=(ts[0].clientX-caja.left)/caja.width*100;"
        "var yp=(ts[0].clientY-caja.top)/caja.height*100;"
        "var mejor=null,menor=MUNDO.radio;"
        "for(var ib=0;ib<blancos.length;ib++){"
        "var bl=blancos[ib];"
        "var dd=Math.sqrt((xp-bl.x)*(xp-bl.x)+(yp-bl.y)*(yp-bl.y));"
        "if(dd<menor){menor=dd;mejor=bl;}}"
        "if(!mejor){return;}"
        "golpeNodo=mejor.nodo;golpeT0=reloj();golpeVivo=false;"
        "impFig=mejor.fig;impT0=golpeT0;"
        "arrancar();}"
        "function aplicarGolpe(t){"
        "if(!golpeNodo){return;}"
        "var e=(t-golpeT0)/MUNDO.rebote;"
        "if(e<0||e>=1){"
        "if(golpeVivo){golpeNodo.style.transform='';golpeVivo=false;}"
        "golpeNodo=null;return;}"
        "golpeVivo=true;"
        "var esc=(1+0.18*Math.sin(e*Math.PI)).toFixed(4);"
        "golpeNodo.style.transform='scale('+esc+')';}"
        "function alGirarDispositivo(ev){"
        "var gam=ev.gamma||0,bet=ev.beta||0;"
        "curMetaX=acotar(-gam/45*MUNDO.tope,-MUNDO.tope,MUNDO.tope);"
        "curMetaY=acotar(-(bet-45)/45*MUNDO.tope,-MUNDO.tope,MUNDO.tope);}"
        "function escucharOrientacion(){"
        "window.addEventListener('deviceorientation',alGirarDispositivo,"
        "{passive:true});}"
        "function activarMovimiento(){"
        "var DOE=window.DeviceOrientationEvent;"
        "if(!DOE){return;}"
        "if(typeof DOE.requestPermission==='function'){"
        "DOE.requestPermission().then(function(estado){"
        "if(estado==='granted'){escucharOrientacion();}},function(){});"
        "return;}"
        "escucharOrientacion();}"
    )


def _js_hero_angosto() -> str:
    """Degradacion en pantallas angostas y tabla de azimuts del Conmutador_Vista.

    Dos reducciones y **ninguna** mas (criterios 12.5, 12.8 y 29.6):

    * El numero de Elemento_Fondo activos: bajo `MUNDO.corte` sobreviven los
      marcados `data-angosto="1"` hasta `MUNDO.maxA`, y si no llegaran a
      `MUNDO.minA` se rellenan con los demas. Se ocultan con `opacity` y
      `visibility`, jamas con `display` (criterios 12.1 y 27.9), y la opacidad
      declarada se restaura desde el valor que se guardo al arrancar.
    * El numero de Clave_Vista candidatas: bajo el mismo corte el
      Conmutador_Vista solo considera los seis azimuts de `MUNDO.azMovil`
      (criterios 12.7, 29.5). Las Vista_Elevacion siguen alcanzables por
      Arrastre_Rotacion, que es gesto de la usuaria y no giro automatico.

    El parallax de tres capas, su escala y su desvanecimiento por Progreso_Scroll
    siguen intactos (criterio 12.3), y el contenido y las dimensiones de los ocho
    Diagrama_Postura no se tocan: aqui no se escribe sobre ninguno.

    La tabla de azimuts se deriva de `MUNDO.vistas`: la clave `az-045` da el
    azimut 45 y la clave `el-p60` da la elevacion tope 60. El JavaScript no
    escribe ni un numero de esos a mano.
    """
    return (
        "function aplicarAngosto(){"
        "var ang=(window.innerWidth||0)<MUNDO.corte;"
        "if(ang===angosto){return;}"
        "angosto=ang;"
        "var vivos=0;"
        "for(var ia=0;ia<objetos.length;ia++){"
        "var ob=objetos[ia];"
        "var vive=true;"
        "if(ang){"
        "vive=ob.marcado?(vivos<MUNDO.maxA):(vivos<MUNDO.minA);"
        "if(vive){vivos++;}}"
        "ob.nodo.style.opacity=vive?ob.base:'0';"
        "ob.nodo.style.visibility=vive?'visible':'hidden';}}"
        "var azimuts=[],idxAz=[],iAlta=-1,iBaja=-1,topeEl=0;"
        "for(var vi=0;vi<MUNDO.vistas.length;vi++){"
        "var clave=MUNDO.vistas[vi];"
        "if(clave.charAt(0)==='a'){"
        "azimuts.push(parseInt(clave.substring(3),10));idxAz.push(vi);}"
        "else if(clave.charAt(3)==='p'){"
        "iAlta=vi;topeEl=parseInt(clave.substring(4),10);}"
        "else{iBaja=vi;}}"
        "function esMovil(az){"
        "for(var im=0;im<MUNDO.azMovil.length;im++){"
        "if(MUNDO.azMovil[im]===az){return true;}}"
        "return false;}"
        "function distCircular(a,az){"
        "var d=Math.abs(a-az)%360;"
        "return d>180?360-d:d;}"
        "function normalizar(d){"
        "return ((d+180)%360+360)%360-180;}"
        # Empate al azimut declarado MENOR: `azimuts` va en orden creciente y la
        # comparacion es estricta, asi que a 22.5 grados exactos gana az-000.
        "function indiceMasCercano(a){"
        "var mejor=-1,dmin=1e9;"
        "for(var ic=0;ic<azimuts.length;ic++){"
        "if(angosto&&!esMovil(azimuts[ic])){continue;}"
        "var d=distCircular(a,azimuts[ic]);"
        "if(d<dmin-1e-9){dmin=d;mejor=ic;}}"
        "return mejor<0?0:idxAz[mejor];}"
        "function azimutDe(indice){"
        "for(var iz=0;iz<idxAz.length;iz++){"
        "if(idxAz[iz]===indice){return azimuts[iz];}}"
        "return azimuts[0];}"
        "function residual(a,indice){"
        "return acotar(normalizar(a-azimutDe(indice)),"
        "-MUNDO.residual,MUNDO.residual);}"
    )


def _js_hero_vistas() -> str:
    """Conmutador_Vista: una Vista_Activa por Figura_Girable, resuelta por indice.

    Cada Figura_Girable se recoge una sola vez al arrancar, con sus **diez**
    Vista_Figura en una lista estatica. El indice de esa lista **es** el indice de
    `MUNDO.vistas`, asi que la vista se resuelve con un entero y nunca con una
    busqueda en el DOM (criterio 25.6 y la nota de `datos_json`).

    Presupuesto por fotograma y por figura (criterios 25.8, 25.9 y 29.2):

    * Si la Clave_Vista mas cercana **no** cambia, no se escribe **nada** sobre
      las Vista_Figura de esa figura: el `continue` esta antes de toda escritura.
    * Si cambia, se escriben exactamente **una** `transform` (la Rotacion_Residual
      `rotateY`, acotada a `MUNDO.residual`), **dos** `opacity` y **dos**
      `visibility`, y se alterna la clase de Vista_Activa en las dos vistas.

    Cero `innerHTML`, `createElement`, `appendChild`, `removeChild` y compania: el
    numero de nodos de cada figura es el mismo antes y despues (criterios 25.12 y
    25.13).

    El angulo de giro sale del reloj y de la duracion declarada de la figura en
    `MUNDO.figuras`; durante el Giro_Impulso la duracion pasa a `MUNDO.girarMs` y
    al terminar se retoma la declarada (criterios 28.2 y 28.3).

    Arrastre_Rotacion (Requisito 28). El estado son cuatro coordenadas de puntero
    que los escuchadores `{passive:true}` guardan y nada mas; la **resolucion** de
    la vista ocurre aqui, dentro de la unica funcion de bucle (criterio 28.14):

    * azimut `(a0 + dx * MUNDO.dragDeg) mod 360`, en `[0, 360)` (criterio 28.9);
    * elevacion acotada al cerrado `[-topeEl, +topeEl]`, con `topeEl` leido de la
      clave `el-p60` (criterio 28.10);
    * con `|elevacion| >= MUNDO.umbralEl` gana la Vista_Elevacion del signo, y por
      debajo la Vista_Azimut mas cercana con el **mismo** desempate de la
      conmutacion automatica (criterios 28.11 y 28.12);
    * con Movimiento_Reducido el giro automatico se detiene y el arrastre sigue
      respondiendo (criterio 28.18).
    """
    return (
        "var girables=[];"
        "var contGirables=document.querySelectorAll('.'+CL_GIRABLE);"
        "for(var gi=0;gi<contGirables.length;gi++){"
        "var cont=contGirables[gi];"
        "var vistas=cont.querySelectorAll('.'+CL_VISTA);"
        "if(!vistas.length){continue;}"
        "var idFig=cont.getAttribute('data-figura');"
        "var fila=-1;"
        "for(var fk=0;fk<MUNDO.figuras.length;fk++){"
        "if(MUNDO.figuras[fk][0]===idFig){fila=fk;}}"
        # El overlay del Visor_Ampliado ya no es el padre directo de la
        # Figura_Girable: entre los dos van el cuerpo desplazable y el lienzo con
        # relacion de aspecto. Se sube por el arbol con `closest`, que resuelve el
        # ancestro con la clase del visor sin importar cuantas capas haya.
        "var padre=cont.closest?cont.closest('.'+CL_VISOR):null;"
        "var enVisor=!!padre;"
        "girables.push({nodo:cont,vistas:vistas,fila:fila,activa:0,"
        "visor:enVisor,llave:enVisor?(padre.id||''):''});}"
        # Arrastre_Rotacion: el estado son CUATRO coordenadas de puntero y nada
        # mas. `dragX0` en -1 significa "sin arrastre", que es un valor imposible
        # para `clientX`. La figura arrastrable se resuelve al arrancar, no en el
        # manejador: la del Visor_Ampliado, la unica que declara Girable.
        "var iArrastre=-1,dragX0=-1,dragY0=-1,dragX=0,dragY=0;"
        "var dragA0=0,dragE0=0;"
        "for(var ja=0;ja<girables.length;ja++){"
        "if(girables[ja].visor){iArrastre=ja;}}"
        "function arrastrando(indice){"
        "return indice===iArrastre&&dragX0>=0;}"
        "function indiceArrastre(){"
        "var dx=dragX-dragX0,dy=dragY-dragY0;"
        "var az=((dragA0+dx*MUNDO.dragDeg)%360+360)%360;"
        "var el=acotar(dragE0+dy*MUNDO.dragDeg,-topeEl,topeEl);"
        "if(el>=MUNDO.umbralEl&&iAlta>=0){return iAlta;}"
        "if(el<=-MUNDO.umbralEl&&iBaja>=0){return iBaja;}"
        "return indiceMasCercano(az);}"
        "function anguloFigura(fila,t){"
        "if(fila<0){return 0;}"
        "var datos=MUNDO.figuras[fila];"
        "var per=datos[1]*1000;"
        "if(fila===impFig&&(t-impT0)<MUNDO.girarMs){per=MUNDO.girarMs;}"
        "if(per<=0){return 0;}"
        "return ((t/per*360*datos[2])%360+360)%360;}"
        "function aplicarVistas(t){"
        "if(inerteActivo){return;}"
        "for(var ig=0;ig<girables.length;ig++){"
        "var fg=girables[ig];"
        "if(fg.llave&&visible[fg.llave]===false){continue;}"
        "var arr=arrastrando(ig);"
        "if(reducido&&!arr){continue;}"
        "var ang2=anguloFigura(fg.fila,t);"
        "var idx=arr?indiceArrastre():indiceMasCercano(ang2);"
        "if(idx===fg.activa){continue;}"
        "var giro=arr?0:residual(ang2,idx);"
        "var sale=fg.vistas[fg.activa];"
        "var entra=fg.vistas[idx];"
        "sale.style.opacity='0';"
        "sale.style.visibility='hidden';"
        "sale.classList.remove(CL_ACTIVA);"
        "entra.style.transform='rotateY('+giro.toFixed(2)+'deg)';"
        "entra.style.opacity='1';"
        "entra.style.visibility='visible';"
        "entra.classList.add(CL_ACTIVA);"
        "fg.activa=idx;}}"
    )


def _js_hero_bucle() -> str:
    """La **unica** funcion de bucle del Script_Unico (criterios 10.5 y 29.1).

    Contiene la **unica** llamada a `requestAnimationFrame(` de todo el script.
    `arrancar()` no pide un fotograma por su cuenta: llama a `bucle` de forma
    directa, y es `bucle` quien pide el siguiente. Asi la cuenta de llamadas es
    exactamente una y sigue estando dentro de la funcion de bucle.

    Reparto de guardas:

    * `debeParar()` exige hero fuera de la ventana **y** documento oculto
      (criterio 10.8). Con el hero fuera y el documento visible el bucle sigue
      vivo pero no dibuja ni escribe (criterio 10.9).
    * `enPantalla` lo escribe **solo** el `IntersectionObserver` (criterios 10.11,
      10.12 y 10.14): el cuerpo de `bucle` no lee geometria de ningun nodo.
    * Con Movimiento_Reducido el visor no avanza su giro y el Mundo_Hero no recibe
      escrituras; el Arrastre_Rotacion sigue respondiendo (criterios 11.5 y 28.18).
    """
    return (
        "function reloj(t){"
        "if(typeof t==='number'){return t;}"
        "if(window.performance&&performance.now){return performance.now();}"
        "return Date.now();}"
        "function debeParar(){return !enPantalla&&document.hidden;}"
        "function bucle(marca){"
        "rafId=0;"
        "if(debeParar()){return;}"
        "var t=reloj(marca);"
        "var dt=previo?(t-previo)/1000:0.016;"
        "previo=t;"
        "if(dt>0.1){dt=0.1;}if(dt<0){dt=0;}"
        "if(enPantalla){"
        # Movimiento_Reducido: el modelo no avanza su giro y solo se redibuja
        # cuando la caja cambio de tamano. El Mundo_Hero no recibe escritura
        # ninguna (criterio 11.5) y el Arrastre_Rotacion sigue respondiendo.
        "if(reducido){if(sucio){sucio=false;dibujar();}}"
        "else{"
        "if(!tocando){yawGiro+=GIRO*dt;}"
        "if(yawGiro>TAU){yawGiro-=TAU;yaw-=TAU;}"
        "var objY=yawGiro+desvioX;"
        "var objP=PITCH0+desvioY;"
        "if(objP>0.72){objP=0.72;}if(objP<-0.45){objP=-0.45;}"
        "var kk=1-Math.exp(-dt*7);"
        "yaw+=(objY-yaw)*kk;"
        "pitch+=(objP-pitch)*kk;"
        "zoom+=(zoomMeta-zoom)*kk;"
        "dibujar();}"
        "aplicarAngosto();"
        "suavizarCursor();"
        "aplicarMundo();"
        "aplicarVistas(t);"
        "aplicarGolpe(t);}"
        "rafId=requestAnimationFrame(bucle);}"
        "function arrancar(){"
        "if(rafId||debeParar()){return;}"
        "previo=0;bucle(reloj());}"
        "function parar(){"
        "if(rafId){cancelAnimationFrame(rafId);rafId=0;}}"
    )


def _js_hero_entradas() -> str:
    """Escuchadores del Script_Unico y el `IntersectionObserver` de visibilidad.

    El escuchador de desplazamiento es `{passive:true}` y **solo** guarda
    `window.scrollY` (criterios 10.4 y 29.12). El unico `preventDefault` de un
    evento de **toque** sigue siendo el del gesto de dos dedos del visor, que se
    registra con `{passive:false}` por eso mismo; los del overlay modal
    (`_js_hero_modal`) cuelgan de `click` y de `keydown`, que no compiten con el
    desplazamiento.

    El `IntersectionObserver` es la **unica** fuente de visibilidad y observa cada
    seccion animada del documento: el hero y cada Visor_Ampliado (criterios 10.11,
    10.12 y 29.10).
    """
    return (
        "if(cv&&ctx){"
        "cv.addEventListener('touchstart',alTocar,{passive:true});"
        "cv.addEventListener('touchmove',alMover,{passive:false});"
        "cv.addEventListener('touchend',alSoltar,{passive:true});"
        "cv.addEventListener('touchcancel',alSoltar,{passive:true});}"
        "if(visor){"
        "visor.addEventListener('mousemove',parallax,{passive:true});"
        "visor.addEventListener('mouseleave',reposo,{passive:true});}"
        # El toque y el cursor viven en el CONTENEDOR del hero, nunca en un
        # Elemento_Fondo: `pointer-events:none` del Mundo_Hero queda intacto.
        "if(hero){"
        "hero.addEventListener('touchstart',alTocarHero,{passive:true});"
        "hero.addEventListener('mousemove',alMoverCursor,{passive:true});"
        "hero.addEventListener('mouseleave',alSalirCursor,{passive:true});}"
        # El permiso de orientacion se pide en UN SOLO sitio: este manejador.
        "var btnMov=document.getElementById('" + _ID_MOVIMIENTO + "');"
        "if(btnMov){"
        "btnMov.addEventListener('click',activarMovimiento,{passive:true});}"
        # Arrastre_Rotacion: tres manejadores `{passive:true}` que guardan SOLO
        # coordenadas. Ni resuelven la vista ni escriben estilo: eso pasa dentro
        # del bucle. El `touch-action:none` del Visor_Ampliado ya lo declara la
        # Hoja_Estilo, asi que no hace falta un solo `preventDefault`.
        "function alTocarVisor(ev){"
        "var ts=ev.touches;if(!ts||!ts.length){return;}"
        "dragX0=ts[0].clientX;dragY0=ts[0].clientY;"
        "dragX=ts[0].clientX;dragY=ts[0].clientY;}"
        "function alArrastrar(ev){"
        "var ts=ev.touches;if(!ts||!ts.length){return;}"
        "dragX=ts[0].clientX;dragY=ts[0].clientY;}"
        "function alSoltarVisor(){dragX0=-1;dragY0=-1;}"
        "if(iArrastre>=0){"
        "var nodoDrag=girables[iArrastre].nodo;"
        "nodoDrag.addEventListener('touchstart',alTocarVisor,{passive:true});"
        "nodoDrag.addEventListener('touchmove',alArrastrar,{passive:true});"
        "nodoDrag.addEventListener('touchend',alSoltarVisor,{passive:true});"
        "nodoDrag.addEventListener('touchcancel',alSoltarVisor,{passive:true});}"
        "window.addEventListener('scroll',function(){"
        "scrollActual=window.scrollY;},{passive:true});"
        "window.addEventListener('resize',function(){"
        "remedir=true;sucio=true;angosto=null;arrancar();},{passive:true});"
        "window.addEventListener('orientationchange',function(){"
        "remedir=true;sucio=true;angosto=null;arrancar();},{passive:true});"
        "document.addEventListener('visibilitychange',function(){"
        "if(debeParar()){parar();}else{arrancar();}},{passive:true});"
        # Unica fuente de visibilidad: ni una lectura de geometria en el bucle.
        "if(typeof IntersectionObserver==='function'){"
        "var obs=new IntersectionObserver(function(filas){"
        "for(var n=0;n<filas.length;n++){"
        "var f=filas[n];"
        "visible[f.target.id||'']=!!f.isIntersecting;"
        "if(f.target===hero){enPantalla=!!f.isIntersecting;}}"
        "if(debeParar()){parar();}else{arrancar();}},{threshold:0.01});"
        "var animadas=document.querySelectorAll(SEL_ANIMADAS);"
        "for(var si=0;si<animadas.length;si++){obs.observe(animadas[si]);}}"
    )


def _js_hero_modal() -> str:
    """Visor_Ampliado como overlay modal: `abrirModal`, `cerrarModal` y su foco.

    Va DENTRO del `<script>` unico y del mismo cuerpo que el resto del hero: no
    abre un segundo `<script>`, no anade una segunda llamada a
    `requestAnimationFrame(` y no declara ni un bucle mas (criterios 10.5, 13.1 y
    29.1). Tampoco escribe estilo en linea: el bloqueo de desplazamiento del
    `<body>` se hace con una CLASE, porque las unicas propiedades que el
    Script_Unico tiene permitido escribir en linea son `transform`, `opacity`,
    `visibility` y `will-change` (criterio 10.3).

    Lo primero que hace es marcar `<html>` con `CLASE_CON_JS`. Esa clase es la
    bisagra de la mejora progresiva: mientras no exista, el overlay lo destapa el
    selector `:target` y el documento funciona sin JavaScript; en cuanto existe,
    la regla `.con-modal .visor-ampliado[hidden]` manda y la visibilidad la
    gobiernan estas dos funciones.

    Contrato de `abrirModal(overlay, origen)`:

    * guarda `window.scrollY` **antes** de bloquear el `<body>`;
    * quita `hidden` del overlay y pone la clase de bloqueo en el `<body>`;
    * manda el foco a la Zona_Tactil de cierre;
    * enciende el bucle, porque la Figura_Girable del overlay acaba de entrar en
      pantalla y su Conmutador_Vista vive dentro de ese bucle.

    Contrato de `cerrarModal()`: pone `hidden`, quita la clase de bloqueo,
    devuelve el foco al elemento que abrio y restaura la posicion de
    desplazamiento **exacta** que se guardo. El foco se pide con
    `{preventScroll:true}` justamente para que no compita con esa restauracion.

    Tres maneras de cerrar, las tres del Requisito 28: el clic o toque en la
    Zona_Tactil de cierre, la tecla Escape y el toque en el fondo comprobando
    `ev.target===overlay` (o el cuerpo del overlay, que es el resto del velo
    visible en una pantalla angosta). La tabulacion queda atrapada dentro del
    overlay: al llegar al borde de la lista de enfocables se vuelve al otro
    extremo.
    """
    return (
        "var CL_AMPLIAR='" + secciones_guia.CLASE_AMPLIAR + "';"
        "var CL_CERRAR='" + secciones_guia.CLASE_CERRAR + "';"
        "var CL_CUERPO_MODAL='" + secciones_guia.CLASE_CUERPO_VISOR + "';"
        "var CL_CON_JS='" + secciones_guia.CLASE_CON_JS + "';"
        "var CL_FIJO='" + secciones_guia.CLASE_CUERPO_FIJO + "';"
        "var raiz=document.documentElement;"
        "if(raiz&&raiz.classList){raiz.classList.add(CL_CON_JS);}"
        "var modalVivo=null,modalOrigen=null,modalScroll=0;"
        "function cierreDe(ov){"
        "var hallados=ov.querySelectorAll('.'+CL_CERRAR);"
        "return hallados.length?hallados[0]:null;}"
        "function enfocar(nodo){"
        "if(nodo&&nodo.focus){nodo.focus({preventScroll:true});}}"
        "function abrirModal(ov,origen){"
        "if(!ov){return;}"
        "if(modalVivo&&modalVivo!==ov){cerrarModal();}"
        "if(!modalVivo){modalScroll=window.scrollY||0;}"
        "modalVivo=ov;modalOrigen=origen||null;"
        "ov.removeAttribute('hidden');"
        "document.body.classList.add(CL_FIJO);"
        "enfocar(cierreDe(ov));"
        "arrancar();}"
        "function cerrarModal(){"
        "var ov=modalVivo;"
        "if(!ov){return;}"
        "var origen=modalOrigen;"
        "modalVivo=null;modalOrigen=null;"
        "ov.setAttribute('hidden','');"
        "document.body.classList.remove(CL_FIJO);"
        "enfocar(origen);"
        "window.scrollTo(0,modalScroll);}"
        "function alAbrirVisor(ev){"
        "var zona=ev.currentTarget;"
        "var destino=zona.getAttribute('href')||'';"
        "if(destino.charAt(0)!=='#'){return;}"
        "var ov=document.getElementById(destino.substring(1));"
        "if(!ov){return;}"
        "ev.preventDefault();"
        "abrirModal(ov,zona);}"
        "function alCerrarVisor(ev){"
        "ev.preventDefault();"
        "cerrarModal();}"
        "function alTocarFondo(ev){"
        "var overlay=ev.currentTarget;"
        "var blanco=ev.target;"
        "var enFondo=(blanco===overlay)||(blanco.classList&&"
        "blanco.classList.contains(CL_CUERPO_MODAL));"
        "if(enFondo){cerrarModal();}}"
        "function atraparFoco(ev){"
        "if(!modalVivo){return;}"
        "var tecla=ev.key||'';"
        "if(tecla==='Escape'){cerrarModal();return;}"
        "if(tecla!=='Tab'){return;}"
        "var foco=modalVivo.querySelectorAll('a[href]');"
        "if(!foco.length){return;}"
        "var borde=ev.shiftKey?foco[0]:foco[foco.length-1];"
        "if(foco.length===1||document.activeElement===borde){"
        "ev.preventDefault();"
        "enfocar(ev.shiftKey?foco[foco.length-1]:foco[0]);}}"
        "var zonasAmp=document.querySelectorAll('.'+CL_AMPLIAR);"
        "for(var za=0;za<zonasAmp.length;za++){"
        "var nodoAmp=zonasAmp[za];"
        "nodoAmp.addEventListener('click',alAbrirVisor);}"
        "var zonasCer=document.querySelectorAll('.'+CL_CERRAR);"
        "for(var zc=0;zc<zonasCer.length;zc++){"
        "var nodoCer=zonasCer[zc];"
        "nodoCer.addEventListener('click',alCerrarVisor);}"
        "var overlays=document.querySelectorAll('.'+CL_VISOR);"
        "for(var vo=0;vo<overlays.length;vo++){"
        "var nodoOverlay=overlays[vo];"
        "nodoOverlay.addEventListener('click',alTocarFondo);}"
        "document.addEventListener('keydown',atraparFoco);"
    )


def _js_hero_arranque() -> str:
    """Arranque del Script_Unico: destapa el canvas y enciende el bucle unico.

    El `<canvas>` solo se destapa cuando el visor esta listo de verdad; hasta
    aqui lo que se ve es el SVG de reserva, que es la mejora progresiva del hero.
    Sin contexto 2D el canvas se queda tapado y el resto del hero sigue vivo.
    """
    return (
        "if(ctx){"
        "cv.removeAttribute('hidden');"
        "if(reserva){reserva.hidden=true;}"
        "remedir=true;medir();dibujar();}"
        "scrollActual=window.scrollY||0;"
        "arrancar();"
    )


def _js_hero() -> str:
    """El Script_Unico del hero completo, para el `<script>` UNICO del sitio.

    Un solo cuerpo con **un solo** bucle, compartido por el visor 3D, el
    Mundo_Hero, el Conmutador_Vista de cada Figura_Girable y el Arrastre_Rotacion
    (criterios 10.5, 10.17 y 29.1). El overlay modal del Visor_Ampliado
    (`_js_hero_modal`) se concatena en el mismo cuerpo y **no** anade bucle ni una
    segunda llamada a `requestAnimationFrame(`: solo alterna atributos y clases.

    Restricciones duras que este codigo respeta, y que **no** se relajaron:

    * `test_build_site.py` afirma `bajo.count("<script") == 1`. El hero no abre un
      `<script>` nuevo: se concatena dentro del que ya existe.
    * `test_sin_script_de_terceros` recorre `("http://", "https://", "//", "cdn",
      "jquery", "unpkg", "googleapis")` sobre el cuerpo del script y exige que
      ninguna aparezca. Por eso aqui no hay **ni un** comentario de linea: los
      comentarios son de Python, entre las piezas, y no viajan al artefacto.
    * `test_script_propio_y_unico` afirma ademas que el cuerpo no contiene `src=`
      ni la subcadena `import`.
    """
    return "".join(
        (
            "(function(){",
            _js_hero_visor(),
            _js_hero_mundo(),
            _js_hero_toque(),
            _js_hero_angosto(),
            _js_hero_vistas(),
            _js_hero_bucle(),
            _js_hero_entradas(),
            _js_hero_modal(),
            _js_hero_arranque(),
            "})();",
        )
    )


def _script(partes: list[str]) -> None:
    """`<script>` propio y minimo (cero terceros, cero red) del buscador/filtros.

    Filtra `article.ficha` por texto (acentos y mayusculas normalizados en JS),
    por `data-categoria` y por `data-nivel`, alternando el atributo `hidden`; el
    indice de anclas se sincroniza por `data-indice-de`. Es **mejora progresiva**:
    si este `<script>` se retira o el navegador no ejecuta JS, ninguna ficha se
    oculta. No referencia ninguna libreria ni recurso externo.
    """
    js = (
        "(function(){"
        f"var q=document.getElementById('{_ID_BUSCAR}');"
        f"var fc=document.getElementById('{_ID_CATEGORIA}');"
        f"var fn=document.getElementById('{_ID_NIVEL}');"
        f"var vacio=document.getElementById('{_ID_VACIO}');"
        "var fichas=[].slice.call(document.querySelectorAll('article.ficha'));"
        "var indice=[].slice.call(document.querySelectorAll('[data-indice-de]'));"
        "function norm(s){return (s||'').toString().toLowerCase()"
        ".normalize('NFD').replace(/[\\u0300-\\u036f]/g,'');}"
        "function filtrar(){"
        "var texto=norm(q?q.value:'');"
        "var cat=fc?fc.value:'';"
        "var niv=fn?fn.value:'';"
        "var visibles=0;var vis={};"
        "for(var i=0;i<fichas.length;i++){var a=fichas[i];"
        "var okT=!texto||norm(a.getAttribute('data-buscar')).indexOf(texto)!==-1;"
        "var okC=!cat||a.getAttribute('data-categoria')===cat;"
        "var okN=!niv||a.getAttribute('data-nivel')===niv;"
        "var ok=okT&&okC&&okN;a.hidden=!ok;"
        "if(ok){visibles++;vis[a.id]=true;}}"
        "for(var j=0;j<indice.length;j++){var li=indice[j];"
        "li.hidden=!vis['ficha-'+li.getAttribute('data-indice-de')];}"
        "if(vacio){vacio.hidden=visibles!==0;}}"
        "if(q)q.addEventListener('input',filtrar);"
        "if(fc)fc.addEventListener('change',filtrar);"
        "if(fn)fn.addEventListener('change',filtrar);"
        "filtrar();"
        "})();"
    )
    # El hero entero (visor 3D, Mundo_Hero, Conmutador_Vista y Arrastre_Rotacion)
    # va DENTRO de este mismo `<script>`: el sitio admite exactamente uno
    # (`test_build_site.py` lo afirma) y esa regla no se toca.
    partes.append(f"<script>{js}{_js_hero()}</script>")


def _apendice(fichas: list[dict[str, Any]], partes: list[str]) -> None:
    """Apendice con todos los enlaces del catalogo, clicables `target=_blank`."""
    partes.append(f'<h2 id="{_ANCLA_APENDICE}">Apendice de enlaces</h2>')
    partes.append(
        "<p>Todos los enlaces de video y busqueda de esta guia, en un solo lugar.</p>"
    )
    partes.append("<ul>")
    for ficha in fichas:
        for item in ficha.get("media") or []:
            url = item.get("url")
            if not url:
                continue
            titulo = item.get("titulo") or url
            partes.append(
                f'<li><a href="{build_html._esc(url)}" target="_blank" '
                f'rel="noopener noreferrer">{build_html._esc(titulo)}</a></li>'
            )
    partes.append("</ul>")


# --------------------------------------------------------------------------- #
# API publica
# --------------------------------------------------------------------------- #


def fundamentos_omitidos(
    catalogo: tuple[dp.DiagramaPostura, ...] | None = None,
) -> tuple[str, ...]:
    """Fundamento ajenos al conjunto cerrado que el Motor_Sitio no emite (3.9).

    Es exactamente la misma tupla que devuelve `secciones_guia.render_secciones`
    al componer el cuerpo del Target_Web, expuesta aqui como consulta pura para
    que el Orquestador_Build la enumere en su reporte (`fundamentos_omitidos`)
    sin tener que rehacer el documento ni guardar estado entre llamadas.
    """
    return dp.fundamentos_omitidos(catalogo)


def html_sitio(
    fichas: list[dict[str, Any]] | None = None,
    *,
    titulo: str = TITULO_SITIO,
    presentes: frozenset[str] | None = None,
) -> str:
    """Genera en memoria el `index.html` autocontenido (util para pruebas).

    Si `fichas` es `None`, carga las 15 Ficha_JSON reales del `Catalogo_JSON`.
    Reutiliza la estetica congelada de `build_html` (CSS, escapado, andamiaje y
    QR). No toca el disco.

    `presentes` es el subconjunto de Archivo_Diagrama que existe de verdad. Por
    defecto lo mide `diagramas_postura.presentes()`, que solo mira el sistema de
    archivos local; las pruebas y el Modo_Muestra pueden inyectar cualquier
    subconjunto para ejercitar los dos modos de render (criterios 5.3 y 5.4).

    Orden del cuerpo, con el plan del criterio 19.1 intercalado en el documento
    que ya existia: hero, botones y descargas, buscador, indice del plan y de las
    fichas, vocabulario del cuerpo, leyenda de simbolos, tecnica con sus cuatro
    bloques de Fundamento, rutina semanal, periodizacion, las 58 fichas, apendice
    de enlaces, Bloque_Creditos y, ultimo hijo de `<main>`, la navegacion.
    """
    if fichas is None:
        fichas = _cargar_fichas()
    if presentes is None:
        presentes = dp.presentes()

    css = build_html.estilo_css()

    cuerpo: list[str] = []
    _estilo_buscador(cuerpo)
    cuerpo.append(f'<main id="{_ANCLA_TOPE}">')
    # Hero con el visor 3D: el kicker, el H1 y el lede viven dentro de su capa de
    # vidrio, sobre el modelo.
    _hero(titulo, cuerpo)
    _acciones_header(cuerpo)
    _descargas(cuerpo)
    _buscador(fichas, cuerpo)
    _indice(fichas, cuerpo)
    # Plan de secciones de la guia: vocabulario, leyenda, tecnica y rutina. Los
    # Fundamento ajenos al conjunto cerrado no generan bloque y quedan aqui para
    # el reporte del Orquestador_Build (criterio 3.9).
    secciones_guia.render_secciones(cuerpo, presentes=presentes)
    # Periodización del ciclo de 12 semanas (metodología, no fichas nuevas).
    cuerpo.append(periodizacion.render_html())
    for ficha in fichas:
        _render_ficha(ficha, cuerpo)
    _apendice(fichas, cuerpo)
    # Bloque_Creditos al final del documento (criterio 18.1).
    secciones_guia.render_creditos_seccion(cuerpo, presentes=presentes)
    # La navegacion cierra `<main>`: asi `position:sticky;bottom:0` la ancla al
    # borde inferior en pantallas angostas (criterio 15.20).
    _nav(cuerpo)
    cuerpo.append("</main>")
    # JS propio y minimo al final del cuerpo (mejora progresiva; sin red).
    _script(cuerpo)

    # El Target_Web es el UNICO destino con `viewport-fit=cover` (criterio
    # 15.11): las paginas de capitulo y la publicacion conservan `META_VIEWPORT`.
    return build_html._envolver_documento(
        titulo, css, "".join(cuerpo), viewport=build_html.META_VIEWPORT_SITIO
    )


def escribir_sitio(dir_dist: str | None = None) -> str:
    """Escribe el unico `dist/index.html` autocontenido y devuelve su ruta.

    Publica de forma **atomica** desde `dist/.tmp/` con `os.replace` (que
    sobrescribe en Windows). Si la escritura temporal no es posible, degrada a
    escritura directa sobre `dist/index.html`. El archivo se escribe en UTF-8
    con `newline='\\n'` para bytes estables entre sistemas.
    """
    if dir_dist is None:
        dir_dist = dir_dist_por_defecto()
    os.makedirs(dir_dist, exist_ok=True)

    documento = html_sitio()
    final = os.path.join(dir_dist, NOMBRE_INDICE)

    try:
        dir_tmp = os.path.join(dir_dist, ".tmp")
        os.makedirs(dir_tmp, exist_ok=True)
        tmp = os.path.join(dir_tmp, NOMBRE_INDICE)
        with open(tmp, "w", encoding="utf-8", newline="\n") as manejador:
            manejador.write(documento)
        os.replace(tmp, final)
    except OSError:
        # Degradacion a escritura directa si el temporal no es utilizable.
        with open(final, "w", encoding="utf-8", newline="\n") as manejador:
            manejador.write(documento)

    return final
