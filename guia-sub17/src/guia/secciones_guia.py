"""Plan de secciones de la guia y registro de las Seccion_Reservada.

Modulo del Requisito 19: declara el **orden exacto** en que el Target_Web emite
sus secciones (criterio 19.1) y el punto de extension por el que otra spec puede
rellenar el cuerpo de una Seccion_Reservada sin tocar `build_site.py`.

Dos piezas y nada mas:

* `PLAN` es la tupla de anclas en el orden del criterio 19.1. `anclas_esperadas()`
  la expone para el indice (criterio 19.3) y para la navegacion en pagina.
* `RESERVADAS` declara las seis Seccion_Reservada que esta spec emite con su
  encabezado y su ancla, y con el cuerpo vacio (criterios 19.6 y 19.7). Otra spec
  llama a `registrar(ancla, render)` y su cuerpo aparece dentro de la misma
  seccion, sin que `build_site.py` cambie una linea.

Reglas del proyecto que este modulo respeta:

* Python 3.11+, solo libreria estandar.
* **Ningun `assert`**: todo invariante viaja como `raise ErrorAsset(...)` con el
  codigo `E_ASSET_INVALIDO`, porque `python -O` borra los `assert`.
* Emision determinista: el registro se recorre por el orden declarado de
  `RESERVADAS`, nunca por el orden de insercion de un `dict` ni por un `set`.

_Requirements: 19.1, 19.6, 19.7_
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from . import build_html
from . import diagramas_postura as dp
from .errores import E_ASSET_INVALIDO, ErrorAsset

__all__ = [
    "ANCLA_HERO",
    "ANCLA_INDICE",
    "ANCLA_LEYENDA",
    "ANCLA_RUTINA",
    "CLASE_AMPLIAR",
    "CLASE_BARRA",
    "CLASE_CERRAR",
    "CLASE_CON_JS",
    "CLASE_CUERPO_FIJO",
    "CLASE_CUERPO_VISOR",
    "CLASE_ICONO",
    "CLASE_LIENZO",
    "CLASE_TACTIL",
    "CLASE_TITULO_VISOR",
    "CLASE_VISOR",
    "EstadoCarga",
    "PLAN",
    "PREFIJO_EJERCICIOS",
    "PREFIJO_FUNDAMENTO",
    "PREFIJO_TITULO_MODAL",
    "RESERVADAS",
    "Reservada",
    "TEXTO_CERRAR",
    "TITULO_FUNDAMENTO",
    "TITULO_SECCION",
    "ancla_ejercicios",
    "ancla_fundamento",
    "anclas_esperadas",
    "anclas_reservadas",
    "enlaces_navegacion",
    "id_titulo_modal",
    "limpiar_registro",
    "registradas",
    "registrar",
    "render_anatomia",
    "render_creditos_seccion",
    "render_indice_secciones",
    "render_reservada",
    "render_secciones",
    "render_tecnica",
    "render_visor_ampliado",
    "render_zona_ampliacion",
    "reservada_de",
    "svg_cerrar",
    "titulo_de",
    "validar_plan",
]


# --------------------------------------------------------------------------- #
# Anclas del plan
# --------------------------------------------------------------------------- #

#: Ancla del hero, primera seccion del plan (criterio 19.1).
ANCLA_HERO: str = "hero"

#: Ancla del indice de la guia (criterio 19.3). No se llama `indice` a secas para
#: no chocar con el ancla `top` que el Target_Web ya usa para la portada.
ANCLA_INDICE: str = "indice-guia"

#: Ancla de la Seccion_Reservada de la leyenda de simbolos (criterio 19.6).
ANCLA_LEYENDA: str = "leyenda-simbolos"

#: Ancla de la Seccion_Reservada de la rutina semanal (criterio 19.6).
ANCLA_RUTINA: str = "rutina-semanal"

#: Prefijo del ancla de los diagramas de ejercicio de un Fundamento (19.6).
PREFIJO_EJERCICIOS: str = "ejercicios-"

#: Prefijo del ancla del bloque de un Fundamento dentro de la seccion de tecnica.
PREFIJO_FUNDAMENTO: str = "fundamento-"


def ancla_ejercicios(fundamento: str) -> str:
    """Ancla `ejercicios-<fundamento>` de la Seccion_Reservada de ese Fundamento."""
    return f"{PREFIJO_EJERCICIOS}{fundamento}"


def ancla_fundamento(fundamento: str) -> str:
    """Ancla `fundamento-<fundamento>` del bloque de ese Fundamento."""
    return f"{PREFIJO_FUNDAMENTO}{fundamento}"


#: Titulo legible de cada Fundamento del conjunto cerrado. En espanol de Mexico y
#: sin jerga interna: es texto que la jugadora lee.
TITULO_FUNDAMENTO: dict[str, str] = {
    "golpeo": "Golpeo",
    "pase": "Pase",
    "control-conduccion": "Control y conducción",
    "cabeceo": "Cabeceo",
}


# --------------------------------------------------------------------------- #
# Seccion_Reservada
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Reservada:
    """Una Seccion_Reservada: ancla, encabezado y nivel de ese encabezado.

    `nivel` vale 2 en las de primer nivel (`leyenda-simbolos` y `rutina-semanal`)
    y 3 en las que viven dentro de un bloque de Fundamento
    (`ejercicios-<fundamento>`), de modo que la jerarquia de encabezados del
    documento no se salte un nivel.
    """

    ancla: str
    titulo: str
    nivel: int


#: Las seis Seccion_Reservada de esta spec, congeladas y en orden declarado: las
#: dos de primer nivel primero y luego una por Fundamento, en el orden del
#: criterio 19.5. `render_reservada` emite el ancla y el encabezado exista o no el
#: cuerpo registrado (criterio 19.7).
RESERVADAS: tuple[Reservada, ...] = (
    Reservada(ancla=ANCLA_LEYENDA, titulo="Leyenda de símbolos", nivel=2),
    Reservada(ancla=ANCLA_RUTINA, titulo="Rutina semanal", nivel=2),
    *(
        Reservada(
            ancla=ancla_ejercicios(fundamento),
            titulo=f"Ejercicios de {TITULO_FUNDAMENTO[fundamento].lower()}",
            nivel=3,
        )
        for fundamento in dp.FUNDAMENTOS
    ),
)

#: Indice `ancla -> Reservada`, derivado de `RESERVADAS` para que no haya dos
#: fuentes capaces de desincronizarse.
_POR_ANCLA: dict[str, Reservada] = {r.ancla: r for r in RESERVADAS}


# --------------------------------------------------------------------------- #
# Plan de secciones (criterio 19.1)
# --------------------------------------------------------------------------- #

#: Orden exacto de las secciones del Target_Web (criterio 19.1): hero, indice,
#: `anatomia-base`, la leyenda de simbolos, la seccion de tecnica con los cuatro
#: bloques de Fundamento en el orden del criterio 19.5, la rutina semanal y el
#: Bloque_Creditos. `tecnica-en-imagenes` esta en el plan porque el criterio 3.1
#: la exige como seccion propia y la navegacion en pagina enlaza a su ancla
#: (criterio 3.7).
PLAN: tuple[str, ...] = (
    ANCLA_HERO,
    ANCLA_INDICE,
    dp.ANCLA_ANATOMIA,
    ANCLA_LEYENDA,
    dp.ANCLA_TECNICA,
    *(ancla_fundamento(f) for f in dp.FUNDAMENTOS),
    ANCLA_RUTINA,
    dp.ANCLA_CREDITOS,
)

#: Titulo legible de cada seccion del plan, para el indice y la navegacion.
TITULO_SECCION: dict[str, str] = {
    ANCLA_HERO: "Portada",
    ANCLA_INDICE: "Índice de la guía",
    dp.ANCLA_ANATOMIA: "Vocabulario del cuerpo",
    ANCLA_LEYENDA: "Leyenda de símbolos",
    dp.ANCLA_TECNICA: "Técnica en imágenes",
    **{ancla_fundamento(f): TITULO_FUNDAMENTO[f] for f in dp.FUNDAMENTOS},
    ANCLA_RUTINA: "Rutina semanal",
    dp.ANCLA_CREDITOS: "Créditos y licencias",
}


def anclas_esperadas() -> tuple[str, ...]:
    """Anclas del plan, en el orden del criterio 19.1.

    Es lo que alimenta el indice (una Zona_Tactil por seccion, criterio 19.3) y
    la comprobacion de orden de la Property 17.
    """
    return PLAN


def anclas_reservadas() -> tuple[str, ...]:
    """Anclas de las seis Seccion_Reservada, en el orden declarado."""
    return tuple(r.ancla for r in RESERVADAS)


def titulo_de(ancla: str) -> str:
    """Titulo legible de una seccion del plan."""
    titulo: str | None = TITULO_SECCION.get(ancla)
    if titulo is None:
        raise ErrorAsset(
            f"ancla fuera del plan de secciones: {ancla!r}",
            detalle={"ancla": ancla},
            codigo=E_ASSET_INVALIDO,
        )
    return titulo


def reservada_de(ancla: str) -> Reservada:
    """La Seccion_Reservada con ese ancla.

    Lanza `ErrorAsset(E_ASSET_INVALIDO)` nombrando el ancla cuando no pertenece a
    `RESERVADAS`, en vez de reventar mas tarde con un `KeyError` opaco.
    """
    reservada: Reservada | None = _POR_ANCLA.get(ancla)
    if reservada is None:
        raise ErrorAsset(
            f"ancla que no es de ninguna seccion reservada: {ancla!r}; "
            f"las reservadas son {anclas_reservadas()}",
            detalle={"ancla": ancla, "reservadas": anclas_reservadas()},
            codigo=E_ASSET_INVALIDO,
        )
    return reservada


# --------------------------------------------------------------------------- #
# Registro del cuerpo de una Seccion_Reservada (punto de extension)
# --------------------------------------------------------------------------- #

#: Cuerpos registrados, `ancla -> render`. Se recorre siempre por el orden de
#: `RESERVADAS`, nunca por el orden de insercion de este diccionario.
_REGISTRO: dict[str, Callable[[list[str]], None]] = {}


def registrar(ancla: str, render: Callable[[list[str]], None]) -> None:
    """Registra el cuerpo de una Seccion_Reservada.

    Solo acepta anclas de `RESERVADAS` y rechaza el registro repetido: dos specs
    que quieran rellenar la misma seccion es un error de composicion, no algo que
    se resuelva pisando en silencio el cuerpo anterior.
    """
    reservada_de(ancla)
    if not callable(render):
        raise ErrorAsset(
            f"el cuerpo registrado para {ancla!r} no es invocable: {render!r}",
            detalle={"ancla": ancla},
            codigo=E_ASSET_INVALIDO,
        )
    if ancla in _REGISTRO:
        raise ErrorAsset(
            f"la seccion reservada {ancla!r} ya tiene un cuerpo registrado",
            detalle={"ancla": ancla},
            codigo=E_ASSET_INVALIDO,
        )
    _REGISTRO[ancla] = render


def limpiar_registro() -> None:
    """Vacia el registro de cuerpos. Lo usan las pruebas entre iteraciones."""
    _REGISTRO.clear()


def registradas() -> tuple[str, ...]:
    """Anclas con cuerpo registrado, en el orden declarado de `RESERVADAS`."""
    return tuple(r.ancla for r in RESERVADAS if r.ancla in _REGISTRO)


def render_reservada(ancla: str, partes: list[str]) -> None:
    """Emite la `<section>` de una Seccion_Reservada con su ancla y su encabezado.

    El ancla y el encabezado se emiten **exista o no** el cuerpo registrado
    (criterio 19.7): con el registro vacio la seccion queda como un hueco con
    nombre, que es exactamente lo que otra spec vendra a rellenar.
    """
    reservada: Reservada = reservada_de(ancla)
    etiqueta: str = f"h{reservada.nivel}"
    partes.append(
        f'<section class="seccion-reservada" id="{build_html._esc(ancla)}" '
        f'data-reservada="1">'
    )
    partes.append(
        f"<{etiqueta}>{build_html._esc(reservada.titulo)}</{etiqueta}>"
    )
    cuerpo: Callable[[list[str]], None] | None = _REGISTRO.get(ancla)
    if cuerpo is not None:
        cuerpo(partes)
    partes.append("</section>")


# --------------------------------------------------------------------------- #
# Validador del plan
# --------------------------------------------------------------------------- #


def validar_plan() -> None:
    """Comprueba los invariantes del plan y del registro de reservadas.

    Todo con `raise ErrorAsset`, ningun `assert`:

    1. `PLAN` no repite ancla y empieza por el hero y el indice.
    2. Las seis Seccion_Reservada tienen ancla unica, titulo no vacio y nivel 2 o
       3, y las cuatro de Fundamento cubren el conjunto cerrado.
    3. `leyenda-simbolos` y `rutina-semanal` estan en `PLAN`, en las posiciones
       que el criterio 19.1 les asigna, y las de Fundamento **no** estan en
       `PLAN` porque viven dentro del bloque de su Fundamento (criterio 19.4).
    4. Todo ancla de `PLAN` tiene titulo legible.
    """
    if len(set(PLAN)) != len(PLAN):
        raise ErrorAsset(
            f"el plan de secciones repite alguna ancla: {PLAN}",
            detalle={"plan": PLAN},
            codigo=E_ASSET_INVALIDO,
        )
    if PLAN[:2] != (ANCLA_HERO, ANCLA_INDICE):
        raise ErrorAsset(
            "el plan de secciones debe empezar por el hero y el indice, no por "
            f"{PLAN[:2]}",
            detalle={"plan": PLAN},
            codigo=E_ASSET_INVALIDO,
        )
    if PLAN[-1] != dp.ANCLA_CREDITOS:
        raise ErrorAsset(
            f"el plan de secciones debe terminar en {dp.ANCLA_CREDITOS!r}, no "
            f"en {PLAN[-1]!r}",
            detalle={"plan": PLAN},
            codigo=E_ASSET_INVALIDO,
        )

    anclas: tuple[str, ...] = anclas_reservadas()
    if len(set(anclas)) != len(anclas):
        raise ErrorAsset(
            f"dos secciones reservadas comparten ancla: {anclas}",
            detalle={"reservadas": anclas},
            codigo=E_ASSET_INVALIDO,
        )
    esperadas: tuple[str, ...] = (
        ANCLA_LEYENDA,
        ANCLA_RUTINA,
        *(ancla_ejercicios(f) for f in dp.FUNDAMENTOS),
    )
    if anclas != esperadas:
        raise ErrorAsset(
            f"las secciones reservadas declaradas son {anclas} y deberian ser "
            f"{esperadas}",
            detalle={"declaradas": anclas, "esperadas": esperadas},
            codigo=E_ASSET_INVALIDO,
        )
    for reservada in RESERVADAS:
        if not reservada.titulo:
            raise ErrorAsset(
                f"la seccion reservada {reservada.ancla!r} no declara titulo",
                detalle={"ancla": reservada.ancla},
                codigo=E_ASSET_INVALIDO,
            )
        if reservada.nivel not in (2, 3):
            raise ErrorAsset(
                f"la seccion reservada {reservada.ancla!r} declara el nivel de "
                f"encabezado {reservada.nivel}, que no es 2 ni 3",
                detalle={"ancla": reservada.ancla, "nivel": reservada.nivel},
                codigo=E_ASSET_INVALIDO,
            )

    for ancla in (ANCLA_LEYENDA, ANCLA_RUTINA):
        if ancla not in PLAN:
            raise ErrorAsset(
                f"la seccion reservada {ancla!r} falta en el plan de secciones",
                detalle={"ancla": ancla, "plan": PLAN},
                codigo=E_ASSET_INVALIDO,
            )
    for fundamento in dp.FUNDAMENTOS:
        interna: str = ancla_ejercicios(fundamento)
        if interna in PLAN:
            raise ErrorAsset(
                f"{interna!r} vive dentro del bloque de su fundamento, no como "
                "seccion de primer nivel del plan",
                detalle={"ancla": interna, "plan": PLAN},
                codigo=E_ASSET_INVALIDO,
            )

    if PLAN.index(ANCLA_LEYENDA) != PLAN.index(dp.ANCLA_ANATOMIA) + 1:
        raise ErrorAsset(
            f"{ANCLA_LEYENDA!r} debe ir justo despues de "
            f"{dp.ANCLA_ANATOMIA!r} en el plan",
            detalle={"plan": PLAN},
            codigo=E_ASSET_INVALIDO,
        )
    if PLAN.index(ANCLA_RUTINA) != PLAN.index(dp.ANCLA_CREDITOS) - 1:
        raise ErrorAsset(
            f"{ANCLA_RUTINA!r} debe ir justo antes de "
            f"{dp.ANCLA_CREDITOS!r} en el plan",
            detalle={"plan": PLAN},
            codigo=E_ASSET_INVALIDO,
        )

    for ancla in PLAN:
        titulo_de(ancla)


# --------------------------------------------------------------------------- #
# Zona_Tactil de ampliacion y Visor_Ampliado (criterios 15.19, 28.16 y 28.17)
# --------------------------------------------------------------------------- #

#: Clase de toda Zona_Tactil de la guia. El CSS le da los 44 px de lado minimo.
CLASE_TACTIL: str = "zona-tactil"

#: Clase de la Zona_Tactil que abre el Visor_Ampliado de un diagrama.
CLASE_AMPLIAR: str = "diagrama-ampliar"

#: Clase del Visor_Ampliado, que es el **overlay modal** con ancla propia.
CLASE_VISOR: str = "visor-ampliado"

#: Clase de la barra superior fija del overlay: titulo a la izquierda y cierre a
#: la derecha.
CLASE_BARRA: str = "visor-barra"

#: Clase del unico encabezado del overlay.
CLASE_TITULO_VISOR: str = "visor-titulo"

#: Clase del cuerpo desplazable del overlay.
CLASE_CUERPO_VISOR: str = "visor-cuerpo"

#: Clase del contenedor con `aspect-ratio` que **contiene** la ilustracion.
CLASE_LIENZO: str = "visor-lienzo"

#: Clase del icono en linea de la Zona_Tactil de cierre.
CLASE_ICONO: str = "visor-icono"

#: Clase de la Zona_Tactil de cierre del Visor_Ampliado.
CLASE_CERRAR: str = "visor-cerrar"

#: Texto de la etiqueta accesible de la Zona_Tactil de cierre. El rotulo visible
#: es el icono en linea, asi que este texto viaja en `aria-label`.
TEXTO_CERRAR: str = "Cerrar"

#: Clase que el Script_Unico anade a `<html>` en cuanto arranca. Es la bisagra de
#: la mejora progresiva: sin JavaScript nunca aparece, y las reglas del overlay
#: que dependen de ella no se activan.
CLASE_CON_JS: str = "con-modal"

#: Clase que el Script_Unico pone en `<body>` mientras un overlay esta abierto.
#: La Hoja_Estilo le cuelga el `overflow:hidden` del bloqueo de desplazamiento.
CLASE_CUERPO_FIJO: str = "modal-abierto"

#: Prefijo del `id` del encabezado del overlay, destino de `aria-labelledby`.
PREFIJO_TITULO_MODAL: str = "modal-titulo-"


def id_titulo_modal(id_diagrama: str) -> str:
    """`id` del unico `<h2>` del overlay de `id_diagrama`.

    Lanza `ErrorAsset(E_ASSET_INVALIDO)` con el identificador vacio, porque un
    `aria-labelledby` que apunta a `modal-titulo-` a secas es un enlace roto de
    accesibilidad y no un detalle cosmetico.
    """
    if not id_diagrama:
        raise ErrorAsset(
            "id_titulo_modal exige el identificador del diagrama",
            detalle={"id": id_diagrama},
            codigo=E_ASSET_INVALIDO,
        )
    return f"{PREFIJO_TITULO_MODAL}{id_diagrama}"


def svg_cerrar() -> str:
    """La ✕ del cierre, como `<svg>` **en linea** y no como carácter suelto.

    Dos trazos con `currentColor`, `aria-hidden="true"` y `focusable="false"`: el
    icono no es contenido para quien usa lector de pantalla (la etiqueta la da el
    `aria-label` de la Zona_Tactil) ni una parada de tabulacion extra.
    """
    trazo: str = (
        'stroke="currentColor" stroke-width="2.5" stroke-linecap="round" '
        'fill="none"'
    )
    return (
        f'<svg class="{CLASE_ICONO}" viewBox="0 0 24 24" width="24" '
        'height="24" aria-hidden="true" focusable="false">'
        f'<path d="M7 7 L17 17" {trazo}></path>'
        f'<path d="M17 7 L7 17" {trazo}></path>'
        "</svg>"
    )

#: Clase de la seccion de tecnica y de la del vocabulario del cuerpo.
CLASE_SECCION: str = "seccion-guia"

#: Clase del bloque de un Fundamento dentro de la seccion de tecnica.
CLASE_FUNDAMENTO: str = "bloque-fundamento"

#: Clase de la lista de Zona_Tactil del indice de secciones.
CLASE_INDICE: str = "indice-secciones"


@dataclass(slots=True)
class EstadoCarga:
    """Lleva la cuenta de si el documento ya emitio algun `<img>`.

    Existe porque el criterio 4.1 habla del **primer `<img>` del documento**, y
    el orden del documento no es el del catalogo: `anatomia-base` va en su propia
    seccion y las otras siete se reparten entre los cuatro bloques de Fundamento.
    Con el subconjunto presente vacio nunca hay `<img>` y este estado no cambia.
    """

    hay_img: bool = field(default=False)

    def siguiente(
        self, d: dp.DiagramaPostura, presentes: frozenset[str]
    ) -> bool:
        """True si `d` va a emitir el **primer** `<img>` del documento."""
        if dp.modo_render(d, presentes) != dp.MODO_ARCHIVO:
            return False
        primero: bool = not self.hay_img
        self.hay_img = True
        return primero


def render_zona_ampliacion(d: dp.DiagramaPostura, partes: list[str]) -> None:
    """Zona_Tactil que abre el Visor_Ampliado de `d` (criterio 28.16).

    Es un enlace de ancla a `#<id>-ampliada`: un toque y cero JavaScript. El `<a>`
    ya es enfocable con teclado, asi que no lleva `tabindex`. Cuando el
    Script_Unico esta vivo, ese mismo `<a>` es el elemento que abre el overlay y
    el que recupera el foco al cerrarlo; cuando no lo esta, el ancla sigue
    llevando al Visor_Ampliado por `:target`.
    """
    from . import svg_postura

    _esc = build_html._esc
    destino: str = svg_postura.ancla_ampliacion(d.id)
    etiqueta: str = f"Ver en grande el dibujo de {d.titulo}"
    partes.append(
        f'<p class="{CLASE_AMPLIAR}-linea">'
        f'<a class="{CLASE_TACTIL} {CLASE_AMPLIAR}" '
        f'href="#{_esc(destino)}" aria-label="{_esc(etiqueta)}">'
        f"{_esc(svg_postura.TEXTO_AMPLIACION)}</a></p>"
    )


def render_visor_ampliado(d: dp.DiagramaPostura, partes: list[str]) -> None:
    """Visor_Ampliado de `d` como **overlay modal** `<section id="<id>-ampliada">`.

    Estructura, de fuera a dentro y sin nada de sobra:

    1. la `<section class="visor-ampliado">` con `role="dialog"`,
       `aria-modal="true"` y `aria-labelledby` apuntando al `id` de su
       encabezado, mas el atributo `hidden` de origen;
    2. la barra superior `.visor-barra`, con el **unico** `<h2>` del overlay
       (truncado a una linea por la Hoja_Estilo) y la Zona_Tactil de cierre con
       su ✕ en SVG en linea y su `aria-label`;
    3. el cuerpo desplazable `.visor-cuerpo`, y dentro el contenedor
       `.visor-lienzo`, que declara la relacion de aspecto del diagrama en el
       `style` en linea (`--relacion`) para que la ilustracion quede **contenida**
       y no pise el titulo ni desborde el recuadro.

    El `<h2>` es uno y solo uno: el titulo del diagrama ya vive en el `<h3>` del
    `<article>` del bloque, que es otro elemento y otro nivel. Antes de este
    rediseño el visor repetia ese titulo dentro del mismo flujo del documento, y
    con `:target` los dos se pintaban encimados.

    Mejora progresiva, decision registrada. El overlay se emite con `hidden`, y la
    Hoja_Estilo lo destapa de dos maneras que no se pisan:

    * **sin JavaScript**, la regla `.visor-ampliado:target{display:flex;}` gana al
      `[hidden]` porque va detras en la cascada, asi que el enlace de ancla
      `#<id>-ampliada` sigue abriendo un overlay legible y su Zona_Tactil de
      cierre es un `<a href="#diagrama-<id>">` que cambia el destino y lo vuelve a
      cerrar: no hay forma de quedarse atrapada dentro;
    * **con JavaScript**, el Script_Unico marca `<html>` con `CLASE_CON_JS` y la
      regla `.con-modal .visor-ampliado[hidden]{display:none;}` pasa a mandar, de
      modo que `abrirModal`/`cerrarModal` gobiernan la visibilidad con el atributo
      `hidden` y `:target` deja de decidir nada.

    `anatomia-base` es la unica entrada con Girable verdadero, asi que lleva su
    `svg_figura_girable` con las diez Vista_Figura en el DOM desde el primer
    fotograma (criterios 22.6 a 22.9). Las otras siete muestran **solo** su vista
    frontal `az-000`, sin contenedor `data-girable`, de modo que no admiten
    Arrastre_Rotacion (criterio 22.5).

    La Zona_Tactil de cierre vuelve al `<article>` del diagrama, que es el
    elemento que la lectora estaba mirando (criterio 28.17).
    """
    from . import svg_postura, vistas_figura

    _esc = build_html._esc
    ancla: str = svg_postura.ancla_ampliacion(d.id)
    pose = svg_postura.pose_de(d.id)
    id_titulo: str = id_titulo_modal(d.id)
    ancho, alto = dp.dimensiones(d, dp.MODO_SVG)

    partes.append(
        f'<section class="{CLASE_VISOR}" id="{_esc(ancla)}" '
        f'data-visor="{_esc(d.id)}" data-girable="{"1" if d.girable else "0"}" '
        f'role="dialog" aria-modal="true" '
        f'aria-labelledby="{_esc(id_titulo)}" hidden>'
    )
    partes.append(f'<div class="{CLASE_BARRA}">')
    partes.append(
        f'<h2 class="{CLASE_TITULO_VISOR}" id="{_esc(id_titulo)}">'
        f"{_esc(d.titulo)}</h2>"
    )
    partes.append(
        f'<a class="{CLASE_TACTIL} {CLASE_CERRAR}" '
        f'href="#{_esc(dp.id_bloque(d))}" role="button" '
        f'aria-label="{_esc(TEXTO_CERRAR)}">{svg_cerrar()}</a>'
    )
    partes.append("</div>")
    partes.append(f'<div class="{CLASE_CUERPO_VISOR}">')
    partes.append(
        f'<div class="{CLASE_LIENZO}" '
        f'style="{dp.VARIABLE_RELACION}:{ancho}/{alto}">'
    )
    if d.girable:
        partes.append(vistas_figura.svg_figura_girable(pose, d))
    else:
        partes.append(
            vistas_figura.svg_vista(pose, vistas_figura.CLAVE_ACTIVA, d)
        )
    partes.append("</div>")
    partes.append("</div>")
    partes.append("</section>")


def _render_diagrama_completo(
    d: dp.DiagramaPostura,
    partes: list[str],
    *,
    presentes: frozenset[str],
    carga: EstadoCarga,
) -> None:
    """Bloque de un Diagrama_Postura, su Zona_Tactil y su Visor_Ampliado."""
    dp.render_bloque(
        d, partes, presentes=presentes, primero=carga.siguiente(d, presentes)
    )
    render_zona_ampliacion(d, partes)
    render_visor_ampliado(d, partes)


# --------------------------------------------------------------------------- #
# Las secciones del plan
# --------------------------------------------------------------------------- #


def render_anatomia(
    partes: list[str],
    *,
    presentes: frozenset[str],
    carga: EstadoCarga | None = None,
    catalogo: tuple[dp.DiagramaPostura, ...] | None = None,
) -> None:
    """Seccion propia del vocabulario del cuerpo, antes de la tecnica (3.2).

    Lleva el ancla `anatomia-base` en la `<section>` y su bloque completo dentro,
    con la Zona_Tactil de ampliacion y el Visor_Ampliado girable.
    """
    estado: EstadoCarga = EstadoCarga() if carga is None else carga
    entradas: tuple[dp.DiagramaPostura, ...] = (
        dp.CATALOGO if catalogo is None else catalogo
    )
    base: dp.DiagramaPostura = next(
        d for d in entradas if d.id == dp.ANCLA_ANATOMIA
    )
    _esc = build_html._esc
    partes.append(
        f'<section class="{CLASE_SECCION}" id="{_esc(dp.ANCLA_ANATOMIA)}">'
    )
    partes.append(f"<h2>{_esc(titulo_de(dp.ANCLA_ANATOMIA))}</h2>")
    _render_diagrama_completo(base, partes, presentes=presentes, carga=estado)
    partes.append("</section>")


def render_tecnica(
    partes: list[str],
    *,
    presentes: frozenset[str],
    carga: EstadoCarga | None = None,
    catalogo: tuple[dp.DiagramaPostura, ...] | None = None,
) -> tuple[str, ...]:
    """Seccion de tecnica con los cuatro bloques de Fundamento (3.1, 3.3, 19.5).

    Emite **exactamente** los cuatro bloques del conjunto cerrado, en el orden
    golpeo, pase, control y conduccion y cabeceo. Un Fundamento ajeno no genera
    bloque: se devuelve para que el reporte del build lo enumere (criterio 3.9).

    Cada bloque contiene sus Diagrama_Postura en el orden del catalogo y termina
    con la Seccion_Reservada `ejercicios-<fundamento>` (criterio 19.4).
    """
    estado: EstadoCarga = EstadoCarga() if carga is None else carga
    _esc = build_html._esc
    partes.append(
        f'<section class="{CLASE_SECCION}" id="{_esc(dp.ANCLA_TECNICA)}">'
    )
    partes.append(f"<h2>{_esc(titulo_de(dp.ANCLA_TECNICA))}</h2>")
    for fundamento in dp.FUNDAMENTOS:
        ancla: str = ancla_fundamento(fundamento)
        partes.append(
            f'<section class="{CLASE_FUNDAMENTO}" id="{_esc(ancla)}" '
            f'data-fundamento="{_esc(fundamento)}">'
        )
        partes.append(f"<h2>{_esc(titulo_de(ancla))}</h2>")
        for diagrama in dp.por_fundamento(fundamento, catalogo=catalogo):
            _render_diagrama_completo(
                diagrama, partes, presentes=presentes, carga=estado
            )
        render_reservada(ancla_ejercicios(fundamento), partes)
        partes.append("</section>")
    partes.append("</section>")
    return dp.fundamentos_omitidos(catalogo)


def render_creditos_seccion(
    partes: list[str],
    *,
    presentes: frozenset[str],
    catalogo: tuple[dp.DiagramaPostura, ...] | None = None,
) -> None:
    """Bloque_Creditos al final del documento (criterios 18.1 a 18.6)."""
    partes.append(f'<section class="{CLASE_SECCION} seccion-creditos">')
    dp.render_creditos(partes, presentes=presentes, catalogo=catalogo)
    partes.append("</section>")


def render_secciones(
    partes: list[str],
    *,
    presentes: frozenset[str],
    catalogo: tuple[dp.DiagramaPostura, ...] | None = None,
) -> tuple[str, ...]:
    """Emite el tramo del plan que va del vocabulario a la rutina semanal.

    Orden del criterio 19.1: `anatomia-base`, `leyenda-simbolos`,
    `tecnica-en-imagenes` con sus cuatro bloques de Fundamento y
    `rutina-semanal`. El Bloque_Creditos se emite aparte, porque va al **final**
    del documento (criterio 18.1) y entre medias van las fichas.

    Devuelve los Fundamento ajenos al conjunto cerrado, para el reporte (3.9).
    """
    carga: EstadoCarga = EstadoCarga()
    render_anatomia(partes, presentes=presentes, carga=carga, catalogo=catalogo)
    render_reservada(ANCLA_LEYENDA, partes)
    omitidos: tuple[str, ...] = render_tecnica(
        partes, presentes=presentes, carga=carga, catalogo=catalogo
    )
    render_reservada(ANCLA_RUTINA, partes)
    return omitidos


# --------------------------------------------------------------------------- #
# Indice y navegacion en pagina
# --------------------------------------------------------------------------- #


def render_indice_secciones(partes: list[str]) -> None:
    """Una Zona_Tactil con enlace de ancla por seccion del plan (criterio 19.3)."""
    _esc = build_html._esc
    partes.append(f'<ul class="{CLASE_INDICE}">')
    for ancla in PLAN:
        partes.append(
            f'<li data-seccion="{_esc(ancla)}">'
            f'<a class="{CLASE_TACTIL}" href="#{_esc(ancla)}">'
            f"{_esc(titulo_de(ancla))}</a></li>"
        )
    partes.append("</ul>")


#: Anclas que la navegacion en pagina debe enlazar (criterios 3.7 y 18.7).
ANCLAS_NAVEGACION: tuple[str, ...] = (
    dp.ANCLA_ANATOMIA,
    dp.ANCLA_TECNICA,
    dp.ANCLA_CREDITOS,
)


def enlaces_navegacion() -> tuple[tuple[str, str], ...]:
    """Pares `(ancla, texto)` que la navegacion en pagina anade (3.7 y 18.7)."""
    return tuple((ancla, titulo_de(ancla)) for ancla in ANCLAS_NAVEGACION)
