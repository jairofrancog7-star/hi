# -*- coding: utf-8 -*-
"""Motor de escena 3D propia para el visor interactivo del sitio de un archivo.

Genera geometría de futbol femenil (jugadora + balón + piso) en Python, testeable
con unittest, y la serializa como JSON compacto para el visor JS vanilla del hero.

Decisión de arquitectura (usuario, 2026-08-08): visor 3D propio, offline, cero CDN,
cero dependencias externas. La geometría se calcula aquí; el JS solo proyecta y
dibuja sobre Canvas 2D.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Literal

__all__ = [
    "MallaEscena",
    "GrupoMalla",
    "escena_hero",
    "serializar_escena",
    "datos_json",
    "svg_estatico",
    "ETIQUETA_ACCESIBLE",
    "NOMBRES_GRUPOS",
]

# Presupuesto de vertices (Req 34.1): menos de 1200 vértices totales
PRESUPUESTO_VERTICES = 1200

#: Nombres de los grupos de malla en la escena (jugadora, balón, piso).
NOMBRES_GRUPOS: tuple[str, ...] = ("jugadora", "balon", "piso")

#: Etiqueta accesible del canvas (atributo `aria-label` del hero).
ETIQUETA_ACCESIBLE: str = (
    "Modelo 3D interactivo de jugadora de futbol femenil golpeando el balon"
)


@dataclass(frozen=True, slots=True)
class GrupoMalla:
    """Grupo nombrado de vértices e índices (submalla de la escena)."""

    nombre: str
    vertices: tuple[tuple[float, float, float], ...]  # (x, y, z)
    indices: tuple[tuple[int, int], ...]  # aristas como pares de índices


@dataclass(frozen=True, slots=True)
class MallaEscena:
    """Escena 3D con grupos de geometría."""

    grupos: tuple[GrupoMalla, ...]

    def vertices_totales(self) -> int:
        """Cuenta total de vértices en la escena."""
        return sum(len(g.vertices) for g in self.grupos)

    def grupo(self, nombre: str) -> GrupoMalla | None:
        """Devuelve el grupo con ese nombre o None."""
        for g in self.grupos:
            if g.nombre == nombre:
                return g
        return None


def escena_hero() -> MallaEscena:
    """Construye la escena del hero: jugadora + balón + piso.

    Geometría de futbol femenil: silueta esquemática de jugadora en movimiento
    golpeando el balón (figura de palo articulada con postura dinámica), balón
    como icosaedro subdividido una vez (esfera geodésica de baja densidad), y
    retícula de piso centrada en el origen.
    """
    # --- Balón (esfera geodésica) ---
    # Icosaedro subdividido 1 vez ≈ 42 vértices, 120 aristas
    balon_verts, balon_edges = _esfera_geodesica(radio=0.35, subdiv=1)
    balon_verts = tuple((x, y + 1.2, z) for x, y, z in balon_verts)  # elevar
    balon = GrupoMalla("balon", balon_verts, balon_edges)

    # --- Jugadora (figura de palo articulada) ---
    # Postura: golpeando el balón con interior (pierna de golpeo extendida hacia
    # el balón, pierna de apoyo semiflexionada, torso inclinado, brazos abiertos
    # para equilibrio). Escala: cabeza ~1.65m del piso (percentil femenino U-17).
    jugadora = _silueta_jugadora()

    # --- Piso (retícula) ---
    piso = _reticula_piso(ancho=6.0, largo=6.0, paso=0.5)

    escena = MallaEscena(grupos=(jugadora, balon, piso))
    if escena.vertices_totales() >= PRESUPUESTO_VERTICES:
        raise ValueError(
            f"La escena excede el presupuesto: "
            f"{escena.vertices_totales()} >= {PRESUPUESTO_VERTICES} vértices"
        )
    return escena


def serializar_escena(escena: MallaEscena) -> str:
    """Serializa la escena como JSON compacto y determinista.

    Redondea coordenadas a 4 decimales, sin espacios, orden garantizado.
    """
    obj = {
        "grupos": [
            {
                "nombre": g.nombre,
                "vertices": [
                    [round(x, 4), round(y, 4), round(z, 4)] for x, y, z in g.vertices
                ],
                "indices": [[a, b] for a, b in g.indices],
            }
            for g in escena.grupos
        ]
    }
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False, sort_keys=True)


# ============================================================================
# Construcción de geometría
# ============================================================================


def _silueta_jugadora() -> GrupoMalla:
    """Figura de palo articulada: golpeando balón con interior del pie derecho.

    Postura dinámica: pierna izquierda (apoyo) semiflexionada, derecha extendida
    hacia el balón a ~1.2m de altura, torso inclinado hacia adelante y a la
    izquierda, brazos abiertos. Escala: cabeza ~1.65m (percentil femenino U-17).
    """
    # Origen: centro de masa de la jugadora en (0, 0, 0)
    # Eje Y: vertical hacia arriba; X: lateral (derecha +); Z: frontal (atrás +)

    # --- Pierna de apoyo (izquierda): semiflexionada ---
    cadera_izq = (-0.12, 0.85, 0.0)
    rodilla_izq = (-0.14, 0.45, 0.05)
    tobillo_izq = (-0.13, 0.08, 0.0)
    pie_izq = (-0.10, 0.0, 0.08)

    # --- Pierna de golpeo (derecha): extendida hacia el balón ---
    cadera_der = (0.12, 0.85, 0.0)
    rodilla_der = (0.28, 1.05, -0.15)
    tobillo_der = (0.40, 1.18, -0.25)
    pie_der = (0.45, 1.20, -0.30)  # casi tocando el balón (y=1.2)

    # --- Torso y cabeza ---
    centro_cadera = (0.0, 0.85, 0.0)
    centro_hombros = (-0.05, 1.35, 0.1)  # inclinado adelante y a la izquierda
    cuello = (-0.05, 1.50, 0.12)
    cabeza = (-0.05, 1.65, 0.12)

    # --- Brazos (abiertos para equilibrio) ---
    hombro_izq = (-0.20, 1.35, 0.1)
    codo_izq = (-0.40, 1.20, 0.05)
    mano_izq = (-0.55, 1.10, 0.0)

    hombro_der = (0.10, 1.35, 0.1)
    codo_der = (0.30, 1.25, 0.15)
    mano_der = (0.48, 1.18, 0.20)

    verts = (
        cadera_izq,
        rodilla_izq,
        tobillo_izq,
        pie_izq,
        cadera_der,
        rodilla_der,
        tobillo_der,
        pie_der,
        centro_cadera,
        centro_hombros,
        cuello,
        cabeza,
        hombro_izq,
        codo_izq,
        mano_izq,
        hombro_der,
        codo_der,
        mano_der,
    )

    # Aristas: esqueleto articulado
    edges = (
        # Pierna izquierda
        (0, 1),
        (1, 2),
        (2, 3),
        # Pierna derecha
        (4, 5),
        (5, 6),
        (6, 7),
        # Cadera -> hombros -> cuello -> cabeza
        (8, 0),  # cadera central -> cadera izq
        (8, 4),  # cadera central -> cadera der
        (8, 9),  # cadera -> hombros
        (9, 10),  # hombros -> cuello
        (10, 11),  # cuello -> cabeza
        # Brazo izquierdo
        (9, 12),  # hombros -> hombro izq
        (12, 13),
        (13, 14),
        # Brazo derecho
        (9, 15),  # hombros -> hombro der
        (15, 16),
        (16, 17),
    )

    return GrupoMalla("jugadora", verts, edges)


def _esfera_geodesica(
    radio: float, subdiv: int
) -> tuple[tuple[tuple[float, float, float], ...], tuple[tuple[int, int], ...]]:
    """Esfera geodésica: icosaedro subdividido.

    Args:
        radio: Radio de la esfera
        subdiv: Nivel de subdivisión (0=icosaedro, 1≈42 verts, 2≈162 verts)

    Returns:
        (vértices, aristas) con coordenadas en la esfera de radio dado
    """
    # Icosaedro base (12 vértices)
    phi = (1.0 + math.sqrt(5.0)) / 2.0  # razón áurea
    a = 1.0 / math.sqrt(1.0 + phi * phi)
    b = phi * a

    verts_base = [
        (0, a, b),
        (0, a, -b),
        (0, -a, b),
        (0, -a, -b),
        (a, b, 0),
        (a, -b, 0),
        (-a, b, 0),
        (-a, -b, 0),
        (b, 0, a),
        (-b, 0, a),
        (b, 0, -a),
        (-b, 0, -a),
    ]

    # 20 caras (triángulos)
    caras = [
        (0, 2, 8),
        (0, 8, 4),
        (0, 4, 6),
        (0, 6, 9),
        (0, 9, 2),
        (2, 9, 7),
        (2, 7, 5),
        (2, 5, 8),
        (8, 5, 10),
        (8, 10, 4),
        (4, 10, 1),
        (4, 1, 6),
        (6, 1, 11),
        (6, 11, 9),
        (9, 11, 7),
        (3, 7, 11),
        (3, 11, 1),
        (3, 1, 10),
        (3, 10, 5),
        (3, 5, 7),
    ]

    # Subdivisión por punto medio
    vertices = list(verts_base)
    caras_sub = list(caras)

    for _ in range(subdiv):
        nuevas_caras = []
        cache_aristas = {}  # (i, j) -> índice del punto medio

        for a, b, c in caras_sub:
            # Punto medio de cada arista
            ab = _punto_medio_en_esfera(vertices, a, b, cache_aristas)
            bc = _punto_medio_en_esfera(vertices, b, c, cache_aristas)
            ca = _punto_medio_en_esfera(vertices, c, a, cache_aristas)

            # 4 triángulos nuevos
            nuevas_caras.append((a, ab, ca))
            nuevas_caras.append((b, bc, ab))
            nuevas_caras.append((c, ca, bc))
            nuevas_caras.append((ab, bc, ca))

        caras_sub = nuevas_caras

    # Escalar a radio pedido
    verts_finales = tuple(
        (x * radio, y * radio, z * radio) for x, y, z in vertices
    )

    # Aristas: extraer de las caras (sin duplicados)
    aristas_set = set()
    for a, b, c in caras_sub:
        aristas_set.add((min(a, b), max(a, b)))
        aristas_set.add((min(b, c), max(b, c)))
        aristas_set.add((min(c, a), max(c, a)))

    aristas_finales = tuple(sorted(aristas_set))

    return verts_finales, aristas_finales


def _punto_medio_en_esfera(
    vertices: list[tuple[float, float, float]],
    i: int,
    j: int,
    cache: dict[tuple[int, int], int],
) -> int:
    """Devuelve el índice del punto medio entre vertices[i] y vertices[j],
    proyectado a la esfera unitaria. Usa caché para evitar duplicados.
    """
    llave = (min(i, j), max(i, j))
    if llave in cache:
        return cache[llave]

    x1, y1, z1 = vertices[i]
    x2, y2, z2 = vertices[j]
    mx = (x1 + x2) / 2.0
    my = (y1 + y2) / 2.0
    mz = (z1 + z2) / 2.0

    # Proyectar a la esfera unitaria
    longitud = math.sqrt(mx * mx + my * my + mz * mz)
    if longitud < 1e-9:
        raise ValueError("Punto medio en el origen, no se puede proyectar")
    mx /= longitud
    my /= longitud
    mz /= longitud

    idx = len(vertices)
    vertices.append((mx, my, mz))
    cache[llave] = idx
    return idx


def _reticula_piso(ancho: float, largo: float, paso: float) -> GrupoMalla:
    """Retícula de piso centrada en (0, 0, 0) en el plano Y=0.

    Args:
        ancho: Extensión en X (de -ancho/2 a +ancho/2)
        largo: Extensión en Z (de -largo/2 a +largo/2)
        paso: Separación entre líneas

    Returns:
        GrupoMalla con líneas horizontales y verticales del piso
    """
    verts = []
    edges = []

    mitad_x = ancho / 2.0
    mitad_z = largo / 2.0

    # Líneas paralelas al eje Z (van de -Z/2 a +Z/2, cada una en su X)
    x = -mitad_x
    while x <= mitad_x + 1e-6:
        i0 = len(verts)
        verts.append((x, 0.0, -mitad_z))
        verts.append((x, 0.0, mitad_z))
        edges.append((i0, i0 + 1))
        x += paso

    # Líneas paralelas al eje X (van de -X/2 a +X/2, cada una en su Z)
    z = -mitad_z
    while z <= mitad_z + 1e-6:
        i0 = len(verts)
        verts.append((-mitad_x, 0.0, z))
        verts.append((mitad_x, 0.0, z))
        edges.append((i0, i0 + 1))
        z += paso

    return GrupoMalla("piso", tuple(verts), tuple(edges))



# ============================================================================
# Serialización compacta para el visor JS
# ============================================================================


def datos_json() -> str:
    """Datos de la escena en formato JSON compacto para el visor JavaScript.

    Devuelve un objeto con tres listas planas:
    - v: vértices aplanados [x0,y0,z0,x1,y1,z1,...]
    - a: aristas aplanadas [i0,j0,i1,j1,...]
    - g: grupos como [nombre,offset_verts,num_verts,offset_aristas,num_aristas,grosor,brillo]

    El visor deserializa esto en arreglos tipados Float32Array/Int32Array sin
    crear ni un objeto por fotograma.
    """
    escena = escena_hero()

    # Aplanar vértices
    verts_planos = []
    for grupo in escena.grupos:
        for x, y, z in grupo.vertices:
            verts_planos.extend([round(x, 4), round(y, 4), round(z, 4)])

    # Aplanar aristas (reasignar índices a la lista global)
    aristas_planas = []
    offset_v = 0
    offset_a = 0
    grupos_meta = []

    # Grosor y brillo por grupo (jugadora: línea fina y brillo moderado;
    # balón: línea media y brillo alto; piso: línea muy fina y brillo bajo)
    GROSOR = {"jugadora": 2.2, "balon": 1.8, "piso": 0.8}
    BRILLO = {"jugadora": 0.92, "balon": 1.0, "piso": 0.45}

    for grupo in escena.grupos:
        nv = len(grupo.vertices)
        na = len(grupo.indices)

        for i, j in grupo.indices:
            aristas_planas.extend([offset_v + i, offset_v + j])

        grosor = GROSOR.get(grupo.nombre, 1.0)
        brillo = BRILLO.get(grupo.nombre, 0.8)

        grupos_meta.append(
            [
                grupo.nombre,
                offset_v,
                nv,
                offset_a,
                offset_a + na,
                round(grosor, 2),
                round(brillo, 2),
            ]
        )

        offset_v += nv
        offset_a += na

    obj = {"v": verts_planos, "a": aristas_planas, "g": grupos_meta}
    return json.dumps(obj, separators=(",", ":"))


def svg_estatico() -> str:
    """SVG estático de reserva para el hero (mejora progresiva).

    Este dibujo se muestra cuando JavaScript está deshabilitado o mientras el
    visor se inicializa. Una vez que el canvas está listo, el JS oculta esta
    reserva y destapa el canvas. Es un render 2D isométrico simple de la jugadora
    y el balón, sin animación.

    Returns:
        Cadena con el SVG inline completo (con viewBox, role, title).
    """
    escena = escena_hero()
    jugadora = escena.grupo("jugadora")
    balon = escena.grupo("balon")

    if not jugadora or not balon:
        return ""

    # Proyección isométrica simple (yaw=-0.62, pitch=0.2, sin zoom)
    cy = math.cos(-0.62)
    sy = math.sin(-0.62)
    cp = math.cos(0.2)
    sp = math.sin(0.2)

    def proyectar(x: float, y: float, z: float) -> tuple[float, float]:
        x1 = x * cy + z * sy
        z1 = z * cy - x * sy
        y1 = y * cp - z1 * sp
        # Escala fija para que quepa en 100x100
        return (50 + x1 * 35, 50 - y1 * 35)

    lineas = []

    # Dibujar jugadora
    for i, j in jugadora.indices:
        x0, y0, z0 = jugadora.vertices[i]
        x1, y1, z1 = jugadora.vertices[j]
        px0, py0 = proyectar(x0, y0, z0)
        px1, py1 = proyectar(x1, y1, z1)
        lineas.append(
            f'<line x1="{round(px0,2)}" y1="{round(py0,2)}" '
            f'x2="{round(px1,2)}" y2="{round(py1,2)}" '
            f'stroke="#3BE8F0" stroke-width="2.2" stroke-linecap="round"/>'
        )

    # Dibujar balón
    for i, j in balon.indices:
        x0, y0, z0 = balon.vertices[i]
        x1, y1, z1 = balon.vertices[j]
        px0, py0 = proyectar(x0, y0, z0)
        px1, py1 = proyectar(x1, y1, z1)
        lineas.append(
            f'<line x1="{round(px0,2)}" y1="{round(py0,2)}" '
            f'x2="{round(px1,2)}" y2="{round(py1,2)}" '
            f'stroke="#3BE8F0" stroke-width="1.8" stroke-linecap="round" opacity="0.9"/>'
        )

    return (
        '<svg class="hero-svg" viewBox="0 0 100 100" role="img" xmlns="http://www.w3.org/2000/svg">'
        f"<title>{ETIQUETA_ACCESIBLE}</title>"
        f"<desc>Vista estatica del modelo 3D de futbol femenil</desc>"
        f"{''.join(lineas)}"
        "</svg>"
    )
