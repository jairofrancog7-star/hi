"""Capitulo 60 - Planificacion de la temporada (contenido en prosa).

Explica como organizar el entrenamiento a lo largo del tiempo: la semana tipo de
martes a jueves con partido el sabado, como se reparte una sesion, como usar el
plan de rotacion, la version corta para cuando falta luz y la tabla de decision
por numero de jugadoras. Es el marco que ordena cuando se entrena cada cosa.

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

CAPITULO_ID: str = "cap60_periodizacion"
TITULO: str = "Planificacion de la temporada"
PAGINAS_OBJETIVO: int = 16

_NUMERO: str = "60"
_BAJADA: str = (
    "Como organizar el tiempo: la semana tipo, la sesion, la rotacion y como "
    "adaptarse a la luz y a las jugadoras que llegan."
)

_SECCIONES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Por que planificar",
        (
            "Entrenar sin plan es repetir lo mismo o improvisar cada dia. "
            "Planificar es decidir con cabeza cuando se trabaja cada cosa para "
            "que el equipo mejore de forma ordenada durante toda la "
            "temporada, sin quemarse ni aburrirse.",
            "Una buena planificacion equilibra los contenidos: tecnica, "
            "trabajo por posicion, fisico y prevencion, juego colectivo y "
            "preparacion mental. Ninguno se descuida y ninguno se repite tanto "
            "que canse.",
            "Tambien reparte el esfuerzo en el tiempo: dias mas exigentes y "
            "dias suaves, semanas de carga y semanas de respiro. Asi el cuerpo "
            "asimila el trabajo y llega fresco al partido del sabado.",
        ),
    ),
    (
        "La semana tipo",
        (
            "La semana de este equipo se entrena de martes a jueves y se juega "
            "el sabado. Cada dia tiene un foco distinto para no cargar siempre "
            "lo mismo y para que la semana toque todos los contenidos.",
            "El martes, tras el fin de semana, se retoma con tecnica y juego, a "
            "intensidad media. El miercoles suele ser el dia de mas carga, con "
            "el trabajo principal de la semana. El jueves baja la intensidad y "
            "afina detalles y estrategia pensando en el partido.",
            "El viernes se descansa o se hace trabajo muy suave, y el sabado "
            "se compite. Llegar descansada y con la semana bien trabajada es "
            "lo que permite competir al mejor nivel.",
            "El plan de rotacion que acompana a esta guia entrega una semana "
            "distinta cada vez, con sus sesiones de martes, miercoles y jueves "
            "y las indicaciones para el sabado, para que nunca se repita la "
            "misma combinacion de ejercicios.",
        ),
    ),
    (
        "Como se reparte una sesion",
        (
            "Cada sesion sigue una estructura clara para aprovechar el tiempo. "
            "Empieza con el calentamiento y la activacion, que preparan el "
            "cuerpo y previenen lesiones; nunca se saltan.",
            "Sigue el bloque principal, donde va el contenido central del dia, "
            "con la mayor energia y concentracion. Luego un trabajo especifico "
            "que complementa ese foco, como finalizacion, duelos o juego por "
            "posicion.",
            "Se cierra con juego libre y vuelta a la calma: jugar es la mejor "
            "forma de aplicar lo entrenado y de terminar con buen sabor, y la "
            "vuelta a la calma ayuda a recuperar.",
            "La sesion completa cabe en unos noventa minutos. Repartir el "
            "tiempo por bloques evita que un solo ejercicio se coma la sesion y "
            "asegura que se toque todo lo planeado.",
        ),
    ),
    (
        "La version corta",
        (
            "No siempre hay noventa minutos ni luz suficiente. Cuando oscurece "
            "antes de tiempo o el tiempo apremia, cada sesion tiene una "
            "version corta de treinta minutos o menos.",
            "La version corta conserva lo esencial: un calentamiento breve y el "
            "bloque principal del dia. Se recorta el juego libre y se ajusta el "
            "calentamiento, pero nunca se elimina la activacion que protege el "
            "cuerpo.",
            "Tener siempre lista la version corta evita la tentacion de "
            "entrenar sin calentar por las prisas, que es justo cuando "
            "aparecen las lesiones.",
        ),
    ),
    (
        "Cuantas jugadoras llegaron",
        (
            "En un equipo real no siempre llegan todas. La planificacion "
            "contempla eso con una tabla de decision: segun el numero de "
            "jugadoras presentes, del uno al once, indica que sesion hacer sin "
            "improvisar.",
            "Si llegan menos de las previstas, se resuelve con una version "
            "reducida centrada en el ejercicio que menos jugadoras necesita. "
            "Si llegan mas, se forman grupos adicionales que rotan.",
            "Asi, sin importar cuantas aparezcan, siempre hay una sesion util "
            "y ordenada que hacer. Entrenar con pocas no es perder el dia: es "
            "una oportunidad para trabajar mas fino y con mas toques por "
            "jugadora.",
        ),
    ),
    (
        "El espacio disponible",
        (
            "El espacio tambien manda. A veces la cancha esta completa y a "
            "veces solo hay una franja prestada, compartida con otros grupos. "
            "La planificacion prevé fichas que se pueden hacer en un espacio "
            "de diez por diez metros o menos.",
            "Antes de empezar conviene revisar el espacio real, ubicar a los "
            "otros grupos y elegir una franja segura. Muchas tareas de "
            "tecnica, pases y control se entrenan perfectamente en poco "
            "espacio.",
            "Adaptar el ejercicio al espacio, y no al reves, permite entrenar "
            "siempre con lo que hay, sin excusas y sin riesgos.",
        ),
    ),
    (
        "Seguir el progreso",
        (
            "Planificar tambien es medir. Muchas fichas proponen una metrica "
            "sencilla, como cuantos pases o tiros de diez salen bien, para ver "
            "si se mejora con las semanas.",
            "Anotar esos numeros de vez en cuando, sin obsesionarse, da una "
            "foto real del avance y motiva. El progreso en el futbol no es "
            "lineal: hay mesetas y saltos, y ver los numeros ayuda a mantener "
            "la paciencia.",
            "La tabla de seguimiento del plan permite marcar las sesiones "
            "completadas de cada semana. Cumplir la mayoria de las sesiones "
            "planeadas es, a la larga, lo que hace mejorar al equipo.",
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
