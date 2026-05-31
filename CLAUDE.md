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

## Key types / naming

**`L`/`R` = keyboard HALF** (uniformly). Side-column keys carry a `COL` tag so the suffix is
not overloaded with column position. The R-half cap is the `mirror([1,0,0])` of the L-half
cap — this flips the asymmetric outboard bed cut to the opposite (outer) edge for the other
half. (Dispatch in `CS/CS.scad` `CS_from_source`; Makefile `CS_PROFILE`/`SOFLE_PROFILES`.)

| Group | Types | Source | Status |
|-------|-------|--------|--------|
| Main rows | `R1L/R1R R2L/R2R R3L/R3R R3-homing-L/R R4L/R4R` | `sculpted_key` (keyID 0/1/15) | ✅ render OK |
| Side columns | `R2-COL-L/R R3-COL-L/R R4-COL-L/R` | `thumb_key("R2L"/"R3L")` (keyID 0/1) | ✅ render OK |
| Thumbs | `T1L T1R` | `thumb_key("T1")` (keyID 2) | ✅ dish fixed |
| Thumb traps | `T1L-trap T1R-trap` | `thumb_key_trap()` (keyID 15) | 🔜 future |
| Convex | `R3xL R3xR` | `convex_key("R3x")` | ✅ render OK |

**Migration note:** old bare names (`R1`,`R2`,`R3`,`R3-homing`,`R4`) and old side-column
names (old `R2L/R3L/R4L`…) are **gone** — they now mean half-variants / `COL` keys. Anything
referencing the old STL names needs updating. **`make-3mf.py` still uses the old `CS-R1`…
names** and must be migrated before its plates will pack (it fails loudly on missing STLs).

**Cut status (Phase 2B done):** `bed_cut()` is a **single** horizontal slab — both the flat
bed-contact face and the outboard chamfer. The chamfer side is set by the **tilt handedness**
(`other` flag), driven per-half by `cs_is_right(type)` at the dispatch: L-half → chamfer left,
R-half → chamfer right. The inner edge stays full → tighter inner gaps. Rows are X-symmetric so
L/R share the cap shape (no cap mirror — the chamfer flip comes purely from `other`). Verified:
R3L print pose sits on a flat 14.3×14.3 mm face at z=−4.9.

**Phase 2C dimension (done):** measured the upright R3L footprint — the uncut edges already
render ~18.16 mm at the old 18.05 base param (corner geometry), so only the outer chamfer was
undersized. Applied a hybrid: eased the chamfer (`cut_distance` 4.9→**5.3** in `bed_cut`) and
widened the base (keyParameters `[0..1]` 18.05→**18.15** for rows keyID 0/1/15 and T1 thumb
keyID 2). Result: uncut edge **18.26 mm**, cut-axis widest **18.08 mm** (was 17.88) — axis
asymmetry down to 0.18 mm. Printed with raft + supports at slow speed, so the smaller bed face
is acceptable.

**Known gap:** the **side-column** keys (`R*-COL-*`, thumb profile keyID 0/1) are still
**Choc-sized 17.20×16.00**, not MX — they were never rescaled. If the Sofle uses them they need
an MX rescale (watch for the `DishShape2` shelf, like T1). Convex `R3x` (keyID 0/1) is a 1.5u/2u
special and left as-is.

## Orientation model: `orient()` / `bed_cut()` / `printable()`

The bed-adhesion cuts are **baked into the cap's native upright frame** so the cap you
inspect upright *is* the final printed geometry (the cut is part of the design, not bolted
on after tilting). Three modules in `CS/CS.scad`:

- `orient(other)` — the known-good print tilt (from commit `91be5bb`):
  `rotate([0,0,other?-45:135]) rotate([0,(other?1:-1)*45,0])`. 45° about Y onto its side,
  then spin flat onto the bed.
- `bed_cut(other)` — applies `orient()`, subtracts the two cut cubes in the print frame,
  then applies `orient⁻¹` so the cap returns upright **carrying** the angled flat print
  faces. Cut tools: `translate([0,0,-h/2-cut_distance]) cube([40,40,h])` and
  `rotate([0,90,-45]) translate(...) cube(...)`, with `h=5, cut_distance=4.9`.
- `printable(other)` — now **pure orientation**: `if (print) orient(other) children();
  else children();`.

Pipeline is `printable() bed_cut() CS(type)`.

**Render modes** (flag `print`, default true):
```bash
OPENSCAD=/Applications/OpenSCAD-2021.01.app/Contents/MacOS/OpenSCAD
# Design validation — cap upright, cuts baked in:
$OPENSCAD -o /tmp/R3.png --imgsize=800,800 --camera=0,0,0,62,0,25,95 -Dprint=false -Dkeycap=\"R3\" CS/CS.scad
# Print-ready STL — tilted onto the bed:
$OPENSCAD -q --render -Dprint=true -Dkeycap=\"R3\" -o things/CS-R3.stl CS/CS.scad
```
The `8e94c43` breakage and the `git show 91be5bb` temp-file workaround are **obsolete** —
the on-disk `CS/CS.scad` now renders correctly and matches the `91be5bb` print exactly
(verified: identical STL bounding box and vertex count).

**Open (Phase 2):** make the two cuts symmetric and size the post-cut footprint to the
intended oversized ~18.15 mm (caps are intentionally larger than standard MX for tighter
gaps). Base dim lives in the submodule profile `keyParameters[keyID][0..1]`.

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
