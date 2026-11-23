import uuid, math, json

def U(): return str(uuid.uuid4())
ROOT = U()
PROJECT = "conditioning"
F = "(effects (font (size 1.27 1.27)))"
FH = "(effects (font (size 1.27 1.27)) hide)"

# ---------------------------------------------------------------- library
def pin(kind, x, y, a, length, num, name="~", hide=False):
    h = " hide" if hide else ""
    return (f'(pin {kind} line (at {x} {y} {a}) (length {length}){h} '
            f'(name "{name}" {F}) (number "{num}" {F}))')

def props(ref, val, desc, ref_at=(2.032, 0, 90), val_at=(0, 0, 90), power=False):
    rh = FH if power else F
    return (f'(property "Reference" "{ref}" (at {ref_at[0]} {ref_at[1]} {ref_at[2]}) {rh})'
            f'(property "Value" "{val}" (at {val_at[0]} {val_at[1]} {val_at[2]}) {F})'
            f'(property "Footprint" "" (at 0 0 0) {FH})'
            f'(property "Datasheet" "~" (at 0 0 0) {FH})'
            f'(property "Description" "{desc}" (at 0 0 0) {FH})')

STROKE = "(stroke (width 0.254) (type default)) (fill (type none))"
STROKE0 = "(stroke (width 0) (type default)) (fill (type none))"

LIB = {}
PINS = {}   # lib_id -> unit -> list of (num, x, y, angle)

def add(lib_id, text, pins):
    LIB[lib_id] = text
    PINS[lib_id] = pins

# Resistor
add("Device:R",
    '(symbol "Device:R" (pin_numbers hide) (pin_names (offset 0)) (exclude_from_sim no) (in_bom yes) (on_board yes) '
    + props("R", "R", "Resistor") +
    f'(symbol "R_0_1" (rectangle (start -1.016 -2.54) (end 1.016 2.54) {STROKE}))'
    f'(symbol "R_1_1" {pin("passive", 0, 3.81, 270, 1.27, "1")} {pin("passive", 0, -3.81, 90, 1.27, "2")}))',
    {1: [("1", 0, 3.81, 270), ("2", 0, -3.81, 90)]})

# Capacitor
add("Device:C",
    '(symbol "Device:C" (pin_numbers hide) (pin_names (offset 0.254)) (exclude_from_sim no) (in_bom yes) (on_board yes) '
    + props("C", "C", "Capacitor", ref_at=(0.635, 2.54, 0), val_at=(0.635, -2.54, 0)) +
    f'(symbol "C_0_1" (polyline (pts (xy -2.032 -0.762) (xy 2.032 -0.762)) (stroke (width 0.508) (type default)) (fill (type none)))'
    f' (polyline (pts (xy -2.032 0.762) (xy 2.032 0.762)) (stroke (width 0.508) (type default)) (fill (type none))))'
    f'(symbol "C_1_1" {pin("passive", 0, 3.81, 270, 3.048, "1")} {pin("passive", 0, -3.81, 90, 3.048, "2")}))',
    {1: [("1", 0, 3.81, 270), ("2", 0, -3.81, 90)]})

# Trimmer potentiometer (pin 2 = wiper)
add("Device:R_Potentiometer_Trim",
    '(symbol "Device:R_Potentiometer_Trim" (pin_names (offset 1.016) hide) (exclude_from_sim no) (in_bom yes) (on_board yes) '
    + props("RV", "R_Potentiometer_Trim", "Trim potentiometer", ref_at=(-4.445, 0, 90), val_at=(-2.54, 0, 90)) +
    f'(symbol "R_Potentiometer_Trim_0_1" (rectangle (start 1.016 2.54) (end -1.016 -2.54) {STROKE})'
    f' (polyline (pts (xy 1.524 0.762) (xy 1.524 -0.762)) {STROKE})'
    f' (polyline (pts (xy 1.524 0) (xy 1.016 0)) {STROKE}))'
    f'(symbol "R_Potentiometer_Trim_1_1" {pin("passive", 0, 3.81, 270, 1.27, "1", "1")} '
    f'{pin("passive", 2.54, 0, 180, 1.016, "2", "2")} {pin("passive", 0, -3.81, 90, 1.27, "3", "3")}))',
    {1: [("1", 0, 3.81, 270), ("2", 2.54, 0, 180), ("3", 0, -3.81, 90)]})

# Quad op-amp MCP6004 (units A-D + power unit E)
oa_units = {1: ("1", "2", "3"), 2: ("7", "6", "5"), 3: ("8", "9", "10"), 4: ("14", "13", "12")}  # out, -, +
units_txt = ""
mcp_pins = {}
for u, (o, m, p) in oa_units.items():
    units_txt += (f'(symbol "MCP6004_{u}_1" (polyline (pts (xy -5.08 5.08) (xy 5.08 0) (xy -5.08 -5.08) (xy -5.08 5.08)) '
                  f'(stroke (width 0.254) (type default)) (fill (type background))) '
                  f'{pin("input", -7.62, 2.54, 0, 2.54, p, "+")} {pin("input", -7.62, -2.54, 0, 2.54, m, "-")} '
                  f'{pin("output", 7.62, 0, 180, 2.54, o, "~")})')
    mcp_pins[u] = [(p, -7.62, 2.54, 0), (m, -7.62, -2.54, 0), (o, 7.62, 0, 180)]
units_txt += (f'(symbol "MCP6004_5_1" {pin("power_in", -2.54, 7.62, 270, 3.81, "4", "V+")} '
              f'{pin("power_in", -2.54, -7.62, 90, 3.81, "11", "V-")})')
mcp_pins[5] = [("4", -2.54, 7.62, 270), ("11", -2.54, -7.62, 90)]
add("Amplifier_Operational:MCP6004",
    '(symbol "Amplifier_Operational:MCP6004" (pin_names (offset 0.127)) (exclude_from_sim no) (in_bom yes) (on_board yes) '
    + props("U", "MCP6004", "Quad 1 MHz rail-to-rail op-amp", ref_at=(0, 5.08, 0), val_at=(0, -5.08, 0)) + units_txt + ')',
    mcp_pins)

# Generic connectors
def conn_1xN(n):
    lid = f"Connector_Generic:Conn_01x{n:02d}"
    top = (n - 1) * 1.27
    ps, pl = "", []
    for i in range(n):
        y = round(top - i * 2.54, 3)
        ps += pin("passive", -5.08, y, 0, 3.81, str(i + 1), f"Pin_{i + 1}")
        pl.append((str(i + 1), -5.08, y, 0))
    add(lid,
        f'(symbol "{lid}" (pin_names (offset 1.016) hide) (exclude_from_sim no) (in_bom yes) (on_board yes) '
        + props("J", f"Conn_01x{n:02d}", "Generic connector", ref_at=(0, top + 2.54, 0), val_at=(0, -top - 2.54, 0)) +
        f'(symbol "Conn_01x{n:02d}_1_1" (rectangle (start -1.27 {top + 1.27}) (end 1.27 {-top - 1.27}) '
        f'(stroke (width 0.254) (type default)) (fill (type background))) {ps}))',
        {1: pl})
conn_1xN(3)
conn_1xN(6)
conn_1xN(8)

lid = "Connector_Generic:Conn_02x03_Odd_Even"
ps, pl = "", []
for i in range(3):
    y = 2.54 - i * 2.54
    ps += pin("passive", -5.08, y, 0, 3.81, str(2 * i + 1), f"Pin_{2 * i + 1}")
    ps += pin("passive", 7.62, y, 180, 3.81, str(2 * i + 2), f"Pin_{2 * i + 2}")
    pl += [(str(2 * i + 1), -5.08, y, 0), (str(2 * i + 2), 7.62, y, 180)]
add(lid,
    f'(symbol "{lid}" (pin_names (offset 1.016) hide) (exclude_from_sim no) (in_bom yes) (on_board yes) '
    + props("J", "Conn_02x03_Odd_Even", "Generic 2x03 connector", ref_at=(1.27, 5.08, 0), val_at=(1.27, -5.08, 0)) +
    f'(symbol "Conn_02x03_Odd_Even_1_1" (rectangle (start -1.27 3.81) (end 3.81 -3.81) '
    f'(stroke (width 0.254) (type default)) (fill (type background))) {ps}))',
    {1: pl})


add("pfe_combat_mirror:FlexiForce",
    '(symbol "pfe_combat_mirror:FlexiForce" (pin_numbers hide) (pin_names (offset 0) hide) (exclude_from_sim no) (in_bom yes) (on_board yes) '
    + props("FS", "FlexiForce", "Tekscan FlexiForce force sensor (outer pins 1 and 3 active)") +
    f'(symbol "FlexiForce_0_1" (rectangle (start -1.016 -2.54) (end 1.016 2.54) {STROKE})'
    f' (polyline (pts (xy -2.032 -2.032) (xy 2.032 2.032)) {STROKE})'
    f' (polyline (pts (xy 2.032 2.032) (xy 1.27 2.032)) {STROKE})'
    f' (polyline (pts (xy 2.032 2.032) (xy 2.032 1.27)) {STROKE}))'
    f'(symbol "FlexiForce_1_1" {pin("passive", 0, 3.81, 270, 1.27, "1")} {pin("passive", 0, -3.81, 90, 1.27, "3")}))',
    {1: [("1", 0, 3.81, 270), ("3", 0, -3.81, 90)]})

# Two-pin link (pin header + jumper), drawn like a resistor
add("pfe_combat_mirror:Link",
    '(symbol "pfe_combat_mirror:Link" (pin_numbers hide) (pin_names (offset 0) hide) (exclude_from_sim no) (in_bom yes) (on_board yes) '
    + props("JP", "Link", "Two-pin header with jumper, closed in normal use") +
    f'(symbol "Link_0_1" (circle (center -1.016 0) (radius 0.508) {STROKE}) (circle (center 1.016 0) (radius 0.508) {STROKE})'
    f' (arc (start -1.524 0.762) (mid 0 1.524) (end 1.524 0.762) {STROKE}))'
    f'(symbol "Link_1_1" {pin("passive", -3.81, 0, 0, 2.286, "1")} {pin("passive", 3.81, 0, 180, 2.286, "2")}))',
    {1: [("1", -3.81, 0, 0), ("2", 3.81, 0, 180)]})

# Test point (one pin, pointing down)
add("pfe_combat_mirror:TestPoint",
    '(symbol "pfe_combat_mirror:TestPoint" (pin_numbers hide) (pin_names (offset 0) hide) (exclude_from_sim no) (in_bom yes) (on_board yes) '
    + props("TP", "TestPoint", "Test point (single header pin)", ref_at=(0, 3.81, 0), val_at=(0, 5.08, 0)) +
    f'(symbol "TestPoint_0_1" (circle (center 0 1.778) (radius 0.762) {STROKE}))'
    f'(symbol "TestPoint_1_1" {pin("passive", 0, 0, 90, 1.016, "1")}))',
    {1: [("1", 0, 0, 90)]})

# Power symbols
add("power:GND",
    '(symbol "power:GND" (power) (pin_numbers hide) (pin_names (offset 0) hide) (exclude_from_sim no) (in_bom yes) (on_board yes) '
    + props("#PWR", "GND", "Power symbol GND", ref_at=(0, -6.35, 0), val_at=(0, -3.81, 0), power=True) +
    f'(symbol "GND_0_1" (polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27)) {STROKE0}))'
    f'(symbol "GND_1_1" {pin("power_in", 0, 0, 270, 0, "1", "GND", hide=True)}))',
    {1: [("1", 0, 0, 270)]})
add("power:+3V3",
    '(symbol "power:+3V3" (power) (pin_numbers hide) (pin_names (offset 0) hide) (exclude_from_sim no) (in_bom yes) (on_board yes) '
    + props("#PWR", "+3V3", "Power symbol +3V3", ref_at=(0, -3.81, 0), val_at=(0, 3.556, 0), power=True) +
    f'(symbol "+3V3_0_1" (polyline (pts (xy -0.762 1.27) (xy 0 2.54)) {STROKE0}) (polyline (pts (xy 0 0) (xy 0 2.54)) {STROKE0})'
    f' (polyline (pts (xy 0 2.54) (xy 0.762 1.27)) {STROKE0}))'
    f'(symbol "+3V3_1_1" {pin("power_in", 0, 0, 90, 0, "1", "+3V3", hide=True)}))',
    {1: [("1", 0, 0, 90)]})
add("power:PWR_FLAG",
    '(symbol "power:PWR_FLAG" (power) (pin_numbers hide) (pin_names (offset 0) hide) (exclude_from_sim no) (in_bom yes) (on_board yes) '
    + props("#FLG", "PWR_FLAG", "Power flag", ref_at=(0, 1.905, 0), val_at=(0, 3.81, 0), power=True) +
    f'(symbol "PWR_FLAG_0_0" {pin("power_out", 0, 0, 90, 0, "1", "pwr", hide=True)})'
    f'(symbol "PWR_FLAG_0_1" (polyline (pts (xy 0 0) (xy 0 1.27) (xy -1.016 1.905) (xy 0 2.54) (xy 1.016 1.905) (xy 0 1.27)) {STROKE0})))',
    {1: [("1", 0, 0, 90)]})

# ---------------------------------------------------------------- schematic
items = []
pwr_count = [0]

def r2(v): return round(v, 3)

def place(lib_id, ref, value, x, y, unit=1, footprint="", extra_props=None, ref_off=(3.81, -1.27), val_off=(3.81, 1.27), rot=0):
    pins = PINS[lib_id][unit]
    p = (f'(symbol (lib_id "{lib_id}") (at {x} {y} {rot}) (unit {unit}) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{U()}") '
         f'(property "Reference" "{ref}" (at {r2(x + ref_off[0])} {r2(y + ref_off[1])} 0) (effects (font (size 1.27 1.27)) (justify left))) '
         f'(property "Value" "{value}" (at {r2(x + val_off[0])} {r2(y + val_off[1])} 0) (effects (font (size 1.27 1.27)) (justify left))) '
         f'(property "Footprint" "{footprint}" (at {x} {y} 0) {FH}) '
         f'(property "Datasheet" "~" (at {x} {y} 0) {FH}) ')
    for k, v in (extra_props or {}).items():
        p += f'(property "{k}" "{v}" (at {x} {y} 0) {FH}) '
    for (num, *_ ) in pins:
        p += f'(pin "{num}" (uuid "{U()}")) '
    p += f'(instances (project "{PROJECT}" (path "/{ROOT}" (reference "{ref}") (unit {unit})))))'
    items.append(p)
    c, sn = round(math.cos(math.radians(rot))), round(math.sin(math.radians(rot)))
    res = {}
    for (num, px, py, a) in pins:
        qx, qy = px * c - py * sn, px * sn + py * c
        res[num] = (r2(x + qx), r2(y - qy), (a + rot) % 360)
    return res

def wire(x1, y1, x2, y2):
    items.append(f'(wire (pts (xy {r2(x1)} {r2(y1)}) (xy {r2(x2)} {r2(y2)})) (stroke (width 0) (type default)) (uuid "{U()}"))')

def outward(a):
    a = (a + 180) % 360
    return {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}[a]

def power(kind, x, y):
    pwr_count[0] += 1
    ref = f"#PWR{pwr_count[0]:02d}" if kind != "power:PWR_FLAG" else f"#FLG{pwr_count[0]:02d}"
    val = kind.split(":")[1]
    p = (f'(symbol (lib_id "{kind}") (at {r2(x)} {r2(y)} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{U()}") '
         f'(property "Reference" "{ref}" (at {r2(x)} {r2(y + 6.35)} 0) {FH}) '
         f'(property "Value" "{val}" (at {r2(x)} {r2(y + (3.81 if val == "GND" else -3.81))} 0) {F}) '
         f'(property "Footprint" "" (at {r2(x)} {r2(y)} 0) {FH}) '
         f'(property "Datasheet" "" (at {r2(x)} {r2(y)} 0) {FH}) '
         f'(pin "1" (uuid "{U()}")) '
         f'(instances (project "{PROJECT}" (path "/{ROOT}" (reference "{ref}") (unit 1)))))')
    items.append(p)

def net(pt, name, stub=2.54):
    x, y, a = pt
    dx, dy = outward(a)
    x2, y2 = x + dx * stub, y + dy * stub
    wire(x, y, x2, y2)
    if name in ("GND", "+3V3"):
        power(f"power:{name}", x2, y2)
        return
    ang, just = {(1, 0): (0, "left bottom"), (-1, 0): (180, "right bottom"),
                 (0, -1): (90, "left bottom"), (0, 1): (270, "right bottom")}[(dx, dy)]
    items.append(f'(label "{name}" (at {r2(x2)} {r2(y2)} {ang}) (fields_autoplaced yes) '
                 f'(effects (font (size 1.27 1.27)) (justify {just})) (uuid "{U()}"))')

def noconnect(pt):
    items.append(f'(no_connect (at {pt[0]} {pt[1]}) (uuid "{U()}"))')

def text(s, x, y, size=1.27):
    items.append(f'(text "{s}" (exclude_from_sim no) (at {x} {y} 0) (effects (font (size {size} {size})) (justify left bottom)) (uuid "{U()}"))')

FP_R = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical"
FP_C = "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P2.50mm"
FP_RV = "Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical"
FP_U = "Package_DIP:DIP-14_W7.62mm"
FP_J3 = "Connector_PinSocket_2.54mm:PinSocket_1x03_P2.54mm_Vertical"
FP_JP = "Connector_PinHeader_2.54mm:PinHeader_2x03_P2.54mm_Vertical"
FP_J6 = "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical"
FP_J8 = "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical"
FP_J3H = "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"
FP_LINK = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
FP_TP = "Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical"
tp_count = [0]
def testpoint(x, y, name, ref=None):
    """Test point whose pin sits at (x, y)."""
    tp_count[0] += 1
    place("pfe_combat_mirror:TestPoint", ref or f"TP{tp_count[0]}", name, x, y, footprint=FP_TP, ref_off=(1.27, -3.81), val_off=(1.27, -5.08))


def junction(x, y):
    items.append(f'(junction (at {r2(x)} {r2(y)}) (diameter 0) (color 0 0 0 0) (uuid "{U()}"))')

def path(*pts):
    for a, b in zip(pts, pts[1:]):
        wire(a[0], a[1], b[0], b[1])

def label(name, x, y, ang=0):
    just = {0: "left bottom", 180: "right bottom", 90: "left bottom", 270: "right bottom"}[ang]
    items.append(f'(label "{name}" (at {r2(x)} {r2(y)} {ang}) (fields_autoplaced yes) '
                 f'(effects (font (size 1.27 1.27)) (justify {just})) (uuid "{U()}"))')

# --- V_REF divider and JP1
text("V_REF divider and mode jumper", 30.48, 33.02, 2)
X = 40.64
r1 = place("Device:R", "R1", "22k 1%", X, 45.72, footprint=FP_R)
r2_ = place("Device:R", "R2", "5.1k 1%", X, 55.88, footprint=FP_R)
r3 = place("Device:R", "R3", "3.9k 1%", X, 66.04, footprint=FP_R)
r4 = place("Device:R", "R4", "1k 1%", X, 76.2, footprint=FP_R)
path((X, r1["1"][1]), (X, 39.37)); power("power:+3V3", X, 39.37)
path((X, r4["2"][1]), (X, 82.55)); power("power:GND", X, 82.55)
for top, bot, ty in ((r1, r2_, 50.8), (r2_, r3, 60.96), (r3, r4, 71.12)):
    path((X, top["2"][1]), (X, ty), (X, bot["1"][1])); junction(X, ty)
jp = place("Connector_Generic:Conn_02x03_Odd_Even", "JP1", "MODE", 60.96, 53.34, footprint=FP_JP, ref_off=(-1.27, -6.35), val_off=(-1.27, 7.62))
path((X, 50.8), jp["1"][:2])
path((X, 60.96), (48.26, 60.96), (48.26, 53.34), jp["3"][:2])
path((X, 71.12), (53.34, 71.12), (53.34, 55.88), jp["5"][:2])
path(jp["2"][:2], (71.12, 50.8), (71.12, 53.34), (71.12, 55.88), jp["6"][:2])
path(jp["4"][:2], (71.12, 53.34)); junction(71.12, 53.34)
c1 = place("Device:C", "C1", "100n", 81.28, 58.42, footprint=FP_C)
path((71.12, 53.34), (81.28, 53.34), (88.9, 53.34)); junction(81.28, 53.34)
path((81.28, 53.34), c1["1"][:2]); path(c1["2"][:2], (81.28, 64.77)); power("power:GND", 81.28, 64.77)
label("VREF", 88.9, 53.34, 0)
text("Mode: jumper on 1-2 = 1.03 V sensitive, 3-4 = 0.51 V standard, 5-6 = 0.10 V high force", 30.48, 96.52)

# --- U1 power unit + decoupling
u5 = place("Amplifier_Operational:MCP6004", "U1", "MCP6004", 104.14, 66.04, unit=5, footprint=FP_U, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
path(u5["4"][:2], (u5["4"][0], 55.88)); power("power:+3V3", u5["4"][0], 55.88)
path(u5["11"][:2], (u5["11"][0], 76.2)); power("power:GND", u5["11"][0], 76.2)
c2 = place("Device:C", "C2", "100n", 114.3, 66.04, footprint=FP_C)
path(c2["1"][:2], (114.3, 59.69)); power("power:+3V3", 114.3, 59.69)
path(c2["2"][:2], (114.3, 72.39)); power("power:GND", 114.3, 72.39)
text("C2 close to U1 pin 4", 109.22, 81.28)
power("power:PWR_FLAG", 124.46, 55.88); path((124.46, 55.88), (124.46, 58.42)); power("power:+3V3", 124.46, 58.42)
power("power:PWR_FLAG", 132.08, 55.88); path((132.08, 55.88), (132.08, 58.42)); power("power:GND", 132.08, 58.42)

# --- 4 measurement channels
# channel -> op-amp unit, chosen for the PCB layout (A0..A3 reached without crossings)
UNIT = {1: 3, 2: 4, 3: 1, 4: 2}
for k, (bx, by) in enumerate([(165.1, 50.8), (243.84, 50.8), (165.1, 116.84), (243.84, 116.84)], start=1):
    text(f"Channel {k}", bx - 20.32, by - 10.16, 1.5)
    uk = UNIT[k]
    u = place("Amplifier_Operational:MCP6004", "U1", "MCP6004", bx, by, unit=uk, footprint=FP_U, ref_off=(1.27, -6.35), val_off=(1.27, 6.35))
    pl = PINS["Amplifier_Operational:MCP6004"][uk]
    P, M, O = u[pl[0][0]][:2], u[pl[1][0]][:2], u[pl[2][0]][:2]
    # non-inverting input to V_REF
    path(P, (bx - 10.16, P[1])); label("VREF", bx - 10.16, P[1], 180)
    # inverting node
    xn = bx - 12.7
    yf = by + 12.7     # RF + RV row
    yc = by + 22.86    # CF row
    fs = place("pfe_combat_mirror:FlexiForce", f"FS{k}", "FlexiForce A201-100", xn, by + 30.48, footprint=FP_J3, ref_off=(-7.62, -1.27), val_off=(-7.62, 1.27))
    rf = place("Device:R", f"RF{k}", "1k 1%", bx - 5.08, yf, footprint=FP_R, rot=90, ref_off=(-1.27, -2.54), val_off=(-1.27, 2.54))
    rv = place("Device:R_Potentiometer_Trim", f"RV{k}", "100k", bx + 5.08, yf, footprint=FP_RV, rot=90, ref_off=(-1.27, 3.81), val_off=(-1.27, 6.35))
    cf = place("Device:C", f"CF{k}", "47p", bx, yc, footprint=FP_C, rot=90, ref_off=(-1.27, 3.81), val_off=(-1.27, 6.35))
    path(M, (xn, M[1]), (xn, yf), (xn, yc), fs["1"][:2]); junction(xn, yf); junction(xn, yc)
    path((xn, yf), rf["1"][:2])
    path(rf["2"][:2], rv["1"][:2])
    path((xn, yc), cf["1"][:2])
    path(fs["3"][:2], (xn, fs["3"][1] + 2.54)); power("power:GND", xn, fs["3"][1] + 2.54)
    # output node and feedback
    xo = bx + 12.7
    path(rv["2"][:2], (rv["3"][0], rv["2"][1]), rv["3"][:2])
    path(rv["3"][:2], (xo, yf), (xo, O[1]))
    junction(rv["3"][0], rv["3"][1])
    path(cf["2"][:2], (xo, yc), (xo, yf)); junction(xo, yf)
    lk = place("pfe_combat_mirror:Link", f"JP{k + 2}", "OUT", bx + 20.32, by, footprint=FP_LINK, ref_off=(-2.54, -3.81), val_off=(-2.54, 3.81))
    path(O, (xo, O[1]), lk["1"][:2]); junction(xo, O[1])
    ro = place("Device:R", f"RO{k}", "1k", bx + 30.48, by, footprint=FP_R, rot=90, ref_off=(-1.27, -2.54), val_off=(-1.27, -5.08))
    path(lk["2"][:2], ro["1"][:2])
    xz = bx + 38.1
    co = place("Device:C", f"CO{k}", "330n", xz, by + 5.08, footprint=FP_C)
    path(ro["2"][:2], (xz, by), (bx + 43.18, by)); junction(xz, by)
    path((xz, by), co["1"][:2]); path(co["2"][:2], (xz, co["2"][1] + 2.54)); power("power:GND", xz, co["2"][1] + 2.54)
    label(f"ADC{k}", bx + 43.18, by, 0)
    # test points: op-amp output and ADC input
    path((xo, O[1]), (xo, by - 5.08)); testpoint(xo, by - 5.08, f"OUT{k}", f"TP{k}")
    path((xz, by), (xz, by - 5.08)); junction(xz, by); testpoint(xz, by - 5.08, f"ADC{k}", f"TP{k + 4}")

# --- Nucleo connection: Arduino headers of the NUCLEO-F072RB (shield)
text("NUCLEO-F072RB Arduino headers (shield, male pins soldered on the copper side)", 312.42, 33.02, 1.5)
j1 = place("Connector_Generic:Conn_01x08", "J1", "CN6 power", 330.2, 50.8, footprint=FP_J8, ref_off=(2.54, -12.7), val_off=(2.54, 12.7))
for n in "1235": noconnect(j1[n])
noconnect(j1["8"])
x0, y0, _ = j1["4"]; path((x0, y0), (x0 - 7.62, y0)); label("3V3_NUCLEO", x0 - 7.62, y0, 180)
for n in "67":
    x0, y0, _ = j1[n]; path((x0, y0), (x0 - 2.54, y0))
path((j1["6"][0] - 2.54, j1["6"][1]), (j1["7"][0] - 2.54, j1["7"][1]), (j1["7"][0] - 2.54, j1["7"][1] + 2.54)); junction(j1["7"][0] - 2.54, j1["7"][1])
power("power:GND", j1["7"][0] - 2.54, j1["7"][1] + 2.54)
text("CN6: 1 NC  2 IOREF  3 RESET  4 +3V3  5 +5V  6 GND  7 GND  8 VIN", 312.42, 68.58)

j2 = place("Connector_Generic:Conn_01x06", "J2", "CN8 analog", 330.2, 86.36, footprint=FP_J6, ref_off=(2.54, -10.16), val_off=(2.54, 10.16))
for n, name in zip("12345", ["ADC1", "ADC2", "ADC3", "ADC4", "VREF"]):
    x0, y0, _ = j2[n]; path((x0, y0), (x0 - 7.62, y0)); label(name, x0 - 7.62, y0, 180)
noconnect(j2["6"])
text("CN8: A0/PA0  A1/PA1  A2/PA4  A3/PB0  A4/PC1  A5/PC0", 312.42, 101.6)

j3 = place("Connector_Generic:Conn_01x08", "J3", "CN9 digital", 330.2, 121.92, footprint=FP_J8, ref_off=(2.54, -12.7), val_off=(2.54, 12.7))
for n in "123456": noconnect(j3[n])
x0, y0, _ = j3["7"]; path((x0, y0), (x0 - 7.62, y0)); label("CAM_STROBE", x0 - 7.62, y0, 180)
x0, y0, _ = j3["8"]; path((x0, y0), (x0 - 7.62, y0)); label("CAM_TRIG", x0 - 7.62, y0, 180)
text("CN9: D0/PA3 D1/PA2 (ST-LINK UART, keep free)  D6/PB10 (TIM2_CH3) strobe in  D7/PA8 (TIM1) trigger out", 312.42, 139.7)

# --- camera connector
text("Cameras", 312.42, 152.4, 1.5)
j4 = place("Connector_Generic:Conn_01x03", "J4", "CAMERAS", 330.2, 165.1, footprint=FP_J3H, ref_off=(2.54, -5.08), val_off=(2.54, 5.08))
x0, y0, _ = j4["1"]; path((x0, y0), (x0 - 7.62, y0)); label("CAM_TRIG", x0 - 7.62, y0, 180)
x0, y0, _ = j4["2"]; path((x0, y0), (x0 - 7.62, y0)); label("CAM_STROBE", x0 - 7.62, y0, 180)
x0, y0, _ = j4["3"]; path((x0, y0), (x0 - 2.54, y0), (x0 - 2.54, y0 + 2.54)); power("power:GND", x0 - 2.54, y0 + 2.54)
text("1 trigger (to camera F pads)  2 strobe (from camera S pad)  3 GND", 312.42, 175.26)

# --- 3V3 link (ammeter) and common test points
text("Supply link and test points", 30.48, 116.84, 2)
jpw = place("pfe_combat_mirror:Link", "JP2", "3V3", 50.8, 127, footprint=FP_LINK, ref_off=(-2.54, -3.81), val_off=(-2.54, 3.81))
path(jpw["1"][:2], (40.64, 127)); label("3V3_NUCLEO", 40.64, 127, 180)
path(jpw["2"][:2], (63.5, 127), (63.5, 124.46)); power("power:+3V3", 63.5, 124.46)
text("JP2 closed in normal use; remove the jumper to put an ammeter in series", 30.48, 134.62)
c3 = place("Device:C", "C3", "10u elec. (+ on 3V3)", 71.12, 132.08, footprint="Capacitor_THT:CP_Radial_D5.0mm_P2.50mm")
path(c3["1"][:2], (71.12, 124.46)); power("power:+3V3", 71.12, 124.46)
path(c3["2"][:2], (71.12, 139.7)); power("power:GND", 71.12, 139.7)
path((40.64, 149.86), (40.64, 154.94)); testpoint(40.64, 149.86, "VREF", "TP9"); label("VREF", 40.64, 154.94, 270)
path((53.34, 149.86), (53.34, 154.94), (58.42, 154.94), (58.42, 152.4)); testpoint(53.34, 149.86, "3V3", "TP10"); power("power:+3V3", 58.42, 152.4)
for i, gx in enumerate((66.04, 76.2, 86.36, 96.52)):
    path((gx, 149.86), (gx, 154.94)); testpoint(gx, 149.86, "GND", f"TP{11 + i}"); power("power:GND", gx, 154.94)
text("TP1-TP4 op-amp outputs, TP5-TP8 ADC inputs, TP11-TP14 ground (one per channel, for the probe clips)", 30.48, 165.1)
text("JP3-JP6 closed in normal use; remove to drive the RO/CO filter from a generator", 30.48, 170.18)

text("V_OUT = V_REF x (1 + R_F / R_sensor), with R_F = RF + RV", 30.48, 22.86, 2)
text("CF across R_F: op-amp stability (Tekscan FlexiForce A201 datasheet Rev I)", 30.48, 27.94, 1.5)

out = ('(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0") '
       f'(uuid "{ROOT}") (paper "A3") '
       '(title_block (title "FlexiForce conditioning - 4 channels, Nucleo shield") (date "2026-11-23") (rev "3.1") '
       '(company "Polytech Montpellier - PFE Combat Mirror") (comment 1 "A. Duchene")) '
       '(lib_symbols ' + " ".join(LIB.values()) + ') '
       + " ".join(items) +
       ' (sheet_instances (path "/" (page "1"))))')

# pretty-ish formatting: one top-level element per line
out = out.replace(") (junction", ")\n  (junction").replace(") (symbol (lib_id", ")\n  (symbol (lib_id").replace(") (wire", ")\n  (wire").replace(") (label", ")\n  (label").replace(") (text", ")\n  (text").replace(") (no_connect", ")\n  (no_connect")
open(f"{PROJECT}.kicad_sch", "w").write(out + "\n")
pro = {"meta": {"filename": f"{PROJECT}.kicad_pro", "version": 1}}
lib_txt = "\n  ".join(LIB[k].replace(f'(symbol "{k}"', f'(symbol "{k.split(":")[1]}"') for k in LIB if k.startswith("pfe_combat_mirror:"))
open("pfe_combat_mirror.kicad_sym", "w").write('(kicad_symbol_lib (version 20231120) (generator "kicad_symbol_editor") (generator_version "8.0")\n  ' + lib_txt + '\n)\n')
open("sym-lib-table", "w").write('(sym_lib_table\n  (version 7)\n  (lib (name "pfe_combat_mirror")(type "KiCad")(uri "${KIPRJMOD}/pfe_combat_mirror.kicad_sym")(options "")(descr "PFE Combat Mirror project symbols"))\n)\n')
open(f"{PROJECT}.kicad_pro", "w").write(json.dumps(pro, indent=2) + "\n")

# sanity: balanced parentheses
d = 0
for ch in out:
    d += (ch == "(") - (ch == ")")
    assert d >= 0
print("balanced:", d == 0, "symbols:", out.count("(lib_id"), "labels:", out.count("(label"))
