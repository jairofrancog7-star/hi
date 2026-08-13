"""Capitulo 00 - Portada y front matter de la Guia_Extensa.

Contenido estructural (no de entrenamiento) del inicio del documento:

* **Portada** con titulo, subtitulo, lede y pie (plantilla ``portada``).
* **Como usar la guia**: como esta ordenada, como leer el indice, las fichas,
  los codigos QR y la rotacion semanal (plantilla ``texto``) -> Req 1.2, 1.6.
* **Descargo informativo**: el contenido es informativo y no sustituye la
  valoracion de un profesional de la salud (plantilla ``texto``) -> Req 6.11.
* **Protocolo de seguridad en cancha compartida** con ninos y con beisbol
  (plantilla ``texto``) -> Req 8.7.

Este modulo es **datos puros con render por plantillas**: no dibuja PDF ni HTML,
solo produce el Modelo_Paginas (`list[PaginaRender]`) apoyandose en las
plantillas de `guia.plantillas` y en el modelo de `guia.layout`. No inventa
fichas de ejercicio: todo el texto de aqui es front matter estandar y necesario,
redactado en espanol de Mexico y con lenguaje directo para jugadoras
adolescentes (Req 1.6). Todo el texto es codificable en WinAnsi (cp1252).

_Requirements: 1.2, 1.6, 6.11, 8.7_
"""

from __future__ import annotations

from ..layout import PaginaRender, Plantilla
from ..plantillas import (
    CtxPlantilla,
    DatosPortada,
    DatosTexto,
    PaginaPlantilla,
    portada,
    texto,
)

__all__ = [
    "CAPITULO_ID",
    "TITULO",
    "PAGINAS_OBJETIVO",
    "TEXTO_DESCARGO",
    "MARCADOR_DESCARGO",
    "MARCADOR_PROTOCOLO",
    "paginas",
]

#: Identificador del capitulo (coincide con la clave de PRESUPUESTO_PAGINAS).
CAPITULO_ID: str = "cap00_portada"

#: Titulo del capitulo, usado en el encabezado/pie de cada pagina (Req 1.5).
TITULO: str = "Portada y como usar la guia"

#: Paginas objetivo del capitulo segun la tabla de escalado del diseno.
PAGINAS_OBJETIVO: int = 8


# --------------------------------------------------------------------------- #
# Textos del front matter (constantes: contenido estructural, no de ejercicios)
# --------------------------------------------------------------------------- #

_TITULO_PORTADA: str = (
    "Guia Extensa de Entrenamiento de Futbol Femenil Sub-17"
)
_SUBTITULO_PORTADA: str = "Equipo femenil Sub-17 de Rincon de Centeno"
_LEDE_PORTADA: str = (
    "Material para entrenar toda la temporada: llegues sola o con siete "
    "companeras, con cancha completa o con una franja prestada. Aqui viene "
    "que hacer y como cuidarte."
)
_PIE_PORTADA: str = (
    "Estilo rosa y negro. Hecha para entrenar de martes a jueves y jugar el "
    "sabado, sin entrenador de planta."
)

#: Palabras clave que las pruebas usan para confirmar la presencia del descargo
#: (Req 6.11) y del protocolo de cancha compartida (Req 8.7) sin depender del
#: texto completo.
MARCADOR_DESCARGO: str = "No sustituye"
MARCADOR_PROTOCOLO: str = "cancha compartida"

_TITULO_COMO_USAR: str = "Como usar esta guia"
_PARRAFOS_COMO_USAR: tuple[str, ...] = (
    "Esta guia esta partida en capitulos. Al inicio hay un indice general que "
    "lista cada capitulo y cada modulo de posicion con su numero de pagina, "
    "para que llegues rapido a lo que necesitas ese dia.",
    "Cada ejercicio es una ficha: trae titulo, objetivo en una frase, un "
    "diagrama de la cancha, los pasos numerados, la dosis (series, "
    "repeticiones o tiempo), que debe mirar la companera, la variante para "
    "espacio reducido y cuantas jugadoras necesitas.",
    "Cuando una ficha tiene video de ejemplo, veras un codigo QR y el enlace "
    "escrito. Apunta la camara del telefono al QR o copia el enlace del "
    "apendice final para verlo cuando tengas datos o wifi.",
    "El plan de rotacion te da una semana distinta cada vez, con sesiones de "
    "martes, miercoles y jueves y las indicaciones para el partido del sabado. "
    "Si oscurece antes de tiempo, cada sesion tiene una version corta de 30 "
    "minutos o menos.",
    "Antes de empezar revisa cuantas jugadoras llegaron y cuanto espacio hay. "
    "La tabla de decision te dice que sesion hacer segun el numero de "
    "jugadoras, y muchas fichas se pueden hacer en una franja de 10 por 10 "
    "metros o menos.",
)

_TITULO_DESCARGO: str = "Descargo informativo"
#: Texto integro del descargo (Req 6.11). Se expone como constante para que las
#: pruebas y el orquestador puedan verificar su presencia sin re-renderizar.
TEXTO_DESCARGO: str = (
    "El contenido de esta guia es informativo y educativo. No sustituye la "
    "valoracion, el diagnostico ni el tratamiento de un profesional de la "
    "salud. Antes de iniciar un plan de entrenamiento, y ante cualquier "
    "molestia, dolor articular persistente, hinchazon o inestabilidad de "
    "rodilla, suspende el impacto y acude a valoracion medica."
)
_PARRAFOS_DESCARGO: tuple[str, ...] = (
    TEXTO_DESCARGO,
    "Entrena a tu ritmo. Si algo duele mas de lo normal o te sientes mareada, "
    "detente, hidratate y descansa. Escuchar a tu cuerpo tambien es parte del "
    "entrenamiento.",
)

_TITULO_PROTOCOLO: str = "Protocolo de seguridad en cancha compartida"
_PARRAFOS_PROTOCOLO: tuple[str, ...] = (
    "Muchas veces la cancha compartida se usa al mismo tiempo con ninos y con "
    "beisbol. Antes de entrenar, revisa el espacio y ubica donde estan los "
    "otros grupos para elegir una franja segura y lejos de la zona de bateo.",
    "Nunca coloques tu area de trabajo detras del bateador ni en la linea de "
    "un batazo o de un lanzamiento. Si escuchas la voz de alerta del beisbol, "
    "detente, ubica la pelota y espera a que sea seguro seguir.",
    "Cuida a los ninos que cruzan la cancha: para el ejercicio si alguien "
    "pequeno entra a tu franja y reanuda cuando este despejada. Manten los "
    "balones controlados para que no invadan el area de los demas.",
    "Marca tu espacio con gis y botellas para que se vea desde lejos, deja un "
    "pasillo de paso y acuerda con los otros grupos una senal para parar. Si "
    "el lugar se vuelve inseguro, muevete a otra franja o cambia a una ficha "
    "que ocupe menos espacio.",
)


# --------------------------------------------------------------------------- #
# Construccion de paginas
# --------------------------------------------------------------------------- #


def _a_paginas_render(
    plantilla: Plantilla,
    paginas_plantilla: list[PaginaPlantilla],
    folio_inicial: int,
) -> list[PaginaRender]:
    """Envuelve las `PaginaPlantilla` de una plantilla en `PaginaRender`.

    Asigna folios consecutivos desde `folio_inicial` y propaga el capitulo al
    encabezado/pie (Req 1.5). Devuelve la lista de paginas ya numeradas.
    """
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
    """Produce el Modelo_Paginas del capitulo de portada.

    Concatena, en orden, la portada, la seccion "como usar la guia", el descargo
    informativo y el protocolo de seguridad en cancha compartida, numerando los
    folios de forma consecutiva desde `folio_inicial`. `ctx` permite compartir
    la geometria del area imprimible con el resto del pipeline; si es `None` se
    usa la geometria por defecto de `guia.layout`.
    """
    bloques: tuple[tuple[Plantilla, list[PaginaPlantilla]], ...] = (
        (
            Plantilla.PORTADA,
            portada(
                DatosPortada(
                    titulo=_TITULO_PORTADA,
                    subtitulo=_SUBTITULO_PORTADA,
                    lede=_LEDE_PORTADA,
                    pie=_PIE_PORTADA,
                ),
                ctx,
            ),
        ),
        (
            Plantilla.TEXTO,
            texto(
                DatosTexto(
                    parrafos=_PARRAFOS_COMO_USAR, titulo=_TITULO_COMO_USAR
                ),
                ctx,
            ),
        ),
        (
            Plantilla.TEXTO,
            texto(
                DatosTexto(parrafos=_PARRAFOS_DESCARGO, titulo=_TITULO_DESCARGO),
                ctx,
            ),
        ),
        (
            Plantilla.TEXTO,
            texto(
                DatosTexto(
                    parrafos=_PARRAFOS_PROTOCOLO, titulo=_TITULO_PROTOCOLO
                ),
                ctx,
            ),
        ),
    )

    render: list[PaginaRender] = []
    folio = folio_inicial
    for plantilla, paginas_plantilla in bloques:
        paginas_cap = _a_paginas_render(plantilla, paginas_plantilla, folio)
        render.extend(paginas_cap)
        folio += len(paginas_cap)
    return render
