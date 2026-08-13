"""Target_PDF_Guia: plantilla "una ficha por hoja" para `dist/guia.pdf` (tarea 22.1).

Este modulo construye el Modelo_Paginas de `dist/guia.pdf` en el formato del
Addendum A (Target_PDF_Guia, seccion A.6 del diseno): **una Ficha por hoja**,
imprimible, con fondo claro de alto contraste (Req 9.9, tema claro ya existente
y congelado). Cada hoja lleva, de arriba hacia abajo:

* el **titulo** de la ficha (mas una linea de metadatos y el subtitulo);
* su **Diagrama_Cancha**, construido desde el campo `cancha` de la Ficha_JSON
  con `diagram_spec.desde_cancha_json` y dibujado por `draw.py` (mismo spec que
  usa el sitio web: sin imagenes de mapa de bits, Req 12.7/12.8);
* la **dosis / montaje** (cuando, duracion, jugadoras, material, meta);
* una **rejilla de QR**, con **un QR por cada Media_Item** de la ficha, generado
  offline con `qr.py` y **verificado offline** con `qr_decode.verificar_qr`
  (round-trip URL -> matriz -> URL). Si un QR no reproduce su URL, se propaga
  `ErrorQR(E_QR_NO_VERIFICA)`; si la URL excede la capacidad del simbolo QR
  soportado por `qr.py`, se traduce el `ValueError` crudo en
  `ErrorQR(E_QR_CAPACIDAD)` con un mensaje claro (no se cuelga el pipeline y no
  se omite el QR en silencio).

Fuente de contenido (regla vigente del proyecto): se usan **solo** las 15
Ficha_JSON reales del Catalogo_JSON, a traves de
`cap10_fundamentos.fichas_json()`. No se inventan fichas ni se toca el esquema
JSON, los enlaces ni los QR.

Reutiliza `build_pdf.py` + `layout.py`: el modelo emitido es una
`list[PaginaRender]` (la frontera unica hacia el Motor_PDF), asi que el
verificador estructural (`verify_pdf.verificar_pdf`) lo acepta sin cambios.

Manejo de URLs largas (decision documentada). Las URLs de tipo `busqueda`
pueden ser largas. `qr.py` soporta versiones 1..6 nivel L (hasta ~134 bytes en
byte mode). Cuando una URL no cabe, `qr.codificar` lanza `ValueError`; aqui se
captura y se convierte en `ErrorQR(E_QR_CAPACIDAD)` nombrando la ficha, el
Media_Item y la longitud de la URL, de modo que el build falla con un mensaje
accionable en lugar de propagar una excepcion cruda o generar un QR ilegible.

Solo libreria estandar; sin `assert` (todo invariante es `raise`); type hints y
`from __future__ import annotations`; sin concatenacion de strings en bucle.

_Requirements: 12.5, 9.6, 9.7, 9.9_
"""

from __future__ import annotations

import math
from typing import Any

from . import afm
from .contenido import cap10_fundamentos
from .diagram_spec import desde_cancha_json
from .errores import E_QR_CAPACIDAD, ErrorQR
from .layout import (
    AREA_H,
    AREA_W,
    AREA_X,
    AREA_Y,
    INTERLINEADO,
    Anotacion,
    ElementoRender,
    PaginaRender,
    Plantilla,
    TextoDatos,
    TipoElemento,
    medir_elemento,
)
from .plantillas import DiagramaDatos, QRDatos
from .qr import codificar as _qr_codificar
from .qr_decode import verificar_qr as _verificar_qr

__all__ = [
    "CAPITULO_ID",
    "TITULO",
    "LADO_QR",
    "modelo",
    "escribir",
]

#: Identificador del "capitulo" del Target_PDF_Guia (una sola coleccion).
CAPITULO_ID: str = "guia_pdf"

#: Titulo mostrado en el encabezado/pie de cada hoja (Req 1.5).
TITULO: str = "Guia imprimible - una ficha por hoja"

#: Lado del cuadro de cada QR en la rejilla, en puntos.
LADO_QR: float = 82.0

#: Separaciones verticales estandar entre bloques de la hoja.
_GAP_PARRAFO: float = 4.0
_GAP_SECCION: float = 9.0

#: Tipografia de cada bloque (solo Standard-14: Helvetica / Helvetica-Bold).
_TAM_TITULO: float = 15.0
_TAM_META: float = 8.5
_TAM_SUBTITULO: float = 10.5
_TAM_CUERPO: float = 9.5
_TAM_CAPTION: float = 7.0

#: Altura minima y maxima que puede ocupar el Diagrama_Cancha en la hoja.
_DIAGRAMA_MIN: float = 110.0
_DIAGRAMA_MAX: float = 330.0

#: Columnas maximas de la rejilla de QR.
_QR_COLUMNAS_MAX: int = 4

#: Etiqueta legible por tipo de Media_Item (para la leyenda del QR).
_ETIQUETA_TIPO: dict[str, str] = {
    "youtube": "VIDEO",
    "tiktok": "VIDEO",
    "instagram_reel": "VIDEO",
    "facebook_reel": "VIDEO",
    "web": "WEB",
    "busqueda": "BUSCAR",
}

#: Claves de dosis a rendir, en orden, con su etiqueta legible.
_CAMPOS_DOSIS: tuple[tuple[str, str], ...] = (
    ("cuando", "Cuando"),
    ("duracion", "Duracion"),
    ("jugadoras", "Jugadoras"),
    ("material", "Material"),
    ("meta", "Meta"),
)


# --------------------------------------------------------------------------- #
# Medicion de bloques de texto con afm.py (nunca se estima)
# --------------------------------------------------------------------------- #


def _alto_texto(texto: str, ancho: float, fuente: str, tam: float) -> float:
    """Altura en puntos de `texto` envuelto a `ancho` (mide con `afm.envolver`)."""
    lineas = afm.envolver(texto, ancho, fuente, tam)
    n = len(lineas) if lineas else 1
    return n * tam * INTERLINEADO


def _texto_dosis(dosis: dict[str, Any]) -> list[str]:
    """Lineas de la dosis/montaje a partir del objeto `dosis` de la Ficha_JSON."""
    lineas: list[str] = []
    for clave, etiqueta in _CAMPOS_DOSIS:
        valor = dosis.get(clave)
        if isinstance(valor, str) and valor.strip():
            lineas.append(f"{etiqueta}: {valor.strip()}")
    return lineas


#: Etiqueta fija de la accion del enlace, para los media que son video.
_ACCION_DEMO: str = "Ver demostracion"

#: Tipos de Media_Item que son un video de demostracion (no una busqueda).
_TIPOS_DEMO: frozenset[str] = frozenset(
    {"youtube", "tiktok", "instagram_reel", "facebook_reel"}
)


def _caption_media(item: dict[str, Any]) -> str:
    """Leyenda de un Media_Item: etiqueta de tipo + titulo (+ accion si es video).

    El titulo del media (por ejemplo "Video de ejemplo") siempre aparece. Cuando
    el media es un video se anade la etiqueta fija `Ver demostracion`, que es la
    misma que usa el sitio en el texto del ancla.
    """
    tipo = str(item.get("tipo", ""))
    etiqueta = _ETIQUETA_TIPO.get(tipo, tipo.upper() or "ENLACE")
    titulo = str(item.get("titulo", "")).strip()
    base = f"[{etiqueta}] {titulo}" if titulo else f"[{etiqueta}]"
    if tipo in _TIPOS_DEMO:
        return f"{base} - {_ACCION_DEMO}"
    return base


def _alto_caption(caption: str, ancho: float) -> float:
    """Altura de una leyenda de QR, recortada a 3 lineas como maximo."""
    lineas = afm.envolver(caption, ancho, "Helvetica", _TAM_CAPTION)
    n = min(len(lineas) if lineas else 1, 3)
    return n * _TAM_CAPTION * INTERLINEADO


# --------------------------------------------------------------------------- #
# Generacion + verificacion offline de los QR de una ficha
# --------------------------------------------------------------------------- #


def _qr_de_media(item: dict[str, Any], *, ficha_id: str, indice: int) -> Any:
    """Codifica el QR de un Media_Item y lo verifica offline (round-trip).

    Traduce el `ValueError` de capacidad de `qr.codificar` en
    `ErrorQR(E_QR_CAPACIDAD)` para no colgar el pipeline con una URL demasiado
    larga; el fallo de round-trip lo reporta `qr_decode.verificar_qr` como
    `ErrorQR(E_QR_NO_VERIFICA)`. Nunca omite un QR en silencio.
    """
    url = str(item.get("url", ""))
    try:
        matriz = _qr_codificar(url)
    except ValueError as causa:
        raise ErrorQR(
            f"la URL del media #{indice} de la ficha {ficha_id} no cabe en un "
            f"QR soportado ({len(url.encode('utf-8'))} bytes): {url}",
            codigo=E_QR_CAPACIDAD,
            detalle={
                "id": ficha_id,
                "media": indice,
                "url": url,
                "bytes": len(url.encode("utf-8")),
                "motivo": str(causa),
            },
        ) from causa
    # Verificacion offline obligatoria: round-trip URL -> matriz -> URL.
    _verificar_qr(url, matriz, id_ficha=ficha_id)
    return matriz


# --------------------------------------------------------------------------- #
# Rejilla de QR (una celda por Media_Item)
# --------------------------------------------------------------------------- #


def _dim_rejilla(media: list[dict[str, Any]]) -> tuple[int, int, float, float]:
    """Devuelve (columnas, filas, ancho_celda, alto_caption) de la rejilla.

    `alto_caption` es el maximo de las leyendas de la rejilla (todas comparten
    la misma altura de fila para que las celdas queden alineadas).
    """
    n = len(media)
    columnas = min(n, _QR_COLUMNAS_MAX) if n > 0 else 1
    filas = math.ceil(n / columnas) if n > 0 else 0
    ancho_celda = AREA_W / columnas
    alto_caption = 0.0
    for item in media:
        alto_caption = max(alto_caption, _alto_caption(_caption_media(item), ancho_celda - 6.0))
    return columnas, filas, ancho_celda, alto_caption


def _alto_rejilla(media: list[dict[str, Any]]) -> float:
    """Altura total del bloque de QR: encabezado + filas de celdas."""
    if not media:
        return 0.0
    encabezado = _TAM_CUERPO * INTERLINEADO + _GAP_PARRAFO
    _, filas, _, alto_caption = _dim_rejilla(media)
    fila_alto = LADO_QR + 2.0 + alto_caption + _GAP_PARRAFO
    return encabezado + filas * fila_alto


# --------------------------------------------------------------------------- #
# Construccion de una hoja (una Ficha_JSON -> una PaginaRender)
# --------------------------------------------------------------------------- #


class _Hoja:
    """Cursor vertical minimal para colocar los bloques de una hoja."""

    __slots__ = ("elementos", "anotaciones", "top")

    def __init__(self) -> None:
        self.elementos: list[ElementoRender] = []
        self.anotaciones: list[Anotacion] = []
        self.top: float = AREA_Y + AREA_H

    def texto(self, texto: str, *, fuente: str, tam: float, gap: float) -> None:
        elemento = ElementoRender(
            tipo=TipoElemento.TEXTO,
            x=AREA_X,
            y=0.0,
            w=AREA_W,
            h=0.0,
            datos=TextoDatos(texto=texto, fuente=fuente, tamano=tam),
        )
        altura = medir_elemento(elemento, AREA_W)
        elemento.h = altura
        elemento.y = self.top - altura
        self.elementos.append(elemento)
        self.top -= altura + gap

    def diagrama(self, spec: Any, alto: float, *, titulo: str | None, gap: float) -> None:
        elemento = ElementoRender(
            tipo=TipoElemento.DIAGRAMA,
            x=AREA_X,
            y=self.top - alto,
            w=AREA_W,
            h=alto,
            datos=DiagramaDatos(spec=spec, titulo=titulo),
        )
        self.elementos.append(elemento)
        self.top -= alto + gap

    def paneles(
        self,
        izquierda: Any,
        derecha: Any,
        alto: float,
        *,
        titulo_izq: str | None,
        titulo_der: str | None,
        gap: float,
    ) -> None:
        """Coloca dos diagramas lado a lado en la misma banda vertical.

        Se usa para la zona visual de una ficha que ademas de su Diagrama_Cancha
        trae ilustracion de tecnica: la ilustracion va a la izquierda y la cancha
        a la derecha. Ocupa la **misma** altura que un solo diagrama, asi que la
        hoja sigue siendo una ficha por hoja sin comerse el presupuesto vertical
        (el Motor_PDF escala cada spec a su caja y lo centra).
        """
        canal = 10.0
        ancho = (AREA_W - canal) / 2.0
        y = self.top - alto
        for indice, (spec, titulo) in enumerate(
            ((izquierda, titulo_izq), (derecha, titulo_der))
        ):
            self.elementos.append(
                ElementoRender(
                    tipo=TipoElemento.DIAGRAMA,
                    x=AREA_X + indice * (ancho + canal),
                    y=y,
                    w=ancho,
                    h=alto,
                    datos=DiagramaDatos(spec=spec, titulo=titulo),
                )
            )
        self.top -= alto + gap


def _postura_de(ficha: dict[str, Any]) -> Any:
    """Ilustracion de tecnica de la Ficha_JSON, o `None` si no le toca ninguna.

    Import **diferido y tolerante** de `guia.figuras` (mismo patron que usa el
    adaptador `schema_json`): la ilustracion es opcional, que una ficha no lleve
    es un resultado legitimo y sin el modulo de figuras la hoja se sigue
    maquetando con su Diagrama_Cancha.
    """
    try:
        from . import figuras
    except ImportError:
        return None
    resolver = getattr(figuras, "para_ficha", None)
    if not callable(resolver):
        return None
    return resolver(ficha)


def _pagina_ficha(ficha: dict[str, Any], folio: int) -> PaginaRender:
    """Construye la hoja de una Ficha_JSON: titulo, diagrama, dosis y rejilla QR.

    El Diagrama_Cancha se dimensiona con el espacio que queda tras reservar el
    texto de cabecera, la dosis y la rejilla de QR, de modo que **todo cabe en
    una sola hoja** (una ficha por hoja). Si ni con el diagrama en su altura
    minima cabe el contenido, se propaga `ErrorLayout('E_DESBORDE_TEXTO')` desde
    el propio `_Hoja` (defensivo; el contenido real cabe con holgura).
    """
    ficha_id = str(ficha.get("id", ""))
    titulo = str(ficha.get("titulo", "")).strip() or ficha_id
    subtitulo = str(ficha.get("subtitulo", "")).strip()
    meta = " · ".join(
        parte
        for parte in (
            str(ficha.get("categoria", "")).strip(),
            str(ficha.get("nivel", "")).strip(),
        )
        if parte
    )
    dosis = ficha.get("dosis") or {}
    lineas_dosis = _texto_dosis(dosis if isinstance(dosis, dict) else {})
    media = [m for m in (ficha.get("media") or []) if isinstance(m, dict)]

    # 1) Generar y verificar TODOS los QR de la ficha antes de maquetar. Asi un
    #    fallo de QR detiene el build sin dejar una hoja a medias.
    matrices = [
        _qr_de_media(item, ficha_id=ficha_id, indice=indice)
        for indice, item in enumerate(media)
    ]

    # 2) Presupuesto vertical: reservar cabecera + dosis + rejilla; el diagrama
    #    ocupa el resto (acotado entre un minimo y un maximo legibles).
    alto_titulo = _alto_texto(titulo, AREA_W, "Helvetica-Bold", _TAM_TITULO)
    alto_meta = _alto_texto(meta, AREA_W, "Helvetica", _TAM_META) if meta else 0.0
    alto_sub = (
        _alto_texto(subtitulo, AREA_W, "Helvetica", _TAM_SUBTITULO) if subtitulo else 0.0
    )
    alto_cab_dosis = _TAM_CUERPO * INTERLINEADO + _GAP_PARRAFO
    alto_dosis = alto_cab_dosis + sum(
        _alto_texto(linea, AREA_W, "Helvetica", _TAM_CUERPO) for linea in lineas_dosis
    )
    alto_qr = _alto_rejilla(media)

    reservado = (
        alto_titulo
        + _GAP_PARRAFO
        + (alto_meta + _GAP_PARRAFO if meta else 0.0)
        + (alto_sub + _GAP_SECCION if subtitulo else 0.0)
        + alto_dosis
        + _GAP_SECCION
        + alto_qr
        + _GAP_SECCION
        + _GAP_SECCION  # gap del diagrama
    )
    disponible = AREA_H - reservado
    spec = desde_cancha_json(ficha.get("cancha") or {})
    postura = _postura_de(ficha)
    if spec is None and postura is None:
        alto_diagrama = 0.0
    else:
        alto_diagrama = max(_DIAGRAMA_MIN, min(_DIAGRAMA_MAX, disponible))

    # 3) Maquetar de arriba hacia abajo.
    hoja = _Hoja()
    hoja.texto(titulo, fuente="Helvetica-Bold", tam=_TAM_TITULO, gap=_GAP_PARRAFO)
    if meta:
        hoja.texto(meta, fuente="Helvetica", tam=_TAM_META, gap=_GAP_PARRAFO)
    if subtitulo:
        hoja.texto(subtitulo, fuente="Helvetica", tam=_TAM_SUBTITULO, gap=_GAP_SECCION)
    # Zona visual de la hoja. Con ilustracion de tecnica se parte en dos paneles
    # (ilustracion a la izquierda, cancha a la derecha) en la misma banda: asi la
    # ficha ensena el pie de apoyo, la superficie de contacto, la orientacion del
    # cuerpo y la trayectoria del balon sin gastar mas alto de hoja.
    titulo_postura = str(getattr(postura, "titulo", "") or "").strip() or titulo
    if spec is not None and postura is not None:
        hoja.paneles(
            postura,
            spec,
            alto_diagrama,
            titulo_izq=titulo_postura,
            titulo_der=titulo,
            gap=_GAP_SECCION,
        )
    elif postura is not None:
        hoja.diagrama(postura, alto_diagrama, titulo=titulo_postura, gap=_GAP_SECCION)
    elif spec is not None:
        hoja.diagrama(spec, alto_diagrama, titulo=titulo, gap=_GAP_SECCION)

    # Dosis / montaje.
    hoja.texto("Dosis y montaje", fuente="Helvetica-Bold", tam=_TAM_CUERPO, gap=_GAP_PARRAFO)
    for linea in lineas_dosis:
        hoja.texto(linea, fuente="Helvetica", tam=_TAM_CUERPO, gap=0.0)
    hoja.top -= _GAP_SECCION

    # Rejilla de QR (una celda por Media_Item).
    if media:
        _colocar_rejilla(hoja, media, matrices, ficha_id=ficha_id)

    return PaginaRender(
        folio=folio,
        capitulo_id=CAPITULO_ID,
        capitulo_titulo=TITULO,
        plantilla=Plantilla.APENDICE_QR,
        titulo_ficha=titulo,
        elementos=hoja.elementos,
        anotaciones=hoja.anotaciones,
    )


def _colocar_rejilla(
    hoja: _Hoja,
    media: list[dict[str, Any]],
    matrices: list[Any],
    *,
    ficha_id: str,
) -> None:
    """Coloca el encabezado y la cuadricula de QR (un QR por Media_Item).

    Cada celda lleva el QR (matriz ya verificada offline), una leyenda con el
    tipo y titulo del enlace, y una anotacion `/Link` clicable hacia la URL
    (Req 9.6), con su rectangulo dentro de la pagina.
    """
    hoja.texto(
        "Videos y busquedas (escanea el QR)",
        fuente="Helvetica-Bold",
        tam=_TAM_CUERPO,
        gap=_GAP_PARRAFO,
    )
    columnas, _filas, ancho_celda, alto_caption = _dim_rejilla(media)
    fila_alto = LADO_QR + 2.0 + alto_caption + _GAP_PARRAFO
    top_fila = hoja.top
    for indice, (item, matriz) in enumerate(zip(media, matrices)):
        col = indice % columnas
        if col == 0 and indice > 0:
            top_fila -= fila_alto
        x_celda = AREA_X + col * ancho_celda
        y_qr = top_fila - LADO_QR
        hoja.elementos.append(
            ElementoRender(
                tipo=TipoElemento.QR,
                x=x_celda,
                y=y_qr,
                w=LADO_QR,
                h=LADO_QR,
                datos=QRDatos(url=str(item.get("url", "")), matriz=matriz),
            )
        )
        # Anotacion /Link clicable hacia la URL, dentro de la pagina (Req 9.6).
        hoja.anotaciones.append(
            Anotacion(
                uri=str(item.get("url", "")),
                rect=(x_celda, y_qr, x_celda + LADO_QR, y_qr + LADO_QR),
                ficha_id=ficha_id,
            )
        )
        # Leyenda debajo del QR.
        caption = _caption_media(item)
        cap_elem = ElementoRender(
            tipo=TipoElemento.TEXTO,
            x=x_celda,
            y=0.0,
            w=ancho_celda - 6.0,
            h=alto_caption,
            datos=TextoDatos(texto=caption, fuente="Helvetica", tamano=_TAM_CAPTION),
        )
        cap_elem.y = y_qr - 2.0 - alto_caption
        hoja.elementos.append(cap_elem)
    hoja.top = top_fila - fila_alto


# --------------------------------------------------------------------------- #
# API publica
# --------------------------------------------------------------------------- #


def modelo(fichas_json: list[dict[str, Any]] | None = None) -> list[PaginaRender]:
    """Modelo_Paginas del Target_PDF_Guia: una `PaginaRender` por Ficha_JSON.

    Usa por defecto las 15 Ficha_JSON reales del Catalogo_JSON (via
    `cap10_fundamentos.fichas_json()`). Cada QR se genera y **verifica offline**
    durante la construccion, asi que el modelo solo se produce entero si todos
    los QR pasan el round-trip. Los folios se asignan consecutivos desde 1.
    """
    crudas = cap10_fundamentos.fichas_json() if fichas_json is None else fichas_json
    render: list[PaginaRender] = []
    for indice, ficha in enumerate(crudas, start=1):
        render.append(_pagina_ficha(ficha, indice))
    return render


def escribir(
    ruta: str,
    *,
    comprimir: bool = True,
    fichas_json: list[dict[str, Any]] | None = None,
    titulo: str = "Guia imprimible Sub-17",
) -> list[PaginaRender]:
    """Genera el modelo del Target_PDF_Guia y lo escribe como PDF en `ruta`.

    Devuelve el Modelo_Paginas emitido (util para verificar el conteo de hojas
    y para las pruebas). Import diferido de `build_pdf` para no acoplar la
    construccion del modelo con el Motor_PDF.
    """
    from . import build_pdf

    paginas = modelo(fichas_json)
    build_pdf.escribir_pdf(paginas, ruta, comprimir=comprimir, titulo=titulo)
    return paginas
