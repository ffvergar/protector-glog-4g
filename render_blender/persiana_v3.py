# Persiana v3: lamas HORIZONTALES a 45 grados (tipo abrigo Stevenson), impresa de pie sin soportes.
# Reemplaza a v1/v2 (aletas verticales de 130 mm que vibraban al imprimir).
# Se atornilla a la placa existente, bajo el techo existente; deja ver nada del frente
# pero el aire circula por las lamas, el piso ranurado y la salida superior bajo el techo.
# Uso: blender -b -P persiana_vN.py   (la version sale del nombre del archivo)
# Coordenadas = las del ensamble (mm): X ancho, Y alto, Z hacia afuera del muro (placa: z 0..4).
import bpy, bmesh, os, math
from mathutils import Vector, Matrix

BASE = os.path.dirname(os.path.abspath(__file__))
STL = os.path.join(BASE, "..", "Protector_GLog", "STL")
SAL = os.path.join(BASE, "..", "Persiana_GLog", "STL")
VER = os.path.splitext(os.path.basename(__file__))[0].split("_")[-1]   # "v1", "v2"...
os.makedirs(SAL, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ---- parametros (mm) ----
X0, X1 = 7.0, 103.0          # ancho exterior (no tapa los agujeros de muro x 7-12 / 97-102 gracias a la muesca)
ZB, ZF = 4.0, 44.0           # desde la cara de la placa hasta el frente
Y0, Y1 = 38.0, 172.0         # piso (bajo la repisa, y=45) hasta bajo el techo (y>=175)
PROF = 7.0                   # profundidad de las lamas
PASO = 6.0                   # paso vertical entre lamas
ESP = 1.8                    # espesor de cada lama medido en la capa = 4 lineas de 0,45 (~1,3 mm perpendicular)
PISO = 2.0
MONT = 1.8                   # ancho de montantes intermedios (4 lineas)
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

# ---- marco: piso, esquinas, montantes y aro superior ----
caja(X0, X1, Y0, Y0 + PISO, ZB, ZF)                                  # piso (va sobre la cama)
for (a_, b_) in ((X0, X0 + PROF), (X1 - PROF, X1)):
    caja(a_, b_, Y0, Y1, ZF - PROF, ZF)                              # esquinas delanteras macizas
    caja(a_, b_, Y0, Y1, ZB, ZB + 3.5)                               # montantes traseros (apoyan en la placa)
    caja(a_, b_, Y1 - 3, Y1, ZB, ZF)                                 # aro superior lateral
    caja(a_, b_, Y0, Y1, (ZB + ZF) / 2 - MONT / 2, (ZB + ZF) / 2 + MONT / 2)   # montante intermedio lateral
caja(X0, X1, Y1 - 3, Y1, ZF - PROF, ZF)                              # aro superior frontal
for xm in (31.0, 55.0, 79.0):
    caja(xm - MONT / 2, xm + MONT / 2, Y0, Y1, ZF - PROF, ZF)        # montantes intermedios del frente (puentes de ~22 mm)

# ---- lamas horizontales: suben hacia adentro a 45 grados ----
# Impresa de pie: cada lama crece a 45 grados desde la cara exterior (sin soportes) y su borde
# inferior solo puentea ~22 mm entre montantes. Lamas cada 6 mm amarran todo el marco: no hay
# elementos altos y sueltos que vibren. Con PROF 7 > PASO 6 no se ve (ni entra agua) en horizontal.
y = Y0 + PISO
while y + PROF + ESP < Y1 - 3 + 0.01:
    prisma([(y, ZF), (y + ESP, ZF), (y + PROF + ESP, ZF - PROF), (y + PROF, ZF - PROF)], "x", X0 + 1, X1 - 1)
    prisma([(X0, y), (X0 + PROF, y + PROF), (X0 + PROF, y + PROF + ESP), (X0, y + ESP)], "z", ZB + 1, ZF - 1)
    prisma([(X1, y), (X1, y + ESP), (X1 - PROF, y + PROF + ESP), (X1 - PROF, y + PROF)], "z", ZB + 1, ZF - 1)
    y += PASO

# ---- orejas de fijacion con chanfle de 45 grados por debajo (sin voladizo) ----
def oreja(xa, s_, yc):
    xo = xa - s_ * X0                             # borde exterior de la oreja (x=1 o x=109)
    ancho = X0
    prisma_xy = [(xa, yc - 7 - ancho), (xa, yc + 7), (xo, yc + 7), (xo, yc - 7)]
    bm = bmesh.new()
    v0 = [bm.verts.new(Vector((u, v, ZB))) for u, v in prisma_xy]
    v1 = [bm.verts.new(Vector((u, v, ZB + 3))) for u, v in prisma_xy]
    bm.faces.new(v0); bm.faces.new(v1[::-1])
    for i in range(4):
        bm.faces.new((v0[i], v1[i], v1[(i + 1) % 4], v0[(i + 1) % 4]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    piezas.append(bm)
for yc in TAB_Y:
    oreja(X0 + 1, 1, yc)
    oreja(X1 - 1, -1, yc)

# unir todo con union booleana exacta (malla limpia y liviana)
objs = []
for i, p in enumerate(piezas):
    me = bpy.data.meshes.new(f"p{i}"); p.to_mesh(me); p.free()
    o = bpy.data.objects.new(f"p{i}", me); sc.collection.objects.link(o); objs.append(o)
pers = objs[0]; pers.name = "persiana"
col = bpy.data.collections.new("resto"); sc.collection.children.link(col)
for o in objs[1:]:
    sc.collection.objects.unlink(o); col.objects.link(o)
m = pers.modifiers.new("unir", "BOOLEAN"); m.operation = "UNION"; m.operand_type = "COLLECTION"; m.collection = col
m.solver = "MANIFOLD" if "MANIFOLD" in [i.identifier for i in m.bl_rna.properties["solver"].enum_items] else "EXACT"
bpy.context.view_layer.objects.active = pers
bpy.ops.object.modifier_apply(modifier="unir")
for o in objs[1:]: bpy.data.objects.remove(o)

# restas: agujeros de las orejas, ranuras del piso y muescas para las cabezas de los tornillos de muro
def restar(x0, x1, y0, y1, z0, z1, cil=None):
    if cil:
        bpy.ops.mesh.primitive_cylinder_add(radius=cil, depth=20, vertices=32, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    else:
        bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
        bpy.context.object.scale = (x1 - x0, y1 - y0, z1 - z0)
    c = bpy.context.object
    m = pers.modifiers.new("r", "BOOLEAN"); m.operation = "DIFFERENCE"; m.object = c; m.solver = "MANIFOLD" if "MANIFOLD" in [i.identifier for i in m.bl_rna.properties["solver"].enum_items] else "EXACT"
    bpy.context.view_layer.objects.active = pers
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(c)

for yc in TAB_Y:
    for xc in (4.0, 106.0):
        restar(xc, xc, yc, yc, 5, 5, cil=1.7)                         # paso para tornillo de 3 mm
for xs in (20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0):
    restar(xs - 2.5, xs + 2.5, Y0 - 1, Y0 + PISO + 1, ZB + 6, ZF - PROF - 2)   # ranuras de drenaje y entrada de aire
for (a, b) in ((X0 - 1, 14.5), (95.5, X1 + 1)):
    restar(a, b, 154, Y1 + 1, ZB - 1, ZB + 9)                           # muesca: cabezas de tornillos de muro superiores

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
exportar(pers, os.path.join(BASE, f"ref_persiana_{VER}_ensamble.stl"))
# impresion: de pie, con el piso sobre la cama (Y del ensamble -> Z de impresion)
exportar(pers, f"4_persiana_{VER}.stl", Matrix.Rotation(math.radians(90), 4, "X"))

d = pers.dimensions
print("PERSIANA dims mm", round(d.x, 1), round(d.y, 1), round(d.z, 1), "verts", len(pers.data.vertices))
bm = bmesh.new(); bm.from_mesh(pers.data)
print("PERSIANA volumen cm3", round(bm.calc_volume() / 1000, 1), "estanca", all(e.is_manifold for e in bm.edges))
bm.free()
