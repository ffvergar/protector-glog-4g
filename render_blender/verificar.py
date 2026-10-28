# Verificacion del producto armado: choques entre piezas, agua estancada, voladizos de impresion.
# Uso: blender -b -P verificar.py -- persiana_v5 cuna_v1
# Deja verificacion_<persiana>_<cuna>.json y las piezas separadas (coordenadas de ensamble) en ./visor/
import bpy, bmesh, os, sys, json, math
from mathutils import Vector

BASE = os.path.dirname(os.path.abspath(__file__))
SAL = os.path.join(BASE, "..", "Persiana_GLog", "STL")
ORIG = os.path.join(BASE, "..", "Protector_GLog", "STL")
VIS = os.path.join(BASE, "visor"); os.makedirs(VIS, exist_ok=True)
arg = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
PERS = arg[0] if arg else "persiana_v5"
CUNA = arg[1] if len(arg) > 1 else "cuna_v1"
VC = CUNA.split("_")[-1]
VP = PERS.split("_")[-1]

# equipo y cuna (mismos valores que cuna_v1.py)
EQ_W, EQ_H, EQ_T, XC, YB, ZD = 68.5, 105.5, 16.5, 55.0, 48.0, 9.0
YT = YB + EQ_H + 0.3
LENG_X = ((28.0, 35.0), (75.0, 82.0))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def importar(ruta, nombre):
    bpy.ops.wm.stl_import(filepath=ruta)
    o = bpy.context.selected_objects[0]; o.name = nombre
    return o

def copia(o, nombre):
    c = o.copy(); c.data = o.data.copy(); c.name = nombre; sc.collection.objects.link(c)
    return c

def booleano(a, b, op):
    m = a.modifiers.new("b", "BOOLEAN"); m.operation = op; m.object = b; m.solver = "MANIFOLD"
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.modifier_apply(modifier=m.name)

def volumen(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    v = bm.calc_volume(); bm.free(); return abs(v)

def caja_obj(x0, x1, y0, y1, z0, z1, nombre="caja"):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    c = bpy.context.object; c.scale = (x1 - x0, y1 - y0, z1 - z0); c.name = nombre
    bpy.ops.object.transform_apply(scale=True)
    return c

def exportar(o, ruta):
    for x in sc.objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.wm.stl_export(filepath=ruta, export_selected_objects=True)

# ---- piezas en coordenadas de ensamble ----
placa = importar(os.path.join(SAL, "1_placa_v2.stl"), "placa")
ens = importar(os.path.join(ORIG, "0_ensamble_ref.stl"), "ens")
bpy.context.view_layer.objects.active = ens
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT"); bpy.ops.mesh.separate(type="LOOSE"); bpy.ops.object.mode_set(mode="OBJECT")
techo = None
for o in list(sc.objects):
    if o.name.startswith("ens"):
        ys = [(o.matrix_world @ v.co).y for v in o.data.vertices]
        if min(ys) > 120: techo = o; o.name = "techo"
        else: bpy.data.objects.remove(o)
pers = importar(os.path.join(BASE, f"ref_{PERS}_ensamble.stl"), "persiana")
cuna = importar(os.path.join(BASE, f"ref_{CUNA}_ensamble.stl"), "cuna")

# equipo: caja con esquinas redondeadas (R 6 en planta, 1,5 en los cantos)
bpy.ops.mesh.primitive_cube_add(size=1, location=(XC, YB + EQ_H / 2, ZD + EQ_T / 2))
eq = bpy.context.object; eq.name = "equipo"; eq.scale = (EQ_W, EQ_H, EQ_T)
bpy.ops.object.transform_apply(scale=True)
bv = eq.modifiers.new("bv", "BEVEL"); bv.width = 1.5; bv.segments = 3
bpy.ops.object.modifier_apply(modifier="bv")

# ---- 1. choques: volumen comun entre cada par (mm3) ----
piezas = {"placa": placa, "techo": techo, "cuna": cuna, "equipo": eq, "persiana": pers}
nombres = list(piezas)
choques = {}
for i in range(len(nombres)):
    for j in range(i + 1, len(nombres)):
        a, b = piezas[nombres[i]], piezas[nombres[j]]
        t = copia(a, "tmp"); booleano(t, b, "INTERSECT")
        v = volumen(t) if len(t.data.vertices) else 0.0
        bpy.data.objects.remove(t)
        choques[f"{nombres[i]}-{nombres[j]}"] = round(v, 1)

# ---- 2. agua: caras que miran hacia arriba (casi horizontales) en posicion de uso ----
def caras_arriba(o, lim=0.94):
    tot = 0.0; zonas = []
    for p in o.data.polygons:
        n = (o.matrix_world.to_3x3() @ p.normal).normalized()
        if n.y > lim:
            tot += p.area
            if p.area > 2: zonas.append([round(c, 1) for c in (o.matrix_world @ p.center)] + [round(p.area, 1)])
    return round(tot, 1), sorted(zonas, key=lambda z: -z[3])[:12]
agua = {k: caras_arriba(piezas[k]) for k in ("cuna", "persiana")}

# ---- 3. voladizos en orientacion de impresion (STL de impresion) ----
def voladizos(ruta):
    o = importar(ruta, "imp")
    g = {"hasta_45_grados_mm2": 0.0, "45_a_60_mm2": 0.0, "60_a_80_mm2": 0.0, "plano_colgante_mm2": 0.0}
    for p in o.data.polygons:
        if p.center.z < 0.3 or p.normal.z >= -1e-3: continue
        ang = math.degrees(math.asin(min(1.0, -p.normal.z)))          # angulo de la cara desde la vertical
        k = "hasta_45_grados_mm2" if ang <= 45.5 else "45_a_60_mm2" if ang <= 60.5 else "60_a_80_mm2" if ang <= 80 else "plano_colgante_mm2"
        g[k] += p.area
    d = o.dimensions
    res = {k: round(v, 1) for k, v in g.items()}
    res["tamano_impresion_mm"] = [round(d.x, 1), round(d.y, 1), round(d.z, 1)]
    bpy.data.objects.remove(o)
    return res
imp = {
    "persiana": voladizos(os.path.join(SAL, f"4_{PERS}.stl")),
    "cuna": voladizos(os.path.join(SAL, f"5_{CUNA}.stl")),
}

# ---- 4. ajuste del equipo en la cuna ----
ajuste = {"holgura_alto_mm": round(YT - YB - EQ_H, 2)}

# ---- 5. piezas separadas para el visor (lenguetas aparte para animarlas) ----
ZP, LAB = 4.3, 1.8
cuerpo = copia(cuna, "cuna_cuerpo")
for k, (a_, b_) in enumerate(LENG_X):
    corte = caja_obj(a_ - 0.01, b_ + 0.01, YT - 3, YT + 4, ZD - 0.4, 60, "corte")
    l = copia(cuna, f"lengueta{k}"); booleano(l, corte, "INTERSECT")
    exportar(l, os.path.join(VIS, f"cuna_{VC}_lengueta{k}.stl"))
    booleano(cuerpo, corte, "DIFFERENCE"); bpy.data.objects.remove(corte)
exportar(cuerpo, os.path.join(VIS, f"cuna_{VC}_cuerpo.stl"))
exportar(placa, os.path.join(VIS, "placa_v2.stl"))
exportar(techo, os.path.join(VIS, "techo.stl"))
exportar(pers, os.path.join(VIS, f"{PERS}.stl"))

res = {"persiana": PERS, "cuna": CUNA, "choques_mm3": choques, "agua_caras_hacia_arriba_mm2": agua,
       "impresion": imp, "ajuste": ajuste, "volumen_cm3": {k: round(volumen(v) / 1000, 1) for k, v in piezas.items()}}
ruta = os.path.join(BASE, f"verificacion_{VP}_{VC}.json")
json.dump(res, open(ruta, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("VERIF", json.dumps(res, ensure_ascii=False))
