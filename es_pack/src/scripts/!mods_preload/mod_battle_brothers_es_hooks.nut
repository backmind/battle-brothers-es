// Hooks propios del pack castellano: hacen pasar por Rosetta textos que el
// juego compone en Squirrel y que ningún hook del runtime upstream intercepta
// (menú de escenarios, títulos del panel de contrato activo, aviso del menú
// principal, séquito, subtítulo del pueblo, puerto, barra de Moral, el
// diálogo de entrar en combate y, desde el lote 3, la taberna entera, las
// pantallas interiores de los edificios del pueblo, la hora del mapa y el
// mensaje de pausa).
// Las strings sin par registrado se muestran en inglés, igual que el resto
// del pack: estos hooks no se rompen con las actualizaciones del juego.
//
// Con Rosetta 0.5.0 se retiraron las copias que la release ya lleva (la
// política es retirar contra release, nunca contra master):
// eventos y contratos (su wrapper global de ::buildTextFromTemplate traduce
// la misma plantilla cruda que interceptaba nuestro buildText, verificado que
// _text llega intacto en event.nut:383 y contract.nut:603), la pantalla de
// resultado de combate, los tips de carga, los rótulos del mapa, las
// descripciones de facciones (van por el template engine en la generación de
// mundo, o sea por el mismo wrapper) y la plantilla del barco del puerto.
// Mantener una copia junto al wrapper no es redundancia inocua: la segunda
// pasada re-traduce texto ya en castellano y una regla golosa puede
// corromperlo (el modo de fallo "goza de"). Por eso la retirada va acoplada
// al require de 0.5.0 de abajo: con un runtime menor, estas pantallas se
// apagarían.
// Lo que queda del lote 2 está en el plan de Suor (docs/more-hooks-plan.md)
// pero no en release: cada pieza se retirará cuando una release la lleve.
if (!("Rosetta" in getroottable())) return;

// Sonda del caso 3 (títulos de campaña y escenario del menú principal): los
// hooks upstream de starting_scenario y del tooltip existen y se finalizan a
// tiempo, pero en partida sale inglés y sin NOT FOUND en el log. Para sondar:
// poner a true, arrancar el juego, abrir el selector de campaña y pasar el
// ratón por un banner de DLC; después mirar log.html. Apagada por defecto y
// sin efecto ninguno: no traduce ni escribe nada en el log.
local SONDA_CASO3 = false;

local def = {
    ID = "mod_battle_brothers_es_hooks"
    Name = "Battle Brothers en Español (hooks)"
    Version = "5.0.0-beta.1"
}
local mod = ::Hooks.register(def.ID, def.Version, def.Name);
mod.require("mod_rosetta >= 0.5.0");

mod.queue(">mod_rosetta", function () {
    local _ = ::Rosetta._;
    local simpleGetter = @(__original) function () {
        return _(__original());
    }

    // Caso 2: los títulos "Objectives" y "Payment" del panel del contrato
    // ACTIVO, que llama a getUIBulletpoints directamente
    // (world_active_contract_panel_module.nut:54) sin pasar por el getUIList
    // que hookea la 0.5.0. Los textos de los items van por buildText, o sea
    // por el wrapper global del runtime; aquí solo faltan los títulos. En la
    // pantalla de negociación getUIList llama aquí dentro y su listHook
    // re-traduce el título ya en castellano: doble _() esperado, cuesta un
    // NOT FOUND de "Objetivos"/"Pago" en el log y nada más (son pares
    // literales, ninguna regla golosa puede casarlos).
    mod.hook("scripts/contracts/contract", function (q) {
        q.getUIBulletpoints = @(__original) function (_objectives = true, _payment = true) {
            local ret = __original(_objectives, _payment);
            foreach (r in ret)
                if ("title" in r) r.title = _(r.title);
            return ret;
        }
    })

    // Las dos intros de partida (early_access y southern_quickstart) titulan
    // "The " + nombre de la compañía, ya concatenado, así que el par de
    // "The %companyname%" no casa y salía "The Los Focalistas". En
    // castellano el título es el nombre tal cual, sin traducirlo.
    //
    // Lo mismo en la lista de efectos de seis eventos: "X leaves the " o
    // "X joins the " + el nombre (deserción, el bastardo y el asesino, el noble
    // repudiado, el mercenario que se va...). Una regla "<a:str> leaves the
    // <b:str>" se comía cualquier frase con "leaves the"; aquí solo se toca la
    // que acaba exactamente en el nombre de la compañía.
    local VERBOS = [[" leaves the ", " deja a "], [" joins the ", " se une a "]];
    mod.hook("scripts/events/event", function (q) {
        q.getUITitle = @(__original) function () {
            local nombre = ::World.Assets.getName();
            return this.m.Title == "The " + nombre ? nombre : __original();
        }
        q.getUIList = @(__original) function () {
            local ret = __original();
            local nombre = ::World.Assets.getName();
            foreach (list in ret)
                foreach (item in list.items) {
                    if (typeof item.text != "string") continue;
                    foreach (v in VERBOS) {
                        local cola = v[0] + nombre;
                        if (item.text.len() > cola.len() && ::std.Str.endswith(item.text, cola)) {
                            item.text = item.text.slice(0, -cola.len()) + v[1] + nombre;
                            break;
                        }
                    }
                }
            return ret;
        }
    })

    // Caso 6: aviso del menú principal. El literal viene incrustado en
    // main_menu_screen.connect(), así que se deja conectar y se re-empuja el
    // MOTD traducido. Si el juego cambia el literal, el par no casa y no se
    // re-empuja nada: se queda el texto vanilla en inglés.
    mod.hook("scripts/ui/screens/menu/main_menu_screen", function (q) {
        q.connect = @(__original) function () {
            local ret = __original();
            local motd = "Battle Brothers is a challenging game. Losses and comebacks are part of the gameplay.\n\nIt's recommended that you start with 'Beginner' difficulty and the tutorial origin!";
            local es = _(motd);
            if (es != motd && this.m.JSHandle != null)
                this.m.JSHandle.asyncCall("setMOTD", es);
            return ret;
        }
    })

    // Lote 2, escrito el 25/08/2026 con el trazado de la ficha. Todos los
    // pares que consumen estos hooks ya existen en el corpus: aquí solo se
    // abren los conductos.

    // Caso 3b: el menú "Escenarios" del menú principal (demos tácticas). Los
    // nombres y descripciones van incrustados en main_menu_state, no salen de
    // los scenario_*.nut tácticos, y el módulo de UI es un pasarrelé. Sin
    // subclases de main_menu_state: hook y no hookTree.
    mod.hook("scripts/states/main_menu_state", function (q) {
        q.scenario_menu_module_onQueryData = @(__original) function () {
            local ret = __original();
            foreach (r in ret) {
                if ("name" in r) r.name = _(r.name);
                if ("description" in r) r.description = _(r.description);
            }
            return ret;
        }
    })

    // Caso 10: pantalla de séquito. Los getters de follower alimentan la
    // pantalla de contratación (retinue_manager.getFollowersForUI) y el
    // tooltip ya hookeado por upstream; ninguna de las 18 subclases los
    // redefine, así que hook sobre la base. Los wrappers devuelven copias
    // (map crea array nuevo y los Requirements se clonan) para no mutar el
    // estado del follower, que el juego reescribe en cada update.
    mod.hook("scripts/retinue/follower", function (q) {
        q.getName = simpleGetter;
        q.getDescription = simpleGetter;
        q.getEffects = @(__original) function () {
            return __original().map(_);
        }
        q.getRequirements = @(__original) function () {
            return __original().map(function (r) {
                local c = clone r;
                if ("Text" in c) c.Text = _(c.Text);
                return c;
            });
        }
    })
    // El título y el subtítulo del panel principal del séquito van
    // incrustados en el propio módulo de la pantalla.
    mod.hook("scripts/ui/screens/world/modules/world_campfire_screen/campfire_main_dialog_module", function (q) {
        q.queryData = @(__original) function () {
            local ret = __original();
            if (ret != null) {
                if ("Title" in ret) ret.Title = _(ret.Title);
                if ("SubTitle" in ret) ret.SubTitle = _(ret.SubTitle);
            }
            return ret;
        }
    })

    // Caso 11: el subtítulo de la pantalla del pueblo. settlement tiene dos
    // campos casi gemelos: m.Description (largo, con punto) viaja por el
    // tooltip del mapa ya hookeado, y m.UIDescription (corto) solo sale por
    // getUIInformation, que nadie intercepta. El Title es el nombre propio
    // del asentamiento y pasa sin tocar. Sin subclases que redefinan el
    // método: hook.
    mod.hook("scripts/entity/world/settlement", function (q) {
        q.getUIInformation = @(__original) function () {
            local ret = __original();
            if (ret != null && "SubTitle" in ret) ret.SubTitle = _(ret.SubTitle);
            return ret;
        }
        // Lote 3 (caso 21): los rumores locales del asentamiento (m.Rumors
        // apunta a los arrays RumorsXSettlement/RumorsItems* por referencia)
        // se mezclan con los generales en la taberna. Se traducen aquí, con la
        // plantilla cruda (%settlement% intacto) contra su par literal, antes
        // de que la taberna los componga y buildText los instancie.
        q.getRumors = @(__original) function () {
            return __original().map(_);
        }
    })

    // Caso 12: la pantalla del puerto. getUITravelRoster compone título,
    // subtítulo, "Sail to X" (casa con el patrón del corpus) y el texto de
    // fondo de cada destino, y nada de eso pasa por Rosetta. La descripción
    // aleatoria del barco ya no se toca aquí: se compone con
    // buildTextFromTemplate y el wrapper global de la 0.5.0 traduce la
    // plantilla cruda, que es exactamente lo que hacía nuestra copia
    // retirada. port_oriental_building hereda el método sin redefinirlo:
    // hook.
    mod.hook("scripts/entity/world/settlements/buildings/port_building", function (q) {
        q.getUITravelRoster = @(__original) function () {
            local ret = __original();
            if (ret == null) return ret;
            if ("Title" in ret) ret.Title = _(ret.Title);
            if ("SubTitle" in ret) ret.SubTitle = _(ret.SubTitle);
            if ("Roster" in ret) {
                foreach (r in ret.Roster) {
                    if ("ListName" in r) r.ListName = _(r.ListName);
                    // BackgroundText = descripción del destino + "<br><br>" +
                    // la descripción del barco, que ya llega en español por
                    // el wrapper de buildTextFromTemplate del runtime; falta
                    // la primera mitad, que aquí se usa cruda sin pasar por
                    // el tooltip del mapa.
                    if ("BackgroundText" in r) {
                        local sep = r.BackgroundText.find("<br><br>");
                        if (sep != null) {
                            r.BackgroundText = _(r.BackgroundText.slice(0, sep)) + r.BackgroundText.slice(sep);
                        }
                    }
                }
            }
            return ret;
        }
    })

    // Caso 13 (facciones), retirado con la 0.5.0: la fusión de la plantilla
    // con los nombres reales pasa por buildTextFromTemplate, así que el
    // wrapper global del runtime la traduce en la misma ventana que usaba
    // nuestra copia (y con la misma servidumbre: solo partidas nuevas, las
    // guardadas llevan el texto fundido en inglés dentro del save).

    // Caso 14: la etiqueta de la barra de Moral ("Steady"). Sale de
    // Const.MoraleStateName consumida por índice, así que la tabla no se
    // toca (la lección de ArmorStateName): se interceptan los dos
    // consumidores, la pantalla de personaje (data_helper) y la barra de
    // iniciativa del combate táctico. El tooltip del icono de ánimo ya se
    // traduce por el conducto genérico de tooltips.
    mod.hook("scripts/ui/global/data_helper", function (q) {
        q.addStatsToUIData = @(__original) function (_entity, _target) {
            __original(_entity, _target);
            if ("moraleLabel" in _target) _target.moraleLabel = _(_target.moraleLabel);
        }
    })
    mod.hook("scripts/ui/screens/tactical/modules/turn_sequence_bar/turn_sequence_bar", function (q) {
        q.convertEntityToUIData = @(__original) function (_entity, isLastEntity = false) {
            local ret = __original(_entity, isLastEntity);
            if (ret != null && "moraleLabel" in ret) ret.moraleLabel = _(ret.moraleLabel);
            return ret;
        }
    })

    // Caso 15: el diálogo de entrar en combate del mapa (texto central y el
    // botón "Fall back!"/"Flee!"). Todos los llamadores (contratos, eventos,
    // IA de mundo) convergen en world_combat_dialog.show, que es la frontera
    // sq-js real, tabla plana como loading_screen: hook.
    mod.hook("scripts/ui/screens/world/world_combat_dialog", function (q) {
        q.show = @(__original) function (_entities, _allyBanners, _enemyBanners, _allowDisengage, _allowFormationPicking, _text, _image, _disengageText = "Cancel") {
            // Añadido el 29/08: la lista de tropas también. world_state.nut:2351
            // compone cada Name como "A " + EntityName o como cantidad +
            // EntityNamePlural, y esa tabla no la pregunta nadie: en partida
            // salía "A few Brigand Thugs" bajo un texto ya en castellano. Los
            // patrones de cantidad del corpus ("A few <troops:t>") resuelven el
            // nombre por dentro. Se copia la fila para no mutar la del juego.
            if (typeof _entities == "array") {
                local trad = [];
                foreach (e in _entities) {
                    if (typeof e == "table" && "Name" in e) {
                        local c = clone e;
                        c.Name = _(c.Name);
                        trad.push(c);
                    } else trad.push(e);
                }
                _entities = trad;
            }
            return __original(_entities, _allyBanners, _enemyBanners, _allowDisengage, _allowFormationPicking, _(_text), _image, _(_disengageText));
        }
    })

    // Caso 16: el conector de la lista de hermanos ("A, B and C") que compone
    // asset_manager.getAllBrotherNames() en runtime y viaja incrustado dentro
    // de la prosa de eventos. Ninguna regla de datos puede verlo por dentro
    // (la pieza llega ya compuesta con nombres propios), así que se traduce el
    // conector en la propia composición. La coma se queda como está.
    mod.hook("scripts/states/world/asset_manager", function (q) {
        q.getAllBrotherNames = @(__original) function () {
            return ::std.Str.replace(__original(), " and ", " y ");
        }
    })

    // Caso 18: el texto de ambición de la barra superior del mapa.
    // ambition_manager empuja getUIText() a TopbarAmbitionModule.setText
    // (ambition_manager.nut:311,319,507) y de ahí va directo a JS: ni los
    // literales de ambición con par ni sus variantes con progreso "(n/8)"
    // pasaban por Rosetta. Se traduce en la frontera; las variantes con
    // número casan con los patrones del corpus (con :t sobre la pieza, que
    // llega cruda en inglés). Sin subclases: hook.
    mod.hook("scripts/ui/screens/world/modules/topbar/world_screen_topbar_ambition_module", function (q) {
        q.setText = @(__original) function (_text) {
            return __original(_(_text));
        }
    })

    // Caso 17: el escudo famoso de lindwurm. Su createRandomName devuelve
    // solo el prefijo CON UN ESPACIO FINAL (named_lindwurm_shield.nut:43,
    // a diferencia de la base, que concatena prefijo + " " + sustantivo), y
    // la búsqueda de Rosetta es exacta: los seis prefijos ya traducidos del
    // corpus (Piel de dragón, Escama de wyrm...) no casaban por ese espacio.
    // Recortarlo aquí enmienda además el defecto cosmético de vanilla; la
    // traducción la hace el getName de items del runtime, como siempre.
    // Sin subclases: hook. Solo alcanza nombres generados tras instalar el
    // pack; los guardados en el save conservan su espacio y siguen en inglés.
    mod.hook("scripts/items/shields/named/named_lindwurm_shield", function (q) {
        q.createRandomName = @(__original) function () {
            return strip(__original());
        }
    })

    // Lote 3, escrito el 29/08/2026 con lo que dio la sesión de QA del 28/08.
    // Las pantallas interiores de los edificios del pueblo componen su
    // Title/SubTitle (y más) en el queryData de cada módulo de
    // world_town_screen y nada pasa por Rosetta; todos los pares ya existen
    // en el corpus (verificado uno a uno). Estilo del lote 2: traducir en la
    // frontera sq-js, sin tocar tablas consumidas por índice.

    // Caso 19: la taberna. queryData compone título, subtítulo, los textos de
    // pago (patrones con precio) y el rumor; onQueryRumor y onDrink devuelven
    // el rumor pagado y el resultado de la ronda. El rumor llega como sobre
    // "intro\n\n[color]rumor[/color]\n\n" y lo casa el patrón de sobre del
    // corpus (la intro con :t; la pieza del rumor llega YA en castellano por
    // el caso 20 y va cruda). Las líneas de la ronda ("X is now drunk",
    // "X gets eager") casan con sus patrones del corpus; el nombre del
    // hermano llega ya traducido y las reglas lo insertan crudo.
    local trTavern = function (ret) {
        if (ret == null) return ret;
        foreach (k in ["Title", "SubTitle", "Rumor", "LeftInfo", "RightInfo"])
            if (k in ret && ret[k] != null) ret[k] = _(ret[k]);
        if ("Drink" in ret && ret.Drink != null) {
            if ("Intro" in ret.Drink) ret.Drink.Intro = _(ret.Drink.Intro);
            if ("Result" in ret.Drink)
                foreach (r in ret.Drink.Result)
                    if ("Text" in r) r.Text = _(r.Text);
        }
        return ret;
    };
    mod.hook("scripts/ui/screens/world/modules/world_town_screen/town_tavern_dialog_module", function (q) {
        q.queryData = @(__original) function () { return trTavern(__original()); }
        q.onQueryRumor = @(__original) function () { return trTavern(__original()); }
        q.onDrink = @(__original) function () { return trTavern(__original()); }
    })

    // Caso 20: los arrays de rumores de taberna. El juego elige el rumor de
    // Const.Strings.Rumors* y lo pasa por buildText ANTES de devolverlo, así
    // que al sobre le llega instanciado (%randomfemalename% ya sustituido) y
    // ningún par literal puede casarlo. Se traducen los arrays una sola vez,
    // en el primer uso (con Rosetta ya activa), plantilla cruda contra par
    // literal, que es el mismo diseño que usan eventos y contratos con el
    // wrapper del runtime. Se consumen por valor (extend y pick aleatorio),
    // nunca por índice, así que mutarlos no rompe nada. PayTavernRumorsIntro
    // se queda EN INGLÉS a propósito: la resuelve el :t del patrón de sobre,
    // y pretraducirla mataría ese :t (la lección del guardián).
    // Actualización del 29/08: la lista fija de cinco tablas se quedaba corta.
    // La taberna mezcla además RumorsItemsOrcs/Goblins/Bandits/Undead/
    // Barbarians/Nomads (arrays de arrays, indexados por categoría) y las
    // Rumors*Settlement de cada terreno. En partida salieron en inglés dos
    // rumores de RumorsItemsBandits (QA 29/08). Ahora se recorre Const.Strings
    // y se traduce TODO lo que empiece por "Rumors", con un nivel de
    // anidamiento.
    //
    // Corrección del 30/08: lo de dejar PayTavernRumorsIntro en inglés para
    // que la resolviera el :t del patrón de sobre era falso. Ese patrón,
    // "<intro:str>\n\n[color=#bcad8c]\x22<rumor:str>\x22[/color]\n\n", NO
    // puede casar nunca, y no por el guardián: por el índice. El runtime
    // archiva cada regla bajo la primera palabra de su patrón (_ruleKey), y
    // este no tiene ninguna palabra literal, solo puntuación, así que la
    // clave que le sale es "[color=#" y ninguna cadena real la genera (a la
    // cadena sí le quitan las etiquetas antes de sacar sus claves). La regla
    // queda archivada en un cajón que nadie abre. En partida la intro salía
    // siempre en inglés ("The innkeeper rings a bell...", QA 30/08) con el
    // rumor ya en castellano al lado.
    //
    // Así que la intro se traduce como todo lo demás, y el sobre se parte a
    // mano al volver de getRumor, que es determinista y no depende del índice
    // de reglas. Dos de las intros no están en ninguna tabla: van a pelo en
    // tavern_building (el rumor gratis y el "ya no hay más que contar").
    //
    // Los rumores de situación son el otro hueco: la taberna mezcla los
    // Const.Strings.Rumors* con settlement.getRumors() y situation.getRumors(),
    // que salen de cada situación viva del mundo y no están en Const. De ahí
    // salía en inglés el de rutas asaltadas ("The guardsmen are doing what
    // they can...").
    local SEPARADOR = "\n\n[color=#bcad8c]\"";
    local rumorArraysDone = false;
    local function traducirArray(_a) {
        foreach (i, s in _a) {
            if (typeof s == "string") _a[i] = _(s);
            else if (typeof s == "array")
                foreach (j, t in s) if (typeof t == "string") s[j] = _(t);
        }
    }
    local function traducirRumores() {
        if (rumorArraysDone) return;
        rumorArraysDone = true;
        // Las dos intros van aparte: no empiezan por "Rumors". La de la ronda
        // de bebida es un texto suelto; la del rumor de pago es el sobre.
        traducirArray(::Const.Strings.PayTavernRoundIntro);
        traducirArray(::Const.Strings.PayTavernRumorsIntro);
        foreach (key, val in ::Const.Strings) {
            if (typeof key != "string" || key.len() < 6 || key.slice(0, 6) != "Rumors") continue;
            if (typeof val == "array") traducirArray(val);
        }
    }
    // El sobre partido: intro + separador + rumor + cierre. El rumor ya viene
    // traducido de la tabla y con sus %vars% sustituidas, así que solo se
    // toca la intro, que es literal y tiene par.
    local function traducirIntro(_t) {
        if (typeof _t != "string") return _t;
        local i = _t.find(SEPARADOR);
        if (i == null) return _(_t);          // "The patrons talk about this and that." a secas
        local intro = _t.slice(0, i);
        local tr = _(intro);
        return tr == intro ? _t : tr + _t.slice(i);
    }
    mod.hook("scripts/entity/world/settlements/buildings/tavern_building", function (q) {
        q.getRumor = @(__original) function (_isPaidFor = false) {
            traducirRumores();
            local ret = __original(_isPaidFor);
            return traducirIntro(ret);
        }
    })
    // Los rumores que aporta cada situación y cada asentamiento. Se traducen
    // en el getter, sobre una copia, porque el array vive en la situación y
    // no queremos guardarlo traducido en la partida.
    local trRumores = @(__original) function () {
        local ret = __original();
        if (typeof ret != "array") return ret;
        local out = [];
        foreach (r in ret) out.push(typeof r == "string" ? _(r) : r);
        return out;
    };
    mod.hookTree("scripts/entity/world/settlements/situations/situation", function (q) {
        q.getRumors = trRumores;
    })
    mod.hookTree("scripts/entity/world/settlement", function (q) {
        q.getRumors = trRumores;
    })

    // Caso 22: el resto de pantallas interiores del pueblo. Cada módulo
    // compone Title/SubTitle en su query correspondiente (nombres distintos
    // por módulo, verificados en vanilla): taxidermista en queryBlueprints
    // (onCraft reusa ese método, así que queda cubierto), templo, sala de
    // entrenamiento y barbero en queryRosterInformation, y el mercado en
    // queryShopInformation (ahí Title/SubTitle salen del getName y
    // getDescription de la tienda). El puerto ya lo cubre el caso 12.
    local trTitles = function (ret) {
        if (ret != null) {
            if ("Title" in ret) ret.Title = _(ret.Title);
            if ("SubTitle" in ret) ret.SubTitle = _(ret.SubTitle);
        }
        return ret;
    };
    mod.hook("scripts/ui/screens/world/modules/world_town_screen/town_taxidermist_dialog_module", function (q) {
        q.queryBlueprints = @(__original) function () { return trTitles(__original()); }
    })
    // El templo se hookea entero en el caso 36, más abajo: además del título
    // lleva la lista de lesiones, y así el método queda envuelto una sola vez.
    // La sala de entrenamiento lleva además los tres ejercicios, que el módulo
    // mete en Roster[i].Training con su nombre a pelo: en partida la lista
    // salía en inglés ("Sparring Fight", "Veteran's Lessons", "Rigorous
    // Schooling") con los tooltips en castellano al lado, que van por id
    // (QA 30/08).
    mod.hook("scripts/ui/screens/world/modules/world_town_screen/town_training_dialog_module", function (q) {
        q.queryRosterInformation = @(__original) function () {
            local ret = trTitles(__original());
            if (ret != null && "Roster" in ret && typeof ret.Roster == "array") {
                foreach (e in ret.Roster) {
                    if (typeof e != "table" || !("Training" in e)) continue;
                    foreach (t in e.Training)
                        if (typeof t == "table" && "name" in t) t.name = _(t.name);
                }
            }
            return ret;
        }
    })
    mod.hook("scripts/ui/screens/world/modules/world_town_screen/town_barber_dialog_module", function (q) {
        q.queryRosterInformation = @(__original) function () { return trTitles(__original()); }
    })
    mod.hook("scripts/ui/screens/world/modules/world_town_screen/town_shop_dialog_module", function (q) {
        q.queryShopInformation = @(__original) function () { return trTitles(__original()); }
    })

    // Caso 23: la hora del rótulo del mapa ("Dawn", "Midday"...). El módulo
    // datasource del topbar la saca de Const.Strings.World.TimeOfDay por
    // índice y la empuja a JS; la tabla no se toca en persistente (lección de
    // ArmorStateName): se cambia solo durante la llamada, así el wrapper no
    // duplica la lógica de vanilla y sobrevive a sus cambios. Los ocho
    // valores tienen par. La palabra "Day" del mismo rótulo se compone en la
    // capa JS y va aparte (ficha, capa ui).
    mod.hook("scripts/ui/screens/world/modules/topbar/world_screen_topbar_datasource_module", function (q) {
        q.updateTimeInformation = @(__original) function () {
            local orig = ::Const.Strings.World.TimeOfDay;
            ::Const.Strings.World.TimeOfDay = orig.map(_);
            __original();
            ::Const.Strings.World.TimeOfDay = orig;
        }
    })

    // Caso 24: el mensaje central de pausa del mapa ("PAUSED" y
    // "(Press Spacebar)"), que world_state empuja por showMessage directo a
    // JS. Los dos pares existen. Legends envuelve este hook desde fuera y
    // llega aquí con _secondary hecho lista (el aviso y el parte del
    // campamento), así que se traduce cada renglón.
    mod.hook("scripts/ui/screens/world/modules/topbar/world_screen_topbar_daytime_module", function (q) {
        q.showMessage = @(__original) function (_primary, _secondary) {
            local sec = typeof _secondary == "array" ? _secondary.map(@(s) _(s)) : _(_secondary);
            return __original(_(_primary), sec);
        }
    })

    // Caso 25: la pantalla de Facciones y relaciones (QA 28/08, punto 5).
    // convertFactionsToUIData compone el renombre del laurel y la reputación
    // de la balanza (BusinessReputation/MoralReputation, con par), y por cada
    // facción el nombre ("House X" casa con el patrón del corpus, "Free City
    // of X" con el suyo), el lema (la lista de strings.nut está entera en el
    // corpus) y la relación ("Neutral", "Friendly"..., con par). La
    // descripción NO se toca a propósito: llega ya en castellano por el
    // wrapper de generación de mundo (o fundida en inglés dentro del save) y
    // re-pasarla por las reglas es el modo de fallo del re-render.
    mod.hook("scripts/ui/screens/world/world_relations_screen", function (q) {
        q.convertFactionsToUIData = @(__original) function () {
            local ret = __original();
            if (ret == null) return ret;
            if ("BusinessReputation" in ret) ret.BusinessReputation = _(ret.BusinessReputation);
            // "Cruel" comparte par con el prefijo de arma legendaria, que va en
            // minúscula ("Hacha cruel"); la reputación es rótulo y empieza en mayúscula.
            if ("MoralReputation" in ret) {
                local t = _(ret.MoralReputation);
                ret.MoralReputation = t.len() > 0 ? t.slice(0, 1).toupper() + t.slice(1) : t;
            }
            if ("Factions" in ret) {
                foreach (f in ret.Factions) {
                    if ("Name" in f) f.Name = _(f.Name);
                    if ("Motto" in f) f.Motto = _(f.Motto);
                    if ("Relation" in f) f.Relation = _(f.Relation);
                    // La descripción SÍ se toca desde el 29/08. La reserva de
                    // antes era por miedo al re-render de una regla golosa
                    // sobre texto ya traducido, pero en partida se vio que
                    // cada aldea es una facción y su descripción ("A village
                    // living off of lumber...") salía en inglés con el par
                    // relleno. La regla golosa que motivaba aquel miedo (la
                    // del " by " del obituario) ya no existe.
                    if ("Description" in f) f.Description = _(f.Description);
                }
            }
            return ret;
        }
    })

    // Caso 26: el renombre "Unknown" bajo el laurel del séquito (QA 28/08,
    // punto 14) y de cualquier otra pantalla que muestre los Assets: viaja en
    // convertAssetsInformationToUIData de data_helper. Mismo fichero que el
    // caso 14; se añade al hook en registro aparte para no mezclar métodos.
    mod.hook("scripts/ui/global/data_helper", function (q) {
        q.convertAssetsInformationToUIData = @(__original) function () {
            local ret = __original();
            if (ret != null && "BusinessReputation" in ret) ret.BusinessReputation = _(ret.BusinessReputation);
            return ret;
        }
    })

    // Caso 27: los datos del árbol de perks que se empujan a JS. El diálogo
    // de desbloquear perk (capa ui) muestra _perk.Name y _perk.Tooltip tal
    // cual llegan de convertPerksToUIData, que devuelve Const.Perks.Perks
    // crudo; el tooltip al pasar el ratón va por otro canal (ya hookeado por
    // upstream) y por eso se veía en castellano mientras el diálogo salía en
    // inglés. Se devuelve una COPIA traducida (filas y perks clonados) para
    // no mutar la tabla, que consumen otros por índice y por ID.
    mod.hook("scripts/ui/global/data_helper", function (q) {
        local trPerk = function (p) {
            local c = clone p;
            if ("Name" in c) c.Name = _(c.Name);
            if ("Tooltip" in c) c.Tooltip = _(c.Tooltip);
            return c;
        };
        q.convertPerksToUIData = @(__original) function () {
            local ret = __original();
            if (typeof ret != "array") return ret;
            return ret.map(@(row) typeof row == "array" ? row.map(trPerk) : row);
        }
        q.convertPerkToUIData = @(__original) function (_perkId) {
            local ret = __original(_perkId);
            if (ret != null) {
                if ("name" in ret) ret.name = _(ret.name);
                if ("description" in ret) ret.description = _(ret.description);
            }
            return ret;
        }
    })

    // Caso 28: los VALORES con que se rellenan los %placeholders% de eventos,
    // contratos, ambiciones y rumores. El wrapper global de
    // ::buildTextFromTemplate del runtime traduce la PLANTILLA, pero los
    // valores viajan aparte y llegan crudos: el tutorial encarga cazar a
    // "%boss%" y ahí el juego mete Flags.get("BossName"), o sea "Hoggart the
    // Weasel" en mitad de la prosa castellana, con el par "Hoggart la
    // Comadreja" relleno y sin usar (QA 29/08, primera ventana de "La última
    // batalla"). La misma vía sirve a los nombres de los jefes de bandidos,
    // los títulos de campeón, las casas nobles, el terreno y las direcciones.
    // Se envuelve el global otra vez, encadenado: cada envoltorio captura el
    // valor vigente y llama al anterior, así que el orden con el runtime da
    // igual (traduzca antes la plantilla o antes los valores, sale lo mismo).
    // Se construye una lista NUEVA y no se muta la del llamante, que en
    // generateName es la misma en cada tirada.
    // El riesgo de traducir a ciegas está medido: los 966 literales de las
    // tablas de nombres del juego (character_names.nut y
    // world_location_names.nut) están todos en el corpus, 551 como par
    // identidad (los nombres de pila, que quedan intactos) y 407 con el
    // apodo traducido a propósito. Quedan fuera por clave las que no son
    // prosa: el nombre de la compañía lo escribe el jugador, y SPEECH_ON,
    // OOC y las imágenes son marcado.
    local crudas = {
        companyname = true, SPEECH_ON = true, SPEECH_OFF = true,
        OOC = true, OOC_OFF = true, terrainImage = true, townImage = true
    };
    // Y la otra mitad del mismo problema: las pantallas que el juego COMPONE
    // por concatenación. En la negociación del pago, negotiation_templates.nut
    // asigna el bloque de entrada (que acaba en "}") y luego CONCATENA el
    // bloque del pago (que empieza en "{"); el corpus tiene las dos mitades
    // como pares separados, porque así las vio el extractor, pero el runtime
    // recibe la suma y no casa ninguna. Por eso la ventana de "¿De cuánto
    // dinero estamos hablando?" salía entera en inglés (QA 29/08) mientras el
    // resto del contrato iba en castellano. Se corta por la frontera "}{" o
    // "} {" y solo se acepta el corte si AMBAS mitades traducen: si una no
    // tiene par, se deja el texto tal cual y no se cose media frase.
    local function partirYTraducir(_t) {
        local a = _t.find("} {"), b = _t.find("}{");
        local corte = null;
        if (a != null) corte = a + 2;
        if (b != null && (corte == null || b + 1 < corte)) corte = b + 1;
        if (corte == null) return _t;
        local uno = _t.slice(0, corte), dos = _t.slice(corte);
        local t1 = _(uno), t2 = _(dos);
        if (t1 != uno && t2 != dos) return t1 + t2;
        return _t;
    }

    // Hay valores que llegan coloreados enteros ("[color=#6f91c9]Direwolves[/color]",
    // con Const.UI.getColorized en los contratos de Legends) y así no casan con
    // el par del nombre: si el valor entero no traduce, se traduce lo de dentro.
    local function traduceValor(_v) {
        local t = _(_v);
        if (t != _v || _v.find("[color=") != 0 || _v.len() < 16 || _v.slice(-8) != "[/color]") return t;
        local i = _v.find("]"), dentro = _v.slice(i + 1, -8);
        local td = _(dentro);
        return td != dentro ? _v.slice(0, i + 1) + td + "[/color]" : _v;
    }

    local buildTextFromTemplate = ::buildTextFromTemplate;
    ::buildTextFromTemplate = function (_text, _vars) {
        local vars = [];
        foreach (v in _vars) {
            if (typeof v == "array" && v.len() == 2 && typeof v[1] == "string"
                    && v[1] != "" && !(v[0] in crudas))
                vars.push([v[0], traduceValor(v[1])]);
            else
                vars.push(v);
        }
        local texto = typeof _text == "string" ? partirYTraducir(_text) : _text;
        return buildTextFromTemplate(texto, vars);
    }

    // Caso 29: los dos diálogos a pantalla completa del combate táctico. Los
    // sirve tactical_dialog_screen.show con cinco cadenas sueltas (título,
    // subtítulo, cuerpo y los dos botones) y ninguna pasa por Rosetta: en
    // partida salía entero en inglés el de "The Enemy Retreats" con su "It's
    // over" y su "Run them down!" (QA 29/08). El mismo hook cubre el de
    // retirarse uno mismo ("Retreat From Combat"), que aún no se ha visto.
    // Los cinco pares existen ya en el corpus, incluidos los dos cuerpos
    // largos de Const.Strings.UI.
    mod.hook("scripts/ui/screens/tactical/tactical_dialog_screen", function (q) {
        q.show = @(__original) function (_title, _subTitle, _text, _yesButton, _noButton, _yesCallback, _noCallback = null) {
            return __original(_(_title), _(_subTitle), _(_text), _(_yesButton), _(_noButton), _yesCallback, _noCallback);
        }
    })

    // Caso 30: el tooltip del botón de ambición. ambition.getButtonTooltip
    // devuelve las filas ya compuestas y nadie las pregunta: en partida los
    // rótulos "Your Task" y "Your Reward" y los dos cuerpos salían en inglés,
    // incluso con la ambición ya aceptada y su línea en castellano (QA 29/08).
    // El cuerpo de la tarea llega con "\n\n" pegado detrás (ambition.nut:115),
    // así que si el par no casa se reintenta sin esa cola y se le devuelve.
    // hookTree y no hook: getButtonTooltip lo redefinen tres clases (la base,
    // no_ambition y oath_ambition), así que un hook sobre la base dejaba los
    // juramentos del origen Juramentados en inglés. Cada clase construye su
    // tabla desde cero y no llama a la de arriba, así que no hay doble pasada.
    mod.hookTree("scripts/ambitions/ambition", function (q) {
        local trCola = function (s) {
            local t = _(s);
            if (t != s) return t;
            if (s.len() > 2 && s.slice(s.len() - 2) == "\n\n") {
                local nucleo = s.slice(0, s.len() - 2);
                local tn = _(nucleo);
                if (tn != nucleo) return tn + "\n\n";
            }
            return s;
        };
        q.getButtonTooltip = @(__original) function () {
            local ret = __original();
            if (typeof ret != "array") return ret;
            foreach (fila in ret)
                if (typeof fila == "table" && "text" in fila) fila.text = trCola(fila.text);
            return ret;
        }
    })

    // Caso 31: los avisos de la pantalla de personaje. Son veintitrés cadenas
    // ("Sin puntos de acción suficientes", "No hay espacio en la bolsa"...)
    // que helper_convertErrorToUIData devuelve en una tabla, sin pasar por
    // Rosetta. Todas tienen par desde siempre; solo faltaba el conducto. Del
    // barrido de ventanas del 29/08, que inventarió los 134 puntos por los
    // que el juego empuja texto a la interfaz y dejó este como el de más
    // cadenas sin hookear.
    mod.hook("scripts/ui/screens/character/character_screen", function (q) {
        q.helper_convertErrorToUIData = @(__original) function (_errorCode) {
            local ret = __original(_errorCode);
            if (ret != null && "error" in ret) ret.error = _(ret.error);
            return ret;
        }
    })

    // Caso 32: los factores de acierto del tooltip de ataque. Al pasar el
    // ratón sobre un enemigo con un arma equipada, el juego lista por qué
    // aciertas más o menos: "Rodeado", "Armado con escudo", "Distancia de 2".
    // Sale de skill.getHitFactors(_targetTile), que devuelve filas con icono y
    // texto y no pasa por ningún getter traducido. Los treinta y pico pares
    // existen en el corpus desde siempre, incluido el patrón de la distancia;
    // faltaba solo el conducto (QA 30/08).
    // hookTree y no hook: las subclases de skill redefinen getHitFactors para
    // añadir sus propios factores (las de arma a distancia, sobre todo).
    mod.hookTree("scripts/skills/skill", function (q) {
        q.getHitFactors = @(__original) function (_targetTile) {
            local ret = __original(_targetTile);
            if (typeof ret != "array") return ret;
            foreach (fila in ret)
                if (typeof fila == "table" && "text" in fila) fila.text = _(fila.text);
            return ret;
        }
    })

    // Caso 33: el origen en el tooltip de una partida del mapa. party.getTooltip
    // compone "From " + faction.getName(), y el patrón del corpus traduce el
    // "From" pero deja el nombre crudo, porque un :t ahí mataría la regla en
    // cuanto la facción fuera una aldea sin par (el guardián de identidad).
    // Así que el nombre se traduce aquí, antes de que la fila llegue al
    // conducto genérico de tooltips, y el patrón se encuentra el trabajo
    // hecho: "Desde Ciudad estado de Al-Anwar" en vez de "Desde City State of
    // Al-Anwar" (QA 30/08). Vale igual para "Hired by X" de los mercenarios.
    local PREFIJOS = ["From ", "Hired by "];
    mod.hookTree("scripts/entity/world/party", function (q) {
        q.getTooltip = @(__original) function () {
            local ret = __original();
            if (typeof ret != "array") return ret;
            foreach (fila in ret) {
                if (typeof fila != "table" || !("text" in fila)) continue;
                local t = fila.text;
                if (typeof t != "string") continue;
                foreach (p in PREFIJOS) {
                    if (t.len() <= p.len() || t.slice(0, p.len()) != p) continue;
                    fila.text = p + _(t.slice(p.len()));
                    break;
                }
            }
            return ret;
        }
    })

    // Caso 35: el tooltip de los efectos de casilla del combate (fuego, miasma
    // y humo). Salido del barrido de cobertura_datos.py, no de la partida.
    // tactical_state arma la tabla del efecto con su Tooltip dentro y se la
    // pasa a spawnEffectOnTile, que acaba en Tactical.Entities.addTileEffect,
    // que es nativo: el texto se va al motor sin pasar por ninguna consulta de
    // tooltip, así que ningún hook del runtime lo ve. Se traduce en el único
    // punto donde la tabla está en Squirrel y ya completa. Un solo hook cubre
    // los tres efectos y los que añada cualquier mod, porque todos entran por
    // aquí. Los tres pares llevaban en el corpus desde el principio.
    mod.hook("scripts/states/tactical_state", function (q) {
        q.spawnEffectOnTile = @(__original) function (_tile, _effectType, _effect, _particles) {
            if (typeof _effect == "table" && "Tooltip" in _effect
                    && typeof _effect.Tooltip == "string")
                _effect.Tooltip = _(_effect.Tooltip);
            return __original(_tile, _effectType, _effect, _particles);
        }
    })

    // Caso 34: el rótulo que el motor dibuja sobre el mapa. Es el único sitio
    // del juego donde el castellano sale como mojibake: "CompaÃ±Ã­a Azote de
    // Orcos". El mismo nombre, en el tooltip, sale bien (verificado en la QA
    // del 30/08 mirando los dos a la vez), así que no es el corpus ni el
    // conducto: es el renderizador.
    //
    // El rótulo no es interfaz HTML. Sale de addLabel("name"), que es un
    // objeto de texto del motor, y el motor lee la cadena byte a byte como
    // cp1252: cada byte del UTF-8 le sale un glifo, y por eso la eñe (C3 B1)
    // se ve como "Ã±". La conjetura, entonces, es que si se le da la cadena YA
    // en cp1252 la dibuja bien. Se le da solo al rótulo; getName() sigue
    // devolviendo UTF-8 y el tooltip no se entera.
    //
    // Corrección del 31/08: la primera versión enganchaba solo el onInit de
    // party y location, y en partida el mojibake seguía igual. El rótulo no se
    // escribe una vez: world_entity.updateStrength lo REESCRIBE desde getName()
    // cada vez que cambia la tropa de la partida (world_entity.nut:427 y :431),
    // y onDeserialize lo vuelve a poner al cargar (:765). O sea que la
    // conversión del onInit la pisaban a los pocos segundos. Ahora se engancha
    // en los tres sitios donde el juego escribe label.Text, que es donde toca.
    //
    // La fuente del mapa tiene los glifos: se comprobó abriendo el atlas. Si
    // aun así salieran huecos, la salida sería plegar los acentos (Compania).
    local function aLatin1(_s) {
        if (typeof _s != "string") return _s;
        local n = _s.len(), i = 0, hay = false;
        // updateStrength se llama constantemente y para todas las partidas del
        // mapa, así que primero un barrido barato: si no hay cabecera UTF-8 no
        // se construye cadena nueva. Los nombres sin tilde salen por aquí.
        while (i < n) {
            local c = _s[i];
            if (c < 0) c += 256;
            if (c == 0xC2 || c == 0xC3) { hay = true; break; }
            i++;
        }
        if (!hay) return _s;
        local out = "";
        i = 0;
        while (i < n) {
            local c = _s[i];
            if (c < 0) c += 256;
            if ((c == 0xC2 || c == 0xC3) && i + 1 < n) {
                local d = _s[i + 1];
                if (d < 0) d += 256;
                out += format("%c", c == 0xC2 ? d : d + 0x40);
                i += 2;
            } else {
                out += format("%c", c);
                i++;
            }
        }
        return out;
    }
    // Idempotente a efectos prácticos: tras convertir, la eñe es un solo byte
    // 0xF1 y ya no dispara el barrido, así que pasar dos veces no rompe nada.
    // getLabel es nativo del motor y no está documentado qué hace si el rótulo
    // no existe, así que va con red: si algo falla, el nombre se queda como
    // estaba y no se lleva por delante el onInit de la entidad.
    local function arreglaRotulo(_e) {
        try {
            if (!_e.hasLabel("name")) return;
            local l = _e.getLabel("name");
            if (l != null) l.Text = aLatin1(l.Text);
        } catch (e) {}
    }
    local ponerRotulo = @(__original) function () {
        __original();
        arreglaRotulo(this);
    };
    mod.hookTree("scripts/entity/world/party", function (q) {
        q.onInit = ponerRotulo;
    })
    mod.hookTree("scripts/entity/world/location", function (q) {
        q.onInit = ponerRotulo;
    })
    // Los dos que faltaban. Se enganchan sobre world_entity, que es donde están
    // definidos: party y location los heredan, y las subclases que redefinen
    // onDeserialize (party, location, settlement) encadenan con la base, así
    // que la conversión entra igual. player_party redefine updateStrength y no
    // toca el rótulo, de modo que la compañía del jugador va por onInit y por
    // onDeserialize, que es como el juego se la escribe.
    mod.hook("scripts/entity/world/world_entity", function (q) {
        q.updateStrength = @(__original) function () {
            __original();
            arreglaRotulo(this);
        }
        q.onDeserialize = @(__original) function (_in) {
            __original(_in);
            arreglaRotulo(this);
        }
    })

    // Lote 4, escrito el 31/08/2026 con lo que dio la cuarta pasada de QA.

    // Caso 36: los nombres de lesión de la pantalla del templo, que salían en
    // inglés ("Pierced Hand", "Injured Shoulder") mientras el mismo nombre, en
    // el tooltip del personaje, salía en castellano (QA 31/08). Los pares
    // estaban todos.
    //
    // El módulo pide inj.getNameOnly(), que devuelve m.Name a pelo; el getName
    // de skill, que es el que hookea upstream, no pasa por ahí. Es el mismo
    // agujero que ya está en la cesta de upstream como issue de getNameOnly.
    //
    // Se tapa AQUÍ y no en getNameOnly a propósito. Traducir el getter partiría
    // el registro de combate: actor.nut compone "... y sufre " + getNameOnly()
    // y el patrón del corpus resuelve esa pieza con :t, que solo sabe traducir
    // inglés; si le llega ya en castellano, el guardián tumba la regla entera y
    // la línea sale en inglés. Lo mismo con los dos contratos que escriben
    // "X suffers Y". El conducto estrecho no toca nada de eso.
    local trLesiones = function (_e) {
        if (typeof _e != "table" || !("Injuries" in _e)) return;
        if (typeof _e.Injuries != "array") return;
        foreach (inj in _e.Injuries)
            if (typeof inj == "table" && "name" in inj) inj.name = _(inj.name);
    };
    mod.hook("scripts/ui/screens/world/modules/world_town_screen/town_temple_dialog_module", function (q) {
        // El título y el subtítulo venían del caso 22; se envuelven aquí para
        // no encadenar dos hooks sobre el mismo método.
        q.queryRosterInformation = @(__original) function () {
            local ret = trTitles(__original());
            if (ret != null && "Roster" in ret && typeof ret.Roster == "array")
                foreach (e in ret.Roster) trLesiones(e);
            return ret;
        }
        // Tras pagar la cura, el módulo devuelve la ficha del hermano con la
        // lista de lesiones que le quedan, por el mismo camino sin traducir.
        q.onTreatInjury = @(__original) function (_data) {
            local ret = __original(_data);
            if (ret != null && "Entity" in ret) trLesiones(ret.Entity);
            return ret;
        }
    })

    // Caso 37: el ordinal repetido de las partidas nobles. No es un fallo de
    // traducción sino un DAÑO que la traducción le hace al juego, y lo vio la
    // QA del 31/08: dos partidas llamadas "Primer Regimiento de Tarwa" a la vez.
    //
    // faction.getUniqueName construye "1st X", "2nd X"... y para saber cuál
    // queda libre compara u.getName() con el candidato EN INGLÉS
    // (faction.nut:512). Con el pack puesto, getName() devuelve el nombre ya
    // traducido, así que la comparación no casa nunca, el contador se queda en
    // cero y todas las partidas nacen "1st". Le pasa a cualquier idioma de
    // Rosetta, no solo al nuestro.
    //
    // Se apaga la traducción durante esa llamada en vez de reescribir el bucle:
    // así la comparación vuelve a ser inglés contra inglés y el día que el
    // juego cambie el algoritmo seguimos heredándolo. La ventana es un bucle
    // cerrado que solo llama a getName, y se restaura también si algo lanza.
    mod.hook("scripts/factions/faction", function (q) {
        q.getUniqueName = @(__original) function (_name) {
            local activa = ::Rosetta.active;
            ::Rosetta.active = null;
            local ret;
            try {
                ret = __original(_name);
            } catch (e) {
                ::Rosetta.active = activa;
                throw e;
            }
            ::Rosetta.active = activa;
            return ret;
        }
    })

    // Caso 38: la columna "Causa" del obituario. player.getObituaryInfo compone
    // la causa como verbo + " by " + nombre del matador (player.nut:1146) y la
    // guarda en la partida; el nombre llega traducido porque sale de
    // getKilledName, pero el verbo y el conector " by " no pasan por Rosetta y
    // nadie los mira después. En partida: "Impaled by un auxiliar antiguo",
    // "Bled to death", "Left to die" (QA 31/08).
    //
    // Se traduce en la pantalla y no en el momento de la muerte, por dos
    // razones: alcanza también a los caídos que ya están guardados en la
    // partida, y cubre las causas que no salen de player.nut (tactical_state
    // pone "Left to die" y varios eventos ponen la suya). Los 39 verbos de
    // KilledString y las 12 causas completas tienen par; solo faltaba
    // "Killed in a duel", que se añadió al corpus con este lote.
    //
    // Primero se prueba la cadena entera, que resuelve las que no llevan
    // matador ("Devoured by a Nachzehrer" tiene su propio par). Si no, se parte
    // por el ÚLTIMO " by " y se traduce la cabeza; si la cabeza no tiene par no
    // se toca nada, que es mejor que coser media frase.
    mod.hook("scripts/ui/screens/world/world_obituary_screen", function (q) {
        local POR = " by ";
        local trCausa = function (_s) {
            if (typeof _s != "string" || _s == "") return _s;
            local t = _(_s);
            if (t != _s) return t;
            local corte = null, i = 0;
            while (true) {
                local j = _s.find(POR, i);
                if (j == null) break;
                corte = j;
                i = j + 1;
            }
            if (corte == null) return _s;
            local verbo = _s.slice(0, corte), matador = _s.slice(corte + POR.len());
            local tv = _(verbo);
            if (tv == verbo) return _s;
            // El matador ya viene en castellano en las partidas jugadas con el
            // pack; se pasa igualmente por si el caído es de antes de ponerlo.
            return tv + " por " + _(matador);
        };
        q.convertFallenToUIData = @(__original) function () {
            local ret = __original();
            if (ret == null || !("Fallen" in ret) || typeof ret.Fallen != "array")
                return ret;
            local caidos = [];
            foreach (f in ret.Fallen) {
                if (typeof f != "table" || !("KilledBy" in f)) {
                    caidos.push(f);
                    continue;
                }
                // Copia: el array es el que vive en las estadísticas de la
                // partida y no queremos guardar la traducción dentro del save.
                local c = clone f;
                c.KilledBy = trCausa(c.KilledBy);
                caidos.push(c);
            }
            ret.Fallen = caidos;
            return ret;
        }
    })

    // Caso 39: la pantalla de fin de partida (la derrota y las cinco de
    // jubilación). El epílogo salía entero en inglés con el botón "Salir" al
    // lado, y el marcador como "0 Points" (QA 31/08).
    //
    // El texto sí pasaba por el motor de plantillas, o sea por el wrapper del
    // runtime, pero nunca casaba: getGameFinishData le pega un "\n\n" al final
    // (asset_manager.nut:1724) justo antes de construirlo, y la búsqueda
    // literal es exacta. Con la cola, ningún par del corpus podía casar. Se vio
    // en el log: "partial fail for {And so it ends...}\n\n", o sea que llegó
    // entero y con dos saltos de más.
    //
    // Las de jubilación tienen además otra costura: el texto es la suma de un
    // bloque de plantilla, dos finales de hermano que addBrotherEnding devuelve
    // YA construidos y en castellano, y otro bloque de plantilla. El corpus
    // tiene cada bloque por separado, que es como los vio el extractor, y la
    // suma no casa con ninguno. Como los finales de hermano no se distinguen
    // del resto una vez concatenados, se marcan al salir de addBrotherEnding y
    // aquí se parte por la marca: los trozos marcados pasan intactos (ya están
    // traducidos) y cada trozo crudo se construye por separado, recortándole
    // la cola de la costura y devolviéndosela después. Así cada bloque
    // llega a Rosetta como lo tiene el corpus y se traduce una sola vez, sin
    // segunda pasada sobre texto ya castellano.
    // Solo se recorta el borde FINAL, que es lo único que el juego añade
    // (el "\n\n" de asset_manager.nut:1724). El inicial forma parte del
    // bloque: los ocho párrafos de cierre empiezan por "\n\n{...}", así los
    // tiene el corpus, y quitárselo dejaba el último párrafo del retiro en
    // inglés (QA del 18/10).
    local MARCA = format("%c", 1);
    local recorta = function (_s) {
        local b = _s.len();
        while (b > 0 && _s[b - 1] <= ' ') b--;
        return [_s.slice(0, b), _s.slice(b)];
    };
    mod.hook("scripts/states/world/asset_manager", function (q) {
        q.getGameFinishData = @(__original) function (_gameWon) {
            local ret = __original(_gameWon);
            // "0 Points", que va aparte del texto y casa con su patrón.
            if (ret != null && "Score" in ret) ret.Score = _(ret.Score);
            return ret;
        }
        q.addBrotherEnding = @(__original) function (_brothers, _excludedBackgrounds, _isPositive) {
            local r = __original(_brothers, _excludedBackgrounds, _isPositive);
            return typeof r == "string" && r != "" ? MARCA + r + MARCA : r;
        }
        q.buildGameFinishText = @(__original) function (_text) {
            if (typeof _text != "string") return __original(_text);
            local out = "", i = 0, n = _text.len();
            while (i < n) {
                local a = _text.find(MARCA, i);
                local crudo = a == null ? _text.slice(i) : _text.slice(i, a);
                if (crudo != "") {
                    local p = recorta(crudo);
                    out += p[0] == "" ? crudo : __original(p[0]) + p[1];
                }
                if (a == null) break;
                local b = _text.find(MARCA, a + 1);
                if (b == null) {
                    out += _text.slice(a + 1);
                    break;
                }
                out += _text.slice(a + 1, b);
                i = b + 1;
            }
            return out;
        }
    })

    // Caso 40: el texto de "Tu tarea" de las ambiciones y de los juramentos,
    // que salía entero en inglés. Es el mismo mecanismo del caso 39 y salió del
    // mismo log: getButtonTooltip escribe getTooltipText() + "\n\n"
    // (ambitions/ambition.nut:114 y ambitions/oaths/oath_ambition.nut:31) y la
    // búsqueda literal es exacta, así que con esa cola no casa ningún par. En el
    // log del 31/08 se ven cuatro, con los dos saltos de más pegados detrás
    // ("Discover a ruin, camp or other hostile location...\n\n").
    //
    // Se engancha getTooltipText, que es de donde sale la pieza y que solo usan
    // esos dos constructores: así el corpus ve la cadena tal como la tiene. De
    // paso les llega su turno a las dos ambiciones que componen el texto
    // (la lista de provisiones del séquito y la de asentamientos por visitar),
    // cuyas reglas recursivas <ret:t> tampoco podían casar con la cola.
    mod.hookTree("scripts/ambitions/ambition", function (q) {
        q.getTooltipText = @(__original) function () {
            return _(__original());
        }
    })

    // Caso 41: el tipo de arma del tooltip. Viene de m.Categories ("Polearm,
    // Two-Handed"), y el corpus tenía cada combinación como par. MSU y Legends la
    // recomponen con más tipos ("Axe/Polearm, Two-Handed") y a veces los repiten
    // ("Staff/Staff/Polearm/Polearm, Two-Handed"), y esas sumas no casaban (QA
    // 24/10). Se traduce cada tipo con esta tabla, sacada de los pares que ya
    // había; las palabras sueltas del corpus no sirven, son nombres de objeto
    // ("Polearm" = «Alabarda»). Los repetidos se quitan. Si algún tipo no está
    // en la tabla, la fila se deja como estaba.
    local TIPOS_ARMA = {
        Axe = "Hacha", Bow = "Arco", Cleaver = "Cuchilla", Crossbow = "Ballesta", Dagger = "Daga",
        Firearm = "Arma de fuego", Flail = "Mayal", Hammer = "Martillo", Mace = "Maza",
        ["Musical Instrument"] = "Instrumento musical", Polearm = "Arma de asta", Sling = "Honda",
        Spear = "Lanza", Staff = "Bastón", Sword = "Espada", ["Throwing Weapon"] = "Arma arrojadiza",
        Whip = "Látigo"
    };
    local MANOS = {["One-Handed"] = "Una mano", ["Two-Handed"] = "Dos manos"};
    local function traduceCategorias(_c) {
        local i = _c.find(", ");
        if (i == null) return null;
        local manos = _c.slice(i + 2);
        if (!(manos in MANOS)) return null;
        local tipos = [], vistos = {};
        foreach (t in split(_c.slice(0, i), "/")) {
            if (!(t in TIPOS_ARMA)) return null;
            if (t in vistos) continue;
            vistos[t] <- true;
            tipos.push(TIPOS_ARMA[t]);
        }
        local ret = tipos.reduce(@(a, b) a + "/" + b) + ", " + MANOS[manos];
        if ("BattleBrothersEs" in getroottable() && "Hechos" in ::BattleBrothersEs) ::BattleBrothersEs.Hechos[ret] <- true;
        return ret;
    }
    mod.hookTree("scripts/items/weapons/weapon", function (q) {
        q.getTooltip = @(__original) function () {
            local ret = __original();
            local c = this.m.Categories;
            if (typeof c == "string" && c != "")
                foreach (fila in ret)
                    if ("text" in fila && fila.text == c) {
                        local es = traduceCategorias(c);
                        if (es != null) fila.text = es;
                    }
            return ret;
        }
    })

    // Sonda del caso 3: envuelve los mismos puntos que upstream ya hookea
    // (rosetta/hooks.nut:158-161 y :122) para ver si la consulta llega hasta
    // ellos. No traduce nada; solo escribe en el log. Los hooks de frontera
    // del caso 3 NO se escriben hasta tener la respuesta de esta sonda.
    if (SONDA_CASO3) {
        mod.hookTree("scripts/scenarios/world/starting_scenario", function (q) {
            q.getName = @(__original) function () {
                local ret = __original();
                ::logInfo("rosetta-es sonda3: starting_scenario.getName -> " + ret);
                return ret;
            }
            q.getDescription = @(__original) function () {
                ::logInfo("rosetta-es sonda3: starting_scenario.getDescription dispara");
                return __original();
            }
        })
        mod.hook("scripts/ui/screens/tooltip/tooltip_events", function (q) {
            q.onQueryUIElementTooltipData = @(__original) function (_entityId, _elementId, _elementOwner) {
                ::logInfo("rosetta-es sonda3: onQueryUIElementTooltipData elementId=" + _elementId);
                return __original(_entityId, _elementId, _elementOwner);
            }
        })
    }
})
