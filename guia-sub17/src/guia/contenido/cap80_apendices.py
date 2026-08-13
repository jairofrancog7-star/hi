"""Capitulo 80 - Apendices (contenido en prosa).

Cierra la guia con material de apoyo: como usar los codigos QR y los videos de
ejemplo, un glosario de terminos del futbol, ideas para autoevaluarse y seguir
el progreso, y unas palabras finales. Contenido propio para Sub-17, en espanol
de Mexico, sin citar fuentes ni personas. Datos puros con render por plantillas.
Texto codificable en WinAnsi.
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

CAPITULO_ID: str = "cap80_apendices"
TITULO: str = "Apendices"
PAGINAS_OBJETIVO: int = 10

_NUMERO: str = "80"
_BAJADA: str = (
    "Material de apoyo: como usar los QR y los videos, glosario, "
    "autoevaluacion y palabras finales."
)

_SECCIONES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Como usar los QR y los videos",
        (
            "Muchas fichas traen un codigo QR y un enlace escrito. Sirven para "
            "ver un video de ejemplo del movimiento, porque ver un gesto bien "
            "hecho ayuda a entenderlo mas rapido que leerlo.",
            "Para abrir un QR, apunta la camara del telefono al codigo y toca "
            "el aviso que aparece. Si no tienes datos en la cancha, abre los "
            "enlaces antes desde tu casa con wifi y guardalos.",
            "Los enlaces llevan a busquedas de video, no a una fuente concreta: "
            "veras varias opciones y eliges la que mejor muestre el "
            "movimiento. Usa el video como referencia del gesto, no como una "
            "receta exacta; lo importante es entender la idea y adaptarla.",
            "El video no sustituye el entrenamiento: es un apoyo. Mira, "
            "entiende y luego practica muchas veces. La mejora llega con la "
            "repeticion, no con ver mas videos.",
        ),
    ),
    (
        "Glosario de terminos (parte 1)",
        (
            "Amplitud: usar todo el ancho del campo, con jugadoras abiertas "
            "pegadas a las bandas, para estirar a la rival.",
            "Profundidad: amenazar el espacio a la espalda de la defensa rival "
            "con carreras que atacan hacia la porteria.",
            "Basculacion: el desplazamiento de la linea o del bloque defensivo "
            "hacia el lado donde esta el balon, moviendose todas juntas.",
            "Control orientado: primer toque que deja el balon listo hacia el "
            "espacio libre y con el cuerpo de cara al juego.",
            "Desmarque: movimiento para librarse de la marca y ofrecerse a "
            "recibir; de apoyo si vienes al balon, de ruptura si atacas el "
            "espacio.",
            "Transicion: el instante de cambio entre atacar y defender, justo "
            "al recuperar o al perder el balon.",
        ),
    ),
    (
        "Glosario de terminos (parte 2)",
        (
            "Pared o uno-dos: combinacion en la que pasas, te desmarcas y te "
            "devuelven el balon de primeras a la espalda de la rival.",
            "Rondo: juego de posesion en un espacio cerrado donde unas "
            "conservan el balon y otra u otras intentan robarlo.",
            "Achique: la portera o la defensa que sale hacia la atacante para "
            "reducir su angulo de tiro o el espacio disponible.",
            "Cobertura: colocarse detras de la companera que va al duelo para "
            "ayudar si la superan.",
            "Fuera de juego: situacion en la que la atacante esta mas adelante "
            "de lo permitido respecto a la ultima defensora en el momento del "
            "pase.",
            "Version corta: la sesion reducida de treinta minutos o menos para "
            "cuando falta luz o tiempo.",
        ),
    ),
    (
        "Autoevaluacion y progreso",
        (
            "Mejorar se nota mas cuando se mide. Elige dos o tres gestos que "
            "quieras mejorar, como el pase con la pierna mala, los tiros a "
            "porteria o los duelos ganados, y anota de vez en cuando cuantos "
            "de diez te salen bien.",
            "No hace falta medir todo ni todos los dias. Una vez cada dos o "
            "tres semanas basta para ver la tendencia. Lo importante es "
            "comparar contigo misma, no con las demas.",
            "El progreso no es una linea recta: hay semanas de estancamiento y "
            "luego saltos. Ver tus numeros ayuda a tener paciencia en las "
            "mesetas y a celebrar los avances cuando llegan.",
            "Ponte metas que dependan de ti y sean alcanzables. Cumplir "
            "pequenas metas, una tras otra, es lo que construye a una gran "
            "jugadora con el tiempo.",
        ),
    ),
    (
        "Palabras finales",
        (
            "Esta guia es una herramienta, no un jefe. Usala con cabeza: "
            "adapta los ejercicios a tu equipo, a tu espacio y a tus "
            "jugadoras. Lo que funciona es lo que pueden hacer bien y con "
            "ganas.",
            "Entrena con constancia, cuida tu cuerpo y cuida a tus companeras. "
            "El talento ayuda, pero el trabajo diario y el buen ambiente de "
            "equipo llevan mas lejos que cualquier otra cosa.",
            "Sobre todo, disfruta. El futbol se juega mejor cuando se juega "
            "con alegria. Que cada entrenamiento y cada partido sean una razon "
            "para volver con ganas al siguiente.",
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
