import bpy, os
from mathutils.bvhtree import BVHTree
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Protector_GLog", "STL")
def load(n):
    bpy.ops.wm.stl_import(filepath=os.path.join(D, n)); o = bpy.context.selected_objects[0]
    dg = bpy.context.evaluated_depsgraph_get(); return BVHTree.FromObject(o, dg)
p = load("1_placa.stl")
import numpy as np
hole = np.zeros((200, 110), bool)
for y in range(200):
    for x in range(110):
        hole[y, x] = p.ray_cast(Vector((x + .5, y + .5, -5)), Vector((0, 0, 1)))[0] is None
from collections import deque
seen = np.zeros_like(hole)
for y in range(200):
    for x in range(110):
        if hole[y, x] and not seen[y, x]:
            q = deque([(y, x)]); seen[y, x] = 1; pts = []
            while q:
                a, b = q.popleft(); pts.append((a, b))
                for da, db in ((1,0),(-1,0),(0,1),(0,-1)):
                    c, d = a+da, b+db
                    if 0 <= c < 200 and 0 <= d < 110 and hole[c, d] and not seen[c, d]:
                        seen[c, d] = 1; q.append((c, d))
            ys = [t[0] for t in pts]; xs = [t[1] for t in pts]
            print("HUECO x", min(xs), max(xs), "y", min(ys), max(ys))
a = load("0_ensamble_ref.stl")
for x in (2, 5, 9, 12, 30, 55):
    row = []
    for z in (5, 10, 20, 30, 40, 50, 60):
        h = a.ray_cast(Vector((x, 128, z)), Vector((0, 1, 0)))
        row.append(round(h[0].y, 1) if h[0] else None)
    print("TECHO x", x, row)
