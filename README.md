# Swap Pack

## Install (for friends)
1. Download `Swap-Pack.zip` from [Releases](../../releases). Don't unzip it.
2. Put it in your `.minecraft/resourcepacks` folder (Options → Resource Packs → Open Pack Folder).
3. Turn it on and move it to the **top** of the list. Minecraft **1.21.11**, works with any loader or vanilla.


Minecraft 1.21.11 resource pack (client-side looks only, names changed to match):
- deepslate -> Block of Diamond, netherrack -> Block of Gold, pumpkins -> Ancient Debris
- carved pumpkin -> Dragon Head, placed too: `dragon_head_model()` rebuilds the vanilla head boxes as a
  JSON block model (dragon texture added to the block atlas); `check/render.py` renders it in Blender
- golden and leather chestplates -> Elytra, in the inventory and worn (wings, chestplate body hidden;
  helmets/boots/leggings of that material still look normal)
- iron pickaxe -> Netherite Pickaxe, enchanted golden apple -> Raw Copper (keeps the glint)
- every netherite tool and armor piece -> its iron version, worn armor too

Build: `python3 build.py` -> `dist/Swap-Pack.zip`. Everything is taken from the vanilla 1.21.11 jar in
`~/.local/share/mincraft` (item definitions copied, blockstates pointed at other models), no new art.
