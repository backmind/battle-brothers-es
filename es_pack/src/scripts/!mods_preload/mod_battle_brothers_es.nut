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
    Version = "4.0.0"
    // Contra qué build del juego se verificó y qué parte de sus textos cubre,
    // medida con es_pack/tools/measure_coverage.py. Los tests exigen que
    // coincidan con build_dist.py.
    GameVersion = "1.5.2.3"
    Cobertura = "100 %"
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
    local enlace = @(texto, url) format("<span style='color: lightblue; text-decoration: underline; cursor: pointer;' onclick='openURL(%c%s%c)'>%s</span>", 34, url, 34, texto);
    local parrafo = @(html) "<div class='es-parrafo text-font-normal font-color-description' style='font-weight: normal; white-space: normal; width: 100%;'>" + html + "</div>";
    local pagina = msu.ModSettings.addPage("Informacion", "Información");
    pagina.addTitle("Version", def.Name + " " + def.Version);
    pagina.addTitle("Descripcion", parrafo("Traducción completa al castellano del juego base y de todas sus expansiones. Lo que el pack no conoce se queda en inglés, así que un parche del juego no lo rompe."));
    pagina.addTitle("Estado", parrafo("Verificada en Battle Brothers " + def.GameVersion + ", con todas sus expansiones. Cubre el " + def.Cobertura + " de las frases del juego."));
    pagina.addDivider("Divisor1");
    pagina.addTitle("Creditos", parrafo("Traducción original: MagnusLioncaster, Hjensikk, AMarauder y ElGranFoca.<br>Revisión completa, traducción de todo lo que faltaba, adaptación a Rosetta y mantenimiento: backmind.<br>Framework: Rosetta, de Suor."));
    pagina.addDivider("Divisor2");
    pagina.addTitle("Enlaces", parrafo(enlace("Repositorio en GitHub", repo) + " · " + enlace("Informar de un error o una errata", repo + "/issues/new/choose")));
});

::include("mod_battle_brothers_es/base_es");
::include("mod_battle_brothers_es/ids_es");

// El juego instalado esta en ingles, asi que la autodeteccion de idioma
// de Rosetta (que mira strings ya traducidas) no aplica: activamos es.
::Rosetta.activate("es");
