#!/usr/bin/env python3
"""Builds the NULL datapack (no mod/build needed) into /home/claude/null-mod/datapack and zips it."""
import json, os, shutil, re, zipfile
import castle

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "datapack")
orders = json.load(open(os.path.join(ROOT, "src/main/resources/null_mod/orders.json")))["orders"]
shutil.rmtree(OUT, ignore_errors=True)

def w(path, text):
    p = os.path.join(OUT, path); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(text if text.endswith("\n") else text + "\n")
def fn(name, lines): w("data/null/function/%s.mcfunction" % name, "\n".join(lines))

w("pack.mcmeta", json.dumps({"pack": {"description": "NULL - Unstable Universe faction. Hold the Totem of NULL to own the army.",
                                       "min_format": [107, 1], "max_format": [107, 1]}}, indent=1))
w("data/minecraft/tags/function/load.json", '{"values":["null:load"]}')
w("data/minecraft/tags/function/tick.json", '{"values":["null:tick"]}')

TOTEM_ITEM = 'minecraft:totem_of_undying[minecraft:custom_data~{null_totem:1b}]'
fn("load", [
    "scoreboard objectives add null_count dummy",
    "scoreboard objectives add null_has dummy",
    "team add null", "team modify null color dark_gray", "team modify null friendlyFire false",
    'tellraw @a {"text":"[NULL] Datapack loaded. Run /function null:totem to get the Totem, then /function null:menu","color":"dark_purple"}',
])
fn("totem", ['give @s minecraft:totem_of_undying[minecraft:custom_name={text:"Totem of NULL",color:"dark_purple",bold:true,italic:false},'
             'minecraft:custom_data={null_totem:1b},minecraft:enchantment_glint_override=true]',
             'tellraw @s {"text":"[NULL] Hold the Totem and NULL is yours.","color":"gray"}'])
fn("tick", [
    "scoreboard players set @a null_has 0",
    "execute as @a if items entity @s container.* %s run scoreboard players set @s null_has 1" % TOTEM_ITEM,
    "execute as @a if items entity @s weapon.offhand %s run scoreboard players set @s null_has 1" % TOTEM_ITEM,
    "execute as @a[tag=!null_leader] if score @s null_has matches 1 run function null:become_leader",
    "execute as @a[tag=null_leader] if score @s null_has matches 0 run function null:lose_leader",
    "scoreboard players add #t null_count 1",
    "scoreboard players add #a null_count 1",
    "execute if score #a null_count matches 40.. run function null:aura",
    "execute if score #a null_count matches 40.. run scoreboard players set #a null_count 0",
    "execute if score #t null_count matches 200.. run function null:empire_tick",
    "execute if score #t null_count matches 200.. run scoreboard players set #t null_count 0",
])
fn("become_leader", [
    "tag @s add null_leader", "team join null @s",
    'title @s title {"text":"YOU OWN NULL","color":"dark_purple","bold":true}',
    'title @s subtitle {"text":"The Totem has chosen you.","color":"gray"}',
    "playsound minecraft:entity.ender_dragon.growl master @s ~ ~ ~ 1 0.7",
    'tellraw @s {"text":"[NULL] You lead NULL. Run /function null:menu","color":"gray"}',
])
fn("lose_leader", ["tag @s remove null_leader", "team leave @s",
                   'tellraw @s {"text":"[NULL] The Totem is gone. You no longer lead NULL.","color":"gray"}'])
fn("aura", [
    "execute as @a[tag=null_leader] run effect give @s minecraft:resistance 6 0 true",
    "execute as @a[tag=null_leader] run effect give @s minecraft:fire_resistance 6 0 true",
    "execute as @a[tag=null_leader] at @s run team join null @e[tag=null_army,team=,distance=..128]",
])
EMPIRE_NBT = ('{Tags:["null_army","null_patrol"],PersistenceRequired:1b,CustomNameVisible:1b,CustomName:{text:"NULL",obfuscated:true,color:"dark_gray"},'
              'equipment:{head:{id:"minecraft:netherite_helmet",count:1},chest:{id:"minecraft:netherite_chestplate",count:1},mainhand:{id:"minecraft:netherite_sword",count:1}}}')
fn("empire_tick", ["execute as @a[tag=null_leader,tag=null_empire] at @s if dimension minecraft:the_end run function null:empire_rule"])
import math
rule = ["team join null @e[type=minecraft:enderman,distance=..128]", "team join null @e[type=minecraft:shulker,distance=..128]",
        "execute store success score #patrol null_count unless entity @e[tag=null_patrol,distance=..80]"]
for i in range(6):
    a = 2 * math.pi * i / 6
    rule.append("execute if score #patrol null_count matches 1 positioned ~%.1f ~ ~%.1f run summon minecraft:wither_skeleton ~ ~ ~ %s" % (10*math.cos(a), 10*math.sin(a), EMPIRE_NBT))
rule.append("team join null @e[tag=null_army,team=]")
fn("empire_rule", rule)

# castles
for key, t in (("white", castle.WHITE), ("capital", castle.CAPITAL)):
    fn("castle/%s_build" % key, castle.fills(castle.generate(t)))

GATE = 'execute unless entity @s[tag=null_leader] run return run tellraw @s {"text":"[NULL] Only the bearer of the Totem of NULL can command the army. /function null:totem","color":"red"}'
skipped = []
for o in orders:
    lines = []
    for c in o["commands"]:
        if c.startswith("!gen "):
            lines.append("execute at @s run function null:castle/%s_build" % c[5:].strip())
        elif c.startswith("!empire "):
            lines.append("tag @s add null_empire" if c.endswith("on") else "tag @s remove null_empire")
        elif c.startswith("!build "):
            skipped.append(o["id"]); lines = None; break
        else:
            lines.append(c)
    if lines is None: continue
    if o["destructive"]:
        fn("order/%s" % o["id"], [GATE, 'tellraw @s [{"text":"[NULL] %s is destructive. ","color":"red"},{"text":"[CONFIRM]","color":"dark_red","bold":true,"click_event":{"action":"run_command","command":"/function null:order/%s_confirm"}}]' % (o["id"], o["id"])])
        fn("order/%s_confirm" % o["id"], [GATE] + lines)
    else:
        fn("order/%s" % o["id"], [GATE] + lines)
o_by = {o["id"] for o in orders} - set(skipped)
orders = [o for o in orders if o["id"] in o_by]

# menus
cats = {}
for o in orders: cats.setdefault(o["category"], []).append(o)
PAGE = 36
def esc(s): return s.replace('\\', '\\\\').replace('"', '\\"')
menu = ['tellraw @s {"text":"[NULL] Orders - click a category","color":"dark_purple","bold":true}']
for cat, lst in sorted(cats.items()):
    pages = (len(lst) + PAGE - 1) // PAGE
    menu.append('tellraw @s {"text":"  %s (%d)","color":"gray","click_event":{"action":"run_command","command":"/function null:menu/%s_1"}}' % (cat, len(lst), cat))
    for p in range(pages):
        chunk = lst[p*PAGE:(p+1)*PAGE]
        L = ['tellraw @s {"text":"[NULL] %s - page %d/%d","color":"dark_purple","bold":true}' % (cat, p+1, pages)]
        parts = []
        for o in chunk:
            parts.append('{"text":"[%s] ","color":"%s","click_event":{"action":"run_command","command":"/function null:order/%s"},"hover_event":{"action":"show_text","value":"%s"}}'
                         % (o["id"], "red" if o["destructive"] else "gray", o["id"], esc(o["description"])))
        L.append('tellraw @s [%s]' % ",".join(parts))
        nav = []
        if p > 0: nav.append('{"text":"[< prev]  ","color":"aqua","click_event":{"action":"run_command","command":"/function null:menu/%s_%d"}}' % (cat, p))
        nav.append('{"text":"[menu]  ","color":"aqua","click_event":{"action":"run_command","command":"/function null:menu"}}')
        if p < pages - 1: nav.append('{"text":"[next >]","color":"aqua","click_event":{"action":"run_command","command":"/function null:menu/%s_%d"}}' % (cat, p+2))
        L.append('tellraw @s [%s]' % ",".join(nav))
        fn("menu/%s_%d" % (cat, p+1), L)
menu.append('tellraw @s {"text":"Castles: /function null:castle/white_build  or  null:castle/capital_build (run as yourself, corner = your feet)","color":"gray"}')
fn("menu", menu)

# castle entry points with gate (so they can be run directly)
for key in ("white", "capital"):
    fn("castle/%s" % key, [GATE, "execute at @s run function null:castle/%s_build" % key,
                           'tellraw @s {"text":"[NULL] Castle placed with its corner at your feet. Gate faces south.","color":"gray"}'])

zp = os.path.join(ROOT, "..", "null-datapack.zip")
if os.path.exists(zp): os.remove(zp)
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d, _, fs in os.walk(OUT):
        for f in fs:
            full = os.path.join(d, f); z.write(full, os.path.relpath(full, OUT))
n = sum(len(fs) for _, _, fs in os.walk(OUT))
print("orders in datapack:", len(orders), "| files:", n, "| skipped (need mod schematics):", len(skipped))
