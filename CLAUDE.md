# printed-keycap-mods-ss

Fork of [wolfwood/printed-keycap-mods](https://github.com/wolfwood/printed-keycap-mods) for printing **Chicago Steno profile keycaps** on a **Sofle MX** keyboard.
- Printer: Bambu A1 Mini (180×180mm build plate)
- Filament: Tecbears transparent PETG
- Stem: Choc stems at MX spacing (19mm)

## Key files

| File | Purpose |
|------|---------|
| `CS/CS.scad` | Main file: `printable()`, `CS_from_source()`, `CS_prerendered()` |
| `CS/CS-bindings/sculpted.scad` | Row keys R1-R4 via `Choc_Chicago_Steno.scad` |
| `CS/CS-bindings/thumb.scad` | Thumb keys via `Choc_Chicago_Steno_Thumb.scad` |
| `includes/PseudoMakeMeKeyCapProfiles/Choc_Chicago_Steno.scad` | Non-thumb profile (R1-R4) |
| `includes/PseudoMakeMeKeyCapProfiles/Choc_Chicago_Steno_Thumb.scad` | Thumb profile |
| `settings.scad` | Keyboard name, grid spacing |
| `Makefile` | Builds STLs: `make cs` |
| `make-3mf.py` | Packs STLs into 3MF plate files for Bambu Studio |

## Build

```bash
# OpenSCAD is installed as an app, not in PATH
OPENSCAD=/Applications/OpenSCAD-2021.01.app/Contents/MacOS/OpenSCAD make cs

# Single STL
OPENSCAD=/Applications/OpenSCAD-2021.01.app/Contents/MacOS/OpenSCAD make things/CS-T1L.stl

# 3MF plates
python3 make-3mf.py
```

**CGAL errors are expected** — they appear for all keys including the working R3. OpenSCAD 2021 produces them for this profile's complex sweep geometry; the STL output is still valid.

## Key types

| Type | Description | Status |
|------|-------------|--------|
| R1, R2, R3, R3-homing, R4 | Standard row keys | ✅ Working |
| T1L, T1R | 1u thumb keys (left/right) | ⚠️ See below |
| T1L-trap, T1R-trap | Trapezoidal outer thumb keys | 🔜 Future task |

## `printable()` module

Applied at `printable() CS(keycap)` — tilts the keycap 45° around the Y axis so a flat face rests on the print bed, then makes two chamfer cuts for bed adhesion:

1. Bottom cut: `translate([0,0,-h/2 - cut_distance]) cube(...)` — trims below z=-4.9
2. Front cut: `rotate([90,0,0]) translate([0,0,-h/2 - cut_distance]) cube(...)` — trims the front face (y > 4.9), straight cut (no XY diagonal needed)

## TWO DIFFERENT PROFILE FILES — critical distinction

| File | Used by | `keycap()` dish impl | Stem transition |
|------|---------|---------------------|-----------------|
| `Choc_Chicago_Steno.scad` | R1-R4 (sculpted_key) | `DishShape` (simple) | 50 steps, variable radius |
| `Choc_Chicago_Steno_Thumb.scad` | Thumb keys (thumb_key) | `DishShape2` (complex, tangent arcs) | 70 steps, fixed r=1 |

These are fundamentally different `keycap()` implementations. **Do not assume parameter changes in one apply to the other.**

## ⚠️ UNRESOLVED: T1L / T1R shelf issue

**Problem**: T1L and T1R have a "shelf" — a flat rectangular ledge protruding from the curved keycap body. Row keys R1-R4 are fine.

**Root cause**: `Choc_Chicago_Steno_Thumb.scad` keyID=2 was originally Choc-sized (17.20×16.00mm) with its own thumb dish — and worked correctly. An earlier session scaled keyParameters to 18.05×18.05mm (keeping XSkew=-3, YSkew=-3) which introduced the shelf. The Thumb profile's `DishShape2` with tangent arc params works at Choc size but breaks at MX size.

**Original keyID=2 in git (Choc-sized, no shelf):**
- keyParameters: `[17.20, 16.00, 4.25, 3.25, 5.0, -.5, 0.0, -3, -3, -0, 2, 2, .10, 2, .10, 2, 2, 2]`
- dishParameters: `[5, 5.5, 0, -40, 7, 1.7, 16, 18, 2, 5.5, 3.5, 5, -50, 16, 18, 2, 5, 3.75, 2, 3.75, 2, 199, 210]`

The original dish had FPit1=0 (no forward pitch), FArcIn=16, FArcFn=18 — these are the thumb-specific values that produced the correct shape.

**What has been changed so far (current state of repo):**

1. `CS/CS.scad` `printable()` line 111: second cut changed from buggy `rotate([0,-90,0])` → `rotate([90,0,0])`. This is correct (front face chamfer, no XY diagonal needed). Do NOT revert this.

2. `Choc_Chicago_Steno_Thumb.scad` keyID=2 `keyParameters`: currently set to Levee R3 params at MX scale:
   ```
   [18.05, 18.05, 5.6, 5, 4.6, 0, 0, 0, 0, -0, 2, 2.5, .10, 3, .10, 3, 2, 2]
   ```
   (XSkew=0, YSkew=0, WSft=0 — removed the -3/-3/-0.5 that caused the diagonal lean)

3. `Choc_Chicago_Steno_Thumb.scad` keyID=2 `dishParameters`: changed to Levee R3 flat dish (copy of dishParameters[1]):
   ```
   [4.5, 4, 5, -40, 7, 1.7, 11, 15, 2, 4.5, 4, 5, -40, 11, 15, 2, 4, 5, 4, 5, 2, 200, 210]
   ```

**What still needs fixing**: The shelf persists. The Thumb profile's `DishShape2` geometry at 18.05mm still doesn't produce a clean keycap matching the original Levee Steno thumb shape. The fix must stay within `Choc_Chicago_Steno_Thumb.scad` — retaining the thumb-specific geometry — and correctly scale the dish/body parameters for MX (18.05mm) dimensions.

**Key insight for next session**: The original Levee Steno thumb at Choc size (17.20×16.00mm, keyID=0 or keyID=1 in the Thumb file) worked correctly. The `DishShape2` tangent arc parameters (`PhiInit`, `PhiFin`, `FTanRadius`, `BTanRadius`) need to be scaled for 18.05mm. Compare working Choc-size dish params vs. what's needed at MX scale. The non-thumb `Choc_Chicago_Steno.scad` R3 at 18.05mm uses the simpler `DishShape` function — studying how it scales might give clues.

## Sofle MX thumb cluster

5 thumb keys per half. Intended layout: 3 standard T1 + 2 trapezoidal T1-trap (outer positions). The trap keys have one angled edge lining up with the adjacent key.
