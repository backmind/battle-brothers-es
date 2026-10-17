// Comprueba si el mecanismo de pares por `id` resuelve los homografos.
//
// Un homografo es un mismo literal ingles que el juego usa en dos sitios que
// piden traducciones distintas. El caso real de este pack: "Dagger" es el
// nombre del tipo de arma (scripts/items/weapons/dagger.nut) y a la vez una
// entrada de la lista de nombres legendarios (Const.Strings.DaggerNames). Con
// un solo par literal por `en`, uno de los dos usos sale mal.
//
// Rosetta ya trae la pieza que hace falta: translate(_str, _id) mira primero el
// mapa de ids, y rosetta/hooks.nut tiene makeGetter(_field), que compone el id
// como "<ruta del script>.<campo>". Lo que falta es que los nombres de objeto y
// habilidad lo usen: hoy van con simpleGetter, que no pasa id.
//
// Uso (ver es_pack/tools/sq_bootstrap.nut para las variables):
//   STDLIB_DIR=... ROSETTA_DIR=... sq.exe es_pack/tools/sq_probe_ids.nut

dofile(getenv("ROSETTA_DIR") + "/es_pack/tools/sq_bootstrap.nut", true);

local def = ::Rosetta;
local meta = {mod = {id = "probe_ids", version = "1.0.0"}, lang = "es"};
::probe_fallos <- 0;

function comprueba( _titulo, _entrada, _id, _esperado ) {
    local r = ::Rosetta.translate(_entrada, _id);
    local ok = r == _esperado;
    if (!ok) ::probe_fallos++;
    print((ok ? "  ok   " : "  FALLO") + "  " + _titulo + "\n"
          + "         translate(\"" + _entrada + "\""
          + (_id == null ? "" : ", \"" + _id + "\"") + ")\n"
          + "         obtenido: " + (r == null ? "null" : "\"" + r + "\"") + "\n"
          + (ok ? "" : "         esperado: \"" + _esperado + "\"\n"));
}

// El par literal se queda con el nombre legendario; el par por id, con el arma.
def.add(meta, [
    {en = "Dagger", es = "Último Beso"}
    {id = "scripts/items/weapons/dagger.Name", es = "Daga"}
]);
def.activate("es");

print("\n=== sin id: gana el literal, que aqui es el nombre legendario ===\n");
comprueba("literal suelto", "Dagger", null, "Último Beso");

print("=== con id: gana el par por id, que es lo que el arma necesita ===\n");
comprueba("mismo literal, con id del arma", "Dagger",
          "scripts/items/weapons/dagger.Name", "Daga");

print("=== un id sin par cae al literal, sin romper nada ===\n");
comprueba("id desconocido", "Dagger",
          "scripts/items/weapons/sword.Name", "Último Beso");

print("=== y el id no estorba a una cadena sin par ninguno ===\n");
comprueba("sin traduccion", "Halberd", "scripts/items/weapons/halberd.Name", "Halberd");

print("fallos: " + ::probe_fallos + "\n");
