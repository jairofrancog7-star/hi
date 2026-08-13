"""Generador de códigos QR con caché por URL (Generador_QR, `qr.py`).

Codifica una URL en una matriz de módulos QR **sin librerías externas**, solo
con la librería estándar de Python 3.11+ (`array`, `functools`). Cubre la tarea
2.1 del plan:

* Codificación en **byte mode**, versiones **1 a 6**, nivel de corrección **L**.
* Corrección de errores **Reed-Solomon en GF(256)** con polinomio primitivo
  `0x11D`; las tablas de logaritmo/antilogaritmo se construyen **una sola vez**
  a nivel de módulo.
* **Selección de máscara**: se evalúan las 8 máscaras con las cuatro reglas de
  penalización del estándar y se elige la de menor penalización.
* La matriz de módulos se guarda en un `array('B')` **plano** (un byte por
  módulo, 0 = claro, 1 = oscuro) en lugar de listas anidadas, para gastar menos
  memoria y recorrer más rápido los bucles de máscara y de Reed-Solomon.
* **Caché `dict[str, MatrizQR]`** a nivel de módulo: muchas fichas comparten el
  mismo video de referencia, así que ~400 llamadas se reducen a ~150
  codificaciones reales (ver design.md, "Caché de QR por URL").

API principal:

    from guia import qr
    matriz = qr.codificar('https://youtube.com/watch?v=...')
    lado = matriz.lado                 # módulos por lado (21..41)
    bit = matriz.modulo(fila, col)     # 0 (claro) o 1 (oscuro)

`codificar(url)` devuelve un `MatrizQR`. El decodificador independiente
(`qr_decode.py`, tarea 2.2) y su verificación de round-trip se implementan
aparte; este módulo solo produce la matriz.

Sin `assert` en producción: los invariantes se comprueban con `raise`. Cuando
la URL excede la capacidad de la versión 6 en nivel L se lanza `ValueError`
documentado (no es un `ErrorBuild`: la jerarquía de `guia.errores` reserva
`E_QR_NO_VERIFICA` para el fallo de round-trip del decodificador de la 2.2).
"""

from __future__ import annotations

from array import array

__all__ = [
    "MatrizQR",
    "codificar",
    "limpiar_cache",
]


# --------------------------------------------------------------------------- #
# Aritmética en GF(256) con polinomio primitivo 0x11D
# --------------------------------------------------------------------------- #
#
# Tablas de antilogaritmo (exp) y logaritmo (log) construidas una única vez al
# importar el módulo. `_GF_EXP` tiene 512 entradas (duplicada) para poder sumar
# exponentes sin tomar módulo 255 en el camino caliente.

_GF_PRIMITIVO: int = 0x11D


def _construir_tablas_gf() -> tuple[array, array]:
    """Construye (antilog, log) de GF(256) con el polinomio primitivo 0x11D."""
    exp = [0] * 512
    log = [0] * 256
    x = 1
    for i in range(255):
        exp[i] = x
        log[x] = i
        x <<= 1
        if x & 0x100:
            x ^= _GF_PRIMITIVO
    for i in range(255, 512):
        exp[i] = exp[i - 255]
    return array("H", exp), array("H", log)


_GF_EXP, _GF_LOG = _construir_tablas_gf()


def _gf_mul(a: int, b: int) -> int:
    """Multiplica dos elementos de GF(256)."""
    if a == 0 or b == 0:
        return 0
    return _GF_EXP[_GF_LOG[a] + _GF_LOG[b]]


# --------------------------------------------------------------------------- #
# Reed-Solomon
# --------------------------------------------------------------------------- #
#
# El divisor (polinomio generador mónico, sin el término líder) se construye de
# forma iterativa multiplicando por (x - α^i). Los coeficientes se guardan de
# mayor a menor grado.


def _rs_divisor(grado: int) -> list[int]:
    """Polinomio generador Reed-Solomon de `grado` coeficientes."""
    resultado = [0] * (grado - 1) + [1]
    raiz = 1
    for _ in range(grado):
        for j in range(grado):
            resultado[j] = _gf_mul(resultado[j], raiz)
            if j + 1 < grado:
                resultado[j] ^= resultado[j + 1]
        raiz = _gf_mul(raiz, 0x02)
    return resultado


def _rs_resto(datos: list[int], divisor: list[int]) -> list[int]:
    """Codewords de corrección de errores para `datos` con `divisor`."""
    grado = len(divisor)
    resto = [0] * grado
    for byte in datos:
        factor = byte ^ resto[0]
        del resto[0]
        resto.append(0)
        for i, coef in enumerate(divisor):
            resto[i] ^= _gf_mul(coef, factor)
    return resto


# --------------------------------------------------------------------------- #
# Tablas de versión para nivel de corrección L (versiones 1..6)
# --------------------------------------------------------------------------- #
#
# En nivel L las versiones 1..5 tienen un solo bloque de corrección; la versión
# 6 tiene dos bloques iguales. Todos los bloques de una misma versión tienen el
# mismo tamaño, así que el entrelazado es directo.

_VERSIONES: tuple[int, ...] = (1, 2, 3, 4, 5, 6)

#: Codewords de datos por versión en nivel L (total del símbolo).
_DATOS_CW_L: dict[int, int] = {1: 19, 2: 34, 3: 55, 4: 80, 5: 108, 6: 136}

#: Codewords de corrección por bloque en nivel L.
_EC_CW_L: dict[int, int] = {1: 7, 2: 10, 3: 15, 4: 20, 5: 26, 6: 18}

#: Número de bloques de corrección en nivel L.
_BLOQUES_L: dict[int, int] = {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 2}

#: Coordenada central del único patrón de alineación (versiones 2..6).
_ALIGN_CENTRO: dict[int, int] = {2: 18, 3: 22, 4: 26, 5: 30, 6: 34}

#: Máscara XOR de los 15 bits de información de formato (estándar QR).
_FORMATO_XOR: int = 0x5412

#: Polinomio generador BCH(15,5) para la información de formato.
_FORMATO_BCH: int = 0x537

#: Indicador de nivel de corrección L en los bits de formato.
_NIVEL_L: int = 0b01


def _lado_de_version(version: int) -> int:
    """Módulos por lado de una versión: 21, 25, ..., 41."""
    return version * 4 + 17


# --------------------------------------------------------------------------- #
# Matriz QR
# --------------------------------------------------------------------------- #


class MatrizQR:
    """Matriz cuadrada de módulos QR (0 = claro, 1 = oscuro).

    Los módulos se guardan en un `array('B')` plano de `lado * lado` bytes,
    indexado por `fila * lado + col`. Expone el número de módulos por lado
    (`lado`, con alias `size`) y el acceso a un módulo con `modulo(fila, col)`
    o con `matriz[fila, col]`.
    """

    __slots__ = ("lado", "version", "mascara", "_modulos")

    def __init__(
        self,
        lado: int,
        version: int,
        mascara: int,
        modulos: array,
    ) -> None:
        if len(modulos) != lado * lado:
            raise ValueError(
                f"la matriz debe tener {lado * lado} módulos, tiene {len(modulos)}"
            )
        self.lado: int = lado
        self.version: int = version
        self.mascara: int = mascara
        self._modulos: array = modulos

    @property
    def size(self) -> int:
        """Alias en inglés de `lado` (módulos por lado)."""
        return self.lado

    def modulo(self, fila: int, col: int) -> int:
        """Devuelve el módulo en (fila, col): 1 si es oscuro, 0 si es claro."""
        if not (0 <= fila < self.lado and 0 <= col < self.lado):
            raise IndexError(f"módulo fuera de rango: ({fila}, {col})")
        return self._modulos[fila * self.lado + col]

    def __getitem__(self, pos: tuple[int, int]) -> int:
        fila, col = pos
        return self.modulo(fila, col)

    def modulos(self) -> array:
        """Devuelve el `array('B')` plano de módulos (referencia interna)."""
        return self._modulos

    def __repr__(self) -> str:
        return (
            f"MatrizQR(version={self.version}, lado={self.lado}, "
            f"mascara={self.mascara})"
        )


# --------------------------------------------------------------------------- #
# Codificación de datos (byte mode)
# --------------------------------------------------------------------------- #


def _elegir_version(n_bytes: int) -> int:
    """Menor versión 1..6 cuya capacidad de datos en nivel L admite `n_bytes`.

    El flujo de bits de una entrada en byte mode ocupa 4 bits de indicador de
    modo + 8 bits de contador de caracteres (versiones 1..9) + 8 bits por byte.

    Lanza `ValueError` documentado si ni la versión 6 tiene capacidad.
    """
    bits_necesarios = 4 + 8 + 8 * n_bytes
    for version in _VERSIONES:
        if bits_necesarios <= _DATOS_CW_L[version] * 8:
            return version
    maximo = _DATOS_CW_L[6] - 2  # descontando indicador + contador
    raise ValueError(
        f"la URL de {n_bytes} bytes excede la capacidad del QR versión 6 "
        f"nivel L (máximo {maximo} bytes en byte mode)"
    )


def _bits_de_datos(datos: bytes, version: int) -> list[int]:
    """Construye el flujo de bits (0/1) del segmento byte mode ya rellenado.

    Incluye indicador de modo, contador de caracteres, los bytes, el terminador,
    el relleno hasta el byte y los bytes de relleno alternos 0xEC/0x11 hasta
    completar la capacidad de datos de la versión.
    """
    capacidad = _DATOS_CW_L[version] * 8
    bits: list[int] = []
    _empujar_bits(bits, 0b0100, 4)          # indicador de modo: byte mode
    _empujar_bits(bits, len(datos), 8)      # contador (8 bits para v1..9)
    for byte in datos:
        _empujar_bits(bits, byte, 8)
    # Terminador: hasta 4 ceros, sin pasarse de la capacidad.
    _empujar_bits(bits, 0, min(4, capacidad - len(bits)))
    # Relleno hasta el borde de byte.
    if len(bits) % 8 != 0:
        _empujar_bits(bits, 0, 8 - (len(bits) % 8))
    # Bytes de relleno alternos.
    relleno = (0xEC, 0x11)
    indice = 0
    while len(bits) < capacidad:
        _empujar_bits(bits, relleno[indice & 1], 8)
        indice += 1
    return bits


def _empujar_bits(bits: list[int], valor: int, cantidad: int) -> None:
    """Añade los `cantidad` bits menos significativos de `valor` (MSB primero)."""
    for desplazamiento in range(cantidad - 1, -1, -1):
        bits.append((valor >> desplazamiento) & 1)


def _bits_a_codewords(bits: list[int]) -> list[int]:
    """Agrupa una lista de bits (múltiplo de 8) en codewords de 8 bits."""
    codewords: list[int] = []
    for i in range(0, len(bits), 8):
        valor = 0
        for j in range(8):
            valor = (valor << 1) | bits[i + j]
        codewords.append(valor)
    return codewords


def _intercalar(codewords: list[int], version: int) -> list[int]:
    """Divide en bloques, calcula corrección y entrelaza datos + corrección."""
    n_bloques = _BLOQUES_L[version]
    ec_por_bloque = _EC_CW_L[version]
    tam_bloque = len(codewords) // n_bloques

    bloques_datos: list[list[int]] = []
    bloques_ec: list[list[int]] = []
    divisor = _rs_divisor(ec_por_bloque)
    for b in range(n_bloques):
        datos = codewords[b * tam_bloque : (b + 1) * tam_bloque]
        bloques_datos.append(datos)
        bloques_ec.append(_rs_resto(datos, divisor))

    resultado: list[int] = []
    for i in range(tam_bloque):
        for datos in bloques_datos:
            resultado.append(datos[i])
    for i in range(ec_por_bloque):
        for ec in bloques_ec:
            resultado.append(ec[i])
    return resultado


def _codewords_a_bits(codewords: list[int]) -> list[int]:
    """Expande codewords a bits (MSB primero) para el llenado de la matriz."""
    bits: list[int] = []
    for cw in codewords:
        for desplazamiento in range(7, -1, -1):
            bits.append((cw >> desplazamiento) & 1)
    return bits


# --------------------------------------------------------------------------- #
# Construcción de la matriz: patrones de función
# --------------------------------------------------------------------------- #


class _Lienzo:
    """Matriz en construcción con seguimiento de módulos de función.

    `modulos` guarda 0/1; `funcion` marca con 1 los módulos de función
    (patrones y zona de formato) que no se rellenan con datos ni se enmascaran.
    """

    __slots__ = ("lado", "version", "modulos", "funcion")

    def __init__(self, version: int) -> None:
        self.version = version
        self.lado = _lado_de_version(version)
        n = self.lado * self.lado
        self.modulos = array("B", bytes(n))
        self.funcion = array("B", bytes(n))

    def _poner(self, fila: int, col: int, valor: int, *, funcion: bool) -> None:
        idx = fila * self.lado + col
        self.modulos[idx] = valor
        if funcion:
            self.funcion[idx] = 1

    def _dibujar_patrones_finder(self) -> None:
        """Dibuja los 3 patrones localizadores y sus separadores."""
        lado = self.lado
        for fila_base, col_base in ((0, 0), (0, lado - 7), (lado - 7, 0)):
            self._dibujar_un_finder(fila_base, col_base)

    def _dibujar_un_finder(self, fila_base: int, col_base: int) -> None:
        """Dibuja un finder 7x7 y el separador de 1 módulo a su alrededor."""
        lado = self.lado
        for df in range(-1, 8):
            for dc in range(-1, 8):
                fila = fila_base + df
                col = col_base + dc
                if not (0 <= fila < lado and 0 <= col < lado):
                    continue
                if -1 <= df <= 7 and -1 <= dc <= 7:
                    dentro = (0 <= df <= 6) and (0 <= dc <= 6)
                    if dentro:
                        borde = df in (0, 6) or dc in (0, 6)
                        centro = 2 <= df <= 4 and 2 <= dc <= 4
                        valor = 1 if (borde or centro) else 0
                    else:
                        valor = 0  # separador
                    self._poner(fila, col, valor, funcion=True)

    def _dibujar_timing(self) -> None:
        """Dibuja los patrones de temporización (fila 6 y columna 6)."""
        lado = self.lado
        for i in range(8, lado - 8):
            valor = 1 if i % 2 == 0 else 0
            self._poner(6, i, valor, funcion=True)
            self._poner(i, 6, valor, funcion=True)

    def _dibujar_alineacion(self) -> None:
        """Dibuja el único patrón de alineación central (versiones 2..6)."""
        centro = _ALIGN_CENTRO.get(self.version)
        if centro is None:
            return
        for df in range(-2, 3):
            for dc in range(-2, 3):
                anillo = max(abs(df), abs(dc))
                valor = 1 if anillo != 1 else 0
                self._poner(centro + df, centro + dc, valor, funcion=True)

    def _reservar_formato(self) -> None:
        """Reserva como función la zona de formato y el módulo oscuro fijo."""
        lado = self.lado
        for pos in _posiciones_formato(lado):
            fila, col = pos
            idx = fila * lado + col
            self.funcion[idx] = 1
        # Módulo oscuro fijo en (lado - 8, 8).
        self._poner(lado - 8, 8, 1, funcion=True)

    def dibujar_funcion(self) -> None:
        """Dibuja todos los patrones de función y reserva la zona de formato."""
        self._dibujar_patrones_finder()
        self._dibujar_timing()
        self._dibujar_alineacion()
        self._reservar_formato()

    def colocar_datos(self, bits: list[int]) -> None:
        """Coloca el flujo de bits en zigzag, saltando módulos de función."""
        lado = self.lado
        idx_bit = 0
        total = len(bits)
        hacia_arriba = True
        col = lado - 1
        while col > 0:
            if col == 6:  # la columna 6 es de temporización
                col -= 1
            for i in range(lado):
                fila = (lado - 1 - i) if hacia_arriba else i
                for c in (col, col - 1):
                    idx = fila * lado + c
                    if not self.funcion[idx]:
                        bit = bits[idx_bit] if idx_bit < total else 0
                        self.modulos[idx] = bit
                        idx_bit += 1
            hacia_arriba = not hacia_arriba
            col -= 2


def _posiciones_formato(lado: int) -> tuple[tuple[int, int], ...]:
    """Devuelve las 30 posiciones (fila, col) de los 15 bits de formato x2."""
    pos: list[tuple[int, int]] = []
    # Primera copia (alrededor del finder superior izquierdo).
    for i in range(6):
        pos.append((i, 8))
    pos.append((7, 8))
    pos.append((8, 8))
    pos.append((8, 7))
    for i in range(9, 15):
        pos.append((8, 14 - i))
    # Segunda copia (bajo el finder superior derecho y a la derecha del inferior).
    for i in range(8):
        pos.append((lado - 1 - i, 8))
    for i in range(8, 15):
        pos.append((8, lado - 15 + i))
    return tuple(pos)


# --------------------------------------------------------------------------- #
# Información de formato (nivel L + máscara) con BCH
# --------------------------------------------------------------------------- #


def _bits_formato(mascara: int) -> int:
    """Calcula los 15 bits de información de formato para nivel L y `mascara`."""
    datos = (_NIVEL_L << 3) | mascara  # 5 bits: 2 de nivel + 3 de máscara
    codigo = datos << 10
    for i in range(4, -1, -1):
        if (codigo >> (i + 10)) & 1:
            codigo ^= _FORMATO_BCH << i
    return ((datos << 10) | codigo) ^ _FORMATO_XOR


def _dibujar_formato(lienzo: _Lienzo, mascara: int) -> None:
    """Escribe los 15 bits de formato en sus dos copias de la matriz."""
    formato = _bits_formato(mascara)
    bits = [(formato >> i) & 1 for i in range(15)]
    lado = lienzo.lado
    posiciones = _posiciones_formato(lado)
    # Las 30 posiciones son 15 de la primera copia y 15 de la segunda.
    for k, (fila, col) in enumerate(posiciones):
        bit = bits[k % 15]
        lienzo.modulos[fila * lado + col] = bit


# --------------------------------------------------------------------------- #
# Máscaras y penalización
# --------------------------------------------------------------------------- #


def _condicion_mascara(mascara: int, fila: int, col: int) -> bool:
    """Evalúa la condición de la `mascara` (0..7) en (fila, col)."""
    if mascara == 0:
        return (fila + col) % 2 == 0
    if mascara == 1:
        return fila % 2 == 0
    if mascara == 2:
        return col % 3 == 0
    if mascara == 3:
        return (fila + col) % 3 == 0
    if mascara == 4:
        return (fila // 2 + col // 3) % 2 == 0
    if mascara == 5:
        return (fila * col) % 2 + (fila * col) % 3 == 0
    if mascara == 6:
        return ((fila * col) % 2 + (fila * col) % 3) % 2 == 0
    if mascara == 7:
        return ((fila + col) % 2 + (fila * col) % 3) % 2 == 0
    raise ValueError(f"máscara inválida: {mascara}")


def _aplicar_mascara(lienzo: _Lienzo, mascara: int) -> None:
    """Aplica (XOR) la máscara a los módulos de datos (no de función)."""
    lado = lienzo.lado
    modulos = lienzo.modulos
    funcion = lienzo.funcion
    for fila in range(lado):
        base = fila * lado
        for col in range(lado):
            idx = base + col
            if not funcion[idx] and _condicion_mascara(mascara, fila, col):
                modulos[idx] ^= 1


def _penalizacion(lienzo: _Lienzo) -> int:
    """Calcula la penalización total de la matriz según las cuatro reglas."""
    lado = lienzo.lado
    modulos = lienzo.modulos

    def en(fila: int, col: int) -> int:
        return modulos[fila * lado + col]

    total = 0

    # Regla 1: rachas de 5+ módulos del mismo color en filas y columnas.
    for fila in range(lado):
        total += _penaliza_racha(en, fila, lado, por_fila=True)
    for col in range(lado):
        total += _penaliza_racha(en, col, lado, por_fila=False)

    # Regla 2: bloques 2x2 del mismo color.
    for fila in range(lado - 1):
        for col in range(lado - 1):
            v = en(fila, col)
            if (
                en(fila, col + 1) == v
                and en(fila + 1, col) == v
                and en(fila + 1, col + 1) == v
            ):
                total += 3

    # Regla 3: patrón tipo finder 1:1:3:1:1 con 4 claros a un lado.
    patron_a = (1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0)
    patron_b = (0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1)
    for fila in range(lado):
        for col in range(lado - 10):
            ventana = tuple(en(fila, col + k) for k in range(11))
            if ventana == patron_a or ventana == patron_b:
                total += 40
    for col in range(lado):
        for fila in range(lado - 10):
            ventana = tuple(en(fila + k, col) for k in range(11))
            if ventana == patron_a or ventana == patron_b:
                total += 40

    # Regla 4: desviación de la proporción de módulos oscuros respecto al 50%.
    oscuros = sum(modulos)
    n = lado * lado
    ratio = oscuros * 100.0 / n
    bajo = int(ratio // 5) * 5
    alto = bajo + 5
    desviacion = min(abs(bajo - 50), abs(alto - 50))
    total += (desviacion // 5) * 10

    return total


def _penaliza_racha(en, indice: int, lado: int, *, por_fila: bool) -> int:
    """Penalización de rachas de 5+ en una fila o columna completa."""
    total = 0
    anterior = -1
    racha = 0
    for j in range(lado):
        valor = en(indice, j) if por_fila else en(j, indice)
        if valor == anterior:
            racha += 1
        else:
            if racha >= 5:
                total += 3 + (racha - 5)
            anterior = valor
            racha = 1
    if racha >= 5:
        total += 3 + (racha - 5)
    return total


# --------------------------------------------------------------------------- #
# Codificación completa y caché por URL
# --------------------------------------------------------------------------- #

#: Caché en memoria de matrices ya codificadas, indexada por URL.
_CACHE: dict[str, MatrizQR] = {}


def _codificar_sin_cache(url: str) -> MatrizQR:
    """Codifica `url` en una `MatrizQR` eligiendo la mejor máscara."""
    datos = url.encode("utf-8")
    version = _elegir_version(len(datos))

    bits = _bits_de_datos(datos, version)
    codewords = _bits_a_codewords(bits)
    intercalados = _intercalar(codewords, version)
    bits_finales = _codewords_a_bits(intercalados)

    base = _Lienzo(version)
    base.dibujar_funcion()
    base.colocar_datos(bits_finales)

    mejor_mascara = 0
    mejor_penalizacion = -1
    mejor_modulos: array | None = None
    for mascara in range(8):
        candidato = _Lienzo(version)
        candidato.funcion = array("B", base.funcion)
        candidato.modulos = array("B", base.modulos)
        _aplicar_mascara(candidato, mascara)
        _dibujar_formato(candidato, mascara)
        pen = _penalizacion(candidato)
        if mejor_penalizacion < 0 or pen < mejor_penalizacion:
            mejor_penalizacion = pen
            mejor_mascara = mascara
            mejor_modulos = candidato.modulos

    if mejor_modulos is None:  # invariante: siempre hay 8 máscaras
        raise ValueError("no se pudo seleccionar una máscara")

    return MatrizQR(base.lado, version, mejor_mascara, mejor_modulos)


def codificar(url: str) -> MatrizQR:
    """Codifica una URL en un código QR y devuelve su `MatrizQR`.

    Reutiliza la caché por URL: la primera llamada codifica y guarda el
    resultado; las siguientes con la misma URL devuelven la misma matriz sin
    recodificar. Lanza `ValueError` si `url` no es `str` o si excede la
    capacidad de la versión 6 en nivel L.
    """
    if not isinstance(url, str):
        raise ValueError(f"la URL debe ser str, no {type(url).__name__}")
    cacheada = _CACHE.get(url)
    if cacheada is not None:
        return cacheada
    matriz = _codificar_sin_cache(url)
    _CACHE[url] = matriz
    return matriz


def limpiar_cache() -> None:
    """Vacía la caché de matrices por URL (útil en pruebas y mediciones)."""
    _CACHE.clear()
