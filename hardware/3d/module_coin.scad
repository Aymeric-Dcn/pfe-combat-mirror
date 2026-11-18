// PFE Combat Mirror - Corner module of the force plate
// One FlexiForce A201 per corner, sandwiched between the base plate
// and the strike plate. Load path: strike plate -> upper support (cone)
// -> steel ball -> puck -> sensor -> base.
// Preload: 2 threaded rods per module with springs and nuts above the
// upper support ears. Turning the nuts brings the stack into contact and
// equalises the 4 corners. The springs are much softer than the sensor,
// so they carry almost none of the impact force.
//
// Select the part with "part", then F6 and File > Export > STL.
// Print orientation: base and ring flat; upper support with the ears on
// the bed (cone opening on the bed, 45 deg overhang, no support needed).

/* [Display] */
part = "assembly"; // [assembly, base, ring, puck, upper_support, print_plate]
show_plates = true;

/* [FlexiForce A201 sensor] */
sensor_d = 14.0;      // diameter of the round sensor end (check on the part)
sensor_t = 0.25;      // sensor thickness
tail_w = 14.0;        // width of the sensor tail
sensing_d = 9.53;     // sensing area diameter (datasheet)

/* [Puck and ball] */
puck_d = 9.0;         // slightly smaller than the sensing area
puck_h = 3.5;
ball_d = 8.0;         // steel bearing ball
cup_depth = 2.0;      // depth of the spherical cup in the puck

/* [Base (bottom plate side)] */
base_l = 64;
base_w = 44;
base_h = 6;

/* [Guide ring] */
ring_l = 32;
ring_w = 20;
pocket_h = 0.8;       // sensor pocket height under the ring
guide_h = 2.5;        // puck guiding height
clr = 0.2;            // printing clearance

/* [Preload rods] */
rod_d = 5;            // M5
rod_spacing = 48;
nut_af = 8;           // M5 nut across flats
nut_h = 4;
spring_l = 28.5;      // spring free length (RS PRO 751-584: OD 9, wire 1 mm, 2.33 N/mm)
spring_od = 9;

/* [Upper support (strike plate side)] */
ear_h = 6;
column_c = 36;
column_h = 30;

/* [Plate fastening] */
screw_d = 4;          // wood screws
head_d = 8.5;
plate_t = 18;         // plate thickness (display only)

$fn = 64;

// ---------- Derived dimensions ----------
z_sensor = base_h;
z_puck = base_h + sensor_t;
ball_r = ball_d / 2;
z_ball = z_puck + puck_h + ball_r - cup_depth;   // ball centre
cone_depth = ball_r * sqrt(2);                   // 90 deg cone
z_upper = z_ball;                                // upper support underside
upper_h = ear_h + column_h;
gap_plates = z_upper + upper_h;
rod_len = z_upper + ear_h + spring_l + 1 + nut_h + 3;
clearance = z_upper - (base_h + pocket_h + guide_h);

echo(str("Gap between plates: ", gap_plates, " mm"));
echo(str("Rod length (from the bottom of the base): ", rod_len, " mm"));
echo(str("Clearance between upper support and ring: ", clearance, " mm"));

// ---------- Parts ----------
module countersunk(d, head, depth_total) {
    translate([0, 0, -1]) cylinder(d = d + 0.5, h = depth_total + 2);
    translate([0, 0, depth_total - (head - d) / 2])
        cylinder(d1 = d + 0.5, d2 = head, h = (head - d) / 2 + 0.01);
    translate([0, 0, depth_total]) cylinder(d = head, h = 1);
}

module base() {
    difference() {
        translate([-base_l / 2, -base_w / 2, 0]) cube([base_l, base_w, base_h]);
        // preload rods: through hole + nut trap underneath
        for (sx = [-1, 1]) translate([sx * rod_spacing / 2, 0, 0]) {
            translate([0, 0, -1]) cylinder(d = rod_d + 0.4, h = base_h + 2);
            translate([0, 0, -0.01])
                cylinder(d = nut_af / cos(30) + 0.3, h = nut_h + 0.3, $fn = 6);
        }
        // fastening to the bottom plate (countersunk)
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * 13, sy * 16, 0])
            countersunk(screw_d, head_d, base_h);
        // pilot holes for the ring M3 screws
        for (sx = [-1, 1]) translate([sx * 12, 0, base_h - 5])
            cylinder(d = 2.6, h = 5.1);
    }
}

module ring() {
    h = pocket_h + guide_h;
    difference() {
        translate([-ring_l / 2, -ring_w / 2, 0]) cube([ring_l, ring_w, h]);
        // puck bore
        translate([0, 0, -1]) cylinder(d = puck_d + 2 * clr, h = h + 2);
        // pocket for the round sensor end
        translate([0, 0, -0.01]) cylinder(d = sensor_d + 2 * clr, h = pocket_h);
        // tail channel towards +Y
        translate([-(tail_w + 2 * clr) / 2, 0, -0.01])
            cube([tail_w + 2 * clr, ring_w, pocket_h]);
        // M3 screws
        for (sx = [-1, 1]) translate([sx * 12, 0, -1]) cylinder(d = 3.4, h = h + 2);
    }
}

module puck() {
    difference() {
        cylinder(d = puck_d, h = puck_h);
        translate([0, 0, puck_h + ball_r - cup_depth]) sphere(r = ball_r + 0.1);
    }
}

module upper_support() {
    difference() {
        union() {
            translate([-base_l / 2, -base_w / 2, 0]) cube([base_l, base_w, ear_h]);
            translate([-column_c / 2, -column_c / 2, 0]) cube([column_c, column_c, upper_h]);
        }
        // 90 deg centring cone for the ball
        translate([0, 0, -0.01]) cylinder(h = cone_depth, r1 = cone_depth, r2 = 0);
        // preload rod clearance holes
        for (sx = [-1, 1]) translate([sx * rod_spacing / 2, 0, -1])
            cylinder(d = rod_d + 1.5, h = ear_h + 2);
        // fastening to the strike plate: access counterbore from below
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * 11, sy * 11, 0]) {
            translate([0, 0, -1]) cylinder(d = screw_d + 0.5, h = upper_h + 2);
            translate([0, 0, -1]) cylinder(d = head_d + 0.5, h = upper_h - 8 + 1);
        }
    }
}

// ---------- Interface for test_rig.scad ----------
function corner_gap() = gap_plates;
function corner_footprint() = [base_l, base_w];

// Fastening holes, seen from the gap (for drilling templates)
module base_holes_2d() {
    for (sx = [-1, 1], sy = [-1, 1]) translate([sx * 13, sy * 16]) circle(d = screw_d);
}
module upper_holes_2d() {
    for (sx = [-1, 1], sy = [-1, 1]) translate([sx * 11, sy * 11]) circle(d = screw_d);
}

// ---------- Assembly ----------
module sensor_model() {
    color("goldenrod") translate([0, 0, z_sensor]) {
        cylinder(d = sensor_d, h = sensor_t);
        translate([-tail_w / 2, 0, 0]) cube([tail_w, base_w / 2 + 10, sensor_t]);
    }
    color("black") translate([0, 0, z_sensor + sensor_t]) cylinder(d = sensing_d, h = 0.05);
}

module assembly(plates = true) {
    color("steelblue") base();
    color("lightskyblue") translate([0, 0, base_h]) ring();
    sensor_model();
    color("silver") translate([0, 0, z_puck]) puck();
    color("gray") translate([0, 0, z_ball]) sphere(d = ball_d);
    color("orange", 0.9) translate([0, 0, z_upper]) upper_support();
    for (sx = [-1, 1]) translate([sx * rod_spacing / 2, 0, 0]) {
        color("dimgray") cylinder(d = rod_d, h = rod_len);
        color("dimgray") cylinder(d = nut_af / cos(30), h = nut_h, $fn = 6);
        color("seagreen", 0.6) translate([0, 0, z_upper + ear_h])
            difference() {
                cylinder(d = spring_od, h = spring_l * 0.8);
                translate([0, 0, -1]) cylinder(d = spring_od - 2, h = spring_l + 2);
            }
        color("dimgray") translate([0, 0, z_upper + ear_h + spring_l * 0.8])
            cylinder(d = nut_af / cos(30), h = nut_h, $fn = 6);
    }
    if (plates) {
        color("burlywood", 0.35)
            translate([-60, -50, -plate_t]) cube([120, 100, plate_t]);
        color("burlywood", 0.35)
            translate([-60, -50, gap_plates]) cube([120, 100, plate_t]);
    }
}

module print_plate() {
    base();
    translate([0, base_w / 2 + ring_w / 2 + 5, 0]) ring();
    translate([ring_l / 2 + 15, base_w / 2 + ring_w / 2 + 5, 0]) puck();
    translate([base_l + 10, 0, 0]) upper_support();
}

if (part == "assembly") assembly(show_plates);
else if (part == "base") base();
else if (part == "ring") ring();
else if (part == "puck") puck();
else if (part == "upper_support") upper_support();
else if (part == "print_plate") print_plate();
