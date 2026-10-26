package com.nullmod.schem;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import java.util.zip.GZIPInputStream;

/** Tiny dependency-free NBT reader. Compounds -> Map, lists -> List, arrays -> primitive arrays. */
public final class Nbt {
    private Nbt() {}

    public static Map<String, Object> readFile(Path path) throws IOException {
        byte[] raw = Files.readAllBytes(path);
        InputStream in = new ByteArrayInputStream(raw);
        if (raw.length > 2 && (raw[0] & 0xff) == 0x1f && (raw[1] & 0xff) == 0x8b) {
            in = new GZIPInputStream(in);
        }
        try (DataInputStream d = new DataInputStream(new BufferedInputStream(in))) {
            int type = d.readUnsignedByte();
            if (type != 10) throw new IOException("Not an NBT compound file");
            d.readUTF(); // root name
            return readCompound(d);
        }
    }

    private static Map<String, Object> readCompound(DataInputStream d) throws IOException {
        Map<String, Object> map = new LinkedHashMap<>();
        while (true) {
            int type = d.readUnsignedByte();
            if (type == 0) return map;
            String name = d.readUTF();
            map.put(name, readPayload(type, d));
        }
    }

    private static Object readPayload(int type, DataInputStream d) throws IOException {
        switch (type) {
            case 1: return d.readByte();
            case 2: return d.readShort();
            case 3: return d.readInt();
            case 4: return d.readLong();
            case 5: return d.readFloat();
            case 6: return d.readDouble();
            case 7: { byte[] a = new byte[d.readInt()]; d.readFully(a); return a; }
            case 8: return d.readUTF();
            case 9: {
                int t = d.readUnsignedByte();
                int n = d.readInt();
                List<Object> list = new ArrayList<>(Math.max(0, n));
                for (int i = 0; i < n; i++) list.add(readPayload(t, d));
                return list;
            }
            case 10: return readCompound(d);
            case 11: { int[] a = new int[d.readInt()]; for (int i = 0; i < a.length; i++) a[i] = d.readInt(); return a; }
            case 12: { long[] a = new long[d.readInt()]; for (int i = 0; i < a.length; i++) a[i] = d.readLong(); return a; }
            default: throw new IOException("Unknown NBT tag type " + type);
        }
    }

    // ---- helpers ----
    @SuppressWarnings("unchecked")
    public static Map<String, Object> compound(Object o) {
        if (o instanceof Map) return (Map<String, Object>) o;
        throw new IllegalArgumentException("Expected compound, got " + o);
    }

    @SuppressWarnings("unchecked")
    public static List<Object> list(Object o) {
        if (o instanceof List) return (List<Object>) o;
        throw new IllegalArgumentException("Expected list, got " + o);
    }

    public static int intVal(Object o) {
        if (o instanceof Number n) return n.intValue();
        throw new IllegalArgumentException("Expected number, got " + o);
    }
}
