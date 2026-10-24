// Sonda del orden de las reglas (24/10): con el runtime real de Rosetta, los
// packs y ::BattleBrothersEs.ordenaReglas (el bloque del preload que el test
// copia aparte), una regla con <x:str> abierto ya no tapa a otra más concreta
// de la misma clave, tampoco a las que se cargan después (Legends).
//
// Uso (lo lanza test_build_dist.py):
//   ROSETTA_DIR=<raiz_repo> STDLIB_DIR=<stdlib descomprimido>
//   SONDA_PACKS=<base_es.nut;...> SONDA_ORDEN=<ese bloque, en un .nut>
//   SONDA_CASOS=<en|es;en|es...> sq.exe <esta sonda>
// Al final imprime "FALLOS: <n>".

dofile(getenv("ROSETTA_DIR") + "/es_pack/tools/sq_bootstrap.nut", true);
foreach (p in split(getenv("SONDA_PACKS"), ";")) dofile(p, true);
::Rosetta.activate("es");
::BattleBrothersEs <- {};
dofile(getenv("SONDA_ORDEN"), true);
::BattleBrothersEs.ordenaReglas();

local fallos = 0;
foreach (caso in split(getenv("SONDA_CASOS"), ";")) {
    local i = caso.find("|"), en = caso.slice(0, i), es = caso.slice(i + 1);
    local r = ::Rosetta.translate(en);
    if (r != es) {
        fallos++;
        print("FALLO  " + en + "\n  obtenido: " + r + "\n  esperado: " + es + "\n");
    } else print("ok     " + en + "\n");
}
print("FALLOS: " + fallos + "\n");
