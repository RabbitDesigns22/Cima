"""Tarjeta metálica Rabbit Designs: archivos DTF UV (negro sobre transparente) y vistas previas.

- Frente: logo RABBIT / DESIGNS con el conejo sobre la I (calcado del original).
- Reverso: el conejo solo.
Los PNG de impresión son 100% negro sobre fondo transparente: el metal queda a la vista.
Tamaño CR80 85.6 x 54 mm a 1200 ppp. Uso: python3 vectores/rabbit.py
"""
import io
import json
import os

import cairosvg
from PIL import Image

from generar import d, rbox
from metal import cepillado

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "rabbit")
W, H, R, DPI = 85.6, 54.0, 3.18, 1200
INK = "#000000"


# Trazado vectorial del logo original (rabbit/fuente/logo_original.jpg) hecho con potrace,
# en coordenadas de píxel del original de 1080 x 1080.
TRAZADO = json.load(open(os.path.join(OUT, "fuente", "trazado.json")))
LOGO_X0, LOGO_X1, LOGO_Y0, LOGO_Y1 = 177, 902, 305, 671  # caja del logo completo
CONEJO_Y0, CONEJO_Y1, CONEJO_X0, CONEJO_X1 = 305, 452, 681, 824  # caja del conejo
ANCHO_LOGO = 55.0  # mm en el frente
ALTO_CONEJO = 30.0  # mm en el reverso


def colocar(paths, x0, x1, y0, y1, k):
    """Escala los trazos (px del original) a mm y los centra en la tarjeta."""
    tx = W / 2 - (x0 + x1) / 2 * k
    ty = H / 2 - (y0 + y1) / 2 * k
    return (f'<g transform="translate({tx:.4f} {ty:.4f}) scale({k:.6f})">'
            f'<path fill-rule="evenodd" d="{"".join(p for _, p in paths)}"/></g>')


def frente_svg():
    return colocar(TRAZADO, LOGO_X0, LOGO_X1, LOGO_Y0, LOGO_Y1, ANCHO_LOGO / (LOGO_X1 - LOGO_X0))


def reverso_svg():
    conejo = [t for t in TRAZADO if t[0] < 458]
    return colocar(conejo, CONEJO_X0, CONEJO_X1, CONEJO_Y0, CONEJO_Y1, ALTO_CONEJO / (CONEJO_Y1 - CONEJO_Y0))


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
