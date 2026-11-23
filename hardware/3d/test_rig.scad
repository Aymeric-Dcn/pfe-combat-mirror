// PFE Combat Mirror - 4-sensor test rig
// Two plates (base plate and strike plate) with one corner module per
// corner. Uses module_coin.scad, which must stay in the same folder.
//
// "assembly": 3D view of the rig.
// "template_bottom" / "template_top": 2D drilling templates at 1:1 scale.
//   F6, then File > Export > SVG or DXF, print at 100 % and tape it on
//   the plate. Templates are symmetric: no need to mirror them.

use <module_coin.scad>

/* [Display] */
part = "assembly"; // [assembly, template_bottom, template_top]

/* [Plates] */
plate_size = 300;     // 300 mm for the test rig, 1000 mm for the final plate
plate_t = 18;         // plate thickness
corner_inset = 45;    // distance from the plate edge to the module centre

$fn = 48;

a = plate_size / 2 - corner_inset;
gap = corner_gap();

// Module positions and orientation: sensor tails point to the centre of the
// plate, where the Nucleo and its shield sit between the plates
corners = [[ a,  a, 135], [-a,  a, 225],
           [ a, -a,  45], [-a, -a, 315]];

echo(str("Distance between sensors: ", 2 * a, " mm"));
echo(str("Gap between plates: ", gap, " mm"));

module rig() {
    for (c = corners) translate([c[0], c[1], 0]) rotate([0, 0, c[2]])
        assembly(false);
    color("burlywood", 0.35)
        translate([-plate_size / 2, -plate_size / 2, -plate_t])
            cube([plate_size, plate_size, plate_t]);
    color("burlywood", 0.25)
        translate([-plate_size / 2, -plate_size / 2, gap])
            cube([plate_size, plate_size, plate_t]);
}

module cross(s = 10) {
    square([s, 0.4], center = true);
    square([0.4, s], center = true);
}

module template(top) {
    difference() {
        square(plate_size, center = true);
        offset(delta = -0.5) square(plate_size, center = true);
    }
    cross(20);
    for (c = corners) translate([c[0], c[1]]) rotate(c[2]) {
        cross(8);
        difference() {
            if (top) upper_holes_2d(); else base_holes_2d();
            if (top) offset(delta = -0.4) upper_holes_2d();
            else offset(delta = -0.4) base_holes_2d();
        }
    }
}

if (part == "assembly") rig();
else if (part == "template_bottom") template(false);
else if (part == "template_top") template(true);
