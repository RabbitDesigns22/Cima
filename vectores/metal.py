"""Tarjeta NFConecta estilo acero cepillado con franjas azules diagonales (PNG para DTF UV).

Genera el frente completo (fondo acero) y una versión sin fondo (solo franjas y fichas).
Todo opaco. Tamaño CR80 85.6 x 54 mm a 1200 ppp. Uso: python3 vectores/metal.py
"""
import io
import math
import os

import cairosvg
import numpy as np
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image
from shapely import affinity
from shapely.geometry import Polygon, box

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "metal")
W, H, R = 85.6, 54.0, 3.18
DPI = 1200
FONT = TTFont("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf")
GLYPHS, CMAP = FONT.getGlyphSet(), FONT.getBestCmap()
UPM, CAP = FONT["head"].unitsPerEm, FONT["OS/2"].sCapHeight

TILES = [("N", "1", True), ("F", "4", True), ("C", "3", True), ("O", "1", False),
         ("N", "1", False), ("E", "1", False), ("C", "3", False), ("T", "1", False), ("A", "1", False)]

DEFS = """<defs>
<linearGradient id="acero" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#B4B8BD"/><stop offset="0.45" stop-color="#DDE0E3"/>
  <stop offset="0.6" stop-color="#D2D5D9"/><stop offset="1" stop-color="#A9AEB4"/></linearGradient>
<linearGradient id="azul" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#14347F"/><stop offset="0.5" stop-color="#2C5FD0"/><stop offset="1" stop-color="#0F2867"/></linearGradient>
<linearGradient id="pulido" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#6F757C"/><stop offset="0.5" stop-color="#F4F6F8"/><stop offset="1" stop-color="#7C828A"/></linearGradient>
<linearGradient id="ficha-azul" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#2450B8"/><stop offset="1" stop-color="#16388E"/></linearGradient>
<linearGradient id="ficha-acero" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#E4E6E9"/><stop offset="1" stop-color="#C3C7CC"/></linearGradient>
<clipPath id="tarjeta"><rect width="85.6" height="54" rx="3.18"/></clipPath>
</defs>"""


def text(t, size, cx, cy):
    s = size / UPM
    names = [CMAP[ord(c)] for c in t]
    x = cx - sum(GLYPHS[n].width for n in names) * s / 2
    pen = SVGPathPen(GLYPHS, ntos=lambda v: f"{v:.3f}".rstrip("0").rstrip("."))
    for n in names:
        GLYPHS[n].draw(TransformPen(pen, (s, 0, 0, -s, x, cy + CAP * s / 2)))
        x += GLYPHS[n].width * s
    return pen.getCommands()


def banda(u0, u1, fill, esquina):
    """Franja diagonal entre distancias u0 y u1 medidas desde la esquina (superior izq. o inferior der.)."""
    phi = math.atan2(21, 16) if esquina == "si" else math.pi / 4
    c, sn = math.cos(phi), math.sin(phi)
    big = 200
    franja = Polygon([(-big * sn + u0 * c, big * c + u0 * sn), (big * sn + u0 * c, -big * c + u0 * sn),
                      (big * sn + u1 * c, -big * c + u1 * sn), (-big * sn + u1 * c, big * c + u1 * sn)])
    if esquina == "ii":
        franja = affinity.rotate(franja, 180, origin=(0, 0))
        franja = affinity.translate(franja, W, H)
    g = franja.intersection(box(0, 0, W, H))
    p = " ".join(f"{x:.3f},{y:.3f}" for x, y in list(g.exterior.coords)[:-1])
    return f'<polygon points="{p}" fill="{fill}"/>'


def franjas():
    negro, blanco = "#111317", "#F5F7FA"
    si = [(11.0, 11.25, negro), (11.25, 13.8, "url(#azul)"), (13.8, 14.05, negro),
          (14.05, 15.4, "url(#pulido)"), (15.4, 15.65, negro), (16.8, 16.95, negro)]
    ii = [(-1, 12.5, "url(#azul)"), (12.5, 12.7, blanco), (12.7, 14.6, "url(#pulido)"), (14.6, 14.85, negro),
          (14.85, 15.0, blanco), (15.0, 16.4, "url(#azul)"), (16.4, 16.65, negro)]
    return "".join(banda(a, b, f, "si") for a, b, f in si) + "".join(banda(a, b, f, "ii") for a, b, f in ii)


def fichas():
    s, g, r = 7.7, 0.6, 0.7
    x0 = (W - (9 * s + 8 * g)) / 2
    y0 = H / 2 - s / 2 + 1.0
    out = []
    for i, (letra, num, azul) in enumerate(TILES):
        x = x0 + i * (s + g)
        if azul:
            cara, borde, tinta = "url(#ficha-azul)", "#0D2260", "#DADDE1"
        else:
            cara, borde, tinta = "url(#ficha-acero)", "#111317", "#111317"
        out.append(f'<rect x="{x:.3f}" y="{y0:.3f}" width="{s}" height="{s}" rx="{r}" fill="{borde}"/>'
                   f'<rect x="{x + 0.28:.3f}" y="{y0 + 0.28:.3f}" width="{s - 0.56:.3f}" height="{s - 0.56:.3f}" '
                   f'rx="{r - 0.2}" fill="{cara}"/>'
                   f'<path d="{text(letra, 5.6, x + s / 2 - 0.25, y0 + s / 2 - 0.3)}'
                   f'{text(num, 1.75, x + s - 1.25, y0 + s - 1.3)}" fill="{tinta}"/>')
    return "".join(out)


def svg(con_fondo):
    fondo = f'<rect width="{W}" height="{H}" fill="url(#acero)"/>' if con_fondo else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">'
            f'{DEFS}<g clip-path="url(#tarjeta)">{fondo}{franjas()}</g>{fichas()}</svg>')


def cepillado(img, seed=7):
    """Textura de acero cepillado: vetas horizontales finas, aplicada como variación de luz."""
    a = np.asarray(img).astype(np.float32)
    h, w = a.shape[:2]
    rng = np.random.default_rng(seed)
    ruido = rng.normal(0, 1, (h, w)).astype(np.float32)
    n = 160  # largo de la veta en píxeles
    c = np.cumsum(np.pad(ruido, ((0, 0), (n, 0)), mode="wrap"), axis=1)
    vetas = (c[:, n:] - c[:, :-n]) / math.sqrt(n)
    vetas += rng.normal(0, 0.6, (h, 1)).astype(np.float32)  # variación por fila
    vetas /= vetas.std()
    a[..., :3] *= (1 + 0.045 * vetas)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    px = round(W / 25.4 * DPI)
    for nombre, con_fondo in (("nfconecta_metal_frente", True), ("nfconecta_metal_sin_fondo", False)):
        doc = svg(con_fondo)
        with open(os.path.join(OUT, f"{nombre}.svg"), "w") as f:
            f.write(doc)
        png = cairosvg.svg2png(bytestring=doc.encode(), output_width=px)
        cepillado(Image.open(io.BytesIO(png)).convert("RGBA")).save(
            os.path.join(OUT, f"{nombre}.png"), dpi=(DPI, DPI))
