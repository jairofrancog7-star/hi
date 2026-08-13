"""Pruebas del motor: bits de formato QR contra la tabla ISO, decodificación
de vuelta del QR, y estructura básica del PDF."""
import re
import sys
sys.path.insert(0, '/projects/sandbox/src')
import pdfkit as pk

fails = []

# ---------------------------------------------------------------- formato QR
TABLA_L = ['111011111000100', '111001011110011', '111110110101010', '111100010011101',
           '110011000101111', '110001100011000', '110110001000001', '110100101110110']
for k in range(8):
    got = format(pk._fmt_bits(k), '015b')
    if got != TABLA_L[k]:
        fails.append('formato mask %d: %s != %s' % (k, got, TABLA_L[k]))
print('formato QR nivel L contra tabla ISO: %s' % ('OK' if not fails else 'FALLA'))


# ---------------------------------------------------------------- decodificador
def decode(size, m):
    """Lee la matriz de vuelta: formato, desenmascarado, de-interleave, texto."""
    ver = (size - 17) // 4
    # leer formato de la copia superior izquierda
    bits = 0
    for i in range(15):
        if i < 6:
            b = m[8][i]
        elif i == 6:
            b = m[8][7]
        elif i == 7:
            b = m[8][8]
        elif i == 8:
            b = m[7][8]
        else:
            b = m[14 - i][8]
        bits |= (1 if b else 0) << i
    raw = bits ^ 0x5412
    ecl, mask = (raw >> 13) & 3, (raw >> 10) & 7
    assert ecl == 0b01, 'nivel de correccion leido != L'

    fn = [[False] * size for _ in range(size)]

    def mark(r, c):
        if 0 <= r < size and 0 <= c < size:
            fn[r][c] = True
    for (r0, c0) in ((0, 0), (0, size - 7), (size - 7, 0)):
        for dr in range(-1, 8):
            for dc in range(-1, 8):
                mark(r0 + dr, c0 + dc)
    for i in range(size):
        mark(6, i)
        mark(i, 6)
    for r in pk._ALIGN[ver]:
        for c in pk._ALIGN[ver]:
            if fn[r][c]:
                continue
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    mark(r + dr, c + dc)
    for i in range(9):
        mark(8, i)
        mark(i, 8)
    for i in range(8):
        mark(8, size - 1 - i)
        mark(size - 1 - i, 8)

    def mfn(k, r, c):
        return [lambda: (r + c) % 2 == 0, lambda: r % 2 == 0, lambda: c % 3 == 0,
                lambda: (r + c) % 3 == 0, lambda: (r // 2 + c // 3) % 2 == 0,
                lambda: (r * c) % 2 + (r * c) % 3 == 0,
                lambda: ((r * c) % 2 + (r * c) % 3) % 2 == 0,
                lambda: ((r + c) % 2 + (r * c) % 3) % 2 == 0][k]()

    out = []
    col, up = size - 1, True
    while col > 0:
        if col == 6:
            col -= 1
        for i in range(size):
            r = size - 1 - i if up else i
            for c in (col, col - 1):
                if not fn[r][c]:
                    v = m[r][c] != mfn(mask, r, c)
                    out.append(1 if v else 0)
        up = not up
        col -= 2
    cw = [int(''.join(str(b) for b in out[i:i + 8]), 2) for i in range(0, len(out) // 8 * 8, 8)]

    ncw = pk._TOTAL[ver] - pk._EC_CW[ver] * pk._BLOCKS[ver]
    nb = pk._BLOCKS[ver]
    short, long_n = ncw // nb, ncw % nb
    lens = [short + (1 if i >= nb - long_n else 0) for i in range(nb)]
    blocks = [[] for _ in range(nb)]
    idx = 0
    for i in range(max(lens)):
        for b in range(nb):
            if i < lens[b]:
                blocks[b].append(cw[idx])
                idx += 1
    data = [b for blk in blocks for b in blk]

    bitstr = ''.join(format(b, '08b') for b in data)
    mode = int(bitstr[:4], 2)
    assert mode == 4, 'modo != byte'
    nl = 8 if ver < 10 else 16
    ln = int(bitstr[4:4 + nl], 2)
    body = bitstr[4 + nl:4 + nl + ln * 8]
    return bytes(int(body[i:i + 8], 2) for i in range(0, len(body), 8)).decode('utf-8')


urls = ['https://youtu.be/t8h12fy3aAw', 'https://youtu.be/sW7Z7gwrjoc',
        'https://youtu.be/bPqqiwOdK8w',
        'https://www.youtube.com/results?search_query=control+orientado+futbol',
        'https://github.com/jairofrancog7-star/hi']
ok = 0
for u in urls:
    size, m = pk.qr_matrix(u)
    try:
        back = decode(size, m)
    except Exception as e:
        fails.append('QR %s: %s' % (u, e))
        continue
    if back != u:
        fails.append('QR round-trip: %r != %r' % (back, u))
    else:
        ok += 1
print('QR decodificados correctamente: %d/%d' % (ok, len(urls)))

# síndromes Reed-Solomon en cero
for u in urls[:2]:
    d = u.encode()
    ec = pk._rs(list(d), 10)
    full = list(d) + ec
    for k in range(10):
        s = 0
        for c in full:
            s = pk._mul(s, pk._EXP[k]) ^ c
        if s != 0:
            fails.append('sindrome RS != 0')
print('sindromes Reed-Solomon: OK')

# ---------------------------------------------------------------- PDF
doc = pk.Doc()
p = doc.page(595.28, 841.89)
p.rect(0, 0, 595.28, 841.89, fill='#fff7fa')
p.text(40, 40, 'Prueba áéíóú ñ ¿¡ — “x” ·', 22, bold=True, color='#c2185b')
p.roundrect(40, 90, 200, 60, 8, fill='#111', stroke='#e91e63', lw=2)
p.circle(300, 200, 20, fill='#e91e63', stroke='#111')
p.arrow(40, 300, 200, 340, '#e91e63', 2)
p.wavy(40, 380, 200, 380, '#00897b', 2)
p.line(40, 420, 300, 420, '#999', 1, dash=[3, 3])
pk.draw_qr(p, 'https://youtu.be/t8h12fy3aAw', 400, 300, 120)
p.link(40, 40, 200, 24, 'https://youtu.be/t8h12fy3aAw')
n = doc.save('/tmp/test.pdf')

raw = open('/tmp/test.pdf', 'rb').read()
if not raw.startswith(b'%PDF-1.4'):
    fails.append('cabecera PDF')
sx = int(re.search(rb'startxref\s+(\d+)', raw).group(1))
if raw[sx:sx + 4] != b'xref':
    fails.append('startxref no apunta a xref')
# comprobar que cada offset apunta a "N 0 obj"
for i, mt in enumerate(re.finditer(rb'^(\d{10}) 00000 n $', raw[sx:].decode('latin-1').encode('latin-1'), re.M)):
    off = int(mt.group(1))
    if off and not raw[off:off + 40].startswith(b'%d 0 obj' % (i + 1)):
        fails.append('offset objeto %d incorrecto' % (i + 1))
if b'/Subtype /Link' not in raw:
    fails.append('sin anotacion de enlace')
print('PDF de prueba: %d bytes, estructura OK' % n)

print()
if fails:
    print('%d FALLAS:' % len(fails))
    for f in fails:
        print(' -', f)
    sys.exit(1)
print('TODO OK')
