"""Genera la version distribuible del pack ES a partir del corpus.

Uso:  PYTHONUTF8=1 uv run python es_pack/tools/build_dist.py

Lee   es_pack/corpus/base_es.nut  (corpus completo)
      es_pack/corpus/<id_del_mod>_es.nut, uno por mod de MODS
Escribe:
  es_pack/build/mod_battle_brothers_es/base_es.nut          pares validos
  es_pack/build/mod_battle_brothers_es/<id_del_mod>_es.nut  los de cada mod
  es_pack/build/mod_battle_brothers_es/titulos_es.nut       titulos en femenino
  es_pack/build/patterns_wip.nut                         cuarentena (Fase 4)
  es_pack/build/scripts/!mods_preload/mod_battle_brothers_es.nut
  es_pack/build/mod_battle_brothers_es_<version>.zip

Reglas de clasificacion por par (contrato real de validateRule en
scripts/!mods_preload/!rosetta.nut):
  drop  sin traduccion (es = "")
  wip   algun placeholder <...> que no cumpla <nombre:tipo> en en o
        <nombre[:flag]> en es; o un tipo de sub no soportado (subRes);
        o dos <...:str> adyacentes en en; o una label en es que no
        existe en en (el runtime 0.4.0 haria throw al cargar el pack)
  dist  todo lo demas
"""
import ast
import contextlib
import re
import shutil
import sys
import tomllib
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "vendor" / "rosetta"))
import rosetta  # vendorizado (vendor/rosetta/ORIGEN.md): load_ref es el parser oficial
import titulos

CORPUS = REPO / "es_pack" / "corpus" / "base_es.nut"
# Las traducciones de mods, una por mod, con la fuente fijada de la que se
# extrajo (su etiqueta es la version que se declara a Rosetta). Van en el mismo
# zip, y el preload solo carga cada una si su mod esta instalado; un test
# comprueba que el preload las conoce todas.
MODS = {"mod_legends": REPO / "es_pack" / "legends" / "fuente.toml"}
# Los pares por id (homografos de m.Name, Rosetta >= 0.5.0) viven en su propio
# fichero fuente-y-artefacto: el load_ref de upstream descarta en silencio los
# bloques sin `en`, asi que dentro de base_es.nut se perderian. Se copia tal
# cual al zip y el preload lo incluye. Censo y criterio: tools/ids_census.py.
IDS = REPO / "es_pack" / "corpus" / "ids_es.nut"
SRC = REPO / "es_pack" / "src"
BUILD = REPO / "es_pack" / "build"

# La versión del juego contra la que se extrajo y verificó el corpus. Es un
# dato para el jugador (sale en el cuadro de la portada), no el nombre del zip.
GAME_VERSION = "1.5.2.3"
# La versión del pack, semver propio. Desde la 4.0.0 continúa la numeración de la
# traducción anterior en Nexus (3.x); las 1.0.x fueron las dos primeras del repo. La comparten los dos zips
# y los dos preloads; test_build_dist impide que se separen.
PACK_VERSION = "4.0.0"
# Parte de las frases del juego que cubre el corpus, medida contra GAME_VERSION
# con measure_coverage.py (necesita el juego instalado, así que no la mide la
# CI). Se actualiza a mano al verificar contra una build nueva.
COBERTURA_JUEGO = "100 %"
# Lo mismo para Legends. La versión es la etiqueta de la fuente fijada de la que
# se extrajo su corpus (fuente.toml); la cobertura se mide sobre esa fuente con
# measure_coverage.py --mod mod_legends y se actualiza a mano al remedirla.
LEGENDS_VERSION = tomllib.loads(MODS["mod_legends"].read_text(encoding="utf-8"))["etiqueta"]
COBERTURA_LEGENDS = "99 %"

# Mismos fuentes, mismo zip byte a byte en cualquier sistema: fecha fija,
# permisos fijos y sistema de origen fijo (zipfile pone 0 en Windows y 3 en
# Unix). La CI construye los zips de la release, y tienen que ser los mismos
# que salen en local. El juego ordena por nombre de zip, nunca por fecha.
FECHA_FIJA = (1980, 1, 1, 0, 0, 0)

# La linea base de los avisos de calidad. En local son informativos y nunca
# bloquean; con --estricto (lo que pasa la CI) el build falla si alguno sube
# por encima de esto. Cada uno esta explicado en su chequeo de checks.py. Si
# baja, se baja aqui en el mismo commit.
LINEA_BASE = {"DUP_VECINO": 18, "TILDES": 2, "TOKENS": 1, "VARIANTES": 19}


def entrada_zip(arco):
    info = zipfile.ZipInfo(arco, date_time=FECHA_FIJA)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    info.create_system = 3
    return info

STR_RE = r'"(?:[^"\\]|\\.)*"'
EN_PLACE_RE = re.compile(r"^<\w+:\w+>$")
ES_PLACE_RE = re.compile(r"^<\w+(:\w+)?>$")
# Etiquetas html literales que aparecen en textos del juego y NO son capturas.
# span y div pueden llevar atributos (Legends: <span style="color:...;">).
HTML_TAG_RE = re.compile(r"^</?(?:br|b|i|u|p|em|strong|hr|(?:span|div)(?:\s[^<>]*)?)\s*/?>$", re.I)

# Tipos de sub soportados por subRes en scripts/!mods_preload/!rosetta.nut
# (validateRule lanza "Label type '%s' is not supported" para cualquier otro).
SUBS = {"int", "val", "word", "str", "line", "tag", "img",
        "int_tag", "val_tag", "str_tag"}

# El corpus codifica caracteres problematicos como \x22 ("), \x7b ({) y
# \x7d (}) dentro de los strings de valor, para que el load_ref de upstream
# pueda re-consumirlos. El escape \xNN de Squirrel es ambiguo en longitud en
# builds UNICODE, asi que la salida de distribucion decodifica de vuelta a
# caracteres literales (evitando depender de que Squirrel interprete \xNN).
DEC_RE = re.compile(r'(?<!\\)((?:\\\\)*)\\x(22|7b|7d)')
_DEC = {"22": '\\"', "7b": "{", "7d": "}"}


def decode_hex_escapes(text):
    return DEC_RE.sub(lambda m: m.group(1) + _DEC[m.group(2)], text)


def cabecera(mod_id="vanilla", version=GAME_VERSION):
    return (
        'if (!("Rosetta" in getroottable())) return;\n'
        'if (::Hooks.SQClass.ModVersion(::Rosetta.Version) '
        '< ::Hooks.SQClass.ModVersion("0.5.0")) return;\n\n'
        "local rosetta = {\n"
        '    mod = {id = "%s", version = "%s"}\n'
        '    author = "comunidad hispana de Battle Brothers"\n'
        '    lang = "es"\n'
        "}\n"
        "local pairs = [\n" % (mod_id, version)
    )


HEADER = cabecera()
FOOTER = "]\n::Rosetta.add(rosetta, pairs);\n"


def corpus_del_pack():
    """Los corpus que van al zip: el del juego base primero y uno por mod."""
    return [{"id": "vanilla", "version": GAME_VERSION, "ruta": CORPUS}] + [
        {"id": mod_id,
         "version": tomllib.loads(toml.read_text(encoding="utf-8"))["etiqueta"],
         "ruta": CORPUS.parent / ("%s_es.nut" % mod_id)}
        for mod_id, toml in MODS.items()]


def get_field(block, name):
    m = re.search(rf"\b{name}\s*=\s*({STR_RE})", block)
    return ast.literal_eval(m.group(1)) if m else None


_ACUMULADORES = ("REF_BLOCKS", "REF_PAIRS", "REF_RULES", "CODE_RULES", "KNOWN_WORDS")
_LISTAS = ("DUP_BLOCKS", "DUP_CAPTURE_BLOCKS", "BAD_PATTERN_BLOCKS")


@contextlib.contextmanager
def parser_prestado(lang="es"):
    """Deja el parser de rosetta.py limpio para nuestro uso y lo devuelve como estaba.

    rosetta.py guarda el estado del parser en globales de modulo. Limpiarlos al
    entrar no basta: si no se restauran al salir, cualquiera que importe este
    modulo se encuentra el parser en lang="es" con los acumuladores llenos, y la
    suite de tests de upstream falla al correr en el mismo proceso que la nuestra.
    """
    previos = {n: getattr(rosetta, n).copy() for n in _ACUMULADORES}
    previos.update({n: getattr(rosetta, n)[:] for n in _LISTAS})
    previas_opts = dict(rosetta.OPTS)

    for n in _ACUMULADORES:
        getattr(rosetta, n).clear()
    for n in _LISTAS:
        del getattr(rosetta, n)[:]
    rosetta.OPTS["lang"] = lang
    rosetta.OPTS["quiet"] = True
    try:
        yield
    finally:
        for n in _ACUMULADORES:
            g = getattr(rosetta, n)
            g.clear()
            g.update(previos[n])
        for n in _LISTAS:
            getattr(rosetta, n)[:] = previos[n]
        rosetta.OPTS.clear()
        rosetta.OPTS.update(previas_opts)


DUPS_DEL_ULTIMO_LOAD = []
"""Bloques con `en` repetido que descarto el ultimo load_blocks.

Vive aqui y no en rosetta.DUP_BLOCKS porque parser_prestado restaura los
globales de upstream al salir: hay que quedarse el dato dentro del contexto.
"""


def load_blocks(path):
    with parser_prestado():
        rosetta.load_ref(str(path))
        DUPS_DEL_ULTIMO_LOAD[:] = rosetta.DUP_BLOCKS
        return list(rosetta.REF_BLOCKS.values())


RULE_KEY_RE = re.compile(r'^\s*(?:plural|split|use)\s*=', re.M)


def is_rule_pair(block):
    """True si el runtime tratara el par como regla (parsePattern) y no como
    literal: mode="pattern", o las claves plural/split/use (ver Rosetta.add)."""
    return 'mode = "pattern"' in block or bool(RULE_KEY_RE.search(block))


CAPTURA_RE = re.compile(r"<\w+:\w+>")
MODE_PATTERN_RE = re.compile(r'^[ \t]*mode = "pattern"\n', re.M)


def literalizar(block):
    """El bloque tal como se emite: un par mode="pattern" sin ninguna captura
    sale como literal. Solo casa su cadena exacta, igual que un literal, pero
    el runtime archiva las reglas por su primera palabra y las prueba en orden
    de carga, así que una regla anterior con la misma clave le gana: "From
    <f:str>" se comía "From what I've heard, %settlement%..." y el jugador leía
    "Desde what I've heard...". Los literales se miran antes que cualquier
    regla. El corpus no cambia: la marca la pone el extractor y volvería."""
    if (MODE_PATTERN_RE.search(block) and not RULE_KEY_RE.search(block)
            and not CAPTURA_RE.search(get_field(block, "en") or "")):
        return MODE_PATTERN_RE.sub("", block, count=1)
    return block


GOLOSA_RE = re.compile(r"^<\w+:str>[^<]{1,16}<\w+:str>$")


def es_golosa(block):
    """Regla que casa con casi cualquier frase inglesa: dos :str abiertas por
    los dos lados alrededor de un conector corto, y ninguna con :t que la haga
    abandonar. "<ailing:str> gains <trait:str>" se comía cualquier "X gains Y"
    que viniera detrás en el corpus: "Hackett gains Deathwish" salía «Hackett
    ahora es Deathwish», y lo mismo con Iron Lungs, Training Experience y
    "+3 Fatigue". Se emiten al final, para que cualquier regla más concreta de
    la misma clave se pruebe antes; el corpus no cambia. Ir al final no basta
    con una frase que no case nada más ("Something gains nothing" salía
    «Something ahora es nothing»), así que esa regla se sustituyó en el
    corpus por una por rasgo. Quedan "leaves the" y "joins the", cuyo
    segundo hueco es el nombre de la compañía, que escribe el jugador."""
    en, es = get_field(block, "en") or "", get_field(block, "es") or ""
    return (is_rule_pair(block) and not RULE_KEY_RE.search(block)
            and bool(GOLOSA_RE.match(en)) and ":t" not in es)


def classify(block):
    en = get_field(block, "en")
    es = get_field(block, "es")
    if en is None or not es:
        return "drop"
    ph_en = re.findall(r"<[^>]*>", en)
    ph_es = re.findall(r"<[^>]*>", es)
    if not ph_en and not ph_es:
        return "dist"
    # Los pares literales (sin mode="pattern" ni plural/split/use) no pasan por
    # parsePattern en el runtime: se registran en strs y nunca validan capturas.
    # Solo se ponen en cuarentena si llevan una expresion cruda de extraccion,
    # que ahi seria texto muerto; las etiquetas html sueltas son literales.
    if not is_rule_pair(block):
        return "wip" if any(not HTML_TAG_RE.match(p) for p in ph_en + ph_es) else "dist"
    en_caps = re.findall(r"<(\w+):(\w+)>", en)
    en_labels = dict(en_caps)
    ok_en = (all(EN_PLACE_RE.match(p) for p in ph_en)
             and all(t in SUBS for t in en_labels.values())
             and len(en_caps) == len(en_labels)
             and not re.search(r"<\w+:str><\w+:str>", en))
    ok_es = (all(ES_PLACE_RE.match(p) for p in ph_es)
             and all(m.group(1) in en_labels
                     for m in re.finditer(r"<(\w+)(?::\w+)?>", es)))
    return "dist" if ok_en and ok_es else "wip"


def emit(path, blocks, cabecera_=HEADER):
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(
        "    " + decode_hex_escapes(b).strip().replace("\n", "\n    ")
        for b in blocks
    )
    path.write_text(cabecera_ + body + "\n" + FOOTER, encoding="utf-8", newline="\n")


WIP_HEADER = (
    "// CUARENTENA: pares con placeholders invalidos; NO cargar en el "
    "juego. Editar el corpus, no este fichero.\n"
)


def emit_wip(path, blocks):
    """Igual que emit() pero SIN header/footer de ::Rosetta.add: este
    fichero es solo para revision humana y nunca debe ser cargable."""
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(decode_hex_escapes(b).strip() for b in blocks)
    path.write_text(WIP_HEADER + body + "\n", encoding="utf-8", newline="\n")


def main():
    blocks = load_blocks(CORPUS)
    print("dups omitidos (en identico): %d" % len(DUPS_DEL_ULTIMO_LOAD))
    # Los dos estados de "sin traducir" son distintos a proposito (la
    # adjudicacion del 27/08, corpus/VACIOS.md): un interno adjudicado va
    # como linea // en = "..." (la forma de upstream: sobrevive a -r y no
    # cuenta como NEW en -c) y un bloque con es vacio es deuda pendiente,
    # que es lo que el cubo drop mide desde entonces. Asi, tras un bump del
    # juego, las cadenas nuevas caen en drop y no se confunden con lo ya
    # descartado.
    internos = len(re.findall(r"^\s*// en = ", CORPUS.read_text(encoding="utf-8"), re.M))
    print("internos adjudicados (// en): %d" % internos)
    buckets = {"dist": [], "wip": [], "drop": []}
    for b in blocks:
        buckets[classify(b)].append(b)
    print("total: %d  dist: %d  wip: %d  drop: %d" % (
        len(blocks), len(buckets["dist"]), len(buckets["wip"]),
        len(buckets["drop"])))
    # Dos poblaciones (decision del propietario, 29/08): los pares extraidos
    # del juego base son fijos por version; los marcados con // @composicion
    # nacen fuera de esa extraccion (composicion en runtime, framework MSU,
    # rescates de QA) y son los que hacen crecer el total sin que cambie el
    # juego. El registro es incremental: familias antiguas se marcan al
    # tocarlas.
    composicion = sum(1 for b in buckets["dist"] if "@composicion" in b)
    print("de composicion (marcados @composicion): %d  extraidos: %d" % (
        composicion, len(buckets["dist"]) - composicion))

    pairs_rel = Path("mod_battle_brothers_es/base_es.nut")
    ids_rel = Path("mod_battle_brothers_es/ids_es.nut")
    titulos_rel = Path("mod_battle_brothers_es/titulos_es.nut")
    # Todo lo que cuelga de src/scripts y de src/mod_battle_brothers_es entra
    # en el build y en el zip tal cual: el wrapper del preload, los hooks
    # propios del pack y el enganche con cada mod.
    scripts_rel = sorted(p.relative_to(SRC)
                         for d in ("scripts", "mod_battle_brothers_es")
                         for p in (SRC / d).rglob("*") if p.is_file())

    emit(BUILD / pairs_rel, [literalizar(b) for b in sorted(buckets["dist"], key=es_golosa)])
    (BUILD / ids_rel).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(IDS, BUILD / ids_rel)
    print("ids: %d pares por id" %
          IDS.read_text(encoding="utf-8").count('{id = "scripts/'))

    # Los corpus de los mods no suman en las cifras del base: cada uno da su
    # linea. La cuarentena es una sola, porque un patron roto de cualquiera
    # aborta la carga igual.
    wip = list(buckets["wip"])
    dist = list(buckets["dist"])
    mods_rel = []
    for c in corpus_del_pack()[1:]:
        mod_buckets = {"dist": [], "wip": [], "drop": []}
        for b in load_blocks(c["ruta"]):
            mod_buckets[classify(b)].append(b)
        print("%s %s: dist: %d  wip: %d  drop: %d" % (
            c["id"], c["version"], len(mod_buckets["dist"]),
            len(mod_buckets["wip"]), len(mod_buckets["drop"])))
        rel = Path("mod_battle_brothers_es") / c["ruta"].name
        emit(BUILD / rel, mod_buckets["dist"], cabecera(c["id"], c["version"]))
        mods_rel.append(rel)
        wip += mod_buckets["wip"]
        dist += mod_buckets["dist"]
        avisar_calidad(mod_buckets["dist"], c["id"])

    fem = titulos.tabla((get_field(b, "en"), get_field(b, "es")) for b in dist)
    (BUILD / titulos_rel).write_text(titulos.emite(fem), encoding="utf-8", newline="\n")
    print("titulos en femenino: %d" % len(fem))
    emit_wip(BUILD / "patterns_wip.nut", wip)
    for rel in scripts_rel:
        (BUILD / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(SRC / rel, BUILD / rel)

    zip_path = BUILD / ("mod_battle_brothers_es_%s.zip" % PACK_VERSION)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in list(scripts_rel) + [pairs_rel, ids_rel] + mods_rel + [titulos_rel]:
            z.writestr(entrada_zip(rel.as_posix()), (BUILD / rel).read_bytes())
    print("zip:", zip_path)
    sintaxis_ok = avisar_sintaxis()
    avisos = avisar_calidad(blocks)
    if "--estricto" in sys.argv:
        problemas = problemas_estrictos(sintaxis_ok, avisos, len(wip))
        for linea in problemas:
            print("ESTRICTO: " + linea)
        if problemas:
            raise SystemExit(1)


def problemas_estrictos(sintaxis_ok, avisos, wip):
    """Lo que hace fallar el build en la CI: sintaxis sin comprobar o rota,
    patrones en cuarentena, o un aviso de calidad por encima de su linea base."""
    problemas = []
    if not sintaxis_ok:
        problemas.append("la sintaxis no se ha podido comprobar o falla")
    if wip:
        problemas.append("%d patrones en cuarentena (wip)" % wip)
    if avisos is None:
        problemas.append("los avisos de calidad no se han podido calcular")
    else:
        for k, n in sorted(avisos.items()):
            if n > LINEA_BASE.get(k, 0):
                problemas.append("%s %d, la linea base es %d" % (k, n, LINEA_BASE.get(k, 0)))
    return problemas


def avisar_sintaxis():
    """Compila el pack generado si hay interprete Squirrel. Informativo:
    un fallo se avisa a gritos pero no rompe el build, igual que los avisos
    de calidad."""
    try:
        from check_syntax import artefactos, comprueba
        interprete, fallos = comprueba(artefactos())
        if interprete is None:
            print("sintaxis: sin interprete Squirrel, no se comprueba")
            return False
        if fallos:
            for f, err in fallos:
                print("SINTAXIS FALLA %s: %s" % (Path(f).name, err.splitlines()[0] if err else ""))
            return False
        print("sintaxis: OK (%s)" % interprete.name)
        return True
    except Exception as e:  # noqa: BLE001
        print("sintaxis: no se pudo comprobar (%s)" % e)
        return False


def avisar_calidad(blocks, corpus=""):
    """Avisos de calidad del corpus: informativos, nunca bloquean el build.
    Si el modulo de chequeos falla, el build sigue adelante igual. La linea
    base de --estricto solo vale para el base: los mods dan su cuenta aparte."""
    try:
        from checks import revisar  # import diferido: checks importa este modulo
        datos = [(get_field(b, "en"), get_field(b, "es")) for b in blocks]
        avisos = revisar([(en, es) for en, es in datos if en and es])
        resumen = ", ".join("%s %d" % (k, len(v)) for k, v in sorted(avisos.items()) if v)
        print("avisos de calidad%s: %s" % (corpus and " " + corpus, resumen or "ninguno"))
        return {k: len(v) for k, v in avisos.items()}
    except Exception as err:
        print("avisos de calidad: no disponibles (%s)" % err)
        return None


if __name__ == "__main__":
    main()
