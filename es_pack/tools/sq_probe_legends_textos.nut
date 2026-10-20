// Comprueba contra el runtime real de Rosetta, los packs construidos y el
// código real de Legends que los textos que Legends monta en ejecución salen en
// castellano: las descripciones de ventajas y de runas (que pasan por
// ::Legends.tooltip, enganchado en src/mod_battle_brothers_es/legends.nut), la
// línea «From the X perk group» que les suma afterHooks/perk_tooltips.nut, los
// mensajes de la tienda de entrenamiento y la descripción de la de reparaciones,
// y que las reglas que antes casaban con cualquier frase ya no lo hacen.
//
// El oráculo de cada descripción es el par del corpus, leído del mapa de
// Rosetta, no una llamada a translate(): así la sonda falla si el enganche deja
// de traducir el texto crudo.
//
// Uso (lo lanza test_build_dist.py, que construye los packs en un temporal):
//   ROSETTA_DIR=<raiz_repo> STDLIB_DIR=<stdlib descomprimido> LEGENDS_DIR=<fuente>
//   SONDA_PACKS=<base_es.nut;ids_es.nut;mod_legends_es.nut> sq.exe <esta sonda>
// Al final imprime "FALLOS: <n>".

local raiz = getenv("ROSETTA_DIR"), fuente = getenv("LEGENDS_DIR") + "/mod_legends/";
dofile(raiz + "/es_pack/tools/sq_bootstrap.nut", true);
foreach (p in split(getenv("SONDA_PACKS"), ";")) dofile(p, true);
::Rosetta.activate("es");
local Str = ::std.Str;
::probe <- {fallos = 0};

local function esc( _s ) {
    return Str.replace(Str.replace(_s, "\n", "\\n"), "\t", "\\t");
}
local function comprueba( _titulo, _obtenido, _esperado, _callado = false ) {
    local ok = _obtenido == _esperado;
    if (!ok) ::probe.fallos++;
    if (!ok || !_callado)
        print((ok ? "  ok     " : "  FALLO  ") + _titulo + (ok ? "" : "\n           obtenido: \""
              + esc(_obtenido) + "\"\n           esperado: \"" + esc(_esperado) + "\"") + "\n");
    return ok;
}

// La traducción que el corpus da a una cadena, sin pasar por translate():
// literal en strs, o regla sin capturas cuyo único trozo es la cadena.
local amap = ::Rosetta.maps.es;
local function esDe( _en ) {
    if (_en in amap.strs) return amap.strs[_en];
    foreach (k, reglas in amap.rules)
        foreach (r in reglas)
            if (r.parts.len() == 1 && r.parts[0] == _en) return r.es.reduce(@(a, b) a + b);
    return null;
}

// Lo poco del juego y de los mods que tocan los ficheros que se cargan.
foreach (k, v in {PositiveEventValue = "#00ff01", NegativeEventValue = "#ff0001"}) ::Const.UI.Color[k] <- v;
::Const.Items.ItemType <- {Shield = 1, Helmet = 2, Armor = 3, Weapon = 4, MeleeWeapon = 4, RangedWeapon = 4};
::Const.Strings.PerkName <- {}.setdelegate({_get = @(_k) _k});
::Const.Strings.PerkDescription <- {};
::Const.LegendMod <- {PronounTable = {}, Pronouns = []};
::BattleBrothersEs <- {TitulosFemeninos = {}};
::MSU <- {String = {replace = function ( _s, _find, _rep ) {
    local i = _s.find(_find);
    return i == null ? _s : _s.slice(0, i) + _rep + _s.slice(i + _find.len());
}}};
local porNombre = {}.setdelegate({_get = @(_k) _k});
::Legends <- {Perk = porNombre, Effect = porNombre};
local enganches = {};
::Hooks.getMod <- @(_id) {hookTree = function ( _src, _f ) { enganches[_src] <- _f; }};
// La plantilla del juego, sin Rosetta: el wrapper de Rosetta se emula aparte.
local function plantilla( _text, _vars ) {
    foreach (v in _vars) _text = Str.replace(_text, "%" + v[0] + "%", "" + v[1]);
    return _text;
}
::buildTextFromTemplate <- @(_text, _vars) plantilla(::Rosetta._(_text), _vars);

dofile(fuente + "!!config/_color_ui.nut", true);
dofile(fuente + "!!config/_tooltip_templates.nut", true);
local original = ::Legends.tooltip;
dofile(raiz + "/es_pack/src/mod_battle_brothers_es/legends.nut", true);
comprueba("legends.nut envuelve ::Legends.tooltip", ::Legends.tooltip != original, true);

print("=== descripciones de ventajas (perk_strings.nut, las dos) ===\n");
::Const.Perks <- {PerkDefObjects = {}.setdelegate({_get = function ( _k ) {
    local t = {Tooltip = "", Name = ""};
    this.rawset(_k, t);
    return t;
}})};
dofile(fuente + "!!config/perk_strings.nut", true);
dofile(fuente + "hooks/config/perk_strings.nut", true);
local n = 0, bien = 0, sinPar = [];
foreach (k, crudo in ::Const.Strings.PerkDescription) {
    local es = esDe(crudo);
    if (es == null) { sinPar.push(k); continue; }
    n++;
    // Lo que Legends habría mostrado con el par: el castellano recortado y con sus colores.
    if (comprueba("ventaja " + k, ::Legends.tooltip(crudo, []), original(es, []), true)) bien++;
}
print("  ventajas en castellano: " + bien + " / " + n + "\n");
print("  sin par en el corpus: " + sinPar.len() + (sinPar.len() ? " (" + sinPar.reduce(@(a, b) a + ", " + b) + ")" : "") + "\n");

print("=== runas (runes_*.nut) ===\n");
local runas = [];
::Legends.Rune <- {};
::Legends.Runes <- {Target = {Weapon = 0, Helmet = 1, Shield = 2, Armor = 3},
                    add = function ( _r ) { runas.push(_r); return runas.len() - 1; }};
foreach (f in ["runes_weapon", "runes_helmet", "runes_shield", "runes_armor"]) dofile(fuente + "config/" + f + ".nut", true);
local objeto = {getRuneBonus1 = @() 5, getRuneBonus2 = @() 7, isUpgraded = @() false};
n = 0; bien = 0;
foreach (r in runas) {
    foreach (campo, metodo in {Tooltip = "getTooltip", RuneTooltip = "getRuneTooltip"}) {
        if (!(metodo in r)) continue;
        // Las variables que monta la propia runa, capturadas con un tooltip de paso.
        local capturado = null, enganchado = ::Legends.tooltip;
        ::Legends.tooltip = function ( _t, _v = [] ) { capturado = clone _v; return ""; };
        r[metodo](objeto);
        ::Legends.tooltip = enganchado;
        n++;
        local es = esDe(r[campo]);
        if (es == null) { comprueba("runa " + r.Name + "." + campo + " tiene par", "no", "sí"); continue; }
        if (comprueba("runa " + r.Name + "." + campo, r[metodo](objeto), original(es, capturado), true)) bien++;
    }
}
print("  runas en castellano: " + bien + " / " + n + "\n");

print("=== línea de grupos de ventajas (afterHooks/perk_tooltips.nut) ===\n");
local perks = ["LegendAnchor", "LegendFirstBlood", "LegendBallistics", "LegendBackswing", "LegendDebilitate"];
::Const.Perks <- {
    ShieldTree = {Name = "Shield", Tree = [[0, 1]]},
    SwordTree = {Name = "Sword", Tree = [[1, 2]]},
    AxeTree = {Name = "Axe", Tree = [[2]]},
    MaceTree = {Name = "Mace", Tree = [[2]]},
    InventorClassTree = {Name = "Inventor", Tree = [[3]]},
    BowTree = {Name = "Bow", Tree = []},
    PerkDefObjects = perks.map(@(c) {Const = c, Tooltip = ""})
};
// El castellano esperado: la descripción del par, los saltos que haya puesto
// Legends y la línea con cada grupo traducido por su par, en el orden en que
// Legends los haya enumerado.
local GRUPO = "[color=#0b0084]From the ";
local function esperado( _tooltip, _desc ) {
    local i = _tooltip.find(GRUPO), j = _tooltip.find(" perk group", i), k = i;
    while (k > 0 && _tooltip[k - 1] <= ' ') k--;
    local nombres = Str.split(" or ", _tooltip.slice(i + GRUPO.len(), j));
    local lista = nombres;
    if (nombres.len() > 1) {
        lista = Str.split(", ", nombres[0]);
        lista.push(nombres[1]);
    }
    // Tres grupos tienen nombre propio, distinto del par global del juego base.
    local propios = {Sword = "Espada", Polearm = "Arma de asta", Sturdy = "Recio"};
    local es = lista.map(@(g) g in propios ? propios[g] : ::Rosetta.translate(g));
    local cab = es.len() == 1 ? "Del grupo de ventajas " + es[0]
        : "De los grupos de ventajas " + Str.join(", ", es.slice(0, -1)) + " o " + es.top();
    return _desc + _tooltip.slice(k, i) + "[color=#0b0084]" + cab + "[/color]";
}
local crudos = clone ::Const.Strings.PerkDescription;
foreach (vuelta in ["primera carga", "vuelta al menú principal"]) {
    dofile(fuente + "afterHooks/perk_tooltips.nut", true);
    foreach (i, c in perks) {
        local tt = ::Const.Perks.PerkDefObjects[i].Tooltip;
        if (tt == "") continue;  // ventaja sin grupo en este árbol de prueba
        comprueba(vuelta + ", " + c + ": una sola línea de grupos", Str.split(GRUPO, tt).len() - 1, 1);
        // translatePerk y el tooltip de la ventaja traducen el Tooltip entero.
        comprueba(vuelta + ", " + c, ::Rosetta.translate(tt), esperado(tt, original(esDe(crudos[c]), [])));
    }
}

print("=== tienda de entrenamiento y de reparaciones ===\n");
local verde = "[color=#00ff01]";
foreach (caso in [
    ["After practicing Short Guard for hours, Hackett feels ready for a fight and gains " + verde + "120[/color] XP.",
     "Tras practicar la Guardia corta durante horas, Hackett se siente a punto para pelear y gana " + verde + "120[/color] de experiencia."],
    ["After practicing hand to hand combat as long as possible, Hackett el Valiente is ready for a scrap and gains a " + verde + "10%[/color] xp increase for the next battle.",
     "Tras practicar combate cuerpo a cuerpo todo lo posible, Hackett el Valiente está a punto para una buena trifulca y gana un " + verde + "10%[/color] más de experiencia en la próxima batalla."],
    ["Hackett finds a stance that feels more natural and gains " + verde + "80[/color] XP.",
     "Hackett encuentra una postura que le resulta más natural y gana " + verde + "80[/color] de experiencia."],
    ["Hackett is ready to learn more in the next battle and gains a " + verde + "10%[/color] xp increase for the next battle.",
     "Hackett tiene ganas de aprender más en la próxima batalla y gana un " + verde + "10%[/color] más de experiencia en la próxima batalla."],
]) comprueba(caso[0], ::Rosetta.translate(caso[0]), caso[1]);
local rep = "This tent repairs damaged items in your stash and equipped fighers. Equipment is repaired one item at time in the order they were queued.At the end of a battle, any damaged equipped gear is added to the front of the repair queue.\n\nItems will repair very slowly when not camped. Camping increases the speed even with no one assigned. Default repair speed is based on game combat difficulty.The more people assigned to the repair tent, the quicker the repairs. Mercenaries with repair skills increase the speed even further and may save you tools.\n\nBuying an upgraded tent from a settlement will increase repair speed by " + verde + "33%[/color] and increase tool efficiency by " + verde + "33%[/color] (1 tool repairs 20 instead of 15).";
local r = ::Rosetta.translate(rep);
comprueba("tienda de reparaciones en castellano", r.find("Esta tienda repara") == 0 && r.find(verde + "33%[/color] (1 herramienta") != null, true);

print("=== reglas que casaban con cualquier frase ===\n");
local azul = "[color=#1e468f]";
foreach (caso in [
    ["Something nobody translated and left alone", "Something nobody translated and left alone"],
    ["Something nobody translated on purpose", "Something nobody translated on purpose"],
    ["Hackett finds something nobody translated", "Hackett finds something nobody translated"],
    // Con " has ": el rasgo de foso de la 1.0.1 ya traduce su propio texto, así
    // que la guardia va con una frase que no es de nadie.
    ["This character has done something nobody translated and did so twice.",
     "This character has done something nobody translated and did so twice."],
    [azul + "Hackett[/color] imbued " + azul + "Bors[/color]", azul + "Hackett[/color] imbuyó de poder a " + azul + "Bors[/color]"],
    [azul + "Hackett[/color] levitated " + azul + "Bors[/color] leaving them free to move", azul + "Hackett[/color] hizo levitar a " + azul + "Bors[/color], que ahora puede moverse libremente"],
    [azul + "Hackett[/color] levitated " + azul + "Bors[/color]", azul + "Hackett[/color] hizo levitar a " + azul + "Bors[/color]"],
    [azul + "Hackett[/color] gives Venda to " + azul + "Bors[/color]", azul + "Hackett[/color] da Venda a " + azul + "Bors[/color]"],
    ["Hackett finds Pergamino antiguo", "Hackett encuentra Pergamino antiguo"],
    ["Hackett receives a Prosthetic Ear", "Hackett recibe " + ::Rosetta.translate("Prosthetic Ear")],
]) comprueba(caso[0], ::Rosetta.translate(caso[0]), caso[1]);
foreach (clase in ["scripts/items/legend_armor/legend_armor", "scripts/items/legend_helmets/legend_helmet"]) {
    local q = {};
    q.setdelegate({_set = function ( _k, _v ) { this.rawset(_k, _v); }});
    enganches[clase](q);
    comprueba(clase + ".makeName", q.makeName(@() "Hombreras de cuero on Sobrevesta acolchada")(),
              "Hombreras de cuero sobre Sobrevesta acolchada");
}

print("=== nombres de grupo propios (Sword, Polearm, Sturdy) ===\n");
local linea = "Hola.\n[color=#0b0084]";
foreach (caso in [
    ["Sword perk group", "Del grupo de ventajas Espada"],
    ["Shield or Sword perk groups", "De los grupos de ventajas Escudo o Espada"],
    ["Polearm, Shield or Axe perk groups", "De los grupos de ventajas Arma de asta, Escudo o Hacha"],
    ["Shield, Axe, Mace or Sturdy perk groups", "De los grupos de ventajas Escudo, Hacha, Maza o Recio"],
    ["Shield, Berserker or Axe perk groups", "De los grupos de ventajas Escudo, Berserker o Hacha"],
]) comprueba("línea «" + caso[0] + "»", ::Rosetta.translate(linea + "From the " + caso[0] + "[/color]"),
             linea + caso[1] + "[/color]");
// Los pares globales no cambian: siguen siendo el objeto y el adjetivo.
foreach (en, es in {Sword = "Espada recta", Polearm = "Alabarda", Sturdy = "de recio porte"})
    comprueba("par global " + en, ::Rosetta.translate(en), es);
{
    local q = {};
    q.setdelegate({_set = function ( _k, _v ) { this.rawset(_k, _v); }});
    enganches["scripts/skills/backgrounds/character_background"](q);
    local filas = [{id = 1, type = "text", text = "Sword"}];
    q.extendKnownPerksTooltip(function ( _arr ) {
        foreach (g in ["Sword", "Polearm", "Sturdy", "Shield"]) _arr.push({id = 2, type = "textDualColumn", text = g});
    })(filas);
    comprueba("grupos conocidos del personaje",
              Str.join(", ", filas.map(@(f) ::Rosetta.translate(f.text))), "Espada recta, Espada, Arma de asta, Recio, Escudo");
    // Línea de aptitudes: una descripción por grupo, para que el sorteo no importe.
    if (!("Math" in getroottable())) ::Math <- {rand = @(_a, _b) _a};
    local grupos = ["heavy armor", "light armor", "cloth armor"].map(@(d) {Descriptions = [d]});
    local aptitud = q.getPerkTreeGroupDescription(null);
    comprueba("aptitudes, un grupo", aptitud(grupos.slice(0, 1), "Likes wearing"), "Le gusta llevar armadura pesada.\n");
    comprueba("aptitudes, dos grupos", aptitud(grupos.slice(0, 2), "Likes wearing"),
              "Le gusta llevar armadura pesada y armadura ligera.\n");
    comprueba("aptitudes, tres grupos", aptitud(grupos, "Likes wearing"),
              "Le gusta llevar armadura pesada, armadura ligera y armadura de tela.\n");
    comprueba("aptitudes, sin prefijo", aptitud(grupos.slice(0, 1)), " armadura pesada.\n");
    comprueba("aptitudes, sin grupos", aptitud([], "Likes wearing"), "");
}
{
    local q = {};
    q.setdelegate({_set = function ( _k, _v ) { this.rawset(_k, _v); }});
    enganches["scripts/entity/tactical/legends_player_horserider"](q);
    local jinete = {m = {Name = ""}, getHorse = @() {getName = @() "Rocinante"}};
    q.setScenarioValues(function () { this.m.Name = "Hackett el Valiente and Rocinante"; }).call(jinete);
    comprueba("nombre del jinete y su caballo", jinete.m.Name, "Hackett el Valiente y Rocinante");
}
comprueba("ventaja del libro", ::Rosetta.translate("[leg_img](gfx/ui/perks/clarity.png,height=20px,width=20px)[/leg_img] [color=%perk%]Clarity[/color]"),
          "[leg_img](gfx/ui/perks/clarity.png,height=20px,width=20px)[/leg_img] [color=%perk%]" + ::Rosetta.translate("Clarity") + "[/color]");

print("=== textos montados con colores o format() ===\n");
::Const.UI.getColorized = @(_t, _c) "[color=" + _c + "]" + _t + "[/color]";
{
    // La descripción de la Cocina del campamento sale del getDescription real de Legends.
    local f = file(getenv("LEGENDS_DIR") + "/scripts/entity/world/camp/buildings/hunter_building.nut", "r");
    local src = "", b = f.readblob(f.len());
    foreach (c in b) src += c.tochar();
    local ini = src.find("local desc"), fin = src.find("return desc;", ini);
    ::Const.UI.Color.getHighlightLightBackgroundValue <- @() "#1e468f";
    ::Const.UI.Color.PositiveValue <- "#135213";
    ::Const.HuntingLoot <- {ExpertHunterBackgrounds = [0, 1], RequiredBackgrounds = ["Hunter", "Poacher"]};
    ::Const.LegendMod.Language <- {arrayToText = @(_a, _y, _c) _a[0] + " " + _y + " " + _a[1]};
    local r = ::Rosetta.translate(compilestring(src.slice(ini, fin + "return desc;".len()))());
    comprueba("Cocina del campamento en castellano", r.find("Las partidas de caza") == 0
              && r.find("[color=#1e468f]Destiladores[/color]") != null && r.find("Hunter and Poacher\n\nTrasfondos de cocina") != null, true);
}
foreach (caso in [
    ["Hackett has received a Voice of Davkul", "Hackett ha recibido " + ::Rosetta.translate("Voice of Davkul")],
    ["Hackett and Bors leave your party", "Hackett and Bors abandonan tu grupo"],
    ["You spend [color=#ff0001]12[/color] Tools and Supplies", "Gastas [color=#ff0001]12[/color] Herramientas y suministros"],
    ["[color=#135213]15%[/color] Favoured Enemy (also grants [color=#135213]+15%[/color] max damage)",
     "[color=#135213]15%[/color] Enemigo predilecto (además otorga [color=#135213]+15%[/color] de daño máximo)"],
    ["[color=%negative%]Can't loot any equipment from this entity[/color]", "[color=%negative%]No se puede saquear su equipo[/color]"],
    ["<span style=\"color:%negative%;\"><u>No Brewers</u></span>", "<span style=\"color:%negative%;\"><u>Sin destiladores</u></span>"],
    // Reglas con la captura dentro de una etiqueta: claves.nut las archiva bajo una palabra real.
    ["[color=%positive%]3[/color] Perk point", "[color=%positive%]3[/color] punto de ventaja"],
    ["[color=%negative%]-2[/color] Vision", "[color=%negative%]-2[/color] Visión"],
    ["+[color=%positive%]10%[/color] Melee Damage", "+[color=%positive%]10%[/color] Daño cuerpo a cuerpo"],
]) comprueba(caso[0], ::Rosetta.translate(caso[0]), caso[1]);

print("FALLOS: " + ::probe.fallos + "\n");
