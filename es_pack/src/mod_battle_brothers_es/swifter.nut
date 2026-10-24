// Swifter (mod_swifter): sus ajustes y atajos de MSU y el tooltip del botón
// de velocidad 8x del mapa. Lo incluye el preload solo si Swifter está, y
// después de él. Se cambia solo lo que se ve (Name, Description); los ids,
// que es lo que guarda la configuración, no se tocan. Si una versión de
// Swifter cambia sus ids, ese texto queda en inglés y nada más.
local m = ::Swifter.Mod;
local ajustes = ::MSU.System.ModSettings.getPanel(::Swifter.ID);
local nombra = function (_pagina, _id, _nombre, _descripcion = null) {
    try {
        local e = ajustes.getPage(_pagina).get(_id);
        e.Name = _nombre;
        if (_descripcion != null) e.Description = _descripcion;
    } catch (e) {}
}

nombra("General", "CombatSpeed", "Velocidad de combate", "Aumenta la velocidad de las animaciones de todos los combates.");
nombra("General", "EventFrequency", "Frecuencia de eventos", "Multiplica por este valor la frecuencia de los eventos.");
nombra("General", "Spin", "Modo Magda", "¡No vomites!");

try { ajustes.getPage("Keybinds").Name = "Atajos de teclado"; } catch (e) {}
nombra("Keybinds", "WorldKeybindsTitle", "Atajos del mapa");
nombra("Keybinds", "TacticalKeybindsTitle", "Atajos de combate");
foreach (id, nombre in {
    superfastTime = "Velocidad 8x en el mapa",
    NormalTimeTactical = "Combate a velocidad 1x",
    FastTimeTactical = "Combate a velocidad 2x",
    VeryFastTimeTactical = "Combate a velocidad 3x",
    SuperFastTimeTactical = "Combate a velocidad 4x"
}) {
    nombra("Keybinds", id, nombre);
    try { m.Keybinds.getKeybind(id).Name = nombre; } catch (e) {}
}

// El tooltip del botón de 8x lo compone Swifter en inglés; se sustituye por
// el mismo con el texto en castellano.
try {
    m.Tooltips.setTooltips({
        TimeSuperfastButton = ::MSU.Class.CustomTooltip(function (_data) {
            return [
                {id = 1, type = "title", text = "Velocidad superrápida (" + ::getModSetting(::Swifter.ID, "superfastTime").getValue() + ")"},
                {id = 2, type = "description", text = "El tiempo pasa muy deprisa (velocidad 8x)."}
            ];
        })
    });
} catch (e) {}
