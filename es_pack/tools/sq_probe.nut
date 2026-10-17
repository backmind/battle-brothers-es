// Comprueba, contra el runtime real de Rosetta, que los nombres compuestos en
// ejecucion no se traducen con pares de las piezas.
//
// Motivo: scripts/items/weapons/named/named_weapon.nut construye el nombre de
// los objetos legendarios concatenando dos listas de config/item_names.nut,
// PrefixList[i] + " " + NameList[j]. La cadena resultante ("Glorious Sword")
// no existe como literal en ningun fichero del juego, asi que traducir
// "Glorious" y "Sword" por separado no sirve de nada. Este fichero lo
// demuestra en vez de razonarlo.
//
// Uso (ver es_pack/tools/sq_bootstrap.nut para las variables):
//   STDLIB_DIR=... ROSETTA_DIR=... sq.exe es_pack/tools/sq_probe.nut

dofile(getenv("ROSETTA_DIR") + "/es_pack/tools/sq_bootstrap.nut", true);

local def = ::Rosetta;
local meta = {mod = {id = "probe", version = "1.0.0"}, lang = "es"};
local fallos = 0;

function comprueba( _titulo, _entrada, _esperado ) {
    local r = ::Rosetta.translate(_entrada);
    local ok = r == _esperado;
    if (!ok) ::probe_fallos++;
    print((ok ? "  ok   " : "  FALLO") + "  " + _titulo + "\n"
          + "         translate(\"" + _entrada + "\")\n"
          + "         obtenido: " + (r == null ? "null" : "\"" + r + "\"") + "\n"
          + (ok ? "" : "         esperado: " + (_esperado == null ? "null" : "\"" + _esperado + "\"") + "\n"));
}
::probe_fallos <- 0;

// Las piezas, tal como estan en el corpus.
def.add(meta, [
    {en = "Glorious", es = "glorioso"}
    {en = "Sword", es = "Espada recta"}
    {en = "Sir Donatus", es = "Ser Aegon"}
]);
def.activate("es");

print("\n=== las piezas por separado si se traducen ===\n");
comprueba("prefijo suelto", "Glorious", "glorioso");
comprueba("nombre suelto", "Sword", "Espada recta");

print("=== lo que el juego compone en ejecucion NO se traduce ===\n");
comprueba("prefijo + nombre", "Glorious Sword", "Glorious Sword");
comprueba("caballero + nombre", "Sir Donatus's Sword", "Sir Donatus's Sword");

print("=== una regla de patron con captura traducida si compone ===\n");
// Funciona mecanicamente, pero el adjetivo no concuerda con el sustantivo:
// espada es femenino y sale "glorioso". Por eso hace falta declarar variantes
// o resolverlo con una regla `use`.
def.add(meta, [
    {mode = "pattern", en = "<prefix:word> Sword", es = "Espada recta <prefix:t>"}
]);
def.activate("es");
comprueba("patron con <prefix:t>", "Glorious Sword", "Espada recta glorioso");

print("fallos: " + ::probe_fallos + "\n");
