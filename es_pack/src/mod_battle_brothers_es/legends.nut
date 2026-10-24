// Enganche con Legends. Lo incluye el preload (mod_battle_brothers_es.nut)
// desde su cola, solo si Legends está y después de él: para entonces Legends
// ya ha definido ::Const.LegendMod (config/z_legends_language.nut), y los
// tokens no se rellenan hasta que el juego compone un texto en partida.
local mod = ::Hooks.getMod("mod_battle_brothers_es");
local L = ::Const.LegendMod;

// Envuelve _o[_nombre] con lo que devuelve _fabrica(original). Si una versión
// de Legends quita o renombra la función, no se envuelve: ese texto sale en
// inglés, pero la clase carga sin error.
local envuelveSq = function (_o, _nombre, _fabrica) {
    if (_nombre in _o && typeof _o[_nombre] == "function") _o[_nombre] = _fabrica(_o[_nombre]);
}

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
// Swordsman y Trained no tienen par global (Swordsman es también nombre de
// token); van con el nombre que les dan las reglas de la línea de grupo.
local GRUPOS = {Sword = "Espada", Polearm = "Arma de asta", Sturdy = "Recio",
                Swordsman = "Espadachín", Trained = "Entrenado"};
// Las cabeceras de categoría llegan como "\n[u]Weapon[/u]", sin par.
local CATEGORIAS = {Weapon = "Armas", Defense = "Defensa", Traits = "Rasgos", Enemy = "Enemigos",
                    Class = "Clase", Profession = "Profesión", Magic = "Magia", Other = "Otros", Special = "Especial"};
// hook y no hookTree: Legends define las dos funciones solo en esta clase, y en
// las subclases Modern Hooks 0.6.0 rehace getPerkTreeGroupDescription con
// compilestring y escribe su `_prefix = ""` como `_prefix = `, que no compila.
mod.hook("scripts/skills/backgrounds/character_background", function (q) {
    q.extendKnownPerksTooltip = @(__original) function (_arr) {
        local n = _arr.len();
        __original(_arr);
        for (local i = n; i < _arr.len(); i++) {
            local fila = _arr[i];
            if (!("type" in fila)) continue;
            if (fila.type == "textDualColumn" && fila.text in GRUPOS)
                fila.text = GRUPOS[fila.text];
            else if (fila.type == "text" && ::std.Str.startswith(fila.text, "\n[u]")) {
                local c = fila.text.slice(4, -4);
                if (c in CATEGORIAS) fila.text = "\n[u]" + CATEGORIAS[c] + "[/u]";
            }
        }
    }
    // «Background Type: Female, Crusader» se compone con los nombres de
    // ::Const.BackgroundTypeName; el corpus tiene cada nombre, no la suma.
    q.getBackgroundTypes = @(__original) function () {
        local ret = "";
        foreach (type, name in ::Const.BackgroundTypeName)
            if (this.isBackgroundType(::Const.BackgroundType[type])) ret += ::Rosetta._(name) + ", ";
        if (ret.len() == 0) return "";
        return "[color=%negative%]Tipo de trasfondo: " + ret.slice(0, -2) + "[/color]";
    }
    // Las líneas de terreno son "<Terreno> [color=...]+25%[/color]", con el
    // nombre inglés de una tabla local de la función.
    q.getBackgroundDescriptionTooltip = @(__original) function (_desc) {
        local ret = __original(_desc);
        foreach (fila in ret)
            if ("icon" in fila && fila.icon == "ui/icons/tracking_disabled.png" && typeof fila.text == "string") {
                local i = fila.text.find(" [color");
                if (i != null) fila.text = ::Rosetta._(fila.text.slice(0, i)) + fila.text.slice(i);
            }
        return ret;
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

// Legends sustituye addStatsToUIData entero (hooks/ui/global/data_helper.nut)
// con mods_hookNewObjectOnce, que escribe en la instancia y tapa cualquier
// enganche de clase, también el del caso 14 de los hooks. La etiqueta de la
// barra de moral ("Steady") se traduce con el mismo mecanismo, registrado
// después del suyo.
// Lo mismo con otras tres que Legends sustituye ahí: la lista de partidas
// guardadas («Day 14 (Veteran/Expert Ironman)» y «Legends Version: ...») y el
// árbol de ventajas de la ficha y de la contratación, cuyas ventajas llevan
// el Name inglés de PerkDefObjects (el diálogo de desbloqueo lo pinta tal
// cual). El árbol se copia: es el del personaje.
::mods_hookNewObjectOnce("ui/global/data_helper", function (o) {
    envuelveSq(o, "addStatsToUIData", @(addStats) function (_entity, _target) {
        addStats.call(this, _entity, _target);
        if ("moraleLabel" in _target) _target.moraleLabel = ::Rosetta._(_target.moraleLabel);
    })
    envuelveSq(o, "convertCampaignStorageToUIData", @(partida) function (_meta) {
        local r = partida.call(this, _meta);
        foreach (k in ["dayName", "legendsVersion"])
            if (k in r && typeof r[k] == "string" && r[k] != "") r[k] = ::Rosetta._(r[k]);
        return r;
    })
    local arbol = function (r) {
        if ("perkTree" in r && typeof r.perkTree == "array")
            r.perkTree = r.perkTree.map(@(fila) fila.map(function (p) {
                local c = clone p;
                if ("Name" in c && typeof c.Name == "string") c.Name = ::Rosetta._(c.Name);
                return c;
            }));
        return r;
    }
    envuelveSq(o, "convertEntityToUIData", @(ficha) function (_entity, _activeEntity) { return arbol(ficha.call(this, _entity, _activeEntity)); })
    envuelveSq(o, "convertEntityHireInformationToUIData", @(contrata) function (_entity) { return arbol(contrata.call(this, _entity)); })
})

// El pago de los contratos. El enganche del base (caso 2 de los hooks) pasa
// "Payment" a "Pago" por dentro del de Legends (hooks/contracts/contract.nut),
// que busca "Payment" para añadirle los objetos y quitar las 100 coronas de
// relleno cuando no hay bolsa. Como no lo encuentra, añade un segundo bloque
// "Payment" en inglés. Este enganche va por fuera de los dos: funde ese bloque
// en el de "Pago" y hace lo que Legends no pudo.
::mods_hookBaseClass("contracts/contract", function (o) {
    while (!("ID" in o.m)) o = o[o.SuperName];
    envuelveSq(o, "getUIBulletpoints", @(getUIBulletpoints) function (_objectives = true, _payment = true) {
        local ret = getUIBulletpoints.call(this, _objectives, _payment);
        if (!_payment) return ret;
        local pago = null, extra = null, PAGO = ::Rosetta._("Payment");
        foreach (e in ret)
            if ("title" in e) {
                if (e.title == "Payment") extra = e;
                else if (e.title == PAGO) pago = e;
            }
        if (extra == null) return ret;
        // " on completion" se separa a mano: "You gain <item:str>" del base casaría con la frase entera.
        local COLA = " on completion";
        foreach (it in extra.items)
            it.text = ::std.Str.endswith(it.text, COLA)
                ? ::Rosetta._(it.text.slice(0, -COLA.len())) + " al completar" : ::Rosetta._(it.text);
        if (pago == null) {
            extra.title = PAGO;
            return ret;
        }
        if (this.m.Payment.Pool == 0) pago.items = [];
        pago.items.extend(extra.items);
        ret.remove(ret.find(extra));
        return ret;
    })
})

// Lo mismo con dos consultas de tooltip que Legends rehace en la instancia
// (hooks/ui/screens/tooltip/obituary_tooltips.nut y tooltip_events.nut): sus
// ramas propias (cabeceras del obituario, huecos del séquito) devuelven el
// texto sin pasar por el enganche de Rosetta. Lo que ya llega en castellano
// por la rama original sale igual.
local traducirTooltip = function (orig) {
    return function (...) {
        vargv.insert(0, this);
        return ::Rosetta.translateTooltip(orig.acall(vargv));
    }
}
::mods_hookNewObject("ui/screens/tooltip/tooltip_events", function (o) {
    foreach (f in ["onQueryUIElementTooltipData", "onQueryFollowerTooltipData"]) envuelveSq(o, f, traducirTooltip);
    // En las habilidades, solo la rama de Legends para cambiar de objeto de la
    // bolsa («Switch to ...»); las demás ya llegan traducidas.
    envuelveSq(o, "onQuerySkillTooltipData", @(skill) function (_entityId, _skillId) {
        local r = skill.call(this, _entityId, _skillId);
        return r != null && r.len() > 0 && "text" in r[0] && typeof r[0].text == "string"
            && ::std.Str.startswith(r[0].text, "Switch to ") ? ::Rosetta.translateTooltip(r) : r;
    })
})

// El campamento de Legends manda a su pantalla los títulos y nombres en
// inglés: el título y el subtítulo de la ventana (camp_manager), los de cada
// diálogo de tienda (queryLoad, o queryRosterInformation en barbero y pintura)
// y el nombre de cada tienda (camp_building.getName y getTitle). Los pares
// están en el corpus; aquí pasan por Rosetta.
local tituloES = function (_t) {
    foreach (k in ["Title", "SubTitle"]) if (k in _t && typeof _t[k] == "string") _t[k] = ::Rosetta._(_t[k]);
    return _t;
}
mod.hook("scripts/states/world/camp_manager", function (q) {
    q.getUIInformation = @(__original) function () { return tituloES(__original()); }
})
local CAMP = "scripts/ui/screens/world/modules/camp_screen/camp_";
foreach (m in ["commander", "crafting", "enchanter", "healer", "repair", "workshop"])
    mod.hook(CAMP + m + "_dialog_module", function (q) {
        q.queryLoad = @(__original) function () { return tituloES(__original()); }
    })
foreach (m in ["barber", "painter"])
    mod.hook(CAMP + m + "_dialog_module", function (q) {
        q.queryRosterInformation = @(__original) function () { return tituloES(__original()); }
    })
mod.hookTree("scripts/entity/world/camp/camp_building", function (q) {
    q.getName = @(__original) function () { return ::Rosetta._(__original()); }
    q.getTitle = @(__original) function () { return ::Rosetta._(__original()); }
})
// La tienda de curación lista las lesiones con getNameOnly, que no pasa por
// Rosetta; se traducen aquí y no en el getter, como el templo (caso 36).
mod.hook("scripts/entity/world/camp/buildings/healer_building", function (q) {
    q.getRoster = @(__original) function () {
        local ret = __original();
        foreach (e in ret) foreach (i in e.Injuries) i.name = ::Rosetta._(i.name);
        return ret;
    }
})

// Jimmy's Tooltips, que viene en el zip de Legends, crea sus ajustes de MSU sin
// nombre visible, y MSU muestra el id ("ItemDurability"). Se les pone nombre
// sin tocar el id, que es lo que guarda la configuración. La cola va tras la
// suya; si el mod falta o cambia sus ids, no se toca nada.
if ("ModJimmysTooltips" in getroottable() && "Mod" in ::ModJimmysTooltips) try {
    local ajustes = ::ModJimmysTooltips.Mod.ModSettings;
    local pagina = ajustes.getPage("page_one");
    pagina.Name = "Ficha táctica de Jimmy";
    pagina.get("title").Name = "Puedes elegir qué se ve en la ficha táctica";
    foreach (id, nombre in {DefaultTooltip = "Ficha por defecto", ProgressBarValues = "Valores en las barras",
            Items = "Objetos", ItemDurability = "Durabilidad de objetos", Skills = "Habilidades", Stats = "Atributos"})
        ajustes.getSetting(id).Name = nombre;
} catch (e) {}

// Legends une las listas con arrayToText («A, B and C»), y una captura del corpus
// recibe la lista entera con su «and». Aquí se traduce cada elemento y la
// conjunción, con «e» y «u» ante i- y o-. Los trasfondos de la caza llegan con su
// nombre inglés; «Barbarian» tiene en el base el par adjetival «de bárbaros».
local arrayToText = L.Language.arrayToText;
local CONJ = {["and"] = ["y", "e", "i"], ["or"] = ["o", "u", "o"]};
L.Language.arrayToText = function (_arr, _finalSeparator = "and", _highlight = false) {
    local arr = _arr.map(@(s) s == "Barbarian" ? "Bárbaro" : ::Rosetta._(s));
    local sep = _finalSeparator;
    if (sep in CONJ && arr.len() > 1) {
        local c = CONJ[sep], ultimo = ::std.Str.replace(arr.top().tolower(), "h", "");
        sep = ultimo.len() > 0 && ultimo[0] == c[2][0] && !::std.Str.startswith(ultimo, "ie") ? c[1] : c[0];
    }
    return arrayToText(arr, sep, _highlight);
}

// La ventaja Adaptativo sin activar enumera los grupos que puede dar
// («A, B, or C»). El corpus solo tiene reglas de 2 y 3 grupos, y con la lista
// de rasgos son hasta 13; se rehace la línea con arrayToText y los nombres de
// grupo propios. Con un solo grupo siguen valiendo las reglas del corpus.
local ADAPTATIVO = "Activating this Perk will randomly grant one of the following Perk Groups:\n[color=#0b0084]";
mod.hookTree("scripts/skills/perks/perk_legend_adaptive", function (q) {
    q.getUnactivatedPerkTooltipHints = @(__original) function (_actor = null) {
        local ret = __original(_actor);
        foreach (h in ret) {
            if (!("text" in h) || typeof h.text != "string" || !::std.Str.startswith(h.text, ADAPTATIVO)
                    || !::std.Str.endswith(h.text, "[/color]")) continue;
            local nombres = [];
            foreach (p in split(h.text.slice(ADAPTATIVO.len(), -8), ",")) {
                p = strip(p);
                if (::std.Str.startswith(p, "or ")) p = p.slice(3);
                nombres.push(p in GRUPOS ? GRUPOS[p] : p);
            }
            h.text = ::Rosetta._(ADAPTATIVO.slice(0, -15)) + "[color=#0b0084]" + L.Language.arrayToText(nombres, "or") + "[/color]";
            ::BattleBrothersEs.Hechos[h.text] <- true;
        }
        return ret;
    }
})

// Las líneas de información del campamento de caza (getInfo) y los nombres de
// entrenamiento de la pantalla de adiestramiento llevan HTML (<span>, <u>, <div>),
// y un patrón de Rosetta no puede escribir «<» literal. Si la línea entera no
// tiene par, se traduce cada trozo de texto entre etiquetas.
local trozo = function (_t) {
    local s = strip(_t);
    if (s == "") return _t;
    local i = _t.find(s);
    if (::std.Str.startswith(s, "Requires ") && !::std.Str.startswith(s, "Requires Hunt Tier "))
        s = "Requiere " + s.slice(9);   // la lista ya llega traducida por arrayToText
    else if (::std.Str.startswith(s, "Current: "))
        s = "Actual: " + s.slice(9);    // nombre de rasgo, ya traducido por su getter
    else
        s = ::Rosetta._(s);
    return _t.slice(0, i) + s + _t.slice(i + strip(_t).len());
}
local trHTML = function (_s) {
    if (typeof _s != "string") return _s;
    local ret = ::Rosetta._(_s);
    if (ret != _s) return ret;
    ret = "";
    local i = 0;
    while (i < _s.len()) {
        local a = _s.find("<", i), b = a == null ? null : _s.find(">", a);
        if (b == null) return ret + trozo(_s.slice(i));
        ret += trozo(_s.slice(i, a)) + _s.slice(a, b + 1);
        i = b + 1;
    }
    return ret;
}
mod.hook("scripts/entity/world/camp/buildings/hunter_building", function (q) {
    q.getInfo = @(__original) function () { return __original().map(trHTML); }
})
// Legends reescribe entera queryRosterInformation de la sala de entrenamiento
// (mods_hookExactClass, con Title y SubTitle en inglés), y el barbero y el
// taxidermista ponen su SubTitle en inglés tras el original. Un
// mods_hookExactClass nuestro quedaba por DENTRO del suyo aunque se registrara
// después (prueba del 24/10: el título del taxidermista salía traducido y el
// subtítulo no), así que estos enganches van a la instancia ya creada
// (mods_hookNewObject), que siempre envuelve la función final.
local WTS = "ui/screens/world/modules/world_town_screen/";
::mods_hookNewObject(WTS + "town_training_dialog_module", function (o) {
    envuelveSq(o, "queryRosterInformation", @(f) function () {
        local ret = tituloES(f.call(this));
        foreach (e in ret.Roster)
            if ("Training" in e) foreach (t in e.Training) t.name = trHTML(t.name);
        return ret;
    })
    // El aviso de rasgo entrenado llega compuesto con format() y va directo a JS.
    envuelveSq(o, "showTraitPopup", @(popup) function (_text) { return popup.call(this, ::Rosetta._(_text)); })
})
foreach (m, fn in {town_barber_dialog_module = "queryRosterInformation", town_taxidermist_dialog_module = "queryBlueprints"})
    ::mods_hookNewObject(WTS + m, function (o) {
        envuelveSq(o, fn, @(f) function () { return tituloES(f.call(this)); })
    })
// La taberna: Legends pisa RightInfo en inglés después del original (caso 19).
::mods_hookNewObject(WTS + "town_tavern_dialog_module", function (o) {
    envuelveSq(o, "queryData", @(f) function () {
        local ret = f.call(this);
        if (ret != null && "RightInfo" in ret && typeof ret.RightInfo == "string") ret.RightInfo = ::Rosetta._(ret.RightInfo);
        return ret;
    })
})
// Más funciones que Legends sustituye entera o añade (mods_hookExactClass):
// el menú de escenarios (tapa el caso 3b), el nombre de la formación de la
// ficha («Formation 1»; el que escribe el jugador no tiene par y no cambia) y
// el texto de progreso de la pantalla de carga al generar el mapa.
::mods_hookNewObject("states/main_menu_state", function (o) {
    envuelveSq(o, "scenario_menu_module_onQueryData", @(f) function () {
        local ret = f.call(this);
        foreach (r in ret)
            foreach (k in ["name", "description"])
                if (k in r && typeof r[k] == "string") r[k] = ::Rosetta._(r[k]);
        return ret;
    })
})
::mods_hookNewObject("ui/screens/character/character_screen", function (o) {
    envuelveSq(o, "queryData", @(f) function () {
        local ret = f.call(this);
        if (ret != null && "formationName" in ret && typeof ret.formationName == "string")
            ret.formationName = ::Rosetta._(ret.formationName);
        return ret;
    })
})
::mods_hookNewObject("ui/screens/loading/loading_screen", function (o) {
    envuelveSq(o, "updateProgress", @(f) function (_text) { return f.call(this, ::Rosetta._(_text)); })
})

// El tooltip de la plantilla pinta "<terreno> [color]50.00%[/color]" con los
// nombres en inglés que getRosterDescription (asset_manager.nut) deja en
// TerrainModifiers; se traducen ahí, antes de componerlos.
mod.hook("scripts/states/world/asset_manager", function (q) {
    q.getRosterDescription = @(__original) function () {
        local ret = __original();
        foreach (t in ret.TerrainModifiers) t[0] = ::Rosetta._(t[0]);
        return ret;
    }
})
// Legends sustituye addBrotherEnding, así que la marca del caso 39 no llega y
// el epílogo de jubilación entra entero en buildGameFinishText, sin casar con
// nada. Se marca aquí, con el mismo carácter; sin Legends vale el del base.
local MARCA_FIN = format("%c", 1);
::mods_hookNewObject("states/world/asset_manager", function (o) {
    envuelveSq(o, "addBrotherEnding", @(f) function (_brothers, _excludedBackgrounds, _isPositive) {
        local r = f.call(this, _brothers, _excludedBackgrounds, _isPositive);
        return typeof r == "string" && r != "" ? MARCA_FIN + r + MARCA_FIN : r;
    })
})

// Los consejos del campamento (_legend_tips_encounter): Legends los pega todos
// con "\n- " bajo «Here are some tips for you:», y la suma no casa con ningún
// par. Se rehace el texto con cada consejo traducido, una línea en blanco entre
// ellos, la cabecera en color y los términos de juego y los nombres entre
// comillas resaltados (decisión del propietario, QA del 22/10).
local TERMINOS = ["puntos de acción", "puntos de vida", "zona de control", "ventajas", "ventaja",
    "rasgos", "rasgo", "heridas", "herida", "resolución", "fatiga", "iniciativa", "moral",
    "renombre", "séquito", "ambiciones", "ambición", "contratos", "contrato", "coronas",
    "herramientas", "munición", "provisiones", "experiencia", "campamento", "orígenes", "origen", "sangrado"];
local esLetra = @(_c) (_c >= 'a' && _c <= 'z') || (_c >= 'A' && _c <= 'Z') || _c >= 0x80 || _c < 0;
local esCifra = @(_c) _c >= '0' && _c <= '9';
local CIERRA = "[/color]";
// Fuera de cualquier [color]: tantas aperturas como cierres antes de la posición.
local fueraDeColor = function (_antes) {
    local ab = 0, ce = 0, k = 0;
    while ((k = _antes.find("[color=", k)) != null) { ab++; k++; }
    k = 0;
    while ((k = _antes.find(CIERRA, k)) != null) { ce++; k++; }
    return ab == ce;
}
// Cifras sueltas («15%», «+10%», «30»), en _color y fuera de otro [color].
local resaltaCifras = function (_s, _color) {
    local ret = "", i = 0, n = _s.len();
    while (i < n) {
        local c = _s[i];
        if ((esCifra(c) || (c == '+' && i + 1 < n && esCifra(_s[i + 1])))
                && (i == 0 || !(esLetra(_s[i - 1]) || esCifra(_s[i - 1]) || _s[i - 1] == '=' || _s[i - 1] == '#'))
                && fueraDeColor(_s.slice(0, i))) {
            local f = i + 1;
            while (f < n && (esCifra(_s[f]) || ((_s[f] == '.' || _s[f] == ',') && f + 1 < n && esCifra(_s[f + 1])))) f++;
            if (f < n && _s[f] == '%') f++;
            if (f < n && esLetra(_s[f])) { ret += _s.slice(i, f); i = f; continue; }
            ret += "[color=" + _color + "]" + _s.slice(i, f) + CIERRA;
            i = f;
            continue;
        }
        ret += _s.slice(i, i + 1);
        i++;
    }
    return ret;
}
// Con _primera, cada término solo se colorea la primera vez que aparece.
local resalta = function (_s, _color, _terminos = TERMINOS, _primera = false) {
    local abre = "[color=" + _color + "]";
    // «...» entero; luego cada término suelto, con su mayúscula inicial también.
    local ret = "", i = 0;
    while (true) {
        local a = _s.find("«", i), b = a == null ? null : _s.find("»", a);
        if (b == null) break;
        ret += _s.slice(i, a) + abre + _s.slice(a, b + "»".len()) + CIERRA;
        i = b + "»".len();
    }
    _s = ret + _s.slice(i);
    foreach (t in _terminos) {
        local hecho = false;
        foreach (forma in [t, t.slice(0, 1).toupper() + t.slice(1)]) {
            ret = ""; i = 0;
            while (true) {
                local j = _s.find(forma, i);
                if (j == null) break;
                local fin = j + forma.len();
                local antes = _s.slice(0, j);
                local libre = (antes.len() == 0 || !esLetra(antes[antes.len() - 1]))
                    && (fin >= _s.len() || !esLetra(_s[fin]));
                if (libre && !hecho && fueraDeColor(antes)) {
                    ret += _s.slice(i, j) + abre + forma + CIERRA;
                    hecho = _primera;
                }
                else ret += _s.slice(i, fin);
                i = fin;
            }
            _s = ret + _s.slice(i);
        }
    }
    return _s;
}
local colorResalte = @() "getHighlightLightBackgroundValue" in ::Const.UI.Color
    ? ::Const.UI.Color.getHighlightLightBackgroundValue() : "#1e468f";
// Para fondos oscuros (pantalla de eventos), el resalte oscuro de Legends,
// también ajustable en sus ajustes de MSU.
local colorResalteOscuro = @() "getHighlightDarkBackgroundValue" in ::Const.UI.Color
    ? ::Const.UI.Color.getHighlightDarkBackgroundValue() : "#6f91c9";
// Se engancha buildText de la clase base y no createScreens del encuentro: el
// enganche de createScreens no llegaba a la partida (la prueba del 23/10 seguía
// desbordando la pila con el texto inglés). buildText es lo que pasa el texto
// de la pantalla a Rosetta; para los consejos se devuelve el texto ya montado,
// sin pasar por ella, también en los clics siguientes, en los que la pantalla
// ya guarda el castellano.
local CONSEJOS = "Here are some tips for you:", consejos = null;
mod.hook("scripts/encounters/encounter", function (q) {
    // El título de la pantalla no pasa por buildText ni por Rosetta (getUITitle
    // lo devuelve tal cual: «Walking through the market...»).
    q.getUITitle = @(__original) function () { return ::Rosetta._(__original()); }
    // Las filas de resultado («Barbering unlocked in camp»): Rosetta solo
    // traduce las de event y contract. Se copian porque la lista es la de la
    // pantalla y getUIList se llama más de una vez.
    q.getUIList = @(__original) function () {
        local ret = __original();
        foreach (l in ret) {
            if (typeof l.title == "string" && l.title != "") l.title = ::Rosetta._(l.title);
            l.items = l.items.map(function (r) {
                local c = clone r;
                if ("text" in c && typeof c.text == "string") c.text = ::Rosetta._(c.text);
                return c;
            });
        }
        return ret;
    }
    q.buildText = @(__original) function (_text, _full = true) {
        if (typeof _text != "string" || this.m.Type != "encounter.legend_tips_encounter"
                || !(::std.Str.startswith(_text, CONSEJOS) || _text == consejos))
            return __original(_text, _full);
        if (consejos == null) {
            local color = colorResalteOscuro();  // los consejos salen en la pantalla de eventos
            consejos = "[color=" + color + "]" + ::Rosetta._(CONSEJOS) + "[/color]";
            foreach (tip in ::Const.TipOfTheDay) consejos += "\n\n- " + resalta(::Rosetta._(tip), color);
            ::BattleBrothersEs.Hechos[consejos] <- true;  // por si otra vía lo pasa a translate()
        }
        return consejos;
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

// La descripción de esas piezas suma, tras la suya, la frase de cada capa
// (" " + u.getArmorDescription()), un getter que Rosetta no envuelve.
foreach (clase in ["scripts/items/legend_armor/legend_armor_upgrade", "scripts/items/legend_helmets/legend_helmet_upgrade"])
    mod.hookTree(clase, function (q) {
        q.getArmorDescription = @(__original) function () {
            return ::Rosetta._(__original());
        }
    })

// El tooltip táctico de Jimmy's Tooltips (integrado en Legends,
// mod_Jimmys_Tooltips/config/tooltip_helper.nut) pone sus cabeceras en inglés
// y la lista de ventajas con m.Name, que no pasa por los getters de Rosetta, y
// con la inicial ya coloreada aparte, así que ningún par la casa. Aquí se
// cambian las cabeceras (sin los dos puntos sueltos de dos de ellas) y se
// rehace la lista con cada nombre traducido. actor.nut busca la función en la
// tabla en cada llamada, así que basta con sustituirla.
if ("ModJimmysTooltips" in getroottable() && "modTacticalTooltip" in ::ModJimmysTooltips) {
    local CABECERAS = {
        "Status perks": "Ventajas de estado", "Usable perks": "Ventajas utilizables", "Perks": "Ventajas",
        "Equipped Items:": "Objetos equipados", "Bags": "Bolsas", "Accessory": "Accesorio", "Ammo": "Munición",
        "Item on ground": "Objeto en el suelo", "Items on ground": "Objetos en el suelo",
        "Chance to loot equipment:": "Probabilidad de saquear el equipo"
    };
    local INI = "[color=%negative%]", FIN = "[/color]";
    // La inicial en color, como la pone Legends; si es una vocal con tilde, sus dos bytes.
    local inicial = @(s) (s[0] & 0xFF) >= 0xC0 ? 2 : 1;
    local ventajas = function (_text) {
        local nombres = [];
        foreach (trozo in split(_text, ",")) {
            local n = ::std.Str.replace(::std.Str.replace(strip(trozo), INI, ""), FIN, "");
            n = ::Rosetta._(n);
            if (n.len() > 1) nombres.push(INI + n.slice(0, inicial(n)) + FIN + n.slice(inicial(n)));
        }
        return nombres.len() ? ::std.Str.join(", ", nombres) : _text;
    }
    local original = ::ModJimmysTooltips.modTacticalTooltip;
    ::ModJimmysTooltips.modTacticalTooltip = function (_tooltip, _targetedWithSkill, _entity) {
        local ret = original(_tooltip, _targetedWithSkill, _entity);
        foreach (fila in ret) {
            // Los efectos de cada herida van en children, donde translateTooltip no entra.
            if ("children" in fila && typeof fila.children == "array")
                foreach (h in fila.children)
                    if (typeof h == "table" && "text" in h && typeof h.text == "string") h.text = ::Rosetta._(h.text);
            if (!("text" in fila) || typeof fila.text != "string") continue;
            local t = fila.text;
            if (::std.Str.startswith(t, "[u][size=14]") && ::std.Str.endswith(t, "[/size][/u]")) {
                local titulo = t.slice(12, -11);
                if (titulo in CABECERAS) fila.text = "[u][size=14]" + CABECERAS[titulo] + "[/size][/u]";
            } else if ("icon" in fila && fila.icon == "ui/icons/perks.png" && t.find(INI) == 0) {
                fila.text = ventajas(t);
            } else if (t.find(" Ammo: ") != null || ::std.Str.endswith(t, " Ammo: infinite")) {
                fila.text = ::std.Str.replace(::std.Str.replace(t, " Ammo: infinite", " Munición: infinita"), " Ammo: ", " Munición: ");
            }
        }
        return ret;
    }
}

// Las descripciones de las tiendas del campamento son bloques de texto plano
// (salvo la cocina, que ya trae algo de color). Con el criterio del propietario
// (QA del 23/10: solo color, sin tocar la redacción), se traducen aquí y se les
// resaltan las cifras y los recursos y términos de juego. El texto ya hecho se
// apunta para que el enganche de tooltips de Rosetta no lo vuelva a recorrer.
local TERMINOS_CAMPAMENTO = clone TERMINOS;
TERMINOS_CAMPAMENTO.extend(["medicinas", "medicina", "comida", "vendas", "durabilidad",
    "trasfondos", "trasfondo", "runas", "tiendas mejoradas", "tienda mejorada"]);
mod.hookTree("scripts/entity/world/camp/camp_building", function (q) {
    q.getTooltip = @(__original) function () {
        local ret = __original();
        foreach (fila in ret)
            if (fila.type == "description" && typeof fila.text == "string") {
                local s = ::Rosetta._(fila.text);
                if (s == fila.text) continue;  // sin par: se deja a Rosetta
                s = resaltaCifras(resalta(s, colorResalte(), TERMINOS_CAMPAMENTO, true), ::Const.UI.Color.PositiveValue);
                ::BattleBrothersEs.Hechos[s] <- true;
                fila.text = s;
            }
        return ret;
    }
})

// La contratación del séquito de Legends pide los requisitos a
// getRequirementsForUI (hooks/retinue/follower.nut), no a getRequirements, que
// es el que traduce el caso 10 de los hooks. Los textos con cifras ya llegan
// compuestos (UpdateText en evaluate) y los cubren los pares y patrones del
// corpus; el método devuelve clones, así que se puede escribir en ellos.
::mods_hookBaseClass("retinue/follower", function (o) {
    while (!("ID" in o.m)) o = o[o.SuperName];
    if (!("getRequirementsForUI" in o)) return;
    envuelveSq(o, "getRequirementsForUI", @(getReq) function () {
        local ret = getReq.call(this);
        foreach (r in ret) if ("Text" in r) r.Text = ::Rosetta._(r.Text);
        return ret;
    })
})

// El oponente más poderoso del obituario se guarda con su nombre inglés
// (getKilledName al morir el enemigo); en las partidas guardadas ya está
// escrito, así que se traduce al consultar el tooltip. Legends reescribe
// getRosterTooltip del jugador y del caído con mods_hookExactClass.
foreach (c in ["entity/tactical/player", "entity/tactical/player_corpse_stub"])
    ::mods_hookNewObject(c, function (o) {
        envuelveSq(o, "getRosterTooltip", @(f) function () {
            local s = this.m.LifetimeStats;
            if ("MostPowerfulVanquished" in s && s.MostPowerfulVanquished != "")
                s.MostPowerfulVanquished = ::Rosetta._(s.MostPowerfulVanquished);
            return f.call(this);
        })
    })

// modGetHitFactors (hooks/skills/skill.nut de Legends) reescribe filas de la
// probabilidad de golpe como "<color>N%</color> <descripción>" y usa la
// descripción inglesa de clave: se traduce la descripción después.
::mods_hookBaseClass("skills/skill", function (o) {
    while (!("ID" in o.m)) o = o[o.SuperName];
    if (!("modGetHitFactors" in o)) return;
    envuelveSq(o, "modGetHitFactors", @(f) function (_ret, _targetTile) {
        local ret = f.call(this, _ret, _targetTile);
        foreach (fila in ret) {
            if (typeof fila != "table" || !("text" in fila) || typeof fila.text != "string") continue;
            local s = fila.text, i = s.find("[/color] ");
            fila.text = s.find("[color=") == 0 && i != null ? s.slice(0, i + 9) + ::Rosetta._(s.slice(i + 9)) : ::Rosetta._(s);
        }
        return ret;
    })
})

// Los libros de habilidad se llaman "<libro> <grupo>" («Astrology and Tarot
// Readings: Trained»); la suma no casa con ningún par.
mod.hookTree("scripts/items/misc/legend_skill_book", function (q) {
    q.getName = @(__original) function () {
        local ret = __original(), libro = this.m.BookName, grupo = this.m.PerkGroupSelection;
        if (libro == "" || typeof grupo != "string" || ret != libro + " " + grupo) return ret;
        return ::Rosetta._(libro) + " " + (grupo in GRUPOS ? GRUPOS[grupo] : ::Rosetta._(grupo));
    }
})
