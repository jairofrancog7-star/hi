"""Capitulo 10 - Fundamentos tecnicos (MODO MUESTRA).

Este capitulo rinde las **15 Ficha_Ejercicio reales** que hoy existen en el
Catalogo_JSON (`contenido/ejercicios.json`), mas el bloque del **Diagrama_Botin**
con sus siete zonas de contacto y la accion de juego de cada una.

Regla vigente del proyecto (modo muestra): se usa **unicamente** el contenido
disponible en `contenido/ejercicios.json`. No se inventan fichas nuevas ni
contenido de entrenamiento. Por eso este capitulo NO alcanza el umbral de
">= 25 fichas de tecnica" que menciona el texto original de la tarea 9.2: ese
umbral exigiria redactar fichas nuevas y queda **pendiente de los HTML de
origen** desde los que se migraria el resto del catalogo. Mientras tanto, el
capitulo rinde las 15 fichas reales disponibles sin detener el pipeline.

Que hace el modulo, en orden:

* **Carga** las 15 Ficha_JSON reales con `schema_json.cargar_catalogo(...)` y las
  convierte a `FichaEjercicio` con `schema_json.ficha_json_a_ficha(...)`. Se
  conservan sus `id`, sus enlaces (`media` -> `video_url` / `video_titulo`) y el
  campo `cancha` (que el adaptador transforma en `DiagramaSpec`)
  **exactamente** como estan; este modulo no toca el esquema JSON ni los
  enlaces ni los QR.
* **Renderiza** el bloque del Diagrama_Botin a media pagina A4 (>= A4_H / 2),
  con sus 7 zonas y la accion de juego de cada zona. La geometria del botin ya
  esta implementada en `diagram_spec.botin_por_defecto()`: aqui solo se coloca
  como elemento de pagina (no es contenido inventado).
* **Renderiza** cada ficha real con la plantilla `ficha` de `plantillas.py`,
  devolviendo el Modelo_Paginas (`list[PaginaRender]`) con
  `capitulo_id="cap10_fundamentos"` y su `capitulo_titulo`.

La ruta a `ejercicios.json` se localiza de forma robusta (relativa al paquete):
el archivo vive en `guia-sub17/contenido/ejercicios.json`, **fuera** de `src`.
Si no se encuentra, se lanza `ErrorDependencia` (subclase de `ErrorBuild`) en
lugar de inventar datos.

Solo librería estándar; sin `assert` (todo invariante es `raise`); type hints y
`from __future__ import annotations`.

_Requirements: 9.5, 3.6, 3.7, 1.6, 8.1, 8.4, 8.9_
"""

from __future__ import annotations

import os
from typing import Any

from ..diagram_spec import botin_por_defecto
from ..errores import ErrorDependencia
from ..layout import (
    A4_H,
    AREA_H,
    AREA_W,
    AREA_X,
    AREA_Y,
    ElementoRender,
    PaginaRender,
    Plantilla,
    TextoDatos,
    TipoElemento,
    medir_elemento,
)
from ..plantillas import CtxPlantilla, DiagramaDatos
from ..plantillas import ficha as _plantilla_ficha
from ..schema_json import cargar_catalogo, ficha_json_a_ficha

__all__ = [
    "CAPITULO_ID",
    "TITULO",
    "PAGINAS_OBJETIVO",
    "TITULO_BOTIN",
    "ruta_catalogo",
    "fichas_json",
    "fichas",
    "paginas",
]

#: Identificador del capitulo (coincide con la clave de PRESUPUESTO_PAGINAS).
CAPITULO_ID: str = "cap10_fundamentos"

#: Titulo del capitulo, usado en el encabezado/pie de cada pagina (Req 1.5).
TITULO: str = "Fundamentos tecnicos"

#: Paginas objetivo del capitulo segun la tabla de escalado del diseno. En modo
#: muestra el conteo real depende de las 15 fichas disponibles, no de este
#: objetivo (que se alcanzara al migrar el resto del catalogo).
PAGINAS_OBJETIVO: int = 22

#: Titulo del bloque del Diagrama_Botin en la pagina.
TITULO_BOTIN: str = "El botin: con que parte del pie golpeas el balon"

#: Introduccion breve del bloque del botin (texto estructural, no una ficha).
_INTRO_BOTIN: str = (
    "Cada parte del pie sirve para algo distinto. Este diagrama muestra el "
    "botin visto desde arriba y de perfil, con las siete zonas de contacto y "
    "para que se usa cada una. Fijate en la zona antes de golpear."
)

#: Encabezado de la lista de acciones de juego por zona (Req 3.7).
_ENCABEZADO_ZONAS: str = "Con que zona y para que sirve:"

#: Etiqueta legible de cada zona de la geometria del botin. Solo es rotulacion
#: de las zonas ya definidas en `diagram_spec`; no inventa contenido.
_ETIQUETA_ZONA: dict[str, str] = {
    "pase": "Interior (pase)",
    "efecto": "Exterior (efecto)",
    "tres_dedos": "Tres dedos",
    "punta": "Punta",
    "canonazo": "Empeine (cañonazo)",
    "planta": "Planta",
    "tacon": "Tacón",
}


# --------------------------------------------------------------------------- #
# Carga del catalogo real (15 fichas), con cache perezosa a nivel de modulo
# --------------------------------------------------------------------------- #

_JSON_CACHE: list[dict[str, Any]] | None = None
_FICHAS_CACHE: tuple[Any, ...] | None = None


def ruta_catalogo() -> str:
    """Ruta absoluta a `contenido/ejercicios.json`, localizada de forma robusta.

    El archivo vive en `guia-sub17/contenido/ejercicios.json`, es decir fuera de
    `src/`. Se prueban varios candidatos subiendo desde el paquete y se devuelve
    el primero que exista. Si ninguno existe, se lanza `ErrorDependencia` con la
    lista de rutas probadas, en vez de inventar datos.
    """
    aqui = os.path.dirname(os.path.abspath(__file__))
    candidatos: list[str] = []
    raiz = aqui
    for _ in range(5):
        raiz = os.path.dirname(raiz)
        candidatos.append(os.path.join(raiz, "contenido", "ejercicios.json"))
    for candidato in candidatos:
        if os.path.isfile(candidato):
            return candidato
    raise ErrorDependencia(
        "no se encontro contenido/ejercicios.json: el capitulo de fundamentos "
        "necesita el Catalogo_JSON real y no inventa fichas",
        detalle={"componente": "contenido/ejercicios.json", "probadas": candidatos},
    )


def fichas_json() -> list[dict[str, Any]]:
    """Devuelve las 15 Ficha_JSON reales, ya cargadas y validadas.

    Usa la cache perezosa de modulo para no releer el archivo en cada llamada
    (concatenar y desvios_presupuesto pueden invocar `paginas()` varias veces).
    """
    global _JSON_CACHE
    if _JSON_CACHE is None:
        _JSON_CACHE = cargar_catalogo(ruta_catalogo())
    return _JSON_CACHE


def fichas() -> tuple[Any, ...]:
    """Convierte las 15 Ficha_JSON reales en `FichaEjercicio` (modelo interno).

    Conserva sus `id`, sus enlaces (`video_url` / `video_titulo`) y su diagrama
    de cancha exactamente como los produce el adaptador, sin tocar el JSON.
    """
    global _FICHAS_CACHE
    if _FICHAS_CACHE is None:
        crudas = fichas_json()
        _FICHAS_CACHE = tuple(
            ficha_json_a_ficha(ficha, indice=indice)
            for indice, ficha in enumerate(crudas)
        )
    return _FICHAS_CACHE


# --------------------------------------------------------------------------- #
# Bloque del Diagrama_Botin (>= media pagina A4, con sus 7 zonas)
# --------------------------------------------------------------------------- #


def _pagina_botin(folio: int) -> PaginaRender:
    """Construye la pagina del Diagrama_Botin a media pagina A4 (Req 3.6, 3.7).

    Coloca, de arriba hacia abajo: titulo, introduccion, el diagrama del botin
    ocupando al menos media pagina A4 y la lista de las 7 zonas con su accion de
    juego. Toda altura de texto se mide con `afm.py` via `medir_elemento`.
    """
    elementos: list[ElementoRender] = []
    top = AREA_Y + AREA_H

    def _poner_texto(texto: str, fuente: str, tam: float, gap: float) -> None:
        nonlocal top
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
        elemento.y = top - altura
        elementos.append(elemento)
        top -= altura + gap

    _poner_texto(TITULO_BOTIN, "Helvetica-Bold", 16.0, 8.0)
    _poner_texto(_INTRO_BOTIN, "Helvetica", 10.0, 8.0)

    # Diagrama del botin: geometria ya implementada, colocada a media pagina A4.
    spec = botin_por_defecto(TITULO_BOTIN)
    alto_diagrama = A4_H / 2.0  # >= media pagina A4 (Req 3.6)
    diagrama = ElementoRender(
        tipo=TipoElemento.DIAGRAMA,
        x=AREA_X,
        y=top - alto_diagrama,
        w=AREA_W,
        h=alto_diagrama,
        datos=DiagramaDatos(spec=spec, titulo=TITULO_BOTIN),
    )
    elementos.append(diagrama)
    top -= alto_diagrama + 8.0

    # Accion de juego de cada una de las 7 zonas (Req 3.7).
    _poner_texto(_ENCABEZADO_ZONAS, "Helvetica-Bold", 11.0, 4.0)
    for zona in spec.zonas:
        etiqueta = _ETIQUETA_ZONA.get(zona.nombre, zona.nombre)
        _poner_texto(f"- {etiqueta}: {zona.accion}", "Helvetica", 10.0, 3.0)

    return PaginaRender(
        folio=folio,
        capitulo_id=CAPITULO_ID,
        capitulo_titulo=TITULO,
        plantilla=Plantilla.FICHA,
        titulo_ficha=TITULO_BOTIN,
        elementos=elementos,
    )


# --------------------------------------------------------------------------- #
# Construccion del Modelo_Paginas del capitulo
# --------------------------------------------------------------------------- #


def paginas(
    *, folio_inicial: int = 1, ctx: CtxPlantilla | None = None
) -> list[PaginaRender]:
    """Produce el Modelo_Paginas del capitulo de fundamentos (modo muestra).

    Emite, con folios consecutivos desde `folio_inicial`: primero el bloque del
    Diagrama_Botin y luego las 15 fichas reales, cada una renderizada con la
    plantilla `ficha`. Cada pagina propaga el capitulo al encabezado/pie
    (Req 1.5) y el titulo de la ficha (Req 1.7). `ctx` comparte la geometria del
    area imprimible con el resto del pipeline; si es `None` se usa la geometria
    por defecto de las plantillas.
    """
    render: list[PaginaRender] = []
    folio = folio_inicial

    render.append(_pagina_botin(folio))
    folio += 1

    # El modelo interno solo guarda el primer enlace en `video_url`, y una ficha
    # puede tener varios. Se pasa el `media` crudo del catalogo para que la
    # plantilla rinda un QR clicable por cada Media_Item (Req 9.6), igual que el
    # sitio y el PDF de fichas.
    media_por_id = {f["id"]: f.get("media") or () for f in fichas_json()}

    for ficha_obj in fichas():
        titulo_ficha = getattr(ficha_obj, "titulo", None)
        media = media_por_id.get(getattr(ficha_obj, "id", "") or "", ())
        for pagina in _plantilla_ficha(ficha_obj, ctx, media=media):
            render.append(
                PaginaRender(
                    folio=folio,
                    capitulo_id=CAPITULO_ID,
                    capitulo_titulo=TITULO,
                    plantilla=Plantilla.FICHA,
                    titulo_ficha=titulo_ficha,
                    elementos=pagina.elementos,
                    anotaciones=pagina.anotaciones,
                )
            )
            folio += 1

    return render
