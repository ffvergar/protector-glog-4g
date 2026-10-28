# Cuna v1: soporte a medida (escurre: ninguna cara plana mirando hacia arriba) para el GLog 4G (SigmaWit GLogm3 / GLogs1), reemplaza a 3_repisa.
# El equipo no tiene tornillos: queda fijo por un bolsillo abajo (piso + pestana frontal), dos
# lenguetas con gancho arriba (encaja a presion, "clic"), nervios de ajuste en los costados y
# los separadores de la placa por detras.
# Se atornilla a la placa en los mismos 2 agujeros de la repisa (M3 x 8 avellanado + tuerca).
# Uso: blender -b -P cuna_vN.py   (la version sale del nombre del archivo)
# Coordenadas = las del ensamble (mm): X ancho, Y alto, Z hacia afuera del muro (placa: z 0..4).
import bpy, bmesh, os, math
from mathutils import Vector, Matrix

BASE = os.path.dirname(os.path.abspath(__file__))
SAL = os.path.join(BASE, "..", "Persiana_GLog", "STL")
VER = os.path.splitext(os.path.basename(__file__))[0].split("_")[-1]
os.makedirs(SAL, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ---- equipo (medir con pie de metro y ajustar aqui) ----
EQ_W, EQ_H, EQ_T = 68.5, 105.5, 16.5     # ancho, alto (sin asa), espesor
XC, YB, ZD = 55.0, 48.0, 9.0             # centro en X, base del equipo, espalda (sobre los separadores)

# ---- parametros de la cuna (mm) ----
HOL = 0.25                   # holgura por lado en X (los nervios la cierran)
NERV = 0.45                  # cuanto sobresale cada nervio de ajuste (se aplasta ~0,2 mm)
HOL_Y = 0.3                  # holgura en alto, entre piso y ganchos
HOL_Z = 0.1                  # holgura entre el frente del equipo y pestana/ganchos
PARED = 2.25                 # 5 lineas de 0,45
PISO = 3.0
ZP = 4.3                     # apoyo sobre la placa
LAB = 1.8                    # espesor de pestana y ganchos
SOLAPE = 2.0                 # cuanto montan pestana y ganchos sobre el frente del equipo
TORN = (29.5, 79.5)          # agujeros de la repisa original en la placa (y = 55,5)
Y_TORN = 55.5
LENG_X = ((28.0, 35.0), (75.0, 82.0))   # lenguetas, cerca de las esquinas (el asa va al centro)

xi0, xi1 = XC - EQ_W / 2 - HOL, XC + EQ_W / 2 + HOL     # cara interior de las paredes
xo0, xo1 = xi0 - PARED, xi1 + PARED
zf = ZD + EQ_T + HOL_Z                                  # cara interior de pestana y ganchos
ZF = zf + LAB                                           # frente de la cuna
Y0 = YB - PISO
yt = YB + EQ_H + HOL_Y                                  # borde superior del equipo + holgura
YTOP = 156.4                                            # bajo la banda de la abrazadera (y 156,5)

piezas = []

def caja(x0, x1, y0, y1, z0, z1):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts:
        v.co = Vector((x0 if v.co.x < 0 else x1, y0 if v.co.y < 0 else y1, z0 if v.co.z < 0 else z1))
    piezas.append(bm)

def prisma(perfil, eje, a0, a1):
    """perfil 2D extruido de a0 a a1 a lo largo de 'eje'. x: perfil (y,z); z: perfil (x,y); y: perfil (x,z)."""
    bm = bmesh.new()
    def p3(u, v, a):
        if eje == "x": return Vector((a, u, v))
        if eje == "y": return Vector((u, a, v))
        return Vector((u, v, a))
    vs0 = [bm.verts.new(p3(u, v, a0)) for u, v in perfil]
    vs1 = [bm.verts.new(p3(u, v, a1)) for u, v in perfil]
    bm.faces.new(vs0[::-1]); bm.faces.new(vs1)
    n = len(perfil)
    for i in range(n):
        bm.faces.new((vs0[i], vs0[(i + 1) % n], vs1[(i + 1) % n], vs1[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    piezas.append(bm)

# ---- paredes laterales: canto superior inclinado hacia el frente (escurre) ----
for (a_, b_) in ((xo0, xi0), (xi1, xo1)):
    prisma([(Y0, ZP), (YTOP, ZP), (YTOP, ZD - 0.4), (yt - 10.0, ZF), (Y0, ZF)], "x", a_, b_)   # canto a ~34 grados

# ---- nervios de ajuste: triangulos verticales (en impresion) en la cara interior ----
for yn in (74.0, 102.0, 132.0):
    for xa, s_ in ((xi0, 1), (xi1, -1)):
        prisma([(xa - s_ * 0.1, yn - 1.2), (xa + s_ * NERV, yn), (xa - s_ * 0.1, yn + 1.2)], "z", ZD + 1.5, zf - 1.5)

# ---- bolsillo de abajo SIN piso lleno: el agua cae entre los apoyos ----
# 3 nervios de apoyo (el equipo se para sobre sus cantos de 2,25 mm), fondo inclinado hacia abajo y al frente
NERV_X = (xi0 + 1.0, XC - PARED / 2, xi1 - 1.0 - PARED)
for xa in NERV_X:
    prisma([(Y0, ZP), (YB, ZP), (YB, ZF), (Y0 - 2.0, ZF)], "x", xa, xa + PARED)
# barra trasera baja (amarra las paredes); cara de arriba inclinada hacia el frente
prisma([(Y0, ZP), (YB, ZP), (Y0 + 0.8, ZD - 0.4), (Y0, ZD - 0.4)], "x", xi0 - 0.1, xi1 + 0.1)
# pestana frontal solo en las esquinas (centro abierto para que salga el agua); canto superior inclinado
LAB_X = 11.0
for (a_, b_) in ((xi0 - 0.1, xi0 + LAB_X), (xi1 - LAB_X, xi1 + 0.1)):
    prisma([(Y0 - 2.0, zf), (YB + SOLAPE, zf), (YB + SOLAPE - 1.0, ZF), (Y0 - 2.0, ZF)], "x", a_, b_)

# ---- bloque de fijacion detras del equipo (2 tuercas M3) ----
for xt in TORN:                                   # cara de arriba a 45 grados hacia el frente
    prisma([(Y0, ZP), (Y_TORN + 8.5, ZP), (Y_TORN + 8.5 - (ZD - 0.2 - ZP), ZD - 0.2), (Y0, ZD - 0.2)], "x", xt - 6, xt + 6)

# ---- travesanos traseros (apoyan en la cama al imprimir y amarran las paredes) ----
# seccion en techo de dos aguas: nada plano mirando hacia arriba
prisma([(99.0, ZP), (105.0, ZP), (102.0, ZD - 0.4)], "x", xi0 - 0.1, xi1 + 0.1)          # entre separadores (y 79 y 135)
prisma([(yt, ZP), (YTOP, ZP), (yt, ZD - 0.4)], "x", xi0 - 0.1, xi1 + 0.1)                # arriba, sobre el equipo

# ---- lenguetas con gancho (flectan en Y al empujar el equipo hacia atras) ----
ZL = ZF + 2.5                                           # la lengueta sobresale un poco: tirador
for (a_, b_) in LENG_X:                              # lomo a dos aguas (23 grados, bajo la banda de la abrazadera): el agua cae por los lados
    cm = (a_ + b_) / 2
    prisma([(a_, yt), (b_, yt), (b_, yt + 1.0), (cm, yt + 2.5), (a_, yt + 1.0)], "z", ZP, ZL)
    # gancho: cara de retencion plana sobre el frente (voladizo de 2 mm) y rampa de entrada a 45 grados
    prisma([(yt + 0.1, zf), (yt - SOLAPE, zf), (yt - SOLAPE, zf + 0.8), (yt + 0.1, zf + 0.8 + SOLAPE + 0.1)], "x", a_, b_)

# ---- unir ----
objs = []
for i, p in enumerate(piezas):
    me = bpy.data.meshes.new(f"p{i}"); p.to_mesh(me); p.free()
    o = bpy.data.objects.new(f"p{i}", me); sc.collection.objects.link(o); objs.append(o)
cuna = objs[0]; cuna.name = "cuna"
col = bpy.data.collections.new("resto"); sc.collection.children.link(col)
for o in objs[1:]:
    sc.collection.objects.unlink(o); col.objects.link(o)
SOLVER = "MANIFOLD"
m = cuna.modifiers.new("unir", "BOOLEAN"); m.operation = "UNION"; m.operand_type = "COLLECTION"; m.collection = col; m.solver = SOLVER
bpy.context.view_layer.objects.active = cuna
bpy.ops.object.modifier_apply(modifier="unir")
for o in objs[1:]: bpy.data.objects.remove(o)

def restar(obj):
    m = cuna.modifiers.new("r", "BOOLEAN"); m.operation = "DIFFERENCE"; m.object = obj; m.solver = SOLVER
    bpy.context.view_layer.objects.active = cuna
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(obj)

def rombo(centro, mitad, eje_paso, largo):
    """rombo (cuadrado a 45 grados) de semidiagonal 'mitad' que atraviesa en 'eje_paso'; puntas arriba/abajo en Z."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=centro)
    c = bpy.context.object
    lado = mitad * math.sqrt(2)
    if eje_paso == "x":
        c.scale = (largo, lado, lado); c.rotation_euler = (math.radians(45), 0, 0)
    else:
        c.scale = (lado, largo, lado); c.rotation_euler = (0, math.radians(45), 0)
    restar(c)

def cilindro(x, y, z, r, prof, lados=32):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=prof, vertices=lados, location=(x, y, z))
    restar(bpy.context.object)

# agujeros M3 y alojamiento hexagonal de tuerca (se abre hacia el frente: la tuerca se pone antes del equipo)
for xt in TORN:
    cilindro(xt, Y_TORN, ZP + 5, 1.7, 12)
    bpy.ops.mesh.primitive_cylinder_add(radius=3.25, depth=3.0, vertices=6, location=(xt, Y_TORN, ZD - 0.2 - 1.5 + 0.05))
    restar(bpy.context.object)

# ventanas en rombo: paredes (aire y menos plastico) y piso (drenaje)
zc = (ZP + ZF) / 2
for yv in (62.0, 87.0, 117.0, 146.0):
    rombo((xo0 + PARED / 2, yv, zc), 6.5, "x", PARED + 2)
    rombo((xo1 - PARED / 2, yv, zc), 6.5, "x", PARED + 2)

# ---- exportar ----
def exportar(obj, ruta):
    for o in sc.objects: o.select_set(False)
    obj.select_set(True); bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.stl_export(filepath=ruta, export_selected_objects=True, apply_modifiers=True)

def bajar_a_cama(obj):
    """impresion: acostada sobre la espalda (cara z = ZP sobre la cama), ya esta en Z arriba."""
    obj.matrix_world = Matrix.Translation((-xo0, -Y0, -ZP)) @ obj.matrix_world
    bpy.context.view_layer.update()

exportar(cuna, os.path.join(BASE, f"ref_cuna_{VER}_ensamble.stl"))

# probeta de ajuste: solo el bolsillo de abajo y la franja de las lenguetas (imprimir primero, ~15 min)
prueba = cuna.copy(); prueba.data = cuna.data.copy(); sc.collection.objects.link(prueba)
bpy.ops.mesh.primitive_cube_add(size=1); corte = bpy.context.object
corte.location = (XC, (Y0 + 66.0) / 2 + 40, 20); corte.scale = (200, 66.0 - Y0 + 0.01, 100)
# mantener y < 66 y y > 138: se resta la franja del medio
corte.location = (XC, (66.0 + 138.0) / 2, 20); corte.scale = (200, 138.0 - 66.0, 100)
m = prueba.modifiers.new("c", "BOOLEAN"); m.operation = "DIFFERENCE"; m.object = corte; m.solver = SOLVER
bpy.context.view_layer.objects.active = prueba
bpy.ops.object.modifier_apply(modifier="c")
bpy.data.objects.remove(corte)

for obj, nombre in ((cuna, f"5_cuna_{VER}.stl"), (prueba, f"5_cuna_{VER}_prueba_ajuste.stl")):
    guard = obj.matrix_world.copy()
    bajar_a_cama(obj)
    exportar(obj, os.path.join(SAL, nombre))
    obj.matrix_world = guard

for obj in (cuna, prueba):
    d = obj.dimensions
    bm = bmesh.new(); bm.from_mesh(obj.data)
    print("CUNA", obj.name, "dims mm", round(d.x, 1), round(d.y, 1), round(d.z, 1),
          "volumen cm3", round(bm.calc_volume() / 1000, 1), "estanca", all(e.is_manifold for e in bm.edges))
    bm.free()
print("CUNA interior X", round(xi1 - xi0, 2), "entre nervios", round(xi1 - xi0 - 2 * NERV, 2),
      "alto", round(yt - YB, 2), "fondo", round(zf - ZD, 2))
