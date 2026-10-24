// Traduccion del juego base Battle Brothers al castellano, via Rosetta.
// Requiere: Modern Hooks, MSU >= 1.6.0, stdlib >= 2.5, Rosetta >= 0.5.0
// (el pack de hooks retiro sus copias de los conductos que la 0.5.0 ya
// lleva, asi que con un runtime menor se apagarian pantallas enteras).
// Las strings sin par registrado se muestran en ingles: este mod no se
// rompe con las actualizaciones del juego.
if (!("Rosetta" in getroottable())) return;

local def = {
    ID = "mod_battle_brothers_es"
    Name = "Battle Brothers en Español"
    Version = "5.0.0"
    // Contra qué build del juego se verificó y qué parte de sus textos cubre,
    // medida con es_pack/tools/measure_coverage.py. Los tests exigen que
    // coincidan con build_dist.py.
    GameVersion = "1.5.2.3"
    Cobertura = "100 %"
    // Lo mismo para la traducción de Legends, que viaja en el pack.
    LegendsVersion = "19.4.22"
    CoberturaLegends = "99 %"
}
local mod = ::Hooks.register(def.ID, def.Version, def.Name);
mod.require("mod_rosetta >= 0.5.0");

// Registrarse en MSU avisa al jugador cuando sale una release en GitHub, y la
// página de información pone el pack en la pantalla de mods de MSU, que es
// donde el jugador mira si algo cargó (sin página, MSU no lo lista).
// MSU exige semver puro en la etiqueta: 1.2.3, nunca v1.2.3.
mod.queue(">mod_msu", function () {
    if (!::Hooks.hasMod("mod_msu")) return;
    ::Hooks.registerLateJS("ui/mods/mod_battle_brothers_es/msu_es.js");
    local msu = ::MSU.Class.Mod(def.ID, def.Version, def.Name);
    local dominio = ::MSU.System.Registry.ModSourceDomain;
    msu.Registry.addModSource(dominio.GitHub, "https://github.com/backmind/battle-brothers-es");
    msu.Registry.setUpdateSource(dominio.GitHub);
    // La página no tiene ajustes: es la ficha del mod. MSU pinta el nombre de
    // un título como HTML tal cual, así que los párrafos y los enlaces van ahí
    // (openURL es la función del juego que la propia MSU usa en sus avisos).
    local repo = "https://github.com/backmind/battle-brothers-es";
    local nexus = "https://www.nexusmods.com/battlebrothers/mods/640";
    local enlace = @(texto, url) format("<span style='color: lightblue; text-decoration: underline; cursor: pointer;' onclick='openURL(%c%s%c)'>%s</span>", 34, url, 34, texto);
    local parrafo = @(html) "<div class='es-parrafo text-font-normal font-color-description' style='font-weight: normal; white-space: normal; width: 100%;'>" + html + "</div>";
    // Todo alineado a la izquierda y poco texto: el panel es estrecho. Los
    // títulos de sección van subrayados en el dorado de los títulos del juego,
    // y lo que se quiere resaltar, en ese mismo dorado sin negrita.
    local dorado = @(s) "<span class='font-color-title'>" + s + "</span>";
    local seccion = @(titulo, filas) parrafo("<div class='title-font-normal font-bold font-color-title' style='text-decoration: underline; margin-bottom: 0.3rem;'>" + titulo + "</div>" + filas);
    local fila = @(html) "<div style='margin: 0.15rem 0;'>" + html + "</div>";
    local pagina = msu.ModSettings.addPage("Informacion", "Información");
    pagina.addTitle("Cabecera", parrafo("<div class='title-font-big font-bold font-color-title'>" + def.Name + " " + def.Version + "</div>"
        + fila("La traducción al castellano de " + dorado("Battle Brothers") + ", " + dorado("sus expansiones") + " y " + dorado("Legends") + ".")));
    pagina.addTitle("Incluye", seccion("Qué incluye",
        fila("Battle Brothers " + dorado(def.GameVersion) + " y sus expansiones: " + def.Cobertura + " de las frases.")
        + fila("Legends " + dorado(def.LegendsVersion) + ": " + def.CoberturaLegends + " de las frases, si está instalado.")
        + fila("Mods: MSU, Jimmy's Tooltips y Swifter.")));
    pagina.addTitle("Autores", seccion("Autores",
        fila(dorado("AMarauder") + ", " + dorado("MagnusLioncaster") + " y " + dorado("Hjensikk") + ": la traducción original.")
        + fila(dorado("ElGranFoca") + ": la adaptación a los parches y la traducción nueva de la 3.0.4 y la 3.0.5.")
        + fila(dorado("hda (backmind)") + ": la traducción sobre Rosetta desde la 4.0.0 y la traducción integral de Legends.")
        + fila("Framework: " + dorado("Rosetta") + ", de hackflow.")));
    pagina.addTitle("Enlaces", seccion("Enlaces", fila(enlace("Nexus", nexus) + " · " + enlace("GitHub", repo)
        + " · " + enlace("Informar de un error", repo + "/issues/new/choose"))));
});

::include("mod_battle_brothers_es/base_es");
::include("mod_battle_brothers_es/ids_es");

// Orden de las reglas de patrón. Rosetta guarda cada regla bajo su primera
// palabra y las prueba en orden de carga, así que una con un <x:str> abierto
// ("You gain <item:str>") casaba antes que cualquier otra más concreta que
// viniera detrás, también las de Legends, que se cargan después del base:
// «You gain 5 Crowns and 3 Experience» salía «Ganas 5 Crowns and 3
// Experience». Aquí, en cada clave, primero van las reglas sin <x:str>, en su
// orden, y después las golosas, de la de más texto literal a la de menos
// (empate: su orden). Rosetta compara las reglas por identidad, así que
// reordenarlas no cambia nada más. Se llama tras cargar cada corpus.
if (!("BattleBrothersEs" in getroottable())) ::BattleBrothersEs <- {};
::BattleBrothersEs.ordenaReglas <- function () {
    foreach (clave, lista in ::Rosetta.maps.es.rules) {
        local libres = [], golosas = [];
        foreach (i, r in lista) {
            local abierta = false, n = 0;
            if ("parts" in r)
                foreach (p in r.parts) {
                    if (typeof p == "string") n += p.len();
                    else if ("sub" in p && p.sub == "str") abierta = true;
                }
            if (abierta) golosas.push({r = r, n = n, i = i});
            else libres.push(r);
        }
        golosas.sort(function (a, b) {
            local c = b.n <=> a.n;
            return c != 0 ? c : a.i <=> b.i;
        });
        foreach (g in golosas) libres.push(g.r);
        ::Rosetta.maps.es.rules[clave] = libres;
    }
};
::BattleBrothersEs.ordenaReglas();

// El juego instalado esta en ingles, asi que la autodeteccion de idioma
// de Rosetta (que mira strings ya traducidas) no aplica: activamos es.
::Rosetta.activate("es");

// Memoria de translate() durante una traducción, contra el cuelgue de las
// reglas golosas con :t.
//
// Las reglas del tipo "<actor:str> has <name:str>" (con <name:t>) casan con
// cualquier texto que contenga " has ", y Rosetta traduce la cola para decidir
// si la regla vale. Esa cola vuelve a casar con "has", "had", "'s"... y cada
// regla la parte por su primera aparición, así que el número de llamadas crece
// de forma exponencial con los separadores: un texto inglés sin par de 86
// caracteres con doce "has"/"had" alternos ya costaba 15 s, y un evento largo
// de Legends, minutos. Casi todas esas llamadas traducen colas repetidas.
//
// translate() es una función pura del texto mientras dura una traducción (el
// mapa y el idioma no cambian a mitad), así que basta con recordar lo que ya
// se tradujo dentro de la misma llamada exterior: el resultado es idéntico y
// cada cola se traduce una sola vez. La memoria se vacía al salir, de modo que
// no crece durante la partida. Las llamadas con id o con regla a saltar (las
// de las reglas split) van directas, sin memoria.
//
// Los textos que el pack monta ya en castellano (los consejos del campamento
// de Legends) se apuntan en ::BattleBrothersEs.Hechos y salen tal cual: sin
// par, las reglas golosas los recorrían trozo a trozo hasta agotar la pila.
if (!("BattleBrothersEs" in getroottable())) ::BattleBrothersEs <- {};
::BattleBrothersEs.Hechos <- {};
(function (_def) {
    local translate = _def.translate, memo = null, hechos = ::BattleBrothersEs.Hechos;
    _def.translate <- function (_str, _id = null, _skip_rule = null) {
        if (typeof _str == "string" && _str in hechos) return _str;
        if (_id != null || _skip_rule != null || typeof _str != "string")
            return translate.call(this, _str, _id, _skip_rule);
        if (memo != null) {
            if (!(_str in memo)) memo[_str] <- translate.call(this, _str);
            return memo[_str];
        }
        memo = {};
        try {
            local ret = translate.call(this, _str);
            memo = null;
            return ret;
        } catch (e) {
            memo = null;
            throw e;
        }
    };
})(::Rosetta);

// Swifter: sus ajustes y atajos de MSU y un tooltip (swifter.nut). Va tras
// Swifter, que los crea en su cola.
mod.queue(">mod_swifter", ">mod_msu", function () {
    if (!::Hooks.hasMod("mod_swifter") || !("Swifter" in getroottable()) || !("Mod" in ::Swifter)) return;
    ::include("mod_battle_brothers_es/swifter");
});

// La traducción de cada mod viaja en este zip y solo se carga si el mod está.
// Va en la cola y después del mod porque el enganche amplía lo que el mod
// define en la suya, y después de Rosetta porque envuelve sus getters;
// build_dist.MODS lista los mods y un test exige que estén todos aquí.
mod.queue(">mod_legends", ">mod_rosetta", ">mod_Jimmys_Tooltips_legends", function () {
    if (!::Hooks.hasMod("mod_legends")) return;
    // Los textos de la interfaz de Legends que no pasan por Rosetta (menú,
    // nueva campaña, botones de ajustes). Va tarde para envolver sus módulos.
    ::Hooks.registerLateJS("ui/mods/mod_battle_brothers_es/legends_es.js");
    ::include("mod_battle_brothers_es/claves");
    ::include("mod_battle_brothers_es/mod_legends_es");
    ::BattleBrothersEs.ordenaReglas();
    ::include("mod_battle_brothers_es/titulos_es");
    ::include("mod_battle_brothers_es/legends");
});
