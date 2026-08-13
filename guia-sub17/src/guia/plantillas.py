"""Plantillas de página: funciones puras `(datos, ctx) -> list[PaginaPlantilla]`.

Cada plantilla convierte un dato de contenido en una o más páginas de
`ElementoRender` ya posicionados dentro del área imprimible, **midiendo toda
altura con `afm.py`** (nunca estimando). Son **funciones puras**: no tocan el
`Cursor`, no mutan estado global y no mutan su `ctx`; dado el mismo `datos` y el
mismo `ctx` devuelven exactamente los mismos elementos. Esto permite verificar
las propiedades de maquetación (cabida, coordenadas, cortes) sin abrir un PDF.

El contrato del diseño es `(datos, ctx) -> list[ElementoRender]` «con altura
consumida conocida». Aquí se materializa como `list[PaginaPlantilla]`: cada
`PaginaPlantilla` agrupa los `ElementoRender` de **una** página y expone la
`altura` consumida dentro del área. Las plantillas de página fija (`portada`,
`portadillaCapitulo`, `laminaVertical`) devuelven exactamente una página; las de
flujo (`texto`, `ficha`) devuelven las que hagan falta; y las que **cortan**
(`tabla` por filas repitiendo cabecera, `apendiceQR` por celdas) devuelven una
página por bloque cortado. `fichaDoble` devuelve dos páginas (par: diagrama y
pasos; impar: variantes, errores y QR), según la tabla de plantillas del diseño.

El `Enum Plantilla` y el modelo `ElementoRender`/`PaginaRender` viven en
`layout.py`; aquí se reexporta `Plantilla` y se declara `REGISTRO_PLANTILLAS`,
que asocia cada valor del enum con su función constructora.

Sin `assert` en producción (los borra `python -O`): un elemento más alto que el
área imprimible es irreparable y se reporta con
`ErrorLayout('E_DESBORDE_TEXTO')`.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum

from . import afm
from .errores import E_DESBORDE_TEXTO, ErrorLayout
from .layout import (
    AREA_H,
    AREA_W,
    AREA_X,
    AREA_Y,
    INTERLINEADO,
    Anotacion,
    ElementoRender,
    Plantilla,
    TextoDatos,
    TipoElemento,
)

__all__ = [
    "Plantilla",
    "PaginaPlantilla",
    "CtxPlantilla",
    "RectDatos",
    "LineaDatos",
    "DiagramaDatos",
    "QRDatos",
    "FilaTablaDatos",
    "DatosPortada",
    "DatosPortadilla",
    "DatosTabla",
    "DatosLamina",
    "EntradaQR",
    "DatosApendiceQR",
    "DatosTexto",
    "EntradaIndice",
    "DatosIndice",
    "ENTRADAS_POR_PAGINA",
    "FOLIO_PLACEHOLDER",
    "portada",
    "portadilla_capitulo",
    "ficha",
    "ficha_doble",
    "tabla",
    "lamina_vertical",
    "apendice_qr",
    "texto",
    "indice",
    "REGISTRO_PLANTILLAS",
]


# --------------------------------------------------------------------------- #
# Constantes del índice de dos pasadas (tarea 5.4)
# --------------------------------------------------------------------------- #

#: Número fijo de entradas por página del índice. La reserva de páginas del
#: índice se calcula con `math.ceil(len(entradas) / ENTRADAS_POR_PAGINA)` (ver
#: `guia.indice`). El valor es conservador: cada entrada ocupa una sola línea
#: (el título se recorta si no cabe), así que `ENTRADAS_POR_PAGINA` entradas
#: caben siempre en el área imprimible y el índice ocupa **exactamente** el
#: número de páginas reservado, sin depender de los folios impresos. Esa
#: independencia es lo que hace estable el punto fijo del paginador.
ENTRADAS_POR_PAGINA: int = 30

#: Marcador de posición de folio de la primera pasada. Se mide con las mismas
#: métricas AFM que cualquier folio real; al ser de 3 dígitos es el más ancho
#: posible en el rango publicable [1, 300], de modo que un folio real nunca es
#: más ancho que el placeholder y la columna de folio conserva su ancho fijo.
FOLIO_PLACEHOLDER: str = "000"


# --------------------------------------------------------------------------- #
# Contexto de maquetación y contenedor de página
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class CtxPlantilla:
    """Geometría del área imprimible y tipografía por defecto de una plantilla.

    `x` es el borde izquierdo; `ancho` el ancho útil; `y_tope` el borde superior
    del área (coordenada Y de la parte de arriba, origen abajo-izquierda) y
    `alto` la altura disponible. Se derivan por defecto de las constantes de
    `layout.py`. Los tamaños tipográficos permiten a las plantillas medir con
    `afm.py` de forma consistente con el motor.
    """

    x: float = AREA_X
    ancho: float = AREA_W
    y_tope: float = AREA_Y + AREA_H
    alto: float = AREA_H
    fuente_cuerpo: str = "Helvetica"
    fuente_titulo: str = "Helvetica-Bold"
    tam_cuerpo: float = 10.0
    tam_titulo: float = 16.0
    interlineado: float = INTERLINEADO

    @property
    def y_base(self) -> float:
        """Coordenada Y del borde inferior del área imprimible."""
        return self.y_tope - self.alto


#: Contexto por defecto reutilizable (es inmutable, así que compartirlo es seguro).
_CTX_POR_DEFECTO = CtxPlantilla()


def _ctx(ctx: CtxPlantilla | None) -> CtxPlantilla:
    return _CTX_POR_DEFECTO if ctx is None else ctx


@dataclass(slots=True)
class PaginaPlantilla:
    """Los `ElementoRender` de una página y la altura que consumen.

    `altura` es la distancia vertical, en puntos, entre el borde superior del
    área y el borde inferior del último elemento colocado. Las anotaciones
    (`/Link`) que la página necesite viajan aparte para que el motor las asocie.
    """

    elementos: list[ElementoRender] = field(default_factory=list)
    altura: float = 0.0
    anotaciones: list[Anotacion] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Payloads de elementos no textuales
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class RectDatos:
    """Relleno y/o borde de un `ElementoRender` de tipo RECT."""

    relleno: str | None = None
    borde: str | None = None
    grosor: float = 0.5


@dataclass(slots=True)
class LineaDatos:
    """Segmento horizontal de un `ElementoRender` de tipo LINEA."""

    color: str = "#111111"
    grosor: float = 0.5


@dataclass(slots=True)
class DiagramaDatos:
    """Envuelve el spec de diagrama que dibujará el Motor_Diagramas."""

    spec: object
    titulo: str | None = None


@dataclass(slots=True)
class QRDatos:
    """Matriz QR (o su URL) para un `ElementoRender` de tipo QR."""

    url: str
    matriz: object = None


@dataclass(slots=True)
class FilaTablaDatos:
    """Una fila de tabla: celdas, anchos de columna y si es la cabecera."""

    celdas: tuple[str, ...]
    anchos: tuple[float, ...]
    es_cabecera: bool = False
    fuente: str = "Helvetica"
    tam: float = 10.0


# --------------------------------------------------------------------------- #
# Payloads de entrada de cada plantilla
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class DatosPortada:
    titulo: str
    subtitulo: str = ""
    lede: str = ""
    pie: str = ""


@dataclass(slots=True)
class DatosPortadilla:
    numero: str
    titulo: str
    bajada: str = ""


@dataclass(slots=True)
class DatosTabla:
    cabecera: Sequence[str]
    filas: Sequence[Sequence[str]]
    anchos: Sequence[float] | None = None
    titulo: str | None = None


@dataclass(slots=True)
class DatosLamina:
    titulo: str
    bajada: str = ""
    items: Sequence[str] = ()
    fondo: str = "rosa"


@dataclass(slots=True)
class EntradaQR:
    titulo: str
    url: str
    matriz: object = None


@dataclass(slots=True)
class DatosApendiceQR:
    entradas: Sequence[EntradaQR]
    titulo: str | None = None
    columnas: int = 3


@dataclass(slots=True)
class DatosTexto:
    parrafos: Sequence[str]
    titulo: str | None = None


@dataclass(slots=True)
class EntradaIndice:
    """Una línea del índice: título, capítulo al que apunta y nivel de sangría.

    `capitulo_id` es la clave con la que se busca el folio real en el
    `Mapa_Paginas` (capítulo → folio de su portadilla). `nivel` 0 es un capítulo
    y `nivel` 1 una subsección (p. ej. cada `Modulo_Posicion`); solo afecta a la
    sangría, no a la altura de la fila.
    """

    titulo: str
    capitulo_id: str
    nivel: int = 0


@dataclass(slots=True)
class DatosIndice:
    """Payload de la plantilla `indice`.

    `folios` es el `Mapa_Paginas` (capítulo → folio inicial). Cuando es `None`
    (primera pasada) cada entrada se dibuja con el placeholder `FOLIO_PLACEHOLDER`
    en la columna de folio de ancho fijo; en la segunda pasada trae los folios
    reales. La altura de cada fila no depende del folio, así que el índice ocupa
    el mismo número de páginas en ambas pasadas.
    """

    entradas: Sequence[EntradaIndice]
    folios: Mapping[str, int] | None = None
    titulo: str | None = "Índice"


# --------------------------------------------------------------------------- #
# Medición de alturas con afm.py
# --------------------------------------------------------------------------- #

_ESPACIO_PARRAFO: float = 4.0
_ESPACIO_SECCION: float = 8.0
_PAD_CELDA: float = 3.0


def _alto_texto(
    texto: str, ancho: float, fuente: str, tam: float, interlineado: float
) -> float:
    """Altura en puntos de `texto` envuelto a `ancho` (mide con `afm.envolver`)."""
    if ancho <= 0.0:
        raise ErrorLayout(
            f"ancho de caja no positivo para texto: {ancho!r}",
            codigo=E_DESBORDE_TEXTO,
            detalle={"ancho": f"{ancho:.3f}"},
        )
    lineas = afm.envolver(texto, ancho, fuente, tam)
    n = len(lineas) if lineas else 1
    return n * tam * interlineado


def _alto_fila(fila: FilaTablaDatos, interlineado: float) -> float:
    """Altura de una fila de tabla: la celda más alta más el relleno vertical."""
    max_lineas = 1
    for celda, ancho in zip(fila.celdas, fila.anchos):
        util = ancho - 2.0 * _PAD_CELDA
        if util <= 0.0:
            util = ancho
        lineas = afm.envolver(str(celda), util, fila.fuente, fila.tam)
        max_lineas = max(max_lineas, len(lineas) if lineas else 1)
    return max_lineas * fila.tam * interlineado + 2.0 * _PAD_CELDA


# --------------------------------------------------------------------------- #
# Constructor de flujo vertical con corte de página
# --------------------------------------------------------------------------- #


class _Flujo:
    """Acumula elementos de arriba hacia abajo y corta en páginas al desbordar.

    Es un ayudante **local** a la construcción de una plantilla: cada plantilla
    crea el suyo, de modo que las funciones siguen siendo puras respecto de sus
    argumentos (no hay estado global). Un elemento más alto que el área entera
    es irreparable y lanza `ErrorLayout('E_DESBORDE_TEXTO')`.
    """

    __slots__ = ("ctx", "paginas", "_elems", "_anots", "_top", "_encabezado")

    def __init__(self, ctx: CtxPlantilla) -> None:
        self.ctx = ctx
        self.paginas: list[PaginaPlantilla] = []
        self._elems: list[ElementoRender] = []
        self._anots: list[Anotacion] = []
        self._top: float = ctx.y_tope
        # Fábrica opcional de elementos de cabecera a repetir en cada página.
        self._encabezado: Callable[[], None] | None = None

    # -- gestión de páginas ------------------------------------------------ #

    def _restante(self) -> float:
        return self._top - self.ctx.y_base

    def cerrar_pagina(self) -> None:
        """Cierra la página en curso (si tiene contenido) y prepara la siguiente."""
        if self._elems:
            altura = self.ctx.y_tope - self._top
            self.paginas.append(
                PaginaPlantilla(
                    elementos=self._elems,
                    altura=altura,
                    anotaciones=self._anots,
                )
            )
        self._elems = []
        self._anots = []
        self._top = self.ctx.y_tope

    def _abrir_siguiente(self) -> None:
        self.cerrar_pagina()
        if self._encabezado is not None:
            self._encabezado()

    def fijar_encabezado(self, fabrica: Callable[[], None]) -> None:
        """Registra un encabezado que se coloca ahora y al abrir cada página."""
        self._encabezado = fabrica
        fabrica()

    # -- colocación -------------------------------------------------------- #

    def poner(
        self,
        tipo: TipoElemento,
        altura: float,
        datos: object,
        *,
        x: float | None = None,
        ancho: float | None = None,
        gap: float = 0.0,
        bloque: object = None,
    ) -> ElementoRender:
        """Coloca un elemento de `altura` puntos, saltando de página si no cabe."""
        if altura > self.ctx.alto + 1e-6:
            raise ErrorLayout(
                f"bloque de {altura:.3f} pt no cabe en el area imprimible "
                f"({self.ctx.alto:.3f} pt)",
                codigo=E_DESBORDE_TEXTO,
                detalle={
                    "bloque": bloque if bloque is not None else tipo.value,
                    "folio": len(self.paginas) + 1,
                },
            )
        if self._top - altura < self.ctx.y_base - 1e-6:
            self._abrir_siguiente()
        ex = self.ctx.x if x is None else x
        ew = self.ctx.ancho if ancho is None else ancho
        elemento = ElementoRender(
            tipo=tipo,
            x=ex,
            y=self._top - altura,
            w=ew,
            h=altura,
            datos=datos,
        )
        self._elems.append(elemento)
        self._top -= altura + gap
        return elemento

    def anotar(self, anotacion: Anotacion) -> None:
        self._anots.append(anotacion)

    def separar(self, gap: float) -> None:
        """Avanza el cursor `gap` puntos sin colocar nada (si cabe en la página)."""
        if self._top - gap >= self.ctx.y_base:
            self._top -= gap

    def resultado(self) -> list[PaginaPlantilla]:
        self.cerrar_pagina()
        if not self.paginas:
            self.paginas.append(PaginaPlantilla(elementos=[], altura=0.0))
        return self.paginas


# --------------------------------------------------------------------------- #
# Ayudantes de alto nivel sobre el flujo
# --------------------------------------------------------------------------- #


def _poner_texto(
    flujo: _Flujo,
    texto: str,
    *,
    fuente: str,
    tam: float,
    x: float | None = None,
    ancho: float | None = None,
    gap: float = _ESPACIO_PARRAFO,
    tipo: TipoElemento = TipoElemento.PARRAFO,
    bloque: object = None,
) -> ElementoRender:
    """Mide un párrafo con `afm` y lo coloca en el flujo."""
    caja = flujo.ctx.ancho if ancho is None else ancho
    altura = _alto_texto(texto, caja, fuente, tam, flujo.ctx.interlineado)
    return flujo.poner(
        tipo,
        altura,
        TextoDatos(
            texto=texto,
            fuente=fuente,
            tamano=tam,
            interlineado=flujo.ctx.interlineado,
        ),
        x=x,
        ancho=caja,
        gap=gap,
        bloque=bloque,
    )


def _anchos_columna(datos: DatosTabla, ancho_total: float) -> tuple[float, ...]:
    """Reparte el ancho total entre columnas (proporcional o en partes iguales)."""
    n = len(datos.cabecera)
    if n <= 0:
        raise ErrorLayout(
            "una tabla necesita al menos una columna",
            codigo=E_DESBORDE_TEXTO,
            detalle={"bloque": "tabla", "folio": 1},
        )
    if datos.anchos is not None:
        pesos = [float(a) for a in datos.anchos]
        if len(pesos) != n:
            raise ErrorLayout(
                f"la tabla declara {n} columnas pero {len(pesos)} anchos",
                codigo=E_DESBORDE_TEXTO,
                detalle={"bloque": "tabla", "folio": 1},
            )
        suma = sum(pesos)
        if suma <= 0.0:
            raise ErrorLayout(
                "los anchos de columna deben sumar un valor positivo",
                codigo=E_DESBORDE_TEXTO,
                detalle={"bloque": "tabla", "folio": 1},
            )
        return tuple(ancho_total * p / suma for p in pesos)
    return tuple(ancho_total / n for _ in range(n))


def _celdas(fila: Sequence[str], n: int) -> tuple[str, ...]:
    """Normaliza una fila a `n` celdas de texto (rellena o recorta)."""
    valores = [str(c) for c in fila]
    if len(valores) < n:
        valores.extend("" for _ in range(n - len(valores)))
    return tuple(valores[:n])


# --------------------------------------------------------------------------- #
# Plantillas
# --------------------------------------------------------------------------- #


def portada(datos: DatosPortada, ctx: CtxPlantilla | None = None) -> list[PaginaPlantilla]:
    """Página de portada: título grande, subtítulo, lede y pie. Fija, 1 página."""
    c = _ctx(ctx)
    flujo = _Flujo(c)
    flujo.separar(c.alto * 0.28)
    _poner_texto(
        flujo,
        datos.titulo,
        fuente=c.fuente_titulo,
        tam=28.0,
        gap=_ESPACIO_SECCION,
        tipo=TipoElemento.TEXTO,
        bloque="portada.titulo",
    )
    if datos.subtitulo:
        _poner_texto(
            flujo, datos.subtitulo, fuente=c.fuente_titulo, tam=15.0, gap=_ESPACIO_SECCION
        )
    if datos.lede:
        _poner_texto(flujo, datos.lede, fuente=c.fuente_cuerpo, tam=11.0, gap=_ESPACIO_SECCION)
    if datos.pie:
        _poner_texto(flujo, datos.pie, fuente=c.fuente_cuerpo, tam=9.0, gap=0.0)
    return flujo.resultado()


def portadilla_capitulo(
    datos: DatosPortadilla, ctx: CtxPlantilla | None = None
) -> list[PaginaPlantilla]:
    """Portadilla de capítulo: número grande, título y bajada. Fija, 1 página."""
    c = _ctx(ctx)
    flujo = _Flujo(c)
    flujo.separar(c.alto * 0.22)
    _poner_texto(
        flujo,
        datos.numero,
        fuente=c.fuente_titulo,
        tam=40.0,
        gap=_ESPACIO_SECCION,
        tipo=TipoElemento.TEXTO,
        bloque="portadilla.numero",
    )
    _poner_texto(
        flujo,
        datos.titulo,
        fuente=c.fuente_titulo,
        tam=22.0,
        gap=_ESPACIO_SECCION,
        tipo=TipoElemento.TEXTO,
        bloque="portadilla.titulo",
    )
    if datos.bajada:
        _poner_texto(flujo, datos.bajada, fuente=c.fuente_cuerpo, tam=11.0, gap=0.0)
    return flujo.resultado()


def _diagrama_ficha(flujo: _Flujo, ficha_obj: object, alto: float) -> None:
    """Coloca el Diagrama_Cancha de una ficha (si lo tiene) con altura `alto`."""
    spec = getattr(ficha_obj, "diagrama", None)
    if spec is None:
        return
    flujo.poner(
        TipoElemento.DIAGRAMA,
        alto,
        DiagramaDatos(spec=spec, titulo=getattr(ficha_obj, "titulo", None)),
        gap=_ESPACIO_SECCION,
        bloque="ficha.diagrama",
    )


def _ilustracion_ficha(flujo: _Flujo, ficha_obj: object, alto: float) -> None:
    """Coloca la ilustracion de tecnica de la ficha (`postura`), si la tiene.

    Es el **mismo** tipo de elemento que el Diagrama_Cancha (`DIAGRAMA` con su
    `DiagramaSpec`), asi que los dos motores ya la dibujan sin cambios: `viz.py`
    la emite como SVG inline accesible y `draw.py` como operadores PDF. Por eso
    la zona visual de la ficha aparece a la vez en el HTML por capitulo y en el
    PDF sin duplicar codigo de render (decision de arquitectura del lote 33.1).

    Que una ficha no lleve ilustracion es un resultado legitimo: no toda ficha es
    de golpeo. En ese caso no se coloca nada.
    """
    spec = getattr(ficha_obj, "postura", None)
    if spec is None:
        return
    titulo = getattr(spec, "titulo", None) or getattr(ficha_obj, "titulo", None)
    flujo.poner(
        TipoElemento.DIAGRAMA,
        alto,
        DiagramaDatos(spec=spec, titulo=titulo),
        gap=_ESPACIO_SECCION,
        bloque="ficha.ilustracion",
    )


def _pasos_ficha(flujo: _Flujo, ficha_obj: object, c: CtxPlantilla) -> None:
    """Coloca el encabezado 'Paso a paso' y los pasos numerados de una ficha."""
    pasos = getattr(ficha_obj, "pasos", None) or ()
    _poner_texto(
        flujo, "Paso a paso", fuente=c.fuente_titulo, tam=11.0, gap=_ESPACIO_PARRAFO
    )
    for indice, paso in enumerate(pasos, start=1):
        _poner_texto(
            flujo,
            f"{indice}. {paso}",
            fuente=c.fuente_cuerpo,
            tam=c.tam_cuerpo,
            gap=_ESPACIO_PARRAFO,
        )


def _valor_montaje(montaje: object, clave: str) -> str:
    """Lee `clave` de un montaje, sea dict o objeto con atributos."""
    if isinstance(montaje, dict):
        valor = montaje.get(clave)
    else:
        valor = getattr(montaje, clave, None)
    return str(valor).strip() if valor else ""


def _texto_montaje(ficha_obj: object) -> str:
    """Línea de dosis a partir del `montaje` (cuándo, duración, jugadoras, material).

    Las fichas del catálogo declaran su dosis en texto (`cuando`, `duracion`,
    `jugadoras`, `material`), no en series y repeticiones, y el adaptador la
    deja en `montaje`. Sin esta lectura la dosis no se imprimía en ninguna
    ficha del catálogo aunque estuviera completa en el JSON.
    """
    montaje = getattr(ficha_obj, "montaje", None)
    if montaje is None:
        return ""
    etiquetas = (
        ("cuando", "cuándo"),
        ("duracion", "duración"),
        ("jugadoras", "jugadoras"),
        ("material", "material"),
    )
    partes = [
        f"{etiqueta} {valor}"
        for clave, etiqueta in etiquetas
        if (valor := _valor_montaje(montaje, clave))
    ]
    return " · ".join(partes)


def _texto_dosis(ficha_obj: object) -> str:
    """Arma una línea legible de dosis a partir del objeto ficha."""
    dosis = getattr(ficha_obj, "dosis", None)
    if dosis is None:
        return _texto_montaje(ficha_obj)
    partes: list[str] = []
    series = getattr(dosis, "series", None)
    repes = getattr(dosis, "repeticiones", None)
    segundos = getattr(dosis, "segundos", None)
    minutos = getattr(dosis, "minutos", None)
    descanso = getattr(dosis, "descanso", None)
    if series is not None:
        partes.append(f"{series} series")
    if repes is not None:
        partes.append(f"{repes} repeticiones")
    if segundos is not None:
        partes.append(f"{segundos} s")
    if minutos is not None:
        partes.append(f"{minutos} min")
    if descanso:
        partes.append(f"descanso {descanso}")
    if not partes:
        return _texto_montaje(ficha_obj)
    return " · ".join(partes)


#: Texto fijo del ancla de cada video de ejemplo. Sin acento a propósito: todo
#: literal del PDF pasa por WinAnsi (cp1252) y este mismo rótulo se usa en el
#: sitio y en el PDF de fichas, para que las tres superficies digan lo mismo.
ETIQUETA_DEMOSTRACION: str = "Ver demostracion"

#: Encabezado del bloque de videos de una ficha.
TITULO_MEDIA: str = "Videos y enlaces"


def _poner_media_ficha(
    flujo: _Flujo, media: Sequence[Mapping[str, object]], ficha_id: str
) -> None:
    """Coloca un QR clicable por cada Media_Item de la ficha.

    Cada entrada rinde `<titulo> - Ver demostracion`, su QR y la URL en texto,
    con la anotación `/Link` correspondiente (Req 9.6). El pie es el mismo que
    usa el PDF de fichas, así que el sitio, el PDF y el HTML por capítulo dicen
    lo mismo. No se afirma nada sobre el contenido del video: es un enlace de
    ejemplo.
    """
    entradas = [m for m in media if m.get("url")]
    if not entradas:
        return
    _poner_texto(
        flujo, TITULO_MEDIA, fuente=flujo.ctx.fuente_titulo, tam=11.0,
        gap=_ESPACIO_SECCION,
    )
    for item in entradas:
        titulo = str(item.get("titulo") or "Video").strip()
        _poner_qr(
            flujo,
            str(item["url"]),
            f"{titulo} - {ETIQUETA_DEMOSTRACION}",
            ficha_id,
        )


def ficha(
    ficha_obj: object,
    ctx: CtxPlantilla | None = None,
    *,
    media: Sequence[Mapping[str, object]] | None = None,
) -> list[PaginaPlantilla]:
    """Ficha en una página: diagrama arriba, pasos, dosis y observación abajo.

    Fluye a más páginas solo si el contenido no cabe (para fichas con muchos
    pasos existe `ficha_doble`). `ficha_obj` es un `FichaEjercicio` o cualquier
    objeto con los atributos `titulo`, `objetivo`, `pasos`, `dosis`,
    `observacion`, `diagrama` y, opcionalmente, `video_url`.

    `media`, si se da, es la lista de Media_Item **cruda** de la ficha: rinde un
    QR clicable por enlace. Se pasa aparte porque el modelo interno solo guarda
    el primer enlace en `video_url`, y una ficha puede tener varios.
    """
    c = _ctx(ctx)
    flujo = _Flujo(c)
    titulo = getattr(ficha_obj, "titulo", "") or ""
    _poner_texto(
        flujo, titulo, fuente=c.fuente_titulo, tam=14.0, gap=_ESPACIO_PARRAFO,
        tipo=TipoElemento.TEXTO, bloque="ficha.titulo",
    )
    objetivo = getattr(ficha_obj, "objetivo", "") or ""
    if objetivo:
        _poner_texto(
            flujo, objetivo, fuente=c.fuente_cuerpo, tam=c.tam_cuerpo, gap=_ESPACIO_SECCION
        )
    # Zona visual: primero la ilustracion de tecnica (cuando la ficha la trae) y
    # despues el diagrama de cancha.
    _ilustracion_ficha(flujo, ficha_obj, min(c.alto * 0.34, 240.0))
    _diagrama_ficha(flujo, ficha_obj, min(c.alto * 0.42, 300.0))
    _pasos_ficha(flujo, ficha_obj, c)
    dosis_txt = _texto_dosis(ficha_obj)
    if dosis_txt:
        _poner_texto(
            flujo, f"Dosis: {dosis_txt}", fuente=c.fuente_titulo, tam=c.tam_cuerpo,
            gap=_ESPACIO_PARRAFO,
        )
    observacion = getattr(ficha_obj, "observacion", "") or ""
    if observacion:
        _poner_texto(
            flujo,
            f"Qué mira la compañera: {observacion}",
            fuente=c.fuente_cuerpo,
            tam=c.tam_cuerpo,
            gap=_ESPACIO_PARRAFO,
        )
    if media:
        _poner_media_ficha(flujo, media, getattr(ficha_obj, "id", "") or "")
    return flujo.resultado()


def ficha_doble(ficha_obj: object, ctx: CtxPlantilla | None = None) -> list[PaginaPlantilla]:
    """Ficha extensa en dos páginas.

    Página par: título, objetivo, diagrama y pasos. Página impar: variantes de
    espacio, errores comunes y, si hay video, el código QR con su enlace
    clicable. Sigue la fila `fichaDoble` de la tabla de plantillas del diseño.
    """
    c = _ctx(ctx)

    # --- Página 1: diagrama + pasos --------------------------------------- #
    p1 = _Flujo(c)
    titulo = getattr(ficha_obj, "titulo", "") or ""
    _poner_texto(
        p1, titulo, fuente=c.fuente_titulo, tam=14.0, gap=_ESPACIO_PARRAFO,
        tipo=TipoElemento.TEXTO, bloque="fichaDoble.titulo",
    )
    objetivo = getattr(ficha_obj, "objetivo", "") or ""
    if objetivo:
        _poner_texto(p1, objetivo, fuente=c.fuente_cuerpo, tam=c.tam_cuerpo, gap=_ESPACIO_SECCION)
    _ilustracion_ficha(p1, ficha_obj, min(c.alto * 0.30, 220.0))
    _diagrama_ficha(p1, ficha_obj, min(c.alto * 0.42, 300.0))
    _pasos_ficha(p1, ficha_obj, c)
    paginas = p1.resultado()

    # --- Página 2: variantes, errores, QR --------------------------------- #
    p2 = _Flujo(c)
    _poner_texto(
        p2, f"{titulo} (continuación)", fuente=c.fuente_titulo, tam=12.0,
        gap=_ESPACIO_SECCION, tipo=TipoElemento.TEXTO, bloque="fichaDoble.cont",
    )
    for campo, etiqueta in (
        ("espacio_reducido", "Espacio reducido"),
        ("espacio_completo", "Espacio completo"),
    ):
        variante = getattr(ficha_obj, campo, None)
        ajuste = getattr(variante, "ajuste", None)
        if ajuste:
            ancho_m = getattr(variante, "ancho_m", 0.0)
            largo_m = getattr(variante, "largo_m", 0.0)
            _poner_texto(
                p2,
                f"{etiqueta} ({ancho_m:g} x {largo_m:g} m): {ajuste}",
                fuente=c.fuente_cuerpo,
                tam=c.tam_cuerpo,
                gap=_ESPACIO_PARRAFO,
            )
    errores = getattr(ficha_obj, "errores_comunes", None) or ()
    if errores:
        _poner_texto(
            p2, "Errores comunes", fuente=c.fuente_titulo, tam=11.0, gap=_ESPACIO_PARRAFO
        )
        for err in errores:
            _poner_texto(
                p2, f"• {err}", fuente=c.fuente_cuerpo, tam=c.tam_cuerpo, gap=_ESPACIO_PARRAFO
            )
    video = getattr(ficha_obj, "video_url", None)
    if video:
        _poner_qr(p2, video, getattr(ficha_obj, "video_titulo", None) or "Ver video",
                  getattr(ficha_obj, "id", "") or "")
    paginas.extend(p2.resultado())
    return paginas


def _poner_qr(flujo: _Flujo, url: str, titulo: str, ficha_id: str) -> None:
    """Coloca un QR (con matriz generada por `qr.py`) y su enlace clicable."""
    from . import qr  # import diferido: qr no es dependencia de la maquetación

    matriz = qr.codificar(url)
    lado = 96.0
    _poner_texto(flujo, titulo, fuente=flujo.ctx.fuente_titulo, tam=11.0, gap=_ESPACIO_PARRAFO)
    elem = flujo.poner(
        TipoElemento.QR,
        lado,
        QRDatos(url=url, matriz=matriz),
        ancho=lado,
        gap=_ESPACIO_PARRAFO,
        bloque="qr",
    )
    flujo.anotar(
        Anotacion(
            uri=url,
            rect=(elem.x, elem.y, elem.x + lado, elem.y + lado),
            ficha_id=ficha_id,
        )
    )
    _poner_texto(flujo, url, fuente=flujo.ctx.fuente_cuerpo, tam=8.0, gap=_ESPACIO_PARRAFO)


def tabla(datos: DatosTabla, ctx: CtxPlantilla | None = None) -> list[PaginaPlantilla]:
    """Tabla que corta por filas y **repite la cabecera** en cada página.

    Reparte el ancho entre columnas, mide cada fila con `afm.py` y va colocando
    filas hasta que la siguiente no cabe; entonces cierra la página y reabre
    repitiendo la fila de cabecera antes de continuar (tabla de la fila `tabla`
    del diseño: decisión, indicadores, seguimiento, alimentos).
    """
    c = _ctx(ctx)
    flujo = _Flujo(c)

    if datos.titulo:
        _poner_texto(
            flujo, datos.titulo, fuente=c.fuente_titulo, tam=13.0, gap=_ESPACIO_SECCION,
            tipo=TipoElemento.TEXTO, bloque="tabla.titulo",
        )

    n = len(datos.cabecera)
    anchos = _anchos_columna(datos, c.ancho)
    fila_cabecera = FilaTablaDatos(
        celdas=_celdas(datos.cabecera, n),
        anchos=anchos,
        es_cabecera=True,
        fuente=c.fuente_titulo,
        tam=c.tam_cuerpo,
    )
    alto_cabecera = _alto_fila(fila_cabecera, c.interlineado)

    def _colocar_cabecera() -> None:
        # Se construye una instancia nueva por página para no compartir estado.
        cab = FilaTablaDatos(
            celdas=fila_cabecera.celdas,
            anchos=fila_cabecera.anchos,
            es_cabecera=True,
            fuente=fila_cabecera.fuente,
            tam=fila_cabecera.tam,
        )
        flujo.poner(TipoElemento.TABLA, alto_cabecera, cab, bloque="tabla.cabecera")

    flujo.fijar_encabezado(_colocar_cabecera)

    for i, fila in enumerate(datos.filas):
        datos_fila = FilaTablaDatos(
            celdas=_celdas(fila, n),
            anchos=anchos,
            es_cabecera=False,
            fuente=c.fuente_cuerpo,
            tam=c.tam_cuerpo,
        )
        alto = _alto_fila(datos_fila, c.interlineado)
        flujo.poner(TipoElemento.TABLA, alto, datos_fila, bloque=f"tabla.fila[{i}]")

    return flujo.resultado()


def lamina_vertical(
    datos: DatosLamina, ctx: CtxPlantilla | None = None
) -> list[PaginaPlantilla]:
    """Lámina vertical infografía rosa/negro. Fija, 1 página."""
    c = _ctx(ctx)
    flujo = _Flujo(c)
    # Fondo de la lámina cubriendo el área imprimible.
    relleno = "#150810" if datos.fondo == "negro" else "#FFF8FB"
    flujo.poner(
        TipoElemento.RECT,
        c.alto,
        RectDatos(relleno=relleno),
        gap=0.0,
        bloque="lamina.fondo",
    )
    # El fondo consume toda la altura; el texto se coloca en una segunda pasada
    # sobre el mismo espacio reiniciando el cursor.
    flujo._top = c.y_tope  # noqa: SLF001 - reposición intencional sobre el fondo
    flujo.separar(c.alto * 0.06)
    _poner_texto(
        flujo, datos.titulo, fuente=c.fuente_titulo, tam=24.0, gap=_ESPACIO_SECCION,
        tipo=TipoElemento.TEXTO, bloque="lamina.titulo",
    )
    if datos.bajada:
        _poner_texto(flujo, datos.bajada, fuente=c.fuente_cuerpo, tam=12.0, gap=_ESPACIO_SECCION)
    for item in datos.items:
        _poner_texto(
            flujo, f"• {item}", fuente=c.fuente_cuerpo, tam=12.0, gap=_ESPACIO_PARRAFO
        )
    return flujo.resultado()


def apendice_qr(
    datos: DatosApendiceQR, ctx: CtxPlantilla | None = None
) -> list[PaginaPlantilla]:
    """Rejilla de códigos QR con su URL, que **corta por celdas** entre páginas.

    Coloca las entradas en una cuadrícula de `columnas` columnas; cada celda
    lleva el QR (matriz de `qr.py`), el título y la URL en texto plano. Cuando
    la siguiente fila de celdas no cabe, salta a la página siguiente.
    """
    from . import qr  # import diferido

    c = _ctx(ctx)
    flujo = _Flujo(c)

    if datos.titulo:
        _poner_texto(
            flujo, datos.titulo, fuente=c.fuente_titulo, tam=13.0, gap=_ESPACIO_SECCION,
            tipo=TipoElemento.TEXTO, bloque="apendiceQR.titulo",
        )

    columnas = max(1, datos.columnas)
    ancho_celda = c.ancho / columnas
    lado_qr = min(ancho_celda - 8.0, 110.0)
    if lado_qr <= 0.0:
        lado_qr = ancho_celda
    tam_url = 7.0
    # Altura de una fila de celdas: QR + título + una línea de URL + relleno.
    alto_titulo = 11.0 * c.interlineado
    alto_url = tam_url * c.interlineado
    alto_fila = lado_qr + alto_titulo + alto_url + _ESPACIO_SECCION

    entradas = list(datos.entradas)
    for inicio in range(0, len(entradas), columnas):
        grupo = entradas[inicio : inicio + columnas]
        # Reservar la fila entera de un tirón para que las celdas no se separen.
        if flujo._top - alto_fila < flujo.ctx.y_base - 1e-6:  # noqa: SLF001
            flujo._abrir_siguiente()  # noqa: SLF001
        fila_top = flujo._top  # noqa: SLF001
        for j, entrada in enumerate(grupo):
            cx = c.x + j * ancho_celda
            matriz = entrada.matriz
            if matriz is None:
                matriz = qr.codificar(entrada.url)
            qr_y = fila_top - lado_qr
            elem = ElementoRender(
                tipo=TipoElemento.QR,
                x=cx,
                y=qr_y,
                w=lado_qr,
                h=lado_qr,
                datos=QRDatos(url=entrada.url, matriz=matriz),
            )
            flujo._elems.append(elem)  # noqa: SLF001
            flujo.anotar(
                Anotacion(
                    uri=entrada.url,
                    rect=(cx, qr_y, cx + lado_qr, qr_y + lado_qr),
                    ficha_id=entrada.titulo,
                )
            )
            # Título bajo el QR.
            tit_y = qr_y - alto_titulo
            flujo._elems.append(  # noqa: SLF001
                ElementoRender(
                    tipo=TipoElemento.TEXTO,
                    x=cx,
                    y=tit_y,
                    w=ancho_celda,
                    h=alto_titulo,
                    datos=TextoDatos(
                        texto=entrada.titulo,
                        fuente=c.fuente_titulo,
                        tamano=11.0,
                        interlineado=c.interlineado,
                    ),
                )
            )
            # URL en texto plano.
            url_y = tit_y - alto_url
            flujo._elems.append(  # noqa: SLF001
                ElementoRender(
                    tipo=TipoElemento.TEXTO,
                    x=cx,
                    y=url_y,
                    w=ancho_celda,
                    h=alto_url,
                    datos=TextoDatos(
                        texto=entrada.url,
                        fuente=c.fuente_cuerpo,
                        tamano=tam_url,
                        interlineado=c.interlineado,
                    ),
                )
            )
        flujo._top = fila_top - alto_fila  # noqa: SLF001

    return flujo.resultado()


def _recortar_una_linea(
    texto_str: str, ancho: float, fuente: str, tam: float
) -> str:
    """Recorta `texto_str` a una sola línea que quepa en `ancho`, con elipsis.

    Mantener cada entrada del índice en una línea hace que la altura de la fila
    no dependa del contenido ni del folio: por eso el índice ocupa el mismo
    número de páginas en las dos pasadas. Si el texto ya cabe, se devuelve tal
    cual.
    """
    if ancho <= 0.0:
        raise ErrorLayout(
            f"ancho de caja no positivo para el índice: {ancho!r}",
            codigo=E_DESBORDE_TEXTO,
            detalle={"bloque": "indice", "ancho": f"{ancho:.3f}"},
        )
    if afm.medir_texto(texto_str, fuente, tam) <= ancho:
        return texto_str
    elipsis = "\u2026"  # … (WinAnsiEncoding 0x85)
    recorte = texto_str
    while recorte and afm.medir_texto(recorte + elipsis, fuente, tam) > ancho:
        recorte = recorte[:-1]
    return recorte + elipsis if recorte else elipsis


def indice(datos: DatosIndice, ctx: CtxPlantilla | None = None) -> list[PaginaPlantilla]:
    """Índice general: una entrada por línea con su folio en columna fija.

    Corta cada `ENTRADAS_POR_PAGINA` entradas (paginación por conteo, no por
    desborde medido) y **repite el título** en cada página, de modo que el
    índice ocupa exactamente `math.ceil(len(entradas) / ENTRADAS_POR_PAGINA)`
    páginas con independencia de los folios impresos. Es la plantilla que
    consume el paginador de dos pasadas (`guia.indice`): en la primera pasada
    `datos.folios is None` y cada folio se dibuja con `FOLIO_PLACEHOLDER`; en la
    segunda trae el `Mapa_Paginas` con los folios reales, alineados a la derecha
    dentro de una columna cuyo ancho es el del placeholder de 3 dígitos.
    """
    c = _ctx(ctx)
    flujo = _Flujo(c)
    fuente = c.fuente_cuerpo
    tam = c.tam_cuerpo
    area_der = c.x + c.ancho
    # Columna de folio de ancho fijo = ancho del placeholder "000".
    folio_col = afm.medir_texto(FOLIO_PLACEHOLDER, fuente, tam)
    gap_folio = 6.0
    sangria = 14.0
    alto_linea = tam * c.interlineado

    titulo = datos.titulo

    def _encabezado() -> None:
        if titulo:
            _poner_texto(
                flujo,
                titulo,
                fuente=c.fuente_titulo,
                tam=14.0,
                gap=_ESPACIO_SECCION,
                tipo=TipoElemento.TEXTO,
                bloque="indice.titulo",
            )

    flujo.fijar_encabezado(_encabezado)

    entradas = list(datos.entradas)
    for i, entrada in enumerate(entradas):
        # Salto por conteo: exactamente ENTRADAS_POR_PAGINA entradas por página.
        if i > 0 and i % ENTRADAS_POR_PAGINA == 0:
            flujo._abrir_siguiente()  # noqa: SLF001

        indent = c.x + max(0, entrada.nivel) * sangria
        ancho_titulo = area_der - indent - folio_col - gap_folio
        if ancho_titulo <= 0.0:
            raise ErrorLayout(
                "la columna de título del índice no tiene ancho positivo",
                codigo=E_DESBORDE_TEXTO,
                detalle={"bloque": "indice", "capitulo_id": entrada.capitulo_id},
            )

        if datos.folios is None:
            folio_str = FOLIO_PLACEHOLDER
        else:
            folio_val = datos.folios.get(entrada.capitulo_id)
            folio_str = FOLIO_PLACEHOLDER if folio_val is None else str(folio_val)

        titulo_linea = _recortar_una_linea(entrada.titulo, ancho_titulo, fuente, tam)

        # Salvaguarda: una fila de una línea siempre cabe con el EPP elegido,
        # pero si no cupiera, se salta a la página siguiente antes de colocarla.
        if flujo._top - alto_linea < flujo.ctx.y_base - 1e-6:  # noqa: SLF001
            flujo._abrir_siguiente()  # noqa: SLF001

        fila_top = flujo._top  # noqa: SLF001
        fila_y = fila_top - alto_linea
        # Título (columna izquierda, con sangría por nivel).
        flujo._elems.append(  # noqa: SLF001
            ElementoRender(
                tipo=TipoElemento.TEXTO,
                x=indent,
                y=fila_y,
                w=ancho_titulo,
                h=alto_linea,
                datos=TextoDatos(
                    texto=titulo_linea,
                    fuente=fuente,
                    tamano=tam,
                    interlineado=c.interlineado,
                ),
            )
        )
        # Folio alineado a la derecha dentro de la columna de ancho fijo.
        folio_w = afm.medir_texto(folio_str, fuente, tam)
        folio_x = area_der - folio_w
        flujo._elems.append(  # noqa: SLF001
            ElementoRender(
                tipo=TipoElemento.TEXTO,
                x=folio_x,
                y=fila_y,
                w=folio_w,
                h=alto_linea,
                datos=TextoDatos(
                    texto=folio_str,
                    fuente=fuente,
                    tamano=tam,
                    interlineado=c.interlineado,
                ),
            )
        )
        flujo._top = fila_top - alto_linea  # noqa: SLF001

    return flujo.resultado()


def texto(datos: DatosTexto, ctx: CtxPlantilla | None = None) -> list[PaginaPlantilla]:
    """Sección de texto explicativo con flujo libre (corta al llenar la página)."""
    c = _ctx(ctx)
    flujo = _Flujo(c)
    if datos.titulo:
        _poner_texto(
            flujo, datos.titulo, fuente=c.fuente_titulo, tam=14.0, gap=_ESPACIO_SECCION,
            tipo=TipoElemento.TEXTO, bloque="texto.titulo",
        )
    for parrafo in datos.parrafos:
        _poner_texto(
            flujo, parrafo, fuente=c.fuente_cuerpo, tam=c.tam_cuerpo, gap=_ESPACIO_PARRAFO
        )
    return flujo.resultado()


# --------------------------------------------------------------------------- #
# Registro: Plantilla -> función constructora
# --------------------------------------------------------------------------- #

#: Asocia cada valor del `Enum Plantilla` (definido en `layout.py`) con la
#: función que lo construye. `Plantilla.INDICE` la resuelve la plantilla
#: `indice` de la tarea 5.4.
REGISTRO_PLANTILLAS: dict[Plantilla, Callable[..., list[PaginaPlantilla]]] = {
    Plantilla.PORTADA: portada,
    Plantilla.PORTADILLA_CAPITULO: portadilla_capitulo,
    Plantilla.FICHA: ficha,
    Plantilla.FICHA_DOBLE: ficha_doble,
    Plantilla.TABLA: tabla,
    Plantilla.LAMINA_VERTICAL: lamina_vertical,
    Plantilla.INDICE: indice,
    Plantilla.APENDICE_QR: apendice_qr,
    Plantilla.TEXTO: texto,
}
