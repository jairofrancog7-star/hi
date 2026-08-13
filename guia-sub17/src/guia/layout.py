"""Paginador de dos pasadas: `Cursor`, área imprimible, bandas y Modelo_Paginas.

Este módulo define la **geometría de la página A4** (constantes en puntos), el
`Cursor` vertical que coloca elementos de arriba hacia abajo saltando de página
cuando el contenido no cabe, y el **Modelo_Paginas**: la lista de
`PaginaRender` que es la *única frontera* entre el paginador y los motores de
salida (`build_pdf.py`, `build_html.py`). Ningún motor conoce el catálogo ni el
cursor; solo saben leer `PaginaRender`. Esto permite verificar las propiedades
de maquetación (desborde, coordenadas, conteos) sin abrir un PDF.

Decisiones de diseño (ver design.md, "Motor de paginación con cursor vertical"
y "Frontera clave: el Modelo_Paginas"):

* Toda altura se **mide** con `afm.py`, nunca se estima: `medir_elemento`
  envuelve el texto con `afm.envolver` y multiplica por el interlineado. El
  desborde vertical es imposible dentro del cursor por construcción.
* Todo salto de página propaga `capitulo_id`, `capitulo_titulo` y
  `titulo_ficha` (Req 1.5 y 1.7 por construcción, no por revisión).
* `mantener_juntos` es un **context manager** (`contextlib.contextmanager`) con
  punto de guardado y un solo reintento: si el grupo indivisible no cabe en lo
  que queda de página, se restaura el estado y se salta a una página nueva
  antes de colocarlo, evitando viudas (diagrama sin su leyenda, cabecera de
  tabla sin su primera fila, título de ficha sin su objetivo).
* Un bloque más alto que el área imprimible completa es un error irreparable:
  `ErrorLayout('E_DESBORDE_TEXTO')` con el folio y el bloque afectado. Nunca se
  usa `assert` (`python -O` los borraría): todo invariante se comprueba con
  `raise`.

Las **plantillas de página** (tarea 5.2) y el **índice de dos pasadas**
(tarea 5.4) se construyen sobre esta API sin modificarla.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
from enum import Enum

from . import afm
from .errores import E_DESBORDE_TEXTO, ErrorLayout

__all__ = [
    "A4_W",
    "A4_H",
    "MARGEN_SUP",
    "MARGEN_INF",
    "MARGEN_IZQ",
    "MARGEN_DER",
    "BANDA_SUP",
    "BANDA_INF",
    "AREA_X",
    "AREA_Y",
    "AREA_W",
    "AREA_H",
    "INTERLINEADO",
    "Plantilla",
    "TipoElemento",
    "TextoDatos",
    "ElementoRender",
    "Anotacion",
    "PaginaRender",
    "Cursor",
    "medir_elemento",
]


# --------------------------------------------------------------------------- #
# Geometría de la página A4 (unidades: puntos PostScript, 1 pt = 1/72 pulgada)
# --------------------------------------------------------------------------- #

A4_W: float = 595.276
A4_H: float = 841.890

MARGEN_SUP: float = 56.0
MARGEN_INF: float = 48.0
MARGEN_IZQ: float = 46.0
MARGEN_DER: float = 46.0

BANDA_SUP: float = 18.0  # encabezado de capitulo
BANDA_INF: float = 16.0  # folio + capitulo

# Área imprimible: rectángulo donde el cursor coloca contenido, ya descontadas
# las bandas de encabezado y pie. Origen abajo-izquierda (convención PDF).
AREA_X: float = MARGEN_IZQ
AREA_Y: float = MARGEN_INF + BANDA_INF
AREA_W: float = A4_W - MARGEN_IZQ - MARGEN_DER
AREA_H: float = A4_H - MARGEN_SUP - BANDA_SUP - MARGEN_INF - BANDA_INF

# Factor de interlineado por defecto para texto fluido.
INTERLINEADO: float = 1.2


# --------------------------------------------------------------------------- #
# Enumeraciones cerradas
# --------------------------------------------------------------------------- #


class Plantilla(str, Enum):
    """Plantillas de página. Su implementación concreta es la tarea 5.2."""

    PORTADA = "portada"
    PORTADILLA_CAPITULO = "portadillaCapitulo"
    FICHA = "ficha"
    FICHA_DOBLE = "fichaDoble"
    TABLA = "tabla"
    LAMINA_VERTICAL = "laminaVertical"
    INDICE = "indice"
    APENDICE_QR = "apendiceQR"
    TEXTO = "texto"


class TipoElemento(str, Enum):
    """Tipos de elemento que un motor sabe dibujar a partir de `PaginaRender`."""

    TEXTO = "texto"
    PARRAFO = "parrafo"
    LINEA = "linea"
    RECT = "rect"
    DIAGRAMA = "diagrama"
    QR = "qr"
    TABLA = "tabla"


# Tipos cuya altura se deriva midiendo texto con `afm.py`.
_TIPOS_TEXTO: frozenset[TipoElemento] = frozenset(
    {TipoElemento.TEXTO, TipoElemento.PARRAFO}
)


# --------------------------------------------------------------------------- #
# Payload de texto y dataclasses del Modelo_Paginas (todas con slots=True)
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class TextoDatos:
    """Payload de un `ElementoRender` de tipo TEXTO o PARRAFO.

    `medir_elemento` envuelve `texto` a la anchura de la caja con `afm.envolver`
    y calcula la altura como `nlineas * tamano * interlineado`. Mantener la
    fuente y el tamaño aquí hace que la medición sea idéntica a la que hará el
    motor al dibujar.
    """

    texto: str
    fuente: str = "Helvetica"
    tamano: float = 10.0
    interlineado: float = INTERLINEADO


@dataclass(slots=True)
class ElementoRender:
    """Un elemento colocado en una página, con caja y payload por tipo.

    `x`, `y` son la esquina inferior-izquierda del elemento (origen abajo-izq).
    `w`, `h` son ancho y alto en puntos. `h` puede llegar en 0 para tipos de
    texto: `Cursor.colocar` lo rellena con la altura medida. Para tipos fijos
    (DIAGRAMA, QR, RECT, LINEA, TABLA) la altura debe venir declarada en `h`.
    """

    tipo: TipoElemento
    x: float = 0.0
    y: float = 0.0
    w: float = 0.0
    h: float = 0.0
    datos: object = None  # payload especifico del tipo


@dataclass(slots=True)
class Anotacion:
    """Anotación `/Link` con `/URI` y su rectángulo clicable dentro de la página."""

    uri: str
    rect: tuple[float, float, float, float]
    ficha_id: str


@dataclass(slots=True)
class PaginaRender:
    """Una página del documento. La lista de estas páginas es el Modelo_Paginas."""

    folio: int  # 1..N, consecutivo
    capitulo_id: str
    capitulo_titulo: str  # para encabezado/pie (Req 1.5)
    plantilla: Plantilla
    titulo_ficha: str | None = None  # repetido en fichas multipagina (Req 1.7)
    elementos: list[ElementoRender] = field(default_factory=list)
    anotaciones: list[Anotacion] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Medición de altura de un elemento (siempre vía afm.py)
# --------------------------------------------------------------------------- #


def medir_elemento(elemento: ElementoRender, ancho_area: float = AREA_W) -> float:
    """Altura en puntos que consume `elemento` en una caja de ancho `ancho_area`.

    Para TEXTO y PARRAFO, envuelve el texto con `afm.envolver` (misma métrica
    que usará el motor) y devuelve `nlineas * tamano * interlineado`. Para tipos
    con altura fija, devuelve `elemento.h`. Nunca estima.
    """
    ancho = elemento.w if elemento.w and elemento.w > 0.0 else ancho_area

    if elemento.tipo in _TIPOS_TEXTO:
        datos = elemento.datos
        if not isinstance(datos, TextoDatos):
            raise ErrorLayout(
                f"elemento de texto sin payload TextoDatos: {datos!r}",
                codigo=E_DESBORDE_TEXTO,
                detalle={"tipo": elemento.tipo.value},
            )
        if ancho <= 0.0:
            raise ErrorLayout(
                f"ancho de caja no positivo para texto: {ancho!r}",
                codigo=E_DESBORDE_TEXTO,
                detalle={"ancho": f"{ancho:.3f}"},
            )
        lineas = afm.envolver(datos.texto, ancho, datos.fuente, datos.tamano)
        n = len(lineas) if lineas else 1
        return n * datos.tamano * datos.interlineado

    return elemento.h if elemento.h and elemento.h > 0.0 else 0.0


# --------------------------------------------------------------------------- #
# Cursor vertical y Modelo_Paginas
# --------------------------------------------------------------------------- #

# Claves de contexto que todo salto de página propaga.
_CLAVES_CTX: tuple[str, ...] = (
    "capitulo_id",
    "capitulo_titulo",
    "titulo_ficha",
    "plantilla",
)


class Cursor:
    """Cursor vertical que coloca elementos y salta de página al desbordar.

    Mantiene la página abierta, la coordenada `y` (borde superior libre) y la
    lista acumulada de páginas (el Modelo_Paginas). El contexto (`ctx`) lleva
    `capitulo_id`, `capitulo_titulo`, `titulo_ficha` y `plantilla`, y se propaga
    a cada página nueva.
    """

    __slots__ = ("ctx", "y", "pagina", "paginas", "_folio")

    def __init__(self, ctx: dict[str, object] | None = None) -> None:
        self.ctx: dict[str, object] = {} if ctx is None else dict(ctx)
        self.ctx.setdefault("capitulo_id", "")
        self.ctx.setdefault("capitulo_titulo", "")
        self.ctx.setdefault("titulo_ficha", None)
        self.ctx.setdefault("plantilla", Plantilla.TEXTO)
        self._folio: int = 0
        self.y: float = AREA_Y + AREA_H
        self.pagina: PaginaRender | None = None
        self.paginas: list[PaginaRender] = []
        self._abrir_pagina()

    # -- contexto ---------------------------------------------------------- #

    def _valor_ctx(self, clave: str) -> object:
        return self.ctx.get(clave)

    def fijar_capitulo(self, capitulo_id: str, capitulo_titulo: str) -> None:
        """Actualiza el capítulo activo. Afecta a las páginas siguientes."""
        self.ctx["capitulo_id"] = capitulo_id
        self.ctx["capitulo_titulo"] = capitulo_titulo

    def fijar_ficha(self, titulo_ficha: str | None) -> None:
        """Fija (o limpia con `None`) el título de ficha que se repite por página."""
        self.ctx["titulo_ficha"] = titulo_ficha

    def fijar_plantilla(self, plantilla: Plantilla) -> None:
        """Fija la plantilla de las páginas que se abran a continuación."""
        self.ctx["plantilla"] = plantilla

    # -- gestión de páginas ------------------------------------------------ #

    def _abrir_pagina(self) -> None:
        self._folio += 1
        plantilla = self._valor_ctx("plantilla")
        if not isinstance(plantilla, Plantilla):
            plantilla = Plantilla.TEXTO
        pagina = PaginaRender(
            folio=self._folio,
            capitulo_id=str(self._valor_ctx("capitulo_id") or ""),
            capitulo_titulo=str(self._valor_ctx("capitulo_titulo") or ""),
            plantilla=plantilla,
            titulo_ficha=self._valor_ctx("titulo_ficha"),  # type: ignore[arg-type]
        )
        self.pagina = pagina
        self.paginas.append(pagina)
        self.y = AREA_Y + AREA_H

    def saltar_pagina(self) -> None:
        """Cierra la página actual y abre otra heredando el contexto completo.

        Propaga `capitulo_id`, `capitulo_titulo`, `titulo_ficha` y `plantilla`
        (Req 1.5 y 1.7 por construcción).
        """
        self._abrir_pagina()

    # -- colocación -------------------------------------------------------- #

    def _detalle(self, bloque: object) -> dict[str, object]:
        folio = self.pagina.folio if self.pagina is not None else self._folio
        detalle: dict[str, object] = {
            "folio": folio,
            "capitulo_id": self._valor_ctx("capitulo_id"),
        }
        titulo = self._valor_ctx("titulo_ficha")
        if titulo is not None:
            detalle["titulo_ficha"] = titulo
        if bloque is not None:
            detalle["bloque"] = bloque
        return detalle

    def reservar(self, h: float, *, bloque: object = None) -> float:
        """Reserva altura `h` y devuelve el borde superior (`y`) reservado.

        Si `h` no cabe en lo que queda de página, salta a una nueva. Un bloque
        más alto que el área imprimible completa es irreparable:
        `ErrorLayout('E_DESBORDE_TEXTO')` con folio y bloque.
        """
        if h > AREA_H:
            raise ErrorLayout(
                f"bloque de {h:.3f} pt no cabe en el area imprimible "
                f"({AREA_H:.3f} pt) de la pagina",
                codigo=E_DESBORDE_TEXTO,
                detalle=self._detalle(bloque),
            )
        if self.y - h < AREA_Y:
            self.saltar_pagina()
        top = self.y
        self.y -= h
        return top

    def colocar(self, elemento: ElementoRender, *, bloque: object = None) -> ElementoRender:
        """Mide, reserva y coloca `elemento` en la página actual.

        Rellena `elemento.h` con la altura medida, ancla `x` al borde izquierdo
        del área y sitúa `y` en la esquina inferior-izquierda del elemento.
        Devuelve el mismo elemento ya colocado.
        """
        if self.pagina is None:  # invariante: siempre hay página abierta
            self._abrir_pagina()

        altura = medir_elemento(elemento, AREA_W)
        top = self.reservar(altura, bloque=bloque if bloque is not None else elemento.tipo.value)

        elemento.h = altura
        elemento.x = AREA_X
        elemento.y = top - altura
        if not elemento.w or elemento.w <= 0.0:
            elemento.w = AREA_W

        # Tras `reservar` siempre hay página abierta (invariante del cursor).
        pagina = self.pagina
        if pagina is None:  # pragma: no cover - defensivo, no debería ocurrir
            self._abrir_pagina()
            pagina = self.pagina
        pagina.elementos.append(elemento)  # type: ignore[union-attr]
        return elemento

    def anotar(self, anotacion: Anotacion) -> None:
        """Registra una anotación `/Link` en la página actual."""
        if self.pagina is None:
            self._abrir_pagina()
        self.pagina.anotaciones.append(anotacion)  # type: ignore[union-attr]

    # -- punto de guardado y grupos indivisibles --------------------------- #

    def _guardar(self) -> tuple[PaginaRender | None, float, int, int]:
        n_elems = len(self.pagina.elementos) if self.pagina is not None else 0
        return (self.pagina, self.y, n_elems, self._folio)

    def _restaurar(self, marca: tuple[PaginaRender | None, float, int, int]) -> None:
        pagina, y, n_elems, folio = marca
        # Descarta cualquier página abierta después de la marca.
        if pagina is not None:
            indice = self.paginas.index(pagina)
            del self.paginas[indice + 1:]
            del pagina.elementos[n_elems:]
        self.pagina = pagina
        self.y = y
        self._folio = folio

    @contextlib.contextmanager
    def mantener_juntos(self, altura: float, *, bloque: object = None):
        """Context manager: coloca un grupo indivisible de `altura` sin partirlo.

        Punto de guardado y un solo reintento: si el grupo no cabe en lo que
        queda de la página actual, restaura el estado y salta a una página nueva
        *antes* de ceder el control, de modo que todo lo colocado dentro del
        bloque quede en la misma página. Si el grupo es más alto que el área
        imprimible completa, no hay reintento posible y se lanza
        `ErrorLayout('E_DESBORDE_TEXTO')` con folio y bloque.
        """
        if altura > AREA_H:
            raise ErrorLayout(
                f"grupo indivisible de {altura:.3f} pt no cabe en el area "
                f"imprimible ({AREA_H:.3f} pt)",
                codigo=E_DESBORDE_TEXTO,
                detalle=self._detalle(bloque),
            )

        marca = self._guardar()
        # Único reintento: si no cabe entero, restaura y salta una vez.
        if self.y - altura < AREA_Y:
            self._restaurar(marca)
            self.saltar_pagina()

        yield self

    # -- salida ------------------------------------------------------------ #

    def modelo_paginas(self) -> list[PaginaRender]:
        """Devuelve el Modelo_Paginas: la lista de `PaginaRender` acumulada.

        Es la única frontera hacia los motores (`build_pdf`, `build_html`).
        """
        return self.paginas
