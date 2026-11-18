"""Test schematics for the FlexiForce conditioning board (breadboard, before the sensors arrive)."""
import textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Polygon, Rectangle, Circle, FancyBboxPatch

LW = 1.4
C = "#1f2328"
BLUE = "#0b3d6b"
RED = "#b3261e"
GREY = "#555"
VREF = 3.3 * 4.9 / 32
RF = 49.4e3


def new_page(title, subtitle):
    fig, ax = plt.subplots(figsize=(11.69, 8.27))
    ax.set_xlim(0, 29.7)
    ax.set_ylim(0, 21)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.text(0.6, 20.3, title, fontsize=15, color=BLUE, weight="bold", va="center")
    ax.text(0.6, 19.5, subtitle, fontsize=10, color=GREY, va="center")
    ax.text(29.1, 20.3, "PFE Combat Mirror — A. Duchene — 18/11/2026", fontsize=8, color=GREY, ha="right", va="center")
    return fig, ax


def primitives(ax):
    def wire(*pts, color=C, lw=LW, **kw):
        xs, ys = zip(*pts)
        ax.plot(xs, ys, color=color, lw=lw, solid_capstyle="round", **kw)

    def dot(x, y):
        ax.add_patch(Circle((x, y), 0.08, color=C, zorder=5))

    def text(x, y, s, size=9, ha="center", va="center", color=C, **kw):
        ax.text(x, y, s, fontsize=size, ha=ha, va=va, color=color, **kw)

    def resistor(x1, y1, x2, y2, label=None, side=1, var=False, color=C, size=8.5):
        L = np.hypot(x2 - x1, y2 - y1)
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        px, py = -uy, ux
        body = 0.9
        lead = (L - body) / 2
        a = (x1 + ux * lead, y1 + uy * lead)
        b = (x2 - ux * lead, y2 - uy * lead)
        wire((x1, y1), a, color=color)
        wire(b, (x2, y2), color=color)
        pts = [a]
        for i in range(1, 7):
            t = (i - 0.5) / 6
            s = 0.16 * (1 if i % 2 else -1)
            pts.append((a[0] + ux * body * t + px * s, a[1] + uy * body * t + py * s))
        pts.append(b)
        wire(*pts, color=color)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        if var:
            ax.annotate("", xy=(mx + ux * 0.5 - px * 0.4, my + uy * 0.5 - py * 0.4),
                        xytext=(mx - ux * 0.5 + px * 0.4, my - uy * 0.5 + py * 0.4),
                        arrowprops=dict(arrowstyle="-|>", color=color, lw=1.0))
        if label:
            off = (0.45 if abs(uy) < 0.5 else 0.6) * side
            dx, dy = px * off, py * off
            if abs(uy) < 0.5:
                text(mx, my + (0.45 if dy >= 0 else -0.45), label, size=size, color=color)
            else:
                text(mx + dx, my, label, size=size, color=color, ha="left" if dx > 0 else "right")

    def cap_v(x, y_top, y_bot, label=None, left=False):
        mid = (y_top + y_bot) / 2
        wire((x, y_top), (x, mid + 0.1))
        wire((x, mid - 0.1), (x, y_bot))
        wire((x - 0.3, mid + 0.1), (x + 0.3, mid + 0.1))
        wire((x - 0.3, mid - 0.1), (x + 0.3, mid - 0.1))
        if label:
            text(x - 0.45 if left else x + 0.45, mid, label, size=8.5, ha="right" if left else "left")

    def cap_h(x1, x2, y, label=None):
        mid = (x1 + x2) / 2
        wire((x1, y), (mid - 0.1, y))
        wire((mid + 0.1, y), (x2, y))
        wire((mid - 0.1, y - 0.3), (mid - 0.1, y + 0.3))
        wire((mid + 0.1, y - 0.3), (mid + 0.1, y + 0.3))
        if label:
            text(mid, y - 0.6, label, size=8.5)

    def gnd(x, y):
        wire((x, y), (x, y - 0.22))
        for i, w in enumerate((0.32, 0.21, 0.1)):
            wire((x - w, y - 0.22 - i * 0.1), (x + w, y - 0.22 - i * 0.1))

    def vcc(x, y, label="+3V3"):
        wire((x, y), (x, y + 0.25))
        wire((x - 0.25, y + 0.25), (x + 0.25, y + 0.25))
        text(x, y + 0.55, label, size=8.5)

    def opamp(x, y, name, pins=("3", "2", "1")):
        w, h = 1.9, 2.1
        ax.add_patch(Polygon([(x - w / 2, y + h / 2), (x - w / 2, y - h / 2), (x + w / 2, y)],
                             closed=True, fill=False, ec=C, lw=LW))
        text(x - w / 2 + 0.25, y + 0.45, "+", size=11)
        text(x - w / 2 + 0.25, y - 0.45, "−", size=12)
        text(x - w / 2 - 0.25, y + 0.75, pins[0], size=7.5, color=RED)
        text(x - w / 2 - 0.25, y - 0.15, pins[1], size=7.5, color=RED)
        text(x + w / 2 + 0.2, y + 0.3, pins[2], size=7.5, color=RED)
        text(x + 0.9, y + 1.0, name, size=8.5, ha="left")
        return (x - w / 2, y + 0.45), (x - w / 2, y - 0.45), (x + w / 2, y)

    def tp(x, y, name, color=RED, dx=0.0, dy=0.45):
        ax.add_patch(Circle((x, y), 0.14, fill=False, ec=color, lw=1.3, zorder=6))
        text(x + dx, y + dy, name, size=8, color=color, weight="bold")

    def frame(x, y, w, h, title=None, color=BLUE):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.2",
                                    fill=False, ec=color, lw=1.0, ls=(0, (5, 3))))
        if title:
            text(x + 0.2, y + h - 0.35, title, size=9.5, ha="left", color=color, weight="bold")

    def table(x, y, rows, widths, size=8.5, header_color=BLUE, row_h=0.62):
        for r, row in enumerate(rows):
            cx = x
            for c, (cell, w) in enumerate(zip(row, widths)):
                text(cx + 0.15, y - r * row_h, cell, size=size, ha="left",
                     color=header_color if r == 0 else C, weight="bold" if r == 0 else "normal")
                cx += w
            if r == 0:
                wire((x, y - 0.33), (x + sum(widths), y - 0.33), lw=0.8, color=header_color)

    return dict(wire=wire, dot=dot, text=text, resistor=resistor, cap_v=cap_v, cap_h=cap_h,
                gnd=gnd, vcc=vcc, opamp=opamp, tp=tp, frame=frame, table=table)


def channel(p, x0=0.0, sensor="rtest"):
    """Divider + one channel + Nucleo pins. Returns the coordinates of the sensor node."""
    wire, dot, text, resistor = p["wire"], p["dot"], p["text"], p["resistor"]
    # V_REF divider
    xd = 2.6 + x0
    p["vcc"](xd, 15.6)
    resistor(xd, 15.6, xd, 13.8, "R1 22 kΩ", side=-1)
    dot(xd, 13.8)
    resistor(xd, 13.8, xd, 12.0, "R2 5,1 kΩ", side=-1)
    dot(xd, 12.0)
    resistor(xd, 12.0, xd, 10.2, "R3 3,9 kΩ", side=-1)
    dot(xd, 10.2)
    resistor(xd, 10.2, xd, 8.4, "R4 1 kΩ", side=-1)
    p["gnd"](xd, 8.4)
    tx = xd + 1.6
    for y, lab in ((13.8, "1,03 V"), (12.0, "0,51 V"), (10.2, "0,10 V")):
        wire((xd, y), (tx - 0.12, y))
        ax_circle(p, tx, y)
        text(tx + 0.1, y + 0.35, lab, size=7.5, color=GREY, ha="left")
    # selector wire (standard mode)
    xv = tx + 1.5
    wire((tx + 0.12, 12.0), (xv, 12.0), color=RED, lw=1.8)
    text(tx + 0.75, 11.6, "fil = mode", size=7, color=RED)
    dot(xv, 12.0)
    p["cap_v"](xv, 12.0, 10.4, "C1 100 nF")
    p["gnd"](xv, 10.4)
    # V_REF line to the op-amp and to A4
    ip, im, out = p["opamp"](xv + 5.6, 12.0 - 0.45, "U1A MCP6004")
    wire((xv, 12.0), (xv + 1.2, 12.0))
    wire((xv + 1.2, 12.0), ip)
    dot(xv + 1.2, 12.0)
    text(xv + 1.2, 12.35, "V_REF", size=8.5, weight="bold", ha="left")
    # op-amp supply
    ox_c = xv + 5.6
    wire((ox_c, 12.0 - 0.45 + 0.55), (ox_c, 13.6))
    p["vcc"](ox_c, 13.6)
    text(ox_c + 0.25, 13.1, "4", size=7.5, color=RED)
    wire((ox_c, 12.0 - 0.45 - 0.55), (ox_c, 10.6))
    p["gnd"](ox_c, 10.6)
    text(ox_c + 0.3, 10.85, "11", size=7.5, color=RED)
    # inverting node and sensor
    nx = xv + 3.4
    wire(im, (nx, im[1]))
    dot(nx, im[1])
    xs = xv + 2.6
    wire((nx, im[1]), (xs, im[1]))
    node = (xs, im[1])
    # feedback
    yr, yc = 8.6, 7.3
    ox = out[0] + 1.2
    wire((nx, im[1]), (nx, yc))
    dot(nx, yr)
    resistor(nx, yr, nx + 2.0, yr, "RF 1 kΩ", side=1)
    resistor(nx + 2.0, yr, ox, yr, "RV 100 kΩ", side=1, var=True)
    p["cap_h"](nx, ox, yc, "CF 47 pF")
    wire(out, (ox, out[1]))
    dot(ox, out[1])
    wire((ox, out[1]), (ox, yc))
    dot(ox, yr)
    p["tp"](ox, out[1] + 0.0, "TP1", dx=0.0, dy=0.5)
    # output filter
    xf = ox + 2.4
    resistor(ox, out[1], xf, out[1], "RO 1 kΩ", side=1)
    dot(xf, out[1])
    p["cap_v"](xf, out[1], out[1] - 2.2, "CO 330 nF", left=True)
    p["gnd"](xf, out[1] - 2.2)
    xa = xf + 1.7
    wire((xf, out[1]), (xa, out[1]))
    p["tp"](xf + 0.8, out[1], "TP2", dy=0.5)
    # Nucleo
    xn = xa
    p["frame"](xn, 9.0, 2.5, 6.6, "NUCLEO", color=C)
    text(xn + 0.25, out[1], "A0", size=9, ha="left", weight="bold")
    text(xn + 1.0, out[1], "(PA0)", size=7.5, ha="left", color=GREY)
    ya4 = 14.4
    wire((xv + 1.2, 12.0), (xv + 1.2, ya4), (xn, ya4))
    text(xn + 0.25, ya4, "A4", size=9, ha="left", weight="bold")
    text(xn + 1.0, ya4, "(PC1)", size=7.5, ha="left", color=GREY)
    text(xn + 0.25, 10.6, "3V3", size=9, ha="left", weight="bold")
    text(xn + 0.25, 9.8, "GND", size=9, ha="left", weight="bold")
    text(xn + 1.25, 12.9, "USB → PC\n(COM4)", size=7.5, color=GREY)
    text(xn + 1.25, 8.2, "3V3 et GND vers les\nrails + / − de la breadboard", size=7, color=GREY)
    return node, (nx, ox, yr)


def x_lab(tx):
    return tx + 0.1


def ax_circle(p, x, y):
    p["wire"]  # keep signature uniform
    plt.gca().add_patch(Circle((x, y), 0.12, fill=False, ec=C, lw=1.2))


def page_linearity(pdf):
    global ax
    fig, ax = new_page("Test 1 et 2 — V_REF, gain et linéarité d'une voie",
                       "Le FlexiForce est remplacé par une résistance fixe R_TEST : une résistance plus faible équivaut à une force plus grande.")
    p = primitives(ax)
    node, _ = channel(p)
    x, y = node
    p["resistor"](x, y, x, y - 2.6, "R_TEST", side=1, color=RED, size=9)
    p["gnd"](x, y - 2.6)
    p["text"](x - 0.3, y - 3.3, "à la place\ndu capteur", size=7.5, color=RED, ha="right")
    # notes
    p["text"](0.6, 5.6, "Mesures", size=10.5, ha="left", color=BLUE, weight="bold")
    notes = [
        "1. Hors tension, R_TEST débranchée : régler RV pour lire R_F ≈ 49,4 kΩ au multimètre entre les broches 1 et 2.",
        "2. Sous tension : python forceplate.py -p COM4 monitor --rf 49.4   (remplacer 49.4 par la valeur mesurée, en kΩ).",
        "3. Déplacer le fil de mode sur les 3 prises : le script affiche V_REF et le mode (sensitive / standard / high force).",
        "4. En mode standard, passer les R_TEST du tableau : relever V1 et la résistance R calculée par le script.",
        "TP1 : sortie de l'ampli (broche 1), avant le filtre.  TP2 : entrée de l'ADC.  Les numéros en rouge sont les broches du MCP6004.",
    ]
    for i, n in enumerate(notes):
        p["text"](0.6, 4.9 - i * 0.62, n, size=8.3, ha="left")
    # tables
    rows = [("Position du fil", "V_REF attendue", "Mode affiché")] + [
        ("prise 1 (R1-R2)", "1,03 V", "sensitive"), ("prise 2 (R2-R3)", "0,505 V", "standard"),
        ("prise 3 (R3-R4)", "0,103 V", "high force")]
    p["frame"](20.6, 15.0, 8.8, 3.6, "Test 1 : V_REF (A4)")
    p["table"](20.7, 17.6, rows, (3.1, 2.9, 2.8), size=8)
    rows = [("R_TEST", "Équivaut à", "V1 attendue")]
    for r, eq in ((None, "à vide (en l'air)"), (1e6, "à vide (fiche Rev I)"), (100e3, "appui léger"),
                  (47e3, ""), (22e3, ""), (15e3, ""), (10e3, "pleine échelle"), (6.8e3, "saturation")):
        v = VREF if r is None else min(VREF * (1 + RF / r), 3.275)
        name = "aucune" if r is None else (f"{r / 1e6:g} MΩ" if r >= 1e6 else f"{r / 1e3:g} kΩ")
        vs = f"≈ {v:.2f} V" if r == 6.8e3 else f"{v:.3f} V"
        rows.append((name, eq, vs.replace(".", ",")))
    p["frame"](20.6, 6.2, 8.8, 8.3, "Test 2 : gain (mode standard)")
    p["table"](20.7, 13.6, rows, (2.3, 3.7, 2.8), size=8)
    p["text"](20.8, 7.5, "V1 = V_REF × (1 + R_F / R_TEST)\nR affichée par le script ≈ R_TEST à 1-2 % près", size=8, ha="left", color=BLUE)
    pdf.savefig(fig)
    plt.close(fig)


def page_step(pdf):
    global ax
    fig, ax = new_page("Test 4 — Réponse à un échelon",
                       "Un bouton-poussoir met une deuxième résistance en parallèle : la « force » passe brusquement d'un appui léger à un appui fort.")
    p = primitives(ax)
    node, _ = channel(p)
    x, y = node
    yj = 9.9
    p["wire"]((x, y), (x, yj), color=RED)
    p["resistor"](x, yj, x, 7.4, None, color=RED)
    p["text"](x - 0.3, 7.75, "100 kΩ", size=8.5, color=RED, ha="right")
    p["gnd"](x, 7.4)
    xb = x - 1.9
    p["wire"]((x, yj), (xb, yj), color=RED)
    p["dot"](x, yj)
    # push button
    yb = yj - 0.5
    p["wire"]((xb, yj), (xb, yb), color=RED)
    p["wire"]((xb, yb - 0.6), (xb, yb - 0.75), color=RED)
    p["wire"]((xb - 0.35, yb - 0.1), (xb + 0.35, yb - 0.1), color=RED)
    p["wire"]((xb, yb - 0.1), (xb, yb + 0.05), color=RED)
    ax.add_patch(Circle((xb, yb), 0.05, color=RED))
    ax.add_patch(Circle((xb, yb - 0.6), 0.05, color=RED))
    p["text"](xb - 0.45, yb - 0.3, "BP", size=8, color=RED, ha="right")
    p["resistor"](xb, yb - 0.75, xb, 6.6, "22 kΩ", side=-1, color=RED)
    p["gnd"](xb, 6.6)
    # expected response
    r1 = 100e3
    r2 = 1 / (1 / 100e3 + 1 / 22e3)
    v1, v2 = VREF * (1 + RF / r1), VREF * (1 + RF / r2)
    tau = 1e3 * 330e-9
    axr = fig.add_axes([0.58, 0.08, 0.38, 0.25])
    t = np.linspace(-2e-3, 6e-3, 800)
    v = np.where(t < 0, v1, v2 - (v2 - v1) * np.exp(-np.clip(t, 0, None) / tau))
    ts = np.arange(-2e-3, 6e-3, 0.5e-3)
    vs = np.where(ts < 0, v1, v2 - (v2 - v1) * np.exp(-np.clip(ts, 0, None) / tau))
    axr.plot(t * 1e3, v, color=BLUE, lw=1.6, label="entrée ADC (théorie)")
    axr.plot(ts * 1e3, vs, "o", color=RED, ms=4, label="échantillons à 2 kHz")
    axr.set_xlabel("temps après l'appui (ms)", fontsize=8)
    axr.set_ylabel("V1 (V)", fontsize=8)
    axr.tick_params(labelsize=7)
    axr.grid(alpha=0.3)
    axr.legend(fontsize=7, loc="lower right")
    p["text"](0.6, 5.6, "Mesures", size=10.5, ha="left", color=BLUE, weight="bold")
    notes = [
        f"Bouton relâché : 100 kΩ seul → V1 ≈ {v1:.2f} V.   Bouton appuyé : 100 kΩ // 22 kΩ = {r2 / 1e3:.1f} kΩ → V1 ≈ {v2:.2f} V.".replace(".", ","),
        "python forceplate.py -p COM4 record -d 5 -o echelon.csv   puis appuyer plusieurs fois sur le bouton.",
        "Attendu : montée de 10 à 90 % en ≈ 0,7 ms (filtre RO-CO, τ = 0,33 ms), soit 1 à 2 échantillons.",
        "Un bouton rebondit pendant quelques dizaines de µs : petites marches possibles sur le premier échantillon.",
        "Oscilloscope (option) : TP1 avec puis sans CF, pour voir si l'ampli sonne après le front.",
    ]
    lines = [l for n in notes for l in textwrap.wrap(n, 86, subsequent_indent="   ")]
    for i, n in enumerate(lines):
        p["text"](0.6, 4.95 - i * 0.48, n, size=8.0, ha="left")
    pdf.savefig(fig)
    plt.close(fig)


def page_pinout(pdf):
    global ax
    fig, ax = new_page("Test 5 — Brochage du MCP6004 et câblage des 4 voies",
                       "Boîtier DIP-14 vu de dessus, encoche en haut. Les 4 voies sont identiques à la voie A ; seules les broches changent.")
    p = primitives(ax)
    # DIP-14
    x0, y0, w, pitch = 4.0, 16.8, 3.0, 1.2
    ax.add_patch(Rectangle((x0, y0 - 7 * pitch), w, 7 * pitch + 0.3, fill=False, ec=C, lw=1.6))
    ax.add_patch(matplotlib.patches.Arc((x0 + w / 2, y0 + 0.3), 0.9, 0.9, theta1=180, theta2=360, lw=1.4, color=C))
    p["text"](x0 + w / 2, y0 - 3.6, "MCP6004", size=10, weight="bold")
    left = ["1 OUT A", "2 IN A−", "3 IN A+", "4 VDD (+3V3)", "5 IN B+", "6 IN B−", "7 OUT B"]
    right = ["14 OUT D", "13 IN D−", "12 IN D+", "11 VSS (GND)", "10 IN C+", "9 IN C−", "8 OUT C"]
    for i, (l, r) in enumerate(zip(left, right)):
        y = y0 - 0.3 - i * pitch
        p["wire"]((x0 - 0.6, y), (x0, y))
        p["wire"]((x0 + w, y), (x0 + w + 0.6, y))
        p["text"](x0 - 0.75, y, l, size=8.5, ha="right", color=RED if "VDD" in l else C)
        p["text"](x0 + w + 0.75, y, r, size=8.5, ha="left", color=RED if "VSS" in r else C)
    ax.add_patch(Circle((x0 + 0.35, y0 - 0.1), 0.12, color=C))
    rows = [("Voie", "Ampli", "Entrée +", "Entrée −", "Sortie", "Vers")] + [
        ("1", "A", "3", "2", "1", "A0 (PA0)"), ("2", "B", "5", "6", "7", "A1 (PA1)"),
        ("3", "C", "10", "9", "8", "A2 (PA4)"), ("4", "D", "12", "13", "14", "A3 (PB0)")]
    p["frame"](14.0, 12.5, 14.8, 5.1, "Correspondance des broches")
    p["table"](14.1, 16.6, rows, (1.6, 1.8, 2.3, 2.3, 2.2, 3.0), size=9)
    p["text"](14.2, 13.2, "Pour chaque voie : V_REF sur l'entrée + ; R_TEST (puis le capteur), RF + RV et CF\nsur l'entrée − ; RO + CO sur la sortie.",
              size=8, ha="left")
    # unused amplifier tie-off
    p["frame"](0.8, 1.2, 12.6, 6.2, "Ampli non utilisé (tant qu'une seule voie est câblée)")
    ip, im, out = p["opamp"](5.5, 4.2, "U1B, C ou D", pins=("", "", ""))
    p["wire"](ip, (ip[0] - 1.0, ip[1]), (ip[0] - 1.0, 2.6))
    p["gnd"](ip[0] - 1.0, 2.6)
    p["wire"](im, (im[0] - 0.4, im[1]), (im[0] - 0.4, 2.3), (out[0] + 0.6, 2.3), (out[0] + 0.6, out[1]), out)
    p["text"](8.7, 3.6, "Suiveur, entrée + à la masse :\nsortie fixe à 0 V, sans\noscillation ni consommation\ninutile.", size=8, ha="left")
    # 4-channel test
    p["frame"](14.0, 1.2, 14.8, 10.8, "Test 5 : comparer les 4 voies")
    steps = [
        "1. Câbler les voies B, C, D comme la voie A (mêmes valeurs),",
        "    sorties filtrées vers A1, A2, A3.",
        "2. Mettre R_TEST = 10 kΩ sur les 4 voies, mode standard.",
        "3. Régler chaque RV pour lire 3,00 V sur sa voie dans monitor.",
        "4. Hors tension, mesurer les 4 R_F au multimètre :",
        "    elles doivent toutes valoir ≈ 49,4 kΩ.",
        "5. Remettre sous tension et passer 22 kΩ sur chaque voie :",
        "    les 4 voies doivent lire ≈ 1,64 V à quelques mV près.",
        "6. python forceplate.py -p COM4 tare : noter le bruit de",
        "    chaque voie (quelques mV RMS attendus).",
        "",
        "Avec de vrais capteurs, les R_F seront différentes d'une voie",
        "à l'autre : c'est le rôle des potentiomètres de compenser",
        "la dispersion des capteurs.",
    ]
    for i, s in enumerate(steps):
        p["text"](14.3, 10.9 - i * 0.62, s, size=8.5, ha="left")
    pdf.savefig(fig)
    plt.close(fig)


with PdfPages("schemas_tests_conditionnement.pdf") as pdf:
    page_linearity(pdf)
    page_step(pdf)
    page_pinout(pdf)
    d = pdf.infodict()
    d["Title"] = "Schémas de test du conditionnement FlexiForce"
    d["Author"] = "Aymeric Duchene"
