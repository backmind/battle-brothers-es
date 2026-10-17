// El load.nut que test.nut espera y que el stdlib.zip instalable no trae:
// solo existe en el arbol de desarrollo de stdlib. Este lo sustituye, y con
// el la bateria COMPLETA de upstream corre en esta maquina (validado en la
// adopcion de la 0.5.0: "Tests OK"), cosa que el sq_bootstrap.nut de al lado
// no da, porque ese monta Rosetta directamente para las sondas y test.nut
// quiere cargarla el.
//
// Monta los globales que stdlib y el runtime tocan al cargarse y carga ::std.
// Mismo arranque que sq_bootstrap.nut, sin la parte de Rosetta (test.nut
// carga mocks.nut y !rosetta.nut por su cuenta, relativos al repo).
//
// Uso, desde la raiz del repo:
//   1. descomprimir el stdlib.zip de la carpeta data del juego en un
//      directorio cualquiera (queda scripts/config/!stdlib.nut y stdlib/)
//   2. copiar este fichero ahi como load.nut
//   3. STDLIB_DIR=<ese directorio>/ sq.exe test.nut
// con el sq.exe del arbol de herramientas del juego (la ruta conocida esta
// en check_syntax.py).
local ROOT = getenv("STDLIB_DIR");

::Math <- {
    function max( _a, _b ) { return _a > _b ? _a : _b; }
    function min( _a, _b ) { return _a < _b ? _a : _b; }
    function round( _v ) { return floor(_v + 0.5); }
    function rand( _a, _b ) { return _a; }
};
::logInfo <- function ( _s ) {};
::logWarning <- function ( _s ) {};
::logError <- function ( _s ) {};
::Const <- {
    UI = {
        Color = {PositiveValue = "#00ff00", NegativeValue = "#ff0000", DamageValue = "#ff0000"}
        function getColorized( _v, _c ) { return _v; }
    }
};

// El sq.exe de las herramientas del juego es Squirrel 3.0.7, cuyo assert()
// nativo solo admite un argumento; matchParts() en !rosetta.nut usa la forma
// de dos (mensaje), sintaxis 3.2. Mismo shim que sq_bootstrap.nut.
::assert <- function ( _cond, _msg = null ) {
    if (!_cond) throw _msg == null ? "assertion failed" : _msg;
};

// Dos raices, como en sq_bootstrap.nut: la de stdlib y la del repo (cwd),
// porque !rosetta.nut incluye rosetta/hooks y rosetta/pack_ru relativos.
::include <- function ( _p ) {
    try { dofile(ROOT + _p + ".nut", true); }
    catch (e) { dofile(_p + ".nut", true); }
};
dofile(ROOT + "scripts/config/!stdlib.nut", true);
