package com.nullmod;

import com.nullmod.schem.Schematic;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

import java.util.*;

/** Places schematics over time using vanilla /setblock so it stays stable across Minecraft versions. */
public final class BuildManager {
    private static final class Job {
        final UUID owner; final String name; final ServerLevel level; final BlockPos origin;
        final Schematic s; final int perTick; int cursor; int nextReport = 25; boolean forceloaded;
        Job(UUID owner, String name, ServerLevel level, BlockPos origin, Schematic s, int perTick) {
            this.owner = owner; this.name = name; this.level = level; this.origin = origin; this.s = s; this.perTick = perTick;
        }
    }

    private static final List<Job> JOBS = new ArrayList<>();

    private BuildManager() {}

    public static void start(ServerPlayer player, ServerLevel level, String name, Schematic s, int perTick) {
        BlockPos o = player.blockPosition();
        Job j = new Job(player.getUUID(), name, level, o, s, perTick);
        MinecraftServer server = level.getServer();
        // keep the area loaded while building (vanilla forceload allows up to 256 chunks)
        int chunksX = (s.sizeX >> 4) + 2, chunksZ = (s.sizeZ >> 4) + 2;
        if (chunksX * chunksZ <= 256) {
            exec(server, level, "forceload add " + o.getX() + " " + o.getZ() + " " + (o.getX() + s.sizeX) + " " + (o.getZ() + s.sizeZ));
            j.forceloaded = true;
        }
        JOBS.add(j);
        player.sendSystemMessage(Component.literal("[NULL] Building '" + name + "' (" + s.count + " blocks, "
                + s.sizeX + "x" + s.sizeY + "x" + s.sizeZ + ") at your position."));
    }

    public static int cancel(MinecraftServer server, UUID owner) {
        int n = 0;
        for (Iterator<Job> it = JOBS.iterator(); it.hasNext(); ) {
            Job j = it.next();
            if (j.owner.equals(owner)) { finish(server, j); it.remove(); n++; }
        }
        return n;
    }

    public static void cancelAll(MinecraftServer server) {
        for (Job j : JOBS) finish(server, j);
        JOBS.clear();
    }

    private static void finish(MinecraftServer server, Job j) {
        if (j.forceloaded) {
            exec(server, j.level, "forceload remove " + j.origin.getX() + " " + j.origin.getZ() + " "
                    + (j.origin.getX() + j.s.sizeX) + " " + (j.origin.getZ() + j.s.sizeZ));
        }
    }

    private static void exec(MinecraftServer server, ServerLevel level, String cmd) {
        try {
            server.getCommands().performPrefixedCommand(
                    server.createCommandSourceStack().withLevel(level).withSuppressedOutput(), cmd);
        } catch (Exception ignored) {
            // e.g. block outside world height; skip it
        }
    }

    public static void tick(MinecraftServer server) {
        if (JOBS.isEmpty()) return;
        for (Iterator<Job> it = JOBS.iterator(); it.hasNext(); ) {
            Job j = it.next();
            Schematic s = j.s;
            int end = Math.min(s.count, j.cursor + j.perTick);
            for (int i = j.cursor; i < end; i++) {
                exec(server, j.level, "setblock " + (j.origin.getX() + s.x[i]) + " " + (j.origin.getY() + s.y[i]) + " "
                        + (j.origin.getZ() + s.z[i]) + " " + s.palette[s.id[i]]);
            }
            j.cursor = end;
            ServerPlayer owner = server.getPlayerList().getPlayer(j.owner);
            int pct = s.count == 0 ? 100 : (int) (100L * j.cursor / s.count);
            if (owner != null && pct >= j.nextReport && j.cursor < s.count) {
                owner.sendSystemMessage(Component.literal("[NULL] " + j.name + ": " + pct + "%"));
                j.nextReport += 25;
            }
            if (j.cursor >= s.count) {
                finish(server, j);
                if (owner != null) owner.sendSystemMessage(Component.literal("[NULL] " + j.name + " is complete."));
                it.remove();
            }
        }
    }
}
