"""Catalogo_Diagramas: los ocho Diagrama_Postura de la guia.

Modulo declarativo de la feature `imagenes-reales-hero-interactivo`. Declara,
para cada uno de los ocho Diagrama_Postura, su Archivo_Diagrama, su texto
alternativo, sus dimensiones por modo de render, sus cinco pasos numerados, sus
Etiqueta_Anatomica, sus Fase_Numerada, su Fundamento, su postura equivalente de
`figuras.FIGURAS`, su marca Requiere_Archivo, su Advertencia_Cabeceo, su error
frecuente y su credito.

Reglas del proyecto que este modulo respeta:

* Python 3.11+, solo libreria estandar.
* **Ningun `assert`**: todo invariante se comprueba con `raise ErrorAsset(...)`
  (`python -O` borra los `assert`).
* Cero peticiones de red: `presentes()` solo mira el sistema de archivos local.
* Tono del Requisito 17: segunda persona del singular y femenino, sin nombres
  propios de personas ni de clubes, cada paso empezando por un verbo de
  `VERBOS_PERMITIDOS`.

_Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 2.12,
5.1, 5.2, 5.3, 5.4, 13.4, 14.12, 14.13, 14.14, 14.16, 17.1, 17.2, 17.3, 17.4,
17.5, 17.6, 17.7, 20.1, 20.2, 20.3, 20.5_
"""

from __future__ import annotations

import os
import unicodedata
from dataclasses import dataclass

from . import figuras
from .errores import E_ASSET_INVALIDO, ErrorAsset

# --------------------------------------------------------------------------- #
# Constantes de ubicacion y de anclas
# --------------------------------------------------------------------------- #

#: Los cuatro Fundamento del conjunto cerrado (criterio 2.8).
FUNDAMENTOS: tuple[str, ...] = ("golpeo", "pase", "control-conduccion", "cabeceo")

#: Directorio relativo de los Archivo_Diagrama. Siempre con "/", porque viaja al
#: HTML como ruta relativa (criterio 1.1), no como ruta del sistema.
DIR_ASSETS: str = "assets/img/tecnica"

#: Extensiones que acepta el Guardarrail_Recursos (criterio 1.3).
EXTENSIONES: tuple[str, ...] = (".webp", ".svg", ".png", ".avif")

#: Extensiones_Permitidas del Validador_Rutas, en el orden exacto del criterio
#: 30.1. Es un **alias** de `EXTENSIONES`, no un segundo literal: si alguien
#: anade un formato tiene que anadirlo en un solo sitio, y `validar_catalogo()`
#: comprueba que las dos sigan siendo la misma tupla.
EXTENSIONES_PERMITIDAS: tuple[str, ...] = EXTENSIONES

#: Prefijo obligatorio de toda ruta de Asset_Local (criterio 30.2).
PREFIJO_ASSETS: str = "assets/"

#: Segmento de ruta que el Validador_Rutas rechaza siempre (criterio 30.4).
SEGMENTO_ASCENDENTE: str = ".."

#: Prefijos que provocarian una peticion de red o una ruta absoluta y que el
#: Validador_Rutas rechaza nombrando la ruta (criterio 30.3). El orden importa:
#: `http://` y `https://` se comprueban antes que `//` y que `/`, para que el
#: mensaje nombre el prefijo mas especifico.
PREFIJOS_RECHAZADOS: tuple[str, ...] = ("http://", "https://", "//", "/")

#: Ancla de la seccion de tecnica (criterio 3.1).
ANCLA_TECNICA: str = "tecnica-en-imagenes"

#: Ancla de la seccion del vocabulario del cuerpo (criterio 3.2).
ANCLA_ANATOMIA: str = "anatomia-base"

#: Ancla del Bloque_Creditos (criterio 18.1).
ANCLA_CREDITOS: str = "creditos"

#: Ancho maximo declarado de un Archivo_Diagrama, en pixeles (criterio 2.4).
ANCHO_MAXIMO: int = 1200

#: Longitud minima del texto alternativo (criterios 2.5 y 2.6).
MINIMO_ALT: int = 60

#: Longitud minima de cada paso numerado (criterio 2.7).
MINIMO_PASO: int = 20

#: Cantidad exacta de pasos por entrada, en el orden fijo del criterio 2.7.
PASOS_POR_ENTRADA: int = 5

#: Nombre de cada paso, en el orden fijo que exige el criterio 2.7.
ORDEN_PASOS: tuple[str, ...] = (
    "pie de apoyo",
    "superficie de contacto",
    "torso",
    "brazos",
    "mirada",
)

#: Modos de render del criterio 5.3 y 5.4.
MODO_ARCHIVO: str = "archivo"
MODO_SVG: str = "svg"


# --------------------------------------------------------------------------- #
# Estructuras declarativas
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Credito:
    """Credito de un Diagrama_Postura para el Bloque_Creditos (Requisito 18).

    `enlace` es **texto visible**: nunca se emite como `<a href>` ni como
    atributo que provoque una peticion de red (criterio 18.5). Un campo en
    `None` se emite con la marca `dato pendiente` (criterio 18.8).
    """

    autor: str | None
    fuente: str | None
    licencia: str | None
    enlace: str | None


@dataclass(frozen=True, slots=True)
class Fase:
    """Fase_Numerada de un gesto con secuencia (criterios 14.10 a 14.12)."""

    numero: int
    texto: str


@dataclass(frozen=True, slots=True)
class DiagramaPostura:
    """Una entrada del Catalogo_Diagramas.

    `ancho_archivo` y `alto_archivo` son las dimensiones del Archivo_Diagrama;
    `ancho_svg` y `alto_svg` las del SVG que emite el Generador_SVG. El render
    usa las del modo efectivo (criterios 4.3 y 4.8).

    `girable` marca la entrada como Figura_Girable del Proyector_Vistas: el
    Target_Web emite para ella las diez Vista_Figura de `CLAVES_VISTA` en vez de
    un solo dibujo. Es verdadero **solo** en `anatomia-base`, que gira dentro de
    su Visor_Ampliado, y falso en las otras siete (criterio 22.5).
    """

    id: str
    titulo: str
    archivo: str
    alt: str
    ancho_archivo: int
    alto_archivo: int
    ancho_svg: int
    alto_svg: int
    pasos: tuple[str, ...]
    etiquetas: tuple[str, ...]
    fases: tuple[Fase, ...]
    fundamento: str | None
    postura_id: str | None
    requiere_archivo: bool
    girable: bool
    advertencia: str | None
    error_frecuente: str
    credito: Credito


#: Credito comun de las ocho entradas: los diagramas los dibuja el
#: Generador_SVG del propio proyecto, asi que la autoria y la licencia son
#: propias (criterio 18.4). `enlace` queda en `None` a proposito: no hay URL que
#: mostrar y el Bloque_Creditos lo marca como `dato pendiente` (criterio 18.8).
CREDITO_PROPIO: Credito = Credito(
    autor="Equipo de la guía Sub-17",
    fuente="Dibujo hecho dentro de la propia guía",
    licencia="CC BY-SA 4.0",
    enlace=None,
)

#: Advertencia_Cabeceo (criterios 20.1 a 20.3). Cubre los siete conceptos de
#: `CONCEPTOS_CABECEO`: la frente como unica superficie, la coronilla y la cara
#: como zonas a evitar, el cuello contraido y firme, los ojos abiertos, el balon
#: blando y la progresion sin salto para menores. Mas de 120 caracteres.
ADVERTENCIA_CABECEO: str = (
    "Seguridad antes que nada: cabecea solo con la frente, nunca con la "
    "coronilla ni con la cara. Mantén el cuello contraído y firme, los hombros "
    "apretados y los ojos abiertos hasta el contacto. Empieza con un balón "
    "blando, poco inflado, y trabaja sin salto: primero de rodillas y luego de "
    "pie, y sumas altura solo cuando el gesto te sale limpio."
)


# --------------------------------------------------------------------------- #
# Catalogo_Diagramas: las ocho entradas, en el orden del criterio 2.1
# --------------------------------------------------------------------------- #

CATALOGO: tuple[DiagramaPostura, ...] = (
    DiagramaPostura(
        id="anatomia-base",
        titulo="Vocabulario del cuerpo",
        archivo="anatomia-base.webp",
        alt=(
            "Silueta de una jugadora de pie, vista de frente, con los rótulos "
            "de frente, cuello, hombro, codo, mano, torso, cadera, rodilla, "
            "espinilla, pie, empeine, planta, parte interna, parte externa, "
            "línea media y centro de gravedad."
        ),
        ancho_archivo=1200,
        alto_archivo=1800,
        ancho_svg=360,
        alto_svg=540,
        pasos=(
            "Apoya los dos pies a la anchura de tus caderas y reparte el peso.",
            "Coloca la planta completa en el suelo y siente el apoyo del empeine.",
            "Alinea el torso sobre la línea media, sin arquear la espalda baja.",
            "Lleva los brazos algo separados del cuerpo, con los codos sueltos.",
            "Mira al frente y reconoce cada parte que nombran los rótulos.",
        ),
        etiquetas=(
            "frente",
            "cuello",
            "hombro",
            "codo",
            "mano",
            "torso",
            "línea media",
            "centro de gravedad",
            "cadera",
            "rodilla",
            "espinilla",
            "pie",
            "empeine",
            "planta",
            "parte interna",
            "parte externa",
        ),
        fases=(),
        fundamento=None,
        postura_id=None,
        requiere_archivo=False,
        girable=True,
        advertencia=None,
        error_frecuente=(
            "Cargas todo el peso en una pierna y pierdes la referencia de la "
            "línea media, así que los rótulos dejan de coincidir con tu postura."
        ),
        credito=CREDITO_PROPIO,
    ),
    DiagramaPostura(
        id="tiro-empeine",
        titulo="Remate con el empeine",
        archivo="tiro-empeine.webp",
        alt=(
            "Jugadora remata el balón con el empeine: el pie de apoyo queda al "
            "costado del balón, el torso se inclina sobre él, los brazos se "
            "abren para equilibrar y la mirada baja al punto de contacto."
        ),
        ancho_archivo=1200,
        alto_archivo=1600,
        ancho_svg=360,
        alto_svg=480,
        pasos=(
            "Coloca el pie de apoyo junto al balón, a un pie de distancia.",
            "Golpea con el empeine, con el tobillo firme y la punta extendida.",
            "Lleva el torso apenas sobre el balón para no elevar el disparo.",
            "Acompaña con el brazo contrario abierto para sostener el equilibrio.",
            "Mira el punto de contacto y sube la vista tras el golpeo.",
        ),
        etiquetas=("empeine", "pie", "rodilla", "cadera", "torso", "mano"),
        fases=(),
        fundamento="golpeo",
        postura_id="tiro-potencia-empeine",
        requiere_archivo=False,
        girable=False,
        advertencia=None,
        error_frecuente=(
            "Golpeas con la punta del pie en vez del empeine y el balón sale "
            "flojo y sin dirección."
        ),
        credito=CREDITO_PROPIO,
    ),
    DiagramaPostura(
        id="pase-interior",
        titulo="Pase corto con la parte interna",
        archivo="pase-interior.webp",
        alt=(
            "Jugadora da un pase corto con la parte interna del pie: el pie de "
            "apoyo apunta al destino, el torso queda de frente al balón, los "
            "brazos acompañan el giro y la mirada revisa a la compañera."
        ),
        ancho_archivo=1200,
        alto_archivo=1600,
        ancho_svg=360,
        alto_svg=480,
        pasos=(
            "Coloca el pie de apoyo apuntando hacia donde quieres el pase.",
            "Contacta el balón con la parte interna, a la altura del tobillo.",
            "Mantén el torso de frente al balón, con el peso algo adelantado.",
            "Lleva los brazos separados para no perder el equilibrio al pasar.",
            "Mira a tu compañera antes del contacto y vuelve al balón.",
        ),
        etiquetas=("parte interna", "pie", "rodilla", "cadera", "torso"),
        fases=(),
        fundamento="pase",
        postura_id="pase-corto-interior",
        requiere_archivo=False,
        girable=False,
        advertencia=None,
        error_frecuente=(
            "Contactas el balón con la punta y el pase se desvía del recorrido "
            "que buscabas."
        ),
        credito=CREDITO_PROPIO,
    ),
    DiagramaPostura(
        id="control-balon",
        titulo="Control orientado con la planta",
        archivo="control-balon.webp",
        alt=(
            "Jugadora controla el balón con la planta del pie: el pie de apoyo "
            "cede un paso, el torso gira hacia el espacio libre, los brazos "
            "protegen el balón y la mirada se levanta al terminar el control."
        ),
        ancho_archivo=1200,
        alto_archivo=1600,
        ancho_svg=360,
        alto_svg=480,
        pasos=(
            "Apoya el pie de atrás y deja libre la pierna que recibe.",
            "Amortigua el balón con la planta, cediendo el pie hacia atrás.",
            "Gira el torso hacia el espacio libre en el mismo movimiento.",
            "Protege el balón con el brazo del lado de la rival.",
            "Mira el espacio antes de recibir y confirma tras el control.",
        ),
        etiquetas=("planta", "pie", "rodilla", "cadera", "torso"),
        fases=(),
        fundamento="control-conduccion",
        postura_id="control-orientado",
        requiere_archivo=False,
        girable=False,
        advertencia=None,
        error_frecuente=(
            "Frenas el balón con el pie rígido y te rebota lejos del cuerpo."
        ),
        credito=CREDITO_PROPIO,
    ),
    DiagramaPostura(
        id="conduccion",
        titulo="Conducción con la parte externa",
        archivo="conduccion.webp",
        alt=(
            "Jugadora conduce el balón con la parte externa del pie: el pie de "
            "apoyo marca el ritmo, el torso se mantiene erguido, los brazos se "
            "balancean con la zancada y la mirada alterna balón y campo."
        ),
        ancho_archivo=1200,
        alto_archivo=1600,
        ancho_svg=360,
        alto_svg=480,
        pasos=(
            "Apoya el pie contrario cerca del balón en cada zancada.",
            "Empuja el balón con la parte externa y el empeine del pie.",
            "Mantén el torso erguido y las rodillas algo flexionadas.",
            "Acompaña cada zancada con los brazos sueltos y algo abiertos.",
            "Mira al frente y baja la vista solo para ajustar el toque.",
        ),
        etiquetas=("parte externa", "empeine", "pie", "rodilla", "torso"),
        fases=(),
        fundamento="control-conduccion",
        postura_id="conduccion",
        requiere_archivo=False,
        girable=False,
        advertencia=None,
        error_frecuente=(
            "Empujas el balón demasiado lejos y lo pierdes en cuanto llega la "
            "presión."
        ),
        credito=CREDITO_PROPIO,
    ),
    DiagramaPostura(
        id="potencia-carrera",
        titulo="Disparo potente con carrera",
        archivo="potencia-carrera.webp",
        alt=(
            "Jugadora dispara con potencia tras la carrera y golpea con el "
            "empeine: el pie de apoyo queda firme al costado, el torso se "
            "inclina sobre el balón, los brazos equilibran el giro y la mirada "
            "sigue el punto de contacto."
        ),
        ancho_archivo=1200,
        alto_archivo=1600,
        ancho_svg=360,
        alto_svg=480,
        pasos=(
            "Apoya el pie de apoyo firme al costado, con la punta al arco.",
            "Golpea con el empeine y el tobillo bloqueado, no con la espinilla.",
            "Lleva el torso sobre el balón y baja el hombro del lado que golpea.",
            "Impulsa el brazo contrario hacia arriba para ganar potencia.",
            "Mira el balón en el impacto y luego levanta la vista al arco.",
        ),
        etiquetas=("empeine", "espinilla", "rodilla", "cadera", "torso", "mano"),
        fases=(
            Fase(
                numero=1,
                texto=(
                    "Aproximas en diagonal al balón, con los últimos pasos más "
                    "cortos."
                ),
            ),
            Fase(
                numero=2,
                texto=(
                    "Plantas el pie de apoyo y armas la pierna de atrás con la "
                    "rodilla flexionada."
                ),
            ),
            Fase(
                numero=3,
                texto=(
                    "Impactas con el empeine y acompañas el pie hacia el "
                    "objetivo."
                ),
            ),
        ),
        fundamento="golpeo",
        postura_id="tiro-potencia-empeine",
        requiere_archivo=False,
        girable=False,
        advertencia=None,
        error_frecuente=(
            "Abres el cuerpo antes del impacto y el disparo se te va muy alto."
        ),
        credito=CREDITO_PROPIO,
    ),
    DiagramaPostura(
        id="cabeceo-frente",
        titulo="Cabeceo con la frente",
        archivo="cabeceo-frente.webp",
        alt=(
            "Jugadora cabecea el balón con la frente: los pies separados dan un "
            "pie de apoyo estable, el torso se echa atrás y vuelve, los brazos "
            "suben para cuidar su espacio y la mirada sigue el balón con los "
            "ojos abiertos."
        ),
        ancho_archivo=1200,
        alto_archivo=1600,
        ancho_svg=360,
        alto_svg=480,
        pasos=(
            "Apoya los dos pies separados, con una pierna algo adelantada.",
            "Contacta el balón con la frente, nunca con la coronilla ni la cara.",
            "Lleva el torso atrás y devuélvelo al balón con el cuello firme.",
            "Mantén los brazos arriba y algo abiertos para cuidar tu espacio.",
            "Mira el balón con los ojos abiertos hasta el momento del contacto.",
        ),
        etiquetas=("frente", "cuello", "torso", "mano", "cadera"),
        fases=(),
        fundamento="cabeceo",
        postura_id=None,
        requiere_archivo=False,
        girable=False,
        advertencia=ADVERTENCIA_CABECEO,
        error_frecuente=(
            "Cierras los ojos y giras la cabeza, y el balón te golpea la "
            "coronilla."
        ),
        credito=CREDITO_PROPIO,
    ),
    DiagramaPostura(
        id="pase-largo-empeine",
        titulo="Pase largo con el empeine: pase elevado a distancia",
        archivo="pase-largo-empeine.webp",
        alt=(
            "Jugadora ejecuta un pase elevado a distancia con el empeine: el "
            "pie de apoyo se planta detrás y al costado del balón, el torso se "
            "echa atrás, los brazos se abren para equilibrar y la mirada calcula "
            "la trayectoria."
        ),
        ancho_archivo=1200,
        alto_archivo=1600,
        ancho_svg=360,
        alto_svg=480,
        pasos=(
            "Coloca el pie de apoyo detrás y al costado del balón.",
            "Golpea con el empeine por debajo del balón para elevarlo.",
            "Lleva el torso hacia atrás en el momento del contacto.",
            "Acompaña el golpeo con los brazos abiertos para equilibrar.",
            "Mira el destino del pase y vuelve la vista al balón.",
        ),
        etiquetas=("empeine", "pie", "rodilla", "cadera", "torso"),
        fases=(),
        fundamento="pase",
        postura_id="pase-largo-empeine",
        requiere_archivo=False,
        girable=False,
        advertencia=None,
        error_frecuente=(
            "Golpeas el centro del balón y el pase sale raso, sin alcanzar la "
            "distancia."
        ),
        credito=CREDITO_PROPIO,
    ),
)

#: Identificadores en el orden exacto del criterio 2.1. Se derivan del catalogo,
#: para que no haya dos listas capaces de desincronizarse.
IDS: tuple[str, ...] = tuple(d.id for d in CATALOGO)


# --------------------------------------------------------------------------- #
# Vocabulario anatomico cerrado (criterios 14.13 y 14.16)
# --------------------------------------------------------------------------- #

#: Las dieciseis Etiqueta_Anatomica que declara `anatomia-base`, en el orden de
#: la tabla del diseno: cabeza y tronco, ejes, cadera y pierna, pie. Es el
#: vocabulario **cerrado** de la guia: toda etiqueta de cualquier diagrama
#: pertenece a este conjunto (criterio 14.16) y `anatomia-base` va primera del
#: catalogo porque ensena las palabras que usan los otros siete.
ETIQUETAS_ANATOMIA: tuple[str, ...] = (
    "frente",
    "cuello",
    "hombro",
    "codo",
    "mano",
    "torso",
    "línea media",
    "centro de gravedad",
    "cadera",
    "rodilla",
    "espinilla",
    "pie",
    "empeine",
    "planta",
    "parte interna",
    "parte externa",
)

#: Las diecisiete articulaciones del esqueleto parametrico. Se declaran aqui
#: porque el mapa `etiqueta -> articulacion` es parte del vocabulario, y el
#: Generador_SVG (`svg_postura.py`) reutiliza esta tupla en vez de repetirla.
ARTICULACIONES: tuple[str, ...] = (
    "cabeza",
    "cuello",
    "hombro_i",
    "hombro_d",
    "codo_i",
    "codo_d",
    "mano_i",
    "mano_d",
    "torso",
    "cadera_i",
    "cadera_d",
    "rodilla_i",
    "rodilla_d",
    "tobillo_i",
    "tobillo_d",
    "pie_i",
    "pie_d",
)

#: Etiquetas cuyo punto **no** es una articulacion del esqueleto, sino un punto
#: derivado de ella: `espinilla` es el punto medio de rodilla-tobillo; `empeine`,
#: `planta`, `parte interna` y `parte externa` son puntos del pie de contacto;
#: `línea media` es el eje vertical de la pose y `centro de gravedad` el punto
#: que la pose declara sobre ese eje. El Generador_SVG ancla cada una a la
#: articulacion base que le asigna `ARTICULACION_POR_ETIQUETA`.
ETIQUETAS_DERIVADAS: frozenset[str] = frozenset(
    {
        "espinilla",
        "empeine",
        "planta",
        "parte interna",
        "parte externa",
        "línea media",
        "centro de gravedad",
    }
)

#: Mapa declarativo etiqueta -> articulacion base. El lado derecho de la figura
#: (`_d`) es el que queda hacia la lectora en las ocho poses, asi que las
#: etiquetas de miembro se anclan ahi.
ARTICULACION_POR_ETIQUETA: dict[str, str] = {
    "frente": "cabeza",
    "cuello": "cuello",
    "hombro": "hombro_d",
    "codo": "codo_d",
    "mano": "mano_d",
    "torso": "torso",
    "línea media": "torso",
    "centro de gravedad": "torso",
    "cadera": "cadera_d",
    "rodilla": "rodilla_d",
    "espinilla": "tobillo_d",
    "pie": "pie_d",
    "empeine": "pie_d",
    "planta": "pie_d",
    "parte interna": "pie_d",
    "parte externa": "pie_d",
}


def articulacion_de(etiqueta: str) -> str:
    """Articulacion base a la que se ancla `etiqueta`.

    Lanza `ErrorAsset(E_ASSET_INVALIDO)` cuando la etiqueta no pertenece al
    vocabulario cerrado, para que el fallo nombre la etiqueta y no reviente mas
    tarde con un `KeyError` opaco dentro del Generador_SVG.
    """
    ancla: str | None = ARTICULACION_POR_ETIQUETA.get(etiqueta)
    if ancla is None:
        raise ErrorAsset(
            f"etiqueta anatomica fuera del vocabulario cerrado: {etiqueta!r}",
            detalle={"etiqueta": etiqueta},
            codigo=E_ASSET_INVALIDO,
        )
    return ancla


def validar_vocabulario() -> None:
    """Comprueba el vocabulario anatomico cerrado (criterios 14.13 y 14.16).

    Tres invariantes, todos con `raise ErrorAsset` y ningun `assert`:

    1. `ETIQUETAS_ANATOMIA` tiene exactamente dieciseis terminos sin repetir y
       coincide con las etiquetas que declara `anatomia-base`.
    2. El mapa `etiqueta -> articulacion` cubre las dieciseis y solo apunta a
       articulaciones reales del esqueleto.
    3. Toda etiqueta de cualquier entrada del catalogo pertenece al vocabulario.
    """
    if len(ETIQUETAS_ANATOMIA) != 16:
        raise ErrorAsset(
            "el vocabulario anatomico debe tener 16 terminos, no "
            f"{len(ETIQUETAS_ANATOMIA)}",
            detalle={"cantidad": len(ETIQUETAS_ANATOMIA)},
        )
    if len(set(ETIQUETAS_ANATOMIA)) != len(ETIQUETAS_ANATOMIA):
        raise ErrorAsset("el vocabulario anatomico repite algun termino")

    base: DiagramaPostura = CATALOGO[0]
    if base.etiquetas != ETIQUETAS_ANATOMIA:
        raise ErrorAsset(
            f"{base.id}: sus etiquetas no son el vocabulario anatomico cerrado",
            detalle={"id": base.id},
        )

    if set(ARTICULACION_POR_ETIQUETA) != set(ETIQUETAS_ANATOMIA):
        faltantes: tuple[str, ...] = tuple(
            sorted(set(ETIQUETAS_ANATOMIA) - set(ARTICULACION_POR_ETIQUETA))
        )
        raise ErrorAsset(
            "el mapa etiqueta -> articulacion no cubre el vocabulario: "
            f"faltan {faltantes}",
            detalle={"faltantes": faltantes},
        )

    validas: frozenset[str] = frozenset(ARTICULACIONES)
    for etiqueta in ETIQUETAS_ANATOMIA:
        ancla: str = ARTICULACION_POR_ETIQUETA[etiqueta]
        if ancla not in validas:
            raise ErrorAsset(
                f"etiqueta {etiqueta!r} anclada a una articulacion inexistente: "
                f"{ancla!r}",
                detalle={"etiqueta": etiqueta, "articulacion": ancla},
            )

    permitidas: frozenset[str] = frozenset(ETIQUETAS_ANATOMIA)
    for diagrama in CATALOGO:
        for etiqueta in diagrama.etiquetas:
            if etiqueta not in permitidas:
                raise ErrorAsset(
                    f"{diagrama.id}: etiqueta {etiqueta!r} fuera del "
                    "vocabulario anatomico cerrado",
                    detalle={"id": diagrama.id, "etiqueta": etiqueta},
                )


# --------------------------------------------------------------------------- #
# Guardarrail_Lexico (Requisito 17)
# --------------------------------------------------------------------------- #

#: Verbos permitidos al inicio de un paso: segunda persona del singular, en
#: imperativo, dirigidos a la jugadora (criterios 17.2 y 17.3).
VERBOS_PERMITIDOS: tuple[str, ...] = (
    "coloca",
    "apoya",
    "gira",
    "lleva",
    "mira",
    "golpea",
    "contacta",
    "acompaña",
    "flexiona",
    "alinea",
    "mantén",
    "empuja",
    "recibe",
    "amortigua",
    "controla",
    "conduce",
    "protege",
    "salta",
    "impulsa",
    "respira",
)

#: Masculino generico: la guia habla de jugadoras, nunca de "el jugador"
#: (criterio 17.4).
MASCULINO_GENERICO: tuple[str, ...] = (
    "el jugador",
    "los jugadores",
    "el alumno",
    "los alumnos",
    "el niño",
    "los niños",
    "el chico",
    "los chicos",
)

#: Formas masculinas de adjetivo referidas a la lectora (criterio 17.5). Se
#: buscan con limites de palabra, para no atrapar "listones" ni "cansancio".
FORMAS_MASCULINAS: tuple[str, ...] = (
    "listo",
    "atento",
    "concentrado",
    "cansado",
    "preparado",
)

#: Expresiones condescendientes (criterio 17.6): minimizan la dificultad o
#: hablan a la jugadora desde arriba.
CONDESCENDIENTES: tuple[str, ...] = (
    "es facilísimo",
    "es muy fácil",
    "no te compliques",
    "solo tienes que",
)

#: Nombres de club vetados en la superficie visible de la guia (criterio 2.11).
#: Es la **misma** lista que aplica el guardarrail vigente
#: `test/test_guardarrail_clubes.py`; la Property 3 compara las dos tuplas, de
#: modo que no puedan desincronizarse. La comparacion siempre lleva limites de
#: palabra: sin ellos "Inter" daria falso positivo en "parte interna".
CLUBES_VETADOS: tuple[str, ...] = (
    "Olympique",
    "Lyonnais",
    "Lyon",
    "Barcelona",
    "Barcelona Femeni",
    "Barca",
    "Barça",
    "Chelsea",
    "Arsenal",
    "Tigres",
    "Rayadas",
    "Monterrey",
    "Bayern",
    "Wolfsburg",
    "Portland",
    "Thorns",
    "Manchester",
    "Real Madrid",
    "Juventus",
    "Atletico",
    "Atlético",
    "America",
    "América",
    "Houston",
    "North Carolina",
    "PSG",
    "Paris Saint",
    "Roma",
    "Milan",
    "Inter",
    "Liverpool",
)

#: Todas las expresiones prohibidas, en el orden en que se reportan: primero el
#: masculino generico, luego las formas masculinas, luego las condescendientes y
#: al final los clubes.
EXPRESIONES_PROHIBIDAS: tuple[str, ...] = (
    *MASCULINO_GENERICO,
    *FORMAS_MASCULINAS,
    *CONDESCENDIENTES,
    *CLUBES_VETADOS,
)


def _plegar_acentos(texto: str) -> str:
    """Quita las marcas diacriticas de `texto` sin tocar el resto."""
    descompuesto: str = unicodedata.normalize("NFD", texto)
    letras: list[str] = [
        caracter
        for caracter in descompuesto
        if not unicodedata.combining(caracter)
    ]
    return unicodedata.normalize("NFC", "".join(letras))


def normalizar_lexico(texto: str) -> str:
    """Normaliza `texto` para el Guardarrail_Lexico: minusculas y sin acentos.

    Plegar los acentos hace que "es facilísimo" y "es facilisimo" se detecten
    igual, y que "mantén" case con el verbo permitido "manten".
    """
    return _plegar_acentos(texto).lower()


def _es_letra_o_digito(caracter: str) -> bool:
    """True si `caracter` cuenta como parte de una palabra."""
    return caracter.isalnum()


def _hay_expresion(texto_normalizado: str, expresion_normalizada: str) -> bool:
    """Busca `expresion_normalizada` con limites de palabra.

    Se implementa a mano en vez de con `re`: la expresion puede llevar espacios y
    caracteres que habria que escapar, y aqui basta con recorrer las apariciones
    y comprobar que el caracter anterior y el siguiente no son parte de una
    palabra. Asi "listo" no casa con "listones" y "el niño" no casa con
    "del niño".
    """
    if not expresion_normalizada:
        return False
    largo: int = len(expresion_normalizada)
    desde: int = 0
    while True:
        posicion: int = texto_normalizado.find(expresion_normalizada, desde)
        if posicion < 0:
            return False
        antes: str = texto_normalizado[posicion - 1] if posicion > 0 else " "
        fin: int = posicion + largo
        despues: str = texto_normalizado[fin] if fin < len(texto_normalizado) else " "
        if not _es_letra_o_digito(antes) and not _es_letra_o_digito(despues):
            return True
        desde = posicion + 1


def violaciones_lexicas(id_: str, texto: str) -> tuple[str, ...]:
    """Expresiones prohibidas que `texto` contiene (Requisito 17).

    Devuelve la tupla de expresiones halladas, en el orden de
    `EXPRESIONES_PROHIBIDAS`, con la forma **declarada** (con sus acentos y sus
    mayusculas), que es la que debe aparecer en el mensaje de fallo junto con
    `id_` (criterio 17.7). Una tupla vacia significa que el texto pasa el
    guardarrail.

    `id_` no se usa para decidir: entra para que la persona que lee el fallo sepa
    de que entrada del catalogo salio el texto, y para que la firma sea la misma
    que consumen el validador y la prueba de propiedad.
    """
    if not id_:
        raise ErrorAsset("violaciones_lexicas exige el identificador de la entrada")
    normalizado: str = normalizar_lexico(texto)
    halladas: list[str] = []
    for expresion in EXPRESIONES_PROHIBIDAS:
        if _hay_expresion(normalizado, normalizar_lexico(expresion)):
            halladas.append(expresion)
    return tuple(halladas)


def mensaje_lexico(id_: str, expresion: str) -> str:
    """Mensaje de fallo del Guardarrail_Lexico (criterio 17.7)."""
    return f"{id_}: expresion prohibida por el Guardarrail_Lexico: {expresion!r}"


def validar_lexico(id_: str, texto: str) -> None:
    """Lanza `ErrorAsset` nombrando la entrada y la primera expresion hallada."""
    halladas: tuple[str, ...] = violaciones_lexicas(id_, texto)
    if halladas:
        raise ErrorAsset(
            mensaje_lexico(id_, halladas[0]),
            detalle={"id": id_, "expresiones": halladas},
        )


def verbo_inicial(paso: str) -> str:
    """Primera palabra de `paso`, normalizada para comparar con los verbos."""
    normalizado: str = normalizar_lexico(paso).strip()
    letras: list[str] = []
    for caracter in normalizado:
        if _es_letra_o_digito(caracter):
            letras.append(caracter)
            continue
        break
    return "".join(letras)


#: Verbos permitidos ya normalizados, para comparar sin recalcular en bucle.
_VERBOS_NORMALIZADOS: frozenset[str] = frozenset(
    normalizar_lexico(v) for v in VERBOS_PERMITIDOS
)


def empieza_con_verbo_permitido(paso: str) -> bool:
    """True si `paso` empieza por un verbo de `VERBOS_PERMITIDOS` (criterio 17.3)."""
    return verbo_inicial(paso) in _VERBOS_NORMALIZADOS


def textos_de(d: DiagramaPostura) -> tuple[str, ...]:
    """Todos los textos visibles de una entrada, para pasarlos al guardarrail."""
    partes: list[str] = [d.titulo, d.alt, *d.pasos, d.error_frecuente]
    partes.extend(fase.texto for fase in d.fases)
    if d.advertencia is not None:
        partes.append(d.advertencia)
    credito: Credito = d.credito
    for campo in (credito.autor, credito.fuente, credito.licencia, credito.enlace):
        if campo is not None:
            partes.append(campo)
    return tuple(partes)


# --------------------------------------------------------------------------- #
# Advertencia_Cabeceo (Requisito 20)
# --------------------------------------------------------------------------- #

#: Longitud minima de la Advertencia_Cabeceo (criterio 20.3).
MINIMO_ADVERTENCIA: int = 120

#: Los siete conceptos que la Advertencia_Cabeceo debe cubrir, cada uno con sus
#: sinonimos aceptados (criterio 20.2). El nombre del concepto es lo que aparece
#: en el mensaje de fallo (criterio 20.5); los sinonimos son las cadenas que se
#: buscan en el texto ya normalizado, asi que "cuello contraído" tambien casa
#: escrito sin tilde.
CONCEPTOS_CABECEO: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("frente como única superficie", ("frente",)),
    ("coronilla a evitar", ("coronilla",)),
    ("cara a evitar", ("cara", "rostro")),
    ("cuello contraído y firme", ("cuello contraído", "cuello firme")),
    ("ojos abiertos", ("ojos abiertos",)),
    ("balón blando", ("balón blando", "balón suave")),
    ("sin salto para menores", ("sin salto",)),
)


def conceptos_ausentes(texto: str) -> tuple[str, ...]:
    """Conceptos de `CONCEPTOS_CABECEO` que `texto` no cubre.

    Un concepto se considera cubierto cuando el texto normalizado contiene
    cualquiera de sus sinonimos. Devuelve los nombres de los conceptos ausentes
    en el orden de la tabla, para que el mensaje de fallo sea estable.
    """
    normalizado: str = normalizar_lexico(texto)
    ausentes: list[str] = []
    for concepto, sinonimos in CONCEPTOS_CABECEO:
        cubierto: bool = any(
            normalizar_lexico(sinonimo) in normalizado for sinonimo in sinonimos
        )
        if not cubierto:
            ausentes.append(concepto)
    return tuple(ausentes)


def validar_advertencia(d: DiagramaPostura) -> None:
    """Valida la Advertencia_Cabeceo de `d` (criterios 20.1 a 20.3, 20.5).

    * La entrada `cabeceo-frente` **debe** declararla; ninguna otra puede.
    * El texto debe tener `MINIMO_ADVERTENCIA` caracteres o mas.
    * Debe cubrir los siete conceptos; el mensaje nombra el concepto ausente.

    Todo fallo es `ErrorAsset(E_ASSET_INVALIDO)`; ningun `assert`.
    """
    exige: bool = d.id == "cabeceo-frente"
    if not exige:
        if d.advertencia is not None:
            raise ErrorAsset(
                f"{d.id}: solo cabeceo-frente declara Advertencia_Cabeceo",
                detalle={"id": d.id},
                codigo=E_ASSET_INVALIDO,
            )
        return

    texto: str | None = d.advertencia
    if texto is None:
        raise ErrorAsset(
            f"{d.id}: falta la Advertencia_Cabeceo obligatoria",
            detalle={"id": d.id},
            codigo=E_ASSET_INVALIDO,
        )
    if len(texto) < MINIMO_ADVERTENCIA:
        raise ErrorAsset(
            f"{d.id}: la Advertencia_Cabeceo tiene {len(texto)} caracteres y "
            f"exige {MINIMO_ADVERTENCIA} o mas; conceptos ausentes: "
            f"{conceptos_ausentes(texto)}",
            detalle={"id": d.id, "longitud": len(texto)},
            codigo=E_ASSET_INVALIDO,
        )
    ausentes: tuple[str, ...] = conceptos_ausentes(texto)
    if ausentes:
        raise ErrorAsset(
            f"{d.id}: la Advertencia_Cabeceo no nombra {ausentes[0]!r}",
            detalle={"id": d.id, "ausentes": ausentes},
            codigo=E_ASSET_INVALIDO,
        )


# --------------------------------------------------------------------------- #
# Consultas del catalogo
# --------------------------------------------------------------------------- #

#: Orden declarado de las ocho entradas (criterios 2.1 y 2.2). Se compara contra
#: `IDS`, que sale del catalogo: si alguien reordena o renombra una entrada, el
#: Validador_Catalogo lo nombra en vez de dejar pasar el cambio.
ORDEN_CATALOGO: tuple[str, ...] = (
    "anatomia-base",
    "tiro-empeine",
    "pase-interior",
    "control-balon",
    "conduccion",
    "potencia-carrera",
    "cabeceo-frente",
    "pase-largo-empeine",
)

#: Fundamento declarado por entrada (criterio 2.8). `None` solo en el vocabulario.
FUNDAMENTO_ESPERADO: dict[str, str | None] = {
    "anatomia-base": None,
    "tiro-empeine": "golpeo",
    "pase-interior": "pase",
    "control-balon": "control-conduccion",
    "conduccion": "control-conduccion",
    "potencia-carrera": "golpeo",
    "cabeceo-frente": "cabeceo",
    "pase-largo-empeine": "pase",
}

#: Postura equivalente de `figuras.FIGURAS` por entrada (criterios 2.9 y 2.10).
POSTURA_ESPERADA: dict[str, str | None] = {
    "anatomia-base": None,
    "tiro-empeine": "tiro-potencia-empeine",
    "pase-interior": "pase-corto-interior",
    "control-balon": "control-orientado",
    "conduccion": "conduccion",
    "potencia-carrera": "tiro-potencia-empeine",
    "cabeceo-frente": None,
    "pase-largo-empeine": "pase-largo-empeine",
}

#: Entradas sin postura equivalente (criterio 2.10).
SIN_POSTURA: frozenset[str] = frozenset({"anatomia-base", "cabeceo-frente"})

#: Unica entrada del catalogo con Girable verdadero (criterio 22.5).
GIRABLE_UNICO: str = "anatomia-base"

#: Superficies de contacto que un texto alternativo de gesto debe nombrar
#: (criterio 2.5). Todas pertenecen al vocabulario anatomico cerrado.
SUPERFICIES_CONTACTO: tuple[str, ...] = (
    "empeine",
    "parte interna",
    "parte externa",
    "planta",
    "frente",
)

#: Elementos de postura que un texto alternativo de gesto debe nombrar, al menos
#: dos de los cuatro (criterio 2.5).
ELEMENTOS_POSTURA: tuple[str, ...] = ("pie de apoyo", "torso", "brazos", "mirada")

#: Etiqueta_Anatomica minimas que debe nombrar el `alt` de `anatomia-base`
#: (criterio 2.6).
MINIMO_ETIQUETAS_EN_ALT: int = 6


def ruta_relativa(d: DiagramaPostura) -> str:
    """Ruta relativa del Archivo_Diagrama, tal como viaja al HTML (criterio 1.1)."""
    return f"{DIR_ASSETS}/{d.archivo}"


def ruta_aceptable(ruta: str) -> bool:
    """Validador_Rutas: **unica** funcion que decide si `ruta` es publicable.

    Es el punto por el que pasa toda ruta de Asset_Local antes de emitirse en un
    `<img>` o de copiarse al directorio de publicacion (Requisito 30), de modo
    que anadir un formato sea cambiar `EXTENSIONES_PERMITIDAS` y nada mas.

    Acepta (devolviendo `True`) cuando las tres condiciones se cumplen:

    1. la ruta empieza por `assets/` (criterio 30.2);
    2. no contiene el segmento `..` (criterio 30.4);
    3. su extension **en minusculas** pertenece a `EXTENSIONES_PERMITIDAS`
       (criterios 30.1, 30.5 y 30.6).

    Rechaza con `ErrorAsset(E_ASSET_INVALIDO)`, no devolviendo `False`: una ruta
    mala es un fallo de build, no un caso a ignorar en silencio. El mensaje
    nombra la ruta cuando el problema es el prefijo o el `..`, y nombra la
    extension cuando el problema es el formato, que es lo que piden los
    criterios 30.3, 30.4 y 30.5. Nunca usa `assert`.
    """
    if not isinstance(ruta, str) or not ruta:
        raise ErrorAsset(
            "el Validador_Rutas exige una ruta no vacia, y recibio "
            f"{ruta!r}",
            detalle={"ruta": ruta},
            codigo=E_ASSET_INVALIDO,
        )

    normalizada: str = ruta.replace("\\", "/")

    for prefijo in PREFIJOS_RECHAZADOS:
        if normalizada.lower().startswith(prefijo):
            raise ErrorAsset(
                f"ruta de asset rechazada: {ruta!r} empieza por {prefijo!r} y "
                "provocaria una peticion de red o una ruta absoluta",
                detalle={"ruta": ruta, "prefijo": prefijo},
                codigo=E_ASSET_INVALIDO,
            )

    if SEGMENTO_ASCENDENTE in normalizada.split("/"):
        raise ErrorAsset(
            f"ruta de asset rechazada: {ruta!r} contiene el segmento "
            f"{SEGMENTO_ASCENDENTE!r}, que se sale del directorio de assets",
            detalle={"ruta": ruta, "segmento": SEGMENTO_ASCENDENTE},
            codigo=E_ASSET_INVALIDO,
        )

    if not normalizada.startswith(PREFIJO_ASSETS):
        raise ErrorAsset(
            f"ruta de asset rechazada: {ruta!r} no empieza por "
            f"{PREFIJO_ASSETS!r}",
            detalle={"ruta": ruta, "prefijo_exigido": PREFIJO_ASSETS},
            codigo=E_ASSET_INVALIDO,
        )

    extension: str = os.path.splitext(normalizada)[1].lower()
    if extension not in EXTENSIONES_PERMITIDAS:
        raise ErrorAsset(
            f"ruta de asset rechazada: la extension {extension!r} no pertenece "
            f"a {EXTENSIONES_PERMITIDAS}",
            detalle={"ruta": ruta, "extension": extension},
            codigo=E_ASSET_INVALIDO,
        )

    return True


def _raiz_proyecto() -> str:
    """Ruta absoluta a `guia-sub17/` (dos niveles sobre este modulo)."""
    aqui: str = os.path.dirname(os.path.abspath(__file__))  # .../src/guia
    src: str = os.path.dirname(aqui)  # .../src
    return os.path.dirname(src)  # .../guia-sub17


def ruta_fuente(d: DiagramaPostura) -> str:
    """Ruta absoluta del Archivo_Diagrama dentro del repositorio."""
    partes: list[str] = DIR_ASSETS.split("/")
    return os.path.join(_raiz_proyecto(), *partes, d.archivo)


def presentes() -> frozenset[str]:
    """Rutas relativas de los Archivo_Diagrama que existen de verdad.

    Solo mira los archivos **declarados** en el catalogo (criterio 5.14) y solo
    toca el sistema de archivos local: cero peticiones de red (criterio 1.7). Con
    el directorio `assets/img/tecnica/` vacio o inexistente devuelve el conjunto
    vacio, y las ocho entradas se rinden con el Generador_SVG.
    """
    halladas: list[str] = []
    for diagrama in CATALOGO:
        if os.path.isfile(ruta_fuente(diagrama)):
            halladas.append(ruta_relativa(diagrama))
    return frozenset(halladas)


def modo_render(d: DiagramaPostura, presentes_: frozenset[str]) -> str:
    """Modo de render efectivo de `d`: `archivo` si esta presente, `svg` si no.

    Es la unica funcion que decide entre los dos modos (criterios 5.3 y 5.4), de
    modo que las dimensiones emitidas y el contenido grafico no puedan discrepar.
    """
    if ruta_relativa(d) in presentes_:
        return MODO_ARCHIVO
    return MODO_SVG


def dimensiones(d: DiagramaPostura, modo: str) -> tuple[int, int]:
    """Dimensiones `(ancho, alto)` declaradas para `modo` (criterios 4.3 y 4.8)."""
    if modo == MODO_ARCHIVO:
        return (d.ancho_archivo, d.alto_archivo)
    if modo == MODO_SVG:
        return (d.ancho_svg, d.alto_svg)
    raise ErrorAsset(
        f"{d.id}: modo de render desconocido: {modo!r}",
        detalle={"id": d.id, "modo": modo},
    )


def por_fundamento(
    f: str, *, catalogo: tuple[DiagramaPostura, ...] | None = None
) -> tuple[DiagramaPostura, ...]:
    """Entradas del catalogo que declaran el Fundamento `f`, en orden.

    Con un Fundamento ajeno al conjunto cerrado devuelve la tupla vacia: quien
    compone las secciones emite solo los cuatro bloques declarados y registra el
    ajeno en el reporte (criterio 3.9), en vez de reventar el build.

    `catalogo` permite consultar un catalogo distinto del declarado. Se usa para
    ejercitar el criterio 3.9 con un Fundamento ajeno inyectado, sin mutar el
    modulo; por defecto es el `CATALOGO` real.
    """
    entradas: tuple[DiagramaPostura, ...] = (
        CATALOGO if catalogo is None else catalogo
    )
    return tuple(d for d in entradas if d.fundamento == f)


def fundamentos_omitidos(
    catalogo: tuple[DiagramaPostura, ...] | None = None,
) -> tuple[str, ...]:
    """Fundamento declarados que no pertenecen al conjunto cerrado (criterio 3.9).

    Devuelve cada valor ajeno **una sola vez**, en el orden en que aparece en el
    catalogo, para que el reporte del build lo enumere sin repetir. El Fundamento
    nulo de `anatomia-base` no cuenta como ajeno: es el vocabulario, no un
    fundamento.
    """
    entradas: tuple[DiagramaPostura, ...] = (
        CATALOGO if catalogo is None else catalogo
    )
    permitidos: frozenset[str] = frozenset(FUNDAMENTOS)
    ajenos: list[str] = []
    for diagrama in entradas:
        fundamento: str | None = diagrama.fundamento
        if fundamento is None or fundamento in permitidos:
            continue
        if fundamento not in ajenos:
            ajenos.append(fundamento)
    return tuple(ajenos)


def por_id(id_: str) -> DiagramaPostura:
    """Entrada del catalogo con ese identificador."""
    for diagrama in CATALOGO:
        if diagrama.id == id_:
            return diagrama
    raise ErrorAsset(
        f"identificador fuera del Catalogo_Diagramas: {id_!r}",
        detalle={"id": id_},
    )


# --------------------------------------------------------------------------- #
# Validador_Catalogo
# --------------------------------------------------------------------------- #


def _validar_archivo(d: DiagramaPostura) -> None:
    """Nombre, extension y ubicacion del Archivo_Diagrama (criterio 2.3)."""
    extension: str = os.path.splitext(d.archivo)[1]
    if extension not in EXTENSIONES:
        raise ErrorAsset(
            f"{d.id}: extension {extension!r} fuera de {EXTENSIONES}",
            detalle={"id": d.id, "extension": extension},
        )
    if d.archivo != f"{d.id}{extension}":
        raise ErrorAsset(
            f"{d.id}: el Archivo_Diagrama se llama {d.archivo!r} y debe "
            f"llamarse {d.id}{extension!r}",
            detalle={"id": d.id, "archivo": d.archivo},
        )
    relativa: str = ruta_relativa(d)
    if not relativa.startswith(f"{DIR_ASSETS}/"):
        raise ErrorAsset(
            f"{d.id}: el Archivo_Diagrama debe vivir en {DIR_ASSETS}/",
            detalle={"id": d.id, "ruta": relativa},
        )


def _validar_dimensiones(d: DiagramaPostura) -> None:
    """Ancho en (0, 1200] y alto positivo en los dos modos (criterio 2.4)."""
    for modo in (MODO_ARCHIVO, MODO_SVG):
        ancho, alto = dimensiones(d, modo)
        if not 0 < ancho <= ANCHO_MAXIMO:
            raise ErrorAsset(
                f"{d.id}: ancho {ancho} del modo {modo} fuera de "
                f"(0, {ANCHO_MAXIMO}]",
                detalle={"id": d.id, "modo": modo, "ancho": ancho},
            )
        if alto <= 0:
            raise ErrorAsset(
                f"{d.id}: alto {alto} del modo {modo} no es positivo",
                detalle={"id": d.id, "modo": modo, "alto": alto},
            )


def _validar_alt(d: DiagramaPostura) -> None:
    """Texto alternativo descriptivo real (criterios 2.5 y 2.6)."""
    if len(d.alt) < MINIMO_ALT:
        raise ErrorAsset(
            f"{d.id}: el texto alternativo tiene {len(d.alt)} caracteres y "
            f"exige {MINIMO_ALT} o mas",
            detalle={"id": d.id, "longitud": len(d.alt)},
        )
    normalizado: str = normalizar_lexico(d.alt)

    if d.id == ANCLA_ANATOMIA:
        nombradas: int = sum(
            1
            for etiqueta in ETIQUETAS_ANATOMIA
            if normalizar_lexico(etiqueta) in normalizado
        )
        if nombradas < MINIMO_ETIQUETAS_EN_ALT:
            raise ErrorAsset(
                f"{d.id}: su texto alternativo nombra {nombradas} etiquetas y "
                f"exige {MINIMO_ETIQUETAS_EN_ALT} o mas",
                detalle={"id": d.id, "etiquetas_nombradas": nombradas},
            )
        return

    superficies: tuple[str, ...] = tuple(
        s
        for s in SUPERFICIES_CONTACTO
        if normalizar_lexico(s) in normalizado
    )
    if not superficies:
        raise ErrorAsset(
            f"{d.id}: su texto alternativo no nombra ninguna superficie de "
            f"contacto de {SUPERFICIES_CONTACTO}",
            detalle={"id": d.id},
        )
    elementos: tuple[str, ...] = tuple(
        e for e in ELEMENTOS_POSTURA if normalizar_lexico(e) in normalizado
    )
    if len(elementos) < 2:
        raise ErrorAsset(
            f"{d.id}: su texto alternativo nombra {len(elementos)} elementos de "
            f"postura y exige al menos dos de {ELEMENTOS_POSTURA}",
            detalle={"id": d.id, "elementos": elementos},
        )


def _validar_pasos(d: DiagramaPostura) -> None:
    """Cinco pasos en el orden fijo, largos y con verbo permitido (2.7, 17.3)."""
    if len(d.pasos) != PASOS_POR_ENTRADA:
        raise ErrorAsset(
            f"{d.id}: declara {len(d.pasos)} pasos y exige "
            f"{PASOS_POR_ENTRADA} en el orden {ORDEN_PASOS}",
            detalle={"id": d.id, "pasos": len(d.pasos)},
        )
    for indice, paso in enumerate(d.pasos):
        nombre: str = ORDEN_PASOS[indice]
        if len(paso) < MINIMO_PASO:
            raise ErrorAsset(
                f"{d.id}: el paso {indice + 1} ({nombre}) tiene {len(paso)} "
                f"caracteres y exige {MINIMO_PASO} o mas",
                detalle={"id": d.id, "paso": indice + 1, "nombre": nombre},
            )
        if not empieza_con_verbo_permitido(paso):
            raise ErrorAsset(
                f"{d.id}: el paso {indice + 1} ({nombre}) empieza por "
                f"{verbo_inicial(paso)!r}, que no es un verbo permitido",
                detalle={
                    "id": d.id,
                    "paso": indice + 1,
                    "verbo": verbo_inicial(paso),
                },
            )


def _validar_fundamento(d: DiagramaPostura) -> None:
    """Fundamento del conjunto cerrado, nulo solo en el vocabulario (2.8)."""
    esperado: str | None = FUNDAMENTO_ESPERADO.get(d.id, "")
    if esperado == "":
        raise ErrorAsset(
            f"{d.id}: sin Fundamento declarado en la tabla del diseno",
            detalle={"id": d.id},
        )
    if d.fundamento is None:
        if d.id != ANCLA_ANATOMIA:
            raise ErrorAsset(
                f"{d.id}: solo {ANCLA_ANATOMIA} puede no declarar Fundamento",
                detalle={"id": d.id},
            )
        return
    if d.fundamento not in FUNDAMENTOS:
        raise ErrorAsset(
            f"{d.id}: Fundamento {d.fundamento!r} fuera del conjunto cerrado "
            f"{FUNDAMENTOS}",
            detalle={"id": d.id, "fundamento": d.fundamento},
        )
    if d.fundamento != esperado:
        raise ErrorAsset(
            f"{d.id}: Fundamento {d.fundamento!r} en vez de {esperado!r}",
            detalle={"id": d.id, "fundamento": d.fundamento},
        )


def _validar_postura(d: DiagramaPostura) -> None:
    """Postura equivalente real de `figuras.FIGURAS` (criterios 2.9 y 2.10)."""
    if d.postura_id is None:
        if d.id not in SIN_POSTURA:
            raise ErrorAsset(
                f"{d.id}: solo {tuple(sorted(SIN_POSTURA))} pueden declararse "
                "sin postura equivalente",
                detalle={"id": d.id},
            )
        return
    if d.id in SIN_POSTURA:
        raise ErrorAsset(
            f"{d.id}: no debe declarar postura equivalente",
            detalle={"id": d.id, "postura_id": d.postura_id},
        )
    if d.postura_id not in figuras.FIGURAS:
        raise ErrorAsset(
            f"{d.id}: postura {d.postura_id!r} inexistente en figuras.FIGURAS",
            detalle={"id": d.id, "postura_id": d.postura_id},
        )
    if d.postura_id != POSTURA_ESPERADA[d.id]:
        raise ErrorAsset(
            f"{d.id}: postura {d.postura_id!r} en vez de "
            f"{POSTURA_ESPERADA[d.id]!r}",
            detalle={"id": d.id, "postura_id": d.postura_id},
        )


def _validar_fases(d: DiagramaPostura) -> None:
    """Fase_Numerada de 1 a n, sin huecos y sin repetir (criterio 14.12)."""
    numeros: tuple[int, ...] = tuple(f.numero for f in d.fases)
    esperados: tuple[int, ...] = tuple(range(1, len(d.fases) + 1))
    if numeros != esperados:
        raise ErrorAsset(
            f"{d.id}: sus Fase_Numerada son {numeros} y deben ser {esperados}",
            detalle={"id": d.id, "numeros": numeros},
        )
    for fase in d.fases:
        if len(fase.texto) < MINIMO_PASO:
            raise ErrorAsset(
                f"{d.id}: la fase {fase.numero} tiene {len(fase.texto)} "
                f"caracteres y exige {MINIMO_PASO} o mas",
                detalle={"id": d.id, "fase": fase.numero},
            )


def _validar_girable(d: DiagramaPostura) -> None:
    """Girable verdadero solo en `anatomia-base` (criterio 22.5)."""
    esperado: bool = d.id == GIRABLE_UNICO
    if d.girable is not esperado:
        raise ErrorAsset(
            f"{d.id}: declara girable={d.girable!r} y debe declarar "
            f"{esperado!r}: la unica Figura_Girable del catalogo es "
            f"{GIRABLE_UNICO!r}",
            detalle={"id": d.id, "girable": d.girable, "esperado": esperado},
            codigo=E_ASSET_INVALIDO,
        )


def girables() -> tuple[DiagramaPostura, ...]:
    """Entradas del catalogo marcadas como Figura_Girable, en orden."""
    return tuple(d for d in CATALOGO if d.girable)


def _validar_pase_largo(d: DiagramaPostura) -> None:
    """`pase-largo-empeine` declara el pase elevado a distancia (criterio 2.12)."""
    if d.id != "pase-largo-empeine":
        return
    for campo, texto in (("titulo", d.titulo), ("alt", d.alt)):
        normalizado: str = normalizar_lexico(texto)
        if "elevado" not in normalizado or "distancia" not in normalizado:
            raise ErrorAsset(
                f"{d.id}: su {campo} debe declarar el pase elevado a distancia",
                detalle={"id": d.id, "campo": campo},
            )


def validar_catalogo() -> None:
    """Comprueba todos los invariantes del Catalogo_Diagramas.

    Orden y identificadores, Archivo_Diagrama, dimensiones por modo, texto
    alternativo, pasos, Fundamento, postura equivalente, Requiere_Archivo,
    Etiqueta_Anatomica, Fase_Numerada, Advertencia_Cabeceo, tono del texto y la
    declaracion del pase elevado a distancia.

    Cada fallo es un `ErrorAsset` que nombra la entrada y el invariante roto;
    ningun `assert`, para que `python -O` no borre nada (criterio 13.4).
    """
    if IDS != ORDEN_CATALOGO:
        raise ErrorAsset(
            f"el catalogo declara {IDS} y el orden exigido es {ORDEN_CATALOGO}",
            detalle={"ids": IDS},
        )
    if EXTENSIONES_PERMITIDAS != (".webp", ".svg", ".png", ".avif"):
        raise ErrorAsset(
            "Extensiones_Permitidas debe ser exactamente "
            f"('.webp', '.svg', '.png', '.avif') y es {EXTENSIONES_PERMITIDAS}",
            detalle={"extensiones": EXTENSIONES_PERMITIDAS},
            codigo=E_ASSET_INVALIDO,
        )
    if CATALOGO[0].id != ANCLA_ANATOMIA:
        raise ErrorAsset(
            f"la primera entrada debe ser {ANCLA_ANATOMIA}, no "
            f"{CATALOGO[0].id!r}",
            detalle={"primera": CATALOGO[0].id},
        )

    validar_vocabulario()

    for diagrama in CATALOGO:
        if not diagrama.titulo:
            raise ErrorAsset(
                f"{diagrama.id}: sin titulo", detalle={"id": diagrama.id}
            )
        if diagrama.requiere_archivo:
            raise ErrorAsset(
                f"{diagrama.id}: Requiere_Archivo debe ser falso en las ocho "
                "entradas actuales",
                detalle={"id": diagrama.id},
            )
        _validar_girable(diagrama)
        ruta_aceptable(ruta_relativa(diagrama))
        if not diagrama.error_frecuente:
            raise ErrorAsset(
                f"{diagrama.id}: sin error frecuente declarado",
                detalle={"id": diagrama.id},
            )
        if not diagrama.etiquetas:
            raise ErrorAsset(
                f"{diagrama.id}: sin ninguna Etiqueta_Anatomica",
                detalle={"id": diagrama.id},
            )
        _validar_archivo(diagrama)
        _validar_dimensiones(diagrama)
        _validar_alt(diagrama)
        _validar_pasos(diagrama)
        _validar_fundamento(diagrama)
        _validar_postura(diagrama)
        _validar_fases(diagrama)
        _validar_pase_largo(diagrama)
        validar_advertencia(diagrama)
        for texto in textos_de(diagrama):
            validar_lexico(diagrama.id, texto)


# --------------------------------------------------------------------------- #
# Render del bloque de un Diagrama_Postura (Requisitos 3, 4 y 5)
# --------------------------------------------------------------------------- #

#: Clases CSS del bloque de un Diagrama_Postura. Se declaran como constantes
#: porque las comparten el render y `bloque_css()`: un solo sitio donde cambiar
#: un nombre de clase.
CLASE_BLOQUE: str = "diagrama-postura"
CLASE_MARCO: str = "diagrama-marco"
CLASE_AVISO: str = "diagrama-aviso"
CLASE_PASOS: str = "diagrama-pasos"
CLASE_FASES: str = "diagrama-fases"
CLASE_ERROR: str = "diagrama-error"

#: Propiedad personalizada en linea con la relacion de aspecto del contenedor.
#: Viaja en el `style` del `<article>` para que el CSS declare **una sola** regla
#: `aspect-ratio:var(--relacion)` y no haya ningun ancho en pixeles (criterio 4.5).
VARIABLE_RELACION: str = "--relacion"

#: Rotulo del error frecuente. Es texto visible, en segunda persona y en femenino.
ETIQUETA_ERROR: str = "Error frecuente: "

#: Prefijo del `id` del `<article>` de cada bloque. No es el identificador a
#: secas para no chocar con el ancla de la seccion `anatomia-base` (criterio 3.2).
PREFIJO_ID_BLOQUE: str = "diagrama-"

#: Valores del atributo `loading` de un `<img>` (criterios 4.1 y 4.2).
CARGA_INMEDIATA: str = "eager"
CARGA_DIFERIDA: str = "lazy"


def id_bloque(d: DiagramaPostura) -> str:
    """`id` del `<article>` del bloque de `d`, destino del cierre del visor."""
    return f"{PREFIJO_ID_BLOQUE}{d.id}"


def relacion_aspecto(d: DiagramaPostura, modo: str) -> str:
    """Relacion de aspecto del contenedor para `modo`, como `"<ancho>/<alto>"`."""
    ancho, alto = dimensiones(d, modo)
    return f"{ancho}/{alto}"


def render_bloque(
    d: DiagramaPostura,
    partes: list[str],
    *,
    presentes: frozenset[str],
    primero: bool,
) -> None:
    """Emite el bloque completo de un Diagrama_Postura en `partes`.

    Render **hibrido** (criterios 5.3 a 5.5): con el Archivo_Diagrama presente
    emite un `<img>` a su ruta relativa; si falta, emite el `<svg>` en linea del
    Generador_SVG. Siempre hay exactamente un contenido grafico, y sus atributos
    `width` y `height` son los del **modo de render efectivo** (criterios 4.3 y
    4.8), aunque los dos modos declaren dimensiones distintas.

    `primero` dice si este seria el **primer** `<img>` del documento; solo ese
    lleva `loading="eager"` y los demas `loading="lazy"` (criterios 4.1 y 4.2). El
    "primero" depende del subconjunto presente y del orden del documento, que no
    es el del catalogo, asi que lo decide quien compone las secciones.

    Orden de emision, fijo (criterios 3.4 a 3.6, 19.4 y 20.4): titulo en `<h3>`,
    `<figure>` con el contenido grafico, Advertencia_Cabeceo, pasos numerados,
    Fase_Numerada y error frecuente. Todo texto pasa por `build_html._esc`.

    Los dos imports son diferidos a proposito: `svg_postura` importa este modulo,
    asi que un import de nivel de modulo seria un ciclo, y `build_html` se trae
    aqui por simetria para que el catalogo siga siendo importable por si solo.
    """
    from . import build_html, svg_postura

    _esc = build_html._esc
    modo: str = modo_render(d, presentes)
    ancho, alto = dimensiones(d, modo)

    partes.append(
        f'<article class="{CLASE_BLOQUE}" id="{_esc(id_bloque(d))}" '
        f'data-diagrama="{_esc(d.id)}" '
        f'style="{VARIABLE_RELACION}:{ancho}/{alto}">'
    )
    partes.append(f"<h3>{_esc(d.titulo)}</h3>")
    partes.append(f'<figure class="{CLASE_MARCO}">')
    if modo == MODO_ARCHIVO:
        ruta: str = ruta_relativa(d)
        # Validador_Rutas: ninguna ruta llega al `<img>` sin pasar por aqui
        # (criterio 30.2). Lanza `ErrorAsset` si la ruta no es publicable.
        ruta_aceptable(ruta)
        carga: str = CARGA_INMEDIATA if primero else CARGA_DIFERIDA
        partes.append(
            f'<img src="{_esc(ruta)}" alt="{_esc(d.alt)}" '
            f'width="{ancho}" height="{alto}" '
            f'loading="{carga}" decoding="async">'
        )
    else:
        partes.append(svg_postura.svg_diagrama(d))
    partes.append("</figure>")

    if d.advertencia is not None:
        # La advertencia va **antes** de los pasos y es texto del HTML, sin
        # depender del Script_Unico (criterios 20.4 y 20.6).
        validar_advertencia(d)
        partes.append(f'<p class="{CLASE_AVISO}">{_esc(d.advertencia)}</p>')

    partes.append(f'<ol class="{CLASE_PASOS}">')
    for paso in d.pasos:
        partes.append(f"<li>{_esc(paso)}</li>")
    partes.append("</ol>")

    if d.fases:
        partes.append(f'<ol class="{CLASE_FASES}">')
        for fase in d.fases:
            partes.append(f'<li value="{fase.numero}">{_esc(fase.texto)}</li>')
        partes.append("</ol>")

    partes.append(
        f'<p class="{CLASE_ERROR}">{_esc(ETIQUETA_ERROR)}'
        f"{_esc(d.error_frecuente)}</p>"
    )
    partes.append("</article>")


# --------------------------------------------------------------------------- #
# Bloque_Creditos (Requisito 18)
# --------------------------------------------------------------------------- #

#: Clases CSS del Bloque_Creditos.
CLASE_CREDITOS: str = "creditos-imagenes"
CLASE_CREDITO: str = "credito-imagen"

#: Marca que sustituye a un campo de credito ausente (criterio 18.8).
MARCA_PENDIENTE: str = "dato pendiente"

#: Rotulo visible de cada campo, en el orden del criterio 18.3.
ROTULOS_CREDITO: tuple[tuple[str, str], ...] = (
    ("autor", "Autoría"),
    ("fuente", "Fuente"),
    ("licencia", "Licencia"),
    ("enlace", "Enlace"),
)

#: Nombres de los cuatro campos, derivados de los rotulos para que no haya dos
#: listas capaces de desincronizarse.
CAMPOS_CREDITO: tuple[str, ...] = tuple(campo for campo, _ in ROTULOS_CREDITO)

#: Titulo del Bloque_Creditos y su linea de apoyo.
TITULO_CREDITOS: str = "Créditos y licencias de las imágenes"
LEDE_CREDITOS: str = (
    "Cada dibujo de esta guía se genera dentro del propio proyecto. Aquí queda "
    "anotada la autoría y la licencia de todos, y los datos que aún faltan por "
    "completar."
)


def campo_de_credito(credito: Credito, campo: str) -> str | None:
    """Valor de `campo` en `credito`, o `None` cuando esta ausente.

    Trata la cadena vacia como ausencia: un campo con "" no es un dato, es un
    hueco, y el criterio 18.8 pide marcarlo igual que el `None`.
    """
    if campo not in CAMPOS_CREDITO:
        raise ErrorAsset(
            f"campo de credito desconocido: {campo!r}; los campos son "
            f"{CAMPOS_CREDITO}",
            detalle={"campo": campo},
            codigo=E_ASSET_INVALIDO,
        )
    valor: str | None = getattr(credito, campo)
    if valor is None or not valor.strip():
        return None
    return valor


def campos_ausentes_de(credito: Credito) -> tuple[str, ...]:
    """Campos ausentes de `credito`, en el orden del criterio 18.3."""
    return tuple(
        campo
        for campo in CAMPOS_CREDITO
        if campo_de_credito(credito, campo) is None
    )


def campos_pendientes(
    catalogo: tuple[DiagramaPostura, ...] | None = None,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Pares `(id, campos_ausentes)` de las entradas incompletas (criterio 18.9).

    Alimenta el reporte del Orquestador_Build: el build **termina** aunque haya
    campos pendientes, solo quedan enumerados.
    """
    entradas: tuple[DiagramaPostura, ...] = (
        CATALOGO if catalogo is None else catalogo
    )
    pendientes: list[tuple[str, tuple[str, ...]]] = []
    for diagrama in entradas:
        ausentes: tuple[str, ...] = campos_ausentes_de(diagrama.credito)
        if ausentes:
            pendientes.append((diagrama.id, ausentes))
    return tuple(pendientes)


def render_creditos(
    partes: list[str],
    *,
    presentes: frozenset[str],
    catalogo: tuple[DiagramaPostura, ...] | None = None,
) -> None:
    """Emite el Bloque_Creditos completo (criterios 18.1 a 18.6 y 18.8).

    Una entrada por Diagrama_Postura, cada una con autoría, fuente, licencia y
    enlace. El enlace es **texto visible**: nunca un `<a href>` ni ningun atributo
    que provoque una peticion de red (criterio 18.5). Los campos ausentes se
    emiten con la marca `dato pendiente` (criterio 18.8). El bloque existe aunque
    las ocho entradas se rindan con el Generador_SVG (criterio 18.6): `presentes`
    solo decide el rotulo del modo, no si el bloque se emite.
    """
    from . import build_html

    _esc = build_html._esc
    entradas: tuple[DiagramaPostura, ...] = (
        CATALOGO if catalogo is None else catalogo
    )

    partes.append(f'<h2 id="{_esc(ANCLA_CREDITOS)}">{_esc(TITULO_CREDITOS)}</h2>')
    partes.append(f"<p>{_esc(LEDE_CREDITOS)}</p>")
    partes.append(f'<ul class="{CLASE_CREDITOS}">')
    for diagrama in entradas:
        modo: str = modo_render(diagrama, presentes)
        partes.append(
            f'<li class="{CLASE_CREDITO}" '
            f'data-credito="{_esc(diagrama.id)}" '
            f'data-modo="{_esc(modo)}">'
        )
        partes.append(f"<b>{_esc(diagrama.titulo)}</b>")
        partes.append("<dl>")
        for campo, rotulo in ROTULOS_CREDITO:
            valor: str | None = campo_de_credito(diagrama.credito, campo)
            texto: str = MARCA_PENDIENTE if valor is None else valor
            partes.append(f"<dt>{_esc(rotulo)}</dt>")
            partes.append(f'<dd data-campo="{_esc(campo)}">{_esc(texto)}</dd>')
        partes.append("</dl>")
        partes.append("</li>")
    partes.append("</ul>")


# --------------------------------------------------------------------------- #
# Bloque CSS de los diagramas (criterios 4.5, 4.6, 4.7 y 15.3)
# --------------------------------------------------------------------------- #

#: Relacion de aspecto por defecto del marco, cuando el `style` en linea no
#: declara `--relacion` (criterio 4.5).
RELACION_POR_DEFECTO: str = "3/4"

#: Alto minimo del marco en pantallas angostas, en pixeles (criterio 4.6). Es el
#: unico valor en pixeles del bloque, y `min-height` no lo toca la regla que
#: acota los anchos fijos a 360.
ALTO_MINIMO_ANGOSTO: int = 320

#: Corte de pantalla angosta expresado en `rem`, equivalente a 767 px con la raiz
#: de 16 px: `47.9375rem`. Se declara en `rem` para que respete el tamano de
#: fuente de la usuaria (criterio 15.3).
CORTE_ANGOSTO_REM: str = "47.9375rem"

#: Tokens de la Paleta_Guia que usa el bloque CSS. `bloque_css()` comprueba que
#: los dos sigan perteneciendo a `paleta.PALETA_GUIA`, de modo que renombrar un
#: token no deje una referencia muerta en la Hoja_Estilo.
TOKEN_CORAL: str = "--coral-alerta"
TOKEN_BLANCO: str = "--blanco-suave"


def bloque_css() -> str:
    """CSS de los bloques de Diagrama_Postura y de su Visor_Ampliado.

    Reglas del criterio 4.5 a 4.7 y 15.3, y nada mas:

    * `.diagrama-marco` fija la relacion de aspecto con `aspect-ratio` y recorta
      con `overflow:hidden`, asi que el texto no salta al cargar la imagen.
    * el contenido grafico (`img` y `svg`) ocupa el 100 % del ancho, con
      `height:auto`, `max-width:100%` y `object-fit:cover`.
    * bajo `47.9375rem` el marco reserva `320px` de alto minimo.

    El Visor_Ampliado ya **no** se despliega desde aqui. Antes este bloque
    declaraba `#anatomia-base-ampliada{min-height:0;}` y su variante `:target` a
    `100dvh`, que era todo el "modal" que habia: una seccion del flujo que crecia.
    Ese par de reglas desaparecio porque el overlay modal completo (velo,
    `position:fixed`, barra superior, cuerpo desplazable y lienzo contenido) lo
    declara `build_html.estilo_css()` sobre la clase `.visor-ampliado`, sin
    depender del `id` de ningun diagrama.

    Sin `url(`, sin `http` y sin ningun `width` ni `min-width` en pixeles: los
    unicos pixeles del bloque son `min-height`, que ninguna regla de ancho toca.
    """
    from . import paleta

    for token in (TOKEN_CORAL, TOKEN_BLANCO):
        if token not in paleta.PALETA_GUIA:
            raise ErrorAsset(
                f"el bloque CSS de los diagramas usa el token {token!r}, que no "
                "pertenece a la Paleta_Guia",
                detalle={"token": token},
                codigo=E_ASSET_INVALIDO,
            )

    piezas: list[str] = [
        f".{CLASE_BLOQUE}{{margin:2rem 0;min-width:0;}}",
        f".{CLASE_MARCO}{{margin:0 0 1rem;padding:0;"
        f"aspect-ratio:var({VARIABLE_RELACION},{RELACION_POR_DEFECTO});"
        "overflow:hidden;border-radius:var(--radio);min-width:0;}",
        f".{CLASE_MARCO} img,.{CLASE_MARCO} svg{{display:block;width:100%;"
        "height:auto;max-width:100%;object-fit:cover;}",
        f"@media (max-width: {CORTE_ANGOSTO_REM}){{"
        f".{CLASE_MARCO}{{min-height:{ALTO_MINIMO_ANGOSTO}px;}}}}",
        f".{CLASE_PASOS},.{CLASE_FASES}{{margin:0 0 1rem;padding-left:1.5rem;}}",
        f".{CLASE_AVISO}{{margin:0 0 1rem;padding:0.75rem 1rem;"
        f"border-left:4px solid var({TOKEN_CORAL});"
        f"background:var({TOKEN_BLANCO});}}",
        f".{CLASE_ERROR}{{margin:0;font-weight:600;}}",
        f".{CLASE_CREDITOS}{{list-style:none;padding:0;margin:1.25rem 0;}}",
        f".{CLASE_CREDITO}{{margin:0 0 1rem;}}",
    ]
    return "".join(piezas)


__all__ = [
    "ADVERTENCIA_CABECEO",
    "ALTO_MINIMO_ANGOSTO",
    "ANCHO_MAXIMO",
    "ANCLA_ANATOMIA",
    "ANCLA_CREDITOS",
    "ANCLA_TECNICA",
    "ARTICULACIONES",
    "ARTICULACION_POR_ETIQUETA",
    "CAMPOS_CREDITO",
    "CARGA_DIFERIDA",
    "CARGA_INMEDIATA",
    "CATALOGO",
    "CLASE_AVISO",
    "CLASE_BLOQUE",
    "CLASE_CREDITO",
    "CLASE_CREDITOS",
    "CLASE_ERROR",
    "CLASE_FASES",
    "CLASE_MARCO",
    "CLASE_PASOS",
    "CLUBES_VETADOS",
    "CORTE_ANGOSTO_REM",
    "CONCEPTOS_CABECEO",
    "CONDESCENDIENTES",
    "CREDITO_PROPIO",
    "Credito",
    "DIR_ASSETS",
    "DiagramaPostura",
    "ELEMENTOS_POSTURA",
    "ETIQUETAS_ANATOMIA",
    "ETIQUETAS_DERIVADAS",
    "ETIQUETA_ERROR",
    "EXPRESIONES_PROHIBIDAS",
    "EXTENSIONES",
    "EXTENSIONES_PERMITIDAS",
    "FORMAS_MASCULINAS",
    "GIRABLE_UNICO",
    "FUNDAMENTOS",
    "FUNDAMENTO_ESPERADO",
    "Fase",
    "IDS",
    "LEDE_CREDITOS",
    "MARCA_PENDIENTE",
    "MASCULINO_GENERICO",
    "MINIMO_ADVERTENCIA",
    "MINIMO_ALT",
    "MINIMO_ETIQUETAS_EN_ALT",
    "MINIMO_PASO",
    "MODO_ARCHIVO",
    "MODO_SVG",
    "ORDEN_CATALOGO",
    "ORDEN_PASOS",
    "PASOS_POR_ENTRADA",
    "POSTURA_ESPERADA",
    "PREFIJOS_RECHAZADOS",
    "PREFIJO_ASSETS",
    "PREFIJO_ID_BLOQUE",
    "RELACION_POR_DEFECTO",
    "ROTULOS_CREDITO",
    "SEGMENTO_ASCENDENTE",
    "SIN_POSTURA",
    "SUPERFICIES_CONTACTO",
    "TITULO_CREDITOS",
    "TOKEN_BLANCO",
    "TOKEN_CORAL",
    "VARIABLE_RELACION",
    "VERBOS_PERMITIDOS",
    "articulacion_de",
    "bloque_css",
    "campo_de_credito",
    "campos_ausentes_de",
    "campos_pendientes",
    "conceptos_ausentes",
    "dimensiones",
    "empieza_con_verbo_permitido",
    "fundamentos_omitidos",
    "girables",
    "id_bloque",
    "mensaje_lexico",
    "modo_render",
    "normalizar_lexico",
    "por_fundamento",
    "por_id",
    "presentes",
    "relacion_aspecto",
    "render_bloque",
    "render_creditos",
    "ruta_aceptable",
    "ruta_fuente",
    "ruta_relativa",
    "textos_de",
    "validar_advertencia",
    "validar_catalogo",
    "validar_lexico",
    "validar_vocabulario",
    "verbo_inicial",
    "violaciones_lexicas",
]
