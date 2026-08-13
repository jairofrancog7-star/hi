"""Capitulo 50 - Preparacion mental (contenido de entrenamiento en prosa).

Explica como entrenar la cabeza: concentracion, manejo de nervios y de errores,
confianza, motivacion y espiritu de equipo. Herramientas sencillas y practicas
para jugadoras adolescentes.

Contenido propio para Sub-17, en espanol de Mexico, sin citar fuentes ni
personas. Datos puros con render por plantillas. Texto codificable en WinAnsi.
"""

from __future__ import annotations

from ..layout import PaginaRender, Plantilla
from ..plantillas import (
    CtxPlantilla,
    DatosPortadilla,
    DatosTexto,
    PaginaPlantilla,
    portadilla_capitulo,
    texto,
)

__all__ = ["CAPITULO_ID", "TITULO", "PAGINAS_OBJETIVO", "paginas"]

CAPITULO_ID: str = "cap50_mental"
TITULO: str = "Preparacion mental"
PAGINAS_OBJETIVO: int = 14

_NUMERO: str = "50"
_BAJADA: str = (
    "Entrenar la cabeza: concentracion, nervios, errores, confianza y equipo."
)

_SECCIONES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "La cabeza tambien se entrena",
        (
            "La parte mental decide muchos partidos. Dos equipos parejos en "
            "tecnica se separan por quien se concentra mejor, quien aguanta la "
            "presion y quien se levanta antes tras un error. Y todo eso se "
            "entrena, igual que un pase o un tiro.",
            "No hace falta ser psicologa para trabajarlo. Con herramientas "
            "sencillas y constancia, cualquier jugadora puede aprender a "
            "manejar sus nervios, a enfocarse y a confiar mas en si misma.",
            "La preparacion mental no es pensar solo en positivo ni ignorar "
            "los problemas. Es aprender a gestionar lo que sientes para que "
            "juegue a tu favor, no en tu contra.",
        ),
    ),
    (
        "Concentracion y foco",
        (
            "Muchos goles se conceden por despistes en los primeros o ultimos "
            "minutos. Mantener el foco es volver una y otra vez a lo que pasa "
            "ahora en el juego, en lugar de perderse en lo que ya paso o en "
            "lo que puede pasar.",
            "Una herramienta util es una palabra clave, corta y personal, que "
            "te devuelva al presente cuando te distraes, por ejemplo aqui y "
            "ahora. La repites en tu cabeza y vuelves a la jugada.",
            "Antes del partido, una rutina breve ayuda a llegar enchufada: "
            "respiracion lenta, activacion del cuerpo y visualizar dos o tres "
            "acciones que quieres hacer bien. Repetida siempre igual, se "
            "vuelve automatica.",
        ),
    ),
    (
        "Manejar los nervios",
        (
            "Los nervios antes de competir son normales, incluso utiles: te "
            "activan. El problema es cuando te bloquean. Aprender a bajarlos a "
            "un punto que te ayude es parte del oficio.",
            "La respiracion es la herramienta mas rapida: inhalar en cuatro "
            "tiempos y exhalar en seis, varias veces, calma el cuerpo en "
            "segundos. Se puede usar antes del partido y en cualquier pausa.",
            "Enfocarte en lo que controlas (tu esfuerzo, tu actitud, la "
            "siguiente jugada) y no en lo que no controlas (el resultado, el "
            "arbitraje, la rival) baja mucho la presion que uno mismo se "
            "pone.",
        ),
    ),
    (
        "Los errores y la resiliencia",
        (
            "Errar es parte del juego; hasta las mejores fallan pases y "
            "ocasiones. Lo que distingue a una gran jugadora es como reacciona: "
            "suelta el error rapido, vuelve al presente y sigue compitiendo.",
            "Un truco util es un gesto fisico de reinicio, como sacudir las "
            "manos, seguido de una respiracion y de tu palabra clave. Cierra "
            "el error y abre la siguiente accion.",
            "Cambiar el dialogo interno ayuda: pasar de me sale todo mal a la "
            "proxima la meto. Hablarte como le hablarias a una companera que "
            "quieres, con exigencia pero sin castigo, sostiene la confianza.",
            "Despues del partido si conviene analizar el error con calma para "
            "aprender. Durante el juego, no: ahi solo toca soltarlo y seguir.",
        ),
    ),
    (
        "Confianza y motivacion",
        (
            "La confianza se construye con trabajo. Cada entrenamiento bien "
            "hecho, cada gesto que mejora, es un ladrillo. Recordar tus "
            "avances, y no solo tus fallos, alimenta la seguridad para "
            "atreverte en el partido.",
            "Ponte objetivos que dependan de ti y que puedas controlar, como "
            "mejorar el pase con la pierna mala o ganar mas duelos, en vez de "
            "objetivos que dependen de otros. Cumplirlos sube la motivacion de "
            "forma real.",
            "La motivacion tambien tiene dias bajos. En esos dias, la rutina y "
            "el compromiso con el equipo tiran de ti. No siempre se entrena "
            "con ganas, pero casi siempre se puede entrenar con actitud.",
        ),
    ),
    (
        "Equipo y comunicacion",
        (
            "Un buen ambiente de equipo hace mejores a todas. Animar a la "
            "companera que falla, celebrar los aciertos de las demas y "
            "sostener en los momentos duros crea un grupo fuerte que compite "
            "mejor.",
            "La comunicacion en el campo es tambien mental: pedir el balon con "
            "voz clara, avisar a tiempo y hablarse con respeto ordena al "
            "equipo y baja la ansiedad de todas.",
            "El liderazgo esta al alcance de cualquiera, no solo de la "
            "capitana. Liderar es ayudar a que las demas jueguen mejor, con el "
            "ejemplo, la palabra justa y la actitud en los dias dificiles.",
        ),
    ),
)


def _a_paginas_render(
    plantilla: Plantilla,
    paginas_plantilla: list[PaginaPlantilla],
    folio_inicial: int,
) -> list[PaginaRender]:
    render: list[PaginaRender] = []
    folio = folio_inicial
    for pagina in paginas_plantilla:
        render.append(
            PaginaRender(
                folio=folio,
                capitulo_id=CAPITULO_ID,
                capitulo_titulo=TITULO,
                plantilla=plantilla,
                elementos=pagina.elementos,
                anotaciones=pagina.anotaciones,
            )
        )
        folio += 1
    return render


def paginas(
    *, folio_inicial: int = 1, ctx: CtxPlantilla | None = None
) -> list[PaginaRender]:
    bloques: list[tuple[Plantilla, list[PaginaPlantilla]]] = [
        (
            Plantilla.PORTADILLA_CAPITULO,
            portadilla_capitulo(
                DatosPortadilla(numero=_NUMERO, titulo=TITULO, bajada=_BAJADA),
                ctx,
            ),
        )
    ]
    for titulo_seccion, parrafos in _SECCIONES:
        bloques.append(
            (
                Plantilla.TEXTO,
                texto(DatosTexto(parrafos=parrafos, titulo=titulo_seccion), ctx),
            )
        )

    render: list[PaginaRender] = []
    folio = folio_inicial
    for plantilla, paginas_plantilla in bloques:
        paginas_cap = _a_paginas_render(plantilla, paginas_plantilla, folio)
        render.extend(paginas_cap)
        folio += len(paginas_cap)
    return render
