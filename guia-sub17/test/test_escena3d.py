# -*- coding: utf-8 -*-
"""Pruebas del motor de escena 3D propia (src/guia/escena3d.py)."""
import json
import math
import unittest

from guia.escena3d import (
    PRESUPUESTO_VERTICES,
    GrupoMalla,
    MallaEscena,
    escena_hero,
    serializar_escena,
)


class TestEscenaHero(unittest.TestCase):
    """Pruebas sobre la escena del hero (jugadora + balón + piso)."""

    def setUp(self):
        self.escena = escena_hero()

    def test_escena_no_vacia(self):
        """La escena tiene al menos un grupo con vértices."""
        self.assertGreater(len(self.escena.grupos), 0)
        total = self.escena.vertices_totales()
        self.assertGreater(total, 0)

    def test_presupuesto_vertices(self):
        """La escena respeta el presupuesto de vértices."""
        total = self.escena.vertices_totales()
        self.assertLess(
            total,
            PRESUPUESTO_VERTICES,
            f"La escena excede el presupuesto: {total} >= {PRESUPUESTO_VERTICES}",
        )

    def test_grupos_obligatorios(self):
        """La escena contiene los grupos 'jugadora', 'balon' y 'piso'."""
        nombres = {g.nombre for g in self.escena.grupos}
        self.assertIn("jugadora", nombres)
        self.assertIn("balon", nombres)
        self.assertIn("piso", nombres)

    def test_grupo_jugadora_no_vacio(self):
        """El grupo 'jugadora' tiene vértices y aristas."""
        jugadora = self.escena.grupo("jugadora")
        self.assertIsNotNone(jugadora)
        self.assertGreater(len(jugadora.vertices), 0)
        self.assertGreater(len(jugadora.indices), 0)

    def test_grupo_balon_no_vacio(self):
        """El grupo 'balon' tiene vértices y aristas."""
        balon = self.escena.grupo("balon")
        self.assertIsNotNone(balon)
        self.assertGreater(len(balon.vertices), 0)
        self.assertGreater(len(balon.indices), 0)

    def test_coordenadas_finitas(self):
        """Todas las coordenadas son finitas (no inf, no nan)."""
        for grupo in self.escena.grupos:
            for x, y, z in grupo.vertices:
                self.assertTrue(math.isfinite(x), f"x={x} no es finito en {grupo.nombre}")
                self.assertTrue(math.isfinite(y), f"y={y} no es finito en {grupo.nombre}")
                self.assertTrue(math.isfinite(z), f"z={z} no es finito en {grupo.nombre}")

    def test_indices_en_rango(self):
        """Todos los índices están en rango [0, len(vertices))."""
        for grupo in self.escena.grupos:
            n = len(grupo.vertices)
            for a, b in grupo.indices:
                self.assertGreaterEqual(a, 0, f"Índice {a} < 0 en {grupo.nombre}")
                self.assertLess(a, n, f"Índice {a} >= {n} en {grupo.nombre}")
                self.assertGreaterEqual(b, 0, f"Índice {b} < 0 en {grupo.nombre}")
                self.assertLess(b, n, f"Índice {b} >= {n} en {grupo.nombre}")

    def test_escena_hashable(self):
        """MallaEscena y GrupoMalla son hashables (frozen dataclass)."""
        _ = hash(self.escena)
        for grupo in self.escena.grupos:
            _ = hash(grupo)

    def test_serializacion_determinista(self):
        """La serialización JSON es determinista (mismo resultado cada vez)."""
        j1 = serializar_escena(self.escena)
        j2 = serializar_escena(self.escena)
        self.assertEqual(j1, j2)

    def test_serializacion_json_valido(self):
        """La serialización produce JSON válido."""
        j = serializar_escena(self.escena)
        obj = json.loads(j)
        self.assertIn("grupos", obj)
        self.assertIsInstance(obj["grupos"], list)

    def test_serializacion_compacta(self):
        """La serialización no contiene espacios innecesarios."""
        j = serializar_escena(self.escena)
        # separators=(',', ':') elimina espacios después de comas y dos puntos
        self.assertNotIn(", ", j)
        self.assertNotIn(": ", j)

    def test_coordenadas_redondeadas(self):
        """Las coordenadas se redondean a 4 decimales en la serialización."""
        j = serializar_escena(self.escena)
        obj = json.loads(j)
        for grupo in obj["grupos"]:
            for v in grupo["vertices"]:
                for coord in v:
                    # Verificar que no hay más de 4 decimales
                    s = str(coord)
                    if "." in s:
                        decimales = len(s.split(".")[1])
                        self.assertLessEqual(decimales, 4, f"Coordenada {coord} tiene más de 4 decimales")

    def test_grupo_metodo_devuelve_correcto(self):
        """El método grupo(...) devuelve el grupo correcto o None."""
        jugadora = self.escena.grupo("jugadora")
        self.assertIsNotNone(jugadora)
        self.assertEqual(jugadora.nombre, "jugadora")

        inexistente = self.escena.grupo("inexistente")
        self.assertIsNone(inexistente)

    def test_balon_elevado(self):
        """El balón está elevado (todas sus coordenadas Y > 0)."""
        balon = self.escena.grupo("balon")
        self.assertIsNotNone(balon)
        for x, y, z in balon.vertices:
            self.assertGreater(y, 0.0, f"Vértice del balón ({x},{y},{z}) tiene y <= 0")

    def test_piso_en_plano_y_cero(self):
        """Todos los vértices del piso tienen Y ≈ 0."""
        piso = self.escena.grupo("piso")
        self.assertIsNotNone(piso)
        for x, y, z in piso.vertices:
            self.assertAlmostEqual(y, 0.0, places=6, msg=f"Vértice del piso ({x},{y},{z}) no está en Y=0")


if __name__ == "__main__":
    unittest.main()
