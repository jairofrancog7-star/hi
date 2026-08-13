"""Capitulo 40 - Preparacion fisica y prevencion (contenido en prosa).

Explica, en lenguaje sencillo y para adolescentes, como cuidar el cuerpo:
calentamiento, fuerza y prevencion de lesiones (con foco en la rodilla), carga y
descanso, hidratacion y alimentacion basica, y senales de alarma. Es material
educativo general; no es consejo medico y no sustituye la valoracion de un
profesional de la salud.

Contenido de entrenamiento propio para Sub-17, en espanol de Mexico, sin citar
fuentes, autores ni personas. Datos puros con render por plantillas. Texto
codificable en WinAnsi.
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

__all__ = ["CAPITULO_ID", "TITULO", "PAGINAS_OBJETIVO", "MARCADOR_DESCARGO", "paginas"]

CAPITULO_ID: str = "cap40_prevencion"
TITULO: str = "Preparacion fisica y prevencion"
PAGINAS_OBJETIVO: int = 20

#: Marcador para que las pruebas confirmen el recordatorio informativo.
MARCADOR_DESCARGO: str = "No sustituye"

_NUMERO: str = "40"
_BAJADA: str = (
    "Como cuidar el cuerpo: calentar, fortalecer, prevenir lesiones, "
    "descansar, hidratarse y alimentarse bien."
)

_SECCIONES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Por que cuidar el cuerpo",
        (
            "Entrenar la tecnica y la tactica sirve de poco si el cuerpo no "
            "aguanta o se lesiona. La preparacion fisica y la prevencion son "
            "la base sobre la que se construye todo lo demas: te permiten "
            "entrenar mas y mejor, y jugar sin miedo.",
            "En el futbol femenil hay una lesion que merece atencion especial: "
            "la del ligamento cruzado anterior de la rodilla, mas frecuente "
            "que en varones. La buena noticia es que un trabajo constante de "
            "prevencion reduce mucho ese riesgo.",
            "Este capitulo es informativo y educativo. No sustituye la "
            "valoracion de un profesional de la salud. Ante cualquier molestia, "
            "dolor articular que no cede, hinchazon o inestabilidad, suspende "
            "el impacto y acude a valoracion medica.",
        ),
    ),
    (
        "El calentamiento",
        (
            "Empezar a entrenar con el cuerpo frio es pedir una lesion. El "
            "calentamiento sube la temperatura de los musculos, despierta las "
            "articulaciones y prepara la cabeza para entrenar. Nunca se salta.",
            "Un buen calentamiento tiene tres partes: primero movimiento "
            "suave y movilidad de tobillo, rodilla y cadera; luego activacion "
            "de los musculos que protegen las articulaciones; y por ultimo "
            "unas aceleraciones cortas y progresivas antes del balon.",
            "La movilidad recorre cada articulacion por todo su rango de "
            "movimiento con control. La activacion despierta glutero, "
            "isquiotibiales y core, que son los que estabilizan la rodilla y "
            "la cadera en los gestos exigentes del juego.",
            "El calentamiento tambien se enfoca: si la sesion va de tiros, "
            "termina con golpeos suaves; si va de duelos, con acciones de "
            "cambio de direccion a baja intensidad. Asi el cuerpo llega listo "
            "para lo que viene.",
        ),
    ),
    (
        "Fuerza y estabilidad",
        (
            "La fuerza no busca musculos grandes, busca un cuerpo capaz de "
            "aguantar empujones, frenar, girar y golpear con potencia sin "
            "lesionarse. En la Sub-17 se trabaja sobre todo con el peso del "
            "propio cuerpo y con buena tecnica.",
            "El core, la zona media, es el centro desde el que se transmite la "
            "fuerza. Planchas frontales y laterales y el puente de glutero, "
            "hechos con la postura correcta, construyen un centro fuerte que "
            "protege la espalda y mejora el golpeo.",
            "Los isquiotibiales y el glutero protegen la rodilla. Ejercicios "
            "como el isquiotibial nordico, bajando lento y con control, y las "
            "sentadillas cuidando la alineacion, son de los mas utiles para "
            "prevenir.",
            "El equilibrio a una pierna, primero quieta y luego con un pase de "
            "balon, entrena la estabilidad que necesitas al apoyar tras un "
            "salto o al frenar. Trabaja siempre los dos lados por igual.",
        ),
    ),
    (
        "Prevenir la lesion de rodilla",
        (
            "El momento de mayor riesgo para la rodilla es el aterrizaje tras "
            "un salto y el frenado brusco. La clave para protegerla es "
            "aprender a caer y a frenar con la rodilla alineada sobre la punta "
            "del pie, nunca metida hacia adentro.",
            "Al caer, amortigua flexionando tobillo, rodilla y cadera, como un "
            "resorte. Empieza con saltos suaves cayendo con las dos piernas y "
            "solo pasa a una pierna cuando la caida a dos sea solida.",
            "Un programa de prevencion hecho dos o tres veces por semana, como "
            "calentamiento, combina carrera, fuerza, equilibrio y saltos "
            "controlados. Su valor esta en la constancia: se nota con las "
            "semanas, no en un dia.",
            "Pocas repeticiones bien hechas valen mas que muchas con mala "
            "tecnica. Si aparece fatiga que rompe el gesto o dolor, se para. "
            "La prevencion mal hecha no previene.",
        ),
    ),
    (
        "Velocidad, agilidad y resistencia",
        (
            "La velocidad en el futbol casi siempre es con balon y en "
            "distancias cortas. Se entrena en fresco, nunca fatigada, con "
            "salidas explosivas y buena tecnica de carrera: rodillas al "
            "frente, brazos activos y pisada hacia adelante.",
            "La agilidad es cambiar de direccion y de ritmo con control. El "
            "trabajo de coordinacion de pies, con escalera o conos, educa "
            "apoyos rapidos y precisos que mejoran el arranque, el frenado y "
            "el giro.",
            "La resistencia en estas edades se gana sobre todo jugando y con "
            "trabajos que combinan esfuerzo y pausa, parecidos al ritmo real "
            "del partido. No hace falta correr kilometros aburridos: el balon "
            "es un gran aliado tambien aqui.",
        ),
    ),
    (
        "Carga, descanso y sueno",
        (
            "El cuerpo mejora cuando descansa, no mientras se esfuerza. Por "
            "eso alternar dias de mayor carga con dias suaves y respetar el "
            "descanso es parte del entrenamiento, no lo contrario.",
            "El sueno es el mejor recuperador que existe y es gratis. Dormir "
            "suficiente y con horarios regulares mejora la recuperacion, la "
            "concentracion y hasta el aprendizaje de gestos nuevos.",
            "Escuchar al cuerpo evita lesiones por sobrecarga. Un cansancio "
            "que no se va, molestias que se repiten o bajon de animo son "
            "senales de que hace falta bajar la carga y recuperar.",
        ),
    ),
    (
        "Hidratacion y alimentacion",
        (
            "El agua es clave para rendir. Conviene llegar hidratada, beber "
            "durante el entrenamiento en las pausas y reponer despues. Si "
            "hace mucho calor, la hidratacion importa todavia mas.",
            "La alimentacion de una futbolista no es complicada: comida real y "
            "variada. Hidratos para la energia (cereales, tuberculos, frutas), "
            "proteina para recuperar (huevo, lacteos, carnes, leguminosas) y "
            "verduras y frutas para la salud general.",
            "Antes de entrenar, una comida ligera y con tiempo para digerir "
            "sienta mejor que llegar llena o en ayunas. Despues, reponer con "
            "algo de hidratos y proteina ayuda a recuperar para la siguiente "
            "sesion.",
            "Esto son ideas generales, no una dieta. Cada cuerpo es distinto; "
            "ante dudas de nutricion o salud, lo mejor es consultar a un "
            "profesional.",
        ),
    ),
    (
        "Senales de alarma",
        (
            "Hay molestias normales del esfuerzo y otras que son aviso de "
            "parar. Un dolor agudo, un chasquido con hinchazon, una rodilla "
            "que se va o un tobillo que no aguanta el peso piden detener el "
            "impacto y buscar valoracion.",
            "Marearse, sentir el corazon muy acelerado sin causa o un cansancio "
            "raro tambien son motivos para parar, hidratarse y avisar. Competir "
            "con dolor o mareo no es ser valiente, es arriesgar la salud.",
            "La regla es simple: ante la duda, para. Una lesion atendida a "
            "tiempo se resuelve antes; una ignorada puede dejarte fuera mucho "
            "mas tiempo.",
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
