"""
ATCON v9 problem room, built in Blender.

Rebuilds the room the website draws (same size, layout, furniture and colours), lights it with real light (sun through
the window, a soft ceiling light, the cove strip and the floor lamp), bakes that light into textures with Cycles, and
exports public/v9/room.glb. The website loads that file and shows the baked room instead of lighting it live, which
looks more real and is much lighter to draw.

Run (Blender 3.6 or newer), from the repo root:
    blender --background --python blender/build_room.py
or open Blender, go to Scripting, open this file and press Run Script.

Also saves blender/room.blend so the room can be opened and edited by hand.

Coordinates: everything is placed in the website's three.js space (Y up, metres) under one root that is turned to
Blender's Z up, so the numbers here match the site's code one to one.
"""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix, Euler

# ---- settings --------------------------------------------------------------------------------------------------------
SAMPLES = 512          # bake quality: more is cleaner and slower (256 for a quick test)
TEX_SHELL = 4096       # floor, walls, beams, stairs
TEX_FURN = 4096        # furniture and the plant
TEX_FRONT = 2048       # the front wall that steps aside as the camera comes in
SUN_POWER = 3.2        # sun through the window
CEIL_POWER = 2600      # the soft ceiling light, in watts
SKY_POWER = 1.0        # sky light coming in through the window

HERE = os.path.dirname(os.path.abspath(bpy.data.filepath or __file__))
REPO = os.path.dirname(HERE) if os.path.basename(HERE) == 'blender' else HERE
OUT_GLB = os.path.join(REPO, 'public', 'v9', 'room.glb')
OUT_BLEND = os.path.join(REPO, 'blender', 'room.blend')
BAKE_DIR = os.path.join(REPO, 'blender', 'bake')
os.makedirs(BAKE_DIR, exist_ok=True)

# ---- a clean scene ---------------------------------------------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.engine = 'CYCLES'
cy = scn.cycles
cy.samples = SAMPLES
cy.max_bounces = 8; cy.diffuse_bounces = 6; cy.glossy_bounces = 2; cy.transmission_bounces = 2
cy.sample_clamp_indirect = 3.0
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for kind in ('OPTIX', 'CUDA', 'HIP', 'METAL', 'ONEAPI'):
        try:
            prefs.compute_device_type = kind; prefs.get_devices()
            if any(d.type != 'CPU' for d in prefs.devices):
                for d in prefs.devices: d.use = True
                cy.device = 'GPU'; break
        except Exception:
            pass
except Exception:
    pass
print('ATCON room: baking on', cy.device)

root = bpy.data.objects.new('ROOT', None); scn.collection.objects.link(root)
root.rotation_euler = (math.pi / 2, 0, 0)   # three.js Y up -> Blender Z up

# ---- materials -------------------------------------------------------------------------------------------------------
def hex_rgb(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c] + [1]

MATS = {}
def mat(hexc, rough=0.85, metal=0.0, emit=0.0, name=None):
    key = name or '%s_%.2f_%.2f_%.2f' % (hexc, rough, metal, emit)
    if key in MATS: return MATS[key]
    m = bpy.data.materials.new(key); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = hex_rgb(hexc)
    b.inputs['Roughness'].default_value = rough
    # metals bake as light grey: the bake keeps only light that bounces off evenly, which a pure metal has none of
    b.inputs['Metallic'].default_value = 0.0
    if emit > 0:
        ec = b.inputs.get('Emission Color') or b.inputs.get('Emission')
        ec.default_value = hex_rgb(hexc)
        b.inputs['Emission Strength'].default_value = emit
    m['hex'] = hexc
    MATS[key] = m
    return m

# ---- geometry, built directly in three.js space (Y up) ---------------------------------------------------------------
def finish(bm, name, m, group, x=0, y=0, z=0, rot=(0, 0, 0), parent=None, scale=(1, 1, 1)):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); scn.collection.objects.link(ob)
    ob.data.materials.append(m)
    ob.parent = parent or root
    ob.rotation_mode = 'ZYX'   # three.js 'XYZ' order
    ob.location = (x, y, z); ob.rotation_euler = rot; ob.scale = scale
    ob['group'] = group
    return ob

def g_box(w, h, d, r=None):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts: v.co = Vector((v.co.x * w, v.co.y * h, v.co.z * d))
    r = min(w, h, d) * 0.12 if r is None else r
    r = min(r, min(w, h, d) * 0.49)
    if r > 0.002:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=r, segments=3, profile=0.5, affect='EDGES', clamp_overlap=True)
    return bm

def g_plane(w, h):
    bm = bmesh.new()
    vs = [bm.verts.new((sx * w / 2, sy * h / 2, 0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    bm.faces.new(vs); return bm

def g_cyl(rt, rb, h, seg=32, open_end=False, t0=0.0, tl=math.pi * 2):
    bm = bmesh.new(); full = abs(tl - math.pi * 2) < 1e-6
    n = seg if full else seg + 1
    top, bot = [], []
    for i in range(n):
        t = t0 + tl * i / seg
        top.append(bm.verts.new((rt * math.sin(t), h / 2, rt * math.cos(t))))
        bot.append(bm.verts.new((rb * math.sin(t), -h / 2, rb * math.cos(t))))
    for i in range(seg):
        j = (i + 1) % n
        bm.faces.new((top[i], bot[i], bot[j], top[j]))
    if not open_end and full:
        bm.faces.new(list(reversed(top))); bm.faces.new(bot)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update(); return bm

def g_circle(r, seg=40):
    bm = bmesh.new()
    vs = [bm.verts.new((r * math.cos(i / seg * math.pi * 2), r * math.sin(i / seg * math.pi * 2), 0)) for i in range(seg)]
    bm.faces.new(vs); return bm

def g_sphere(r):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=10, radius=r); return bm

def bez(p0, p1, p2, p3, n):
    out = []
    for i in range(1, n + 1):
        t = i / n; a = (1 - t) ** 3; b = 3 * (1 - t) ** 2 * t; c = 3 * (1 - t) * t * t; d = t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out

def g_blade():
    # the snake-plant leaf outline from the site
    pts = [(-0.055, 0)] + bez((-0.055, 0), (-0.095, 0.42), (-0.065, 0.82), (0, 1), 9) + bez((0, 1), (0.065, 0.82), (0.095, 0.42), (0.055, 0), 9)
    bm = bmesh.new(); vs = [bm.verts.new((p[0], p[1], 0)) for p in reversed(pts[:-1])]
    f = bm.faces.new(vs); bmesh.ops.triangulate(bm, faces=[f]); return bm

def grp(x, z, ry=0.0, parent=None):
    e = bpy.data.objects.new('grp', None); scn.collection.objects.link(e)
    e.parent = parent or root; e.rotation_mode = 'ZYX'; e.location = (x, 0, z); e.rotation_euler = (0, ry, 0)
    return e

def plant(x, z, potR, potH, h, group, parent=None):
    finish(g_cyl(potR, potR * 0.82, potH, 48), 'pot', mat('#FFFFFF', 0.45), group, x, potH / 2, z, parent=parent)
    finish(g_cyl(potR * 0.92, potR * 0.92, 0.02, 40), 'soil', mat('#4A3B30', 1.0), group, x, potH - 0.03, z, parent=parent)
    g1, g2 = mat('#3E6B45', 0.55), mat('#5E8C55', 0.55)
    for b in range(16):
        ang = b * 2.399963; rr = potR * (0.12 + (b % 5) * 0.14)
        sc = h * (0.62 + ((b * 7) % 6) * 0.075)
        finish(g_blade(), 'blade', g1 if b % 3 else g2, group, x + math.cos(ang) * rr, potH - 0.02, z + math.sin(ang) * rr,
               rot=(math.sin(ang) * (0.08 + rr * 0.5), ang, -math.cos(ang) * (0.08 + rr * 0.5)), parent=parent, scale=(1 + (b % 2) * 0.25, sc, 1))

PI = math.pi
S, F, FR, E = 'shell', 'furn', 'front', 'emit'

# ---- the room: 20 wide, 7 high, 16 deep ------------------------------------------------------------------------------
wallM = mat('#D3DFF6', 0.9); floorM = mat('#BFD0EE', 0.42)
finish(g_plane(20, 16), 'floor', floorM, S, 0, 0, 0, rot=(-PI / 2, 0, 0))
# the ceiling stays pure white on the site; here it is a white surface for the light to bounce off
finish(g_plane(20, 16), 'ceiling', mat('#FFFFFF', 0.9, name='EMIT_FFFFFF'), E, 0, 7, 0, rot=(PI / 2, 0, 0))
dlx = -7.5
while dlx <= 7.51:
    dlz = -6.0
    while dlz <= 6.01:
        finish(g_circle(0.13), 'dl', mat('#EEF1F5', 0.5, name='EMIT_EEF1F5'), E, dlx, 6.985, dlz, rot=(PI / 2, 0, 0))
        finish(g_circle(0.115), 'dl', mat('#FFFFFF', 0.5, emit=4.0, name='EMIT_FFFFFF_dl'), E, dlx, 6.98, dlz, rot=(PI / 2, 0, 0))
        dlz += 3
    dlx += 3
finish(g_plane(20, 7), 'back wall', wallM, S, 0, 3.5, -8)
finish(g_plane(16, 7), 'right wall', wallM, S, 10, 3.5, 0, rot=(0, -PI / 2, 0))
# left wall around the window opening, with white mullions
for w, hh, zz, yy in ((16, 0.7, 0, 0.35), (16, 1.1, 0, 6.45), (1.5, 5.2, -7.25, 3.3), (1.5, 5.2, 6.75, 3.3)):
    finish(g_plane(w, hh), 'left wall', wallM, S, -10, yy, zz, rot=(0, PI / 2, 0))
frameM = mat('#FFFFFF', 0.4)
mz = -6.5
while mz <= 6.01: finish(g_box(0.12, 5.2, 0.12, 0.02), 'mullion', frameM, S, -9.95, 3.3, mz); mz += 1.3
my = 0.7
while my <= 5.91: finish(g_box(0.12, 0.12, 13, 0.02), 'transom', frameM, S, -9.95, my, -0.5); my += 1.3

# the front wall, its sideboard and two plants: one piece, so the site can move it aside as the camera comes in
front = bpy.data.objects.new('front_grp', None); scn.collection.objects.link(front); front.parent = root
finish(g_plane(20, 7), 'front wall', mat('#EEF2F9', 0.95), FR, 0, 3.5, 8, rot=(0, PI, 0), parent=front)
finish(g_box(6.4, 0.62, 0.55, 0.04), 'sideboard', mat('#FBFBFA', 0.45), FR, 0, 0.36, 7.6, parent=front)
finish(g_box(6.2, 0.04, 0.5, 0.01), 'sideboard top', mat('#E9ECF1', 0.6), FR, 0, 0.69, 7.6, parent=front)
plant(-4.6, 7.45, 0.34, 0.7, 1.15, FR, front); plant(4.6, 7.45, 0.34, 0.7, 0.9, FR, front)

# the coffered ceiling and the cove with its light strip
beamM = mat('#F8F9FC', 0.9)
for bz in (-7.5, -4.5, -1.5, 1.5, 4.5): finish(g_box(19.6, 0.14, 0.16, 0.02), 'beam', beamM, S, 0, 6.9, bz)
for bx in (-9, -6, -3, 0, 3, 6, 9): finish(g_box(0.16, 0.14, 15.2, 0.02), 'beam', beamM, S, bx, 6.9, 0)
bandM = mat('#F3F4F6', 0.8)
finish(g_box(19.6, 0.5, 0.9, 0.05), 'cove', bandM, S, 0, 6.75, -7.5)
finish(g_box(0.9, 0.5, 15.2, 0.05), 'cove', bandM, S, 9.5, 6.75, 0)
finish(g_box(0.9, 0.5, 15.2, 0.05), 'cove', bandM, S, -9.5, 6.75, 0)
stripM = mat('#FFFFFF', 0.5, emit=6.0, name='EMIT_FFFFFF_strip')
finish(g_box(19.4, 0.05, 0.08, 0), 'strip', stripM, E, 0, 6.48, -7.25)
finish(g_box(0.08, 0.05, 15, 0), 'strip', stripM, E, 9.25, 6.48, 0)

# ---- furniture -------------------------------------------------------------------------------------------------------
oakM = mat('#C9A57A', 0.5); metalM = mat('#C9CED6', 0.3); navyM = mat('#1A2C4A', 0.35)
def put(g, bm, m, x, y, z, rot=(0, 0, 0)): return finish(bm, 'part', m, F, x, y, z, rot=rot, parent=g)
# the woven round rug
finish(g_cyl(3.0, 3.0, 0.03, 96), 'rug', mat('#EEF3FC', 1.0), F, -0.6, 0.016, -2.4)
# the coffee table
ct = grp(-0.8, -2.4)
put(ct, g_box(2.3, 0.05, 1.05, 0.024), navyM, 0, 0.46, 0)
put(ct, g_box(2.1, 0.03, 0.9, 0.012), navyM, 0, 0.16, 0)
for lx, lz in ((-1.05, -0.45), (1.05, -0.45), (-1.05, 0.45), (1.05, 0.45)): put(ct, g_cyl(0.018, 0.018, 0.44, 16), metalM, lx, 0.22, lz)
put(ct, g_cyl(0.11, 0.1, 0.06, 32), mat('#FFFFFF', 0.4), 0.55, 0.52, 0.1)
put(ct, g_box(0.36, 0.05, 0.26, 0.01), mat('#2D63E6', 0.7), -0.5, 0.51, -0.1, rot=(0, 0.3, 0))
# the sofa against the back wall
sf = grp(-3.6, -6.4); green = mat('#3FB27E', 0.95); green2 = mat('#4BBE89', 0.95)
put(sf, g_box(4.6, 0.3, 1.35, 0.06), green, 0, 0.36, 0)
for lx, lz in ((-2.1, -0.55), (2.1, -0.55), (-2.1, 0.55), (2.1, 0.55), (-0.7, -0.55), (0.7, -0.55)): put(sf, g_cyl(0.03, 0.022, 0.22, 16), oakM, lx, 0.11, lz)
for cx in (-1.43, 0, 1.43):
    put(sf, g_box(1.4, 0.24, 1.02, 0.1), green2, cx, 0.63, 0.12)
    put(sf, g_box(1.4, 0.66, 0.3, 0.13), green2, cx, 1.02, -0.5, rot=(-0.12, 0, 0))
for ax in (-2.15, 2.15): put(sf, g_box(0.3, 0.62, 1.35, 0.13), green, ax, 0.66, 0)
put(sf, g_box(4.6, 0.7, 0.18, 0.08), green, 0, 0.82, -0.6)
put(sf, g_box(0.52, 0.5, 0.15, 0.08), mat('#1A2C4A', 0.95), -1.7, 0.98, -0.25, rot=(-0.25, 0.25, 0.08))
put(sf, g_box(0.48, 0.46, 0.14, 0.08), mat('#F4F6FA', 0.95), 1.75, 0.96, -0.25, rot=(-0.25, -0.3, -0.06))
# the armchair by the window
ac = grp(-6.2, -1.4, 0.6); blue = mat('#2D63E6', 0.95); blue2 = mat('#3A6EEA', 0.95)
put(ac, g_box(1.2, 0.26, 1.1, 0.06), blue, 0, 0.38, 0)
put(ac, g_box(0.92, 0.2, 0.86, 0.09), blue2, 0, 0.6, 0.05)
put(ac, g_box(1.2, 0.78, 0.26, 0.12), blue2, 0, 0.88, -0.44, rot=(-0.14, 0, 0))
for ax in (-0.53, 0.53): put(ac, g_box(0.16, 0.42, 1.06, 0.07), blue, ax, 0.62, 0)
for lx, lz in ((-0.48, -0.42), (0.48, -0.42), (-0.48, 0.42), (0.48, 0.42)): put(ac, g_cyl(0.025, 0.018, 0.26, 16), oakM, lx, 0.13, lz)
# the floor lamp
finish(g_cyl(0.16, 0.17, 0.03, 40), 'lamp base', navyM, F, -1.0, 0.015, -6.6)
finish(g_cyl(0.014, 0.014, 2.1, 12), 'lamp pole', navyM, F, -1.0, 1.06, -6.6)
finish(g_cyl(0.28, 0.32, 0.4, 48, open_end=True), 'lamp shade', mat('#F4F7FF', 0.5, emit=1.5, name='EMIT_F4F7FF'), E, -1.0, 2.2, -6.6)
plant(8.4, -6.8, 0.32, 0.55, 1.25, F)
# the desk, laptop and office chair
dk = grp(4.6, -5.9); deskM = mat('#FFFFFF', 0.35)
put(dk, g_box(3.2, 0.05, 1.05, 0.02), deskM, 0, 0.78, 0)
for lx in (-1.45, 1.45):
    put(dk, g_box(0.05, 0.74, 0.05, 0.012), deskM, lx, 0.37, -0.42); put(dk, g_box(0.05, 0.74, 0.05, 0.012), deskM, lx, 0.37, 0.42)
    put(dk, g_box(0.05, 0.04, 0.9, 0.012), deskM, lx, 0.02, 0); put(dk, g_box(0.05, 0.04, 0.9, 0.012), deskM, lx, 0.72, 0)
alu = mat('#C9CED6', 0.3)
put(dk, g_box(0.66, 0.018, 0.46, 0.008), alu, -0.2, 0.815, 0.05)
put(dk, g_box(0.66, 0.44, 0.012, 0.008), alu, -0.2, 1.03, -0.2, rot=(-0.22, 0, 0))
finish(g_plane(0.6, 0.38), 'screen', mat('#2D63E6', 0.25, emit=1.0, name='EMIT_2D63E6'), E, -0.2, 1.03, -0.192, rot=(-0.22, 0, 0), parent=dk)
put(dk, g_cyl(0.045, 0.04, 0.1, 32), mat('#FFFFFF', 0.4), 0.6, 0.86, -0.1)
oc = grp(4.5, -4.85, 0.2); ocM = mat('#1A2C4A', 0.9)
put(oc, g_box(0.56, 0.08, 0.54, 0.035), ocM, 0, 0.5, 0)
put(oc, g_cyl(0.32, 0.32, 0.5, 40, open_end=True, t0=PI * 0.68, tl=PI * 0.64), ocM, 0, 0.86, 0.1)
put(oc, g_cyl(0.025, 0.03, 0.34, 16), metalM, 0, 0.3, 0)
for s5 in range(5):
    a5 = s5 / 5 * PI * 2
    put(oc, g_box(0.32, 0.025, 0.045, 0.005), metalM, math.cos(a5) * 0.16, 0.08, math.sin(a5) * 0.16, rot=(0, -a5, 0))
    put(oc, g_sphere(0.028), navyM, math.cos(a5) * 0.32, 0.03, math.sin(a5) * 0.32)
# the stairs along the right wall
stepM = mat('#E6EEFB', 0.6)
for st in range(9):
    hh = 0.4 + st * 0.38
    finish(g_box(1.7, hh, 0.6, 0.03), 'step', stepM, S, 9.1, hh / 2, 3.6 - st * 0.6)

# ---- light -----------------------------------------------------------------------------------------------------------
world = bpy.data.worlds.new('sky'); scn.world = world; world.use_nodes = True
bg = world.node_tree.nodes['Background']; bg.inputs[0].default_value = hex_rgb('#EAF1FF'); bg.inputs[1].default_value = SKY_POWER

def light(kind, name, x, y, z, color, power, rot=None, **kw):
    ld = bpy.data.lights.new(name, kind); ld.color = hex_rgb(color)[:3]; ld.energy = power
    for k, v in kw.items(): setattr(ld, k, v)
    ob = bpy.data.objects.new(name, ld); scn.collection.objects.link(ob); ob.parent = root; ob.location = (x, y, z)
    if rot is not None:
        ob.rotation_mode = 'QUATERNION'; ob.rotation_quaternion = rot
    return ob

# sun through the window, from the site's sun position toward its target
sd = (Vector((0, 0, -2)) - Vector((-16, 9, 2))).normalized()
light('SUN', 'sun', -16, 9, 2, '#FFE9C8', SUN_POWER, rot=sd.to_track_quat('-Z', 'Y'), angle=math.radians(4))
# the soft ceiling light over the middle of the room, facing down
light('AREA', 'ceiling light', 0.5, 6.6, -0.5, '#F2F6FF', CEIL_POWER, rot=Euler((-PI / 2, 0, 0)).to_quaternion(), shape='RECTANGLE', size=15, size_y=11)
# the warm floor lamp
light('POINT', 'lamp', -1.0, 2.1, -6.3, '#FFE7C2', 60, shadow_soft_size=0.2)
# the sky behind the window, a soft glowing plane
finish(g_plane(13, 5.2), 'sky', mat('#E3ECFB', 1.0, emit=1.4, name='SKY'), 'sky', -10.6, 3.3, -0.5, rot=(0, PI / 2, 0))

bpy.context.view_layer.update()

# ---- flatten: every part in world space, joined per group ------------------------------------------------------------
meshes = [o for o in scn.objects if o.type == 'MESH']
for o in meshes:
    mw = o.matrix_world.copy(); o.parent = None; o.data.transform(mw); o.matrix_world = Matrix.Identity(4)

def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active; ob.name = name; ob.data.name = name
    return ob

groups = {}
for o in meshes: groups.setdefault(o['group'], []).append(o)
baked = {S: join(groups[S], 'Shell'), F: join(groups[F], 'Furniture'), FR: join(groups[FR], 'FrontWallMesh')}
# lit pieces: one mesh per colour, kept unbaked (the site shows them as plain light)
emit_objs = []
by_mat = {}
for o in groups[E]: by_mat.setdefault(o.data.materials[0].name, []).append(o)
for mname, objs in by_mat.items(): emit_objs.append(join(objs, mname))
sky_ob = groups['sky'][0]

# ---- bake ------------------------------------------------------------------------------------------------------------
def lightmap_uv(ob):
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    while ob.data.uv_layers: ob.data.uv_layers.remove(ob.data.uv_layers[0])
    ob.data.uv_layers.new(name='bake')
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003, area_weight=1.0, scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT')

scn.render.bake.margin = 16
scn.render.bake.use_pass_direct = True; scn.render.bake.use_pass_indirect = True; scn.render.bake.use_pass_color = True
for key, size in ((S, TEX_SHELL), (F, TEX_FURN), (FR, TEX_FRONT)):
    ob = baked[key]; lightmap_uv(ob)
    img = bpy.data.images.new('bake_' + ob.name, size, size, alpha=False, float_buffer=False)
    for m in ob.data.materials:
        nt = m.node_tree; n = nt.nodes.get('BAKE') or nt.nodes.new('ShaderNodeTexImage'); n.name = 'BAKE'
        n.image = img; nt.nodes.active = n
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    print('ATCON room: baking', ob.name, size, 'px ...')
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'DIRECT', 'INDIRECT', 'COLOR'}, margin=16, use_clear=True)
    img.filepath_raw = os.path.join(BAKE_DIR, ob.name + '.png'); img.file_format = 'PNG'; img.save()
    # the exported surface: just the baked picture
    out = bpy.data.materials.new('BAKED_' + ob.name); out.use_nodes = True
    b = out.node_tree.nodes['Principled BSDF']; t = out.node_tree.nodes.new('ShaderNodeTexImage'); t.image = img
    out.node_tree.links.new(t.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 1
    ob.data.materials.clear(); ob.data.materials.append(out)

# the front wall keeps its own node so the site can move it as one piece
fw = bpy.data.objects.new('FrontWall', None); scn.collection.objects.link(fw)
baked[FR].parent = fw

bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)

# ---- export ----------------------------------------------------------------------------------------------------------
bpy.data.objects.remove(sky_ob)   # the site draws its own sky
for o in list(scn.objects):
    if o.type in ('LIGHT', 'EMPTY') and o.name != 'FrontWall': bpy.data.objects.remove(o)
kw = dict(filepath=OUT_GLB, export_format='GLB', export_yup=True, export_apply=True, export_lights=False,
          export_cameras=False, export_texcoords=True, export_normals=False, export_image_format='JPEG')
try:
    bpy.ops.export_scene.gltf(export_image_quality=90, **kw)
except TypeError:
    bpy.ops.export_scene.gltf(export_jpeg_quality=90, **kw)
print('ATCON room: saved', OUT_GLB, round(os.path.getsize(OUT_GLB) / 1e6, 1), 'MB')
