"""Métricas de texto y codificación WinAnsi para las fuentes Standard-14.

Este módulo es el único punto del pipeline que sabe cuánto mide un texto en
puntos y cómo se convierte una cadena Unicode a los bytes que espera un PDF
con `WinAnsiEncoding`. Solo se soportan las dos fuentes que usa la guía:
`Helvetica` y `Helvetica-Bold`.

Estrategia de rendimiento (ver design.md, "Estrategia de rendimiento"):

* Los anchos de glifo de cada fuente se guardan en un `array('f')` de 256
  entradas indexado por el byte cp1252, **construido una sola vez** en tiempo
  de import. Medir un texto es entonces una suma sobre un array tipado, no una
  sucesión de búsquedas en un diccionario.
* `medir_texto` y `envolver` llevan `functools.lru_cache`: sus argumentos son
  inmutables y hashables, así que la caché es correcta por construcción.
* `envolver` devuelve `tuple[str, ...]` (hashable e inmutable) para poder ser
  cacheada y para que nadie la mute por accidente.

Codificación WinAnsi (ver design.md, "Codificación WinAnsi explícita y
verificada"): `str.encode('cp1252')` es el equivalente exacto de
`WinAnsiEncoding` para el rango que usa el documento. Un carácter no
codificable se detecta en la fase de validación y se reporta como
`E_CARACTER_NO_CODIFICABLE` con el carácter, su code point y su posición.

Sin `assert` en producción: todo invariante se comprueba con `raise`
(`python -O` borra los `assert`).
"""

from __future__ import annotations

from array import array
from functools import lru_cache

from .errores import E_CARACTER_NO_CODIFICABLE, ErrorBuild

__all__ = [
    "ANCHOS_HELV",
    "ANCHOS_HELV_BOLD",
    "codificar_winansi",
    "envolver",
    "escapar_literal_pdf",
    "medir_texto",
]


# --------------------------------------------------------------------------- #
# WinAnsiEncoding: byte cp1252 -> nombre de glifo AFM
# --------------------------------------------------------------------------- #
#
# Solo se listan los códigos con glifo asignado en cp1252/WinAnsiEncoding. Los
# bytes sin glifo (control y 0x81, 0x8D, 0x8F, 0x90, 0x9D) quedan con ancho 0.

_CP1252_A_GLIFO: dict[int, str] = {
    0x20: "space", 0x21: "exclam", 0x22: "quotedbl", 0x23: "numbersign",
    0x24: "dollar", 0x25: "percent", 0x26: "ampersand", 0x27: "quotesingle",
    0x28: "parenleft", 0x29: "parenright", 0x2A: "asterisk", 0x2B: "plus",
    0x2C: "comma", 0x2D: "hyphen", 0x2E: "period", 0x2F: "slash",
    0x30: "zero", 0x31: "one", 0x32: "two", 0x33: "three", 0x34: "four",
    0x35: "five", 0x36: "six", 0x37: "seven", 0x38: "eight", 0x39: "nine",
    0x3A: "colon", 0x3B: "semicolon", 0x3C: "less", 0x3D: "equal",
    0x3E: "greater", 0x3F: "question", 0x40: "at",
    0x41: "A", 0x42: "B", 0x43: "C", 0x44: "D", 0x45: "E", 0x46: "F",
    0x47: "G", 0x48: "H", 0x49: "I", 0x4A: "J", 0x4B: "K", 0x4C: "L",
    0x4D: "M", 0x4E: "N", 0x4F: "O", 0x50: "P", 0x51: "Q", 0x52: "R",
    0x53: "S", 0x54: "T", 0x55: "U", 0x56: "V", 0x57: "W", 0x58: "X",
    0x59: "Y", 0x5A: "Z",
    0x5B: "bracketleft", 0x5C: "backslash", 0x5D: "bracketright",
    0x5E: "asciicircum", 0x5F: "underscore", 0x60: "grave",
    0x61: "a", 0x62: "b", 0x63: "c", 0x64: "d", 0x65: "e", 0x66: "f",
    0x67: "g", 0x68: "h", 0x69: "i", 0x6A: "j", 0x6B: "k", 0x6C: "l",
    0x6D: "m", 0x6E: "n", 0x6F: "o", 0x70: "p", 0x71: "q", 0x72: "r",
    0x73: "s", 0x74: "t", 0x75: "u", 0x76: "v", 0x77: "w", 0x78: "x",
    0x79: "y", 0x7A: "z",
    0x7B: "braceleft", 0x7C: "bar", 0x7D: "braceright", 0x7E: "asciitilde",
    0x80: "Euro", 0x82: "quotesinglbase", 0x83: "florin",
    0x84: "quotedblbase", 0x85: "ellipsis", 0x86: "dagger",
    0x87: "daggerdbl", 0x88: "circumflex", 0x89: "perthousand",
    0x8A: "Scaron", 0x8B: "guilsinglleft", 0x8C: "OE", 0x8E: "Zcaron",
    0x91: "quoteleft", 0x92: "quoteright", 0x93: "quotedblleft",
    0x94: "quotedblright", 0x95: "bullet", 0x96: "endash", 0x97: "emdash",
    0x98: "tilde", 0x99: "trademark", 0x9A: "scaron",
    0x9B: "guilsinglright", 0x9C: "oe", 0x9E: "zcaron", 0x9F: "Ydieresis",
    0xA0: "space", 0xA1: "exclamdown", 0xA2: "cent", 0xA3: "sterling",
    0xA4: "currency", 0xA5: "yen", 0xA6: "brokenbar", 0xA7: "section",
    0xA8: "dieresis", 0xA9: "copyright", 0xAA: "ordfeminine",
    0xAB: "guillemotleft", 0xAC: "logicalnot", 0xAD: "hyphen",
    0xAE: "registered", 0xAF: "macron", 0xB0: "degree", 0xB1: "plusminus",
    0xB2: "twosuperior", 0xB3: "threesuperior", 0xB4: "acute", 0xB5: "mu",
    0xB6: "paragraph", 0xB7: "periodcentered", 0xB8: "cedilla",
    0xB9: "onesuperior", 0xBA: "ordmasculine", 0xBB: "guillemotright",
    0xBC: "onequarter", 0xBD: "onehalf", 0xBE: "threequarters",
    0xBF: "questiondown",
    0xC0: "Agrave", 0xC1: "Aacute", 0xC2: "Acircumflex", 0xC3: "Atilde",
    0xC4: "Adieresis", 0xC5: "Aring", 0xC6: "AE", 0xC7: "Ccedilla",
    0xC8: "Egrave", 0xC9: "Eacute", 0xCA: "Ecircumflex", 0xCB: "Edieresis",
    0xCC: "Igrave", 0xCD: "Iacute", 0xCE: "Icircumflex", 0xCF: "Idieresis",
    0xD0: "Eth", 0xD1: "Ntilde", 0xD2: "Ograve", 0xD3: "Oacute",
    0xD4: "Ocircumflex", 0xD5: "Otilde", 0xD6: "Odieresis", 0xD7: "multiply",
    0xD8: "Oslash", 0xD9: "Ugrave", 0xDA: "Uacute", 0xDB: "Ucircumflex",
    0xDC: "Udieresis", 0xDD: "Yacute", 0xDE: "Thorn", 0xDF: "germandbls",
    0xE0: "agrave", 0xE1: "aacute", 0xE2: "acircumflex", 0xE3: "atilde",
    0xE4: "adieresis", 0xE5: "aring", 0xE6: "ae", 0xE7: "ccedilla",
    0xE8: "egrave", 0xE9: "eacute", 0xEA: "ecircumflex", 0xEB: "edieresis",
    0xEC: "igrave", 0xED: "iacute", 0xEE: "icircumflex", 0xEF: "idieresis",
    0xF0: "eth", 0xF1: "ntilde", 0xF2: "ograve", 0xF3: "oacute",
    0xF4: "ocircumflex", 0xF5: "otilde", 0xF6: "odieresis", 0xF7: "divide",
    0xF8: "oslash", 0xF9: "ugrave", 0xFA: "uacute", 0xFB: "ucircumflex",
    0xFC: "udieresis", 0xFD: "yacute", 0xFE: "thorn", 0xFF: "ydieresis",
}


# --------------------------------------------------------------------------- #
# Anchos AFM estándar de Adobe (unidades/1000), por nombre de glifo
# --------------------------------------------------------------------------- #
#
# Valores tomados de las métricas Core-14 de Adobe para Helvetica y
# Helvetica-Bold. Los glifos acentuados comparten el ancho de avance de su
# letra base (los acentos no modifican el avance en estas fuentes).

_AFM_HELVETICA: dict[str, int] = {
    "space": 278, "exclam": 278, "quotedbl": 355, "numbersign": 556,
    "dollar": 556, "percent": 889, "ampersand": 667, "quotesingle": 191,
    "parenleft": 333, "parenright": 333, "asterisk": 389, "plus": 584,
    "comma": 278, "hyphen": 333, "period": 278, "slash": 278,
    "zero": 556, "one": 556, "two": 556, "three": 556, "four": 556,
    "five": 556, "six": 556, "seven": 556, "eight": 556, "nine": 556,
    "colon": 278, "semicolon": 278, "less": 584, "equal": 584,
    "greater": 584, "question": 556, "at": 1015,
    "A": 667, "B": 667, "C": 722, "D": 722, "E": 667, "F": 611, "G": 778,
    "H": 722, "I": 278, "J": 500, "K": 667, "L": 556, "M": 833, "N": 722,
    "O": 778, "P": 667, "Q": 778, "R": 722, "S": 667, "T": 611, "U": 722,
    "V": 667, "W": 944, "X": 667, "Y": 667, "Z": 611,
    "bracketleft": 278, "backslash": 278, "bracketright": 278,
    "asciicircum": 469, "underscore": 556, "grave": 333,
    "a": 556, "b": 556, "c": 500, "d": 556, "e": 556, "f": 278, "g": 556,
    "h": 556, "i": 222, "j": 222, "k": 500, "l": 222, "m": 833, "n": 556,
    "o": 556, "p": 556, "q": 556, "r": 333, "s": 500, "t": 278, "u": 556,
    "v": 500, "w": 722, "x": 500, "y": 500, "z": 500,
    "braceleft": 334, "bar": 260, "braceright": 334, "asciitilde": 584,
    "Euro": 556, "quotesinglbase": 222, "florin": 556, "quotedblbase": 333,
    "ellipsis": 1000, "dagger": 556, "daggerdbl": 556, "circumflex": 333,
    "perthousand": 1000, "Scaron": 667, "guilsinglleft": 333, "OE": 1000,
    "Zcaron": 611, "quoteleft": 222, "quoteright": 222, "quotedblleft": 333,
    "quotedblright": 333, "bullet": 350, "endash": 556, "emdash": 1000,
    "tilde": 333, "trademark": 1000, "scaron": 500, "guilsinglright": 333,
    "oe": 944, "zcaron": 500, "Ydieresis": 667,
    "exclamdown": 333, "cent": 556, "sterling": 556, "currency": 556,
    "yen": 556, "brokenbar": 260, "section": 556, "dieresis": 333,
    "copyright": 737, "ordfeminine": 370, "guillemotleft": 556,
    "logicalnot": 584, "registered": 737, "macron": 333, "degree": 400,
    "plusminus": 584, "twosuperior": 333, "threesuperior": 333, "acute": 333,
    "mu": 556, "paragraph": 537, "periodcentered": 278, "cedilla": 333,
    "onesuperior": 333, "ordmasculine": 365, "guillemotright": 556,
    "onequarter": 834, "onehalf": 834, "threequarters": 834,
    "questiondown": 611, "multiply": 584, "divide": 584,
    "Agrave": 667, "Aacute": 667, "Acircumflex": 667, "Atilde": 667,
    "Adieresis": 667, "Aring": 667, "AE": 1000, "Ccedilla": 722,
    "Egrave": 667, "Eacute": 667, "Ecircumflex": 667, "Edieresis": 667,
    "Igrave": 278, "Iacute": 278, "Icircumflex": 278, "Idieresis": 278,
    "Eth": 722, "Ntilde": 722, "Ograve": 778, "Oacute": 778,
    "Ocircumflex": 778, "Otilde": 778, "Odieresis": 778, "Oslash": 778,
    "Ugrave": 722, "Uacute": 722, "Ucircumflex": 722, "Udieresis": 722,
    "Yacute": 667, "Thorn": 667, "germandbls": 611,
    "agrave": 556, "aacute": 556, "acircumflex": 556, "atilde": 556,
    "adieresis": 556, "aring": 556, "ae": 889, "ccedilla": 500,
    "egrave": 556, "eacute": 556, "ecircumflex": 556, "edieresis": 556,
    "igrave": 278, "iacute": 278, "icircumflex": 278, "idieresis": 278,
    "eth": 556, "ntilde": 556, "ograve": 556, "oacute": 556,
    "ocircumflex": 556, "otilde": 556, "odieresis": 556, "oslash": 611,
    "ugrave": 556, "uacute": 556, "ucircumflex": 556, "udieresis": 556,
    "yacute": 500, "thorn": 556, "ydieresis": 500,
}

_AFM_HELVETICA_BOLD: dict[str, int] = {
    "space": 278, "exclam": 333, "quotedbl": 474, "numbersign": 556,
    "dollar": 556, "percent": 889, "ampersand": 722, "quotesingle": 238,
    "parenleft": 333, "parenright": 333, "asterisk": 389, "plus": 584,
    "comma": 278, "hyphen": 333, "period": 278, "slash": 278,
    "zero": 556, "one": 556, "two": 556, "three": 556, "four": 556,
    "five": 556, "six": 556, "seven": 556, "eight": 556, "nine": 556,
    "colon": 333, "semicolon": 333, "less": 584, "equal": 584,
    "greater": 584, "question": 611, "at": 975,
    "A": 722, "B": 722, "C": 722, "D": 722, "E": 667, "F": 611, "G": 778,
    "H": 722, "I": 278, "J": 556, "K": 722, "L": 611, "M": 833, "N": 722,
    "O": 778, "P": 667, "Q": 778, "R": 722, "S": 667, "T": 611, "U": 722,
    "V": 667, "W": 944, "X": 667, "Y": 667, "Z": 611,
    "bracketleft": 333, "backslash": 278, "bracketright": 333,
    "asciicircum": 584, "underscore": 556, "grave": 333,
    "a": 556, "b": 611, "c": 556, "d": 611, "e": 556, "f": 333, "g": 611,
    "h": 611, "i": 278, "j": 278, "k": 556, "l": 278, "m": 889, "n": 611,
    "o": 611, "p": 611, "q": 611, "r": 389, "s": 556, "t": 333, "u": 611,
    "v": 556, "w": 778, "x": 556, "y": 556, "z": 500,
    "braceleft": 389, "bar": 280, "braceright": 389, "asciitilde": 584,
    "Euro": 556, "quotesinglbase": 278, "florin": 556, "quotedblbase": 500,
    "ellipsis": 1000, "dagger": 556, "daggerdbl": 556, "circumflex": 333,
    "perthousand": 1000, "Scaron": 667, "guilsinglleft": 333, "OE": 1000,
    "Zcaron": 611, "quoteleft": 278, "quoteright": 278, "quotedblleft": 500,
    "quotedblright": 500, "bullet": 350, "endash": 556, "emdash": 1000,
    "tilde": 333, "trademark": 1000, "scaron": 556, "guilsinglright": 333,
    "oe": 944, "zcaron": 500, "Ydieresis": 667,
    "exclamdown": 333, "cent": 556, "sterling": 556, "currency": 556,
    "yen": 556, "brokenbar": 280, "section": 556, "dieresis": 333,
    "copyright": 737, "ordfeminine": 370, "guillemotleft": 556,
    "logicalnot": 584, "registered": 737, "macron": 333, "degree": 400,
    "plusminus": 584, "twosuperior": 333, "threesuperior": 333, "acute": 333,
    "mu": 611, "paragraph": 556, "periodcentered": 278, "cedilla": 333,
    "onesuperior": 333, "ordmasculine": 365, "guillemotright": 556,
    "onequarter": 834, "onehalf": 834, "threequarters": 834,
    "questiondown": 611, "multiply": 584, "divide": 584,
    "Agrave": 722, "Aacute": 722, "Acircumflex": 722, "Atilde": 722,
    "Adieresis": 722, "Aring": 722, "AE": 1000, "Ccedilla": 722,
    "Egrave": 667, "Eacute": 667, "Ecircumflex": 667, "Edieresis": 667,
    "Igrave": 278, "Iacute": 278, "Icircumflex": 278, "Idieresis": 278,
    "Eth": 722, "Ntilde": 722, "Ograve": 778, "Oacute": 778,
    "Ocircumflex": 778, "Otilde": 778, "Odieresis": 778, "Oslash": 778,
    "Ugrave": 722, "Uacute": 722, "Ucircumflex": 722, "Udieresis": 722,
    "Yacute": 667, "Thorn": 667, "germandbls": 611,
    "agrave": 556, "aacute": 556, "acircumflex": 556, "atilde": 556,
    "adieresis": 556, "aring": 556, "ae": 889, "ccedilla": 556,
    "egrave": 556, "eacute": 556, "ecircumflex": 556, "edieresis": 556,
    "igrave": 278, "iacute": 278, "icircumflex": 278, "idieresis": 278,
    "eth": 611, "ntilde": 611, "ograve": 611, "oacute": 611,
    "ocircumflex": 611, "otilde": 611, "odieresis": 611, "oslash": 611,
    "ugrave": 611, "uacute": 611, "ucircumflex": 611, "udieresis": 611,
    "yacute": 556, "thorn": 611, "ydieresis": 556,
}


def _cargar_anchos(anchos_glifo: dict[str, int]) -> array:
    """Construye el `array('f')` de 256 anchos indexado por byte cp1252.

    Cada entrada es el ancho AFM (unidades/1000) del glifo que
    `WinAnsiEncoding` asigna a ese byte. Los bytes sin glifo asignado quedan
    en 0.0.
    """
    tabla = array("f", bytes(4 * 256))  # 256 flotantes en 0.0
    for byte, glifo in _CP1252_A_GLIFO.items():
        ancho = anchos_glifo.get(glifo)
        if ancho is None:
            raise ValueError(
                f"glifo {glifo!r} (byte 0x{byte:02X}) sin ancho AFM definido"
            )
        tabla[byte] = float(ancho)
    return tabla


# Construidos una única vez al importar el módulo.
ANCHOS_HELV: array = _cargar_anchos(_AFM_HELVETICA)
ANCHOS_HELV_BOLD: array = _cargar_anchos(_AFM_HELVETICA_BOLD)

_TABLAS: dict[str, array] = {
    "Helvetica": ANCHOS_HELV,
    "Helvetica-Bold": ANCHOS_HELV_BOLD,
}


# --------------------------------------------------------------------------- #
# Medición y envoltura de texto
# --------------------------------------------------------------------------- #


@lru_cache(maxsize=200_000)
def medir_texto(
    texto: str, fuente: str = "Helvetica", tamano: float = 10.0
) -> float:
    """Ancho en puntos del `texto` con `fuente` a `tamano` puntos.

    Suma los anchos de glifo (unidades/1000) sobre el array tipado indexando
    por los bytes cp1252 del texto, y escala por `tamano / 1000`.
    """
    tabla = _TABLAS.get(fuente)
    if tabla is None:
        raise ValueError(f"fuente no soportada: {fuente!r}")
    crudos = texto.encode("cp1252")  # WinAnsiEncoding
    total = 0.0
    for b in crudos:  # bytes -> ints, sin objetos intermedios
        total += tabla[b]
    return total * tamano / 1000.0


def _partir_palabra(
    palabra: str, ancho: float, fuente: str, tamano: float
) -> list[str]:
    """Parte una palabra más larga que `ancho` en trozos que sí caben.

    Garantiza al menos un carácter por trozo, así que termina incluso si un
    solo carácter excede la caja.
    """
    trozos: list[str] = []
    actual = ""
    for ch in palabra:
        if actual and medir_texto(actual + ch, fuente, tamano) > ancho:
            trozos.append(actual)
            actual = ch
        else:
            actual += ch
    if actual:
        trozos.append(actual)
    return trozos


@lru_cache(maxsize=100_000)
def envolver(
    texto: str,
    ancho: float,
    fuente: str = "Helvetica",
    tamano: float = 10.0,
) -> tuple[str, ...]:
    """Devuelve tupla (hashable, cacheable) de líneas que caben en `ancho`.

    Envuelve por palabras de forma voraz. Una palabra más larga que la caja se
    parte en trozos con `_partir_palabra`.
    """
    if ancho <= 0:
        raise ValueError(f"ancho debe ser positivo, recibido {ancho!r}")
    palabras = texto.split()
    lineas: list[str] = []
    actual = ""
    for palabra in palabras:
        if medir_texto(palabra, fuente, tamano) > ancho:
            if actual:
                lineas.append(actual)
                actual = ""
            trozos = _partir_palabra(palabra, ancho, fuente, tamano)
            lineas.extend(trozos[:-1])
            actual = trozos[-1]
            continue
        candidato = palabra if not actual else actual + " " + palabra
        if medir_texto(candidato, fuente, tamano) <= ancho:
            actual = candidato
        else:
            lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return tuple(lineas)


# --------------------------------------------------------------------------- #
# Codificación WinAnsi y escape de literales PDF
# --------------------------------------------------------------------------- #


def codificar_winansi(texto: str, *, ctx: str) -> bytes:
    """Codifica `texto` a bytes `WinAnsiEncoding` (cp1252).

    Un carácter fuera de WinAnsiEncoding se reporta como
    `E_CARACTER_NO_CODIFICABLE`, nombrando el carácter, su code point
    (U+XXXX) y su posición dentro del texto. `ctx` describe de dónde viene el
    texto para localizar el fallo.
    """
    try:
        return texto.encode("cp1252")
    except UnicodeEncodeError as e:
        malo = texto[e.start:e.end]
        raise ErrorBuild(
            E_CARACTER_NO_CODIFICABLE,
            f"{ctx}: el caracter {malo!r} (U+{ord(malo[0]):04X}) "
            f"no existe en WinAnsiEncoding, posicion {e.start}",
            detalle={
                "ctx": ctx,
                "caracter": malo[0],
                "code_point": f"U+{ord(malo[0]):04X}",
                "posicion": e.start,
            },
        ) from e


def escapar_literal_pdf(crudos: bytes) -> bytes:
    """Escapa `\\`, `(` y `)` en un literal de cadena PDF."""
    return (
        crudos.replace(b"\\", b"\\\\")
        .replace(b"(", b"\\(")
        .replace(b")", b"\\)")
    )
