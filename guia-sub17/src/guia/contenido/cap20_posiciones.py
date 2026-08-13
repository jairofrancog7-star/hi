"""Capitulo 20 - Juego por posicion (contenido de entrenamiento en prosa).

Explica, posicion por posicion, que se le pide a cada jugadora del equipo
femenil Sub-17: sus tareas en defensa y en ataque, sus decisiones clave y los
errores mas comunes. Complementa las fichas de posicion del Catalogo_JSON con la
idea de conjunto, para que cada jugadora entienda su rol dentro del equipo.

Es contenido de entrenamiento redactado como material propio para Sub-17, en
espanol de Mexico y con lenguaje directo. No cita fuentes, autores, clubes ni
jugadoras concretas: solo describe el juego. Como el resto de capitulos, es
**datos puros con render por plantillas**: produce el Modelo_Paginas apoyandose
en `portadilla_capitulo` y `texto`. Todo el texto es codificable en WinAnsi.
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

CAPITULO_ID: str = "cap20_posiciones"
TITULO: str = "Juego por posicion"
PAGINAS_OBJETIVO: int = 18

_NUMERO: str = "20"
_BAJADA: str = (
    "Que hace cada jugadora dentro del equipo: sus tareas en defensa y en "
    "ataque, sus decisiones y sus errores mas comunes."
)

_SECCIONES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "La idea de conjunto",
        (
            "El futbol se juega en equipo, pero cada jugadora ocupa un puesto "
            "con tareas propias. Entender tu posicion es saber que se espera "
            "de ti cuando el equipo tiene el balon, cuando lo pierde y cuando "
            "hay que decidir rapido. Cada rol se apoya en los de al lado: "
            "nadie juega sola.",
            "Un equipo ordenado reparte el campo en lineas y carriles. Las "
            "defensoras cierran los espacios cerca de la porteria, las "
            "mediocampistas conectan la defensa con el ataque y las delanteras "
            "generan y terminan las jugadas. Cuando cada una cumple su tarea, "
            "el equipo se mueve como un solo bloque.",
            "Este capitulo describe posicion por posicion lo que se pide a "
            "cada jugadora. Leelo pensando en tu puesto, pero tambien en los de "
            "tus companeras: entender el juego de la de al lado te ayuda a "
            "anticipar, a cubrir y a ofrecer la ayuda justa en el momento "
            "justo.",
            "Recuerda que en la Sub-17 conviene probar varias posiciones. "
            "Jugar en distintos puestos te hace mas completa, te ayuda a "
            "entender el juego desde varios angulos y te abre mas caminos para "
            "seguir creciendo como futbolista.",
        ),
    ),
    (
        "La portera",
        (
            "La portera es la ultima linea de seguridad y la primera de la "
            "salida. Su tarea principal es evitar el gol con una buena "
            "colocacion, un blocaje seguro y decisiones claras sobre cuando "
            "salir y cuando esperar. Una portera bien colocada para muchos "
            "tiros antes de tener que lanzarse.",
            "Con el balon en los pies, la portera moderna inicia el juego. "
            "Distribuye en corto para construir, saca en medio para saltar la "
            "primera presion o juega largo cuando conviene. Elegir bien la "
            "opcion segun la presion rival es tan importante como atajar.",
            "En balon parado y en los centros, la portera manda: ordena a la "
            "defensa, ataca el balon con salto potente y despeja lejos y a las "
            "bandas, nunca al centro. Su voz organiza a las companeras que "
            "juegan de espaldas a la porteria.",
            "Errores comunes: quedarse clavada en la linea sin achicar, "
            "lanzarse antes de tiempo en las salidas y despejar al centro. Se "
            "corrigen con trabajo de postura base, de achique y de decision "
            "entre salir y quedarse.",
        ),
    ),
    (
        "Las centrales",
        (
            "Las centrales son las jefas de la defensa. Ganan los duelos "
            "importantes, organizan la linea y arrancan el juego con calma. "
            "Deben combinar firmeza en el choque con la cabeza fria para salir "
            "jugando bajo presion.",
            "En defensa, la central llega firme al duelo pero sin lanzarse: "
            "gana el balon o retrasa a la atacante hasta que llegue la ayuda. "
            "Da cobertura a la companera que sale a presionar, cerrando su "
            "espalda, y ordena cuando la linea sube y cuando baja.",
            "Con el balon, levanta la cabeza y elige: pase en corto a la "
            "lateral, pase a la mediocentro o cambio de orientacion al lado "
            "libre. Si la presionan, conduce unos metros para atraer a la "
            "rival y luego suelta el pase.",
            "Errores comunes: lanzarse al suelo en el duelo, perder la linea "
            "con las companeras y precipitar la salida. Se corrigen con "
            "trabajo de duelo controlado, de basculacion y de salida bajo "
            "presion.",
        ),
    ),
    (
        "Las laterales",
        (
            "Las laterales viven en la banda y tienen doble tarea: defender su "
            "carril con solvencia y sumarse al ataque con criterio. Recorren "
            "mucho campo, asi que la condicion fisica y la lectura del momento "
            "son claves.",
            "En defensa, la lateral orienta a la extrema rival hacia la banda "
            "y espera el apoyo de la central, sin dejarse superar de un pase al "
            "espacio. Mantiene una distancia que le permita achicar y a la vez "
            "reaccionar a la profundidad.",
            "En ataque, da amplitud subiendo por fuera cuando su extremo se "
            "mete hacia dentro, y elige bien el momento de subir: lo hace "
            "cuando el equipo tiene el balon controlado. Al centrar, busca la "
            "zona de remate con un envio tenso y raso o al segundo palo.",
            "Errores comunes: subir a destiempo y dejar el carril libre, "
            "quedar lejos de la extrema y centrar sin mirar. Se corrigen "
            "coordinando la subida con el extremo y trabajando la accion "
            "repetida de subir, centrar y replegar.",
        ),
    ),
    (
        "La mediocentro",
        (
            "La mediocentro, o pivote, es el corazon del equipo. Recibe de la "
            "defensa, orienta el ataque y protege a las centrales. Debe "
            "ofrecerse siempre como opcion de pase y recibir de perfil para "
            "ver todo el campo antes de decidir.",
            "Con el balon, da el primer pase seguro y, cuando puede, orienta "
            "el juego hacia el lado libre. Su lectura marca el ritmo: sabe "
            "cuando acelerar el juego y cuando calmarlo para que el equipo "
            "respire.",
            "En defensa, coloca su cuerpo delante de las centrales para tapar "
            "el pase interior de la rival y cuida el equilibrio: si una "
            "companera sube, ella se queda para tapar el contragolpe.",
            "Errores comunes: recibir de espaldas y perder el balon, no "
            "ofrecerse cuando la defensa la necesita y abandonar el equilibrio. "
            "Se corrigen con trabajo de recepcion de perfil y de coberturas.",
        ),
    ),
    (
        "Las interiores y la media punta",
        (
            "Las interiores conectan el mediocampo con el ataque. Reciben "
            "entre lineas, participan en la circulacion y, sobre todo, llegan "
            "al area desde segunda linea para rematar o dar el ultimo pase. Su "
            "capacidad de aparecer en el momento justo es dificil de defender.",
            "La media punta juega mas cerca del area y busca el espacio entre "
            "la defensa y el mediocampo rival. Al recibir ahi, de perfil, "
            "puede girar y encarar para filtrar un pase o tirar. Es una "
            "jugadora de ultimo pase y de gol.",
            "Ambas deben coordinar sus llegadas con la delantera para no pisar "
            "el mismo espacio, y ayudar en defensa a tapar el juego interior "
            "de la rival cuando el equipo no tiene el balon.",
            "Errores comunes: llegar tarde al area, pisar el espacio de la "
            "delantera y desentenderse de la defensa. Se corrigen trabajando "
            "las llegadas de segunda linea y el ultimo pase en jugadas "
            "completas.",
        ),
    ),
    (
        "Las extremas",
        (
            "Las extremas son las jugadoras del uno contra uno y el desborde. "
            "Reciben pegadas a la banda, encaran a la lateral rival y deciden "
            "entre desbordar por fuera para centrar o cortar hacia dentro para "
            "tirar. Su valentia abre el ataque por los costados.",
            "Para ser peligrosa, la extrema recibe de cara a la porteria, "
            "ataca a la defensora con decision y usa el cambio de ritmo para "
            "superarla. Al desbordar, levanta la cabeza para elegir la zona de "
            "centro; al cortar, prepara el balon para el tiro con su pierna "
            "fuerte.",
            "La extrema tambien defiende: cuando el equipo pierde el balon por "
            "su banda, vuelve a ayudar a su lateral para no dejarla en "
            "inferioridad.",
            "Errores comunes: recibir de espaldas sin poder encarar, abusar "
            "del regate sin sentido y no replegar. Se corrigen con duelos 1v1 "
            "en banda que terminan en centro o en tiro.",
        ),
    ),
    (
        "La delantera",
        (
            "La delantera es la ultima jugadora y la primera defensora del "
            "ataque. Vive de los movimientos: fija a la central, ataca el "
            "espacio, se ofrece al pie y aparece en el area para rematar. Su "
            "trabajo no se mide solo en goles, sino en cuanto espacio genera "
            "para las demas.",
            "En el area, ataca el primer palo o el punto de penal segun de "
            "donde venga el centro, y remata al primer toque sin controlar de "
            "mas. Fuera del area, aguanta el balon de espaldas para asociarse "
            "cuando el equipo necesita subir.",
            "Sin balon, la delantera es la primera en presionar la salida "
            "rival para orientar la presion del equipo, y persigue todos los "
            "rechaces dentro del area.",
            "Errores comunes: quedarse quieta esperando el balon, controlar de "
            "mas en el area y no presionar. Se corrigen con trabajo de "
            "movimientos de ataque al espacio y de remate de centro en "
            "oleadas.",
        ),
    ),
)


def _a_paginas_render(
    plantilla: Plantilla,
    paginas_plantilla: list[PaginaPlantilla],
    folio_inicial: int,
) -> list[PaginaRender]:
    """Envuelve `PaginaPlantilla` en `PaginaRender` con folios y capitulo."""
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
    """Modelo_Paginas del capitulo: portadilla mas una seccion de texto por rol."""
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
