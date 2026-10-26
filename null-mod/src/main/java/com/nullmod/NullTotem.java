package com.nullmod;

import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

/**
 * The Totem of NULL is a totem of undying named "Totem of NULL" (given with /null totem).
 * Carrying it anywhere in your inventory makes you the owner/leader of NULL; dropping it revokes that.
 */
public final class NullTotem {
    public static final String NAME = "Totem of NULL";
    private static final Set<UUID> LEADERS = new HashSet<>();
    private static final Set<UUID> EMPIRE = new HashSet<>();
    private static int ticks;

    public static void setEmpire(ServerPlayer p, boolean on) {
        if (on) EMPIRE.add(p.getUUID()); else EMPIRE.remove(p.getUUID());
    }

    private NullTotem() {}

    public static boolean isTotem(ItemStack s) {
        return !s.isEmpty() && s.is(Items.TOTEM_OF_UNDYING) && s.getHoverName().getString().equals(NAME);
    }

    public static boolean carries(ServerPlayer p) {
        Inventory inv = p.getInventory();
        for (int i = 0; i < inv.getContainerSize(); i++) {
            if (isTotem(inv.getItem(i))) return true;
        }
        return false;
    }

    public static boolean isLeader(ServerPlayer p) {
        return LEADERS.contains(p.getUUID());
    }

    /** Runs a vanilla command as the player (at their position/rotation) with full server permission. */
    public static void run(MinecraftServer server, ServerPlayer p, String command) {
        String wrapped = "execute as " + p.getUUID() + " at @s run " + command;
        server.getCommands().performPrefixedCommand(server.createCommandSourceStack().withSuppressedOutput(), wrapped);
    }

    /** The End Empire rule: in the End, endermen/shulkers obey NULL and a patrol keeps itself stocked near the leader. */
    private static void empireRule(MinecraftServer server, ServerPlayer p) {
        String end = "execute if dimension minecraft:the_end run ";
        run(server, p, end + "team join null @e[type=minecraft:enderman,distance=..128]");
        run(server, p, end + "team join null @e[type=minecraft:shulker,distance=..128]");
        run(server, p, "execute store success score #patrol null_count if dimension minecraft:the_end unless entity @e[tag=null_patrol,distance=..80]");
        String nbt = "{Tags:[\"null_army\",\"null_patrol\"],PersistenceRequired:1b,CustomNameVisible:1b,CustomName:{text:\"NULL\",obfuscated:true,color:\"dark_gray\"},"
                + "equipment:{head:{id:\"minecraft:netherite_helmet\",count:1},chest:{id:\"minecraft:netherite_chestplate\",count:1},mainhand:{id:\"minecraft:netherite_sword\",count:1}}}";
        for (int i = 0; i < 6; i++) {
            double a = Math.PI * 2 * i / 6;
            run(server, p, String.format(java.util.Locale.ROOT,
                    "execute if score #patrol null_count matches 1 positioned ~%.1f ~ ~%.1f run summon minecraft:wither_skeleton ~ ~ ~ %s",
                    10 * Math.cos(a), 10 * Math.sin(a), nbt));
        }
        run(server, p, "team join null @e[tag=null_army,team=]");
    }

    public static void tick(MinecraftServer server) {
        if (++ticks % 10 != 0) return;
        for (ServerPlayer p : server.getPlayerList().getPlayers()) {
            boolean has = carries(p);
            boolean was = LEADERS.contains(p.getUUID());
            try {
                if (has && !was) {
                    LEADERS.add(p.getUUID());
                    run(server, p, "team add null");
                    run(server, p, "team modify null color dark_gray");
                    run(server, p, "team modify null friendlyFire false");
                    run(server, p, "team join null @s");
                    run(server, p, "scoreboard objectives add null_count dummy");
                    run(server, p, "title @s title {\"text\":\"YOU OWN NULL\",\"color\":\"dark_purple\",\"bold\":true}");
                    run(server, p, "title @s subtitle {\"text\":\"The Totem has chosen you.\",\"color\":\"gray\"}");
                    run(server, p, "playsound minecraft:entity.ender_dragon.growl master @s ~ ~ ~ 1 0.7");
                    p.sendSystemMessage(Component.literal("[NULL] You are the leader of NULL. /null orders to see your commands."));
                } else if (!has && was) {
                    LEADERS.remove(p.getUUID());
                    run(server, p, "team leave @s");
                    p.sendSystemMessage(Component.literal("[NULL] The Totem is gone. You no longer lead NULL."));
                }
                if (has && ticks % 40 == 0) {
                    // leader aura (hidden particles) + the army always knows its owner
                    run(server, p, "effect give @s minecraft:resistance 6 0 true");
                    run(server, p, "effect give @s minecraft:fire_resistance 6 0 true");
                    run(server, p, "team join null @e[tag=null_army,team=,distance=..128]");
                }
                if (has && EMPIRE.contains(p.getUUID()) && ticks % 200 == 0) {
                    empireRule(server, p);
                }
            } catch (Exception e) {
                NullMod.LOG.warn("Totem tick failed", e);
            }
        }
        LEADERS.removeIf(id -> server.getPlayerList().getPlayer(id) == null);
    }
}
