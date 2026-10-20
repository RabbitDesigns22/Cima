"""Genera los vectores (SVG/PDF, texto convertido a trazos) de la tarjeta NFConecta, estilo victoriano.

Tamaño tarjeta CR80: 85.6 x 54 mm, radio de esquina 3.18 mm. Unidades en mm.
Capas por color (convención láser):
  - Rojo  #FF0000 hairline : CORTE (contorno de la tarjeta)
  - Negro #000000 relleno  : GRABADO
  - Azul  #1B2F6B relleno  : GRABADO + RELLENO DE COLOR
Requiere: fonttools, shapely, cairosvg. Uso: python3 vectores/generar.py
"""
import math
import os

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

OUT = os.path.dirname(os.path.abspath(__file__))
W, H, R = 85.6, 54.0, 3.18
BLUE, BLACK, CUT, WOOD = "#1B2F6B", "#000000", "#FF0000", "#D9B27C"


class Font:
    def __init__(self, name):
        self.font = TTFont(os.path.join(OUT, "fuentes", name))
        self.glyphs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.upm = self.font["head"].unitsPerEm
        self.cap = self.font["OS/2"].sCapHeight

    def path(self, text, size, cx, cy, tracking=0.0):
        """Texto centrado (horizontal y por altura de mayúscula) como path SVG."""
        s = size / self.upm
        names = [self.cmap[ord(c)] for c in text]
        width = sum(self.glyphs[n].width * s for n in names) + tracking * (len(names) - 1)
        x, base = cx - width / 2, cy + self.cap * s / 2
        pen = SVGPathPen(self.glyphs, ntos=lambda v: f"{v:.3f}".rstrip("0").rstrip("."))
        for n in names:
            self.glyphs[n].draw(TransformPen(pen, (s, 0, 0, -s, x, base)))
            x += self.glyphs[n].width * s + tracking
        return pen.getCommands()


BLACKF = Font("PlayfairDisplay-Black.ttf")
BOLDF = Font("PlayfairDisplay-Bold.ttf")
ITALIC = Font("PlayfairDisplay-SemiBoldItalic.ttf")


# ---------- geometría ----------

def d(geom):
    """Geometría shapely -> path SVG (usar con fill-rule evenodd)."""
    polys = getattr(geom, "geoms", [geom])
    ring = lambda c: "M" + "L".join(f"{x:.3f},{y:.3f}" for x, y in list(c.coords)[:-1]) + "Z"
    return "".join(ring(p.exterior) + "".join(ring(i) for i in p.interiors) for p in polys)


def rbox(x, y, w, h, r):
    return box(x + r, y + r, x + w - r, y + h - r).buffer(r, quad_segs=16)


def notched(x, y, w, h, r, cr=None):
    """Rectángulo con esquinas cóncavas (recorte victoriano)."""
    cr = cr or (x, y, x + w, y + h)
    x0, y0, x1, y1 = cr
    cuts = [Point(px, py).buffer(r, quad_segs=24) for px in (x0, x1) for py in (y0, y1)]
    return box(x, y, x + w, y + h).difference(unary_union(cuts))


def ring(shape, t):
    return shape.difference(shape.buffer(-t, join_style="mitre", mitre_limit=10))


def bez(p0, p1, p2, p3, n=40):
    return [tuple((1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t ** 2 * c + t ** 3 * e
                  for a, b, c, e in zip(p0, p1, p2, p3)) for t in (i / n for i in range(n + 1))]


def spiral(c, r0, r1, a0, a1, n=90):
    out = []
    for i in range(n + 1):
        t = i / n
        a, r = math.radians(a0 + (a1 - a0) * t), r0 + (r1 - r0) * t
        out.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    return out


def taper(pts, wfun, ball=0.0):
    """Trazo caligráfico: ancho variable a lo largo de la curva, remate en bola opcional."""
    pts = [p for i, p in enumerate(pts) if i == 0 or math.dist(p, pts[i - 1]) > 1e-6]
    acc = [0.0]
    for a, b in zip(pts, pts[1:]):
        acc.append(acc[-1] + math.dist(a, b))
    left, right = [], []
    for i, p in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy)
        nx, ny = -dy / ln, dx / ln
        w = wfun(acc[i] / acc[-1]) / 2
        left.append((p[0] + nx * w, p[1] + ny * w))
        right.append((p[0] - nx * w, p[1] - ny * w))
    g = Polygon(left + right[::-1]).buffer(0)
    if ball:
        g = g.union(Point(pts[-1]).buffer(ball, quad_segs=12))
    return g


def mirror_xy(g):
    """Refleja respecto a la diagonal y = x."""
    return affinity.affine_transform(g, [0, 1, 1, 0, 0, 0])


# ---------- ornamentos ----------

O1, T1, O2, T2, NR = 2.0, 0.32, 2.75, 0.12, 2.3  # marco: insets, grosores, radio de muesca


def marco():
    corners = (O1, O1, W - O1, H - O1)
    outer = ring(notched(O1, O1, W - 2 * O1, H - 2 * O1, NR, corners), T1)
    inner = ring(notched(O2, O2, W - 2 * O2, H - 2 * O2, NR + (O2 - O1), corners), T2)
    dots = [Point(px, py).buffer(0.42, quad_segs=12)
            for px in (O1 + 0.95, W - O1 - 0.95) for py in (O1 + 0.95, H - O1 - 0.95)]
    return unary_union([outer, inner, *dots, *esquinas()])


def esquina():
    """Ornamento de esquina en coordenadas locales (esquina en el origen)."""
    curva = bez((4.0, 6.6), (4.0, 4.9), (5.2, 4.25), (7.4, 4.25), 30)[:-1]
    curva += bez((7.4, 4.25), (9.0, 4.25), (10.4, 4.0), (11.6, 4.25), 20)[:-1]
    curva += spiral((11.6, 5.55), 1.3, 0.45, -90, 250)
    wf = lambda t: 0.04 + min(1, t / 0.1) * (0.58 - 0.4 * t)
    voluta = taper(curva, wf, ball=0.36)
    lado = voluta
    hoja = taper(bez((4.3, 4.3), (5.6, 5.0), (7.0, 6.6), (8.6, 8.6)),
                 lambda t: 1.5 * math.sin(math.pi * t) ** 0.85 + 0.05)
    nervio = taper(bez((4.9, 4.9), (6.0, 5.6), (6.8, 6.6), (7.7, 7.7)), lambda t: 0.16 * (1 - t) + 0.04)
    gota = Point(9.35, 9.35).buffer(0.38, quad_segs=12)
    return unary_union([lado, mirror_xy(lado), hoja.difference(nervio), gota])


def esquinas():
    e = esquina()
    return [e, affinity.scale(e, -1, 1, origin=(W / 2, H / 2)),
            affinity.scale(e, 1, -1, origin=(W / 2, H / 2)), affinity.scale(e, -1, -1, origin=(W / 2, H / 2))]


def divisor(cx, cy, half, up=True):
    """Filete ornamental horizontal con rombo central y remates en voluta."""
    rombo = affinity.rotate(box(-0.75, -0.75, 0.75, 0.75), 45).buffer(0)
    rombo = affinity.translate(rombo, cx, cy).difference(Point(cx, cy).buffer(0.3, quad_segs=12))
    s = -1 if up else 1
    linea = [(cx + 2.4 + (half - 2.4) * i / 40, cy) for i in range(41)][:-1]
    linea += spiral((cx + half, cy + s * 0.85), 0.85, 0.25, -90 * s, -90 * s + 290 * s, 60)
    brazo = taper(linea, lambda t: 0.55 * (1 - t) ** 0.6 + 0.1, ball=0.24)
    punto = Point(cx + 1.75, cy).buffer(0.32, quad_segs=12)
    lado = unary_union([brazo, punto])
    return unary_union([rombo, lado, affinity.scale(lado, -1, 1, origin=(cx, cy))])


def svg(body, wood):
    outline = rbox(0, 0, W, H, R)
    bg = f'<path d="{d(outline)}" fill="{WOOD}"/>\n' if wood else ""
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">\n'
            f'{bg}{body}\n'
            f'<path id="corte" d="{d(outline)}" fill="none" stroke="{CUT}" stroke-width="0.01"/>\n</svg>\n')


# ---------- caras ----------

def frente():
    tiles = [("N", "1", True), ("F", "4", True), ("C", "3", True), ("O", "1", False),
             ("N", "1", False), ("E", "1", False), ("C", "3", False), ("T", "1", False), ("A", "1", False)]
    s, g, nr = 7.5, 0.55, 0.85
    x0 = (W - (len(tiles) * s + (len(tiles) - 1) * g)) / 2
    y0 = (H - s) / 2
    color, grabado, texto = [], [marco(), divisor(W / 2, y0 - 4.2, 17.5, True),
                                 divisor(W / 2, y0 + s + 4.2, 17.5, False)], []
    for i, (letra, num, azul) in enumerate(tiles):
        x = x0 + i * (s + g)
        tile = notched(x, y0, s, s, nr)
        filete = ring(tile.buffer(-0.55, join_style="mitre", mitre_limit=10), 0.11)
        letra_d = BLACKF.path(letra, 5.7, x + s / 2 - 0.2, y0 + s / 2 - 0.25)
        num_d = BOLDF.path(num, 1.6, x + s - 1.75, y0 + s - 1.9)
        if azul:
            # Ficha rellena en azul; filete interior, letra y número quedan en madera.
            color.append(f'<path d="{d(tile.difference(filete))}{letra_d}{num_d}"/>')
        else:
            grabado += [ring(tile, 0.24), filete]
            texto.append(letra_d + num_d)
    return (f'<g id="relleno-azul" fill="{BLUE}" fill-rule="evenodd">{"".join(color)}</g>\n'
            f'<g id="grabado" fill="{BLACK}" fill-rule="evenodd">'
            f'<path d="{d(unary_union(grabado))}"/><path d="{"".join(texto)}"/></g>')


def onda(cx, cy, r, t, half, side):
    """Onda en media luna con remates de bola en las puntas."""
    n, outer, inner, mid = 90, [], [], []
    for i in range(n + 1):
        a = -half + 2 * half * i / n
        th = 0.5 + (t - 0.5) * math.cos(math.pi / 2 * a / half) ** 0.7
        ang = math.radians(a if side > 0 else 180 - a)
        c, sn = math.cos(ang), math.sin(ang)
        outer.append((cx + (r + th / 2) * c, cy + (r + th / 2) * sn))
        inner.append((cx + (r - th / 2) * c, cy + (r - th / 2) * sn))
        mid.append((cx + r * c, cy + r * sn))
    bolas = [Point(mid[j]).buffer(0.55, quad_segs=12) for j in (0, n)]
    return unary_union([Polygon(outer + inner[::-1]), *bolas])


def medallon(cx, cy):
    disco = Point(cx, cy).buffer(7.0, quad_segs=48)
    aro = Point(cx, cy).buffer(8.0, quad_segs=48).difference(Point(cx, cy).buffer(7.75, quad_segs=48))
    perlas = [Point(cx + 9.0 * math.cos(2 * math.pi * k / 40), cy + 9.0 * math.sin(2 * math.pi * k / 40))
              .buffer(0.3, quad_segs=8) for k in range(40)]
    return unary_union([disco, aro, *perlas])


def reverso(cta=False):
    cx, cy = W / 2, H / 2 - (2.6 if cta else 0)
    geo = [marco(), medallon(cx, cy)]
    for radio, t_w, half in ((12.6, 1.8, 48), (16.6, 2.0, 41), (20.6, 2.2, 35)):
        geo += [onda(cx, cy, radio, t_w, half, 1), onda(cx, cy, radio, t_w, half, -1)]
    # La N queda calada en madera dentro del medallón.
    body = f'<path d="{d(unary_union(geo))}{BLACKF.path("N", 10.5, cx - 0.15, cy - 0.1)}"/>'
    if cta:
        ty = H - 8.6
        body += f'<path d="{ITALIC.path("Acerca tu celular", 3.1, W / 2, ty)}"/>'
        body += f'<path d="{d(divisor(W / 2, ty + 3.2, 13.5, False))}"/>'
    return f'<g id="grabado" fill="{BLACK}" fill-rule="evenodd">{body}</g>'


if __name__ == "__main__":
    import cairosvg

    piezas = (("frente", frente), ("reverso", reverso), ("reverso_cta", lambda: reverso(True)))
    for nombre, fn in piezas:
        body = fn()
        for sufijo, wood in (("", False), ("_preview", True)):
            with open(os.path.join(OUT, f"nfconecta_{nombre}{sufijo}.svg"), "w") as f:
                f.write(svg(body, wood))
        cairosvg.svg2pdf(url=os.path.join(OUT, f"nfconecta_{nombre}.svg"),
                         write_to=os.path.join(OUT, f"nfconecta_{nombre}.pdf"))
        cairosvg.svg2png(url=os.path.join(OUT, f"nfconecta_{nombre}_preview.svg"),
                         write_to=os.path.join(OUT, f"nfconecta_{nombre}_preview.png"),
                         output_width=1712)
