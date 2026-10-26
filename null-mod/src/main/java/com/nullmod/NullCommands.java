package com.nullmod;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.nullmod.schem.Castle;
import com.nullmod.schem.Schematic;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import java.util.stream.Stream;

public final class NullCommands {
    private NullCommands() {}

    public static void register(CommandDispatcher<CommandSourceStack> d) {
        d.register(Commands.literal("null")
                .executes(c -> help(c.getSource()))
                .then(Commands.literal("totem")
                        .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .executes(c -> giveTotem(c.getSource())))
                .then(Commands.literal("orders")
                        .executes(c -> listCategories(c.getSource()))
                        .then(Commands.argument("category", StringArgumentType.word())
                                .suggests((c, b) -> SharedSuggestionProvider.suggest(OrderRegistry.byCategory().keySet(), b))
                                .executes(c -> listCategory(c.getSource(), StringArgumentType.getString(c, "category")))))
                .then(Commands.literal("order")
                        .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .then(Commands.argument("id", StringArgumentType.word())
                                .suggests((c, b) -> SharedSuggestionProvider.suggest(OrderRegistry.ids(), b))
                                .executes(c -> order(c, false))
                                .then(Commands.literal("confirm").executes(c -> order(c, true)))))
                .then(Commands.literal("build")
                        .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .then(Commands.argument("file", StringArgumentType.word())
                                .suggests((c, b) -> SharedSuggestionProvider.suggest(listSchematics(), b))
                                .executes(c -> build(c, 400))
                                .then(Commands.argument("blocksPerTick", IntegerArgumentType.integer(1, 5000))
                                        .executes(c -> build(c, IntegerArgumentType.getInteger(c, "blocksPerTick"))))))
                .then(Commands.literal("castle")
                        .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .then(Commands.literal("white").executes(c -> castle(c.getSource(), Castle.WHITE)))
                        .then(Commands.literal("capital").executes(c -> castle(c.getSource(), Castle.CAPITAL))))
                .then(Commands.literal("stronghold")
                        .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .executes(c -> {
                            c.getSource().getServer().getCommands().performPrefixedCommand(c.getSource(), "locate structure minecraft:stronghold");
                            return 1;
                        }))
                .then(Commands.literal("buildstop")
                        .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .executes(c -> buildStop(c.getSource())))
                .then(Commands.literal("schematics").executes(c -> schematics(c.getSource()))));
    }

    // ------------------------------------------------------------------ helpers
    private static void ok(CommandSourceStack s, String msg) {
        s.sendSuccess(() -> Component.literal(msg).withStyle(ChatFormatting.GRAY), false);
    }

    private static int fail(CommandSourceStack s, String msg) {
        s.sendFailure(Component.literal("[NULL] " + msg).withStyle(ChatFormatting.RED));
        return 0;
    }

    private static List<String> listSchematics() {
        try (Stream<Path> st = Files.list(NullMod.schematicDir())) {
            return st.map(p -> p.getFileName().toString())
                    .filter(n -> n.endsWith(".schem") || n.endsWith(".litematic") || n.endsWith(".nbt"))
                    .sorted().toList();
        } catch (IOException e) {
            return List.of();
        }
    }

    private static Path resolveSchematic(String name) {
        Path dir = NullMod.schematicDir();
        for (String ext : new String[]{"", ".schem", ".litematic", ".nbt"}) {
            Path p = dir.resolve(name + ext).normalize();
            if (p.startsWith(dir) && Files.isRegularFile(p)) return p;
        }
        return null;
    }

    // ------------------------------------------------------------------ commands
    private static int help(CommandSourceStack s) {
        ok(s, "[NULL] /null totem  - get the Totem of NULL (op). Carrying it makes you the owner of NULL.");
        ok(s, "[NULL] /null orders [category]  - list the " + OrderRegistry.all().size() + " orders.");
        ok(s, "[NULL] /null order <id> [confirm]  - issue an order (needs the Totem; destructive ones need 'confirm').");
        ok(s, "[NULL] /null build <file> [blocksPerTick]  - autobuild a schematic at your feet.");
        ok(s, "[NULL] /null castle white|capital  - generate the big white End castle / the dark NULL capital at your feet. /null stronghold - locate the nearest stronghold.");
        ok(s, "[NULL] /null schematics | /null buildstop   (folder: config/null_mod/schematics)");
        return 1;
    }

    private static int giveTotem(CommandSourceStack s) {
        try {
            ServerPlayer p = s.getPlayerOrException();
            NullTotem.run(s.getServer(), p, "give @s minecraft:totem_of_undying[custom_name={text:\"" + NullTotem.NAME
                    + "\",color:\"dark_purple\",bold:true,italic:false},enchantment_glint_override=true]");
            ok(s, "[NULL] Hold the Totem and NULL is yours.");
            return 1;
        } catch (CommandSyntaxException e) {
            return fail(s, "Players only.");
        }
    }

    private static int listCategories(CommandSourceStack s) {
        ok(s, "[NULL] Categories (use /null orders <category>):");
        OrderRegistry.byCategory().forEach((k, v) -> ok(s, "  " + k + " (" + v.size() + ")"));
        return OrderRegistry.all().size();
    }

    private static int listCategory(CommandSourceStack s, String cat) {
        List<OrderRegistry.Order> list = OrderRegistry.byCategory().get(cat);
        if (list == null) return fail(s, "Unknown category.");
        ok(s, "[NULL] " + cat + " - " + list.size() + " orders:");
        for (OrderRegistry.Order o : list) ok(s, "  " + o.id() + (o.destructive() ? " [!]" : "") + " - " + o.description());
        return list.size();
    }

    private static int order(CommandContext<CommandSourceStack> c, boolean confirmed) {
        CommandSourceStack s = c.getSource();
        ServerPlayer p;
        try { p = s.getPlayerOrException(); } catch (CommandSyntaxException e) { return fail(s, "Players only."); }
        if (!NullTotem.carries(p)) return fail(s, "Only the bearer of the Totem of NULL can command the army. Use /null totem.");
        OrderRegistry.Order o = OrderRegistry.get(StringArgumentType.getString(c, "id"));
        if (o == null) return fail(s, "Unknown order.");
        if (o.destructive() && !confirmed) {
            return fail(s, "'" + o.id() + "' is destructive. Run: /null order " + o.id() + " confirm");
        }
        MinecraftServer server = s.getServer();
        int okCount = 0, failed = 0;
        for (String cmd : o.commands()) {
            try {
                if (cmd.startsWith("!gen ")) {
                    Castle.Theme th = cmd.substring(5).trim().equals("capital") ? Castle.CAPITAL : Castle.WHITE;
                    if (p.level() instanceof ServerLevel lv) BuildManager.start(p, lv, th.name(), Castle.generate(th), 700);
                } else if (cmd.startsWith("!empire ")) {
                    NullTotem.setEmpire(p, cmd.substring(8).trim().equals("on"));
                } else if (cmd.startsWith("!build ")) {
                    String file = cmd.substring(7).trim();
                    Path path = resolveSchematic(file);
                    if (path == null) {
                        p.sendSystemMessage(Component.literal("[NULL] Missing schematic '" + file + "' in config/null_mod/schematics (.schem/.litematic/.nbt)."));
                        failed++;
                        continue;
                    }
                    startBuild(p, file, path, 400);
                } else {
                    NullTotem.run(server, p, cmd);
                }
                okCount++;
            } catch (Exception e) {
                failed++;
            }
        }
        ok(s, "[NULL] Order '" + o.id() + "' issued (" + okCount + " steps" + (failed > 0 ? ", " + failed + " skipped" : "") + ").");
        return okCount;
    }

    private static void startBuild(ServerPlayer p, String name, Path path, int perTick) throws IOException {
        Schematic sch = Schematic.load(path);
        if (!(p.level() instanceof ServerLevel level)) return;
        BuildManager.start(p, level, name, sch, perTick);
    }

    private static int build(CommandContext<CommandSourceStack> c, int perTick) {
        CommandSourceStack s = c.getSource();
        ServerPlayer p;
        try { p = s.getPlayerOrException(); } catch (CommandSyntaxException e) { return fail(s, "Players only."); }
        if (!NullTotem.carries(p)) return fail(s, "Only the bearer of the Totem of NULL can build. Use /null totem.");
        String name = StringArgumentType.getString(c, "file");
        Path path = resolveSchematic(name);
        if (path == null) return fail(s, "No such schematic. Put files in config/null_mod/schematics and see /null schematics.");
        try {
            startBuild(p, name, path, perTick);
            return 1;
        } catch (Exception e) {
            NullMod.LOG.warn("Schematic load failed", e);
            return fail(s, "Could not load schematic: " + e.getMessage());
        }
    }

    private static int castle(CommandSourceStack s, Castle.Theme th) {
        ServerPlayer p;
        try { p = s.getPlayerOrException(); } catch (CommandSyntaxException e) { return fail(s, "Players only."); }
        if (!NullTotem.carries(p)) return fail(s, "Only the bearer of the Totem of NULL can build. Use /null totem.");
        if (p.level() instanceof ServerLevel lv) BuildManager.start(p, lv, th.name(), Castle.generate(th), 700);
        return 1;
    }

    private static int buildStop(CommandSourceStack s) {
        try {
            int n = BuildManager.cancel(s.getServer(), s.getPlayerOrException().getUUID());
            ok(s, "[NULL] Stopped " + n + " build(s).");
            return n;
        } catch (CommandSyntaxException e) {
            return fail(s, "Players only.");
        }
    }

    private static int schematics(CommandSourceStack s) {
        List<String> l = listSchematics();
        if (l.isEmpty()) ok(s, "[NULL] No schematics yet. Folder: " + NullMod.schematicDir());
        else l.forEach(n -> ok(s, "  " + n));
        return l.size();
    }
}
