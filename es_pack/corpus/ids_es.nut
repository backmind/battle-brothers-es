// Pares por id: homógrafos de m.Name que el par literal no puede resolver.
//
// Desde Rosetta 0.5.0, getName de objetos, habilidades y entidades pasa
// `<ruta del script>.Name` como id, y translate() mira el mapa de ids antes
// que el literal. Cada entrada de aquí recupera un uso que hasta ahora estaba
// sacrificado: el par literal daba su valor al uso visible y el otro fichero
// se quedaba con lo que hubiera. El par literal de base_es.nut NO se toca:
// sigue sirviendo a los consumidores sin id (tablas de config, composiciones).
//
// Este fichero es fuente Y artefacto: build_dist.py lo copia tal cual al zip
// y el preload lo incluye después de base_es. Vive fuera de base_es.nut
// porque el load_ref de upstream descarta en silencio los bloques sin `en`
// (comprobado en la adopción de la 0.5.0), así que ahí se perdería.
//
// El censo del que salen (y sus descartes razonados): tools/ids_census.py,
// ejecutado el 27/08/2026 contra el árbol de referencia. Valores de la
// referencia 3.0.5, SIN pasar por el censo ciego: se revisan en QA como el
// resto de lo nuevo. Antes de añadir una entrada: correr el censo y mirar la
// contraparte, que el valor no pertenezca ya a otro uso.
if (!("Rosetta" in getroottable())) return;
if (::Hooks.SQClass.ModVersion(::Rosetta.Version)
    < ::Hooks.SQClass.ModVersion("0.5.0")) return;

local rosetta = {
    mod = {id = "vanilla-ids", version = "1.5.2.3"}
    author = "comunidad hispana de Battle Brothers"
    lang = "es"
}
local pairs = [
    // La armadura ligera de trol perdía su "ligera": el literal "Armor" es de
    // la pesada.
    {id = "scripts/items/armor/barbarians/unhold_armor_light.Name", es = "Armadura ligera de trol"}
    // Los dos cascos de trol tienen m.Name = "Armor" en vanilla y mostraban
    // "Armadura de trol" siendo piezas de cabeza. Decisión del propietario
    // (tanda del 27/08): nombre propio, con el espejo ligero/pesado de las
    // armaduras. La referencia no da valor (los dejó en inglés).
    {id = "scripts/items/helmets/barbarians/unhold_helmet_heavy.Name", es = "Casco de trol"}
    {id = "scripts/items/helmets/barbarians/unhold_helmet_light.Name", es = "Casco ligero de trol"}
    // El arma (orc_metal_club, "Porra gigante") ganó el literal "Cudgel"; la
    // habilidad de golpear con ella es un verbo.
    {id = "scripts/skills/actives/cudgel_skill.Name", es = "Aporrear"}
    // "Drag" tiene el es vacío en el corpus a propósito (ambiguo suelto);
    // los dos usos con conducto son la misma acción.
    {id = "scripts/skills/actives/kraken_move_ensnared_skill.Name", es = "Arrastrar"}
    {id = "scripts/skills/actives/serpent_hook_skill.Name", es = "Arrastrar"}
    // El arma ("Mayal") ganó el literal "Flail"; la habilidad es el verbo.
    {id = "scripts/skills/actives/flail_skill.Name", es = "Flagelar"}
    // La variante orca del puñetazo comparte literal con la genérica.
    {id = "scripts/skills/actives/hand_to_hand_orc.Name", es = "Puñetazos potentes"}
    // "Hex" con es vacío en el corpus; los dos usos con conducto son el
    // maleficio de la bruja.
    {id = "scripts/skills/actives/hex_skill.Name", es = "Maleficio"}
    {id = "scripts/skills/effects/hex_slave_effect.Name", es = "Maleficio"}
    // El literal "Poison" se volteó al genérico "Veneno" (tanda del 27/08),
    // así que la araña ya no necesita par propio; el goblin conserva su
    // apellido por id.
    {id = "scripts/skills/racial/goblin_ambusher_racial.Name", es = "Veneno goblin"}
    // "Split" es "Dividir" en los dos usos espectrales y de formación; el
    // golpe de hacha es partir.
    {id = "scripts/skills/actives/split_axe.Name", es = "Partir"}
    // Vanilla reutiliza "Unleash Wardog" también para la variante que suelta
    // lobos; la referencia lo corrige por fichero, que es justo lo que el id
    // permite respetar.
    {id = "scripts/skills/actives/unleash_wolf.Name", es = "Liberar lobo"}
    // El efecto de veneno de araña comparte literal con el genérico
    // ("Arma recubierta con veneno").
    {id = "scripts/skills/effects/spider_poison_coat_effect.Name", es = "Arma recubierta de veneno de araña"}
    // Once habilidades cuyo literal quedó retenido en la sección config/ai.nut
    // del corpus (el extractor deduplica por en: el nombre de comportamiento
    // de IA y el de la habilidad son la misma cadena). El literal suelto se
    // queda vacío a propósito, como Hex y Drag; el id apunta al fichero que
    // sí se pinta (tooltip y registro de combate vía getName). Valores de la
    // referencia 3.0.5, verificados fichero a fichero el 27/08.
    {id = "scripts/skills/actives/hook.Name", es = "Enganchar"}
    {id = "scripts/skills/actives/rally_the_troops.Name", es = "Arengar"}
    {id = "scripts/skills/actives/darkflight.Name", es = "Vuelo oscuro"}
    {id = "scripts/skills/actives/warcry.Name", es = "Grito de guerra"}
    {id = "scripts/skills/actives/charge.Name", es = "Cargar"}
    {id = "scripts/skills/actives/horror_skill.Name", es = "Horror"}
    {id = "scripts/skills/actives/miasma_skill.Name", es = "Miasma"}
    {id = "scripts/skills/actives/charm_skill.Name", es = "Encantar"}
    {id = "scripts/skills/actives/sleep_skill.Name", es = "Adormecer"}
    {id = "scripts/skills/actives/wither_skill.Name", es = "Marchitar"}
    {id = "scripts/skills/actives/explode_skill.Name", es = "Explotar"}
    // "Old" es homografo de dos usos sin nada que ver: el modificador de
    // objeto famoso ("Old Sword", que el corpus da como "de antano") y el
    // rasgo de edad. El literal sirve al objeto, que no tiene conducto con
    // id; el rasgo se recupera aqui. Antes la ficha del hermano decia
    // "de antano" y el mensaje de rasgo ganado "es ahora un de antano".
    {id = "scripts/skills/traits/old_trait.Name", es = "Viejo"}
    // Los otros dos rasgos con el mismo problema, encontrados en la QA del
    // 31/08 al barrer TODOS los m.Name del arbol contra el corpus. "Quick" es
    // el prefijo de objeto famoso de item_names.nut ("veloz") y "Strong" el
    // descriptor de fuerza de partida de strings.nut ("fuerte"): los dos
    // literales se quedan como estan, que sirven a su uso, y el rasgo se
    // recupera aqui. La pieza de composicion del mensaje de rasgo ganado
    // ("un Rapido", "un Fuerte") va en base_es.nut, como la de Viejo.
    {id = "scripts/skills/traits/quick_trait.Name", es = "Rápido"}
    {id = "scripts/skills/traits/strong_trait.Name", es = "Fuerte"}
]
::Rosetta.add(rosetta, pairs);
