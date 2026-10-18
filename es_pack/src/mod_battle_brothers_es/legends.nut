// Enganche con Legends. Lo incluye el preload (mod_battle_brothers_es.nut)
// desde su cola, solo si Legends está y después de él: para entonces Legends
// ya ha definido ::Const.LegendMod (config/z_legends_language.nut), y los
// tokens no se rellenan hasta que el juego compone un texto en partida.
local mod = ::Hooks.getMod("mod_battle_brothers_es");
local L = ::Const.LegendMod;

// Tokens castellanos de género (es_pack/legends/BRIEF.md). Por cada clave de
// Pronouns, extendVarsWithPronouns rellena %clave% y %clave_<personaje>% con
// la columna de PronounTable que toca al género (neutro, hombre, mujer; aquí el
// neutro es el masculino), y pone la mayúscula si la clave empieza por ella.
// No hay "El": Legends la pone byte a byte y rompería la "é".
foreach (clave, formas in {
    o = ["o", "o", "a"]
    el = ["él", "él", "ella"]
    lo = ["lo", "lo", "la"]
    un = ["un", "un", "una"]
    hombre = ["hombre", "hombre", "mujer"]
    art = ["el", "el", "la"]
    del = ["del", "del", "de la"]
    al = ["al", "al", "a la"]
    ese = ["ese", "ese", "esa"]
}) L.PronounTable[clave] <- formas;
L.Pronouns.extend(["o", "el", "lo", "Lo", "un", "Un", "hombre", "Hombre",
                   "art", "Art", "del", "Del", "al", "Al", "ese", "Ese"]);

// Títulos tras el nombre («el Valiente»): el corpus los traduce en masculino y
// aquí pasan a femenino si el personaje es mujer, con la tabla que build_dist
// genera en titulos_es.nut (la regla está en es_pack/tools/titulos.py). Estos
// getters envuelven los de Rosetta (rosetta/hooks.nut), que se registran antes,
// así que reciben el título ya en castellano.
local fem = ::BattleBrothersEs.TitulosFemeninos;
mod.hookTree("scripts/entity/tactical/actor", function (q) {
    q.getTitle = @(__original) function () {
        local ret = __original();
        return this.getGender() == 1 && ret in fem ? fem[ret] : ret;
    }
    // Rosetta compone el nombre como nombre + " " + título; si el título
    // traducido no está al final, el nombre viene de otro sitio y se deja.
    q.getName = @(__original) function () {
        local ret = __original();
        if (this.getGender() != 1 || this.m.Title == "") return ret;
        local masc = ::Rosetta._(this.m.Title);
        if (!(masc in fem)) return ret;
        local n = ret.len() - masc.len();
        return n >= 0 && ret.slice(n) == masc ? ret.slice(0, n) + fem[masc] : ret;
    }
})
