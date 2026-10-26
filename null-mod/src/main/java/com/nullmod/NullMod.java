package com.nullmod;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.loader.api.FabricLoader;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.file.Files;
import java.nio.file.Path;

public class NullMod implements ModInitializer {
    public static final String ID = "null_mod";
    public static final Logger LOG = LoggerFactory.getLogger(ID);

    public static Path schematicDir() {
        return FabricLoader.getInstance().getConfigDir().resolve(ID).resolve("schematics");
    }

    @Override
    public void onInitialize() {
        try {
            Files.createDirectories(schematicDir());
        } catch (Exception e) {
            LOG.warn("Could not create schematic folder", e);
        }
        OrderRegistry.load();
        CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> NullCommands.register(dispatcher));
        ServerTickEvents.END_SERVER_TICK.register(server -> {
            NullTotem.tick(server);
            BuildManager.tick(server);
        });
        ServerLifecycleEvents.SERVER_STOPPING.register(server -> BuildManager.cancelAll(server));
        LOG.info("NULL mod loaded: {} orders. Schematics go in {}", OrderRegistry.all().size(), schematicDir());
    }
}
