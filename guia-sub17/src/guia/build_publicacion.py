"""Ensamblador de la estructura de publicacion para `jairofrancog7-star/hi`.

Este modulo es un **punto de entrada separado** del pipeline: no lo invoca
`build.construir()` (para no alterar los tests verdes existentes). Toma los
artefactos ya generados en `dist/` y los ensambla en un arbol publicable pensado
para GitHub Pages, siguiendo la seccion 8 del diseno ("Estructura de carpetas de
salida"):

```
publicacion/
  index.html                 # landing: portada + botones de descarga/lectura + indice
  README.md                  # enlaces de descarga directa, Pages y conteos del build
  .nojekyll                  # evita que Jekyll ignore archivos
  Guia_Extensa_Sub17.pdf     # copia de dist/guia.pdf (artefacto principal, Req 2.6)
  guia/                      # copia del sitio multi-archivo dist/web/
    index.html estilo.css NN-*.html
  laminas/
    lamina-01.svg ... lamina-NN.svg   # una Lamina_Vertical suelta por ficha
```

Estetica CONGELADA: no se toca `paleta.py`, `estilo_css`, `viz.py`, `draw.py` ni
el render de `build_site.py`. El `index.html` de la landing usa un `<style>`
inline minimo y autocontenido; las laminas sueltas se rinden a SVG propio (sin
recursos externos, sin bitmap). El sitio `guia/` conserva su estetica original
porque es una copia de `dist/web/`: el unico ajuste es reapuntar el href del PDF
(`../guia.pdf` -> `../Guia_Extensa_Sub17.pdf`), que de otro modo quedaria roto.

Convenciones del proyecto: solo libreria estandar; sin `assert` (todo invariante
es `raise ErrorBuild`/subclase con codigo `E_*`); `from __future__ import
annotations`; type hints; escritura en UTF-8 con `newline='\\n'`; sin
concatenacion de strings en bucle (se acumula en `list[str]` y se une con
`''.join(...)`). No borra nada fuera de `dir_salida`.

_Requirements: 2.6, 2.7, 9.4_
"""

from __future__ import annotations

import html
import os
import shutil
from typing import Any

from . import build, build_html, build_laminas
from .contenido import cap10_fundamentos
from .errores import E_PDF_CORRUPTO, ErrorBuild
from .plantillas import DatosLamina

__all__ = [
    "NOMBRE_PDF_PUBLICADO",
    "NOMBRE_GUIA",
    "NOMBRE_LAMINAS",
    "URL_DESCARGA_CRUDA",
    "URL_PAGES",
    "dir_salida_por_defecto",
    "ensamblar_publicacion",
    "main",
]


# --------------------------------------------------------------------------- #
# Constantes del artefacto publicable
# --------------------------------------------------------------------------- #

#: Nombre del PDF publicado en la raiz (decision C6: conserva este nombre).
NOMBRE_PDF_PUBLICADO: str = "Guia_Extensa_Sub17.pdf"

#: Carpeta que aloja la copia del sitio HTML multi-archivo (`dist/web/`).
NOMBRE_GUIA: str = "guia"

#: Carpeta que aloja las Lamina_Vertical sueltas en SVG.
NOMBRE_LAMINAS: str = "laminas"

#: Enlace de descarga directa (raw) del PDF en el repositorio destino.
URL_DESCARGA_CRUDA: str = (
    "https://github.com/jairofrancog7-star/hi/raw/main/Guia_Extensa_Sub17.pdf"
)

#: Enlace del sitio publicado con GitHub Pages.
URL_PAGES: str = "https://jairofrancog7-star.github.io/hi/"

#: Titulo mostrado en la landing y en el README.
_TITULO: str = "Guia Extensa de Entrenamiento Femenil Sub-17"

#: Nombres gestionados dentro de `dir_salida`. Solo estos se limpian/reescriben;
#: cualquier otro contenido de la carpeta se respeta.
_GESTIONADOS: tuple[str, ...] = (
    "index.html",
    "README.md",
    ".nojekyll",
    NOMBRE_PDF_PUBLICADO,
    NOMBRE_GUIA,
    NOMBRE_LAMINAS,
)

# --------------------------------------------------------------------------- #
# Geometria de la Lamina_Vertical suelta (misma proporcion que build_laminas)
# --------------------------------------------------------------------------- #

#: Ancho/alto del viewBox de cada lamina SVG (9:16, telefono), como build_laminas.
_ANCHO: float = build_laminas.LAMINA_ANCHO
_ALTO: float = build_laminas.LAMINA_ALTO

#: Margen uniforme dentro de la lamina, en unidades del viewBox.
_MARGEN: float = 40.0

#: Tamanos de fuente de cada bloque de texto de la lamina.
_TAM_TITULO: float = 34.0
_TAM_BAJADA: float = 18.0
_TAM_ITEM: float = 19.0

#: Ancho aproximado de caracter como fraccion del tamano de fuente (Helvetica).
#: Sirve para un presupuesto de ancho simple (wrap por conteo de caracteres).
_FACTOR_CHAR: float = 0.52

#: Fondo oscuro autocontenido de la lamina (no importa paleta; estetica propia).
_FONDO_SVG: str = "#141018"
_TEXTO_TITULO: str = "#ff2e88"
_TEXTO_BAJADA: str = "#e7e2ea"
_TEXTO_ITEM: str = "#c9c3cf"
_VINETA: str = "#ff6a3d"


# --------------------------------------------------------------------------- #
# Localizacion de rutas
# --------------------------------------------------------------------------- #


def _raiz_proyecto() -> str:
    """Ruta absoluta a `guia-sub17/` (dos niveles sobre este modulo)."""
    aqui = os.path.dirname(os.path.abspath(__file__))  # .../src/guia
    src = os.path.dirname(aqui)  # .../src
    return os.path.dirname(src)  # .../guia-sub17


def dir_salida_por_defecto() -> str:
    """Directorio de salida por defecto: `<raiz_proyecto>/publicacion`."""
    return os.path.join(_raiz_proyecto(), "publicacion")


# --------------------------------------------------------------------------- #
# Escapado
# --------------------------------------------------------------------------- #


def _esc_html(texto: object) -> str:
    """Escapa `texto` para HTML (comillas incluidas)."""
    return html.escape("" if texto is None else str(texto), quote=True)


def _esc_xml(texto: object) -> str:
    """Escapa `texto` para contenido XML/SVG (`&`, `<`, `>`, comillas).

    Se define aqui a proposito para no modificar `viz.py` (estetica congelada).
    Reutiliza `html.escape`, que cubre `&`, `<`, `>` y, con `quote=True`, `"` y
    `'`, suficiente tanto para nodos de texto como para valores de atributo.
    """
    return html.escape("" if texto is None else str(texto), quote=True)


# --------------------------------------------------------------------------- #
# Landing page (index.html) autocontenida
# --------------------------------------------------------------------------- #


def _estilo_landing() -> str:
    """CSS inline minimo y autocontenido de la landing (sin recursos externos)."""
    return (
        "*{box-sizing:border-box;}"
        "body{margin:0;background:#141018;color:#e7e2ea;"
        'font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;'
        "line-height:1.6;}"
        "main{max-width:44rem;margin:0 auto;padding:2.5rem 1.25rem 4rem;}"
        "h1{font-size:clamp(1.8rem,7vw,2.75rem);line-height:1.1;color:#ff2e88;"
        "margin:0 0 0.5rem;}"
        "p.lede{color:#c9c3cf;margin:0 0 2rem;}"
        ".botones{display:flex;flex-wrap:wrap;gap:0.9rem;margin:0 0 2.5rem;}"
        ".btn{display:inline-block;padding:0.9rem 1.4rem;border-radius:14px;"
        "font-weight:700;text-decoration:none;border:1px solid #ff2e88;}"
        ".btn-solid{background:#ff2e88;color:#fff;}"
        ".btn-outline{background:transparent;color:#ff2e88;}"
        "h2{font-size:1.3rem;margin:2.5rem 0 1rem;color:#fff;}"
        "ul.capitulos{list-style:none;padding:0;margin:0;display:grid;gap:0.6rem;}"
        "ul.capitulos li{margin:0;}"
        "ul.capitulos a{display:block;padding:0.9rem 1.1rem;border-radius:14px;"
        "background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.12);"
        "color:#e7e2ea;font-weight:600;text-decoration:none;}"
        ".aviso{margin-top:2.5rem;padding:1rem 1.25rem;border-radius:14px;"
        "background:rgba(255,106,61,0.12);border:1px solid rgba(255,106,61,0.35);"
        "color:#f2d9cd;font-size:0.95em;}"
    )


def _html_landing(fichas: list[dict[str, Any]]) -> str:
    """Genera el `index.html` de la landing (autocontenido, recursos relativos).

    Titulo, dos botones grandes (descargar PDF con `download` y leer en linea),
    lista de fichas/capitulos con enlaces de ancla hacia `guia/index.html`, y un
    aviso de que el contenido es informativo. Todo el texto pasa por
    `html.escape`; el unico estilo es un `<style>` inline. Los recursos propios
    (href del PDF y del sitio) son rutas relativas: sin `http://`/`https://`.
    """
    href_pdf = _esc_html(NOMBRE_PDF_PUBLICADO)
    href_guia = _esc_html(f"{NOMBRE_GUIA}/index.html")

    partes: list[str] = []
    partes.append("<!DOCTYPE html>")
    partes.append('<html lang="es-MX">')
    partes.append("<head>")
    partes.append('<meta charset="utf-8">')
    # Mismo viewport EXACTO que el resto de los destinos web (tarea 34.4):
    # permite ampliar hasta cinco veces y nunca escribe `user-scalable=no`.
    partes.append(
        f'<meta name="viewport" content="{build_html.META_VIEWPORT}">'
    )
    partes.append(f"<title>{_esc_html(_TITULO)}</title>")
    partes.append(f"<style>{_estilo_landing()}</style>")
    partes.append("</head>")
    partes.append("<body>")
    partes.append("<main>")
    partes.append(f"<h1>{_esc_html(_TITULO)}</h1>")
    # El numero de ejercicios se deriva del catalogo actual (nunca se escribe a
    # mano): si el Catalogo_JSON crece o se recorta, la portada lo refleja.
    partes.append(
        f'<p class="lede">{len(fichas)} ejercicios reales para entrenar con lo '
        "que hay. Descarga la guia en PDF o leela en linea desde el celular.</p>"
    )
    partes.append('<div class="botones">')
    partes.append(
        f'<a class="btn btn-solid" href="{href_pdf}" download>Descargar PDF</a>'
    )
    partes.append(
        f'<a class="btn btn-outline" href="{href_guia}">Leer en linea</a>'
    )
    partes.append("</div>")

    partes.append("<h2>Contenido</h2>")
    partes.append('<ul class="capitulos">')
    for ficha in fichas:
        fid = str(ficha.get("id", "")).strip()
        numero = ficha.get("numero", "")
        titulo = str(ficha.get("titulo", "")).strip() or fid
        etiqueta = f"{numero}. {titulo}" if numero != "" else titulo
        ancla = _esc_html(f"{NOMBRE_GUIA}/index.html#ficha-{fid}")
        partes.append(f'<li><a href="{ancla}">{_esc_html(etiqueta)}</a></li>')
    partes.append("</ul>")

    partes.append(
        '<p class="aviso">Este material es <strong>contenido informativo</strong> '
        "de entrenamiento y no sustituye la valoracion de un profesional de la "
        "salud ni la supervision de personal tecnico calificado.</p>"
    )
    partes.append("</main>")
    partes.append("</body>")
    partes.append("</html>")
    return "\n".join(partes)


# --------------------------------------------------------------------------- #
# README.md
# --------------------------------------------------------------------------- #


def _texto_readme(*, paginas: int, fichas: int, laminas: int) -> str:
    """Genera el `README.md` con enlaces de descarga, Pages y conteos del build."""
    lineas: list[str] = [
        f"# {_TITULO}",
        "",
        "Contenido informativo de entrenamiento femenil Sub-17: guia en PDF, "
        "sitio para leer en linea y laminas para compartir.",
        "",
        "## Descargar",
        "",
        f"- **PDF (descarga directa):** {URL_DESCARGA_CRUDA}",
        f"- **Leer en linea (GitHub Pages):** {URL_PAGES}",
        "",
        "## Contenido del ultimo build",
        "",
        f"- Paginas: {paginas}",
        f"- Fichas: {fichas}",
        f"- Laminas: {laminas}",
        "",
        "## Estructura",
        "",
        "- `index.html`: portada con botones de descarga y de lectura en linea.",
        f"- `{NOMBRE_PDF_PUBLICADO}`: guia completa en PDF.",
        f"- `{NOMBRE_GUIA}/`: sitio HTML para leer en linea.",
        f"- `{NOMBRE_LAMINAS}/`: laminas verticales sueltas en SVG.",
        "",
    ]
    return "\n".join(lineas)


# --------------------------------------------------------------------------- #
# Lamina_Vertical suelta -> SVG autocontenido
# --------------------------------------------------------------------------- #


def _envolver_lineas(texto: str, tam_fuente: float, ancho_util: float) -> list[str]:
    """Parte `texto` en lineas que caben en `ancho_util` (presupuesto simple).

    Estima el ancho de cada caracter como `tam_fuente * _FACTOR_CHAR` (Helvetica)
    y acumula palabras hasta agotar el presupuesto. Una palabra mas larga que el
    presupuesto se corta por caracteres para no desbordar. Sin dependencias de
    metricas AFM: es un wrap aproximado suficiente para una lamina compartible.
    """
    limpio = " ".join(str(texto).split())
    if not limpio:
        return []
    max_chars = max(1, int(ancho_util / (tam_fuente * _FACTOR_CHAR)))
    lineas: list[str] = []
    actual = ""
    for palabra in limpio.split(" "):
        while len(palabra) > max_chars:
            if actual:
                lineas.append(actual)
                actual = ""
            lineas.append(palabra[:max_chars])
            palabra = palabra[max_chars:]
        candidato = palabra if not actual else f"{actual} {palabra}"
        if len(candidato) <= max_chars:
            actual = candidato
        else:
            if actual:
                lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


def _svg_lamina(datos: DatosLamina) -> str:
    """Rinde una `DatosLamina` como SVG vertical autocontenido (540x960).

    Usa `viewBox="0 0 540 960"`, `xmlns` y `role="img"`, un `<rect>` de fondo y
    `<text>` para el titulo, la bajada y cada item (con wrap por presupuesto de
    ancho). Sin recursos externos, sin bitmap. El texto se escapa con `_esc_xml`.
    """
    ancho_util = _ANCHO - 2.0 * _MARGEN
    y_max = _ALTO - _MARGEN

    cuerpo: list[str] = []
    cuerpo.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {_ANCHO:.0f} {_ALTO:.0f}" '
        f'role="img" preserveAspectRatio="xMidYMid meet">'
    )
    cuerpo.append(f"<title>{_esc_xml(datos.titulo)}</title>")
    cuerpo.append(
        f'<rect x="0" y="0" width="{_ANCHO:.0f}" height="{_ALTO:.0f}" '
        f'fill="{_FONDO_SVG}"/>'
    )
    # Vineta de acento superior.
    cuerpo.append(
        f'<rect x="{_MARGEN:.0f}" y="{_MARGEN:.0f}" width="64" height="6" '
        f'rx="3" fill="{_VINETA}"/>'
    )

    y = _MARGEN + 44.0

    # Titulo (puede ocupar varias lineas).
    for linea in _envolver_lineas(datos.titulo, _TAM_TITULO, ancho_util):
        if y > y_max:
            break
        cuerpo.append(
            f'<text x="{_MARGEN:.0f}" y="{y:.1f}" '
            f'font-family="Helvetica, Arial, sans-serif" '
            f'font-size="{_TAM_TITULO:.0f}" font-weight="bold" '
            f'fill="{_TEXTO_TITULO}">{_esc_xml(linea)}</text>'
        )
        y += _TAM_TITULO * 1.2

    # Bajada.
    if datos.bajada:
        y += 8.0
        for linea in _envolver_lineas(datos.bajada, _TAM_BAJADA, ancho_util):
            if y > y_max:
                break
            cuerpo.append(
                f'<text x="{_MARGEN:.0f}" y="{y:.1f}" '
                f'font-family="Helvetica, Arial, sans-serif" '
                f'font-size="{_TAM_BAJADA:.0f}" '
                f'fill="{_TEXTO_BAJADA}">{_esc_xml(linea)}</text>'
            )
            y += _TAM_BAJADA * 1.35

    # Items (dosis, claves y enlaces), cada uno con vineta.
    y += 20.0
    for item in datos.items:
        lineas_item = _envolver_lineas(item, _TAM_ITEM, ancho_util - 18.0)
        if not lineas_item or y > y_max:
            continue
        # Vineta del item.
        cuerpo.append(
            f'<circle cx="{_MARGEN + 4.0:.1f}" cy="{y - 6.0:.1f}" r="4" '
            f'fill="{_VINETA}"/>'
        )
        for idx, linea in enumerate(lineas_item):
            if y > y_max:
                break
            x = _MARGEN + 18.0
            cuerpo.append(
                f'<text x="{x:.1f}" y="{y:.1f}" '
                f'font-family="Helvetica, Arial, sans-serif" '
                f'font-size="{_TAM_ITEM:.0f}" '
                f'fill="{_TEXTO_ITEM}">{_esc_xml(linea)}</text>'
            )
            y += _TAM_ITEM * 1.3
        y += 8.0

    cuerpo.append("</svg>")
    return "".join(cuerpo)


# --------------------------------------------------------------------------- #
# Utilidades de escritura de archivos
# --------------------------------------------------------------------------- #


def _escribir_texto(ruta: str, contenido: str) -> None:
    """Escribe `contenido` en `ruta` en UTF-8 con `newline='\\n'`."""
    with open(ruta, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(contenido)


def _reapuntar_pdf_en_sitio(dir_guia: str) -> int:
    """Reapunta la banda de descarga del sitio copiado al PDF publicado.

    En `dist/` el sitio multi-archivo enlaza el PDF como `../guia.pdf`
    (`build.PDF_HREF_WEB`), pero en el arbol publicable el PDF vive en la raiz
    con el nombre `Guia_Extensa_Sub17.pdf`. Sin este ajuste el enlace de
    descarga de cada capitulo quedaria roto en GitHub Pages.

    Solo se sustituye esa ruta relativa dentro de los `.html` copiados: no se
    toca el CSS, ni el marcado, ni el contenido (estetica congelada). Devuelve
    el numero de archivos modificados; si tras la sustitucion quedara alguna
    referencia al nombre antiguo, lanza `ErrorBuild`.
    """
    viejo = build.PDF_HREF_WEB  # "../guia.pdf"
    nuevo = "../" + NOMBRE_PDF_PUBLICADO
    modificados = 0
    for nombre in sorted(os.listdir(dir_guia)):
        if not nombre.endswith(".html"):
            continue
        ruta = os.path.join(dir_guia, nombre)
        with open(ruta, encoding="utf-8", newline="") as fh:
            texto = fh.read()
        if viejo not in texto:
            continue
        texto = texto.replace(viejo, nuevo)
        if viejo in texto:
            raise ErrorBuild(
                E_PDF_CORRUPTO,
                "quedo una referencia al PDF de dist en el sitio publicado",
                detalle={"archivo": nombre, "href": viejo},
            )
        with open(ruta, "w", encoding="utf-8", newline="") as fh:
            fh.write(texto)
        modificados += 1
    return modificados


def _limpiar_gestionados(dir_salida: str) -> None:
    """Elimina solo los elementos gestionados dentro de `dir_salida`.

    No toca ningun otro contenido de la carpeta ni nada fuera de ella. Un archivo
    se borra con `os.remove` y un directorio con `shutil.rmtree`.
    """
    for nombre in _GESTIONADOS:
        objetivo = os.path.join(dir_salida, nombre)
        if os.path.isdir(objetivo):
            shutil.rmtree(objetivo)
        elif os.path.exists(objetivo):
            os.remove(objetivo)


# --------------------------------------------------------------------------- #
# API publica
# --------------------------------------------------------------------------- #


def ensamblar_publicacion(
    dir_salida: str | None = None,
    *,
    dir_dist: str | None = None,
) -> dict[str, Any]:
    """Ensambla el arbol publicable para `jairofrancog7-star/hi` y lo describe.

    Pasos:

    1. Regenera los artefactos de `dist/` invocando `build.construir(...)` en
       `MODO_MUESTRA` (sin preflight); toma del `Reporte` los conteos del ultimo
       build (paginas, fichas, laminas).
    2. Ensambla el arbol en `dir_salida` (por defecto `<raiz>/publicacion`),
       limpiando SOLO los elementos gestionados; nunca toca nada fuera de
       `dir_salida`. Emite `index.html`, `README.md`, `.nojekyll`,
       `Guia_Extensa_Sub17.pdf` (copia de `dist/guia.pdf`), `guia/` (copia de
       `dist/web/`) y `laminas/lamina-NN.svg` (una por Lamina_Vertical).
    3. Devuelve un `dict` con las rutas escritas y los conteos.

    Cualquier fallo se expresa con `raise ErrorBuild` (o subclase); nunca con
    `assert`.
    """
    dir_dist_efectivo = dir_dist or build.dir_dist_por_defecto()

    # Paso 1: (re)generar dist/ y capturar los conteos del Reporte.
    reporte = build.construir(
        modo=build.MODO_MUESTRA,
        dir_dist=dir_dist_efectivo,
        con_preflight=False,
    )

    pdf_origen = os.path.join(dir_dist_efectivo, build.NOMBRE_PDF)
    web_origen = os.path.join(dir_dist_efectivo, build.NOMBRE_WEB)
    if not os.path.isfile(pdf_origen):
        raise ErrorBuild(
            E_PDF_CORRUPTO,
            "no se encontro el PDF de origen para publicar",
            detalle={"ruta": pdf_origen},
        )
    if not os.path.isdir(web_origen):
        raise ErrorBuild(
            E_PDF_CORRUPTO,
            "no se encontro el sitio web de origen para publicar",
            detalle={"ruta": web_origen},
        )

    # Paso 2: preparar dir_salida limpiando solo lo gestionado.
    destino = dir_salida if dir_salida is not None else dir_salida_por_defecto()
    os.makedirs(destino, exist_ok=True)
    _limpiar_gestionados(destino)

    fichas = cap10_fundamentos.fichas_json()

    # index.html (landing autocontenida).
    ruta_index = os.path.join(destino, "index.html")
    _escribir_texto(ruta_index, _html_landing(fichas))

    # README.md con enlaces y conteos del ultimo build.
    ruta_readme = os.path.join(destino, "README.md")
    _escribir_texto(
        ruta_readme,
        _texto_readme(
            paginas=reporte.paginas_modelo,
            fichas=reporte.fichas,
            laminas=reporte.laminas,
        ),
    )

    # .nojekyll vacio.
    ruta_nojekyll = os.path.join(destino, ".nojekyll")
    _escribir_texto(ruta_nojekyll, "")

    # Guia_Extensa_Sub17.pdf (copia; el origen dist/guia.pdf queda intacto).
    ruta_pdf = os.path.join(destino, NOMBRE_PDF_PUBLICADO)
    shutil.copyfile(pdf_origen, ruta_pdf)

    # guia/ (copia del sitio multi-archivo dist/web/).
    dir_guia = os.path.join(destino, NOMBRE_GUIA)
    if os.path.isdir(dir_guia):
        shutil.rmtree(dir_guia)
    shutil.copytree(web_origen, dir_guia)
    # El sitio copiado enlaza `../guia.pdf`; en la publicacion el PDF se llama
    # Guia_Extensa_Sub17.pdf. Se reapunta solo ese href (nada mas cambia).
    html_reapuntados = _reapuntar_pdf_en_sitio(dir_guia)

    # laminas/lamina-NN.svg (una Lamina_Vertical suelta por ficha).
    dir_laminas = os.path.join(destino, NOMBRE_LAMINAS)
    os.makedirs(dir_laminas, exist_ok=True)
    rutas_laminas: list[str] = []
    for indice, ficha in enumerate(fichas, start=1):
        datos = build_laminas.datos_lamina(ficha)
        svg = _svg_lamina(datos)
        nombre = f"lamina-{indice:02d}.svg"
        ruta_svg = os.path.join(dir_laminas, nombre)
        _escribir_texto(ruta_svg, svg)
        rutas_laminas.append(ruta_svg)

    return {
        "dir_salida": destino,
        "index_html": ruta_index,
        "readme": ruta_readme,
        "nojekyll": ruta_nojekyll,
        "pdf": ruta_pdf,
        "dir_guia": dir_guia,
        "html_reapuntados": html_reapuntados,
        "laminas": rutas_laminas,
        "conteos": {
            # Paginas del paginador real (Modelo_Paginas), no las hojas del PDF
            # de fichas: es el conteo que evalua el umbral de publicacion.
            "paginas": reporte.paginas_modelo,
            "hojas_pdf_fichas": reporte.paginas_totales,
            "fichas": reporte.fichas,
            "laminas": reporte.laminas,
        },
    }


def main() -> int:
    """Punto de entrada CLI: ensambla la publicacion e imprime un resumen."""
    resultado = ensamblar_publicacion()
    conteos = resultado["conteos"]
    print(f"Publicacion ensamblada en: {resultado['dir_salida']}")
    print(
        f"  paginas={conteos['paginas']} fichas={conteos['fichas']} "
        f"laminas={conteos['laminas']}"
    )
    print(f"  laminas SVG escritas: {len(resultado['laminas'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
