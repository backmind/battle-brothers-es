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

// Descripciones de ventajas y de runas. Son cadenas @"..." que empiezan y
// acaban en salto de línea (las runas acaban en salto y tabulador), y
// ::Legends.tooltip las recorta con strip antes de pasarlas por la plantilla:
// el wrapper de Rosetta recibía el texto sin bordes y la clave del corpus, que
// los lleva, no casaba. Aquí se traduce el texto crudo, antes del strip. Legends
// define la función en su cola (!!config/_tooltip_templates.nut) y la llama
// desde los afterHooks, que carga al conectar el menú principal: este enganche
// va en medio.
// Al volver al menú principal, perk_tooltips.nut vuelve a pasar cada
// descripción, que ya lleva su línea «From the X perk group». Esa línea se
// aparta y se devuelve tal cual, para que no la vea el wrapper: Legends la
// busca en inglés para rehacerla, y la traduce la regla del corpus cuando el
// tooltip se muestra.
local tooltip = ::Legends.tooltip, GRUPO = "[color=#0b0084]From the ";
::Legends.tooltip = function (_text, ...) {
    local args = [this, _text];
    args.extend(vargv);
    if (typeof _text != "string") return tooltip.acall(args);
    local i = _text.find(GRUPO);
    if (i == null) {
        args[1] = ::Rosetta._(_text);
        return tooltip.acall(args);
    }
    local cabeza = _text.slice(0, i), n = i;
    while (n > 0 && cabeza[n - 1] <= ' ') n--;
    args[1] = cabeza;
    return tooltip.acall(args) + cabeza.slice(n) + _text.slice(i);
}

// Tres grupos de ventajas se llaman igual que un objeto o un adjetivo del juego
// base, y su par global («Espada recta», «Alabarda», «de recio porte») no vale
// para el grupo. El tooltip de los grupos que conoce el personaje
// (extendKnownPerksTooltip, que Legends añade a character_background) los pone
// aquí con su nombre de grupo antes de que lo vea Rosetta; en la línea de grupos
// de cada ventaja lo hacen las reglas del corpus.
local GRUPOS = {Sword = "Espada", Polearm = "Arma de asta", Sturdy = "Recio"};
mod.hookTree("scripts/skills/backgrounds/character_background", function (q) {
    q.extendKnownPerksTooltip = @(__original) function (_arr) {
        local n = _arr.len();
        __original(_arr);
        for (local i = n; i < _arr.len(); i++) {
            local fila = _arr[i];
            if ("type" in fila && fila.type == "textDualColumn" && fila.text in GRUPOS)
                fila.text = GRUPOS[fila.text];
        }
    }
    // La línea de aptitudes del trasfondo («Has an aptitude for swords, maces
    // and bows.») se compone con " and " entre descripciones de grupo al azar;
    // el corpus tiene el prefijo y cada descripción, pero la frase entera nunca
    // casaba. Se rehace con las piezas traducidas, mismo sorteo y misma forma.
    q.getPerkTreeGroupDescription = @(__original) function (_p, _prefix = "") {
        if (_p.len() == 0) return "";
        local partes = _p.map(@(g) ::Rosetta._(g.Descriptions[::Math.rand(0, g.Descriptions.len() - 1)]));
        local text = partes[0];
        for (local i = 1; i < partes.len(); i++)
            text += (i == partes.len() - 1 ? " y " : ", ") + partes[i];
        return (_prefix == "" ? "" : ::Rosetta._(_prefix)) + " " + text + ".\n";
    }
})

// El jinete montado toma el nombre «<jinete> and <caballo>»
// (legends_player_horserider.setScenarioValues). Una regla "<a:str> and <b:str>"
// casaría con cualquier frase; aquí se cambia solo esa unión.
mod.hookTree("scripts/entity/tactical/legends_player_horserider", function (q) {
    q.setScenarioValues = @(__original) function () {
        __original();
        local cola = " and " + this.getHorse().getName();
        if (::std.Str.endswith(this.m.Name, cola))
            this.m.Name = this.m.Name.slice(0, -cola.len()) + " y " + this.getHorse().getName();
    }
})

// El nombre de las armaduras y cascos por capas une las piezas con " on "
// (legend_armor.nut y legend_helmet.nut, makeName), y las piezas ya llegan en
// castellano por los getters de Rosetta. El corpus lo resolvía con la regla
// "<upgrade:str> on <armor:str>", que casaba con cualquier frase inglesa con un
// " on " dentro; aquí se cambia solo la unión.
foreach (clase in ["scripts/items/legend_armor/legend_armor", "scripts/items/legend_helmets/legend_helmet"])
    mod.hookTree(clase, function (q) {
        q.makeName = @(__original) function () {
            return ::std.Str.replace(__original(), " on ", " sobre ");
        }
    })
