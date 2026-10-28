# Persiana tipo abrigo meteorologico (Stevenson) para el protector GLog 4G.
# Se atornilla a la placa existente, bajo el techo existente; deja ver nada del frente
# pero el aire circula por las lamas, el piso ranurado y la salida superior bajo el techo.
# Uso: blender -b -P persiana_v0_lamas.py
# Coordenadas = las del ensamble (mm): X ancho, Y alto, Z hacia afuera del muro (placa: z 0..4).
import bpy, bmesh, os, math
from mathutils import Vector, Matrix

BASE = os.path.dirname(os.path.abspath(__file__))
STL = os.path.join(BASE, "..", "Protector_GLog", "STL")
SAL = os.path.join(BASE, "..", "Persiana_GLog", "STL")
os.makedirs(SAL, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ---- parametros (mm) ----
X0, X1 = 7.0, 103.0          # ancho exterior (no tapa los agujeros de muro x 7-12 / 97-102 gracias a la muesca)
ZB, ZF = 4.0, 44.0           # desde la cara de la placa hasta el frente
Y0, Y1 = 38.0, 172.0         # piso (bajo la repisa, y=45) hasta bajo el techo (y>=175)
PROF = 7.0                   # profundidad de las lamas
PASO = 6.0                   # paso vertical entre lamas
ESP = 2.1                    # espesor vertical de cada lama (~1,5 mm perpendicular)
PISO = 2.0
POSTE = 2.0                  # montantes y marco
TAB_Y = (75.0, 120.0)        # orejas de fijacion (centro en Y)

piezas = []

def caja(x0, x1, y0, y1, z0, z1):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts:
        v.co = Vector((x0 if v.co.x < 0 else x1, y0 if v.co.y < 0 else y1, z0 if v.co.z < 0 else z1))
    piezas.append(bm)

def prisma(perfil, eje, a0, a1):
    """perfil: lista de puntos 2D en el plano perpendicular a 'eje'; se extruye de a0 a a1."""
    bm = bmesh.new()
    def p3(u, v, a):
        if eje == "x": return Vector((a, u, v))      # perfil en (y, z)
        if eje == "z": return Vector((u, v, a))      # perfil en (x, y)
    vs0 = [bm.verts.new(p3(u, v, a0)) for u, v in perfil]
    vs1 = [bm.verts.new(p3(u, v, a1)) for u, v in perfil]
    bm.faces.new(vs0[::-1]); bm.faces.new(vs1)
    n = len(perfil)
    for i in range(n):
        bm.faces.new((vs0[i], vs0[(i + 1) % n], vs1[(i + 1) % n], vs1[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    piezas.append(bm)

# ---- marco ----
caja(X0, X1, Y0, Y0 + PISO, ZB, ZF)                                  # piso
for (a, b) in ((X0, X0 + PROF), (X1 - PROF, X1)):
    caja(a, b, Y0, Y1, ZF - PROF, ZF)                                # montantes de esquina delanteros
    caja(a, b, Y0, Y1, ZB, ZB + 3)                                   # montantes traseros (apoyan en la placa)
    caja(a, b, Y1 - 3, Y1, ZB, ZF)                                   # marco superior lateral
    caja(a, b, Y0, Y1, (ZB + ZF) / 2 - POSTE / 2, (ZB + ZF) / 2 + POSTE / 2)  # montante intermedio lateral
caja(X0, X1, Y1 - 3, Y1, ZF - PROF, ZF)                              # marco superior frontal
for xm in (31.0, 55.0, 79.0):
    caja(xm - 0.8, xm + 0.8, Y0, Y1, ZF - PROF, ZF)                  # montantes intermedios del frente

# ---- lamas: bajan hacia afuera a 45 grados ----
y = Y0 + PISO
while y + PROF + ESP < Y1 - 3 + 0.01:
    # frente (perfil en y,z; se extiende en x)
    prisma([(y, ZF), (y + ESP, ZF), (y + PROF + ESP, ZF - PROF), (y + PROF, ZF - PROF)], "x", X0 + 1, X1 - 1)
    # costados (perfil en x,y; se extiende en z)
    prisma([(X0, y), (X0 + PROF, y + PROF), (X0 + PROF, y + PROF + ESP), (X0, y + ESP)], "z", ZB + 1, ZF - 1)
    prisma([(X1, y), (X1, y + ESP), (X1 - PROF, y + PROF + ESP), (X1 - PROF, y + PROF)], "z", ZB + 1, ZF - 1)
    y += PASO

# ---- orejas de fijacion (hacia afuera, apoyadas en la placa) ----
for yc in TAB_Y:
    caja(1.0, X0 + 1, yc - 7, yc + 7, ZB, ZB + 3)
    caja(X1 - 1, 109.0, yc - 7, yc + 7, ZB, ZB + 3)

# unir todo en un objeto
me = bpy.data.meshes.new("persiana"); bm = bmesh.new()
for p in piezas:
    tmp = bpy.data.meshes.new("t"); p.to_mesh(tmp); bm.from_mesh(tmp); bpy.data.meshes.remove(tmp); p.free()
bm.to_mesh(me); bm.free()
pers = bpy.data.objects.new("persiana", me); sc.collection.objects.link(pers)

# fusionar volumenes solapados (remesh por voxel = una sola malla estanca para el laminador)
rm = pers.modifiers.new("unir", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = 0.3; rm.adaptivity = 0
bpy.context.view_layer.objects.active = pers
bpy.ops.object.modifier_apply(modifier="unir")

# restas: agujeros de las orejas, ranuras del piso y muescas para las cabezas de los tornillos de muro
def restar(x0, x1, y0, y1, z0, z1, cil=None):
    if cil:
        bpy.ops.mesh.primitive_cylinder_add(radius=cil, depth=20, vertices=32, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    else:
        bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
        bpy.context.object.scale = (x1 - x0, y1 - y0, z1 - z0)
    c = bpy.context.object
    m = pers.modifiers.new("r", "BOOLEAN"); m.operation = "DIFFERENCE"; m.object = c; m.solver = "EXACT"
    bpy.context.view_layer.objects.active = pers
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(c)

for yc in TAB_Y:
    for xc in (4.0, 106.0):
        restar(xc, xc, yc, yc, 5, 5, cil=1.7)                         # paso para tornillo de 3 mm
for xs in (20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0):
    restar(xs - 2.5, xs + 2.5, Y0 - 1, Y0 + PISO + 1, ZB + 6, ZF - PROF - 2)   # ranuras de drenaje y entrada de aire
for (a, b) in ((X0 - 1, 14.5), (95.5, X1 + 1)):
    restar(a, b, 154, 171, ZB - 1, ZB + 9)                           # muesca: cabezas de tornillos de muro superiores

# ---- placa v2: 4 agujeros guia de 2,5 mm para las orejas ----
bpy.ops.wm.stl_import(filepath=os.path.join(STL, "1_placa.stl"))
placa = bpy.context.selected_objects[0]
for yc in TAB_Y:
    for xc in (4.0, 106.0):
        bpy.ops.mesh.primitive_cylinder_add(radius=1.25, depth=30, vertices=24, location=(xc, yc, 5))
        c = bpy.context.object
        m = placa.modifiers.new("r", "BOOLEAN"); m.operation = "DIFFERENCE"; m.object = c; m.solver = "EXACT"
        bpy.context.view_layer.objects.active = placa
        bpy.ops.object.modifier_apply(modifier=m.name)
        bpy.data.objects.remove(c)

def exportar(obj, nombre, rot=None):
    for o in sc.objects: o.select_set(False)
    obj.select_set(True); bpy.context.view_layer.objects.active = obj
    guard = obj.matrix_world.copy()
    if rot is not None:
        obj.matrix_world = rot @ obj.matrix_world
        bpy.context.view_layer.update()
        mn = min((obj.matrix_world @ v.co).z for v in obj.data.vertices)
        mx = min((obj.matrix_world @ v.co).x for v in obj.data.vertices)
        my = min((obj.matrix_world @ v.co).y for v in obj.data.vertices)
        obj.matrix_world = Matrix.Translation((-mx, -my, -mn)) @ obj.matrix_world
        bpy.context.view_layer.update()
    bpy.ops.wm.stl_export(filepath=os.path.join(SAL, nombre), export_selected_objects=True, apply_modifiers=True)
    obj.matrix_world = guard

# referencia de ensamble (coordenadas del ensamble) para renders
exportar(pers, "ref_persiana_v0_ensamble.stl")
# impresion: de pie, con el piso sobre la cama (Y del ensamble -> Z de impresion)
exportar(pers, "4_persiana_v0_lamas.stl", Matrix.Rotation(math.radians(90), 4, "X"))
exportar(placa, "1_placa_v2.stl")

d = pers.dimensions
print("PERSIANA dims mm", round(d.x, 1), round(d.y, 1), round(d.z, 1), "verts", len(pers.data.vertices))
bm = bmesh.new(); bm.from_mesh(pers.data)
print("PERSIANA volumen cm3", round(bm.calc_volume() / 1000, 1), "estanca", all(e.is_manifold for e in bm.edges))
bm.free()
