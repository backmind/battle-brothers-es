// Arranque minimo para ejecutar codigo de Rosetta fuera del juego.
//
// El test.nut del repo espera un load.nut que solo existe en el arbol de
// desarrollo de stdlib; el zip que se instala en el juego no lo trae. Esto
// hace su trabajo: monta los pocos globales del juego que stdlib y Rosetta
// tocan al cargarse, define ::include con dos raices (la de stdlib y la del
// repo) y carga ::std.
//
// Uso, con el interprete Squirrel del arbol de herramientas del juego:
//
//   STDLIB_DIR=<raiz_stdlib_descomprimido> ROSETTA_DIR=<raiz_repo> \
//     sq.exe es_pack/tools/sq_probe.nut
//
// donde <raiz_stdlib_descomprimido> es donde se haya descomprimido
// stdlib.zip (el que va en la carpeta data del juego) y contiene
// scripts/config/!stdlib.nut y stdlib/*.nut.

::SQ_STDLIB <- getenv("STDLIB_DIR");
::SQ_ROSETTA <- getenv("ROSETTA_DIR");
if (::SQ_STDLIB == null || ::SQ_STDLIB == "") throw "falta STDLIB_DIR";
if (::SQ_ROSETTA == null || ::SQ_ROSETTA == "") throw "falta ROSETTA_DIR";
if (::SQ_STDLIB.slice(::SQ_STDLIB.len() - 1) != "/") ::SQ_STDLIB += "/";
if (::SQ_ROSETTA.slice(::SQ_ROSETTA.len() - 1) != "/") ::SQ_ROSETTA += "/";
// El framework vive vendorizado, con su estructura relativa (vendor/rosetta/ORIGEN.md).
::SQ_VENDOR <- ::SQ_ROSETTA + "vendor/rosetta/";

// Globales del juego que stdlib y Rosetta usan al cargarse.
::Math <- {
    function max( _a, _b ) { return _a > _b ? _a : _b; }
    function min( _a, _b ) { return _a < _b ? _a : _b; }
    function round( _v ) { return floor(_v + 0.5); }
    function rand( _a, _b ) { return _a; }
};
::logInfo <- function ( _s ) {};
::logWarning <- function ( _s ) {};
::logError <- function ( _s ) {};
// matchParts() en !rosetta.nut llama assert() con mensaje (dos argumentos),
// y el assert() nativo de este sq.exe (3.0.7) y del juego solo admite uno:
// "wrong number of parameters" en cuanto una captura :str va seguida de otra.
// No se sustituye: la sonda tiene que fallar donde falla el juego (build_dist
// manda esas reglas a cuarentena).
::Const <- {
    UI = {
        Color = {PositiveValue = "#00ff00", NegativeValue = "#ff0000", DamageValue = "#ff0000"}
        function getColorized( _v, _c ) { return _v; }
    }
};

// El juego resuelve ::include contra su raiz de datos. Aqui hay dos raices.
::include <- function ( _p ) {
    try { dofile(::SQ_STDLIB + _p + ".nut", true); }
    catch (e) { dofile(::SQ_VENDOR + _p + ".nut", true); }
};

dofile(::SQ_STDLIB + "scripts/config/!stdlib.nut", true);
dofile(::SQ_VENDOR + "mocks.nut", true);
dofile(::SQ_VENDOR + "scripts/!mods_preload/!rosetta.nut", true);
