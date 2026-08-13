"""Capitulo 30 - Juego colectivo (contenido de entrenamiento en prosa).

Explica las ideas de conjunto que ordenan al equipo: como atacar, como
defender, como cambiar de una fase a otra y como comunicarse. Es el marco que da
sentido a las fichas y a los roles por posicion.

Contenido de entrenamiento propio para Sub-17, en espanol de Mexico, sin citar
fuentes, autores, clubes ni jugadoras. Datos puros con render por plantillas
(`portadilla_capitulo` y `texto`). Texto codificable en WinAnsi.
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

CAPITULO_ID: str = "cap30_colectivo"
TITULO: str = "Juego colectivo"
PAGINAS_OBJETIVO: int = 12

_NUMERO: str = "30"
_BAJADA: str = (
    "Las ideas de conjunto que ordenan al equipo: atacar, defender y cambiar "
    "de fase con sentido."
)

_SECCIONES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Las cuatro fases del juego",
        (
            "El futbol tiene cuatro momentos que se repiten todo el partido: "
            "cuando tenemos el balon (ataque), cuando lo tiene la rival "
            "(defensa) y los dos instantes de cambio, cuando lo recuperamos y "
            "cuando lo perdemos (las transiciones). Entender en que fase estas "
            "te dice que hacer.",
            "El equipo que reconoce rapido el cambio de fase gana ventaja. "
            "Recuperar el balon y atacar antes de que la rival se ordene, o "
            "perderlo y reorganizarse de inmediato, decide muchos partidos.",
            "Cada jugadora debe saber su tarea en las cuatro fases, no solo "
            "cuando tiene el balon. El futbol se juega mas tiempo sin balon "
            "que con el, y ahi tambien se gana.",
        ),
    ),
    (
        "Atacar con orden",
        (
            "Atacar bien no es correr todas hacia el balon. Es ocupar el campo "
            "con amplitud (usar todo el ancho) y profundidad (amenazar la "
            "espalda de la defensa) para estirar a la rival y abrir huecos.",
            "El balon se mueve mas rapido que las piernas: circularlo de lado "
            "a lado hace bascular a la rival y aparece el espacio libre. "
            "Cuando el juego esta en un lado, la banda contraria se mantiene "
            "abierta para el cambio de orientacion.",
            "Ataca el espacio que la rival deja al desplazarse hacia el balon. "
            "Las combinaciones simples, como la pared, superan lineas sin "
            "necesidad de regatear, y el ultimo pase busca a la companera "
            "mejor colocada, no la jugada mas vistosa.",
            "Ocupa distintas alturas: si todas estan al mismo nivel, es facil "
            "defenderlas. Escalonar la posicion da lineas de pase y hace mas "
            "dificil marcar.",
        ),
    ),
    (
        "Defender como bloque",
        (
            "Defender es tarea de las once. Un buen bloque defensivo se mueve "
            "junto: bascula al lado del balon, sube y baja a la vez y mantiene "
            "distancias cortas entre lineas para que no quepan pases "
            "peligrosos entre ellas.",
            "La primera decision al defender es si presionar arriba para robar "
            "cerca del area rival o replegarse para cerrar espacios cerca de "
            "la nuestra. Las dos son validas; lo que no vale es que unas "
            "presionen y otras se queden, dejando al equipo partido.",
            "La jugadora mas cercana al balon presiona orientando (cierra un "
            "lado del campo) y las demas cierran las lineas de pase cercanas. "
            "Defender es quitar opciones, no solo perseguir el balon.",
            "La comunicacion sostiene la defensa: avisar de una rival que "
            "llega, ordenar la subida de la linea o pedir el achique evita la "
            "mayoria de los goles por desorden.",
        ),
    ),
    (
        "Las transiciones",
        (
            "Al recuperar el balon, levanta la cabeza: si hay opcion de "
            "atacar rapido, los dos primeros pases deben ser seguros y hacia "
            "adelante, y las companeras de arriba atacan el espacio de "
            "inmediato. Si el ataque rapido no esta, asegura la posesion.",
            "Al perder el balon, la reaccion decide entre conceder un "
            "contraataque o cortarlo. La mas cercana presiona de inmediato "
            "para frenar a la portadora mientras las demas repliegan "
            "ordenadas, cerrando primero el camino directo a la porteria.",
            "Recupera tu posicion corriendo por dentro, no por fuera, para "
            "tapar los pases peligrosos. Si hace falta, una falta tactica "
            "lejos del area frena el contraataque, pero solo como recurso.",
            "Las transiciones se entrenan: reconocer el cambio de fase en "
            "segundos y reaccionar todas a una es un habito que se construye "
            "con repeticion.",
        ),
    ),
    (
        "La presion: cuando y como",
        (
            "Presionar arriba sirve para robar cerca del gol, pero cansa y "
            "deja espacio a la espalda. Por eso se hace con una senal clara de "
            "arranque: un pase hacia atras de la rival, un mal control o un "
            "pase lento que da tiempo a llegar.",
            "Cuando arranca la presion, todas se mueven juntas: la primera "
            "aprieta a la portadora, las cercanas cierran las lineas de pase y "
            "el resto sube para achicar el espacio y dejar a la rival sin "
            "salida comoda.",
            "Si la rival supera la primera presion, el equipo repliega junto "
            "de inmediato. Presionar sin orden, cada una por su lado, regala "
            "espacios y desgasta sin robar.",
        ),
    ),
    (
        "Balon parado a favor y en contra",
        (
            "Los balones parados deciden muchos partidos. A favor, un corner o "
            "una falta ensayada, con movimientos claros y una buena entrega, "
            "multiplica las opciones de gol. Cada jugadora sabe su recorrido y "
            "su punto de ataque, y siempre queda cobertura para el rechace y "
            "el contraataque.",
            "En contra, la organizacion evita goles evitables: palos "
            "cubiertos, marcaje a las rematadoras mas peligrosas, zonas clave "
            "ocupadas y un despeje que salga alto, lejos y a las bandas.",
            "Ensayar el balon parado, atacando y defendiendo, es de las formas "
            "mas rentables de usar el tiempo de entrenamiento.",
        ),
    ),
    (
        "Comunicacion y liderazgo",
        (
            "Un equipo que se comunica juega mas ordenado y comete menos "
            "errores. Comunicar es dar informacion util a tiempo: avisar de "
            "una rival, pedir el balon, ordenar el achique. Se hace con "
            "palabras cortas y claras, antes de que llegue el balon.",
            "El liderazgo no es gritar ni mandar: es ayudar a que las "
            "companeras jueguen mejor. La que ve la jugada, como la portera o "
            "la central, guia a las que estan de espaldas.",
            "La comunicacion es de ida y vuelta: hay que hablar y tambien "
            "escuchar. Animar a la companera tras un error sostiene al equipo "
            "mas que cualquier reproche.",
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
