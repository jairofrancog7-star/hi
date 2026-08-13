"""Escritor de PDF mínimo pero real: texto, vectores, enlaces clicables y QR.

Sin dependencias externas. Usa las fuentes estándar (Helvetica) con
WinAnsiEncoding, así que no hay que incrustar tipografías.
"""
import zlib

# ---------------------------------------------------------------- métricas
# Anchos AFM de las fuentes estándar (unidades /1000).
_HELV = {
    ' ': 278, '!': 278, '"': 355, '#': 556, '$': 556, '%': 889, '&': 667, "'": 191,
    '(': 333, ')': 333, '*': 389, '+': 584, ',': 278, '-': 333, '.': 278, '/': 278,
    ':': 278, ';': 278, '<': 584, '=': 584, '>': 584, '?': 556, '@': 1015,
    'A': 667, 'B': 667, 'C': 722, 'D': 722, 'E': 667, 'F': 611, 'G': 778, 'H': 722,
    'I': 278, 'J': 500, 'K': 667, 'L': 556, 'M': 833, 'N': 722, 'O': 778, 'P': 667,
    'Q': 778, 'R': 722, 'S': 667, 'T': 611, 'U': 722, 'V': 667, 'W': 944, 'X': 667,
    'Y': 667, 'Z': 611, '[': 278, '\\': 278, ']': 278, '^': 469, '_': 556, '`': 333,
    'a': 556, 'b': 556, 'c': 500, 'd': 556, 'e': 556, 'f': 278, 'g': 556, 'h': 556,
    'i': 222, 'j': 222, 'k': 500, 'l': 222, 'm': 833, 'n': 556, 'o': 556, 'p': 556,
    'q': 556, 'r': 333, 's': 500, 't': 278, 'u': 556, 'v': 500, 'w': 722, 'x': 500,
    'y': 500, 'z': 500, '{': 334, '|': 260, '}': 334, '~': 584,
}
_BOLD = {
    ' ': 278, '!': 333, '"': 474, '#': 556, '$': 556, '%': 889, '&': 722, "'": 238,
    '(': 333, ')': 333, '*': 389, '+': 584, ',': 278, '-': 333, '.': 278, '/': 278,
    ':': 333, ';': 333, '<': 584, '=': 584, '>': 584, '?': 611, '@': 975,
    'A': 722, 'B': 722, 'C': 722, 'D': 722, 'E': 667, 'F': 611, 'G': 778, 'H': 722,
    'I': 278, 'J': 556, 'K': 722, 'L': 611, 'M': 833, 'N': 722, 'O': 778, 'P': 667,
    'Q': 778, 'R': 722, 'S': 667, 'T': 611, 'U': 722, 'V': 667, 'W': 944, 'X': 667,
    'Y': 667, 'Z': 611, '[': 333, '\\': 278, ']': 333, '^': 584, '_': 556, '`': 333,
    'a': 556, 'b': 611, 'c': 556, 'd': 611, 'e': 556, 'f': 333, 'g': 611, 'h': 611,
    'i': 278, 'j': 278, 'k': 556, 'l': 278, 'm': 889, 'n': 611, 'o': 611, 'p': 611,
    'q': 611, 'r': 389, 's': 556, 't': 333, 'u': 611, 'v': 556, 'w': 778, 'x': 556,
    'y': 556, 'z': 500, '{': 389, '|': 280, '}': 389, '~': 584,
}
for _t in (_HELV, _BOLD):
    for _d in '0123456789':
        _t[_d] = 556
    # acentuadas y signos en español: mismo ancho que la base
    for _a, _b in (('á', 'a'), ('é', 'e'), ('í', 'i'), ('ó', 'o'), ('ú', 'u'),
                   ('ñ', 'n'), ('ü', 'u'), ('Á', 'A'), ('É', 'E'), ('Í', 'I'),
                   ('Ó', 'O'), ('Ú', 'U'), ('Ñ', 'N'), ('ç', 'c'), ('à', 'a')):
        _t[_a] = _t[_b]
    _t['¿'] = _t['?']
    _t['¡'] = _t['!']
    _t['·'] = 278 if _t is _HELV else 278
    _t['—'] = 1000
    _t['–'] = 556
    _t['“'] = _t['”'] = 333 if _t is _HELV else 500
    _t['’'] = _t["'"]
    _t['•'] = 350

# Caracteres fuera de latin-1 que sí existen en WinAnsi
_WINANSI = {'—': 0x97, '–': 0x96, '“': 0x93, '”': 0x94, '’': 0x92, '‘': 0x91,
            '•': 0x95, '…': 0x85, '€': 0x80}


def width(s, size, bold=False):
    """Ancho del texto en puntos (con 2% de margen de seguridad)."""
    t = _BOLD if bold else _HELV
    return sum(t.get(c, 556) for c in s) * size / 1000.0 * 1.02


def _pdfstr(s):
    out = bytearray(b'(')
    for ch in s:
        if ch in _WINANSI:
            b = _WINANSI[ch]
        else:
            try:
                b = ch.encode('latin-1')[0]
            except UnicodeEncodeError:
                b = ord('?')
        if b in (0x28, 0x29, 0x5C):          # ( ) \
            out += b'\\'
        out.append(b)
    out += b')'
    return bytes(out)


def rgb(color):
    c = color.lstrip('#')
    if len(c) == 3:
        c = ''.join(ch * 2 for ch in c)
    return (int(c[0:2], 16) / 255.0, int(c[2:4], 16) / 255.0, int(c[4:6], 16) / 255.0)


def blend(fg, bg, alpha):
    """Mezcla previa de color: el PDF queda sin transparencias."""
    f, b = rgb(fg), rgb(bg)
    m = [f[i] * alpha + b[i] * (1 - alpha) for i in range(3)]
    return '#%02x%02x%02x' % tuple(int(round(v * 255)) for v in m)


# ---------------------------------------------------------------- páginas
class Page:
    def __init__(self, doc, w, h):
        self.doc, self.w, self.h = doc, w, h
        self.ops = []
        self.links = []

    # -- utilidades internas
    def _y(self, y):
        return self.h - y

    def _c(self, color, stroke=False):
        r, g, b = rgb(color)
        self.ops.append('%.4f %.4f %.4f %s' % (r, g, b, 'RG' if stroke else 'rg'))

    # -- vectores
    def rect(self, x, y, w, h, fill=None, stroke=None, lw=1):
        if fill:
            self._c(fill)
        if stroke:
            self._c(stroke, True)
            self.ops.append('%.3f w' % lw)
        self.ops.append('%.3f %.3f %.3f %.3f re' % (x, self._y(y + h), w, h))
        self.ops.append('B' if (fill and stroke) else ('f' if fill else 'S'))

    def roundrect(self, x, y, w, h, r, fill=None, stroke=None, lw=1):
        r = min(r, w / 2, h / 2)
        k = r * 0.5523
        y0, y1 = self._y(y + h), self._y(y)
        p = ['%.3f %.3f m' % (x + r, y0),
             '%.3f %.3f l' % (x + w - r, y0),
             '%.3f %.3f %.3f %.3f %.3f %.3f c' % (x + w - r + k, y0, x + w, y0 + r - k, x + w, y0 + r),
             '%.3f %.3f l' % (x + w, y1 - r),
             '%.3f %.3f %.3f %.3f %.3f %.3f c' % (x + w, y1 - r + k, x + w - r + k, y1, x + w - r, y1),
             '%.3f %.3f l' % (x + r, y1),
             '%.3f %.3f %.3f %.3f %.3f %.3f c' % (x + r - k, y1, x, y1 - r + k, x, y1 - r),
             '%.3f %.3f l' % (x, y0 + r),
             '%.3f %.3f %.3f %.3f %.3f %.3f c' % (x, y0 + r - k, x + r - k, y0, x + r, y0),
             'h']
        if fill:
            self._c(fill)
        if stroke:
            self._c(stroke, True)
            self.ops.append('%.3f w' % lw)
        self.ops += p
        self.ops.append('B' if (fill and stroke) else ('f' if fill else 'S'))

    def circle(self, cx, cy, r, fill=None, stroke=None, lw=1):
        k = r * 0.5523
        y = self._y(cy)
        self.ops.append('%.3f %.3f m' % (cx - r, y))
        self.ops.append('%.3f %.3f %.3f %.3f %.3f %.3f c' % (cx - r, y + k, cx - k, y + r, cx, y + r))
        self.ops.append('%.3f %.3f %.3f %.3f %.3f %.3f c' % (cx + k, y + r, cx + r, y + k, cx + r, y))
        self.ops.append('%.3f %.3f %.3f %.3f %.3f %.3f c' % (cx + r, y - k, cx + k, y - r, cx, y - r))
        self.ops.append('%.3f %.3f %.3f %.3f %.3f %.3f c' % (cx - k, y - r, cx - r, y - k, cx - r, y))
        if fill:
            self._c(fill)
        if stroke:
            self._c(stroke, True)
            self.ops.append('%.3f w' % lw)
        self.ops.append('B' if (fill and stroke) else ('f' if fill else 'S'))

    def line(self, x1, y1, x2, y2, color='#000', lw=1, dash=None, cap=1):
        self._c(color, True)
        self.ops.append('%.3f w %d J' % (lw, cap))
        self.ops.append('[%s] 0 d' % (' '.join('%.2f' % d for d in dash) if dash else ''))
        self.ops.append('%.3f %.3f m %.3f %.3f l S' % (x1, self._y(y1), x2, self._y(y2)))
        self.ops.append('[] 0 d')

    def poly(self, pts, fill=None, stroke=None, lw=1, close=True):
        if not pts:
            return
        if fill:
            self._c(fill)
        if stroke:
            self._c(stroke, True)
            self.ops.append('%.3f w' % lw)
        self.ops.append('%.3f %.3f m' % (pts[0][0], self._y(pts[0][1])))
        for x, y in pts[1:]:
            self.ops.append('%.3f %.3f l' % (x, self._y(y)))
        if close:
            self.ops.append('h')
        self.ops.append('B' if (fill and stroke) else ('f' if fill else 'S'))

    def bezier(self, pts, fill=None, stroke=None, lw=1):
        """pts = [(x,y), (c1,c2,p), ...] donde cada tramo son 3 puntos."""
        if fill:
            self._c(fill)
        if stroke:
            self._c(stroke, True)
            self.ops.append('%.3f w' % lw)
        self.ops.append('%.3f %.3f m' % (pts[0][0], self._y(pts[0][1])))
        for seg in pts[1:]:
            (ax, ay), (bx, by), (cx, cy) = seg
            self.ops.append('%.3f %.3f %.3f %.3f %.3f %.3f c'
                            % (ax, self._y(ay), bx, self._y(by), cx, self._y(cy)))
        self.ops.append('h')
        self.ops.append('B' if (fill and stroke) else ('f' if fill else 'S'))

    def arrow(self, x1, y1, x2, y2, color='#000', lw=1.4, dash=None, head=5):
        import math
        d = math.hypot(x2 - x1, y2 - y1)
        if d < 0.01:
            return
        ux, uy = (x2 - x1) / d, (y2 - y1) / d
        bx, by = x2 - ux * head * 0.95, y2 - uy * head * 0.95
        self.line(x1, y1, bx, by, color, lw, dash)
        px, py = -uy, ux
        self.poly([(x2, y2), (bx + px * head * 0.5, by + py * head * 0.5),
                   (bx - px * head * 0.5, by - py * head * 0.5)], fill=color)

    def wavy(self, x1, y1, x2, y2, color='#000', lw=1.4, amp=2.2, head=5):
        import math
        d = math.hypot(x2 - x1, y2 - y1)
        if d < 1:
            return
        ux, uy = (x2 - x1) / d, (y2 - y1) / d
        px, py = -uy, ux
        n = max(8, int(d / 4))
        pts = []
        for i in range(n + 1):
            t = i / n
            off = math.sin(t * math.pi * (d / 11.0)) * amp
            pts.append((x1 + ux * d * t + px * off, y1 + uy * d * t + py * off))
        self._c(color, True)
        self.ops.append('%.3f w 1 J' % lw)
        self.ops.append('%.3f %.3f m' % (pts[0][0], self._y(pts[0][1])))
        for x, y in pts[1:]:
            self.ops.append('%.3f %.3f l' % (x, self._y(y)))
        self.ops.append('S')
        bx, by = x2 - ux * head, y2 - uy * head
        self.poly([(x2, y2), (bx + px * head * 0.5, by + py * head * 0.5),
                   (bx - px * head * 0.5, by - py * head * 0.5)], fill=color)

    # -- texto
    def text(self, x, y, s, size=10, bold=False, italic=False, color='#000',
             align='left', maxw=None):
        """y = borde superior de la caja de texto."""
        if not s:
            return
        if maxw:
            while size > 3 and width(s, size, bold) > maxw:
                size -= 0.25
        w = width(s, size, bold)
        if align == 'center':
            x -= w / 2
        elif align == 'right':
            x -= w
        f = 'F2' if bold else ('F3' if italic else 'F1')
        if not hasattr(self, 'texts'):
            self.texts = []
        self.texts.append((x, y, w, size, s))
        self._c(color)
        self.ops.append('BT /%s %.2f Tf 1 0 0 1 %.3f %.3f Tm %s Tj ET'
                        % (f, size, x, self._y(y) - size * 0.79,
                           _pdfstr(s).decode('latin-1')))
        return w

    def wrap(self, s, size, maxw, bold=False):
        lines, cur = [], ''
        for word in s.split():
            t = (cur + ' ' + word).strip()
            if cur and width(t, size, bold) > maxw:
                lines.append(cur)
                cur = word
            else:
                cur = t
        if cur:
            lines.append(cur)
        return lines

    def para(self, x, y, s, size, maxw, leading=None, bold=False, color='#000',
             align='left'):
        leading = leading or size * 1.36
        for i, ln in enumerate(self.wrap(s, size, maxw, bold)):
            self.text(x, y + i * leading, ln, size, bold, color=color, align=align)
        return y + len(self.wrap(s, size, maxw, bold)) * leading

    def para_h(self, s, size, maxw, bold=False, leading=None):
        leading = leading or size * 1.36
        return len(self.wrap(s, size, maxw, bold)) * leading

    def rich(self, x, y, runs, size, maxw, leading=None, color='#000'):
        """runs = [(texto, 'b'|'r'|'i')] con salto de línea automático."""
        leading = leading or size * 1.36
        cx, cy = x, y
        for txt, style in runs:
            bold, ital = style == 'b', style == 'i'
            words = txt.split(' ')
            for j, wd in enumerate(words):
                if wd == '':
                    continue
                piece = wd + (' ' if j < len(words) - 1 else '')
                pw = width(piece, size, bold)
                if cx > x and cx + width(wd, size, bold) > x + maxw:
                    cx, cy = x, cy + leading
                self.text(cx, cy, piece, size, bold, ital, color)
                cx += pw
        return cy + leading

    def rich_h(self, runs, size, maxw, leading=None):
        leading = leading or size * 1.36
        cx, n = 0.0, 1
        for txt, style in runs:
            bold = style == 'b'
            words = txt.split(' ')
            for j, wd in enumerate(words):
                if wd == '':
                    continue
                piece = wd + (' ' if j < len(words) - 1 else '')
                if cx > 0 and cx + width(wd, size, bold) > maxw:
                    cx = 0.0
                    n += 1
                cx += width(piece, size, bold)
        return n * leading

    # -- enlaces
    def link(self, x, y, w, h, url):
        self.links.append((x, self._y(y + h), x + w, self._y(y), url))


# ---------------------------------------------------------------- documento
class Doc:
    def __init__(self):
        self.objs = [None]
        self.pages = []

    def add(self, data):
        self.objs.append(data)
        return len(self.objs) - 1

    def reserve(self):
        self.objs.append(None)
        return len(self.objs) - 1

    def page(self, w, h):
        p = Page(self, w, h)
        self.pages.append(p)
        return p

    def save(self, path):
        fonts = {}
        for key, base in (('F1', 'Helvetica'), ('F2', 'Helvetica-Bold'),
                          ('F3', 'Helvetica-Oblique')):
            fonts[key] = self.add(
                ('<< /Type /Font /Subtype /Type1 /BaseFont /%s '
                 '/Encoding /WinAnsiEncoding >>' % base).encode())
        res = '<< /Font << %s >> >>' % ' '.join(
            '/%s %d 0 R' % (k, v) for k, v in fonts.items())
        pages_id = self.reserve()
        kids = []
        for p in self.pages:
            content = '\n'.join(p.ops).encode('latin-1')
            comp = zlib.compress(content, 9)
            sid = self.add(b'<< /Length %d /Filter /FlateDecode >>\nstream\n' % len(comp)
                           + comp + b'\nendstream')
            annots = []
            for (x1, y1, x2, y2, url) in p.links:
                a = self.add(
                    ('<< /Type /Annot /Subtype /Link /Rect [%.2f %.2f %.2f %.2f] '
                     '/Border [0 0 0] /F 4 /A << /Type /Action /S /URI /URI %s >> >>'
                     % (x1, y1, x2, y2, _pdfstr(url).decode('latin-1'))).encode('latin-1'))
                annots.append(a)
            extra = (' /Annots [%s]' % ' '.join('%d 0 R' % a for a in annots)) if annots else ''
            pid = self.add(
                ('<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %.2f %.2f] '
                 '/Resources %s /Contents %d 0 R%s >>'
                 % (pages_id, p.w, p.h, res, sid, extra)).encode('latin-1'))
            kids.append(pid)
        self.objs[pages_id] = ('<< /Type /Pages /Count %d /Kids [%s] >>'
                               % (len(kids), ' '.join('%d 0 R' % k for k in kids))).encode()
        cat = self.add(b'<< /Type /Catalog /Pages %d 0 R >>' % pages_id)
        info = self.add('<< /Title (Guia de entrenamiento futbol femenil) '
                        '/Producer (Kiro) >>'.encode('latin-1'))

        out = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
        offsets = [0] * len(self.objs)
        for i in range(1, len(self.objs)):
            offsets[i] = len(out)
            out += b'%d 0 obj\n' % i + self.objs[i] + b'\nendobj\n'
        xref = len(out)
        out += b'xref\n0 %d\n' % len(self.objs)
        out += b'0000000000 65535 f \n'
        for i in range(1, len(self.objs)):
            out += b'%010d 00000 n \n' % offsets[i]
        out += (b'trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n'
                % (len(self.objs), cat, info, xref))
        with open(path, 'wb') as f:
            f.write(out)
        return len(out)


# ---------------------------------------------------------------- QR
_EC_CW = {1: 7, 2: 10, 3: 15, 4: 20, 5: 26, 6: 18, 7: 20, 8: 24, 9: 30, 10: 18}
_BLOCKS = {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 2, 10: 4}
_TOTAL = {1: 26, 2: 44, 3: 70, 4: 100, 5: 134, 6: 172, 7: 196, 8: 242, 9: 292, 10: 346}
_ALIGN = {1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30], 6: [6, 34],
          7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50]}

_EXP = [0] * 256
_LOG = [0] * 256
_x = 1
for _i in range(255):
    _EXP[_i] = _x
    _LOG[_x] = _i
    _x <<= 1
    if _x & 0x100:
        _x ^= 0x11D
_EXP[255] = _EXP[0]


def _mul(a, b):
    if a == 0 or b == 0:
        return 0
    return _EXP[(_LOG[a] + _LOG[b]) % 255]


def _gen(n):
    g = [1]
    for i in range(n):
        ng = [0] * (len(g) + 1)
        for j, c in enumerate(g):
            ng[j] ^= c
            ng[j + 1] ^= _mul(c, _EXP[i])
        g = ng
    return g


def _rs(data, n):
    g = _gen(n)
    rem = [0] * n
    for b in data:
        f = b ^ rem[0]
        rem = rem[1:] + [0]
        for i, c in enumerate(g[1:]):
            rem[i] ^= _mul(f, c)
    return rem


def _fmt_bits(mask):
    """15 bits de información de formato para nivel L."""
    data = (0b01 << 3) | mask
    v = data << 10
    for _ in range(10):
        if v >> (14 - (14 - v.bit_length() + 1)) and False:
            pass
        break
    # división BCH
    v = data << 10
    while v.bit_length() > 10:
        v ^= 0x537 << (v.bit_length() - 11)
    return ((data << 10) | v) ^ 0x5412


def qr_matrix(text):
    """Devuelve (size, matriz de booleanos). Modo byte, nivel L."""
    data = text.encode('utf-8')
    ver = None
    for v in range(1, 11):
        cap = (_TOTAL[v] - _EC_CW[v] * _BLOCKS[v]) * 8
        need = 4 + (8 if v < 10 else 16) + len(data) * 8
        if need <= cap:
            ver = v
            break
    if ver is None:
        raise ValueError('texto demasiado largo para QR v10-L: %d' % len(data))

    size = 17 + ver * 4
    ncw = _TOTAL[ver] - _EC_CW[ver] * _BLOCKS[ver]

    bits = []

    def put(val, n):
        for i in range(n - 1, -1, -1):
            bits.append((val >> i) & 1)

    put(0b0100, 4)
    put(len(data), 8 if ver < 10 else 16)
    for b in data:
        put(b, 8)
    cap = ncw * 8
    put(0, min(4, cap - len(bits)))
    while len(bits) % 8:
        bits.append(0)
    pad = [0xEC, 0x11]
    i = 0
    while len(bits) < cap:
        put(pad[i % 2], 8)
        i += 1
    cws = [int(''.join(str(b) for b in bits[i:i + 8]), 2) for i in range(0, len(bits), 8)]

    nb = _BLOCKS[ver]
    short = ncw // nb
    long_n = ncw % nb
    blocks, p = [], 0
    for i in range(nb):
        ln = short + (1 if i >= nb - long_n else 0)
        blocks.append(cws[p:p + ln])
        p += ln
    ecs = [_rs(b, _EC_CW[ver]) for b in blocks]

    inter = []
    for i in range(max(len(b) for b in blocks)):
        for b in blocks:
            if i < len(b):
                inter.append(b[i])
    for i in range(_EC_CW[ver]):
        for e in ecs:
            inter.append(e[i])

    m = [[None] * size for _ in range(size)]
    fn = [[False] * size for _ in range(size)]

    def finder(r, c):
        for dr in range(-1, 8):
            for dc in range(-1, 8):
                rr, cc = r + dr, c + dc
                if 0 <= rr < size and 0 <= cc < size:
                    d = max(abs(dr - 3), abs(dc - 3))
                    m[rr][cc] = d in (0, 1, 3)
                    fn[rr][cc] = True

    finder(0, 0)
    finder(0, size - 7)
    finder(size - 7, 0)
    for i in range(size):
        if not fn[6][i]:
            m[6][i] = i % 2 == 0
            fn[6][i] = True
        if not fn[i][6]:
            m[i][6] = i % 2 == 0
            fn[i][6] = True
    for r in _ALIGN[ver]:
        for c in _ALIGN[ver]:
            if fn[r][c]:
                continue
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    m[r + dr][c + dc] = max(abs(dr), abs(dc)) != 1
                    fn[r + dr][c + dc] = True
    # zonas reservadas de formato
    for i in range(9):
        if i != 6:
            if not fn[8][i]:
                m[8][i], fn[8][i] = False, True
            if not fn[i][8]:
                m[i][8], fn[i][8] = False, True
    for i in range(8):
        if not fn[8][size - 1 - i]:
            m[8][size - 1 - i], fn[8][size - 1 - i] = False, True
        if not fn[size - 1 - i][8]:
            m[size - 1 - i][8], fn[size - 1 - i][8] = False, True
    m[size - 8][8], fn[size - 8][8] = True, True   # módulo oscuro

    # datos en zigzag
    dbits = []
    for b in inter:
        for i in range(7, -1, -1):
            dbits.append((b >> i) & 1)
    idx = 0
    col = size - 1
    up = True
    while col > 0:
        if col == 6:
            col -= 1
        for i in range(size):
            r = size - 1 - i if up else i
            for c in (col, col - 1):
                if not fn[r][c]:
                    m[r][c] = (dbits[idx] == 1) if idx < len(dbits) else False
                    idx += 1
        up = not up
        col -= 2

    def mask_fn(k, r, c):
        return [lambda: (r + c) % 2 == 0,
                lambda: r % 2 == 0,
                lambda: c % 3 == 0,
                lambda: (r + c) % 3 == 0,
                lambda: (r // 2 + c // 3) % 2 == 0,
                lambda: (r * c) % 2 + (r * c) % 3 == 0,
                lambda: ((r * c) % 2 + (r * c) % 3) % 2 == 0,
                lambda: ((r + c) % 2 + (r * c) % 3) % 2 == 0][k]()

    def penalty(mm):
        p = 0
        for line in list(mm) + [list(col) for col in zip(*mm)]:
            run, prev = 1, line[0]
            for v in line[1:]:
                if v == prev:
                    run += 1
                else:
                    if run >= 5:
                        p += 3 + (run - 5)
                    run, prev = 1, v
            if run >= 5:
                p += 3 + (run - 5)
        for r in range(size - 1):
            for c in range(size - 1):
                if mm[r][c] == mm[r][c + 1] == mm[r + 1][c] == mm[r + 1][c + 1]:
                    p += 3
        dark = sum(sum(1 for v in row if v) for row in mm)
        p += abs(dark * 100 // (size * size) - 50) // 5 * 10
        return p

    best, best_p, best_k = None, None, 0
    for k in range(8):
        mm = [[m[r][c] != (mask_fn(k, r, c) and not fn[r][c]) for c in range(size)]
              for r in range(size)]
        f = _fmt_bits(k)
        for i in range(15):
            bit = ((f >> i) & 1) == 1
            if i < 6:
                mm[8][i] = bit
            elif i == 6:
                mm[8][7] = bit
            elif i == 7:
                mm[8][8] = bit
            elif i == 8:
                mm[7][8] = bit
            else:
                mm[14 - i][8] = bit
            if i < 8:
                mm[size - 1 - i][8] = bit
            else:
                mm[8][size - 15 + i] = bit
        mm[size - 8][8] = True
        p = penalty(mm)
        if best_p is None or p < best_p:
            best, best_p, best_k = mm, p, k
    return size, best


def draw_qr(page, text, x, y, box, fg='#000000', bg='#ffffff', quiet=2):
    """Dibuja el QR dentro de un cuadrado de lado `box`."""
    size, m = qr_matrix(text)
    total = size + quiet * 2
    s = box / total
    if bg:
        page.rect(x, y, box, box, fill=bg)
    page._c(fg)
    runs = []
    for r in range(size):
        c = 0
        while c < size:
            if m[r][c]:
                c0 = c
                while c < size and m[r][c]:
                    c += 1
                runs.append((r, c0, c - c0))
            else:
                c += 1
    for (r, c0, n) in runs:
        px = x + (quiet + c0) * s
        py = y + (quiet + r) * s
        page.ops.append('%.3f %.3f %.3f %.3f re' % (px, page._y(py + s), n * s, s))
    page.ops.append('f')
