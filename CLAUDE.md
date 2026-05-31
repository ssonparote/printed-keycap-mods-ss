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
| T1L, T1R | 1u thumb keys (left/right) | ✅ Dish + chop fixed (verify render) |
| T1L-trap, T1R-trap | Trapezoidal outer thumb keys | 🔜 Future task |

## `printable()` module

The correct working `printable()` is from commit `91be5bb` ("add lateral..."). It has three transforms + two cuts:

1. Z orientation: `rotate([0,0,other ? -45 : 135])` — **no** `fans_on_left` term
2. Y tilt: `rotate([0,(other ? 1 : -1)*45,0])` — tilts 45° for printing on its side
3. Bottom cut: `translate([0,0,-h/2 - cut_distance]) cube([40,40,h], center=true)`
4. Side cut: `rotate([0,90,-45]) translate([0,0,-h/2 - cut_distance]) cube([40,40,h], center=true)`

**Commit history of `printable()` breakage** — `CS/CS.scad` HEAD (`8e94c43`, last night) changed `printable()` when adding Sofle MX thumb keys, removing the Z rotation and changing the second cut to `rotate([90,0,0])`. This broke R3 (and all keys). STLs for R3 must be rendered using the `91be5bb` version of CS.scad until the HEAD version is fixed.

**To render with the correct printable():**
```bash
git show 91be5bb:CS/CS.scad > CS/CS-tmp.scad
/Applications/OpenSCAD-2021.01.app/Contents/MacOS/OpenSCAD -q --render -Dkeycap=\"R3\" -o things/CS-R3.stl CS/CS-tmp.scad
rm CS/CS-tmp.scad
```

**Do not** use the committed `CS/CS.scad` (HEAD) to render row keys until `printable()` is fixed.

## TWO DIFFERENT PROFILE FILES — critical distinction

| File | Used by | `keycap()` dish impl | Stem transition |
|------|---------|---------------------|-----------------|
| `Choc_Chicago_Steno.scad` | R1-R4 (sculpted_key) | `DishShape` (simple) | 50 steps, variable radius |
| `Choc_Chicago_Steno_Thumb.scad` | Thumb keys (thumb_key) | `DishShape2` (complex, tangent arcs) | 70 steps, fixed r=1 |

These are fundamentally different `keycap()` implementations. **Do not assume parameter changes in one apply to the other.**

## T1L / T1R shelf — root cause and fix applied

**Problem**: T1L and T1R had a "shelf" — a flat rectangular ledge protruding from the curved keycap body. Row keys R1-R4 are fine.

**Root cause (confirmed)**: The `DishShape2` function used by the Thumb profile requires larger arc values (`FArcIn`/`FArcFn`) than the simpler `DishShape` used by row keys. When the dish params for keyID=2 were replaced with a copy of the R3 flat row params (`FArcIn=11, FArcFn=15`), the DishShape2 cutting solid no longer spanned the full key top — leaving the shelf. Numerical analysis showed the profile y-span dropped from 27.7–32.5 (original, working) to 23.4–27.1 (broken).

**Fix applied** (`Choc_Chicago_Steno_Thumb.scad` line 82): Restored the original Choc T1 dish params:
```
[5, 5.5, 0, -40, 7, 1.7, 16, 18, 2, 5.5, 3.5, 5, -50, 16, 18, 2, 5, 3.75, 2, 3.75, 2, 199, 210]
```
Key changes: FArcIn 11→16, FArcFn 15→18, FPit1 5→0, FTanFin 5→3.75, BTanInit 4→2, PhiInit 200→199.
These worked at Choc size (12.95×12.75mm top); MX top is 12.45×13.05mm — nearly identical.

**Current state of keyID=2:**
- keyParameters: `[18.05, 18.05, 5.6, 5, 4.6, 0, 0, 0, 0, -0, 2, 2.5, .10, 3, .10, 3, 2, 2]` (XSkew=0, YSkew=0 — correct, no lean)
- dishParameters: restored original Choc T1 thumb dish (line 82)

**How to verify**: Open `Choc_Chicago_Steno_Thumb.scad` with `keyID=2, visualizeDish=true, crossSection=true`. The dish cutting solid should span all the way to the edges of the key top with no flat ledge remaining. Compare with keyID=0 (working original Choc thumb) as reference shape.

**If shelf persists after this fix**: Scale FArcIn/FArcFn slightly upward (try 17/19) — the MX key length (13.05mm) is slightly longer than original (12.75mm). Keep all other original params unchanged.

**Do NOT use** `rotate([90,0,0])` for the second cut — that was introduced by the broken `8e94c43` commit and cuts the wrong plane.

## Sofle MX thumb cluster

5 thumb keys per half. Intended layout: 3 standard T1 + 2 trapezoidal T1-trap (outer positions). The trap keys have one angled edge lining up with the adjacent key.
