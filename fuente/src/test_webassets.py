# -*- coding: utf-8 -*-
"""Pruebas de los SVG autónomos usados por la versión web offline."""

import unittest
from pathlib import Path
import sys
from urllib.parse import unquote

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import content as C
import webassets as assets


def decoded_svg(uri):
    prefix = 'data:image/svg+xml,'
    if not uri.startswith(prefix):
        raise AssertionError('prefijo data:image/svg+xml inesperado')
    return unquote(uri[len(prefix):])


class WebAssetsTest(unittest.TestCase):
    def test_fifteen_diagrams_are_compact_and_self_contained(self):
        uris = []
        used_items = set()
        used_kinds = set()
        for drill in C.DRILLS:
            spec = C.D[drill['dia']]
            used_kinds.add(spec['kind'])
            used_items.update(item[0] for item in spec['items'])
            uri = assets.diagram_data_uri(spec, drill['title'])
            svg = decoded_svg(uri)

            self.assertTrue(svg.startswith('<svg'))
            self.assertTrue(svg.endswith('</svg>'))
            self.assertIn('<title id="title">', svg)
            self.assertNotIn('<script', svg.lower())
            self.assertNotIn('<image', svg.lower())
            self.assertNotIn(' href=', svg.lower())
            self.assertLess(len(uri), 12_000)
            image_width, image_height = assets.diagram_dimensions(spec)
            self.assertEqual(960, image_width)
            self.assertGreaterEqual(image_height, 180)
            self.assertIn('width="%d" height="%d"' % (image_width, image_height), svg)
            # Los caracteres que pueden romper un atributo HTML están codificados.
            payload = uri.split(',', 1)[1]
            for unsafe in ('<', '>', '"', "'", '#', '&'):
                self.assertNotIn(unsafe, payload)
            self.assertNotIn(' ', payload)
            uris.append(uri)

        self.assertEqual(15, len(uris))
        self.assertLess(sum(map(len, uris)), 100_000)
        self.assertEqual({'blank', 'grid', 'half', 'own', 'wall'}, used_kinds)
        self.assertEqual(
            {'b', 'boot', 'c', 'drib', 'gk', 'mark', 'p', 'pass', 'r', 'run',
             'shot', 't', 'target', 'zone'},
            used_items,
        )

    def test_fifteen_qr_have_quiet_zone_and_stay_compact(self):
        uris = []
        for drill in C.DRILLS:
            uri = assets.qr_data_uri(drill['qr'], 'QR · ' + drill['title'])
            svg = decoded_svg(uri)
            self.assertIn('shape-rendering="crispEdges"', svg)
            self.assertIn('<rect width=', svg)
            self.assertIn('fill="#fff"', svg)
            self.assertIn('<path d="', svg)
            self.assertNotIn(';base64,', uri)
            self.assertLess(len(uri), 9_000)
            self.assertNotIn(' ', uri.split(',', 1)[1])
            uris.append(uri)

        self.assertEqual(15, len(uris))
        self.assertLess(sum(map(len, uris)), 75_000)

    def test_labels_are_xml_escaped_before_uri_encoding(self):
        svg = decoded_svg(assets.diagram_data_uri(
            C.D[C.DRILLS[0]['dia']], 'A & "B" <C>'
        ))
        self.assertIn('A &amp; &quot;B&quot; &lt;C&gt;', svg)

    def test_invalid_specs_fail_with_a_clear_message(self):
        with self.assertRaisesRegex(ValueError, 'faltan campos'):
            assets.diagram_data_uri({'kind': 'grid'})
        with self.assertRaisesRegex(ValueError, 'no compatible'):
            assets.diagram_data_uri({'kind': 'video', 'w': 1, 'h': 1, 'items': []})


if __name__ == '__main__':
    unittest.main()
