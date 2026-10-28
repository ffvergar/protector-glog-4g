import bpy, bmesh, os, math
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Persiana_GLog", "STL")
for n in ("4_persiana.stl", "ref_persiana_ensamble.stl"):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.stl_import(filepath=os.path.join(S, n)); o = bpy.context.selected_objects[0]
    bpy.context.view_layer.objects.active = o
    d = o.modifiers.new("d", "DECIMATE"); d.decimate_type = "COLLAPSE"; d.ratio = 0.1
    bpy.ops.object.modifier_apply(modifier="d")
    t = o.modifiers.new("t", "TRIANGULATE"); bpy.ops.object.modifier_apply(modifier="t")
    bm = bmesh.new(); bm.from_mesh(o.data)
    print("ALIGERADO", n, len(o.data.polygons), "estanca", all(e.is_manifold for e in bm.edges), "vol", round(bm.calc_volume()/1000, 1))
    bm.free()
    bpy.ops.wm.stl_export(filepath=os.path.join(S, n), export_selected_objects=True)
