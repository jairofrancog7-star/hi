"""Decodificador de códigos QR independiente (Decodificador_QR, `qr_decode.py`).

Recupera la URL codificada en una `MatrizQR` **sin recorrer el camino de
codificación** de `qr.py`: no reutiliza `_bits_de_datos`, `_intercalar`,
`_rs_resto` ni `colocar_datos`. Implementa su propia lectura, así que un fallo
del codificador (máscara mal escrita, entrelazado invertido, RS incorrecto) se
detecta como una divergencia real en el round-trip, no queda enmascarado por
compartir la misma rutina. Cubre la tarea 2.2 del plan.

Pasos del decodificador (independientes del codificador):

1. **Versión** deducida del lado de la matriz: ``version = (lado - 17) // 4``.
2. **Información de formato**: se leen los 15 bits de la primera copia, se
   deshace la máscara XOR del estándar y se extrae el patrón de máscara y el
   nivel de corrección.
3. **Mapa de módulos de función** reconstruido por el propio decodificador
   (localizadores + separadores, temporización, alineación, zona de formato y
   módulo oscuro fijo) para saber qué módulos llevan datos.
4. **Lectura en zigzag** de los módulos de datos, deshaciendo la máscara con la
   condición del patrón leído.
5. **Desentrelazado** de codewords en bloques de datos y de corrección.
6. **Corrección Reed-Solomon** en GF(256) (síndromes → Berlekamp-Massey →
   búsqueda de Chien → Forney) por bloque.
7. **Extracción del segmento byte mode**: indicador de modo, contador de
   caracteres y bytes, decodificados como UTF-8.

Reutiliza de `qr.py` únicamente las **tablas GF(256)** y las **utilidades de
bajo nivel/geometría** (tablas de versión, coordenadas de formato, condición de
máscara), tal y como permiten las convenciones del proyecto; nunca las
funciones de codificación.

API:

    from guia import qr, qr_decode
    matriz = qr.codificar(url)
    url_leida = qr_decode.decodificar(matriz)      # -> str
    qr_decode.verificar_qr(url, matriz, id_ficha='ficha-42')  # round-trip

`verificar_qr` lanza `ErrorQR` (`E_QR_NO_VERIFICA`) con el id de la ficha y la
URL cuando el round-trip no reproduce la URL de origen (Requisito 9.8). Sin
`assert` en producción: los fallos estructurales del decodificador se expresan
con `raise` (`ValueError` en la decodificación pura, `ErrorQR` en la
verificación).
"""

from __future__ import annotations

from array import array

from guia import qr
from guia.errores import ErrorQR

__all__ = [
    "decodificar",
    "verificar_qr",
]


# --------------------------------------------------------------------------- #
# Aritmética en GF(256): se reutilizan las tablas de `qr.py`, con utilidades
# propias (inverso, división y operaciones sobre polinomios) para el decoder.
# --------------------------------------------------------------------------- #

_EXP = qr._GF_EXP
_LOG = qr._GF_LOG


def _gf_mul(a: int, b: int) -> int:
    """Producto en GF(256) (reutiliza las tablas exp/log de `qr`)."""
    if a == 0 or b == 0:
        return 0
    return _EXP[_LOG[a] + _LOG[b]]


def _gf_inv(a: int) -> int:
    """Inverso multiplicativo en GF(256)."""
    if a == 0:
        raise ValueError("GF(256): el 0 no tiene inverso")
    return _EXP[255 - _LOG[a]]


def _poly_escala(poly: list[int], x: int) -> list[int]:
    """Multiplica cada coeficiente del polinomio por el escalar `x`."""
    return [_gf_mul(coef, x) for coef in poly]


def _poly_suma(p: list[int], q: list[int]) -> list[int]:
    """Suma (XOR) de dos polinomios, alineados por el término de menor grado."""
    largo = max(len(p), len(q))
    resultado = [0] * largo
    desf_p = largo - len(p)
    desf_q = largo - len(q)
    for i, coef in enumerate(p):
        resultado[i + desf_p] = coef
    for i, coef in enumerate(q):
        resultado[i + desf_q] ^= coef
    return resultado


def _poly_mul(p: list[int], q: list[int]) -> list[int]:
    """Producto de dos polinomios en GF(256)."""
    resultado = [0] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        if a == 0:
            continue
        for j, b in enumerate(q):
            resultado[i + j] ^= _gf_mul(a, b)
    return resultado


def _poly_eval(poly: list[int], x: int) -> int:
    """Evalúa el polinomio en `x` (regla de Horner). `poly[0]` es el mayor grado."""
    y = 0
    for coef in poly:
        y = _gf_mul(y, x) ^ coef
    return y


# --------------------------------------------------------------------------- #
# Reed-Solomon: decodificación (síndromes, Berlekamp-Massey, Chien, Forney)
# --------------------------------------------------------------------------- #
#
# El generador de `qr.py` tiene raíces α^0..α^(nsym-1) (primer exponente 0,
# generador α = 2), así que los síndromes se evalúan en α^0..α^(nsym-1).


def _rs_sindromes(mensaje: list[int], nsym: int) -> list[int]:
    """Síndromes del `mensaje` (datos + corrección) para `nsym` codewords EC."""
    sindromes = [0] * nsym
    for k in range(nsym):
        sindromes[k] = _poly_eval(mensaje, _EXP[k])
    return sindromes


def _rs_localizador(sindromes: list[int], nsym: int) -> list[int]:
    """Polinomio localizador de errores por Berlekamp-Massey."""
    loc = [1]
    ant = [1]
    for i in range(nsym):
        ant = ant + [0]
        delta = sindromes[i]
        for j in range(1, len(loc)):
            delta ^= _gf_mul(loc[len(loc) - 1 - j], sindromes[i - j])
        if delta != 0:
            if len(ant) > len(loc):
                nuevo = _poly_escala(ant, delta)
                ant = _poly_escala(loc, _gf_inv(delta))
                loc = nuevo
            loc = _poly_suma(loc, _poly_escala(ant, delta))
    while loc and loc[0] == 0:
        del loc[0]
    return loc


def _rs_posiciones_error(localizador: list[int], n: int) -> list[int]:
    """Búsqueda de Chien: posiciones (índice en el mensaje) de los errores."""
    errores = len(localizador) - 1
    posiciones: list[int] = []
    for i in range(n):
        if _poly_eval(localizador, _EXP[255 - i]) == 0:
            posiciones.append(n - 1 - i)
    if len(posiciones) != errores:
        raise ValueError(
            "Reed-Solomon: no se localizaron todos los errores "
            f"({len(posiciones)} de {errores})"
        )
    return posiciones


def _rs_corregir(
    mensaje: list[int],
    sindromes: list[int],
    posiciones: list[int],
) -> list[int]:
    """Corrige los errores en `posiciones` con el algoritmo de Forney."""
    n = len(mensaje)
    # Polinomio localizador a partir de las posiciones de error.
    localizador = [1]
    for pos in posiciones:
        x = _EXP[n - 1 - pos]
        localizador = _poly_mul(localizador, [x, 1])
    # Polinomio evaluador de errores: Ω(x) = (S(x) · Λ(x)) mod x^nsym.
    sindromes_poly = list(reversed(sindromes))
    producto = _poly_mul(sindromes_poly, localizador)
    nsym = len(sindromes)
    evaluador = producto[len(producto) - nsym :]

    corregido = list(mensaje)
    for pos in posiciones:
        # X_k = α^(n-1-pos) es el localizador de este error.
        xi = _EXP[n - 1 - pos]
        xi_inv = _gf_inv(xi)
        num = _poly_eval(evaluador, xi_inv)
        den = _derivada_eval(localizador, xi_inv)
        if den == 0:
            raise ValueError("Reed-Solomon: derivada nula en Forney")
        # Forney con primer exponente 0: e_k = X_k · Ω(X_k^-1) / Λ'(X_k^-1).
        magnitud = _gf_mul(xi, _gf_mul(num, _gf_inv(den)))
        corregido[pos] ^= magnitud
    return corregido


def _derivada_eval(localizador: list[int], x: int) -> int:
    """Evalúa la derivada formal del localizador en `x` (GF(2^m)).

    En característica 2 la derivada formal conserva solo los términos de
    exponente impar; su coeficiente se mantiene y el exponente baja en 1 (par).
    `localizador[0]` es el coeficiente de mayor grado.
    """
    grado = len(localizador) - 1
    resultado = 0
    for i, coef in enumerate(localizador):
        exponente = grado - i
        if coef != 0 and exponente % 2 == 1:
            resultado ^= _gf_mul(coef, _potencia(x, exponente - 1))
    return resultado


def _potencia(x: int, exponente: int) -> int:
    """Eleva `x` a `exponente` en GF(256) (exponente >= 0)."""
    if exponente == 0:
        return 1
    if x == 0:
        return 0
    return _EXP[(_LOG[x] * exponente) % 255]


def _rs_decodificar_bloque(datos: list[int], ec: list[int]) -> list[int]:
    """Decodifica un bloque (datos + EC) devolviendo los datos ya corregidos."""
    nsym = len(ec)
    mensaje = datos + ec
    sindromes = _rs_sindromes(mensaje, nsym)
    if not any(sindromes):
        return list(datos)
    localizador = _rs_localizador(sindromes, nsym)
    posiciones = _rs_posiciones_error(localizador, len(mensaje))
    corregido = _rs_corregir(mensaje, sindromes, posiciones)
    # Reverificación: los síndromes del mensaje corregido deben anularse.
    if any(_rs_sindromes(corregido, nsym)):
        raise ValueError("Reed-Solomon: la corrección no eliminó los errores")
    return corregido[: len(datos)]


# --------------------------------------------------------------------------- #
# Mapa de módulos de función (reconstruido por el decodificador)
# --------------------------------------------------------------------------- #


def _lado_de_version(version: int) -> int:
    """Módulos por lado de una versión (21, 25, ..., 41)."""
    return version * 4 + 17


def _mapa_funcion(version: int) -> array:
    """Marca con 1 los módulos de función (no portan datos) de la versión."""
    lado = _lado_de_version(version)
    funcion = array("B", bytes(lado * lado))

    def marcar(fila: int, col: int) -> None:
        if 0 <= fila < lado and 0 <= col < lado:
            funcion[fila * lado + col] = 1

    # Localizadores 7x7 con separador de 1 módulo (ventana 9x9 recortada).
    for fila_base, col_base in ((0, 0), (0, lado - 7), (lado - 7, 0)):
        for df in range(-1, 8):
            for dc in range(-1, 8):
                marcar(fila_base + df, col_base + dc)

    # Patrones de temporización (fila 6 y columna 6).
    for i in range(8, lado - 8):
        marcar(6, i)
        marcar(i, 6)

    # Patrón de alineación central (versiones 2..6).
    centro = qr._ALIGN_CENTRO.get(version)
    if centro is not None:
        for df in range(-2, 3):
            for dc in range(-2, 3):
                marcar(centro + df, centro + dc)

    # Zona de información de formato y módulo oscuro fijo.
    for fila, col in qr._posiciones_formato(lado):
        marcar(fila, col)
    marcar(lado - 8, 8)

    return funcion


# --------------------------------------------------------------------------- #
# Lectura de la información de formato
# --------------------------------------------------------------------------- #


def _leer_mascara(matriz: qr.MatrizQR) -> int:
    """Lee los 15 bits de formato de la primera copia y extrae la máscara."""
    lado = matriz.lado
    posiciones = qr._posiciones_formato(lado)
    formato = 0
    for k in range(15):
        fila, col = posiciones[k]
        formato |= matriz.modulo(fila, col) << k
    datos = (formato ^ qr._FORMATO_XOR) >> 10  # 5 bits: nivel (2) + máscara (3)
    return datos & 0b111


# --------------------------------------------------------------------------- #
# Lectura de módulos de datos en zigzag
# --------------------------------------------------------------------------- #


def _leer_bits_datos(matriz: qr.MatrizQR, funcion: array, mascara: int) -> list[int]:
    """Recorre los módulos de datos en zigzag deshaciendo la máscara."""
    lado = matriz.lado
    bits: list[int] = []
    hacia_arriba = True
    col = lado - 1
    while col > 0:
        if col == 6:  # la columna 6 es de temporización
            col -= 1
        for i in range(lado):
            fila = (lado - 1 - i) if hacia_arriba else i
            for c in (col, col - 1):
                idx = fila * lado + c
                if not funcion[idx]:
                    bit = matriz.modulo(fila, c)
                    if qr._condicion_mascara(mascara, fila, c):
                        bit ^= 1
                    bits.append(bit)
        hacia_arriba = not hacia_arriba
        col -= 2
    return bits


def _bits_a_codewords(bits: list[int], total: int) -> list[int]:
    """Agrupa los primeros `total` codewords (8 bits, MSB primero)."""
    codewords: list[int] = []
    for i in range(total):
        base = i * 8
        valor = 0
        for j in range(8):
            valor = (valor << 1) | bits[base + j]
        codewords.append(valor)
    return codewords


# --------------------------------------------------------------------------- #
# Desentrelazado
# --------------------------------------------------------------------------- #


def _desentrelazar(codewords: list[int], version: int) -> list[int]:
    """Invierte el entrelazado: reconstruye el flujo de datos ya corregido."""
    n_bloques = qr._BLOQUES_L[version]
    ec_por_bloque = qr._EC_CW_L[version]
    datos_totales = qr._DATOS_CW_L[version]
    tam_bloque = datos_totales // n_bloques

    # Reparto column-major inverso de los codewords de datos.
    bloques_datos: list[list[int]] = [[0] * tam_bloque for _ in range(n_bloques)]
    pos = 0
    for i in range(tam_bloque):
        for b in range(n_bloques):
            bloques_datos[b][i] = codewords[pos]
            pos += 1

    # Reparto column-major inverso de los codewords de corrección.
    bloques_ec: list[list[int]] = [[0] * ec_por_bloque for _ in range(n_bloques)]
    for i in range(ec_por_bloque):
        for b in range(n_bloques):
            bloques_ec[b][i] = codewords[pos]
            pos += 1

    # Corrección RS por bloque y concatenación en orden de bloque.
    resultado: list[int] = []
    for b in range(n_bloques):
        resultado.extend(_rs_decodificar_bloque(bloques_datos[b], bloques_ec[b]))
    return resultado


# --------------------------------------------------------------------------- #
# Extracción del segmento byte mode
# --------------------------------------------------------------------------- #

_INDICADOR_BYTE: int = 0b0100


def _extraer_url(datos: list[int]) -> str:
    """Extrae la URL del segmento byte mode del flujo de codewords de datos."""
    bits: list[int] = []
    for cw in datos:
        for desplazamiento in range(7, -1, -1):
            bits.append((cw >> desplazamiento) & 1)

    if len(bits) < 12:
        raise ValueError("flujo de datos demasiado corto para un segmento QR")

    modo = _leer_entero(bits, 0, 4)
    if modo != _INDICADOR_BYTE:
        raise ValueError(f"modo QR no soportado: {modo:#06b} (se esperaba byte mode)")

    longitud = _leer_entero(bits, 4, 8)
    inicio = 12
    fin = inicio + longitud * 8
    if fin > len(bits):
        raise ValueError(
            f"el contador de caracteres ({longitud}) excede los datos disponibles"
        )

    crudos = bytearray()
    for i in range(longitud):
        base = inicio + i * 8
        crudos.append(_leer_entero(bits, base, 8))
    return crudos.decode("utf-8")


def _leer_entero(bits: list[int], inicio: int, cantidad: int) -> int:
    """Lee `cantidad` bits (MSB primero) desde `inicio` como entero."""
    valor = 0
    for i in range(cantidad):
        valor = (valor << 1) | bits[inicio + i]
    return valor


# --------------------------------------------------------------------------- #
# API pública
# --------------------------------------------------------------------------- #


def decodificar(matriz: qr.MatrizQR) -> str:
    """Decodifica una `MatrizQR` y devuelve la URL codificada.

    No comparte el camino de codificación de `qr.py`: deduce la versión del
    lado, lee la máscara del formato, reconstruye el mapa de función, lee los
    módulos de datos, desentrelaza, corrige con Reed-Solomon y extrae el
    segmento byte mode. Lanza `ValueError` ante cualquier fallo estructural
    (formato inconsistente, RS incorregible o modo no soportado).
    """
    if not isinstance(matriz, qr.MatrizQR):
        raise ValueError(f"se esperaba MatrizQR, no {type(matriz).__name__}")

    lado = matriz.lado
    if (lado - 17) % 4 != 0:
        raise ValueError(f"lado de matriz inválido: {lado}")
    version = (lado - 17) // 4
    if version not in qr._DATOS_CW_L:
        raise ValueError(f"versión de QR fuera de rango (1..6): {version}")

    mascara = _leer_mascara(matriz)
    funcion = _mapa_funcion(version)
    bits = _leer_bits_datos(matriz, funcion, mascara)

    total_codewords = qr._DATOS_CW_L[version] + qr._EC_CW_L[version] * qr._BLOQUES_L[version]
    if len(bits) < total_codewords * 8:
        raise ValueError(
            f"módulos de datos insuficientes: {len(bits)} bits para "
            f"{total_codewords} codewords"
        )

    codewords = _bits_a_codewords(bits, total_codewords)
    datos = _desentrelazar(codewords, version)
    return _extraer_url(datos)


def verificar_qr(url: str, matriz: qr.MatrizQR, *, id_ficha: str = "") -> None:
    """Verifica el round-trip de un QR: `decodificar(matriz)` debe dar `url`.

    Se ejecuta una vez por entrada de caché (no por uso). Si el decodificador
    no reproduce la URL de origen —por un fallo del codificador o una matriz
    corrompida más allá de la corrección de errores— lanza `ErrorQR`
    (`E_QR_NO_VERIFICA`) nombrando la Ficha_Ejercicio y la URL afectadas
    (Requisitos 9.7, 9.8).
    """
    detalle: dict[str, object] = {"id": id_ficha, "url": url}
    try:
        leida = decodificar(matriz)
    except (ValueError, UnicodeDecodeError) as causa:
        raise ErrorQR(
            f"QR de la ficha {id_ficha} no reproduce {url}",
            detalle={**detalle, "motivo": str(causa)},
        ) from causa
    if leida != url:
        raise ErrorQR(
            f"QR de la ficha {id_ficha} no reproduce {url}",
            detalle={**detalle, "leida": leida},
        )
