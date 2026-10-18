// Sonda del cuelgue de translate() (4.0.1): con el runtime real de Rosetta, el
// pack y su memoria (el bloque final del preload mod_battle_brothers_es.nut,
// que el test copia aparte), ninguna traducción
// puede disparar la recursión exponencial de las reglas golosas con :t
// ("<actor:str> has <name:str>" y compañía).
//
// Cuenta las llamadas a translate() de cada texto, memoria incluida, y corta
// en SONDA_TOPE: así la sonda falla en segundos en vez de colgarse si la
// memoria falta o deja de funcionar. Mide dos cosas:
//   - una frase inglesa sin par con "has" y "had" alternos (sin memoria, doce
//     separadores ya eran 150 000 llamadas y 15 s);
//   - cada texto ya traducido del pack pasado otra vez por translate(), como
//     cuando el juego vuelve a pintar algo que ya salió en castellano (sin
//     memoria, el tooltip de la moral eran 13 700 llamadas y 4 s).
//
// Uso (lo lanza test_build_dist.py):
//   ROSETTA_DIR=<raiz_repo> STDLIB_DIR=<stdlib descomprimido>
//   SONDA_PACKS=<base_es.nut;...> SONDA_MEMO=<ese bloque, en un .nut>
//   SONDA_TOPE=<llamadas> sq.exe <esta sonda>
// SONDA_MEMO vacío carga el pack sin memoria (para ver la sonda fallar).
// Al final imprime "FALLOS: <n>".

dofile(getenv("ROSETTA_DIR") + "/es_pack/tools/sq_bootstrap.nut", true);
foreach (p in split(getenv("SONDA_PACKS"), ";")) dofile(p, true);
::Rosetta.activate("es");
local memo = getenv("SONDA_MEMO");
if (memo != null && memo != "") dofile(memo, true);

local tope = getenv("SONDA_TOPE").tointeger();
local translate = ::Rosetta.translate;
::sondaLlamadas <- 0;
::Rosetta.translate <- function (_str, _id = null, _skip_rule = null) {
    if (++::sondaLlamadas > tope) throw "TOPE";
    return translate.call(this, _str, _id, _skip_rule);
};

local fallos = 0;
local function mide( _titulo, _str ) {
    ::sondaLlamadas = 0;
    local r = null;
    try { r = ::Rosetta.translate(_str); } catch (e) { if (e != "TOPE") throw e; }
    if (r == null) {
        fallos++;
        print("  FALLO  " + _titulo + ": más de " + tope + " llamadas\n");
    }
    return ::sondaLlamadas;
}

local s = "Zq";
for (local i = 0; i < 24; i++) s += (i % 2 == 0 ? " has Zq" : " had Zq");
print("  frase con 24 has/had: " + mide("frase con 24 has/had", s) + " llamadas\n");

local n = 0, peor = 0;
foreach (en, es in ::Rosetta.maps.es.strs) {
    n++;
    local c = mide("retraducción de \"" + es.slice(0, es.len() < 60 ? es.len() : 60) + "\"", es);
    if (c > peor) peor = c;
}
print("  textos ya traducidos: " + n + ", peor caso " + peor + " llamadas\n");
print("FALLOS: " + fallos + "\n");
