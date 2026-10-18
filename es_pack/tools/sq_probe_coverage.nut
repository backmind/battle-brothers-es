// Sonda de cobertura: ejecuta el emparejador REAL de Rosetta sobre la lista de
// literales que measure_coverage.py extrajo del arbol del juego, y clasifica
// cada uno con las funciones reales del runtime, no comparando texto.
//
// Por que translate() no basta por si solo para todo: un literal ESTATICO (sin
// concatenacion) es el string real del juego, y pasarlo a translate() es la
// medida correcta. Pero un literal de PATRON (extraido de una concatenacion,
// "<actor> gains <v> Experience") es una PLANTILLA sin tipar, no un string que
// vaya a existir nunca en el juego tal cual: el runtime necesitaria el valor
// real ("Anatomist", "[color=..]+100[/color]") para que matchParts() casara la
// captura tipada del corpus (<v:val_tag> exige corchetes). Pasar la plantilla
// cruda a translate() da falsos negativos sistematicos y seria el mismo error
// de fondo que comparar cadenas. La pieza que SI vale sin un valor real es
// _iterKeys(), la funcion con la que translate() decide que reglas probar: si
// ninguna clave no vacia de la plantilla tiene reglas en el mapa, no hay
// ninguna regla que pudiera aplicar, con certeza (hueco real). Si alguna clave
// si tiene reglas, hay una candidata real, aunque el casado completo con tipos
// no queda demostrado sin el valor real (candidato, no confirmado).
//
// La clave vacia que _iterKeys() anade siempre al final se descarta a
// proposito: es un cajon de sastre que comparten reglas sin relacion (todas
// las reglas cuyo en se reduce a puras stopwords), y contarla metería el mismo
// tipo de falso positivo que la comparacion de cadenas que esta tarea prohibe.
//
// Entrada, todo por variables de entorno (ver measure_coverage.py):
//   ROSETTA_DIR, STDLIB_DIR   como sq_bootstrap.nut
//   COV_PACK                  los packs construidos a cargar, separados por ";"
//                             (base_es.nut, y el del mod si se mide un mod)
//   COV_DATOS                 .nut que define COV_LITERALES, COV_DROP_PATTERN_EN
//                             y COV_WIP_PATTERN_EN (measure_coverage.py lo genera)
//
// Salida: una linea por literal en COV_LITERALES, en su mismo orden (indice
// 0-based), separada por tabuladores: "<indice>\t<clase>\t<detalle>". El texto
// del literal no viaja de vuelta: measure_coverage.py ya lo tiene en memoria en
// esa misma posicion, y evita tener que escapar/desescapar tabuladores y saltos
// de linea reales en la salida.
//
// Clases para literales estaticos (mode distinto de "pattern"):
//   OK_DIRECTO   translate(en) devolvio algo distinto: cubierto, medida directa
//   OK_IDENTICO  translate(en) devolvio en mismo, pero en es clave del mapa
//                strs: par cubierto cuyo es es igual al en (nombres propios)
//   HUECO        translate(en) devolvio en mismo y en no esta en strs: hueco real
//
// Clases para literales de patron (mode == "pattern"):
//   PAT_OK_DIRECTO  translate() sobre la plantilla cruda ya dio otra cosa
//                   (raro: implicaria que el propio marcador sin tipar
//                   casa con una regla, pero se registra si ocurre)
//   PAT_CANDIDATO   alguna clave no vacia tiene reglas reales en el mapa
//   PAT_HUECO       ninguna clave no vacia tiene reglas: hueco real. El
//                   detalle lleva "drop" o "wip" si esa misma clave la
//                   explica un patron sin traducir o en cuarentena del
//                   corpus (deuda de traduccion, no de cobertura)

::SQ_STDLIB <- getenv("STDLIB_DIR");
::SQ_ROSETTA <- getenv("ROSETTA_DIR");
local covPack = getenv("COV_PACK");
local covDatos = getenv("COV_DATOS");
if (covPack == null || covPack == "") throw "falta COV_PACK";
if (covDatos == null || covDatos == "") throw "falta COV_DATOS";

dofile(::SQ_ROSETTA + "/es_pack/tools/sq_bootstrap.nut", true);
foreach (p in split(covPack, ";")) dofile(p, true);
::Rosetta.activate("es");
dofile(covDatos, true);

local amap = ::Rosetta.maps["es"];

function clavesNoVacias(_str) {
    local ks = [];
    foreach (k in ::Rosetta._iterKeys(_str)) if (k != "") ks.push(k);
    return ks;
}

function algunaClaveEnReglas(_claves) {
    foreach (k in _claves) {
        if (k in amap.rules && amap.rules[k].len() > 0) return true;
    }
    return false;
}

// Claves que YA tiene un patron del corpus sin embarcar (drop: sin traducir;
// wip: en cuarentena por sintaxis). Sirven solo para anotar un PAT_HUECO como
// deuda de traduccion en vez de ausencia real, nunca para contar cobertura:
// esos patrones no estan en el pack cargado, asi que translate() nunca los usa.
local dropKeys = {}, wipKeys = {};
foreach (en in ::COV_DROP_PATTERN_EN) dropKeys[::Rosetta._ruleKey(en)] <- true;
foreach (en in ::COV_WIP_PATTERN_EN) wipKeys[::Rosetta._ruleKey(en)] <- true;

local total = ::COV_LITERALES.len();
for (local i = 0; i < total; i++) {
    local item = ::COV_LITERALES[i];
    local en = item.en;

    if (item.mode == "pattern") {
        local claves = clavesNoVacias(en);
        local traducido = ::Rosetta.translate(en);
        if (traducido != en) {
            print(i + "\tPAT_OK_DIRECTO\t\n");
        } else if (algunaClaveEnReglas(claves)) {
            print(i + "\tPAT_CANDIDATO\t\n");
        } else {
            local anota = "";
            foreach (k in claves) {
                if (k in dropKeys) { anota = "drop"; break; }
                if (k in wipKeys) { anota = "wip"; break; }
            }
            print(i + "\tPAT_HUECO\t" + anota + "\n");
        }
    } else {
        local traducido = ::Rosetta.translate(en);
        if (traducido != en) {
            print(i + "\tOK_DIRECTO\t\n");
        } else if (en in amap.strs) {
            print(i + "\tOK_IDENTICO\t\n");
        } else {
            print(i + "\tHUECO\t\n");
        }
    }
}
