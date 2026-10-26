package com.nullmod.schem;

import java.io.IOException;
import java.nio.file.Path;
import java.util.*;

/**
 * A loaded schematic: a palette of block-state strings and a flat list of non-air blocks.
 * Coordinates are normalised so the minimum corner is (0,0,0). Blocks are sorted bottom-up (by y)
 * so supports are placed before the things that sit on them.
 */
public final class Schematic {
    public final String[] palette;
    public int sizeX, sizeY, sizeZ;
    public int count;
    public int[] x, y, z, id;

    private Schematic(String[] palette) {
        this.palette = palette;
    }

    // ------------------------------------------------------------------ public API
    public static Schematic load(Path path) throws IOException {
        String n = path.getFileName().toString().toLowerCase(Locale.ROOT);
        Map<String, Object> root = Nbt.readFile(path);
        try {
            if (n.endsWith(".schem")) return fromSponge(root);
            if (n.endsWith(".litematic")) return fromLitematic(root);
            if (n.endsWith(".nbt")) return fromStructure(root);
        } catch (RuntimeException e) {
            throw new IOException("Could not parse " + n + ": " + e.getMessage(), e);
        }
        throw new IOException("Unsupported schematic type (use .schem, .litematic or .nbt): " + n);
    }

    /** Procedural builder: later set() calls override earlier ones at the same position. */
    public static final class Builder {
        private final Map<Long, Integer> cells = new HashMap<>();
        private final List<String> palette = new ArrayList<>();
        private final Map<String, Integer> lookup = new HashMap<>();

        private static long key(int x, int y, int z) {
            return ((long) (y + 1024) << 40) | ((long) (x + 1024) << 20) | (long) (z + 1024);
        }

        public Builder set(int x, int y, int z, String state) {
            Integer id = lookup.get(state);
            if (id == null) { id = palette.size(); palette.add(state); lookup.put(state, id); }
            cells.put(key(x, y, z), id);
            return this;
        }

        public Builder clear(int x, int y, int z) {
            cells.remove(key(x, y, z));
            return this;
        }

        public Builder box(int x1, int y1, int z1, int x2, int y2, int z2, String state) {
            for (int y = Math.min(y1, y2); y <= Math.max(y1, y2); y++)
                for (int z = Math.min(z1, z2); z <= Math.max(z1, z2); z++)
                    for (int x = Math.min(x1, x2); x <= Math.max(x1, x2); x++) set(x, y, z, state);
            return this;
        }

        public Builder clearBox(int x1, int y1, int z1, int x2, int y2, int z2) {
            for (int y = Math.min(y1, y2); y <= Math.max(y1, y2); y++)
                for (int z = Math.min(z1, z2); z <= Math.max(z1, z2); z++)
                    for (int x = Math.min(x1, x2); x <= Math.max(x1, x2); x++) clear(x, y, z);
            return this;
        }

        public Schematic build() {
            Acc a = new Acc();
            for (Map.Entry<Long, Integer> e : cells.entrySet()) {
                long k = e.getKey();
                a.add((int) ((k >> 20) & 0xFFFFF) - 1024, (int) (k >> 40) - 1024, (int) (k & 0xFFFFF) - 1024, e.getValue());
            }
            return finish(palette.toArray(new String[0]), a);
        }
    }

    // ------------------------------------------------------------------ builder helpers
    private static final class Acc {
        int[] x = new int[1024], y = new int[1024], z = new int[1024], id = new int[1024];
        int n;
        void add(int px, int py, int pz, int pid) {
            if (n == x.length) {
                int c = n * 2;
                x = Arrays.copyOf(x, c); y = Arrays.copyOf(y, c); z = Arrays.copyOf(z, c); id = Arrays.copyOf(id, c);
            }
            x[n] = px; y[n] = py; z[n] = pz; id[n] = pid; n++;
        }
    }

    private static boolean skipped(String state) {
        String name = state;
        int b = name.indexOf('[');
        if (b >= 0) name = name.substring(0, b);
        return name.equals("minecraft:air") || name.equals("minecraft:cave_air")
                || name.equals("minecraft:void_air") || name.equals("minecraft:structure_void")
                || name.equals("minecraft:jigsaw") || name.equals("minecraft:structure_block");
    }

    /** Normalise to min corner = 0 and sort by y (counting sort). */
    private static Schematic finish(String[] palette, Acc a) {
        Schematic s = new Schematic(palette);
        if (a.n == 0) {
            s.x = s.y = s.z = s.id = new int[0];
            return s;
        }
        int minX = Integer.MAX_VALUE, minY = Integer.MAX_VALUE, minZ = Integer.MAX_VALUE;
        int maxX = Integer.MIN_VALUE, maxY = Integer.MIN_VALUE, maxZ = Integer.MIN_VALUE;
        for (int i = 0; i < a.n; i++) {
            minX = Math.min(minX, a.x[i]); maxX = Math.max(maxX, a.x[i]);
            minY = Math.min(minY, a.y[i]); maxY = Math.max(maxY, a.y[i]);
            minZ = Math.min(minZ, a.z[i]); maxZ = Math.max(maxZ, a.z[i]);
        }
        int heights = maxY - minY + 1;
        int[] start = new int[heights + 1];
        for (int i = 0; i < a.n; i++) start[a.y[i] - minY + 1]++;
        for (int i = 0; i < heights; i++) start[i + 1] += start[i];
        s.count = a.n;
        s.x = new int[a.n]; s.y = new int[a.n]; s.z = new int[a.n]; s.id = new int[a.n];
        for (int i = 0; i < a.n; i++) {
            int slot = start[a.y[i] - minY]++;
            s.x[slot] = a.x[i] - minX;
            s.y[slot] = a.y[i] - minY;
            s.z[slot] = a.z[i] - minZ;
            s.id[slot] = a.id[i];
        }
        s.sizeX = maxX - minX + 1;
        s.sizeY = maxY - minY + 1;
        s.sizeZ = maxZ - minZ + 1;
        return s;
    }

    private static String stateString(Map<String, Object> entry) {
        String name = (String) entry.get("Name");
        Object props = entry.get("Properties");
        if (props instanceof Map<?, ?> m && !m.isEmpty()) {
            StringBuilder sb = new StringBuilder(name).append('[');
            boolean first = true;
            for (Map.Entry<String, Object> e : new TreeMap<>(Nbt.compound(props)).entrySet()) {
                if (!first) sb.append(',');
                sb.append(e.getKey()).append('=').append(e.getValue());
                first = false;
            }
            return sb.append(']').toString();
        }
        return name;
    }

    // ------------------------------------------------------------------ Sponge .schem (v2 and v3)
    private static Schematic fromSponge(Map<String, Object> root) {
        Map<String, Object> s = root.containsKey("Schematic") ? Nbt.compound(root.get("Schematic")) : root;
        int w = Nbt.intVal(s.get("Width")), h = Nbt.intVal(s.get("Height")), l = Nbt.intVal(s.get("Length"));
        Map<String, Object> pal;
        byte[] data;
        if (s.containsKey("Blocks")) { // v3
            Map<String, Object> b = Nbt.compound(s.get("Blocks"));
            pal = Nbt.compound(b.get("Palette"));
            data = (byte[]) b.get("Data");
        } else { // v2
            pal = Nbt.compound(s.get("Palette"));
            data = (byte[]) s.get("BlockData");
        }
        int max = -1;
        for (Object v : pal.values()) max = Math.max(max, Nbt.intVal(v));
        String[] palette = new String[max + 1];
        for (Map.Entry<String, Object> e : pal.entrySet()) palette[Nbt.intVal(e.getValue())] = e.getKey();
        boolean[] skip = new boolean[palette.length];
        for (int i = 0; i < palette.length; i++) skip[i] = palette[i] == null || skipped(palette[i]);

        Acc a = new Acc();
        int idx = 0, pos = 0;
        while (pos < data.length) {
            int value = 0, shift = 0;
            while (true) {
                int b = data[pos++] & 0xff;
                value |= (b & 0x7f) << shift;
                if ((b & 0x80) == 0) break;
                shift += 7;
            }
            if (value < skip.length && !skip[value]) {
                int px = idx % w;
                int pz = (idx / w) % l;
                int py = idx / (w * l);
                a.add(px, py, pz, value);
            }
            idx++;
        }
        return finish(palette, a);
    }

    // ------------------------------------------------------------------ vanilla structure .nbt
    private static Schematic fromStructure(Map<String, Object> root) {
        List<Object> pal = Nbt.list(root.get("palette"));
        String[] palette = new String[pal.size()];
        boolean[] skip = new boolean[palette.length];
        for (int i = 0; i < palette.length; i++) {
            palette[i] = stateString(Nbt.compound(pal.get(i)));
            skip[i] = skipped(palette[i]);
        }
        Acc a = new Acc();
        for (Object o : Nbt.list(root.get("blocks"))) {
            Map<String, Object> b = Nbt.compound(o);
            int st = Nbt.intVal(b.get("state"));
            if (skip[st]) continue;
            List<Object> p = Nbt.list(b.get("pos"));
            a.add(Nbt.intVal(p.get(0)), Nbt.intVal(p.get(1)), Nbt.intVal(p.get(2)), st);
        }
        return finish(palette, a);
    }

    // ------------------------------------------------------------------ Litematica .litematic
    private static Schematic fromLitematic(Map<String, Object> root) {
        Map<String, Object> regions = Nbt.compound(root.get("Regions"));
        List<String> palette = new ArrayList<>();
        Map<String, Integer> lookup = new HashMap<>();
        Acc a = new Acc();

        for (Object ro : regions.values()) {
            Map<String, Object> r = Nbt.compound(ro);
            Map<String, Object> pos = Nbt.compound(r.get("Position"));
            Map<String, Object> size = Nbt.compound(r.get("Size"));
            int sx = Nbt.intVal(size.get("x")), sy = Nbt.intVal(size.get("y")), sz = Nbt.intVal(size.get("z"));
            int ax = Math.abs(sx), ay = Math.abs(sy), az = Math.abs(sz);
            int ox = Nbt.intVal(pos.get("x")) + (sx < 0 ? sx + 1 : 0);
            int oy = Nbt.intVal(pos.get("y")) + (sy < 0 ? sy + 1 : 0);
            int oz = Nbt.intVal(pos.get("z")) + (sz < 0 ? sz + 1 : 0);

            List<Object> rp = Nbt.list(r.get("BlockStatePalette"));
            int[] map = new int[rp.size()];
            for (int i = 0; i < map.length; i++) {
                String st = stateString(Nbt.compound(rp.get(i)));
                if (skipped(st)) { map[i] = -1; continue; }
                Integer existing = lookup.get(st);
                if (existing == null) {
                    existing = palette.size();
                    palette.add(st);
                    lookup.put(st, existing);
                }
                map[i] = existing;
            }

            long[] bits = (long[]) r.get("BlockStates");
            int nbits = Math.max(2, 32 - Integer.numberOfLeadingZeros(Math.max(1, rp.size() - 1)));
            long mask = (1L << nbits) - 1;
            long total = (long) ax * ay * az;
            for (long i = 0; i < total; i++) {
                long bitPos = i * nbits;
                int word = (int) (bitPos >>> 6);
                int off = (int) (bitPos & 63);
                long v = (bits[word] >>> off) & mask;
                if (off + nbits > 64 && word + 1 < bits.length) {
                    v |= (bits[word + 1] << (64 - off)) & mask;
                }
                int pid = map[(int) v];
                if (pid < 0) continue;
                int px = (int) (i % ax);
                int pz = (int) ((i / ax) % az);
                int py = (int) (i / ((long) ax * az));
                a.add(ox + px, oy + py, oz + pz, pid);
            }
        }
        return finish(palette.toArray(new String[0]), a);
    }
}
