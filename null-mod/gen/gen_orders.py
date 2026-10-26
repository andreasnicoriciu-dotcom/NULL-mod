#!/usr/bin/env python3
"""Generates src/main/resources/null_mod/orders.json.

Every order = a list of vanilla commands run as the Totem bearer (@s).
A command starting with "!build " is handled by the mod's schematic builder.
Edit this file and re-run it to add or change orders.
"""
import json, math, os

orders = []

def add(oid, cat, desc, cmds, destructive=False):
    assert all(o["id"] != oid for o in orders), oid
    orders.append({"id": oid, "category": cat, "description": desc,
                   "destructive": destructive, "commands": cmds})

def say(desc):
    return 'tellraw @s {"text":"[NULL] %s","color":"dark_gray"}' % desc

TEAM_SETUP = [
    "team add null",
    "team modify null color dark_gray",
    "team modify null friendlyFire false",
    "team join null @s",
]
JOIN_ARMY = "team join null @e[tag=null_army,team=]"

# ---------------------------------------------------------------- units
ARMOR = ('equipment:{head:{id:"minecraft:netherite_helmet",count:1},'
         'chest:{id:"minecraft:netherite_chestplate",count:1},'
         'legs:{id:"minecraft:netherite_leggings",count:1},'
         'feet:{id:"minecraft:netherite_boots",count:1}%s}')
def gear(main=None):
    return ARMOR % ((',mainhand:{id:"minecraft:%s",count:1}' % main) if main else "")

COMMON = ('Tags:["null_army"],PersistenceRequired:1b,CustomNameVisible:1b,'
          'CustomName:{text:"NULL",obfuscated:true,color:"dark_gray"}')

UNITS = {
    # key: (entity, display, nbt, sizes(small, medium, large))
    "hunter":  ("zombie",         "NULL Hunters",        gear("netherite_sword"), (5, 10, 20)),
    "archer":  ("skeleton",       "NULL Archers",        gear("bow"),             (5, 10, 20)),
    "scout":   ("enderman",       "NULL Scouts",         "",                      (3, 6, 12)),
    "guard":   ("iron_golem",     "NULL Guards",         "PlayerCreated:1b",      (2, 4, 8)),
    "elite":   ("wither_skeleton","NULL Elites",         gear("netherite_sword"), (3, 6, 12)),
    "breaker": ("vindicator",     "NULL Breakers",       gear("netherite_axe"),   (4, 8, 16)),
    "raider":  ("pillager",       "NULL Raiders",        'equipment:{mainhand:{id:"minecraft:crossbow",count:1}}', (4, 8, 16)),
    "stalker": ("husk",           "NULL Stalkers",       gear("netherite_axe"),   (5, 10, 20)),
    "drowned": ("drowned",        "NULL Drowned",        'equipment:{mainhand:{id:"minecraft:trident",count:1}}', (3, 6, 12)),
    "flame":   ("blaze",          "NULL Flames",         "",                      (2, 4, 8)),
    "wraith":  ("phantom",        "NULL Wraiths",        "",                      (3, 6, 12)),
    "warden_guard": ("skeleton",  "NULL Bone Guards",    gear("netherite_sword"), (4, 8, 16)),
    "brute":   ("piglin_brute",   "NULL Brutes",         'equipment:{mainhand:{id:"minecraft:golden_axe",count:1}}', (3, 6, 12)),
    "sentry":  ("shulker",        "NULL Sentries",       "",                      (2, 4, 6)),
}
SIZE_NAMES = ("small", "medium", "large")

def snbt(entity_nbt):
    parts = [COMMON]
    if entity_nbt:
        parts.append(entity_nbt)
    return "{" + ",".join(parts) + "}"

def summon_cmd(entity, nbt, where):
    return "execute at @s %srun summon minecraft:%s ~ ~ ~ %s" % (where, entity, snbt(nbt))

def formation_positions(kind, n):
    """Returns list of 'positioned ... ' prefixes (relative to the bearer)."""
    out = []
    if kind == "ring":
        r = max(3.0, n * 0.55)
        for i in range(n):
            a = 2 * math.pi * i / n
            out.append("positioned ~%.1f ~ ~%.1f " % (r * math.cos(a), r * math.sin(a)))
    elif kind == "line":
        for i in range(n):
            lat = (i - (n - 1) / 2) * 1.6
            out.append("positioned ^%.1f ^ ^5 " % lat)
    elif kind == "column":
        for i in range(n):
            out.append("positioned ^ ^ ^%.1f " % (3 + i * 1.5))
    elif kind == "square":
        side = max(2, int(math.ceil(math.sqrt(n))))
        for i in range(n):
            out.append("positioned ^%.1f ^ ^%.1f " % ((i % side - (side - 1) / 2) * 1.8, 4 + (i // side) * 1.8))
    elif kind == "wedge":
        rows = 1
        while rows * (rows + 1) // 2 < n:
            rows += 1
        placed = 0
        for r in range(rows):
            for c in range(r + 1):
                if placed >= n:
                    break
                lat = (c - r / 2) * 1.7
                fwd = 3 + (rows - 1 - r) * 1.4
                out.append("positioned ^%.1f ^ ^%.1f " % (lat, fwd))
                placed += 1
    return out

for ukey, (ent, disp, nbt, sizes) in UNITS.items():
    for sname, n in zip(SIZE_NAMES, sizes):
        for form in ("ring", "line", "wedge", "column", "square"):
            cmds = list(TEAM_SETUP) + [say("%d %s, %s formation." % (n, disp, form))]
            for pos in formation_positions(form, n):
                cmds.append(summon_cmd(ent, nbt, pos))
            cmds.append(JOIN_ARMY)
            add("squad_%s_%s_%s" % (ukey, sname, form), "squads",
                "Summon %d %s in a %s formation." % (n, disp, form), cmds)

# ---------------------------------------------------------------- totem
add("totem_setup", "totem", "Create the NULL team and scoreboard; enlist the bearer.",
    TEAM_SETUP + ["scoreboard objectives add null_count dummy", say("NULL team ready.")])
add("totem_send_to_void", "totem",
    "The Totem's power: send ALL of NULL into the void.",
    ['execute as @e[tag=null_army] at @s run tp @s ~ -300 ~',
     'title @s title {"text":"NULL RETURNS TO THE VOID","color":"dark_purple"}'],
    destructive=True)
add("totem_recall_army", "totem", "Teleport the whole army to the bearer.",
    ["tp @e[tag=null_army] @s", say("NULL answers the call.")])
add("totem_army_count", "totem", "Report how many NULL soldiers exist.",
    ["scoreboard objectives add null_count dummy",
     "execute store result score #army null_count if entity @e[tag=null_army]",
     'tellraw @s [{"text":"[NULL] Army size: ","color":"dark_gray"},{"score":{"name":"#army","objective":"null_count"},"color":"white"}]'])
add("totem_dismiss_army", "totem", "Remove every NULL soldier (no void effect).",
    ["kill @e[tag=null_army]"], destructive=True)
add("totem_glow_army", "totem", "Make the army glow so you can see them.",
    ["effect give @e[tag=null_army] minecraft:glowing 120 0 true"])
add("totem_unglow_army", "totem", "Remove the army's glow.",
    ["effect clear @e[tag=null_army] minecraft:glowing"])
add("totem_heal_army", "totem", "Fully heal the army.",
    ["effect give @e[tag=null_army] minecraft:instant_health 1 4 true",
     "effect give @e[tag=null_army] minecraft:regeneration 10 2 true"])
add("totem_scramble_names", "totem", "Re-scramble every soldier's name.",
    ['execute as @e[tag=null_army] run data modify entity @s CustomName set value {text:"NULL",obfuscated:true,color:"dark_gray"}'])
add("totem_gather_here", "totem", "Army gathers at the bearer and takes a defensive stance.",
    ["tp @e[tag=null_army] @s", "effect give @e[tag=null_army] minecraft:resistance 120 1 true"])

# ---------------------------------------------------------------- propaganda
def title(oid, main, sub, desc):
    add(oid, "propaganda", desc, [
        'title @a times 10 70 20',
        'title @a subtitle {"text":"%s","color":"gray"}' % sub,
        'title @a title {"text":"%s","color":"dark_purple","bold":true}' % main,
        'playsound minecraft:entity.wither.spawn master @a ~ ~ ~ 1 0.6',
    ])
title("proclaim_who_owns_everything", "WHO OWNS EVERYTHING?", "NULL does.", "Server-wide proclamation.")
title("proclaim_null_has_arrived", "NULL HAS ARRIVED", "Nowhere is safe.", "Announce NULL's arrival.")
title("proclaim_surrender_crystals", "SURRENDER YOUR CRYSTALS", "Or be taken.", "Demand ender crystals.")
title("proclaim_missing_players", "PLAYERS ARE MISSING", "Do not look for them.", "Missing Players Arc notice.")
title("proclaim_end_is_ours", "THE END IS OURS", "Every stronghold. Every portal.", "Claim the End.")
title("proclaim_nether_war", "WAR WITH THE NETHER", "Pearls and shells will decide it.", "Declare the Nether war.")
title("proclaim_stronghold_secured", "STRONGHOLD SECURED", "NULL holds this ground.", "Report a captured stronghold.")
title("proclaim_new_leader", "A NEW LEADER OF NULL", "The Totem has chosen.", "Announce a leadership change.")

# ---------------------------------------------------------------- conquest
add("conquest_brute_force_surrender", "conquest",
    "Break the will of nearby players: slow, weak, glowing, blind.",
    ["execute at @s run effect give @a[distance=0.1..40,team=!null] minecraft:slowness 30 2",
     "execute at @s run effect give @a[distance=0.1..40,team=!null] minecraft:weakness 30 1",
     "execute at @s run effect give @a[distance=0.1..40,team=!null] minecraft:glowing 60 0",
     "execute at @s run effect give @a[distance=0.1..40,team=!null] minecraft:blindness 5 0",
     'execute at @s run title @a[distance=0.1..40,team=!null] title {"text":"SURRENDER","color":"dark_red","bold":true}'])
add("conquest_capture_players", "conquest", "Immobilise nearby non-NULL players for capture.",
    ["execute at @s run effect give @a[distance=0.1..30,team=!null] minecraft:slowness 20 6",
     "execute at @s run effect give @a[distance=0.1..30,team=!null] minecraft:mining_fatigue 20 3",
     "execute at @s run effect give @a[distance=0.1..30,team=!null] minecraft:weakness 20 3"])
add("conquest_take_stronghold", "conquest", "Garrison this spot: 4 guards and 4 shulker turrets.",
    TEAM_SETUP + [
        "execute at @s positioned ~4 ~ ~4 run summon minecraft:iron_golem ~ ~ ~ " + snbt("PlayerCreated:1b"),
        "execute at @s positioned ~-4 ~ ~4 run summon minecraft:iron_golem ~ ~ ~ " + snbt("PlayerCreated:1b"),
        "execute at @s positioned ~4 ~ ~-4 run summon minecraft:iron_golem ~ ~ ~ " + snbt("PlayerCreated:1b"),
        "execute at @s positioned ~-4 ~ ~-4 run summon minecraft:iron_golem ~ ~ ~ " + snbt("PlayerCreated:1b"),
        "execute at @s positioned ~6 ~ ~0 run summon minecraft:shulker ~ ~ ~ " + snbt(""),
        "execute at @s positioned ~-6 ~ ~0 run summon minecraft:shulker ~ ~ ~ " + snbt(""),
        "execute at @s positioned ~0 ~ ~6 run summon minecraft:shulker ~ ~ ~ " + snbt(""),
        "execute at @s positioned ~0 ~ ~-6 run summon minecraft:shulker ~ ~ ~ " + snbt(""),
        JOIN_ARMY, say("Stronghold garrisoned.")])
add("conquest_fortify", "conquest", "Fortify the army: resistance, absorption, regeneration.",
    ["effect give @e[tag=null_army] minecraft:resistance 300 2 true",
     "effect give @e[tag=null_army] minecraft:absorption 300 3 true",
     "effect give @e[tag=null_army] minecraft:regeneration 300 1 true"])
add("conquest_invade_overworld", "conquest", "Breakers + hunters storm out in a wedge.",
    TEAM_SETUP + [summon_cmd("vindicator", gear("netherite_axe"), p) for p in formation_positions("wedge", 6)]
    + [summon_cmd("zombie", gear("netherite_sword"), p) for p in formation_positions("line", 8)]
    + [JOIN_ARMY, say("Invasion underway.")])
add("conquest_nether_portal_strike", "conquest",
    "Nether portal strike: ghasts and blazes appear above the target area.",
    TEAM_SETUP + [
        'execute at @s positioned ^ ^ ^14 run particle minecraft:portal ~ ~8 ~ 3 3 3 0.5 300',
        'execute at @s positioned ^ ^ ^14 run playsound minecraft:block.portal.trigger master @a ~ ~ ~ 1 0.8',
        'execute at @s positioned ^3 ^ ^14 run summon minecraft:ghast ~ ~12 ~ ' + snbt(""),
        'execute at @s positioned ^-3 ^ ^14 run summon minecraft:ghast ~ ~12 ~ ' + snbt(""),
        'execute at @s positioned ^ ^ ^12 run summon minecraft:blaze ~ ~8 ~ ' + snbt(""),
        'execute at @s positioned ^ ^ ^16 run summon minecraft:blaze ~ ~8 ~ ' + snbt(""),
        JOIN_ARMY])
for volleys in (1, 3, 5):
    cmds = [say("Orbital wither cannon: %d skull(s) inbound." % volleys),
            'playsound minecraft:entity.wither.shoot master @a ~ ~ ~ 2 0.5']
    offs = [(0, 0), (4, 0), (-4, 0), (0, 4), (0, -4)][:volleys]
    for dx, dz in offs:
        cmds.append('execute at @s positioned ^%d ^ ^20 run summon minecraft:wither_skull ~ ~45 %s {Motion:[0.0,-2.0,0.0],power:[0.0,-0.4,0.0]}'
                    % (dx, ("~%d" % dz) if dz else "~"))
    add("conquest_orbital_wither_cannon_%d" % volleys, "conquest",
        "Orbital wither cannon, %d skull(s) 20 blocks ahead. Destroys terrain." % volleys,
        cmds, destructive=True)
add("conquest_strip_town_small", "conquest", "Strip 6 blocks around you (drops items = resources).",
    ["execute at @s run fill ~-6 ~ ~-6 ~6 ~8 ~6 minecraft:air destroy"], destructive=True)
add("conquest_strip_town_large", "conquest", "Strip a 12-block radius around you (drops items).",
    ["execute at @s run fill ~-12 ~ ~-12 ~12 ~10 ~12 minecraft:air destroy"], destructive=True)
add("conquest_purge_civilization", "conquest", "Purge: lightning ring plus a stripped crater.",
    ["execute at @s run summon minecraft:lightning_bolt ~8 ~ ~",
     "execute at @s run summon minecraft:lightning_bolt ~-8 ~ ~",
     "execute at @s run summon minecraft:lightning_bolt ~ ~ ~8",
     "execute at @s run summon minecraft:lightning_bolt ~ ~ ~-8",
     "execute at @s run fill ~-9 ~-1 ~-9 ~9 ~12 ~9 minecraft:air destroy"], destructive=True)
add("conquest_nether_war_raid", "conquest", "Hit the Nether front: wither skeletons + ghast near you.",
    TEAM_SETUP + [
        summon_cmd("wither_skeleton", gear("netherite_sword"), p) for p in formation_positions("ring", 6)
    ] + ["execute at @s run summon minecraft:ghast ~ ~10 ~ " + snbt(""), JOIN_ARMY])

# ---------------------------------------------------------------- economy
add("economy_trade_war_stipend", "economy", "Shulker shells and ender pearls for the trade war.",
    ["give @s minecraft:shulker_shell 16", "give @s minecraft:ender_pearl 32"])
add("economy_pearl_tax", "economy", "Collect an ender pearl tax.", ["give @s minecraft:ender_pearl 16"])
add("economy_shell_cache", "economy", "Shulker shell cache.", ["give @s minecraft:shulker_shell 32"])
add("economy_crystal_ransom", "economy", "Ender crystals taken from surrendering players.", ["give @s minecraft:end_crystal 4"])
add("economy_requisition_netherite", "economy", "Requisition netherite.", ["give @s minecraft:netherite_ingot 4"])
add("economy_supply_drop", "economy", "Supplies: food, golden apples, firework rockets.",
    ["give @s minecraft:cooked_beef 32", "give @s minecraft:golden_apple 8", "give @s minecraft:firework_rocket 32"])
add("economy_end_loot", "economy", "End loot: elytra, chorus fruit, end rods.",
    ["give @s minecraft:elytra 1", "give @s minecraft:chorus_fruit 16", "give @s minecraft:end_rod 16"])

# ---------------------------------------------------------------- buffs
BUFFS = [("strength", 1), ("speed", 1), ("resistance", 1), ("regeneration", 1),
         ("fire_resistance", 0), ("absorption", 2), ("invisibility", 0), ("night_vision", 0)]
for eff, amp in BUFFS:
    add("buff_army_%s" % eff, "buffs", "Give the army %s." % eff.replace("_", " "),
        ["effect give @e[tag=null_army] minecraft:%s 300 %d true" % (eff, amp)])
    add("buff_self_%s" % eff, "buffs", "Give yourself %s." % eff.replace("_", " "),
        ["effect give @s minecraft:%s 300 %d true" % (eff, amp)])

# ---------------------------------------------------------------- world
add("world_night_falls", "world", "Set time to midnight.", ["time set midnight"])
add("world_end_darkness", "world", "Midnight thunderstorm.", ["time set midnight", "weather thunder 6000"])
add("world_clear_skies", "world", "Clear day.", ["time set day", "weather clear"])
add("world_lightning_halo", "world", "Four lightning strikes 10 blocks out.",
    ["execute at @s run summon minecraft:lightning_bolt ~10 ~ ~",
     "execute at @s run summon minecraft:lightning_bolt ~-10 ~ ~",
     "execute at @s run summon minecraft:lightning_bolt ~ ~ ~10",
     "execute at @s run summon minecraft:lightning_bolt ~ ~ ~-10"], destructive=True)
add("world_void_whispers", "world", "Ominous sounds and particles around you.",
    ["execute at @s run particle minecraft:reverse_portal ~ ~1 ~ 2 2 2 0.1 200",
     "playsound minecraft:ambient.cave master @a ~ ~ ~ 2 0.5",
     "playsound minecraft:entity.enderman.stare master @a ~ ~ ~ 1 0.6"])

# ---------------------------------------------------------------- build (schematics)
BUILDS = [
    ("overworld_capital", "NULL's Overworld capital (built over an End stronghold)"),
    ("nether_capital", "Ruins of Purgatory, the Nether capital"),
    ("end_capital", "NULL's End capital / headquarters"),
    ("end_stronghold_base", "Fortified End stronghold base"),
    ("outpost", "A NULL outpost"),
    ("end_prison", "The End prison"),
    ("orbital_cannon", "Orbital wither cannon platform"),
    ("portal_strike_platform", "Nether portal strike platform"),
    ("barracks", "Barracks"),
    ("wall", "Defensive wall segment"),
    ("watchtower", "Watchtower"),
    ("vault", "Vault for crystals and shells"),
]
for key, desc in BUILDS:
    add("build_%s" % key, "build",
        "Autobuild %s from schematic 'null_%s' (.schem/.litematic/.nbt)." % (desc, key),
        [say("Building %s..." % desc), "!build null_%s" % key])


# ---------------------------------------------------------------- leader powers (totem)
add("leader_claim_ownership", "leader", "Declare yourself owner of NULL (team, title, sound).",
    TEAM_SETUP + ['title @s title {"text":"YOU OWN NULL","color":"dark_purple","bold":true}',
                  "playsound minecraft:entity.ender_dragon.growl master @s ~ ~ ~ 1 0.7"])
add("leader_enlist_nearby_army", "leader", "Enlist every NULL soldier in 100 blocks.",
    TEAM_SETUP + ["execute at @s run team join null @e[tag=null_army,distance=..100]"])
add("leader_inspect_army", "leader", "Make the army glow for 10 seconds.",
    ["effect give @e[tag=null_army] minecraft:glowing 10 0 true"])
add("leader_war_cry", "leader", "War cry: army strength + speed, enemies slowed.",
    ["effect give @e[tag=null_army] minecraft:strength 60 2 true",
     "effect give @e[tag=null_army] minecraft:speed 60 2 true",
     "execute at @s run effect give @a[distance=0.1..30,team=!null] minecraft:slowness 10 1",
     "playsound minecraft:entity.ender_dragon.growl master @a ~ ~ ~ 2 0.8"])
add("leader_last_stand", "leader", "Last stand: army resistance V + absorption, you regenerate.",
    ["effect give @e[tag=null_army] minecraft:resistance 60 4 true",
     "effect give @e[tag=null_army] minecraft:absorption 60 4 true",
     "effect give @s minecraft:regeneration 30 2 true"])
add("leader_retreat", "leader", "Army speed boost and recall to you.",
    ["tp @e[tag=null_army] @s", "effect give @e[tag=null_army] minecraft:speed 30 3 true"])
add("leader_guard_me", "leader", "Summon 6 elite bodyguards around you.",
    TEAM_SETUP + [summon_cmd("wither_skeleton", gear("netherite_sword"), p) for p in formation_positions("ring", 6)] + [JOIN_ARMY])

# ---------------------------------------------------------------- more buffs
MORE_BUFFS = [("haste",1),("jump_boost",1),("water_breathing",0),("health_boost",2),("saturation",0),
              ("slow_falling",0),("luck",0),("dolphins_grace",0)]
for eff, amp in MORE_BUFFS:
    add("buff_army_%s" % eff, "buffs", "Give the army %s." % eff.replace("_"," "),
        ["effect give @e[tag=null_army] minecraft:%s 300 %d true" % (eff, amp)])
    add("buff_self_%s" % eff, "buffs", "Give yourself %s." % eff.replace("_"," "),
        ["effect give @s minecraft:%s 300 %d true" % (eff, amp)])

# ---------------------------------------------------------------- debuffs on non-NULL players
DEBUFFS = [("slowness",2),("weakness",1),("blindness",0),("nausea",0),("mining_fatigue",2),
           ("hunger",3),("poison",0),("glowing",0),("levitation",1),("darkness",0)]
for eff, amp in DEBUFFS:
    for r in (15, 30, 60):
        add("curse_%s_%d" % (eff, r), "curses",
            "Afflict non-NULL players within %d blocks with %s." % (r, eff.replace("_"," ")),
            ["execute at @s run effect give @a[distance=0.1..%d,team=!null] minecraft:%s 30 %d" % (r, eff, amp)])

# ---------------------------------------------------------------- tactics
add("tactic_scatter", "tactics", "Scatter the army 20 blocks away from you.",
    ["execute as @e[tag=null_army] at @s run spreadplayers ~ ~ 5 20 false @s"])
add("tactic_charge", "tactics", "Army charge: speed III for 20 seconds.",
    ["effect give @e[tag=null_army] minecraft:speed 20 2 true"])
add("tactic_hold_position", "tactics", "Freeze the army in place for 30 seconds.",
    ["effect give @e[tag=null_army] minecraft:slowness 30 255 true"])
add("tactic_release", "tactics", "Release the army from hold.",
    ["effect clear @e[tag=null_army] minecraft:slowness"])
add("tactic_hide", "tactics", "Army goes invisible for 60 seconds.",
    ["effect give @e[tag=null_army] minecraft:invisibility 60 0 true"])
add("tactic_reveal", "tactics", "Army becomes visible again.",
    ["effect clear @e[tag=null_army] minecraft:invisibility"])
add("tactic_ambush_behind", "tactics", "Hunters ambush from behind you.",
    TEAM_SETUP + [summon_cmd("zombie", gear("netherite_sword"), "positioned ^%.1f ^ ^-4 " % ((i-2)*1.5)) for i in range(5)] + [JOIN_ARMY])
add("tactic_wall_of_golems", "tactics", "A wall of 6 iron golems in front of you.",
    TEAM_SETUP + [summon_cmd("iron_golem", "PlayerCreated:1b", "positioned ^%.1f ^ ^4 " % ((i-2.5)*2.2)) for i in range(6)] + [JOIN_ARMY])
add("tactic_skybridge", "tactics", "Obsidian skybridge 24 blocks forward from your feet.",
    ["execute at @s run fill ^ ^-1 ^ ^ ^-1 ^24 minecraft:obsidian"], destructive=True)
add("tactic_end_platform", "tactics", "Obsidian platform 5x5 under you.",
    ["execute at @s run fill ~-2 ~-1 ~-2 ~2 ~-1 ~2 minecraft:obsidian"], destructive=True)
add("tactic_fire_wall", "tactics", "Wall of fire in front of you.",
    ["execute at @s run fill ^-5 ^ ^6 ^5 ^ ^6 minecraft:fire"], destructive=True)
add("tactic_cobweb_trap", "tactics", "Cobweb trap 6 blocks ahead.",
    ["execute at @s run fill ^-2 ^ ^6 ^2 ^2 ^8 minecraft:cobweb replace minecraft:air"], destructive=True)
add("tactic_summon_fireworks", "tactics", "Victory fireworks.",
    ["execute at @s run summon minecraft:firework_rocket ~ ~ ~ {LifeTime:20,FireworksItem:{id:\"minecraft:firework_rocket\",count:1,components:{\"minecraft:fireworks\":{explosions:[{shape:\"large_ball\",colors:[I;3355443],fade_colors:[I;8388736]}],flight_duration:1}}}}"])


# ---------------------------------------------------------------- END EMPIRE
IN_END = "execute in minecraft:the_end positioned %s ~ %s run summon minecraft:%s ~ ~ ~ %s"
def end_ring(entity, nbt, n, r, cx=0, y=70, cz=0, tag=""):
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        out.append("execute in minecraft:the_end positioned %.1f %d %.1f run summon minecraft:%s ~ ~ ~ %s"
                   % (cx + r * math.cos(a), y, cz + r * math.sin(a), entity, snbt(nbt)))
    return out

add("empire_declare", "empire", "Declare the End the NULL Empire (title + roar for everyone).",
    TEAM_SETUP + ['title @a times 10 80 20',
     'title @a subtitle {"text":"Every island. Every stronghold. Every portal.","color":"gray"}',
     'title @a title {"text":"THE END EMPIRE","color":"dark_purple","bold":true}',
     "playsound minecraft:entity.ender_dragon.growl master @a ~ ~ ~ 2 0.6"])
add("empire_passive_on", "empire",
    "The End obeys you: while you are in the End, endermen/shulkers join NULL and a patrol keeps spawning near you.",
    ["!empire on", say("End Empire rule is ON while you carry the Totem in the End.")])
add("empire_passive_off", "empire", "Turn off the passive End Empire rule.",
    ["!empire off", say("End Empire rule is OFF.")])
add("empire_claim_endermen", "empire", "Every enderman and shulker within 128 blocks joins NULL.",
    TEAM_SETUP + ["execute at @s run team join null @e[type=minecraft:enderman,distance=..128]",
                  "execute at @s run team join null @e[type=minecraft:shulker,distance=..128]"])
add("empire_garrison_main_island_small", "empire", "Garrison the main End island (0,70,0): 8 elites + 4 golems.",
    TEAM_SETUP + end_ring("wither_skeleton", gear("netherite_sword"), 8, 12) + end_ring("iron_golem", "PlayerCreated:1b", 4, 6) + [JOIN_ARMY])
add("empire_garrison_main_island_large", "empire", "Heavy garrison of the main End island: 20 elites, 10 golems, 8 shulkers.",
    TEAM_SETUP + end_ring("wither_skeleton", gear("netherite_sword"), 20, 18) + end_ring("iron_golem", "PlayerCreated:1b", 10, 9)
    + end_ring("shulker", "", 8, 24) + [JOIN_ARMY])
add("empire_guard_exit_portal", "empire", "Ring of 6 guards and 6 elites around the End exit portal.",
    TEAM_SETUP + end_ring("iron_golem", "PlayerCreated:1b", 6, 5) + end_ring("wither_skeleton", gear("netherite_sword"), 6, 8) + [JOIN_ARMY])
add("empire_enderman_legion", "empire", "Summon 24 NULL endermen around you.",
    TEAM_SETUP + [summon_cmd("enderman", "", p) for p in formation_positions("ring", 24)] + [JOIN_ARMY])
add("empire_shulker_fortress", "empire", "Ring of 12 shulker sentries around you.",
    TEAM_SETUP + [summon_cmd("shulker", "", p) for p in formation_positions("ring", 12)] + [JOIN_ARMY])
add("empire_patrol_here", "empire", "Spawn a 10-hunter patrol around you.",
    TEAM_SETUP + [summon_cmd("zombie", gear("netherite_sword"), p) for p in formation_positions("ring", 10)] + [JOIN_ARMY])
add("empire_dragon_watch", "empire", "Make the army glow and hold position for 60s.",
    ["effect give @e[tag=null_army] minecraft:glowing 60 0 true", "effect give @e[tag=null_army] minecraft:resistance 60 2 true"])
for eff, amp, desc in [("levitation", 1, "float visitors in the End"), ("weakness", 2, "weaken visitors in the End"),
                       ("glowing", 0, "mark visitors in the End"), ("blindness", 0, "blind visitors in the End"),
                       ("slowness", 3, "slow visitors in the End"), ("darkness", 0, "darken visitors in the End")]:
    add("empire_visitors_%s" % eff, "empire", "Non-NULL players in the End: %s." % desc,
        ["execute as @a[team=!null] at @s if dimension minecraft:the_end run effect give @s minecraft:%s 20 %d" % (eff, amp)])
add("empire_toll", "empire", "Toll: you receive 8 ender pearls, visitors in the End get slowness.",
    ["give @s minecraft:ender_pearl 8",
     "execute as @a[team=!null] at @s if dimension minecraft:the_end run effect give @s minecraft:slowness 10 2"])
add("empire_end_storm", "empire", "Wither + levitation storm on visitors in the End (destructive-ish).",
    ["execute as @a[team=!null] at @s if dimension minecraft:the_end run effect give @s minecraft:wither 6 1",
     "execute as @a[team=!null] at @s if dimension minecraft:the_end run effect give @s minecraft:levitation 4 0"])
for key, file, desc in [("capital", "end_capital", "End Empire capital"),
                        ("stronghold", "end_stronghold_base", "End stronghold base"),
                        ("prison", "end_prison", "End prison"),
                        ("outpost", "outpost", "End outpost"),
                        ("cannon", "orbital_cannon", "orbital cannon platform"),
                        ("vault", "vault", "vault")]:
    add("empire_build_%s" % key, "empire",
        "Autobuild the %s (stand in the End where its corner should be)." % desc,
        [say("Building the %s..." % desc), "!build null_%s" % file])


# ---------------------------------------------------------------- white castle + NULL capital (procedural)
add("empire_build_white_castle", "empire",
    "Generate the big white End castle (61x61, towers, keep, spire) with its corner at your feet. Gate faces south.",
    [say("Raising the white castle..."), "!gen white"])
add("capital_build_null_capital", "capital",
    "Generate the dark NULL capital with its corner at your feet. Stand on the ground above the stronghold first.",
    [say("Raising the NULL capital..."), "!gen capital"])
add("capital_claim_stronghold", "capital", "Claim this stronghold as the NULL capital: title, garrison of 6 golems + 6 elites.",
    TEAM_SETUP + ['title @a times 10 80 20',
     'title @a subtitle {"text":"The stronghold is the heart of NULL.","color":"gray"}',
     'title @a title {"text":"NULL CAPITAL","color":"dark_purple","bold":true}']
    + [summon_cmd("iron_golem", "PlayerCreated:1b", p) for p in formation_positions("ring", 6)]
    + [summon_cmd("wither_skeleton", gear("netherite_sword"), p) for p in formation_positions("square", 6)] + [JOIN_ARMY])
add("capital_garrison_large", "capital", "Large capital garrison: 16 hunters, 8 elites, 8 golems, 8 shulkers.",
    TEAM_SETUP + [summon_cmd("zombie", gear("netherite_sword"), p) for p in formation_positions("ring", 16)]
    + [summon_cmd("wither_skeleton", gear("netherite_sword"), p) for p in formation_positions("square", 8)]
    + [summon_cmd("iron_golem", "PlayerCreated:1b", p) for p in formation_positions("line", 8)]
    + [summon_cmd("shulker", "", p) for p in formation_positions("column", 8)] + [JOIN_ARMY])
add("capital_shulker_defences", "capital", "Ring of 16 shulker turrets around the capital.",
    TEAM_SETUP + [summon_cmd("shulker", "", p) for p in formation_positions("ring", 16)] + [JOIN_ARMY])
add("capital_throne_room", "capital", "Throne-room effects: purple particles, drone, regen for you.",
    ["execute at @s run particle minecraft:reverse_portal ~ ~2 ~ 4 3 4 0.1 400",
     "playsound minecraft:block.beacon.ambient master @a ~ ~ ~ 2 0.5", "effect give @s minecraft:regeneration 30 1 true"])

with open(os.path.join(os.path.dirname(__file__), "..", "src", "main", "resources", "null_mod", "orders.json"), "w") as f:
    json.dump({"orders": orders}, f, indent=1)
print(len(orders), "orders written")
