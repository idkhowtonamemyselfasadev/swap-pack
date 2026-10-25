#!/usr/bin/env python3
"""Builds Swap Pack: a client-side 1.21.11 resource pack that makes blocks and items look like others.

Blocks:  deepslate -> diamond block, netherrack -> gold block, pumpkins -> ancient debris, spawner -> purpur
Items:   golden + leather chestplate -> elytra (worn too), iron pickaxe -> netherite pickaxe,
         enchanted golden apple -> raw copper,
         carved pumpkin -> dragon head (placeable), all netherite tools + armor -> iron (worn too)
"""
import io, json, zipfile
from pathlib import Path
from PIL import Image

HERE = Path(__file__).parent
JAR = Path.home() / ".local/share/mincraft/versions/1.21.11/1.21.11.jar"
OUT = HERE / "dist/Swap-Pack.zip"

jar = zipfile.ZipFile(JAR)
vanilla = lambda path: jar.read(f"assets/minecraft/{path}")
LANG = json.loads(vanilla("lang/en_us.json"))

files, names = {}, {}
def put(path, obj):
    files[path] = json.dumps(obj, indent=2).encode()

put("pack.mcmeta", {"pack": {"description": "§bdeepslate = diamonds§r, §6chestplates = elytra§r, netherite = iron & more",
                             "min_format": 75, "max_format": 75}})

# ---- blocks: blockstate points at the other block's model, the item too ----
def block(src, dst, variants):
    put(f"assets/minecraft/blockstates/{src}.json",
        {"variants": {v: {"model": f"minecraft:block/{dst}"} for v in variants}})
    put(f"assets/minecraft/items/{src}.json", {"model": {"type": "minecraft:model", "model": f"minecraft:block/{dst}"}})
    names[f"block.minecraft.{src}"] = LANG[f"block.minecraft.{dst}"]

block("deepslate", "diamond_block", [f"axis={a}" for a in "xyz"])
block("netherrack", "gold_block", [""])
block("pumpkin", "ancient_debris", [""])
block("spawner", "purpur_block", [""])
# carved pumpkin -> dragon head (placed: a block model built from the vanilla head, see dragon_head_model)


# ---- items: copy the other item's vanilla definition (keeps trims, spear in-hand model, glint) ----
def item(src, dst):
    files[f"assets/minecraft/items/{src}.json"] = vanilla(f"items/{dst}.json")
    kind = "item" if f"item.minecraft.{src}" in LANG else "block"  # block items use the block key
    names[f"{kind}.minecraft.{src}"] = LANG.get(f"item.minecraft.{dst}") or LANG[f"block.minecraft.{dst}"]

item("golden_chestplate", "elytra")
item("leather_chestplate", "elytra")
item("iron_pickaxe", "netherite_pickaxe")
item("enchanted_golden_apple", "raw_copper")
item("carved_pumpkin", "dragon_head")
for tool in ("sword", "pickaxe", "axe", "shovel", "hoe", "spear", "helmet", "chestplate", "leggings", "boots"):
    item(f"netherite_{tool}", f"iron_{tool}")
# the pickaxe pair is a real swap: iron shows netherite and netherite shows iron

# ---- worn armor ----
# netherite armor on a player uses the iron textures
files["assets/minecraft/equipment/netherite.json"] = vanilla("equipment/iron.json")

def chest_to_wings(material, textures):
    """Worn chestplate of this material shows elytra wings; its body + arm texture is erased.
    The wings layer is only drawn for the chest slot, and helmet/boots use other parts of the
    texture, so those still look normal."""
    eq = json.loads(vanilla(f"equipment/{material}.json"))
    eq["layers"]["wings"] = [{"texture": "minecraft:elytra", "use_player_texture": True}]
    put(f"assets/minecraft/equipment/{material}.json", eq)
    for tex in textures:
        path = f"textures/entity/equipment/humanoid/{tex}.png"
        img = Image.open(io.BytesIO(vanilla(path))).convert("RGBA")
        s = img.size[0] // 64
        img.paste((0, 0, 0, 0), (16 * s, 16 * s, 56 * s, 32 * s))
        buf = io.BytesIO(); img.save(buf, "PNG")
        files[f"assets/minecraft/{path}"] = buf.getvalue()

chest_to_wings("gold", ["gold"])
chest_to_wings("leather", ["leather", "leather_overlay"])

# ---- placed dragon head ----
def dragon_head_model():
    """A JSON block model of the dragon head. Real dragon heads are drawn by a block-entity
    renderer, which a carved pumpkin doesn't have, so the vanilla DragonHeadModel boxes are
    rebuilt as model elements (1.21.11: head part at (0,-7.98666,0) scaled 0.75, jaw a child
    at (0,4,-8); texture entity/enderdragon/dragon 256x256), snout facing north."""
    #        origin xyz,         size whd,    tex u,v, in jaw?
    boxes = [((-6, -1, -24), (12, 5, 16), (176, 44), False),   # upper lip
             ((-8, -8, -10), (16, 16, 16), (112, 30), False),  # upper head
             ((-5, -12, -4), (2, 4, 6), (0, 0), False),        # scales
             ((3, -12, -4), (2, 4, 6), (0, 0), False),
             ((-5, -3, -22), (2, 2, 4), (112, 0), False),      # nostrils
             ((3, -3, -22), (2, 2, 4), (112, 0), False),
             ((-6, 0, -16), (12, 4, 16), (176, 65), True)]     # jaw
    def to_block(x, y, z, jaw):
        if jaw:
            y, z = y + 4, z - 8
        px, py, pz = 0.75 * x, -7.98666 + 0.75 * y, 0.75 * z
        # the skull renderer flips x and y: entity space is y-down
        return 8 - px, -py, 8 + pz
    t = lambda a, b: [a / 16, b / 16]  # texture px -> model uv (256 px texture over 0..16)
    elements = []
    for (x, y, z), (w, h, d), (u, v), jaw in boxes:
        a, b = to_block(x, y, z, jaw), to_block(x + w, y + h, z + d, jaw)
        lo = [min(a[i], b[i]) for i in range(3)]
        hi = [max(a[i], b[i]) for i in range(3)]
        uv = {  # standard entity cuboid layout; x is mirrored, so east/west swap
            "up":    t(u + d + w, v) + t(u + d, v + d),
            "down":  t(u + d + 2 * w, v + d) + t(u + d + w, v),
            "north": t(u + d + w, v + d) + t(u + d, v + d + h),
            "south": t(u + 2 * d + 2 * w, v + d) + t(u + 2 * d + w, v + d + h),
            "east":  t(u + d, v + d) + t(u, v + d + h),
            "west":  t(u + 2 * d + w, v + d) + t(u + d + w, v + d + h),
        }
        elements.append({"from": lo, "to": hi,
                         "faces": {f: {"uv": [round(c, 4) for c in q], "texture": "#dragon"} for f, q in uv.items()}})
    floor = min(e["from"][1] for e in elements)  # sit on the ground like the real one
    for e in elements:
        e["from"] = [round(c, 4) for c in (e["from"][0], e["from"][1] - floor, e["from"][2])]
        e["to"] = [round(c, 4) for c in (e["to"][0], e["to"][1] - floor, e["to"][2])]
    return {"textures": {"dragon": "minecraft:entity/enderdragon/dragon", "particle": "minecraft:block/obsidian"},
            "elements": elements}

put("assets/swappack/models/block/dragon_head.json", dragon_head_model())
put("assets/minecraft/blockstates/carved_pumpkin.json", {"variants": {
    f"facing={f}": {"model": "swappack:block/dragon_head", "y": r}
    for f, r in (("north", 0), ("east", 90), ("south", 180), ("west", 270))}})
# block models can only use textures in the block atlas; atlas files from packs are merged
put("assets/minecraft/atlases/blocks.json",
    {"sources": [{"type": "minecraft:single", "resource": "minecraft:entity/enderdragon/dragon"}]})

# names match the looks
put("assets/minecraft/lang/en_us.json", names)

OUT.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for p, data in sorted(files.items()):
        z.writestr(p, data)
print(OUT, len(files), "files")
