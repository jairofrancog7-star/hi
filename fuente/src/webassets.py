# -*- coding: utf-8 -*-
"""Activos SVG autónomos para la guía web offline.

El módulo transforma los diagramas declarativos de :mod:`content` y las
matrices QR de :mod:`pdfkit` en URI ``data:image/svg+xml``.  No usa fuentes,
imágenes, JavaScript ni servicios externos.  Las URI resultantes se pueden
asignar directamente a ``src`` de un ``<img loading="lazy">``.

Se usa codificación porcentual en vez de Base64: conserva todos los caracteres
que podrían interferir con un atributo HTML correctamente escapados y produce
activos sensiblemente más pequeños para este tipo de SVG repetitivo.
"""

from html import escape
import math
from urllib.parse import quote

try:  # El proyecto ejecuta los módulos tanto sueltos como desde ``fuente.src``.
    from . import pdfkit as pk
except ImportError:  # pragma: no cover - ruta usada por build.py y las pruebas
    import pdfkit as pk


__all__ = (
    'diagram_dimensions', 'diagram_svg', 'diagram_data_uri',
    'qr_svg', 'qr_data_uri',
)


# Paleta compartida con la edición impresa y la web.
SKY = '#bfe9ff'
GRASS = '#2f8f57'
GRASS_ALT = '#2a8250'
FIELD_LINE = '#ffffff'
INK = '#102a3a'
BLUE = '#0b6fa4'
BLUE_DARK = '#06496e'
PINK = '#a52357'
PINK_SOFT = '#ffe3ed'
YELLOW = '#ffd23f'
ORANGE = '#ff9800'

_KINDS = {'blank', 'wall', 'grid', 'half', 'own', 'full'}
_ITEMS = {
    'zone', 'poly', 'target', 'run', 'pass', 'shot', 'drib', 'seg',
    'c', 'boot', 'mark', 'p', 'gk', 'r', 'b', 't',
}


def _n(value):
    """Número SVG corto y estable, con precisión suficiente para los dibujos."""
    result = ('%.2f' % float(value)).rstrip('0').rstrip('.')
    return '0' if result in ('', '-0') else result


def _xml(value):
    return escape(str(value), quote=True)


def _data_uri(svg):
    # No se dejan ``<``, ``>``, comillas, ``#`` ni ``&`` sin codificar: la URI
    # se puede insertar en un atributo HTML entre comillas sin una segunda
    # transformación y sin que ``#`` se interprete como fragmento de la URL.
    encoded = quote(svg, safe='/:;,+-._~()=')
    return 'data:image/svg+xml,' + encoded


def _point(height, x, y):
    """Convierte el origen inferior izquierdo del spec al origen superior SVG."""
    return float(x), float(height) - float(y)


def _line(parts, a, b, color, width, extra=''):
    parts.append(
        '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" '
        'stroke-width="%s"%s/>'
        % (_n(a[0]), _n(a[1]), _n(b[0]), _n(b[1]), color, _n(width), extra)
    )


def _chip(parts, cx, cy, text, size, align, max_width):
    """Etiqueta compacta, legible y contenida en el ancho del diagrama."""
    text = str(text)
    font_size = max(.86, float(size))
    pad_x = font_size * .48
    height = font_size * 1.72
    estimated_text = max(font_size * 1.5, len(text) * font_size * .56)
    inner_limit = max(font_size * 2, float(max_width) - pad_x * 2)
    text_width = min(estimated_text, inner_limit)
    width = text_width + pad_x * 2

    if align == 'right':
        x = cx - width
    elif align == 'left':
        x = cx
    else:
        x = cx - width / 2
    y = cy - height / 2

    parts.append(
        '<rect x="%s" y="%s" width="%s" height="%s" rx="%s" '
        'fill="%s" stroke="#e9b9ca" stroke-width=".08"/>'
        % (_n(x), _n(y), _n(width), _n(height), _n(height / 2.6), PINK_SOFT)
    )
    length = ''
    if estimated_text > inner_limit:
        length = ' textLength="%s" lengthAdjust="spacingAndGlyphs"' % _n(inner_limit)
    parts.append(
        '<text class="label" x="%s" y="%s" font-size="%s"%s>%s</text>'
        % (_n(x + width / 2), _n(cy), _n(font_size), length, _xml(text))
    )


def _pitch(parts, spec):
    kind = spec['kind']
    width, height = float(spec['w']), float(spec['h'])
    if kind == 'blank':
        return

    parts.append('<rect width="%s" height="%s" rx=".35" fill="%s"/>'
                 % (_n(width), _n(height), GRASS))
    if kind == 'wall':
        parts.append('<rect width="%s" height="2.4" fill="#7b6a63"/>' % _n(width))
        x = 0.0
        while x < width:
            parts.append('<path d="M%s 0v2.4" stroke="#665650" stroke-width=".08"/>'
                         % _n(x))
            x += 2.2
        return

    band = max(6.0, height / 7.0)
    i = 0
    while i * band < height:
        if i % 2:
            y = i * band
            parts.append('<rect y="%s" width="%s" height="%s" fill="%s"/>'
                         % (_n(y), _n(width), _n(min(band, height - y)), GRASS_ALT))
        i += 1
    parts.append('<rect width="%s" height="%s" rx=".35" fill="none" '
                 'stroke="%s" stroke-width=".16"/>'
                 % (_n(width), _n(height), FIELD_LINE))

    def area(at_top):
        box_width = min(40.3, width * .62)
        goal_width = min(18.3, width * .29)
        for area_width, depth in ((box_width, 16.5), (goal_width, 5.5)):
            depth = min(depth, height)
            y = 0 if at_top else height - depth
            parts.append('<rect x="%s" y="%s" width="%s" height="%s" fill="none" '
                         'stroke="%s" stroke-width=".16"/>'
                         % (_n((width - area_width) / 2), _n(y), _n(area_width),
                            _n(depth), FIELD_LINE))
        mouth = min(7.32, width * .42)
        goal_y = -1.25 if at_top else height + 1.25
        parts.append('<path d="M%s %sH%s" fill="none" stroke="%s" '
                     'stroke-width=".42" stroke-linecap="round"/>'
                     % (_n((width - mouth) / 2), _n(goal_y),
                        _n((width + mouth) / 2), FIELD_LINE))

    if kind in ('half', 'full'):
        area(True)
    if kind in ('own', 'full'):
        area(False)
    if kind == 'full':
        parts.append('<path d="M0 %sH%s" stroke="%s" stroke-width=".16"/>'
                     % (_n(height / 2), _n(width), FIELD_LINE))
        parts.append('<circle cx="%s" cy="%s" r="%s" fill="none" stroke="%s" '
                     'stroke-width=".16"/>'
                     % (_n(width / 2), _n(height / 2), _n(min(9.15, height / 2)),
                        FIELD_LINE))


def _boot_path(cx, cy, width, height):
    """Silueta del botín equivalente a ``diagram.boot_outline``."""
    half = width / 2
    top, bottom = cy + height / 2, cy - height / 2
    start = (cx - half * .30, top)
    segments = (
        ((cx - half * .95, top - height * .10),
         (cx - half * 1.02, top - height * .42),
         (cx - half * .92, bottom + height * .30)),
        ((cx - half * .85, bottom + height * .10),
         (cx - half * .62, bottom), (cx - half * .10, bottom)),
        ((cx + half * .45, bottom), (cx + half * .80, bottom + height * .08),
         (cx + half * .86, bottom + height * .32)),
        ((cx + half * .98, bottom + height * .62),
         (cx + half * .72, top - height * .06), start),
    )
    path = 'M%s %s' % (_n(start[0]), _n(start[1]))
    for segment in segments:
        path += 'C' + ' '.join('%s %s' % (_n(x), _n(y)) for x, y in segment)
    return path + 'Z'


def _dribble_path(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    distance = math.hypot(dx, dy)
    if distance < .01:
        return 'M%s %s' % (_n(a[0]), _n(a[1]))
    ux, uy = dx / distance, dy / distance
    px, py = -uy, ux
    count = max(8, int(distance / 1.4))
    path = ['M%s %s' % (_n(a[0]), _n(a[1]))]
    for i in range(1, count + 1):
        t = i / count
        offset = math.sin(t * math.pi * max(1.0, distance / 3.2)) * .34
        path.append('L%s %s' % (_n(a[0] + dx * t + px * offset),
                                _n(a[1] + dy * t + py * offset)))
    return ''.join(path)


def _validate_spec(spec):
    if not isinstance(spec, dict):
        raise TypeError('el diagrama debe ser un diccionario')
    missing = {'kind', 'w', 'h', 'items'} - set(spec)
    if missing:
        raise ValueError('faltan campos del diagrama: %s' % ', '.join(sorted(missing)))
    if spec['kind'] not in _KINDS:
        raise ValueError('tipo de cancha no compatible: %s' % spec['kind'])
    if float(spec['w']) <= 0 or float(spec['h']) <= 0:
        raise ValueError('el ancho y el alto del diagrama deben ser positivos')
    unknown = sorted({item[0] for item in spec['items']} - _ITEMS)
    if unknown:
        raise ValueError('símbolos de diagrama no compatibles: %s' % ', '.join(unknown))


def diagram_dimensions(spec, width=960):
    """Devuelve ``(ancho, alto)`` intrínsecos para los atributos de ``<img>``."""
    _validate_spec(spec)
    width = int(width)
    if width <= 0:
        raise ValueError('el ancho intrínseco debe ser positivo')
    pad = float(spec.get('pad', 2.0))
    view_width = float(spec['w']) + pad * 2
    view_height = float(spec['h']) + pad * 2
    return width, max(180, round(width * view_height / view_width))


def diagram_svg(spec, label='Diagrama del ejercicio'):
    """Devuelve un SVG compacto para uno de los specs de ``content.D``.

    ``label`` se inserta escapado como título accesible.  La función soporta
    todos los tipos de cancha y símbolos empleados por los 15 ``DRILLS``.
    """
    _validate_spec(spec)
    width, height = float(spec['w']), float(spec['h'])
    pad = float(spec.get('pad', 2.0))
    player_radius = float(spec.get('pr', 1.55))
    vb_width, vb_height = width + pad * 2, height + pad * 2
    intrinsic_width, intrinsic_height = diagram_dimensions(spec)

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title" '
        'viewBox="%s %s %s %s" width="%d" height="%d" '
        'preserveAspectRatio="xMidYMid meet">'
        % (_n(-pad), _n(-pad), _n(vb_width), _n(vb_height), intrinsic_width,
           intrinsic_height),
        '<title id="title">%s</title>' % _xml(label),
        '<defs><marker id="run" viewBox="0 0 10 10" refX="8" refY="5" '
        'markerWidth="4" markerHeight="4" orient="auto"><path d="M0 0l10 5-10 5Z" '
        'fill="%s"/></marker><marker id="pass" viewBox="0 0 10 10" refX="8" '
        'refY="5" markerWidth="4" markerHeight="4" orient="auto"><path '
        'd="M0 0l10 5-10 5Z" fill="%s"/></marker><marker id="shot" '
        'viewBox="0 0 10 10" refX="8" refY="5" markerWidth="4" markerHeight="4" '
        'orient="auto"><path d="M0 0l10 5-10 5Z" fill="%s"/></marker>'
        '<style>.label,.number{font-family:system-ui,-apple-system,"Segoe UI",Arial,sans-serif;'
        'font-weight:800;text-anchor:middle;dominant-baseline:central}.label{fill:%s}'
        '.move{fill:none;stroke-linecap:round;stroke-linejoin:round}'
        '</style></defs>' % (PINK, FIELD_LINE, YELLOW, PINK),
    ]
    _pitch(parts, spec)

    # Zonas y formas de fondo.
    for item in spec['items']:
        kind = item[0]
        if kind == 'zone':
            _, x1, y1, x2, y2 = item[:5]
            top = height - float(y2)
            parts.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#7ea166" '
                         'stroke="%s" stroke-width=".12"/>'
                         % (_n(x1), _n(top), _n(float(x2) - float(x1)),
                            _n(float(y2) - float(y1)), YELLOW))
            if len(item) > 5 and item[5]:
                _chip(parts, (float(x1) + float(x2)) / 2,
                      height - (float(y1) + float(y2)) / 2, item[5], .9, 'center',
                      float(x2) - float(x1))
        elif kind == 'poly':
            points = ' '.join('%s,%s' % (_n(x), _n(height - y)) for x, y in item[1])
            fill = item[2] if len(item) > 2 and item[2] else 'none'
            stroke = item[3] if len(item) > 3 and item[3] else 'none'
            stroke_width = item[4] if len(item) > 4 else 1
            parts.append('<polygon points="%s" fill="%s" stroke="%s" stroke-width="%s"/>'
                         % (points, _xml(fill), _xml(stroke), _n(stroke_width)))
        elif kind == 'target':
            _, x, y, target_width, target_height = item
            parts.append('<rect x="%s" y="%s" width="%s" height="%s" fill="none" '
                         'stroke="%s" stroke-width=".22"/>'
                         % (_n(x), _n(height - y - target_height), _n(target_width),
                            _n(target_height), FIELD_LINE))

    # Trayectorias, antes de los símbolos de jugadoras y balón.
    for item in spec['items']:
        kind = item[0]
        if kind not in ('run', 'pass', 'shot', 'drib', 'seg'):
            continue
        a = _point(height, item[1], item[2])
        b = _point(height, item[3], item[4])
        if kind == 'run':
            _line(parts, a, b, PINK, .24, ' class="move" marker-end="url(#run)"')
        elif kind == 'pass':
            _line(parts, a, b, FIELD_LINE, .20,
                  ' class="move" stroke-dasharray=".55 .42" marker-end="url(#pass)"')
        elif kind == 'shot':
            _line(parts, a, b, YELLOW, .38,
                  ' class="move" marker-end="url(#shot)"')
        elif kind == 'drib':
            parts.append('<path class="move" d="%s" stroke="%s" stroke-width=".24" '
                         'marker-end="url(#run)"/>' % (_dribble_path(a, b), PINK))
        else:
            color = item[5] if len(item) > 5 else FIELD_LINE
            stroke_width = item[6] if len(item) > 6 else .2
            dash = ''
            if len(item) > 7 and item[7]:
                dash = ' stroke-dasharray="%s"' % ' '.join(_n(v) for v in item[7])
            _line(parts, a, b, _xml(color), stroke_width, ' class="move"' + dash)

    # Símbolos y protagonistas.
    for item in spec['items']:
        kind = item[0]
        if kind == 'c':
            x, y = _point(height, item[1], item[2])
            radius = player_radius * .62
            points = ((x, y - radius), (x + radius * .72, y + radius * .6),
                      (x - radius * .72, y + radius * .6))
            parts.append('<polygon points="%s" fill="%s" stroke="#8a4b00" '
                         'stroke-width=".1"/>'
                         % (' '.join('%s,%s' % (_n(px), _n(py)) for px, py in points), ORANGE))
        elif kind == 'boot':
            _, x, y, boot_width, boot_height = item
            cx, cy = _point(height, x, y)
            parts.append('<path d="%s" fill="#fff" stroke="%s" stroke-width=".28"/>'
                         % (_boot_path(cx, cy, float(boot_width), float(boot_height)), INK))
            for i in range(4):
                lace_y = cy - float(boot_height) * .06 + i * float(boot_height) * .1
                _line(parts, (cx - float(boot_width) * .19, lace_y),
                      (cx + float(boot_width) * .13,
                       lace_y - float(boot_height) * .02), INK, .18)
        elif kind == 'mark':
            _, mark_x, mark_y, label_x, label_y, text = item[:6]
            a, b = _point(height, mark_x, mark_y), _point(height, label_x, label_y)
            _line(parts, a, b, PINK, .19)
            parts.append('<circle cx="%s" cy="%s" r=".62" fill="#d94f87" '
                         'stroke="#fff" stroke-width=".16"/>' % (_n(a[0]), _n(a[1])))
            align = 'left' if float(label_x) > float(mark_x) else 'right'
            text_size = item[6] if len(item) > 6 else .95
            _chip(parts, b[0], b[1], text, text_size, align, width + pad * 1.6)
        elif kind in ('p', 'gk', 'r'):
            x, y = _point(height, item[1], item[2])
            radius = player_radius if kind in ('p', 'gk') else player_radius * .94
            fill = BLUE if kind == 'p' else (YELLOW if kind == 'gk' else INK)
            stroke = BLUE_DARK if kind == 'p' else ('#8a6a00' if kind == 'gk' else '#52616a')
            parts.append('<circle cx="%s" cy="%s" r="%s" fill="#1d553d" opacity=".35"/>'
                         % (_n(x + radius * .14), _n(y + radius * .18), _n(radius)))
            parts.append('<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" '
                         'stroke-width=".16"/>'
                         % (_n(x), _n(y), _n(radius), fill, stroke))
            if len(item) > 3 and item[3] not in ('', None):
                text_fill = INK if kind == 'gk' else '#fff'
                parts.append('<text class="number" x="%s" y="%s" font-size="%s" '
                             'fill="%s">%s</text>'
                             % (_n(x), _n(y), _n(radius * 1.14), text_fill,
                                _xml(item[3])))
        elif kind == 'b':
            x, y = _point(height, item[1], item[2])
            radius = max(.58, player_radius * .5)
            parts.append('<circle cx="%s" cy="%s" r="%s" fill="#fff" stroke="%s" '
                         'stroke-width=".14"/><circle cx="%s" cy="%s" r="%s" fill="%s"/>'
                         % (_n(x), _n(y), _n(radius), INK, _n(x), _n(y),
                            _n(radius * .34), INK))

    # Etiquetas por encima del resto.
    for item in spec['items']:
        if item[0] != 't':
            continue
        _, x, y, text = item[:4]
        size = item[4] if len(item) > 4 else 1.0
        align = item[5] if len(item) > 5 else 'center'
        point = _point(height, x, y)
        _chip(parts, point[0], point[1], text, size, align, width + pad * 1.6)

    parts.append('</svg>')
    return ''.join(parts)


def diagram_data_uri(spec, label='Diagrama del ejercicio'):
    """Devuelve el diagrama como URI segura para ``<img loading="lazy">``."""
    return _data_uri(diagram_svg(spec, label))


def qr_svg(url, label='Código QR'):
    """Devuelve un QR SVG compacto con zona silenciosa de cuatro módulos."""
    if not isinstance(url, str) or not url:
        raise ValueError('el destino del código QR no puede estar vacío')
    size, matrix = pk.qr_matrix(url)
    quiet = 4
    total = size + quiet * 2
    runs = []
    for row in range(size):
        column = 0
        while column < size:
            if matrix[row][column]:
                start = column
                while column < size and matrix[row][column]:
                    column += 1
                length = column - start
                runs.append('M%d %dh%dv1h-%dz' %
                            (quiet + start, quiet + row, length, length))
            else:
                column += 1
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title" '
        'viewBox="0 0 %d %d" width="256" height="256" shape-rendering="crispEdges">'
        '<title id="title">%s</title><rect width="%d" height="%d" fill="#fff"/>'
        '<path d="%s" fill="%s"/></svg>'
        % (total, total, _xml(label), total, total, ''.join(runs), INK)
    )


def qr_data_uri(url, label='Código QR'):
    """Devuelve el QR como URI segura para ``<img loading="lazy">``."""
    return _data_uri(qr_svg(url, label))
