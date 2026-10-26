package com.nullmod.schem;

/**
 * Procedural castle generator. Footprint is 61x61 (plus gate steps to z=63); the min corner is the
 * placement point (your feet). The plinth is 3 blocks tall, so the floor you walk on is y=3.
 * Gate faces +z (south). Two themes: the white End castle and the dark NULL capital.
 */
public final class Castle {
    private Castle() {}

    public record Theme(String name, String base, String floor, String wall, String crenel, String pillar,
                        String roof, String glass, String light, String stairs, String path) {}

    public static final Theme WHITE = new Theme("white_castle",
            "minecraft:end_stone_bricks", "minecraft:smooth_quartz", "minecraft:quartz_bricks", "minecraft:quartz_block",
            "minecraft:quartz_pillar[axis=y]", "minecraft:white_concrete", "minecraft:white_stained_glass",
            "minecraft:sea_lantern", "minecraft:quartz_stairs", "minecraft:white_concrete");

    public static final Theme CAPITAL = new Theme("null_capital",
            "minecraft:blackstone", "minecraft:polished_blackstone", "minecraft:polished_blackstone_bricks",
            "minecraft:deepslate_tiles", "minecraft:polished_basalt[axis=y]", "minecraft:purple_concrete",
            "minecraft:purple_stained_glass", "minecraft:crying_obsidian", "minecraft:polished_blackstone_brick_stairs",
            "minecraft:black_concrete");

    private static final String ROD = "minecraft:end_rod";
    private static final int G = 3; // walking level

    public static Schematic generate(Theme t) {
        Schematic.Builder b = new Schematic.Builder();

        // ---- plinth (y 0..2) and floor
        b.box(0, 0, 0, 60, 1, 60, t.base());
        b.box(0, 2, 0, 60, 2, 60, t.floor());

        // ---- curtain wall (y 3..14) + crenellations
        for (int x = 5; x <= 55; x++) {
            for (int z = 5; z <= 55; z++) {
                boolean band = x <= 6 || x >= 54 || z <= 6 || z >= 54;
                if (!band) continue;
                for (int y = G; y <= 14; y++) b.set(x, y, z, t.wall());
                if ((x + z) % 2 == 0) b.set(x, 15, z, t.crenel());
            }
        }
        // gate in the south wall (z 54..55), pillars, raised portcullis
        b.clearBox(27, G, 54, 33, 11, 55);
        b.box(26, G, 54, 26, 14, 55, t.pillar());
        b.box(34, G, 54, 34, 14, 55, t.pillar());
        b.box(27, 10, 55, 33, 11, 55, "minecraft:iron_bars");

        // ---- corner towers on the wall
        int[][] corners = {{5, 5}, {55, 5}, {5, 55}, {55, 55}};
        for (int[] c : corners) tower(b, t, c[0], c[1], 5, G, 30, new int[]{12, 20, 28}, new int[]{9, 17, 25}, 14);

        // ---- keep
        int cx = 30, cz = 30;
        for (int x = 20; x <= 40; x++) {
            for (int z = 20; z <= 40; z++) {
                boolean band = x <= 21 || x >= 39 || z <= 21 || z >= 39;
                if (!band) continue;
                for (int y = G; y <= 34; y++) b.set(x, y, z, t.wall());
            }
        }
        int[] ys = {8, 18, 28};
        for (int u : new int[]{-8, -4, 4, 8}) {
            for (int wy : ys) {
                for (int dy = 0; dy < 3; dy++) {
                    b.box(cx + u, wy + dy, 20, cx + u, wy + dy, 21, t.glass());
                    b.box(cx + u, wy + dy, 39, cx + u, wy + dy, 40, t.glass());
                    b.box(20, wy + dy, cz + u, 21, wy + dy, cz + u, t.glass());
                    b.box(39, wy + dy, cz + u, 40, wy + dy, cz + u, t.glass());
                }
            }
        }
        // floors at y=14, 24 and roof at y=35 (hole at x 37..38, z 22..24 for the ladder)
        for (int fy : new int[]{14, 24, 35}) {
            b.box(22, fy, 22, 38, fy, 38, t.floor());
            b.clearBox(37, fy, 22, 38, fy, 24);
        }
        for (int i = G; i <= 36; i++) b.set(38, i, 23, "minecraft:ladder[facing=west]");
        for (int fy : new int[]{G - 1, 14, 24}) {
            for (int dx : new int[]{-6, 6}) for (int dz : new int[]{-6, 6}) b.set(cx + dx, fy, cz + dz, t.light());
        }
        // keep door (south face) and parapet
        b.clearBox(28, G, 39, 32, 8, 40);
        b.clearBox(29, 9, 39, 31, 9, 40);
        for (int x = 20; x <= 40; x++) for (int z = 20; z <= 40; z++) {
            boolean edge = x == 20 || x == 40 || z == 20 || z == 40;
            if (edge && (x + z) % 2 == 0) b.set(x, 36, z, t.crenel());
        }

        // ---- keep corner turrets
        for (int[] c : new int[][]{{20, 20}, {40, 20}, {20, 40}, {40, 40}}) {
            tower(b, t, c[0], c[1], 3, G, 44, new int[]{14, 24, 34}, new int[]{9, 19, 29, 39}, 12);
        }

        // ---- central spire above the keep
        tower(b, t, cx, cz, 4, 36, 66, new int[]{44, 56}, new int[]{47, 59}, 18);
        b.clearBox(cx - 1, 37, cz + 3, cx + 1, 39, cz + 5); // spire door
        b.clearBox(cx - 2, 35, cz - 2, cx + 2, 35, cz + 2);  // open the roof under the spire

        // ---- courtyard path, lamps, gate steps
        b.box(28, 2, 41, 32, 2, 62, t.path());
        for (int z = 44; z <= 54; z += 5) {
            b.box(27, G, z, 27, G + 2, z, ROD);
            b.box(33, G, z, 33, G + 2, z, ROD);
        }
        String st = t.stairs() + "[facing=north,half=bottom]";
        for (int i = 0; i < 3; i++) {
            int z = 63 - i;
            b.box(27, 0, z, 33, i - 1 < 0 ? -1 : i - 1, z, t.base());
            for (int x = 27; x <= 33; x++) b.set(x, i, z, st);
        }
        return b.build();
    }

    // ---------------------------------------------------------------- helpers
    private static void disc(Schematic.Builder b, int cx, int cz, int y, double r, String state) {
        int ri = (int) Math.ceil(r);
        for (int x = cx - ri; x <= cx + ri; x++)
            for (int z = cz - ri; z <= cz + ri; z++)
                if (Math.hypot(x - cx, z - cz) <= r + 0.3) b.set(x, y, z, state);
    }

    private static void ring(Schematic.Builder b, int cx, int cz, int y, double rOut, double rIn, String state) {
        int ri = (int) Math.ceil(rOut);
        for (int x = cx - ri; x <= cx + ri; x++)
            for (int z = cz - ri; z <= cz + ri; z++) {
                double d = Math.hypot(x - cx, z - cz);
                if (d <= rOut + 0.3 && d > rIn) b.set(x, y, z, state);
            }
    }

    /** Round tower: shell y0..y1, pillars, window rows, interior floors, cone roof and end-rod tip. */
    private static void tower(Schematic.Builder b, Theme t, int cx, int cz, int r, int y0, int y1,
                              int[] floors, int[] windowYs, int coneH) {
        for (int y = y0; y <= y1; y++) ring(b, cx, cz, y, r, r - 1.3, t.wall());
        for (int i = 0; i < 8; i++) {
            double a = Math.PI * 2 * i / 8;
            int px = (int) Math.round(cx + r * Math.cos(a)), pz = (int) Math.round(cz + r * Math.sin(a));
            b.box(px, y0, pz, px, y1, pz, t.pillar());
        }
        for (int wy : windowYs) {
            for (int dy = 0; dy < 2; dy++) {
                b.set(cx + r, wy + dy, cz, t.glass()); b.set(cx - r, wy + dy, cz, t.glass());
                b.set(cx, wy + dy, cz + r, t.glass()); b.set(cx, wy + dy, cz - r, t.glass());
            }
        }
        for (int fy : floors) disc(b, cx, cz, fy, r - 1.3, t.floor());
        // lip, cone roof, tip
        ring(b, cx, cz, y1 + 1, r + 1, r - 1.3, t.crenel());
        for (int k = 0; k <= coneH; k++) {
            double rad = (r + 1) * (1.0 - (double) k / (coneH + 1));
            disc(b, cx, cz, y1 + 2 + k, rad, t.roof());
        }
        b.box(cx, y1 + coneH + 3, cz, cx, y1 + coneH + 6, cz, ROD);
    }
}
