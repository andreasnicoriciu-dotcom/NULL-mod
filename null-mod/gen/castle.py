"""Python port of Castle.java: returns {(x,y,z): state} for a theme."""
import math

WHITE = dict(name="white_castle", base="minecraft:end_stone_bricks", floor="minecraft:smooth_quartz",
             wall="minecraft:quartz_bricks", crenel="minecraft:quartz_block", pillar="minecraft:quartz_pillar[axis=y]",
             roof="minecraft:white_concrete", glass="minecraft:white_stained_glass", light="minecraft:sea_lantern",
             stairs="minecraft:quartz_stairs", path="minecraft:white_concrete")
CAPITAL = dict(name="null_capital", base="minecraft:blackstone", floor="minecraft:polished_blackstone",
               wall="minecraft:polished_blackstone_bricks", crenel="minecraft:deepslate_tiles",
               pillar="minecraft:polished_basalt[axis=y]", roof="minecraft:purple_concrete",
               glass="minecraft:purple_stained_glass", light="minecraft:crying_obsidian",
               stairs="minecraft:polished_blackstone_brick_stairs", path="minecraft:black_concrete")
ROD = "minecraft:end_rod"; G = 3

class B:
    def __init__(s): s.c = {}
    def set(s, x, y, z, st): s.c[(x, y, z)] = st
    def clear(s, x, y, z): s.c.pop((x, y, z), None)
    def box(s, x1, y1, z1, x2, y2, z2, st):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                for x in range(min(x1, x2), max(x1, x2) + 1): s.set(x, y, z, st)
    def clearbox(s, x1, y1, z1, x2, y2, z2):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                for x in range(min(x1, x2), max(x1, x2) + 1): s.clear(x, y, z)

def rnd(v): return int(math.floor(v + 0.5))

def disc(b, cx, cz, y, r, st):
    ri = math.ceil(r)
    for x in range(cx - ri, cx + ri + 1):
        for z in range(cz - ri, cz + ri + 1):
            if math.hypot(x - cx, z - cz) <= r + 0.3: b.set(x, y, z, st)

def ring(b, cx, cz, y, rout, rin, st):
    ri = math.ceil(rout)
    for x in range(cx - ri, cx + ri + 1):
        for z in range(cz - ri, cz + ri + 1):
            d = math.hypot(x - cx, z - cz)
            if d <= rout + 0.3 and d > rin: b.set(x, y, z, st)

def tower(b, t, cx, cz, r, y0, y1, floors, wys, cone):
    for y in range(y0, y1 + 1): ring(b, cx, cz, y, r, r - 1.3, t["wall"])
    for i in range(8):
        a = 2 * math.pi * i / 8
        px, pz = rnd(cx + r * math.cos(a)), rnd(cz + r * math.sin(a))
        b.box(px, y0, pz, px, y1, pz, t["pillar"])
    for wy in wys:
        for dy in range(2):
            b.set(cx + r, wy + dy, cz, t["glass"]); b.set(cx - r, wy + dy, cz, t["glass"])
            b.set(cx, wy + dy, cz + r, t["glass"]); b.set(cx, wy + dy, cz - r, t["glass"])
    for fy in floors: disc(b, cx, cz, fy, r - 1.3, t["floor"])
    ring(b, cx, cz, y1 + 1, r + 1, r - 1.3, t["crenel"])
    for k in range(cone + 1):
        disc(b, cx, cz, y1 + 2 + k, (r + 1) * (1.0 - k / (cone + 1)), t["roof"])
    b.box(cx, y1 + cone + 3, cz, cx, y1 + cone + 6, cz, ROD)

def generate(t):
    b = B()
    b.box(0, 0, 0, 60, 1, 60, t["base"]); b.box(0, 2, 0, 60, 2, 60, t["floor"])
    for x in range(5, 56):
        for z in range(5, 56):
            if not (x <= 6 or x >= 54 or z <= 6 or z >= 54): continue
            for y in range(G, 15): b.set(x, y, z, t["wall"])
            if (x + z) % 2 == 0: b.set(x, 15, z, t["crenel"])
    b.clearbox(27, G, 54, 33, 11, 55)
    b.box(26, G, 54, 26, 14, 55, t["pillar"]); b.box(34, G, 54, 34, 14, 55, t["pillar"])
    b.box(27, 10, 55, 33, 11, 55, "minecraft:iron_bars")
    for c in [(5, 5), (55, 5), (5, 55), (55, 55)]:
        tower(b, t, c[0], c[1], 5, G, 30, [12, 20, 28], [9, 17, 25], 14)
    cx = cz = 30
    for x in range(20, 41):
        for z in range(20, 41):
            if not (x <= 21 or x >= 39 or z <= 21 or z >= 39): continue
            for y in range(G, 35): b.set(x, y, z, t["wall"])
    for u in (-8, -4, 4, 8):
        for wy in (8, 18, 28):
            for dy in range(3):
                b.box(cx + u, wy + dy, 20, cx + u, wy + dy, 21, t["glass"])
                b.box(cx + u, wy + dy, 39, cx + u, wy + dy, 40, t["glass"])
                b.box(20, wy + dy, cz + u, 21, wy + dy, cz + u, t["glass"])
                b.box(39, wy + dy, cz + u, 40, wy + dy, cz + u, t["glass"])
    for fy in (14, 24, 35):
        b.box(22, fy, 22, 38, fy, 38, t["floor"]); b.clearbox(37, fy, 22, 38, fy, 24)
    for i in range(G, 37): b.set(38, i, 23, "minecraft:ladder[facing=west]")
    for fy in (G - 1, 14, 24):
        for dx in (-6, 6):
            for dz in (-6, 6): b.set(cx + dx, fy, cz + dz, t["light"])
    b.clearbox(28, G, 39, 32, 8, 40); b.clearbox(29, 9, 39, 31, 9, 40)
    for x in range(20, 41):
        for z in range(20, 41):
            if (x in (20, 40) or z in (20, 40)) and (x + z) % 2 == 0: b.set(x, 36, z, t["crenel"])
    for c in [(20, 20), (40, 20), (20, 40), (40, 40)]:
        tower(b, t, c[0], c[1], 3, G, 44, [14, 24, 34], [9, 19, 29, 39], 12)
    tower(b, t, cx, cz, 4, 36, 66, [44, 56], [47, 59], 18)
    b.clearbox(cx - 1, 37, cz + 3, cx + 1, 39, cz + 5); b.clearbox(cx - 2, 35, cz - 2, cx + 2, 35, cz + 2)
    b.box(28, 2, 41, 32, 2, 62, t["path"])
    for z in range(44, 55, 5):
        b.box(27, G, z, 27, G + 2, z, ROD); b.box(33, G, z, 33, G + 2, z, ROD)
    st = t["stairs"] + "[facing=north,half=bottom]"
    for i in range(3):
        z = 63 - i
        b.box(27, 0, z, 33, max(i - 1, 0), z, t["base"])
        for x in range(27, 34): b.set(x, i, z, st)
    return b.c

def fills(cells):
    """Compress cells into fill boxes: x-runs -> merge in z -> merge in y."""
    rows = {}
    for (x, y, z), st in cells.items(): rows.setdefault((y, z, st), []).append(x)
    runs = {}  # (y, st) -> list of (z, x1, x2)
    for (y, z, st), xs in rows.items():
        xs.sort(); s = p = xs[0]
        for x in xs[1:]:
            if x == p + 1: p = x; continue
            runs.setdefault((y, st), []).append((z, s, p)); s = p = x
        runs.setdefault((y, st), []).append((z, s, p))
    rects = {}  # (y, st) -> list of (x1,x2,z1,z2)
    for (y, st), lst in runs.items():
        open_ = {}; out = []
        for z, x1, x2 in sorted(lst):
            key = (x1, x2)
            if key in open_ and open_[key][1] == z - 1: open_[key][1] = z
            else:
                if key in open_: out.append((x1, x2) + tuple(open_[key]))
                open_[key] = [z, z]
        for key, (z1, z2) in open_.items(): out.append((key[0], key[1], z1, z2))
        rects[(y, st)] = out
    boxes = {}  # (st, x1,x2,z1,z2) -> sorted ys
    for (y, st), lst in rects.items():
        for r in lst: boxes.setdefault((st,) + r, []).append(y)
    cmds = []
    for (st, x1, x2, z1, z2), ys in boxes.items():
        ys.sort(); s = p = ys[0]
        for y in ys[1:] + [None]:
            if y is not None and y == p + 1: p = y; continue
            cmds.append((s, "fill ~%d ~%d ~%d ~%d ~%d ~%d %s" % (x1, s, z1, x2, p, z2, st)))
            if y is not None: s = p = y
    cmds.sort(key=lambda c: c[0])
    return [c for _, c in cmds]

if __name__ == "__main__":
    for t in (WHITE, CAPITAL):
        c = generate(t); f = fills(c); print(t["name"], len(c), "blocks ->", len(f), "fill commands")
