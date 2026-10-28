# Uso: blender -b -P vista_persiana.py -- salida.png [4_persiana_vN.stl]
# Vista rapida de la persiana en orientacion de impresion + conteo de voladizos.
import bpy, os, sys, math
from mathutils import Vector
BASE = os.path.dirname(os.path.abspath(__file__))
arg = sys.argv[sys.argv.index("--") + 1:]
sal = arg[0]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.stl_import(filepath=os.path.join(BASE, "..", "Persiana_GLog", "STL", arg[1] if len(arg) > 1 else "4_persiana_v2.stl"))
o = bpy.context.selected_objects[0]
mal = 0.0
for p in o.data.polygons:
    c = (o.matrix_world @ p.center).z
    if p.normal.z < -0.7072 and c > 0.3: mal += p.area
print("VOLADIZO >45 mm2", round(mal, 1))
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"
sc.display.shading.show_cavity = True; sc.display.shading.color_type = "SINGLE"
sc.display.shading.single_color = (0.9, 0.9, 0.88)
sc.render.resolution_x, sc.render.resolution_y = 1400, 1200
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50; cam.location = (-120, -170, 150)
d = Vector((54, 20, 67)) - cam.location; cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
sc.render.filepath = sal; bpy.ops.render.render(write_still=True)
