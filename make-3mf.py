#!/usr/bin/env python3
"""
Generate a 3MF file (or pair of files) for the full Sofle v2 keycap set.

Sofle v2 counts (both halves, 58 keys total):
  R1:        12  (number row, 6 per half)
  R2:        12
  R3:        10  (5 per half; homing key is separate)
  R3-homing:  2  (1 per half, F and J keys)
  R4:        12
  T1L:        3  (left half only, 3 standard thumb keys)
  T1L-trap:   2  (left half only, 2 angled outer thumb keys)
  T1R:        3  (right half only)
  T1R-trap:   2  (right half only)

Build plate: Bambu A1 Mini = 180x180mm
"""

import struct
import zipfile
import math
import os
import sys
from io import BytesIO

REPO = os.path.dirname(os.path.abspath(__file__))
THINGS = os.path.join(REPO, "things")
BUILD_W  = 179.0
BUILD_H  = 179.0
MARGIN   = 4.0   # mm from plate edge
COL_GAP  = 5.0   # mm between keycaps in a row — max for 9×14mm in 179mm: (179-126-8)/8=5.6
ROW_GAP  = 7.0   # mm between rows (more room for brim + support clearance)
GAP      = COL_GAP  # alias used by generic packing code

FULL_SET = [
    ("CS-R1",        12),  # rows 1-2
    ("CS-R2",        12),  # rows 3-4
    ("CS-R3",        10),  # rows 5-6 (R3-homing fills end of row 6)
    ("CS-R3-homing",  2),  # end of row 6
    ("CS-R4",        12),  # rows 7-8
    ("CS-T1L",        3),  # left thumb standard
    ("CS-T1L-trap",   2),  # left thumb trapezoidal
    ("CS-T1R",        3),  # right thumb standard
    ("CS-T1R-trap",   2),  # right thumb trapezoidal
]

FULL_SET_NOTRAP = [
    ("CS-R1",        12),
    ("CS-R2",        12),
    ("CS-R3",        10),
    ("CS-R3-homing",  2),
    ("CS-R4",        12),
    ("CS-T1L",        5),
    ("CS-T1R",        5),
]

LEFT_SET = [
    ("CS-R1",        6),
    ("CS-R2",        6),
    ("CS-R3",        5),
    ("CS-R3-homing", 1),
    ("CS-R4",        6),
    ("CS-T1L",       3),
    ("CS-T1L-trap",  2),
]

RIGHT_SET = [
    ("CS-R1",        6),
    ("CS-R2",        6),
    ("CS-R3",        5),
    ("CS-R3-homing", 1),
    ("CS-R4",        6),
    ("CS-T1R",       3),
    ("CS-T1R-trap",  2),
]

LEFT_SET_NOTRAP = [
    ("CS-R1",        6),
    ("CS-R2",        6),
    ("CS-R3",        5),
    ("CS-R3-homing", 1),
    ("CS-R4",        6),
    ("CS-T1L",       5),
]

RIGHT_SET_NOTRAP = [
    ("CS-R1",        6),
    ("CS-R2",        6),
    ("CS-R3",        5),
    ("CS-R3-homing", 1),
    ("CS-R4",        6),
    ("CS-T1R",       5),
]


def read_stl(path):
    """Return list of triangles as flat float list, and bounding box.
    Handles both binary and ASCII STL."""
    with open(path, "rb") as f:
        header = f.read(5)
    if header == b"solid":
        return _read_stl_ascii(path)
    else:
        return _read_stl_binary(path)


def _read_stl_binary(path):
    with open(path, "rb") as f:
        f.read(80)
        count = struct.unpack("<I", f.read(4))[0]
        triangles = []
        xs, ys, zs = [], [], []
        for _ in range(count):
            f.read(12)
            verts = struct.unpack("<9f", f.read(36))
            f.read(2)
            triangles.extend(verts)
            for i in range(3):
                xs.append(verts[i*3])
                ys.append(verts[i*3+1])
                zs.append(verts[i*3+2])
    return triangles, (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def _read_stl_ascii(path):
    import re
    triangles = []
    xs, ys, zs = [], [], []
    vertex_re = re.compile(r'vertex\s+([\d.eE+\-]+)\s+([\d.eE+\-]+)\s+([\d.eE+\-]+)')
    with open(path, "r") as f:
        verts_in_tri = []
        for line in f:
            m = vertex_re.search(line)
            if m:
                v = (float(m.group(1)), float(m.group(2)), float(m.group(3)))
                verts_in_tri.append(v)
                xs.append(v[0]); ys.append(v[1]); zs.append(v[2])
                if len(verts_in_tri) == 3:
                    for vv in verts_in_tri:
                        triangles.extend(vv)
                    verts_in_tri = []
    return triangles, (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def stl_to_mesh_xml(triangles, object_id):
    """Convert flat triangle list to 3MF mesh XML string."""
    # Deduplicate vertices
    vmap = {}
    verts = []
    tris  = []
    for i in range(0, len(triangles), 9):
        tri = []
        for j in range(3):
            v = (triangles[i+j*3], triangles[i+j*3+1], triangles[i+j*3+2])
            # round to avoid floating-point duplicates
            vk = (round(v[0],6), round(v[1],6), round(v[2],6))
            if vk not in vmap:
                vmap[vk] = len(verts)
                verts.append(vk)
            tri.append(vmap[vk])
        tris.append(tri)

    vlines = "\n".join(
        f'          <vertex x="{v[0]}" y="{v[1]}" z="{v[2]}" />' for v in verts
    )
    tlines = "\n".join(
        f'          <triangle v1="{t[0]}" v2="{t[1]}" v3="{t[2]}" />' for t in tris
    )
    return f"""      <object id="{object_id}" type="model">
        <mesh>
          <vertices>
{vlines}
          </vertices>
          <triangles>
{tlines}
          </triangles>
        </mesh>
      </object>"""


MAX_ROW      = 6    # used by generic packing only
PROFILE_GAP  = 2.0  # extra mm added between different profile types (total col gap = COL_GAP + PROFILE_GAP)

# Fixed layout: each row is a list of (profile, count) segments, all 58 keys grouped by type.
ROWS = [
    [("CS-R1", 10)],
    [("CS-R1", 2), ("CS-R2", 8)],
    [("CS-R2", 4), ("CS-R3", 6)],
    [("CS-R3", 4), ("CS-R3-homing", 2), ("CS-R4", 4)],
    [("CS-R4", 8), ("CS-T1L", 2)],
    [("CS-T1L", 1), ("CS-T1L-trap", 2), ("CS-T1R", 3), ("CS-T1R-trap", 2)],
]
EXTRAS = []

# Tight layout: 1.5mm gaps, 10 keys/row — fits all 58 keys on a single 179mm plate.
# For use when merging all objects into one with a unified raft.
TIGHT_COL_GAP     = 1.5
TIGHT_ROW_GAP     = 2.0
TIGHT_PROFILE_GAP = 2.0
TIGHT_MAX_ROW     = 11

TIGHT_ROWS = [
    [("CS-R1", 10)],
    [("CS-R1", 2), ("CS-R2", 8)],
    [("CS-R2", 4), ("CS-R3", 6)],
    [("CS-R3", 4), ("CS-R3-homing", 2), ("CS-R4", 4)],
    [("CS-R4", 8), ("CS-T1L", 2)],
    [("CS-T1L", 1), ("CS-T1L-trap", 2), ("CS-T1R", 3), ("CS-T1R-trap", 2)],
]


def pack_items(items, plate_w, plate_h, margin, max_row=None, gap=None):
    """
    Greedy row-packing of (name, dx, dy, ox, oy) items.
    Caps each row at max_row items to keep raft sections short.
    Returns list of (name, cx, cy) placed center positions, or None if overflow.
    """
    if max_row is None:
        max_row = MAX_ROW
    if gap is None:
        gap = GAP
    placed = []
    x = margin
    y = margin
    row_h = 0.0
    row_count = 0

    for name, dx, dy, ox, oy in items:
        if x + dx > plate_w - margin or row_count >= max_row:
            x = margin
            y += row_h + gap
            row_h = 0.0
            row_count = 0
        if y + dy > plate_h - margin:
            return None  # doesn't fit
        cx = x + ox
        cy = y + oy
        placed.append((name, cx, cy))
        x += dx + gap
        row_h = max(row_h, dy)
        row_count += 1

    return placed


def make_3mf(filename, keycap_set, stl_data, max_row=None, gap=None, flip_alternate=False):
    """
    keycap_set: list of (profile_name, count)
    stl_data:   dict profile_name -> (triangles, bbox)
    """
    # Build flat item list: one entry per keycap instance
    flat_items = []  # (profile_name, dx, dy, ox, oy)
    for profile, count in keycap_set:
        tris, (xmin, ymin, zmin, xmax, ymax, zmax) = stl_data[profile]
        dx = xmax - xmin
        dy = ymax - ymin
        ox = -xmin  # offset so bbox-min -> 0
        oy = -ymin
        for _ in range(count):
            flat_items.append((profile, dx, dy, ox, oy))

    placed = pack_items(flat_items, BUILD_W, BUILD_H, MARGIN, max_row=max_row, gap=gap)
    if placed is None:
        return False  # doesn't fit

    # Build 3MF XML
    # Object IDs: one per profile (not per instance)
    profile_ids = {}
    obj_id = 1
    for profile, _ in keycap_set:
        if profile not in profile_ids:
            profile_ids[profile] = obj_id
            obj_id += 1

    # Mesh objects
    mesh_xml_parts = []
    for profile, pid in profile_ids.items():
        tris, (xmin, ymin, zmin, xmax, ymax, zmax) = stl_data[profile]
        mesh_xml_parts.append(stl_to_mesh_xml(tris, pid))

    # Build items — each instance references a component object
    # Use a wrapper object per instance for placement transform
    component_xml_parts = []
    item_xml_parts = []

    inst_id = obj_id
    placed_idx = 0
    for profile, count in keycap_set:
        tris, (xmin, ymin, zmin, xmax, ymax, zmax) = stl_data[profile]
        pid = profile_ids[profile]
        zoff = -zmin  # lift to z=0

        for i in range(count):
            name, cx, cy = placed[placed_idx]
            placed_idx += 1

            # cx = x_plate_left + (-xmin), so x_plate_left = cx + xmin
            # vertex (vx,vy,vz) → world (vx + cx, vy + cy, vz + zoff)
            flipped = flip_alternate and (i % 2 == 1)
            if flipped:
                # 180° Z rotation: vertex (-vx,-vy,vz) + (tx,ty,tz)
                # want left edge at x_plate_left = cx + xmin:  -xmax + tx = cx+xmin → tx = cx+xmin+xmax
                tx = cx + xmin + xmax
                ty = cy + ymin + ymax
                transform = f"-1 0 0 0 -1 0 0 0 1 {tx:.4f} {ty:.4f} {zoff:.4f}"
            else:
                transform = f"1 0 0 0 1 0 0 0 1 {cx:.4f} {cy:.4f} {zoff:.4f}"

            component_xml_parts.append(
                f'      <object id="{inst_id}" type="model">\n'
                f'        <components>\n'
                f'          <component objectid="{pid}" transform="{transform}" />\n'
                f'        </components>\n'
                f'      </object>'
            )
            item_xml_parts.append(f'      <item objectid="{inst_id}" />')
            inst_id += 1

    objects_xml = "\n".join(mesh_xml_parts) + "\n" + "\n".join(component_xml_parts)
    items_xml   = "\n".join(item_xml_parts)

    model_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US"
    xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06">
  <resources>
{objects_xml}
  </resources>
  <build>
{items_xml}
  </build>
</model>"""

    rels_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
                Target="/3D/3dmodel.model" Id="rel0" />
</Relationships>"""

    content_types_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml" />
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml" />
</Types>"""

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml)
        zf.writestr("_rels/.rels", rels_xml)
        zf.writestr("3D/3dmodel.model", model_xml)

    out_path = os.path.join(THINGS, filename)
    with open(out_path, "wb") as f:
        f.write(buf.getvalue())
    print(f"Written: {out_path}")
    return True


def make_3mf_stacked(filename, keycap_set, stl_data):
    """Generate a 3MF with all objects at the origin — import into Bambu Studio and auto-arrange."""
    profile_ids = {}
    obj_id = 1
    for profile, _ in keycap_set:
        if profile not in profile_ids:
            profile_ids[profile] = obj_id
            obj_id += 1

    mesh_xml_parts = []
    for profile, pid in profile_ids.items():
        tris, (xmin, ymin, zmin, xmax, ymax, zmax) = stl_data[profile]
        mesh_xml_parts.append(stl_to_mesh_xml(tris, pid))

    component_xml_parts = []
    item_xml_parts = []
    inst_id = obj_id
    col_pitch = 30.0  # spread out enough for Bambu Studio to see separate objects
    cols = 10
    idx = 0
    for profile, count in keycap_set:
        tris, (xmin, ymin, zmin, xmax, ymax, zmax) = stl_data[profile]
        pid = profile_ids[profile]
        zoff = -zmin
        for _ in range(count):
            tx = (idx % cols) * col_pitch
            ty = (idx // cols) * col_pitch
            transform = f"1 0 0 0 1 0 0 0 1 {tx:.4f} {ty:.4f} {zoff:.4f}"
            component_xml_parts.append(
                f'      <object id="{inst_id}" type="model">\n'
                f'        <components>\n'
                f'          <component objectid="{pid}" transform="{transform}" />\n'
                f'        </components>\n'
                f'      </object>'
            )
            item_xml_parts.append(f'      <item objectid="{inst_id}" />')
            inst_id += 1
            idx += 1

    objects_xml = "\n".join(mesh_xml_parts) + "\n" + "\n".join(component_xml_parts)
    items_xml   = "\n".join(item_xml_parts)

    model_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US"
    xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <resources>
{objects_xml}
  </resources>
  <build>
{items_xml}
  </build>
</model>"""

    rels_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
                Target="/3D/3dmodel.model" Id="rel0" />
</Relationships>"""

    content_types_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml" />
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml" />
</Types>"""

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml)
        zf.writestr("_rels/.rels", rels_xml)
        zf.writestr("3D/3dmodel.model", model_xml)

    out_path = os.path.join(THINGS, filename)
    with open(out_path, "wb") as f:
        f.write(buf.getvalue())
    print(f"Written: {out_path}")


def make_3mf_layout(filename, rows, extras, stl_data, col_gap=None, row_gap=None, profile_gap=None, flip_alternate=False):
    """Generate a 3MF using an explicit row layout with profile-aware gaps."""
    if col_gap is None:
        col_gap = COL_GAP
    if row_gap is None:
        row_gap = ROW_GAP
    if profile_gap is None:
        profile_gap = PROFILE_GAP
    all_profiles = set()
    for row in rows:
        for p, _ in row:
            all_profiles.add(p)
    for p, _ in extras:
        all_profiles.add(p)

    profile_ids = {}
    obj_id = 1
    for p in sorted(all_profiles):
        profile_ids[p] = obj_id
        obj_id += 1

    mesh_xml_parts = [stl_to_mesh_xml(stl_data[p][0], pid)
                      for p, pid in profile_ids.items()]

    component_xml_parts = []
    item_xml_parts = []
    inst_id = obj_id

    y = MARGIN
    max_y = MARGIN

    def place_segment(profile, count, start_x, cur_y):
        nonlocal inst_id
        tris, (xmin, ymin, zmin, xmax, ymax, zmax) = stl_data[profile]
        pid = profile_ids[profile]
        dx, dy = xmax - xmin, ymax - ymin
        ox, oy, zoff = -xmin, -ymin, -zmin
        x = start_x
        for i in range(count):
            flipped = flip_alternate and (i % 2 == 1)
            if flipped:
                tx = x + xmax
                ty = cur_y + ymax
                transform = f"-1 0 0 0 -1 0 0 0 1 {tx:.4f} {ty:.4f} {zoff:.4f}"
            else:
                cx, cy = x + ox, cur_y + oy
                transform = f"1 0 0 0 1 0 0 0 1 {cx:.4f} {cy:.4f} {zoff:.4f}"
            component_xml_parts.append(
                f'      <object id="{inst_id}" type="model">\n'
                f'        <components>\n'
                f'          <component objectid="{pid}" transform="{transform}" />\n'
                f'        </components>\n'
                f'      </object>'
            )
            item_xml_parts.append(f'      <item objectid="{inst_id}" />')
            inst_id += 1
            x += dx + col_gap
        return x, dy  # return next x and row height contribution

    for row_segments in rows:
        x = MARGIN
        row_h = 0.0
        prev_profile = None
        for profile, count in row_segments:
            if prev_profile is not None and profile != prev_profile:
                x += profile_gap  # extra gap between profile types
            next_x, seg_h = place_segment(profile, count, x, y)
            _, bbox = stl_data[profile]
            row_h = max(row_h, bbox[4] - bbox[1])
            x = next_x
            prev_profile = profile
        y += row_h + row_gap
        max_y = max(max_y, y)

    # Place extras with a modest separator gap
    if extras:
        y += 4  # visual separator from main grid
        x = MARGIN
        for profile, count in extras:
            next_x, _ = place_segment(profile, count, x, y)
            x = next_x + profile_gap  # wider gap between reference keys

    objects_xml = "\n".join(mesh_xml_parts) + "\n" + "\n".join(component_xml_parts)
    items_xml   = "\n".join(item_xml_parts)

    model_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US"
    xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <resources>
{objects_xml}
  </resources>
  <build>
{items_xml}
  </build>
</model>"""

    rels_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
                Target="/3D/3dmodel.model" Id="rel0" />
</Relationships>"""

    content_types_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml" />
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml" />
</Types>"""

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml)
        zf.writestr("_rels/.rels", rels_xml)
        zf.writestr("3D/3dmodel.model", model_xml)

    out_path = os.path.join(THINGS, filename)
    with open(out_path, "wb") as f:
        f.write(buf.getvalue())
    print(f"Written: {out_path}")


def main():
    # Load all needed STLs
    needed = set(p for p, _ in FULL_SET)
    for p, _ in FULL_SET_NOTRAP:
        needed.add(p)
    for row in ROWS:
        for p, _ in row:
            needed.add(p)
    for p, _ in EXTRAS:
        needed.add(p)
    for s in (LEFT_SET, RIGHT_SET, LEFT_SET_NOTRAP, RIGHT_SET_NOTRAP):
        for p, _ in s:
            needed.add(p)
    stl_data = {}
    missing = []
    for profile in needed:
        path = os.path.join(THINGS, profile + ".stl")
        if not os.path.exists(path):
            missing.append(path)
        else:
            print(f"Loading {profile}.stl ...", end=" ", flush=True)
            stl_data[profile] = read_stl(path)
            _, bbox = stl_data[profile]
            dx = bbox[3] - bbox[0]
            dy = bbox[4] - bbox[1]
            dz = bbox[5] - bbox[2]
            print(f"bbox {dx:.1f} x {dy:.1f} x {dz:.1f} mm")

    # Fall back to T1L/T1R if trap variants not yet rendered
    fallbacks = {"CS-T1L-trap": "CS-T1L", "CS-T1R-trap": "CS-T1R"}
    for m in missing[:]:
        profile = os.path.splitext(os.path.basename(m))[0]
        if profile in fallbacks:
            fb = fallbacks[profile]
            print(f"  {profile}.stl not ready — using {fb} as placeholder")
            stl_data[profile] = stl_data[fb]
            missing.remove(m)

    if missing:
        print("\nMissing STL files (no fallback):")
        for m in missing:
            print(f"  {m}")
        sys.exit(1)

    print("\nGenerating sofle-keycaps.3mf (6×10 layout, all 58 keys grouped by profile)...")
    make_3mf_layout("sofle-keycaps.3mf", ROWS, EXTRAS, stl_data)

    print("Generating sofle-left.3mf ...")
    make_3mf("sofle-left.3mf", LEFT_SET, stl_data)

    print("Generating sofle-right.3mf ...")
    make_3mf("sofle-right.3mf", RIGHT_SET, stl_data)

    print("Generating sofle-left-notrap.3mf ...")
    make_3mf("sofle-left-notrap.3mf", LEFT_SET_NOTRAP, stl_data)

    print("Generating sofle-right-notrap.3mf ...")
    make_3mf("sofle-right-notrap.3mf", RIGHT_SET_NOTRAP, stl_data)

    print("Generating sofle-all.3mf (stacked for auto-arrange)...")
    make_3mf_stacked("sofle-all.3mf", FULL_SET, stl_data)

    print("Generating sofle-all-notrap.3mf (stacked for auto-arrange)...")
    make_3mf_stacked("sofle-all-notrap.3mf", FULL_SET, stl_data)

    print("\nGenerating tight-packed versions (1.5mm gap, 11/row — merge into one object + unified raft)...")
    print("Generating sofle-keycaps-tight.3mf ...")
    make_3mf_layout("sofle-keycaps-tight.3mf", TIGHT_ROWS, EXTRAS, stl_data,
                    col_gap=TIGHT_COL_GAP, row_gap=TIGHT_ROW_GAP, profile_gap=TIGHT_PROFILE_GAP)
    print("Generating sofle-left-tight.3mf ...")
    make_3mf("sofle-left-tight.3mf", LEFT_SET, stl_data, max_row=TIGHT_MAX_ROW, gap=TIGHT_COL_GAP)
    print("Generating sofle-right-tight.3mf ...")
    make_3mf("sofle-right-tight.3mf", RIGHT_SET, stl_data, max_row=TIGHT_MAX_ROW, gap=TIGHT_COL_GAP)

    B2B_GAP = 4.5  # stem ends need more clearance than plain tight packing
    print("\nGenerating back-to-back versions (alternating keys flipped 180°, prongs facing each other)...")
    print("Generating sofle-keycaps-b2b.3mf ...")
    make_3mf_layout("sofle-keycaps-b2b.3mf", TIGHT_ROWS, EXTRAS, stl_data,
                    col_gap=B2B_GAP, row_gap=TIGHT_ROW_GAP, profile_gap=TIGHT_PROFILE_GAP,
                    flip_alternate=True)
    print("Generating sofle-left-b2b.3mf ...")
    make_3mf("sofle-left-b2b.3mf", LEFT_SET, stl_data, max_row=TIGHT_MAX_ROW, gap=B2B_GAP, flip_alternate=True)
    print("Generating sofle-right-b2b.3mf ...")
    make_3mf("sofle-right-b2b.3mf", RIGHT_SET, stl_data, max_row=TIGHT_MAX_ROW, gap=B2B_GAP, flip_alternate=True)


if __name__ == "__main__":
    main()
