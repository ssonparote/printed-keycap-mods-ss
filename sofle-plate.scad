// Sofle keycap print plates
// Usage: make sofle-plates
// Or: openscad -Dprofile=\"R1\" -o things/sofle-R1.stl sofle-plate.scad

profile = "R1";
spacing = 22;

count =
  profile == "R1"        ? 12 :
  profile == "R2"        ? 12 :
  profile == "R3"        ? 10 :
  profile == "R3-homing" ?  2 :
  profile == "R4"        ? 12 :
  profile == "T1L"       ?  5 :
  profile == "T1R"       ?  5 :
  assert(false, str("unknown profile: ", profile));

cols =
  profile == "R3-homing"                    ? 2 :
  (profile == "T1L" || profile == "T1R")    ? 5 :
  4;

module cap() {
  if      (profile == "R1")        import("things/CS-R1.stl");
  else if (profile == "R2")        import("things/CS-R2.stl");
  else if (profile == "R3")        import("things/CS-R3.stl");
  else if (profile == "R3-homing") import("things/CS-R3-homing.stl");
  else if (profile == "R4")        import("things/CS-R4.stl");
  else if (profile == "T1L")       import("things/CS-T1L.stl");
  else if (profile == "T1R")       import("things/CS-T1R.stl");
}

for (i = [0:count-1]) {
  translate([(i % cols) * spacing, floor(i / cols) * spacing, 0])
    cap();
}
