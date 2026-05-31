use <../trackpoint_notch.scad>;
include <../settings.scad>;

use <CS-bindings/sculpted.scad>;
use <CS-bindings/thumb.scad>;
use <CS-bindings/convex.scad>;

prerendered=false;

module CS(type="R3") {
  if (prerendered) {
    CS_prerendered(type);
  } else {
    CS_from_source(type);
  }
}

module invert_offset(x=true, y=true, z=false) {
  if (is_undef($stem_offset)) {
    children();
  } else {
    temp = [$stem_offset.x * (x ? -1 : 1), $stem_offset.y * (y ? -1 : 1), $stem_offset.z * (z ? -1 : 1)];
    //echo("whut ", temp, $stem_offset, is_undef($stem_offset),  ($stem_offset * -1));
    children($stem_offset = temp );
  }
}

// Naming: L/R = keyboard HALF. The L-half cap keeps the original transform; the R-half cap
// is its X-mirror (mirror([1,0,0])), which flips the asymmetric outboard cut to the opposite
// edge so the two halves mirror each other. Side-column keys carry a COL tag so L/R is not
// overloaded with column position. Thumbs already used L/R for the half.
module CS_from_source(type="R3L") {
  $fn=60;

  // --- main rows (sculpted profile) ---
  if (type == "R1L") {
    mirror([0,1,0]) sculpted_key("R1");
  } else if (type == "R1R") {
    mirror([1,0,0]) mirror([0,1,0]) sculpted_key("R1");
  } else if (type == "R2L") {
    mirror([0,1,0]) sculpted_key("R4");
  } else if (type == "R2R") {
    mirror([1,0,0]) mirror([0,1,0]) sculpted_key("R4");
  } else if (type == "R3L") {
    sculpted_key("R3");
  } else if (type == "R3R") {
    mirror([1,0,0]) sculpted_key("R3");
  } else if (type == "R3-homing-L") {
    sculpted_key("R3", homing=true);
  } else if (type == "R3-homing-R") {
    mirror([1,0,0]) sculpted_key("R3", homing=true);
  } else if (type == "R4L") {
    invert_offset() sculpted_key("R4");
  } else if (type == "R4R") {
    mirror([1,0,0]) invert_offset() sculpted_key("R4");

  // --- side columns (thumb profile); transforms preserved from the old side-column entries ---
  } else if (type == "R2-COL-L") {
    mirror([1,0,0]) invert_offset(y=false) thumb_key("R2L");
  } else if (type == "R4-COL-R") {
    mirror([1,0,0]) invert_offset(x=false) thumb_key("R2L");
  } else if (type == "R4-COL-L") {
    // smoother feel if you don't print with the curved side at the top
    rotate([0,0,180]) invert_offset() thumb_key("R2L");
  } else if (type == "R2-COL-R") {
    rotate([0,0,180]) thumb_key("R2L");
  } else if (type == "R3-COL-L") {
    rotate([0,0,180]) invert_offset() thumb_key("R3L");
  } else if (type == "R3-COL-R") {
    rotate([0,0,180]) thumb_key("R3L");

  // --- thumbs (L/R already = half) ---
  } else if (type == "T1L") {
    // smoother feel if you don't print with the curved side at the top
    rotate([0,0,180]) invert_offset() thumb_key("T1");
  } else if (type == "T1R") {
    mirror([1,0,0]) invert_offset(x=false) thumb_key("T1");
  } else if (type == "T1L-trap") {
    rotate([0,0,180]) invert_offset() thumb_key_trap();
  } else if (type == "T1R-trap") {
    mirror([1,0,0]) invert_offset(x=false) thumb_key_trap();

  // --- convex inner-column / thumb key ---
  } else if (type == "R3xL") {
    convex_key("R3x");
  } else if (type == "R3xR") {
    mirror([1,0,0]) convex_key("R3x");
  } else {
    assert(false, str("unrecognized Chicago Steno keycap type: ", type));
  }
}

// Lev's reference STLs have no L/R-half cut variants, so R-half = X-mirror of the L import.
module CS_prerendered(type="R3L") {
  // --- main rows ---
  if (type == "R3L") {
    import("levs-CS/r3-middle-row.stl");
  } else if (type == "R3R") {
    mirror([1,0,0]) import("levs-CS/r3-middle-row.stl");
  } else if (type == "R3-homing-L") {
    import("levs-CS/r3-homing.stl");
  } else if (type == "R3-homing-R") {
    mirror([1,0,0]) import("levs-CS/r3-homing.stl");
  } else if (type == "R2L") {
    rotate([0,0, 180]) import("levs-CS/r2r4-topbottom-rows.stl");
  } else if (type == "R2R") {
    mirror([1,0,0]) rotate([0,0, 180]) import("levs-CS/r2r4-topbottom-rows.stl");
  } else if (type == "R4L") {
    import("levs-CS/r2r4-topbottom-rows.stl");
  } else if (type == "R4R") {
    mirror([1,0,0]) import("levs-CS/r2r4-topbottom-rows.stl");

  // --- side columns ---
  } else if (type == "R2-COL-L" || type == "R4-COL-R") {
    import("levs-CS/r2r4L-side-columns.stl");
  } else if (type == "R3-COL-L" || type == "R3-COL-R") {
    import("levs-CS/r3L-side-columns.stl");
  } else if (type == "R4-COL-L" || type == "R2-COL-R") {
    mirror([0,1,0]) import("levs-CS/r2r4L-side-columns.stl");

  // --- thumbs ---
  } else if (type == "T1L") {
    rotate([0,0,180])
      mirror([1,0,0]) import("levs-CS/thumb-1u.stl");
  } else if (type == "T1R") {
    import("levs-CS/thumb-1u.stl");

  // --- convex ---
  } else if (type == "R3xL") {
    import("levs-CS/convex-1u-for-thumbs-or-inner-index-column.stl");
  } else if (type == "R3xR") {
    mirror([1,0,0]) import("levs-CS/convex-1u-for-thumbs-or-inner-index-column.stl");
  } else {
    assert(false, str("unrecognized Chicago Steno keycap type: ", type));
  }
}

// Render mode. Override on the command line with -Dprint=false to get the cap
// upright (cuts baked in) for design validation; default true tilts it for printing.
print = is_undef(print) ? true : print;

// Print-orientation transform R: tilt the upright cap onto its print face.
//   inner  rotate([0,(other?1:-1)*45,0])  -- 45 deg about Y, onto its side
//   outer  rotate([0,0,other?-45:135])    -- spin flat onto the bed
// These are the known-good rotations (from commit 91be5bb).
module orient(other=false) {
  rotate([0,0,other ? -45 : 135])
    rotate([0,(other ? 1 : -1)*45,0])
      children();
}

// bed_cut bakes the bed-adhesion cuts into the cap's NATIVE upright frame, so the
// upright cap you inspect already carries the angled flat print faces -- the cut is
// part of the design, not bolted on after tilting. It does this by orienting forward,
// subtracting the cut tools in the print frame, then orienting back (R then R^-1), so
// the cuts land exactly where they will sit on the bed. printable() only re-applies R.
module bed_cut(other=false) {
  // R^-1: undo orient(), leaving the cut cap sitting upright.
  rotate([0,(other ? -1 : 1)*45,0])
  rotate([0,0,other ? 45 : -135])
  difference(){
    orient(other) children();
    h=5;
    cut_distance=4.9;
    translate([0,0,-h/2 - cut_distance]) cube([40,40,h], center=true);
    rotate([0,90,-45]) translate([0,0,-h/2 - cut_distance]) cube([40,40,h], center=true);
  }
}

// printable() is now pure orientation. When print=false it is a pass-through so the
// (already bed-cut) cap renders upright for design validation.
module printable(other=false) {
  if (print) orient(other) children();
  else children();
}

index = false;
lateral=true;

if (is_undef(keycap)) {
  let(x_spacing = is_list(grid_spacing) ? grid_spacing.x : grid_spacing, y_spacing = is_list(grid_spacing) ? grid_spacing.y : grid_spacing, stagger = is_undef(grid_stagger) ? 0 : grid_stagger ? y_spacing/2 : 0) {
    if (!index) { // middle
      if (is_undef(tpkey) || tpkey == "R3-homing") printable() bed_cut() trackpoint_notch(far=true) CS("R3L");
      if (is_undef(tpkey) || tpkey == "R2-near") translate(is_undef(tpkey) ? [0,y_spacing,0] : [0,0,0]) printable() bed_cut() trackpoint_notch(far=false) CS("R2-COL-R");
      if (is_undef(tpkey) || tpkey == "R3") translate(is_undef(tpkey) ? [x_spacing,stagger,0] : [0,0,0]) printable(other=true) bed_cut(other=true) mirror([1,0,0]) trackpoint_notch(far=false, index=true) CS("R3-COL-R");
      if (is_undef(tpkey) || tpkey == "R2-far") translate(is_undef(tpkey) ? [x_spacing,stagger+y_spacing,0] : [0,0,0]) printable(other=true) bed_cut(other=true) mirror([1,0,0]) trackpoint_notch(far=true, index=true) CS("R2L");

    } else { // index

      if ((is_undef(tpkey) || tpkey == "R3-homing") && !lateral) printable(other=true) bed_cut(other=true) trackpoint_notch($x=-1,$y=1,far=false, index=true) CS("R3-homing-L");
      if ((is_undef(tpkey) || tpkey == "R2-far") && !lateral) translate(is_undef(tpkey) ? [0,y_spacing,0] : [0,0,0]) printable(other=true) bed_cut(other=true) trackpoint_notch($x=-1,$y=-1,far=true) CS("R2L");
      if ((is_undef(tpkey) || tpkey == "R3") && !lateral) translate(is_undef(tpkey) ? [x_spacing,stagger,0] : [0,0,0]) printable() bed_cut() trackpoint_notch($x=1,$y=1,far=true) CS("R3L");
      if ((is_undef(tpkey) || tpkey == "R2-near") && !lateral) translate(is_undef(tpkey) ? [x_spacing,stagger+y_spacing,0] : [0,0,0]) printable() bed_cut() trackpoint_notch($x=1,$y=-1,far=false) CS("R2L");

      if ((is_undef(tpkey) || tpkey == "R3-homing") && lateral) printable(other=true) bed_cut(other=true) trackpoint_notch($x=-1,$y=1,far=false) CS("R3-COL-R");
      if ((is_undef(tpkey) || tpkey == "R2-far") && lateral) translate(is_undef(tpkey) ? [0,y_spacing,0] : [0,0,0]) printable(other=true) bed_cut(other=true) trackpoint_notch($x=-1,$y=-1, far=true) CS("R2-COL-R");
      if ((is_undef(tpkey) || tpkey == "R3") && lateral) translate(is_undef(tpkey) ? [x_spacing,stagger,0] : [0,0,0]) printable() bed_cut() trackpoint_notch($x=1,$y=1,far=true) rotate([0,0,180]) CS("R3-COL-L");
      if ((is_undef(tpkey) || tpkey == "R2-near") && lateral) translate(is_undef(tpkey) ? [x_spacing,stagger+y_spacing,0] : [0,0,0]) printable() bed_cut() trackpoint_notch($x=1,$y=-1,far=false) rotate([0,0,180]) CS("R2-COL-L");
    }
  }
} else {
  printable() bed_cut() CS(keycap);
}

debug_orientation=false;

if (debug_orientation) {
  grid_stagger = false;
  !let(x_spacing = is_list(grid_spacing) ? grid_spacing.x : grid_spacing, y_spacing = is_list(grid_spacing) ? grid_spacing.y : grid_spacing, stagger = is_undef(grid_stagger) ? 0 : grid_stagger ? y_spacing/2 : 0) {
    one = "T1L";
    two= "T1R";

    if (!is_undef(two)) CS_from_source(two);
    translate([0,y_spacing,0]) CS_from_source(one);
    if (!is_undef(two)) translate([x_spacing,stagger,0]) printable() bed_cut() CS_from_source(two);
    translate([x_spacing,stagger+y_spacing,0]) printable() bed_cut() CS_from_source(one);
    if (!is_undef(two)) translate([2*x_spacing,stagger,0]) printable() CS_prerendered(two);
    translate([2*x_spacing,stagger+y_spacing,0]) printable() CS_prerendered(one);
    if (!is_undef(two)) translate([3*x_spacing,stagger,0]) CS_prerendered(two);
    translate([3*x_spacing,stagger+y_spacing,0]) CS_prerendered(one);
  }
}
