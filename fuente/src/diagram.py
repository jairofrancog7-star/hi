"""Dibuja diagramas de cancha dentro de un rectángulo de la página.

Coordenadas del mundo en metros, origen abajo-izquierda, y hacia arriba
(dirección de ataque). El renderer se encarga de voltear la y.
"""
import pdfkit as pk

GRASS = '#2f8f57'
GRASS2 = '#2a8250'
LINE = '#e8f5ec'
OURS = '#ff5c8a'
OURS_D = '#8e1d47'
RIVAL = '#1c1c22'
CONE = '#ff9800'
BALL = '#ffffff'
RUN = '#ff2d6f'
PASS = '#ffffff'
SHOT = '#ffd23f'
CHIP_BG = '#fff1f5'
CHIP_TX = '#8e1d47'


def _fit(spec, x, y, w, h):
    pad = spec.get('pad', 2.0)
    vw, vh = spec['w'] + pad * 2, spec['h'] + pad * 2
    s = min(w / vw, h / vh)
    ox = x + (w - vw * s) / 2 + pad * s
    oy = y + (h - vh * s) / 2 + pad * s

    def T(mx, my):
        return (ox + mx * s, oy + (spec['h'] - my) * s)
    return T, s


def height_for(spec, w):
    """Alto en puntos que necesita el diagrama para un ancho dado."""
    pad = spec.get('pad', 2.0)
    vw, vh = spec['w'] + pad * 2, spec['h'] + pad * 2
    return w * vh / vw


def _pitch(page, spec, T, s):
    kind, W, H = spec['kind'], spec['w'], spec['h']
    if kind == 'blank':
        return
    if kind == 'wall':
        # pared al fondo
        x0, y0 = T(0, H)
        page.rect(x0, y0, W * s, H * s, fill=GRASS)
        wx, wy = T(0, H)
        page.rect(wx, wy, W * s, 2.4 * s, fill='#7b6a63')
        for i in range(int(W / 2.2)):
            page.line(wx + i * 2.2 * s, wy, wx + i * 2.2 * s, wy + 2.4 * s, '#6a5a54', 0.8)
        return

    x0, y0 = T(0, H)
    page.rect(x0, y0, W * s, H * s, fill=GRASS)
    band = max(6.0, H / 7.0)
    i = 0
    while i * band < H:
        if i % 2:
            yy0 = T(0, min(H, (i + 1) * band))[1]
            page.rect(x0, yy0, W * s, min(band, H - i * band) * s, fill=GRASS2)
        i += 1
    lw = max(0.7, 0.16 * s)
    page.rect(x0, y0, W * s, H * s, stroke=LINE, lw=lw)

    def area(at_top):
        bw, bd = min(40.3, W * 0.62), 16.5
        gw, gd = min(18.3, W * 0.29), 5.5
        for (aw, ad) in ((bw, bd), (gw, gd)):
            cx = W / 2
            if at_top:
                p = T(cx - aw / 2, H)
                page.rect(p[0], p[1], aw * s, ad * s, stroke=LINE, lw=lw)
            else:
                p = T(cx - aw / 2, ad)
                page.rect(p[0], p[1], aw * s, ad * s, stroke=LINE, lw=lw)
        # portería
        gm = 7.32
        if at_top:
            a, b = T(cx - gm / 2, H), T(cx + gm / 2, H)
            page.line(a[0], a[1] - 1.6 * s, b[0], b[1] - 1.6 * s, LINE, lw * 2.4)
        else:
            a, b = T(cx - gm / 2, 0), T(cx + gm / 2, 0)
            page.line(a[0], a[1] + 1.6 * s, b[0], b[1] + 1.6 * s, LINE, lw * 2.4)

    if kind in ('half', 'full'):
        area(True)
    if kind in ('own', 'full'):
        area(False)
    if kind == 'full':
        a, b = T(0, H / 2), T(W, H / 2)
        page.line(a[0], a[1], b[0], b[1], LINE, lw)
        c = T(W / 2, H / 2)
        page.circle(c[0], c[1], 9.15 * s, stroke=LINE, lw=lw)


def _chip(page, cx, cy, txt, size, align='center', maxw=None):
    w = pk.width(txt, size, True)
    if maxw and w > maxw:
        while size > 3.2 and pk.width(txt, size, True) > maxw:
            size -= 0.2
        w = pk.width(txt, size, True)
    padx, h = size * 0.42, size * 1.62
    if align == 'center':
        x = cx - w / 2 - padx
    elif align == 'right':
        x = cx - w - padx * 2
    else:
        x = cx
    page.roundrect(x, cy - h / 2, w + padx * 2, h, h / 2.6, fill=CHIP_BG)
    page.text(x + padx, cy - size * 0.62, txt, size, True, color=CHIP_TX)


def boot_outline(cx, cy, bw, bh):
    """Silueta de un botín visto desde arriba (lista de tramos bezier)."""
    hw = bw / 2
    top, bot = cy + bh / 2, cy - bh / 2
    return [
        (cx - hw * 0.30, top),
        [(cx - hw * 0.95, top - bh * 0.10), (cx - hw * 1.02, top - bh * 0.42), (cx - hw * 0.92, bot + bh * 0.30)],
        [(cx - hw * 0.85, bot + bh * 0.10), (cx - hw * 0.62, bot), (cx - hw * 0.10, bot)],
        [(cx + hw * 0.45, bot), (cx + hw * 0.80, bot + bh * 0.08), (cx + hw * 0.86, bot + bh * 0.32)],
        [(cx + hw * 0.98, bot + bh * 0.62), (cx + hw * 0.72, top - bh * 0.06), (cx - hw * 0.30, top)],
    ]


def render(page, spec, x, y, w, h, ink='#241a1e'):
    T, s = _fit(spec, x, y, w, h)
    _pitch(page, spec, T, s)
    pr = spec.get('pr', 1.55)

    for it in spec['items']:
        k = it[0]
        if k == 'zone':
            _, x1, y1, x2, y2 = it[:5]
            a, b = T(x1, y2), T(x2, y1)
            page.rect(a[0], a[1], b[0] - a[0], b[1] - a[1], fill=pk.blend('#ffd23f', GRASS, 0.28))
            page.rect(a[0], a[1], b[0] - a[0], b[1] - a[1], stroke=SHOT, lw=0.9)
            if len(it) > 5 and it[5]:
                _chip(page, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, it[5], max(4.4, 0.85 * s))
        elif k == 'poly':
            pts = [T(*p) for p in it[1]]
            page.poly(pts, fill=it[2] if len(it) > 2 else None,
                      stroke=it[3] if len(it) > 3 else None,
                      lw=it[4] if len(it) > 4 else 1)
        elif k == 'target':
            _, tx, ty, tw, th = it
            a = T(tx, ty + th)
            page.rect(a[0], a[1], tw * s, th * s, stroke='#ffffff', lw=1.6)

    for it in spec['items']:
        k = it[0]
        if k in ('run', 'pass', 'shot', 'drib', 'seg'):
            a, b = T(it[1], it[2]), T(it[3], it[4])
            if k == 'run':
                page.arrow(a[0], a[1], b[0], b[1], RUN, max(1.1, 0.24 * s), head=max(4, 1.05 * s))
            elif k == 'pass':
                page.arrow(a[0], a[1], b[0], b[1], PASS, max(1.0, 0.2 * s),
                           dash=[max(2.0, 0.5 * s), max(1.6, 0.42 * s)], head=max(4, 1.0 * s))
            elif k == 'shot':
                page.arrow(a[0], a[1], b[0], b[1], SHOT, max(1.6, 0.4 * s), head=max(5, 1.35 * s))
            elif k == 'drib':
                page.wavy(a[0], a[1], b[0], b[1], RUN, max(1.1, 0.24 * s),
                          amp=max(1.4, 0.4 * s), head=max(4, 1.05 * s))
            else:
                page.line(a[0], a[1], b[0], b[1], it[5] if len(it) > 5 else '#ffffff',
                          it[6] if len(it) > 6 else 1,
                          dash=it[7] if len(it) > 7 else None)

    for it in spec['items']:
        k = it[0]
        if k == 'c':
            p = T(it[1], it[2])
            r = pr * 0.62 * s
            page.poly([(p[0], p[1] - r), (p[0] + r * 0.72, p[1] + r * 0.6),
                       (p[0] - r * 0.72, p[1] + r * 0.6)], fill=CONE, stroke='#8a4b00', lw=0.6)
        elif k == 'boot':
            _, bx, by, bw, bh = it
            c = T(bx, by)
            segs = boot_outline(c[0], c[1], bw * s, bh * s)
            page.bezier([segs[0]] + segs[1:], fill='#ffffff', stroke='#2b2b33', lw=1.4)
            for i in range(4):
                yy = c[1] - bh * s * 0.06 + i * bh * s * 0.1
                page.line(c[0] - bw * s * 0.19, yy, c[0] + bw * s * 0.13, yy - bh * s * 0.02,
                          '#2b2b33', 1.0)
        elif k == 'mark':
            _, mx, my, lx, ly, label = it[:6]
            a, b = T(mx, my), T(lx, ly)
            page.line(a[0], a[1], b[0], b[1], '#e8443a', 1.1)
            page.circle(a[0], a[1], max(2.0, 0.62 * s), fill='#f24236', stroke='#ffffff', lw=1.0)
            al = 'left' if lx > mx else 'right'
            _chip(page, b[0], b[1], label, max(4.6, 0.95 * s), al)
        elif k in ('p', 'gk'):
            p = T(it[1], it[2])
            col = OURS if k == 'p' else '#ffd23f'
            r = pr * s
            page.circle(p[0] + r * 0.14, p[1] + r * 0.18, r, fill=pk.blend('#000000', GRASS, 0.22))
            page.circle(p[0], p[1], r, fill=col, stroke=OURS_D if k == 'p' else '#8a6a00', lw=max(0.7, 0.16 * s))
            if len(it) > 3 and it[3]:
                fs = r * 1.16
                page.text(p[0], p[1] - fs * 0.52, str(it[3]), fs, True,
                          color='#ffffff' if k == 'p' else '#3a2c00', align='center')
        elif k == 'r':
            p = T(it[1], it[2])
            r = pr * 0.94 * s
            page.circle(p[0] + r * 0.14, p[1] + r * 0.18, r, fill=pk.blend('#000000', GRASS, 0.22))
            page.circle(p[0], p[1], r, fill=RIVAL, stroke='#5b5b66', lw=max(0.6, 0.14 * s))
            if len(it) > 3 and it[3]:
                fs = r * 1.1
                page.text(p[0], p[1] - fs * 0.52, str(it[3]), fs, True, color='#ffffff', align='center')
        elif k == 'b':
            p = T(it[1], it[2])
            r = max(1.9, pr * 0.5 * s)
            page.circle(p[0], p[1], r, fill=BALL, stroke='#1c1c22', lw=max(0.6, 0.14 * s))
            page.circle(p[0], p[1], r * 0.34, fill='#1c1c22')

    for it in spec['items']:
        if it[0] == 't':
            _, tx, ty, txt = it[:4]
            size = it[4] if len(it) > 4 else 1.0
            align = it[5] if len(it) > 5 else 'center'
            p = T(tx, ty)
            _chip(page, p[0], p[1], txt, max(4.4, size * s), align,
                  maxw=spec['w'] * s + spec.get('pad', 2) * s * 1.6)
