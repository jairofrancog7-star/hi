"""Composicion editorial de una ficha: las nueve zonas (`zonas.py`, tarea 33.4).

Un solo modulo decide **que contenido va en cada zona** de una ficha, para que el
sitio de un archivo (`build_site.py`), el sitio por capitulo y el PDF lean la
misma descomposicion y no se dupliquen reglas. Las nueve zonas, en orden:

1. `encabezado`   numero, titulo corto, categoria, nivel y objetivo en una frase.
2. `visual`       ilustracion de tecnica (postura/golpeo) y diagrama de cancha.
3. `hazlo-asi`    pasos numerados, una instruccion por linea.
4. `puntos-clave` postura, pie de apoyo, contacto, orientacion y ritmo.
5. `errores`      el error y su correccion corta (imagen + rotulo).
6. `dosis`        cuando, duracion, jugadoras, material y meta.
7. `progresion`   fases de dificultad y adaptacion por numero de jugadoras.
8. `medicion`     que se mide, como se registra y cual es la meta.
9. `video`        "Video de ejemplo" + "Ver demostracion" + su codigo QR.

Regla de contenido del proyecto: **no se inventa contenido de entrenamiento**.
Todo lo que estas funciones devuelven sale de dos fuentes que ya existen:

* la Ficha_JSON del `Catalogo_JSON` (`pasos`, `que_mira_la_companera`, `dosis`,
  `cancha`, `media`);
* la ilustracion registrada en `figuras.py` (su `leyenda` y las etiquetas de sus
  items, incluido el panel "ASI NO" con su rotulo `Corrige: ...`).

Cuando una fuente no existe para una ficha concreta, la funcion devuelve una
tupla vacia: **es un resultado legitimo** y quien rinde decide si omite la zona o
pone su linea de encuadre. Ninguna funcion lanza por falta de datos; solo
`ValueError` ante un uso incorrecto de la API (una ficha que no es un mapeo).

Solo libreria estandar; sin `assert` (los borra `python -O`); funciones puras.

_Requirements: 2.4, 2.5, 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

__all__ = [
    "ZONAS",
    "TITULO_HAZLO_ASI",
    "TITULO_PUNTOS_CLAVE",
    "TITULO_ERRORES",
    "TITULO_DOSIS",
    "TITULO_PROGRESION",
    "TITULO_MEDICION",
    "TITULO_VIDEO",
    "ETIQUETA_DEMOSTRACION",
    "ENCUADRE_ERRORES",
    "CAMPOS_DOSIS",
    "pasos_hazlo_asi",
    "puntos_clave",
    "errores_comunes",
    "dosis_chips",
    "progresion",
    "medicion",
    "texto_alternativo",
    "zonas_de_ficha",
]


# --------------------------------------------------------------------------- #
# Nombres de las nueve zonas y rotulos visibles
# --------------------------------------------------------------------------- #

#: Identificadores de las nueve zonas, en el orden de lectura de la ficha. Es la
#: lista que consumen las pruebas mecanicas (`data-zona="..."` por seccion).
ZONAS: tuple[str, ...] = (
    "encabezado",
    "visual",
    "hazlo-asi",
    "puntos-clave",
    "errores",
    "dosis",
    "progresion",
    "medicion",
    "video",
)

#: Rotulos visibles. Van **sin acento** donde el mismo literal viaja al PDF, que
#: codifica en WinAnsi (cp1252); asi las tres superficies dicen lo mismo.
TITULO_HAZLO_ASI: str = "Hazlo asi"
TITULO_PUNTOS_CLAVE: str = "Puntos clave"
TITULO_ERRORES: str = "Errores comunes"
TITULO_DOSIS: str = "Dosis"
TITULO_PROGRESION: str = "Progresion"
TITULO_MEDICION: str = "Medicion"

#: Titulo EXACTO de la zona de video (Req 14.6). No se traduce ni se adorna.
TITULO_VIDEO: str = "Video de ejemplo"

#: Texto EXACTO del boton de video. Sin acento a proposito (WinAnsi).
ETIQUETA_DEMOSTRACION: str = "Ver demostracion"

#: Linea de encuadre de la zona de errores cuando la ficha no trae ni ilustracion
#: ni un punto redactado en negativo. **No es contenido de entrenamiento nuevo**:
#: solo dice donde mirar, para que la zona no quede muda.
ENCUADRE_ERRORES: str = (
    "El error es cualquier punto clave que no se cumple: revisa la lista de "
    "puntos clave con tu companera."
)

#: Claves de la dosis, en orden, con su rotulo visible (chips grandes).
CAMPOS_DOSIS: tuple[tuple[str, str], ...] = (
    ("cuando", "Cuando"),
    ("duracion", "Duracion"),
    ("jugadoras", "Jugadoras"),
    ("material", "Material"),
    ("meta", "Meta"),
)

#: Prefijos con los que el catalogo marca los pasos que NO son instrucciones de
#: ejecucion, sino progresion, metrica o variante por numero de jugadoras.
_PREFIJOS_META: tuple[str, ...] = (
    "progresion",
    "metrica de mejora",
    "variante",
)

#: Marcas de un punto redactado en negativo (un error a evitar).
_MARCAS_NEGATIVO: tuple[str, ...] = ("nunca", "no ", "sin ", "evita", "jamas")

#: Rotulo del panel de error de las ilustraciones de `figuras.py`.
_PANEL_ERROR: str = "ASI NO"

#: Prefijo del rotulo de correccion dentro del panel de error.
_PREFIJO_CORRIGE: str = "Corrige:"

#: Etiquetas anatomicas de la figura: describen el dibujo, no un error concreto,
#: asi que no entran en la lista de errores comunes.
_ETIQUETAS_ANATOMICAS: frozenset[str] = frozenset(
    {
        "cabeza",
        "linea de hombros",
        "linea de cadera",
        "rodilla de apoyo",
        "tronco",
        "brazo",
        "brazos",
    }
)


# --------------------------------------------------------------------------- #
# Lectura defensiva de la Ficha_JSON
# --------------------------------------------------------------------------- #


def _mapa(ficha: object) -> Mapping[str, Any]:
    """Devuelve `ficha` como mapeo, o lanza `ValueError` si no lo es.

    Una ficha que no es un mapeo es un error de programacion de quien llama (no
    un fallo del build), asi que se reporta con `ValueError`, igual que
    `paleta.rgb_pdf` ante un color ajeno a la paleta.
    """
    if not isinstance(ficha, Mapping):
        raise ValueError(f"se esperaba una Ficha_JSON (mapeo), no {type(ficha)!r}")
    return ficha


def _lineas(valor: object) -> tuple[str, ...]:
    """Normaliza una lista del catalogo a tupla de cadenas no vacias."""
    if not isinstance(valor, Sequence) or isinstance(valor, (str, bytes)):
        return ()
    salida: list[str] = []
    for elemento in valor:
        texto = str(elemento).strip()
        if texto:
            salida.append(texto)
    return tuple(salida)


def _es_meta(paso: str) -> bool:
    """`True` si el paso es progresion, metrica o variante (no una instruccion)."""
    bajo = paso.strip().lower()
    return any(bajo.startswith(prefijo) for prefijo in _PREFIJOS_META)


def _empieza_por(lineas: tuple[str, ...], prefijo: str) -> str:
    """Primera linea que arranca con `prefijo` (sin distinguir mayusculas)."""
    for linea in lineas:
        if linea.strip().lower().startswith(prefijo):
            return linea.strip()
    return ""


def _sin_prefijo(linea: str) -> str:
    """Quita el rotulo `Algo:` inicial de una linea del catalogo, si lo trae."""
    cabeza, sep, cola = linea.partition(":")
    if sep and len(cabeza) <= 40:
        return cola.strip() or linea.strip()
    return linea.strip()


# --------------------------------------------------------------------------- #
# Zona 3: "Hazlo asi"
# --------------------------------------------------------------------------- #


def pasos_hazlo_asi(ficha: object) -> tuple[str, ...]:
    """Pasos de ejecucion de la ficha, una instruccion por linea.

    Deja fuera los pasos que el catalogo usa como progresion, metrica de mejora
    y variante por numero de jugadoras: esos tienen su propia zona (7 y 8), y
    repetirlos aqui alargaria la lista sin ensenar nada nuevo.
    """
    pasos = _lineas(_mapa(ficha).get("pasos"))
    return tuple(paso for paso in pasos if not _es_meta(paso))


# --------------------------------------------------------------------------- #
# Zonas 4 y 5: puntos clave y errores comunes
# --------------------------------------------------------------------------- #


def _leyenda_figura(postura: object) -> tuple[str, ...]:
    """Textos de la leyenda de la ilustracion, sin la entrada de error."""
    leyenda = getattr(postura, "leyenda", ()) or ()
    salida: list[str] = []
    for entrada in leyenda:
        texto = str(getattr(entrada, "texto", "") or "").strip()
        if not texto or "error" in texto.lower():
            continue
        salida.append(texto)
    return tuple(salida)


def _etiquetas_panel_error(postura: object) -> tuple[str, ...]:
    """Etiquetas del panel "ASI NO" de la ilustracion (el error y su correccion).

    Recorre los items en orden y se queda con las etiquetas posteriores al rotulo
    del panel de error, descartando las anatomicas (que describen el dibujo, no
    el error). El rotulo `Corrige: ...` se conserva: es la correccion corta que
    pide la zona.
    """
    items = getattr(postura, "items", ()) or ()
    en_panel = False
    salida: list[str] = []
    for item in items:
        etiqueta = str(getattr(item, "etiqueta", "") or "").strip()
        if not etiqueta:
            continue
        if etiqueta.upper() == _PANEL_ERROR:
            en_panel = True
            continue
        if not en_panel:
            continue
        if etiqueta.lower() in _ETIQUETAS_ANATOMICAS:
            continue
        salida.append(etiqueta)
    return tuple(salida)


def puntos_clave(ficha: object, postura: object = None) -> tuple[str, ...]:
    """Puntos clave de la ficha: lo que hay que vigilar para ejecutarla bien.

    Combina, sin inventar nada:

    * los rotulos de la leyenda de la ilustracion cuando la ficha lleva una
      (pie de apoyo, superficie de contacto, orientacion de cadera, trayectoria
      del balon), que son exactamente los cinco ejes que pide la zona;
    * los puntos redactados en positivo de `que_mira_la_companera`.

    Los puntos redactados en negativo se van a la zona de errores comunes, para
    que las dos zonas no digan lo mismo.
    """
    datos = _mapa(ficha)
    observaciones = _lineas(datos.get("que_mira_la_companera"))
    positivos = tuple(obs for obs in observaciones if not _es_negativo(obs))
    if not positivos:
        positivos = observaciones
    return _leyenda_figura(postura) + positivos


def _es_negativo(texto: str) -> bool:
    """`True` si el punto esta redactado como un error a evitar."""
    bajo = f" {texto.strip().lower()} "
    return any(marca in bajo for marca in _MARCAS_NEGATIVO)


def errores_comunes(ficha: object, postura: object = None) -> tuple[str, ...]:
    """Errores comunes de la ficha, con su correccion corta cuando existe.

    Fuentes, en este orden: el panel "ASI NO" de la ilustracion (que trae el
    error dibujado y su rotulo `Corrige: ...`) y los puntos de
    `que_mira_la_companera` redactados en negativo. Si la ficha no tiene ninguna
    de las dos, devuelve la linea de encuadre `ENCUADRE_ERRORES`, que remite a
    los puntos clave en lugar de inventar un error.
    """
    datos = _mapa(ficha)
    observaciones = _lineas(datos.get("que_mira_la_companera"))
    positivos = tuple(obs for obs in observaciones if not _es_negativo(obs))
    negativos = tuple(obs for obs in observaciones if _es_negativo(obs))
    del_dibujo = _etiquetas_panel_error(postura)
    # Los puntos en negativo solo bajan aqui si en la ficha queda al menos un
    # punto en positivo para la zona de puntos clave. Si no queda ninguno, las
    # observaciones se quedan enteras alli y esta zona no las repite: las dos
    # zonas nunca dicen lo mismo.
    juntos = del_dibujo + negativos if positivos else del_dibujo
    return juntos if juntos else (ENCUADRE_ERRORES,)


# --------------------------------------------------------------------------- #
# Zona 6: dosis
# --------------------------------------------------------------------------- #


def dosis_chips(ficha: object) -> tuple[tuple[str, str], ...]:
    """Pares (rotulo, valor) de la dosis, en orden, omitiendo los vacios."""
    dosis = _mapa(ficha).get("dosis")
    if not isinstance(dosis, Mapping):
        return ()
    salida: list[tuple[str, str]] = []
    for clave, rotulo in CAMPOS_DOSIS:
        valor = dosis.get(clave)
        texto = str(valor).strip() if valor else ""
        if texto:
            salida.append((rotulo, texto))
    return tuple(salida)


# --------------------------------------------------------------------------- #
# Zonas 7 y 8: progresion y medicion
# --------------------------------------------------------------------------- #


def progresion(ficha: object) -> tuple[tuple[str, str], ...]:
    """Pares (rotulo, texto) de la progresion de dificultad de la ficha.

    Del catalogo salen dos ejes, y cada uno mueve **una sola** dificultad:

    * `Fases`: la linea `Progresion: ...` (sin oposicion, oposicion pasiva,
      oposicion real), cuando la ficha la trae;
    * `Segun cuantas sean`: la linea `Variante 1-8 jugadoras: ...`, que adapta el
      montaje al numero de jugadoras.
    """
    pasos = _lineas(_mapa(ficha).get("pasos"))
    salida: list[tuple[str, str]] = []
    fases = _empieza_por(pasos, "progresion")
    if fases:
        salida.append(("Fases", _sin_prefijo(fases)))
    variante = _empieza_por(pasos, "variante")
    if variante:
        salida.append(("Segun cuantas sean", _sin_prefijo(variante)))
    return tuple(salida)


def medicion(ficha: object) -> tuple[tuple[str, str], ...]:
    """Pares (rotulo, texto) de la zona de medicion.

    `Que se mide` sale de la linea `Metrica de mejora: ...` de la ficha y `Meta`
    de `dosis.meta`. Las dos ya existen en el catalogo; aqui solo se separan para
    que se lean como una metrica y no como un paso mas.
    """
    datos = _mapa(ficha)
    pasos = _lineas(datos.get("pasos"))
    salida: list[tuple[str, str]] = []
    metrica = _empieza_por(pasos, "metrica de mejora")
    if metrica:
        salida.append(("Que se mide", _sin_prefijo(metrica)))
    dosis = datos.get("dosis")
    if isinstance(dosis, Mapping):
        meta = str(dosis.get("meta") or "").strip()
        if meta:
            salida.append(("Meta", meta))
    return tuple(salida)


# --------------------------------------------------------------------------- #
# Texto alternativo de la ilustracion
# --------------------------------------------------------------------------- #


def texto_alternativo(ficha: object, postura: object) -> str:
    """Texto alternativo de la ilustracion de una ficha (para `figcaption`/`alt`).

    Se arma con el titulo de la ilustracion y el de la ficha, mas los ejes de su
    leyenda: describe lo que se ve sin depender del color.
    """
    datos = _mapa(ficha)
    titulo_figura = str(getattr(postura, "titulo", "") or "").strip()
    titulo_ficha = str(datos.get("titulo") or "").strip()
    ejes = ", ".join(_leyenda_figura(postura)).lower()
    partes: list[str] = []
    if titulo_figura:
        partes.append(titulo_figura)
    elif titulo_ficha:
        partes.append(f"Ilustracion de tecnica: {titulo_ficha}")
    if ejes:
        partes.append(f"Muestra {ejes}, con el gesto correcto y el error al lado")
    return ". ".join(partes)


# --------------------------------------------------------------------------- #
# Vista completa (util para pruebas y para el render)
# --------------------------------------------------------------------------- #


def zonas_de_ficha(ficha: object, postura: object = None) -> dict[str, bool]:
    """Mapa `zona -> tiene contenido` de una ficha concreta.

    `encabezado` y `visual` se consideran presentes cuando la ficha trae titulo y
    cuando hay ilustracion o diagrama de cancha, respectivamente.
    """
    datos = _mapa(ficha)
    cancha = datos.get("cancha")
    return {
        "encabezado": bool(str(datos.get("titulo") or "").strip()),
        "visual": postura is not None or bool(isinstance(cancha, Mapping) and cancha),
        "hazlo-asi": bool(pasos_hazlo_asi(datos)),
        "puntos-clave": bool(puntos_clave(datos, postura)),
        "errores": bool(errores_comunes(datos, postura)),
        "dosis": bool(dosis_chips(datos)),
        "progresion": bool(progresion(datos)),
        "medicion": bool(medicion(datos)),
        "video": bool(_lineas([m.get("url") for m in datos.get("media") or [] if isinstance(m, Mapping)])),
    }
