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
::Const.LegendMod <- {};
dofile(getenv("LEGENDS_DIR") + "/mod_legends/config/z_legends_language.nut", true);
::BattleBrothersEs <- {TitulosFemeninos = {}, Hechos = {}};
::MSU <- {String = {replace = function ( _s, _find, _rep ) {
    local i = _s.find(_find);
    return i == null ? _s : _s.slice(0, i) + _rep + _s.slice(i + _find.len());
}}};
local porNombre = {}.setdelegate({_get = @(_k) _k});
::Legends <- {Perk = porNombre, Effect = porNombre};
local enganches = {};
// Si un fichero se engancha dos veces (hookTree de camp_building), se encadenan.
local engancha = function ( _src, _f ) {
    if (!(_src in enganches)) { enganches[_src] <- _f; return; }
    local antes = enganches[_src];
    enganches[_src] = function ( _q ) { antes(_q); _f(_q); };
};
::Hooks.getMod <- @(_id) {hookTree = engancha, hook = engancha};
::mods_hookNewObject <- engancha;
::mods_hookNewObjectOnce <- engancha;
::mods_hookBaseClass <- engancha;
::mods_hookExactClass <- engancha;
// La plantilla del juego, sin Rosetta: el wrapper de Rosetta se emula aparte.
local function plantilla( _text, _vars ) {
    foreach (v in _vars) _text = Str.replace(_text, "%" + v[0] + "%", "" + v[1]);
    return _text;
}
::buildTextFromTemplate <- @(_text, _vars) plantilla(::Rosetta._(_text), _vars);

dofile(fuente + "!!config/_color_ui.nut", true);
dofile(fuente + "!!config/_tooltip_templates.nut", true);
::ModJimmysTooltips <- {modTacticalTooltip = @(_t, _s, _e) _t};
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
    filas = [{id = 1, type = "text", text = "x"}];
    q.extendKnownPerksTooltip(function ( _arr ) {
        _arr.push({id = 2, type = "text", text = "\n[u]Weapon[/u]"});
        foreach (g in ["Trained", "Swordsman"]) _arr.push({id = 2, type = "textDualColumn", text = g});
        _arr.push({id = 3, type = "text", text = "\n[u]Enemy[/u]"});
    })(filas);
    comprueba("cabeceras y grupos sin par", Str.join("|", filas.slice(1).map(@(f) f.text)),
              "\n[u]Armas[/u]|Entrenado|Espadachín|\n[u]Enemigos[/u]");
    ::Const.BackgroundTypeName <- {Female = "Female"};
    ::Const.BackgroundType <- {Female = 1};
    local fondo = {isBackgroundType = @(_t) true};
    comprueba("tipo de trasfondo", q.getBackgroundTypes(null).call(fondo),
              "[color=%negative%]Tipo de trasfondo: " + ::Rosetta._("Female") + "[/color]");
    local terreno = q.getBackgroundDescriptionTooltip(@(_d) [
        {id = 6, type = "hint", text = "[u]Terrain Movement Modifiers[/u]"},
        {id = 6, type = "hint", icon = "ui/icons/tracking_disabled.png", text = "Swamps [color=#135213]+25%[/color]"}])(false);
    comprueba("línea de terreno", terreno[1].text, ::Rosetta._("Swamps") + " [color=#135213]+25%[/color]");
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
    local r = ::Rosetta.translate(compilestring(src.slice(ini, fin + "return desc;".len()))());
    comprueba("Cocina del campamento en castellano", r.find("Las partidas de caza") == 0
              && r.find("[color=#1e468f]Destiladores[/color]") != null && r.find(::Rosetta._("Hunter") + " y " + ::Rosetta._("Poacher") + "\n\nTrasfondos de cocina") != null, true);
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
    ["Preset Slot 8", "Ranura de preajuste 8"],
    // QA del 22/10.
    ["Contract Category: [color=%positive%]Battle[/color]", "Categoría del contrato: [color=%positive%]Batalla[/color]"],
    ["Successful hunt will take approximately [color=%positive%]inf[/color] hours.", "Sin nadie asignado a la tienda, la caza no terminará nunca."],
    ["Shieldmaiden", "Doncella escudera"],
    ["His wife's cherished [color=#0237bd]Ceremonial Staff[/color] has been stolen. This nobleman needs you to track it down or he'll never hear the end of it.",
     "Han robado [color=#0237bd]" + ::Rosetta._("Ceremonial Staff") + "[/color], la posesión más querida de la esposa de este noble. Necesita que des con ella o tendrá que oír reproches el resto de su vida."],
]) comprueba(caso[0], ::Rosetta.translate(caso[0]), caso[1]);
{
    // La negociación por objetos suma la entrada y el apéndice (contract_template_items.nut).
    local src = "", f = file(fuente + "!!config/contract_template__flavors_items.nut", "r"), b = f.readblob(f.len());
    foreach (ch in b) src += ch.tochar();
    ::Legends.ContractTemplate <- {};
    compilestring(src)();
    local h = ::Legends.ContractTemplate.Items.FlavorCampHuman;
    local r = ::Rosetta.translate(h.IsNegotiatingText + h.MultipleOfferAppendix);
    comprueba("negociación por objetos en castellano", r.find("este montón de %reward_item_count% objetos") != null && r.find("Yes. Good") == null, true);
}
{
    // Los consejos del campamento: uno por párrafo, cabecera y términos en color.
    local q = {};
    q.setdelegate({_set = function ( _k, _v ) { this.rawset(_k, _v); }});
    enganches["scripts/encounters/encounter"](q);
    ::Const.TipOfTheDay <- ["If you are having trouble killing trees, try bringing axes.",
        "Shields take minor damage each time they are used to deflect an attack, shield expert reduces this damage significantly."];
    local orig = @(_t, _f = true) "original: " + _t;
    local enc = {m = {Type = "encounter.legend_tips_encounter"}};
    local bt = q.buildText(orig);
    local primero = bt.call(enc, "Here are some tips for you:\n- a\n- b");
    comprueba("consejos: segundo clic igual", bt.call(enc, primero), primero);
    comprueba("consejos: el título va al original", bt.call(enc, "Tips"), "original: Tips");
    comprueba("consejos: otro encuentro va al original", bt.call({m = {Type = "x"}}, "Here are some tips for you:"), "original: Here are some tips for you:");
    local az = "[color=#1e468f]";
    comprueba("consejos del campamento", primero,
        az + "Aquí tienes algunos consejos:[/color]\n\n- Si te cuesta matar árboles, intenta llevar hachas.\n\n- Los escudos sufren un daño leve cada vez que se usan para desviar un ataque; la "
        + az + "ventaja[/color] Experto en escudos reduce considerablemente ese daño.");
    comprueba("consejos apuntados como ya traducidos", primero in ::BattleBrothersEs.Hechos, true);
}

{
    // El tooltip táctico de Jimmy's Tooltips: cabeceras y lista de ventajas.
    local f = @(_t) "[u][size=14]" + _t + "[/size][/u]";
    local filas = ::ModJimmysTooltips.modTacticalTooltip([
        {id = 150, type = "text", text = f("Status perks")},
        {id = 300, type = "text", text = f("Perks")},
        {id = 301, type = "text", icon = "ui/icons/perks.png", text = "[color=%negative%]F[/color]earsome, [color=%negative%]R[/color]otation"},
        {id = 400, type = "text", text = f("Equipped Items:")},
        {id = 701, type = "text", text = "Throwing Spear Ammo: infinite"},
        {id = 700, type = "hint", text = f("Chance to loot equipment:")}], null, null);
    comprueba("JT: cabecera de estado", filas[0].text, f("Ventajas de estado"));
    comprueba("JT: cabecera de ventajas", filas[1].text, f("Ventajas"));
    comprueba("JT: lista de ventajas", filas[2].text, "[color=%negative%]T[/color]emible, [color=%negative%]R[/color]otación");
    comprueba("JT: objetos equipados sin dos puntos", filas[3].text, f("Objetos equipados"));
    comprueba("JT: munición", filas[4].text, "Throwing Spear Munición: infinita");
    comprueba("JT: botín", filas[5].text, f("Probabilidad de saquear el equipo"));
}

comprueba("tropa con cifra exacta", ::Rosetta.translate("2 Ancient Auxiliaries"), "2 Soldados auxiliares ancestrales");

{
    // Las tiendas del campamento: traducidas, con cifras y términos en color,
    // y apuntadas como ya hechas.
    local q = {};
    q.setdelegate({_set = function ( _k, _v ) { this.rawset(_k, _v); }});
    enganches["scripts/entity/world/camp/camp_building"](q);
    local en = "Repairing equipment takes tools. Break down and reuse equipment in your stash to create tools to repair other gear. Once an item reaches zero durability, it will be consumed and destroyed. Every 30 durability equals a tool. \n\nThe more people assigned to the tent, the quicker items will be salvaged. People with salvage skills increase the speed further.\n\nThe salvage tent can be upgraded by purchasing a salvage cart from a settlement merchant. An upgraded tent has a 15% increase in salvage speed and every 10 durability equals a tool.\n\nHolding Alt and right clicking on an item in your inventory can send it to your repair or salvage queues";
    local filas = q.getTooltip(@() [{id = 1, type = "title", text = "x"}, {id = 2, type = "description", text = en}]).call({});
    local s = filas[1].text, az = "[color=#1e468f]", ve = "[color=#135213]";
    print("  tienda de desguace: " + s + "\n");
    comprueba("campamento: herramientas en color", s.find(az + "herramientas[/color]") != null, true);
    comprueba("campamento: durabilidad en color", s.find(az + "durabilidad[/color]") != null, true);
    comprueba("campamento: tienda mejorada en color", s.find(az + "tienda mejorada[/color]") != null, true);
    comprueba("campamento: 15% en color", s.find(ve + "15%[/color]") != null, true);
    comprueba("campamento: 30 en color", s.find(ve + "30[/color]") != null, true);
    comprueba("campamento: apuntada como hecha", s in ::BattleBrothersEs.Hechos, true);
    local sinPar = q.getTooltip(@() [{type = "description", text = "Zzz no pair 15%"}]).call({});
    comprueba("campamento: sin par, intacta", sinPar[0].text, "Zzz no pair 15%");
}

{
    // Requisitos del séquito de Legends (getRequirementsForUI).
    local o = {m = {ID = "follower.x"}, getRequirementsForUI = @() [{Text = "Discovered a legendary location", IsSatisfied = false}]};
    enganches["retinue/follower"](o);
    local r = o.getRequirementsForUI()[0].Text;
    comprueba("séquito: requisito traducido", r != "Discovered a legendary location" && r == ::Rosetta.translate("Discovered a legendary location"), true);
}

{
    // Título de encuentro (getUITitle) y oponente del obituario.
    local q = {};
    q.setdelegate({_set = function ( _k, _v ) { this.rawset(_k, _v); }});
    enganches["scripts/encounters/encounter"](q);
    comprueba("título de encuentro traducido", q.getUITitle(@() "Walking through the market...")(), ::Rosetta.translate("Walking through the market..."));
    local s = {MostPowerfulVanquished = "a Bandit Rabble Poacher"};
    local o = {m = {LifetimeStats = s}, getRosterTooltip = @() this.m.LifetimeStats.MostPowerfulVanquished};
    enganches["entity/tactical/player"](o);
    comprueba("obituario: oponente traducido", o.getRosterTooltip(), "un cazador furtivo de la chusma");
    comprueba("obituario: cabeza con cola ya traducida",
        ::Rosetta.translate("With the company for 3 days. El oponente más poderoso que venció fue un cazador furtivo de la chusma.").find("With the company") == null, true);
    comprueba("Hired by con nombre que no cambia", ::Rosetta.translate("Hired by Harlingen"), "Contratados por Harlingen");
    comprueba("renombre del campamento", ::Rosetta.translate("Your company lacks the renown necessary to accommodate more equipment in your camp. Attain at least 'Reputable' (1400) renown in order to unlock this space. Gain renown by completing ambitions and contracts, as well as by winning battles.").find("Your company") == null, true);
    comprueba("You gain a con artículo inglés", ::Rosetta.translate("You gain a Pico militar"), "Ganas Pico militar");
}

comprueba("objeto con runas", ::Rosetta.translate("Arming Sword[color=#bf2aac] (Runed)[/color]").find("(Runed)") == null, true);

// Funciones que Legends rehace en la instancia (mods_hookNewObject y Once):
// el enganche se registra después del suyo y traduce lo que devuelven.
{
    // El árbol de ventajas es compartido: el enganche tiene que devolver copias.
    local arbol = [[{ID = "perk.a", Name = "Pathfinder"}, {ID = "perk.b", Name = "Relentless"}]];
    local o = {addStatsToUIData = function (_e, _t) { _t.moraleLabel <- "Steady"; },
        convertCampaignStorageToUIData = @(_m) {dayName = _m[0], legendsVersion = _m[1]},
        convertEntityToUIData = @(_e, _a) {perkTree = arbol},
        convertEntityHireInformationToUIData = @(_e) {perkTree = arbol}};
    enganches["ui/global/data_helper"](o);
    local t = {};
    o.addStatsToUIData(null, t);
    comprueba("etiqueta de moral traducida", t.moraleLabel != "Steady" && t.moraleLabel == ::Rosetta.translate("Steady"), true);
    foreach (caso in [
        [["Day 14 (Veteran/Expert Ironman)", "Legends Version: 19.4.22"],
         [::Rosetta._("Veteran"), ::Rosetta._("Expert")], "Día 14 (%s/%s, Hombre de hierro)", "Versión de Legends: 19.4.22"],
        [["Day 3 (Beginner/Legendary)", ""], [::Rosetta._("Beginner"), ::Rosetta._("Legendary")], "Día 3 (%s/%s)", ""],
    ]) {
        local r = o.convertCampaignStorageToUIData(caso[0]);
        comprueba("partida guardada: " + caso[0][0], r.dayName, format(caso[2], caso[1][0], caso[1][1]));
        comprueba("partida guardada: versión", r.legendsVersion, caso[3]);
    }
    comprueba("partida guardada: dificultades traducidas", ::Rosetta._("Veteran") != "Veteran" && ::Rosetta._("Legendary") != "Legendary", true);
    foreach (fn, r in [o.convertEntityToUIData(null, null), o.convertEntityHireInformationToUIData(null)])
        comprueba("árbol de ventajas (" + ["ficha", "contratación"][fn] + ")", r.perkTree[0][0].Name + ", " + r.perkTree[0][1].Name,
                  ::Rosetta.translate("Pathfinder") + ", " + ::Rosetta.translate("Relentless"));
    comprueba("árbol de ventajas: nombre traducido", ::Rosetta.translate("Pathfinder") != "Pathfinder", true);
    comprueba("árbol de ventajas: el original no cambia", arbol[0][0].Name, "Pathfinder");
    local renombre = [{id = 1, type = "title", text = "Insufficient Renown"}];
    local cambio = [{id = 1, type = "title", text = "Switch to Wooden Shield"},
        {id = 2, type = "description", text = "Quickly switch to another item from your bag"},
        {id = 3, type = "text", text = "Costs [b][color=%positive%] 4[/color][/b] AP to switch"}];
    local te = {onQueryUIElementTooltipData = @(_e, _id, _o) clone renombre, onQueryFollowerTooltipData = @(_f) clone renombre,
        onQuerySkillTooltipData = @(_e, _s) _s == "objeto" ? cambio.map(@(f) clone f) : [{id = 1, type = "title", text = "Insufficient Renown"}]};
    enganches["ui/screens/tooltip/tooltip_events"](te);
    comprueba("tooltip propio de Legends (obituario)", te.onQueryUIElementTooltipData(0, "x", "y")[0].text, "Renombre insuficiente");
    comprueba("tooltip propio de Legends (séquito)", te.onQueryFollowerTooltipData(3)[0].text, "Renombre insuficiente");
    comprueba("cambio de objeto de la bolsa", Str.join(" | ", te.onQuerySkillTooltipData(1, "objeto").map(@(f) f.text)),
        "Cambiar a Wooden Shield | Cambia rápidamente a otro objeto de tu bolsa | Cambiar cuesta [b][color=%positive%] 4[/color][/b] PA");
    comprueba("tooltip de habilidad, sin tocar", te.onQuerySkillTooltipData(1, "skill")[0].text, "Insufficient Renown");

    // El pago: lo que devuelve el envoltorio de Legends cuando el del base ya
    // ha puesto "Pago" (bloque inglés aparte y coronas de relleno).
    foreach (bolsa in [0, 500]) {
        local c = {m = {ID = "x", Payment = {Pool = bolsa}}};
        c.getUIBulletpoints <- @(_o = true, _p = true) [
            {title = "Pago", items = [{icon = "", text = "Obtendrás 100 coronas"}]},
            {title = "Payment", items = [{icon = "", text = "You gain 2x Collar de cuentas on completion"}], fixed = true}];
        enganches["contracts/contract"](c);
        local r = c.getUIBulletpoints();
        comprueba("pago con bolsa " + bolsa, Str.join(" | ", r.map(@(e) e.title + ": " + Str.join(", ", e.items.map(@(i) i.text)))),
                  "Pago: " + (bolsa == 0 ? "" : "Obtendrás 100 coronas, ") + "Ganas 2x Collar de cuentas al completar");
    }
}
foreach (clase in ["scripts/items/legend_armor/legend_armor_upgrade", "scripts/items/legend_helmets/legend_helmet_upgrade"]) {
    local q = {};
    q.setdelegate({_set = function ( _k, _v ) { this.rawset(_k, _v); }});
    enganches[clase](q);
    comprueba(clase + ".getArmorDescription", q.getArmorDescription(@() "Insufficient Renown")(), "Renombre insuficiente");
}

print("=== listas de Legends y frases con HTML ===\n");
local lista = ::Const.LegendMod.Language.arrayToText;
comprueba("lista con y", lista(["Hackett", "Bors", "Otto"]), "Hackett, Bors y Otto");
comprueba("lista con e", lista(["Hackett", "Ivo"]), "Hackett e Ivo");
comprueba("lista con y ante hie-", lista(["Hackett", "Hierro"]), "Hackett y Hierro");
comprueba("lista con u", lista(["Bors", "Otto"], "or"), "Bors u Otto");
comprueba("lista de trasfondos", lista(["Barbarian", "Poacher"], "or"), "Bárbaro o " + ::Rosetta._("Poacher"));
local c = @(_t) "[color=#1e468f]" + _t + "[/color]";
foreach (caso in [
    ["[color=#8f1e1e]Imported[/color] from " + c("Tuchow") + " to " + c("Berg"),
     "[color=#8f1e1e]Importado[/color] de " + c("Tuchow") + " a " + c("Berg")],
    ["[color=#8f1e1e]Imported[/color] from " + c("Tuchow") + " to " + c("Berg") + " via " + lista(["Ulm", "Ivo"]),
     "[color=#8f1e1e]Importado[/color] de " + c("Tuchow") + " a " + c("Berg") + " pasando por Ulm e Ivo"],
    ["Requires Hunt Tier 3", "Requiere nivel de caza 3"],
]) comprueba(caso[0], ::Rosetta.translate(caso[0]), caso[1]);
{
    local q = {};
    q.setdelegate({_set = function ( _k, _v ) { this.rawset(_k, _v); }});
    enganches["scripts/entity/world/camp/buildings/hunter_building"](q);
    local rojo = "<span style=\"color:%negative%; padding-left: 2rem;\">";
    local info = q.getInfo(@() [
        "Current mode: <span style=\"color:#1e468f;\">Hunt</span>",
        "Current biome: <span style=\"color:#1e468f;\">on the plains</span>",
        "<s>- Wolf (around 3 hours)</s>",
        rojo + "Requires Hunt Tier 2</span>",
        rojo + "Requires " + lista(["Hunter", "Poacher"], "or") + "</span>",
        "<u>Forageable</u>",
    ])();
    foreach (i, esperado in [
        "Modo actual: <span style=\"color:#1e468f;\">Caza</span>",
        "Bioma actual: <span style=\"color:#1e468f;\">en las llanuras</span>",
        "<s>" + ::Rosetta._("- Wolf (around 3 hours)") + "</s>",
        rojo + "Requiere nivel de caza 2</span>",
        rojo + "Requiere " + ::Rosetta._("Hunter") + " o " + ::Rosetta._("Poacher") + "</span>",
        "<u>Recolectable</u>",
    ]) comprueba("campamento de caza, línea " + i, info[i], esperado);

    local bloque = @(_a, _b) "<div style='display: block;'><span style='font-size: 18px;'>" + _a + "</span><br><span style='color:#135213;'>" + _b + "</span></div>";
    local o = {queryRosterInformation = @() {Title = "Training Hall", SubTitle = "Have your men train for combat and learn from veterans",
        Roster = [{Training = [{name = bloque("Merciless Regimen", "Current: Iron Lungs")}, {name = "Thorough Training"}]}]},
        showTraitPopup = @(_t) _t};
    enganches["ui/screens/world/modules/world_town_screen/town_training_dialog_module"](o);
    local r = o.queryRosterInformation();
    comprueba("sala de entrenamiento: título", r.Title, ::Rosetta.translate("Training Hall"));
    comprueba("sala de entrenamiento: título traducido", r.Title != "Training Hall", true);
    comprueba("Merciless Regimen", r.Roster[0].Training[0].name, bloque("Régimen despiadado", "Actual: Iron Lungs"));
    comprueba("nombre de entrenamiento", r.Roster[0].Training[1].name, "Entrenamiento a fondo");
    local ve = "[color=#135213]";
    comprueba("aviso de rasgo entrenado", o.showTraitPopup("Trait " + ve + "Frugal[/color] gained. " + ve + "1[/color] perk point granted."),
        "Rasgo " + ve + "Frugal[/color] obtenido. Se otorga " + ve + "1[/color] punto de ventaja.");
    comprueba("aviso de rasgo cambiado", o.showTraitPopup("Trained trait changed to " + ve + "Frugal[/color]."),
        "El rasgo entrenado ha cambiado a " + ve + "Frugal[/color].");
}

print("=== pantallas que Legends rehace o añade ===\n");
{
    local o = {queryData = @() {RightInfo = "Pay a round for your mercenaries to get their spirits up ([img]gfx/ui/tooltips/money.png[/img]35)."}};
    enganches["ui/screens/world/modules/world_town_screen/town_tavern_dialog_module"](o);
    comprueba("taberna: ronda", o.queryData().RightInfo,
        "Paga una ronda a tus mercenarios para levantarles el ánimo ([img]gfx/ui/tooltips/money.png[/img]35).");

    local en = [{id = 41, name = "Basilisks", description = "[p=c][img]gfx/ui/events/event_05.png[/img][/p]\n[p=c]Fight against Basilisk Drones[/p]"}];
    o = {scenario_menu_module_onQueryData = @() en.map(@(e) clone e)};
    enganches["states/main_menu_state"](o);
    local r = o.scenario_menu_module_onQueryData()[0];
    comprueba("escenarios: nombre y descripción", r.name != en[0].name && r.description != en[0].description
        && r.name == ::Rosetta.translate(en[0].name) && r.description == ::Rosetta.translate(en[0].description), true);

    o = {queryData = @() {brothers = [], formationName = "Formation 3"}};
    enganches["ui/screens/character/character_screen"](o);
    comprueba("formación por defecto", o.queryData().formationName, "Formación 3");
    o = {queryData = @() {brothers = [], formationName = "Muro de escudos"}};
    enganches["ui/screens/character/character_screen"](o);
    comprueba("formación con nombre del jugador", o.queryData().formationName, "Muro de escudos");

    o = {updateProgress = @(_t) _t};
    enganches["ui/screens/loading/loading_screen"](o);
    comprueba("pantalla de carga", o.updateProgress("Building Settlements ..."), "Construyendo asentamientos ...");

    local q = {};
    q.setdelegate({_set = function ( _k, _v ) { this.rawset(_k, _v); }});
    enganches["scripts/entity/world/camp/buildings/healer_building"](q);
    local roster = q.getRoster(@() [{ID = 1, Injuries = [{id = "injury.x", name = "Pierced Hand"}]}])();
    comprueba("curandero del campamento: lesión", roster[0].Injuries[0].name, "Mano perforada");

    o = {addBrotherEnding = @(_b, _e, _p) _p ? "\n\nHackett se retiró." : ""};
    enganches["states/world/asset_manager"](o);
    local M = format("%c", 1);
    comprueba("epílogo: final de hermano marcado", o.addBrotherEnding([], [], true), M + "\n\nHackett se retiró." + M);
    comprueba("epílogo: sin final, sin marca", o.addBrotherEnding([], [], false), "");

    // Encuentros: filas de resultado, sin tocar la lista de la pantalla.
    q = {};
    q.setdelegate({_set = function ( _k, _v ) { this.rawset(_k, _v); }});
    enganches["scripts/encounters/encounter"](q);
    local filas = [{id = 10, icon = "ui/icons/special.png", text = "Barbering unlocked in camp"}];
    local lista = q.getUIList(@() [{title = "", items = filas, fixed = false}])();
    comprueba("encuentro: fila de resultado", lista[0].items[0].text, "Barbería desbloqueada en el campamento");
    comprueba("encuentro: lista de la pantalla intacta", filas[0].text, "Barbering unlocked in camp");
}
{
    // Jimmy's Tooltips: efectos de cada herida en children.
    local filas = ::ModJimmysTooltips.modTacticalTooltip([
        {id = 200, type = "text", text = "Pierced Hand", children = [{id = 1, type = "text", text = "[color=%negative%]-10[/color] Melee Skill"}]}], null, null);
    comprueba("JT: efecto de herida", filas[0].children[0].text, ::Rosetta.translate("[color=%negative%]-10[/color] Melee Skill"));
    comprueba("JT: efecto de herida traducido", filas[0].children[0].text.find("Melee Skill") == null, true);
}
{
    // La ventaja Adaptativo sin activar: lista de grupos de cualquier tamaño.
    local q = {};
    q.setdelegate({_set = function ( _k, _v ) { this.rawset(_k, _v); }});
    enganches["scripts/skills/perks/perk_legend_adaptive"](q);
    local hints = @(_lista) q.getUnactivatedPerkTooltipHints(@(_a = null) [{id = 3, type = "hint", icon = "ui/tooltips/positive.png",
        text = "Activating this Perk will randomly grant one of the following Perk Groups:\n[color=#0b0084]" + _lista + "[/color]"}])()[0].text;
    local cab = "Activar esta ventaja otorgará al azar uno de los siguientes grupos de ventajas:\n[color=#0b0084]";
    local g = @(_n) ::Rosetta._(_n);
    comprueba("Adaptativo, cinco grupos", hints("Agile, Tenacious, Martyr, Vicious, or Trained"),
        cab + g("Agile") + ", " + g("Tenacious") + ", " + g("Martyr") + ", " + g("Vicious") + " o Entrenado[/color]");
    comprueba("Adaptativo, dos grupos con nombre propio", hints("Sword, or Polearm"), cab + "Espada o Arma de asta[/color]");
    local uno = "Activating this Perk will grant the following Perk Group:\n[color=#0b0084]Sword[/color]";
    comprueba("Adaptativo, un grupo: lo deja al corpus", q.getUnactivatedPerkTooltipHints(@(_a = null) [{type = "hint", text = uno}])()[0].text, uno);
}

print("FALLOS: " + ::probe.fallos + "\n");
