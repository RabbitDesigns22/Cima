"""Genera los vectores (SVG/PDF, texto convertido a trazos) de la tarjeta NFConecta.

Tamaño tarjeta CR80: 85.6 x 54 mm, radio de esquina 3.18 mm. Unidades en mm.
Capas por color (convención láser):
  - Rojo  #FF0000 hairline : CORTE (contorno de la tarjeta)
  - Negro #000000 relleno  : GRABADO
  - Azul  #1E3F8A relleno  : GRABADO + RELLENO DE COLOR
Requiere: fonttools, shapely, cairosvg. Uso: python3 vectores/generar.py
"""
import math
import os

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

OUT = os.path.dirname(os.path.abspath(__file__))
W, H, R = 85.6, 54.0, 3.18
BLUE, BLACK, CUT, WOOD = "#1E3F8A", "#000000", "#FF0000", "#D9B27C"


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


BOLD, SEMI = Font("Poppins-Bold.ttf"), Font("Poppins-SemiBold.ttf")


def rbox(x, y, w, h, r):
    return box(x + r, y + r, x + w - r, y + h - r).buffer(r, quad_segs=16)


def d(geom):
    """Geometría shapely -> path SVG (usar con fill-rule evenodd)."""
    polys = getattr(geom, "geoms", [geom])
    ring = lambda c: "M" + "L".join(f"{x:.3f},{y:.3f}" for x, y in list(c.coords)[:-1]) + "Z"
    return "".join(ring(p.exterior) + "".join(ring(i) for i in p.interiors) for p in polys)


def wave(cx, cy, r, t, half, side):
    """Onda en forma de media luna: gruesa al centro, afinada en las puntas."""
    n, outer, inner = 90, [], []
    for i in range(n + 1):
        a = -half + 2 * half * i / n
        k = math.cos(math.pi / 2 * a / half) ** 0.7
        th = 0.55 + (t - 0.55) * k
        ang = math.radians(a if side > 0 else 180 - a)
        outer.append((cx + (r + th / 2) * math.cos(ang), cy + (r + th / 2) * math.sin(ang)))
        inner.append((cx + (r - th / 2) * math.cos(ang), cy + (r - th / 2) * math.sin(ang)))
    body = Polygon(outer + inner[::-1])
    tips = [LineString([outer[j], inner[j]]).centroid.buffer(0.275, quad_segs=8) for j in (0, n)]
    return unary_union([body, *tips])


def svg(body, wood):
    outline = rbox(0, 0, W, H, R)
    bg = f'<path d="{d(outline)}" fill="{WOOD}"/>\n' if wood else ""
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">\n'
            f'{bg}{body}\n'
            f'<path id="corte" d="{d(outline)}" fill="none" stroke="{CUT}" stroke-width="0.01"/>\n</svg>\n')


def frente():
    tiles = [("N", "1", True), ("F", "4", True), ("C", "3", True), ("O", "1", False),
             ("N", "1", False), ("E", "1", False), ("C", "3", False), ("T", "1", False), ("A", "1", False)]
    s, g, r, sh = 7.8, 0.55, 1.1, 0.3
    x0 = (W - (len(tiles) * s + (len(tiles) - 1) * g)) / 2
    y0 = (H - s) / 2
    color, grabado = [], []
    for i, (letra, num, azul) in enumerate(tiles):
        x = x0 + i * (s + g)
        tile = rbox(x, y0, s, s, r)
        # Sombra inferior derecha: da volumen de ficha física.
        sombra = rbox(x + sh, y0 + sh, s, s, r).difference(tile)
        letra_d = BOLD.path(letra, 5.9, x + s / 2 - 0.2, y0 + s / 2 - 0.15)
        num_d = BOLD.path(num, 1.6, x + s - 1.3, y0 + s - 1.35)
        grabado.append(f'<path d="{d(sombra)}"/>')
        if azul:
            # Ficha rellena en azul con bisel fino; letra y número quedan en madera.
            bisel = rbox(x + 0.45, y0 + 0.45, s - 0.9, s - 0.9, r - 0.45)
            bisel = bisel.difference(bisel.buffer(-0.14, quad_segs=16))
            color.append(f'<path d="{d(tile.difference(bisel))}{letra_d}{num_d}" fill-rule="evenodd"/>')
        else:
            marco = tile.difference(tile.buffer(-0.24, quad_segs=16))
            grabado.append(f'<path d="{d(marco)}"/><path d="{letra_d}{num_d}"/>')
    return (f'<g id="relleno-azul" fill="{BLUE}">{"".join(color)}</g>\n'
            f'<g id="grabado" fill="{BLACK}" fill-rule="evenodd">{"".join(grabado)}</g>')


def reverso(cta=False):
    cx, cy = W / 2, H / 2 - (2.2 if cta else 0)
    b = 14.0
    square = rbox(cx - b / 2, cy - b / 2, b, b, 3.2)
    # N geométrica calada en el cuadro.
    m, t = 3.6, 2.15
    l, rr, top, bot = cx - b / 2 + m, cx + b / 2 - m, cy - b / 2 + m - 0.2, cy + b / 2 - m + 0.2
    dg = t * 1.3
    n = unary_union([box(l, top, l + t, bot), box(rr - t, top, rr, bot),
                     Polygon([(l, top), (l + dg, top), (rr, bot), (rr - dg, bot)])])
    marca = square.difference(n)
    # Marco fino exterior para un acabado más premium.
    halo = square.buffer(1.0, quad_segs=16).difference(square.buffer(0.72, quad_segs=16))
    parts = [marca, halo]
    for radio, t_w, half in ((12.4, 2.0, 46), (16.9, 2.1, 40), (21.4, 2.2, 34)):
        parts += [wave(cx, cy, radio, t_w, half, 1), wave(cx, cy, radio, t_w, half, -1)]
    body = f'<path d="{d(unary_union(parts))}"/>'
    if cta:
        body += f'<path d="{SEMI.path("ACERCA TU CELULAR", 2.1, W / 2, H - 7.2, tracking=0.55)}"/>'
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
