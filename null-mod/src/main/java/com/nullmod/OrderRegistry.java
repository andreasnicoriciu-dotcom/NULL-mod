package com.nullmod;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;

import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Orders are data: see gen/gen_orders.py. Each order is a list of vanilla commands run as the Totem bearer. */
public final class OrderRegistry {
    public record Order(String id, String category, String description, boolean destructive, List<String> commands) {}

    private static final Map<String, Order> ORDERS = new LinkedHashMap<>();

    private OrderRegistry() {}

    public static void load() {
        ORDERS.clear();
        try (Reader r = new InputStreamReader(OrderRegistry.class.getResourceAsStream("/null_mod/orders.json"), StandardCharsets.UTF_8)) {
            JsonObject root = new Gson().fromJson(r, JsonObject.class);
            for (JsonElement el : root.getAsJsonArray("orders")) {
                JsonObject o = el.getAsJsonObject();
                List<String> cmds = new ArrayList<>();
                JsonArray arr = o.getAsJsonArray("commands");
                for (JsonElement c : arr) cmds.add(c.getAsString());
                ORDERS.put(o.get("id").getAsString(), new Order(
                        o.get("id").getAsString(), o.get("category").getAsString(),
                        o.get("description").getAsString(), o.get("destructive").getAsBoolean(), cmds));
            }
        } catch (Exception e) {
            NullMod.LOG.error("Failed to load orders.json", e);
        }
    }

    public static Collection<Order> all() { return ORDERS.values(); }
    public static Order get(String id) { return ORDERS.get(id); }
    public static Set<String> ids() { return ORDERS.keySet(); }

    public static Map<String, List<Order>> byCategory() {
        Map<String, List<Order>> m = new TreeMap<>();
        for (Order o : ORDERS.values()) m.computeIfAbsent(o.category(), k -> new ArrayList<>()).add(o);
        return m;
    }
}
