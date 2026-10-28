# Render fotorrealista del protector GLog 4G con Blender (Cycles).
# Uso: blender -b -P escena.py -- <muro|poste|invernadero|despiece> <salida.png> [muestras] [version persiana, ej. v2]
import bpy, bmesh, math, sys, os
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODO = args[0] if args else "muro"
SALIDA = os.path.abspath(args[1] if len(args) > 1 else f"render_{MODO}.png")
MUESTRAS = int(args[2]) if len(args) > 2 else 256
VER_PERS = args[3] if len(args) > 3 else "v2"

BASE = os.path.dirname(os.path.abspath(__file__))
STL = os.path.join(BASE, "..", "Protector_GLog", "STL", "0_ensamble_ref.stl")
FOTO = os.path.join(BASE, "frente_glog.png")
MM = 0.001

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def mat(nombre, color, rough=0.5, metal=0.0, bump=None):
    m = bpy.data.materials.new(nombre); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if bump:
        bump(nt, b)
    return m

def capas_impresion(nt, b):
    # lineas de capa de 0,2 mm de la impresion 3D (a lo largo del eje Z del objeto)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    w = nt.nodes.new("ShaderNodeTexWave"); w.wave_type = "BANDS"; w.bands_direction = "Z"
    w.inputs["Scale"].default_value = 1 / (0.2 * MM) / 6.28 * 0.16
    nt.links.new(tc.outputs["Object"], w.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.06
    bp.inputs["Distance"].default_value = 0.0001
    nt.links.new(w.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])

def rugoso(escala, fuerza):
    def f(nt, b):
        n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = escala
        n.inputs["Detail"].default_value = 12
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = fuerza
        nt.links.new(n.outputs["Fac"], bp.inputs["Height"])
        nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return f

m_asa = mat("PETG blanco", (0.80, 0.81, 0.80), 0.42, bump=capas_impresion)
m_caja = mat("Carcasa GLog", (0.86, 0.87, 0.87), 0.35)
m_asa_glog = mat("Asa GLog", (0.80, 0.81, 0.82), 0.4)
m_tornillo = mat("Inox", (0.75, 0.75, 0.76), 0.25, metal=1.0)

# ---------- protector (STL real: X ancho, Y alto, Z hacia afuera del muro) ----------
bpy.ops.wm.stl_import(filepath=STL)
prot = bpy.context.selected_objects[0]
prot.scale = (MM, MM, MM)
prot.rotation_euler = (math.radians(90), 0, 0)   # Y_stl -> Z, Z_stl -> -Y
prot.data.materials.append(m_asa)
bpy.ops.object.shade_auto_smooth(angle=math.radians(30))

def P(x, y, z):  # coordenadas del STL (mm) -> Blender (m)
    return Vector((x * MM, -z * MM, y * MM))

# persiana tipo Stevenson (version invernadero); en "despiece" se muestra sacada hacia adelante
if MODO in ("invernadero", "despiece"):
    bpy.ops.wm.stl_import(filepath=os.path.join(BASE, f"ref_persiana_{VER_PERS}_ensamble.stl"))
    pers = bpy.context.selected_objects[0]
    pers.scale = (MM, MM, MM); pers.rotation_euler = (math.radians(90), 0, 0)
    if MODO == "despiece":
        pers.location = P(125, -15, 35)
    pers.data.materials.append(m_asa)
    bpy.ops.object.shade_auto_smooth(angle=math.radians(30))

# ---------- GLog: 68,5 x 105,5 x 16,5 mm, sobre la repisa (y=48) contra separadores (z=9) ----------
W, H, D = 68.5, 105.5, 16.5
bpy.ops.mesh.primitive_cube_add(size=1, location=P(55, 48 + H / 2, 9 + D / 2))
caja = bpy.context.object; caja.name = "GLog"
caja.scale = (W * MM, D * MM, H * MM)
bpy.ops.object.transform_apply(scale=True)
bv = caja.modifiers.new("bisel", "BEVEL"); bv.width = 5 * MM; bv.segments = 8
caja.data.materials.append(m_caja)
bpy.ops.object.shade_smooth()

# nervaduras laterales de la carcasa
for lado in (-1, 1):
    for i in range(14):
        y = 48 + 18 + i * 5.2
        bpy.ops.mesh.primitive_cube_add(size=1, location=P(55 + lado * (W / 2 + 0.3), y, 9 + D / 2))
        r = bpy.context.object; r.scale = (1.2 * MM, 11 * MM, 2.2 * MM)
        r.data.materials.append(m_caja)

# frente: foto real del fabricante
bpy.ops.mesh.primitive_plane_add(size=1, location=P(55, 48 + H / 2, 9 + D + 0.05))
fr = bpy.context.object; fr.name = "Frente GLog"
fr.rotation_euler = (math.radians(90), 0, 0)
fr.scale = ((W - 1.0) * MM, (H - 1.0) * MM, 1)
mf = bpy.data.materials.new("Frente"); mf.use_nodes = True
nt = mf.node_tree; b = nt.nodes["Principled BSDF"]
tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(FOTO)
nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
nt.links.new(tex.outputs["Alpha"], b.inputs["Alpha"])
b.inputs["Roughness"].default_value = 0.18          # pantalla/etiqueta con algo de brillo
b.inputs["Coat Weight"].default_value = 0.3
fr.data.materials.append(mf)

# asa del equipo, pasada por el gancho del protector
bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.09, major_segments=64, minor_segments=12,
                                 location=P(55, 48 + H - 2, 9 + D / 2), rotation=(math.radians(90), 0, 0))
asa = bpy.context.object
asa.scale = (24 * MM, 12 * MM, 12 * MM)
bpy.ops.object.transform_apply(scale=True, rotation=True)
bm = bmesh.new(); bm.from_mesh(asa.data)
bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
                       plane_co=(0, 0, 0), plane_no=(0, 0, 1), clear_inner=True)
bm.to_mesh(asa.data); bm.free()
asa.data.materials.append(m_asa_glog)
bpy.ops.object.shade_smooth()

# ---------- entorno ----------
if MODO == "muro":
    bpy.ops.mesh.primitive_plane_add(size=1.2, location=(0.055, 0.0002, 0.1), rotation=(math.radians(90), 0, 0))
    muro = bpy.context.object
    m_muro = mat("Muro estuco", (0.50, 0.46, 0.41), 0.9, bump=rugoso(900, 0.35))
    muro.data.materials.append(m_muro)
    # tornillos de muro en la placa
    for (x, y) in ((55, 20),):
        bpy.ops.mesh.primitive_cylinder_add(radius=4 * MM, depth=1.5 * MM, location=P(x, y, 4.6),
                                            rotation=(math.radians(90), 0, 0))
        bpy.context.object.data.materials.append(m_tornillo)
else:
    R = 0.038
    bpy.ops.mesh.primitive_cylinder_add(radius=R, depth=1.6, vertices=96, location=(0.055, R + 0.001, 0.1))
    poste = bpy.context.object
    poste.data.materials.append(mat("Poste galvanizado", (0.55, 0.57, 0.58), 0.45, metal=0.9, bump=rugoso(400, 0.12)))
    bpy.ops.object.shade_smooth()
    m_banda = mat("Abrazadera inox", (0.8, 0.8, 0.82), 0.2, metal=1.0)
    for y in (25, 175):
        bpy.ops.mesh.primitive_cylinder_add(radius=R + 0.0008, depth=0.012, vertices=96, location=(0.055, R + 0.001, y * MM))
        band = bpy.context.object; band.data.materials.append(m_banda); bpy.ops.object.shade_smooth()
    # fondo exterior desenfocado
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 6, 0), rotation=(math.radians(90), 0, 0))
    fondo = bpy.context.object
    mfo = mat("Fondo", (0.35, 0.42, 0.38), 1.0); fondo.data.materials.append(mfo)
    if MODO in ("invernadero", "despiece"):
        # invernadero: hileras de plantas desenfocadas detras y plastico difuso arriba
        import random; random.seed(4)
        m_hoja = [mat(f"Hoja{i}", c, 0.6) for i, c in enumerate(((0.10, 0.28, 0.06), (0.16, 0.36, 0.08), (0.08, 0.22, 0.05)))]
        for fila in range(6):
            yf = 0.9 + fila * 0.8
            for k in range(40):
                x = -2.5 + k * 0.13 + random.uniform(-0.05, 0.05)
                z = -0.9 + random.uniform(0.2, 0.9)
                bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=random.uniform(0.12, 0.28), location=(x, yf, z))
                bpy.context.object.data.materials.append(random.choice(m_hoja)); bpy.ops.object.shade_smooth()
        mfo.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.75, 0.78, 0.74, 1)
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.9))
    bpy.context.object.data.materials.append(mat("Suelo", (0.3, 0.32, 0.28), 1.0))

# ---------- luz ----------
w = bpy.data.worlds.new("cielo"); sc.world = w; w.use_nodes = True
sky = w.node_tree.nodes.new("ShaderNodeTexSky")
sky.sky_type = "NISHITA" if "NISHITA" in [i.identifier for i in sky.bl_rna.properties["sky_type"].enum_items] else sky.sky_type
sky.sun_elevation = math.radians(35); sky.sun_rotation = math.radians(210)
bg = w.node_tree.nodes["Background"]; bg.inputs["Strength"].default_value = 0.08
w.node_tree.links.new(sky.outputs["Color"], bg.inputs["Color"])

sol = bpy.data.lights.new("sol", "SUN"); sol.energy = 2.2; sol.angle = math.radians(1.5)
so = bpy.data.objects.new("sol", sol); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(50), math.radians(-25), math.radians(-35))
rel = bpy.data.lights.new("relleno", "AREA"); rel.energy = 2; rel.size = 0.6
ro = bpy.data.objects.new("relleno", rel); sc.collection.objects.link(ro)
ro.location = (-0.35, -0.6, 0.25); ro.rotation_euler = (math.radians(70), 0, math.radians(-30))

# ---------- camara ----------
cam = bpy.data.cameras.new("cam"); cam.lens = 70
cam.dof.use_dof = True; cam.dof.aperture_fstop = 5.6
co = bpy.data.objects.new("cam", cam); sc.collection.objects.link(co); sc.camera = co
co.location = (-0.20, -0.52, 0.17)
obj = bpy.data.objects.new("mira", None); sc.collection.objects.link(obj)
obj.location = P(55, 105, 12)
if MODO == "despiece":
    co.location = (-0.22, -0.62, 0.20); obj.location = P(110, 100, 25); cam.lens = 55
    cam.dof.aperture_fstop = 4
t = co.constraints.new("TRACK_TO"); t.target = obj; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
cam.dof.focus_object = obj

# ---------- render ----------
sc.render.engine = "CYCLES"
sc.cycles.samples = MUESTRAS; sc.cycles.use_denoising = True
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for tipo in ("OPTIX", "CUDA", "HIP", "ONEAPI"):
        try:
            prefs.compute_device_type = tipo; prefs.get_devices()
            if any(d.type == tipo for d in prefs.devices):
                for d in prefs.devices: d.use = True
                sc.cycles.device = "GPU"; break
        except Exception:
            pass
except Exception:
    pass
sc.render.resolution_x = 1600; sc.render.resolution_y = 2000
sc.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
try:
    sc.view_settings.look = "AgX - Punchy"
except Exception:
    sc.view_settings.look = "None"
sc.view_settings.exposure = -0.6
sc.render.filepath = SALIDA
bpy.ops.render.render(write_still=True)
print("LISTO", SALIDA, sc.cycles.device)
