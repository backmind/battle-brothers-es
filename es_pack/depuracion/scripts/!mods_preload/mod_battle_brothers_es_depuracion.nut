// Modo de depuración del pack, solo para las pruebas (no va en la release).
// Registra en el log cada texto visible en pantalla que parezca inglés,
// también los que nunca pasan por Rosetta (rótulos del JS, textos que un mod
// compone por su cuenta). Las líneas salen como «[es-depuracion] ...».
// Se construye con es_pack/tools/build_depuracion.py; se quita de data para
// jugar normal.
local mod = ::Hooks.register("mod_battle_brothers_es_depuracion", "1.0.0", "Battle Brothers en Español (depuración)");
mod.require("mod_msu");
mod.queue(">mod_msu", function () {
    ::Hooks.registerJS("ui/mods/mod_battle_brothers_es_depuracion/depuracion.js");
    ::MSU.UI.registerConnection(::new("scripts/mods/mod_battle_brothers_es_depuracion/conexion"));
});
