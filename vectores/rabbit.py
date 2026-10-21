"""Tarjeta metálica Rabbit Designs: archivos DTF UV (negro sobre transparente) y vistas previas.

- Frente: logo RABBIT / DESIGNS con el conejo sobre la I.
- Reverso: el conejo solo.
Los PNG de impresión son 100% negro sobre fondo transparente: el metal queda a la vista.
Tamaño CR80 85.6 x 54 mm a 1200 ppp. Uso: python3 vectores/rabbit.py
"""
import io
import os

import cairosvg
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image
from shapely import affinity
from shapely.geometry import Point
from shapely.ops import unary_union

from generar import d, rbox
from metal import cepillado

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "rabbit")
W, H, R, DPI = 85.6, 54.0, 3.18, 1200
INK = "#000000"


class Font:
    def __init__(self, name):
        f = TTFont(os.path.join(BASE, "fuentes", name))
        self.glyphs, self.cmap = f.getGlyphSet(), f.getBestCmap()
        self.upm, self.cap = f["head"].unitsPerEm, f["OS/2"].sCapHeight

    def advances(self, text, size, tracking=0.0):
        s = size / self.upm
        names = [self.cmap[ord(c)] for c in text]
        adv = [self.glyphs[n].width * s for n in names]
        return names, adv, sum(adv) + tracking * (len(names) - 1)

    def path(self, text, size, x, base, tracking=0.0):
        """Texto desde x (izquierda) sobre la línea base; devuelve (path, posiciones x de cada letra)."""
        s = size / self.upm
        names, adv, _ = self.advances(text, size, tracking)
        pen = SVGPathPen(self.glyphs, ntos=lambda v: f"{v:.3f}".rstrip("0").rstrip("."))
        xs = []
        for n, a in zip(names, adv):
            xs.append(x)
            self.glyphs[n].draw(TransformPen(pen, (s, 0, 0, -s, x, base)))
            x += a + tracking
        return pen.getCommands(), xs

    def ink_bounds(self, ch, size):
        """Límites horizontales reales (sin márgenes laterales) de un glifo."""
        from fontTools.pens.boundsPen import BoundsPen
        bp = BoundsPen(self.glyphs)
        self.glyphs[self.cmap[ord(ch)]].draw(bp)
        s = size / self.upm
        return bp.bounds[0] * s, bp.bounds[2] * s


BLACK, LIGHT = Font("Montserrat-Black.ttf"), Font("Montserrat-Light.ttf")


def conejo():
    """Silueta del conejo (cabeza + oreja recta + oreja doblada). Base de la cabeza en y=0, alto ~2."""
    elipse = lambda cx, cy, rx, ry, rot: affinity.rotate(
        affinity.scale(Point(cx, cy).buffer(1, quad_segs=48), rx, ry), rot, origin=(cx, cy))
    cabeza = elipse(0, -0.38, 0.6, 0.38, 0)
    izq = elipse(-0.24, -1.26, 0.16, 0.68, -9)
    der_base = elipse(0.24, -1.0, 0.15, 0.46, 12)
    der_punta = elipse(0.56, -1.38, 0.33, 0.13, 10)
    g = unary_union([cabeza, izq, der_base, der_punta])
    return g.buffer(0.09, quad_segs=16).buffer(-0.09, quad_segs=16)  # suaviza las uniones


def frente_svg():
    size = 14.0  # cuerpo de RABBIT
    _, _, ancho = BLACK.advances("RABBIT", size, tracking=-0.35)
    l0, _ = BLACK.ink_bounds("R", size)
    _, r1 = BLACK.ink_bounds("T", size)
    t_adv = BLACK.advances("T", size)[1][0]
    ink_w = ancho - l0 - (t_adv - r1)
    x = (W - ink_w) / 2 - l0
    cap = BLACK.cap * size / BLACK.upm
    base = H / 2 + 4.2
    rabbit, xs = BLACK.path("RABBIT", size, x, base, tracking=-0.35)
    # DESIGNS justificado al ancho de RABBIT.
    dsize = 5.0
    dl0, _ = LIGHT.ink_bounds("D", dsize)
    _, dr1 = LIGHT.ink_bounds("S", dsize)
    _, _, dw0 = LIGHT.advances("DESIGNS", dsize)
    s_adv = LIGHT.advances("S", dsize)[1][0]
    d_ink = dw0 - dl0 - (s_adv - dr1)
    track = (ink_w - d_ink) / 6
    designs, _ = LIGHT.path("DESIGNS", dsize, x + l0 - dl0, base + 2.4 + LIGHT.cap * dsize / LIGHT.upm, track)
    # Conejo centrado sobre la I.
    i0, i1 = BLACK.ink_bounds("I", size)
    cx = xs[4] + (i0 + i1) / 2
    c = affinity.scale(conejo(), 4.6, 4.6, origin=(0, 0))
    c = affinity.translate(c, cx, base - cap - 0.35)
    return f'<path d="{rabbit}{designs}"/><path d="{d(c)}" fill-rule="evenodd"/>'


def reverso_svg():
    c = conejo()
    minx, miny, maxx, maxy = c.bounds
    k = 30.0 / (maxy - miny)
    c = affinity.scale(c, k, k, origin=(0, 0))
    minx, miny, maxx, maxy = c.bounds
    c = affinity.translate(c, W / 2 - (minx + maxx) / 2, H / 2 - (miny + maxy) / 2)
    return f'<path d="{d(c)}" fill-rule="evenodd"/>'


def doc(body, metal=False):
    fondo = (f'<defs><linearGradient id="acero" x1="0" y1="0" x2="1" y2="1">'
             f'<stop offset="0" stop-color="#B4B8BD"/><stop offset="0.45" stop-color="#DDE0E3"/>'
             f'<stop offset="0.6" stop-color="#D2D5D9"/><stop offset="1" stop-color="#A9AEB4"/></linearGradient></defs>'
             f'<path d="{d(rbox(0, 0, W, H, R))}" fill="url(#acero)"/>') if metal else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">'
            f'{fondo}<g fill="{INK}">{body}</g></svg>')


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    px = round(W / 25.4 * DPI)
    for cara, body in (("frente", frente_svg()), ("reverso", reverso_svg())):
        with open(os.path.join(OUT, f"rabbit_{cara}_dtf.svg"), "w") as f:
            f.write(doc(body))
        cairosvg.svg2png(bytestring=doc(body).encode(), write_to=os.path.join(OUT, f"rabbit_{cara}_dtf.png"),
                         output_width=px)
        Image.open(os.path.join(OUT, f"rabbit_{cara}_dtf.png")).save(
            os.path.join(OUT, f"rabbit_{cara}_dtf.png"), dpi=(DPI, DPI))
        # Vista previa sobre acero cepillado (solo para ver, no para imprimir).
        prev = cairosvg.svg2png(bytestring=doc(body, metal=True).encode(), output_width=px)
        img = cepillado(Image.open(io.BytesIO(prev)).convert("RGBA"))
        img.resize((px // 2, round(px / 2 * H / W))).save(os.path.join(OUT, f"rabbit_{cara}_vista_previa.png"))
