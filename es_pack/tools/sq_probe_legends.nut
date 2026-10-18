// Comprueba el enganche con Legends (src/mod_battle_brothers_es/legends.nut)
// contra el código real de Legends, sin arrancar el juego.
//
// Carga el z_legends_language.nut de la fuente fijada (es_pack/legends/), una
// tabla de títulos generada por tools/titulos.py y el enganche, y mira dos
// cosas: que extendVarsWithPronouns rellena los tokens castellanos con la forma
// de cada género (mayúsculas incluidas, que Legends pone byte a byte), y que
// los getters de título y nombre pasan a femenino solo a las mujeres.
//
// Uso (lo lanza test_build_dist.py, que genera la tabla):
//   ROSETTA_DIR=<raiz_repo> LEGENDS_DIR=<fuente de Legends> TITULOS_NUT=<tabla> \
//     sq.exe es_pack/tools/sq_probe_legends.nut
// Al final imprime "FALLOS: <n>".

local raiz = getenv("ROSETTA_DIR");
::probe <- {fallos = 0, hook = null};

// Lo poco del juego y de los mods que tocan los dos ficheros.
::Const <- {};
// El enganche también envuelve ::Legends.tooltip y engancha las armaduras por
// capas; aquí solo se mira el hook del actor (los textos, en sq_probe_legends_textos.nut).
::Legends <- {S = {isNull = @(_x) _x == null}, tooltip = @(_t, ...) _t};
::Hooks <- {getMod = @(_id) {hookTree = function (_src, _f) {
    if (_src == "scripts/entity/tactical/actor") ::probe.hook = _f;
}}};
local tr = {["the Brave"] = "el Valiente", ["the Old Wolf"] = "el Viejo Lobo",
            ["the Shieldmaiden"] = "la Escudera"};
::Rosetta <- {_ = @(_s, _id = null) _s in tr ? tr[_s] : _s};

dofile(getenv("LEGENDS_DIR") + "/mod_legends/config/z_legends_language.nut", true);
dofile(getenv("TITULOS_NUT"), true);
dofile(raiz + "/es_pack/src/mod_battle_brothers_es/legends.nut", true);

function comprueba( _titulo, _obtenido, _esperado ) {
    local ok = _obtenido == _esperado;
    if (!ok) ::probe.fallos++;
    print((ok ? "  ok     " : "  FALLO  ") + _titulo + ": \"" + _obtenido + "\""
          + (ok ? "" : ", esperado \"" + _esperado + "\"") + "\n");
}

print("=== tokens de género, con sufijo de personaje ===\n");
local esperado = {
    o = ["o", "o", "a"], el = ["él", "él", "ella"], lo = ["lo", "lo", "la"],
    Lo = ["Lo", "Lo", "La"], un = ["un", "un", "una"], Un = ["Un", "Un", "Una"],
    hombre = ["hombre", "hombre", "mujer"], Hombre = ["Hombre", "Hombre", "Mujer"],
    art = ["el", "el", "la"], Art = ["El", "El", "La"], del = ["del", "del", "de la"],
    Del = ["Del", "Del", "De la"], al = ["al", "al", "a la"], Al = ["Al", "Al", "A la"],
    ese = ["ese", "ese", "esa"], Ese = ["Ese", "Ese", "Esa"], they = ["they", "he", "she"]
};
foreach (genero in [-1, 0, 1]) {
    local vars = [];
    ::Const.LegendMod.extendVarsWithPronouns(vars, genero, "bro");
    local t = {};
    foreach (v in vars) t[v[0]] <- v[1];
    foreach (clave, formas in esperado) {
        local k = clave + "_bro";
        comprueba(k + " (género " + genero + ")", k in t ? t[k] : "<sin token>", formas[genero + 1]);
    }
}

print("=== títulos ===\n");
// Como el q de Modern Hooks, admite asignar con = un getter que no existía.
local q = {};
q.setdelegate({_set = function (_k, _v) { this.rawset(_k, _v); }});
::probe.hook(q);
local getTitle = q.getTitle(function () { return ::Rosetta._(this.m.Title); });
local getName = q.getName(function () {
    return this.m.Title == "" ? ::Rosetta._(this.m.Name)
        : ::Rosetta._(this.m.Name) + " " + ::Rosetta._(this.m.Title);
});
local function actor( _nombre, _titulo, _genero ) {
    return {m = {Name = _nombre, Title = _titulo}, g = _genero, getGender = function () { return g; }};
}
foreach (caso in [
    ["mujer", actor("Ana", "the Brave", 1), "la Valiente", "Ana la Valiente"],
    ["mujer, título de varias palabras", actor("Ana", "the Old Wolf", 1), "la Vieja Loba", "Ana la Vieja Loba"],
    ["hombre", actor("Hans", "the Brave", 0), "el Valiente", "Hans el Valiente"],
    ["sin género (neutro)", actor("Hans", "the Brave", -1), "el Valiente", "Hans el Valiente"],
    ["mujer con título ya femenino", actor("Ana", "the Shieldmaiden", 1), "la Escudera", "Ana la Escudera"],
    ["mujer sin título", actor("Ana", "", 1), "", "Ana"],
]) {
    comprueba("getTitle, " + caso[0], getTitle.call(caso[1]), caso[2]);
    comprueba("getName, " + caso[0], getName.call(caso[1]), caso[3]);
}

print("FALLOS: " + ::probe.fallos + "\n");
