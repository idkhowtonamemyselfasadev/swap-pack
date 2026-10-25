# Blender check render of a Minecraft JSON block model: blender -b -P render.py -- model.json texture.png out_prefix
import bpy, json, sys, math
args = sys.argv[sys.argv.index("--") + 1:]
model, tex, out = args
bpy.ops.wm.read_factory_settings(use_empty=True)
img = bpy.data.images.load(bpy.path.abspath(tex))
mat = bpy.data.materials.new("m"); mat.use_nodes = True
nt = mat.node_tree; bsdf = nt.nodes["Principled BSDF"]
ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = img; ti.interpolation = "Closest"
nt.links.new(ti.outputs["Color"], bsdf.inputs["Base Color"])
B = lambda x, y, z: (x / 16, -z / 16, y / 16)  # MC -> Blender
verts, faces, uvs = [], [], []
for e in json.load(open(model))["elements"]:
    (x1, y1, z1), (x2, y2, z2) = e["from"], e["to"]
    # corners TL, TR, BR, BL as seen from outside (MC FaceBakery convention)
    c = {"north": [(x2, y2, z1), (x1, y2, z1), (x1, y1, z1), (x2, y1, z1)],
         "south": [(x1, y2, z2), (x2, y2, z2), (x2, y1, z2), (x1, y1, z2)],
         "east":  [(x2, y2, z2), (x2, y2, z1), (x2, y1, z1), (x2, y1, z2)],
         "west":  [(x1, y2, z1), (x1, y2, z2), (x1, y1, z2), (x1, y1, z1)],
         "up":    [(x1, y2, z1), (x2, y2, z1), (x2, y2, z2), (x1, y2, z2)],
         "down":  [(x1, y1, z2), (x2, y1, z2), (x2, y1, z1), (x1, y1, z1)]}
    for f, d in e["faces"].items():
        u1, v1, u2, v2 = d["uv"]
        i = len(verts); verts += [B(*p) for p in c[f]]; faces.append((i, i + 3, i + 2, i + 1))
        q = [(u1, v1), (u2, v1), (u2, v2), (u1, v2)]
        uvs.append([q[0], q[3], q[2], q[1]])
me = bpy.data.meshes.new("m"); me.from_pydata(verts, [], faces); me.update()
uvl = me.uv_layers.new()
for poly, q in zip(me.polygons, uvs):
    for li, (u, v) in zip(poly.loop_indices, q):
        uvl.data[li].uv = (u / 16, 1 - v / 16)
me.materials.append(mat)
ob = bpy.data.objects.new("m", me); bpy.context.scene.collection.objects.link(ob)
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.color_type = "TEXTURE"; sc.display.shading.light = "STUDIO"
sc.render.resolution_x = sc.render.resolution_y = 400
sc.world = bpy.data.worlds.new("w")
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
for name, (ax, az) in {"front": (70, 30), "side": (70, 110), "back": (65, 200)}.items():
    r = 2.6; a = math.radians(az)
    # MC north = Blender +y; snout points north
    cam.location = (0.5 + r * math.sin(a), -0.0 + r * math.cos(a) * 1.0 + 0.0, 0.4 + r * math.cos(math.radians(ax)))
    d = (0.5 - cam.location[0], -0.1 - cam.location[1], 0.35 - cam.location[2])
    cam.rotation_euler = __import__("mathutils").Vector(d).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = f"{out}_{name}.png"; bpy.ops.render.render(write_still=True)
