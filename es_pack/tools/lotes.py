"""Prepara la traducción por lotes de un mod grande (hoy, Legends).

Uso:
    PYTHONUTF8=1 uv run python es_pack/tools/lotes.py extraer [--forzar]

  extraer   clona la fuente fijada en es_pack/legends/fuente.toml, saca el
            corpus con el extractor de Rosetta y criba lo que ya traduce
            base_es.nut: Rosetta tiene una sola tabla por idioma con el `en`
            como clave, así que un `en` repetido entre corpus sobra en el
            mejor caso y, en el peor, pisa al del base (ver el spec).

El corpus resultante es la fuente de verdad; todo se escribe por bytes y en LF.
"""
import difflib
import functools
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from collections import Counter
from dataclasses import dataclass
from itertools import groupby
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_dist import CORPUS, REPO, get_field, is_rule_pair, load_blocks  # noqa: E402

LEGENDS = REPO / "es_pack" / "legends"
FUENTE_TOML = LEGENDS / "fuente.toml"
FUENTE = LEGENDS / "fuente"
LOTES = LEGENDS / "lotes"
CORPUS_LEGENDS = REPO / "es_pack" / "corpus" / "mod_legends_es.nut"
ROSETTA_PY = REPO / "vendor" / "rosetta" / "rosetta.py"
SIN_COMMIT = "<sin fijar>"

FILE_RE = re.compile(r"^\s*// FILE: (.+)$")
CONTEXT_RE = re.compile(r"^\s*// context: (.+)$")
EN_LINEA_RE = re.compile(r'^\s*en = ("(?:[^"\\]|\\.)*")\s*$', re.M)
CABECERA_MOD_RE = re.compile(r'mod = \{id = "mod_", version = "\.\.\."\}')


@dataclass
class Bloque:
    file: str
    inicio: int  # líneas inicio..fin inclusive, 0-based, del texto partido por \n
    fin: int
    texto: str
    en: str | None
    es: str | None
    contexto: str | None = None  # la línea `// context:` del extractor, si la hay


def bloques(texto):
    """Los pares del corpus con el `// FILE:` del que salen.

    Cuenta con el formato que emite el extractor: cada par abre con una línea
    que es exactamente "    {" y cierra con la siguiente "    }".
    """
    lineas = texto.split("\n")
    res, file, inicio, contexto = [], "?", None, None
    for i, linea in enumerate(lineas):
        if inicio is None:
            m = FILE_RE.match(linea)
            c = CONTEXT_RE.match(linea)
            if m:
                file, contexto = m.group(1).strip(), None
            elif c:
                contexto = c.group(1).strip()
            elif linea == "    {":
                inicio = i
        elif linea == "    }":
            t = "\n".join(lineas[inicio:i + 1])
            res.append(Bloque(file, inicio, i, t, get_field(t, "en"), get_field(t, "es"), contexto))
            inicio, contexto = None, None
    return res


def duplicados(texto):
    cuenta = Counter(b.en for b in bloques(texto) if b.en is not None)
    return sorted(en for en, n in cuenta.items() if n > 1)


def ens_base():
    return {get_field(b, "en") for b in load_blocks(CORPUS)} - {None}


def cribar(texto, base):
    """Cambia por `// en = "..."` cada par cuyo `en` ya traduce base_es.nut."""
    lineas = texto.split("\n")
    n = 0
    for b in reversed(bloques(texto)):
        if b.en in base:
            literal = EN_LINEA_RE.search(b.texto).group(1)
            lineas[b.inicio:b.fin + 1] = ["    // en = %s" % literal, "    // en base_es"]
            n += 1
    return "\n".join(lineas), n


# Grupos de un par corto según su `// context:`. Las listas de nombres siguen
# la convención de la 1.0 (nombres opacos tal cual, transparentes traducidos)
# y no entran en el glosario; los términos son nombres de cosas del juego.
LISTA_RE = re.compile(r"Names|NameList|Mottos|Titles\b|\.extend\(\)|Array\.rand")
TERMINO_RE = re.compile(r"\.m\.Name$|\(\)\.Name$|PerkName\.|EntityType\.addNew|\.m\.Title$|setTitle|LegendArmorLayers|\.Name$")
MARCAS_RE = re.compile(r"[%<\[{]")
ESPACIOS_RAROS_RE = re.compile(r"[\t\n\r]")  # romperían el TSV del glosario

CATEGORIAS = [("perk", "perk"), ("backgrounds/", "trasfondo"), ("traits/", "rasgo"),
              ("injury", "lesion"), ("skills/", "habilidad"), ("items/", "objeto"),
              ("entity/", "entidad"), ("faction", "faccion"), ("scenarios/", "origen"),
              ("retinue", "seguidor"), ("contracts/", "contrato"), ("runes_", "objeto")]
# Listas de nombres y frases del base que no son terminología (sin `// context:`
# en base_es.nut, se reconocen por la ruta).
RUTAS_SIN_TERMINOS = ("character_names.nut", "world_location_names.nut",
                      "\\settlements\\", "\\enemies\\alp.nut")
GLOSARIO_BASE = LEGENDS / "glosario_base.tsv"
GLOSARIO_LEGENDS = LEGENDS / "glosario_legends.tsv"
COLUMNAS = ("en", "es", "categoria", "file", "nota")


@dataclass
class Termino:
    en: str
    es: str
    categoria: str
    file: str
    nota: str = ""


def es_termino(b):
    """Candidato a término: literal corto con mayúscula inicial y sin marcas."""
    return (bool(b.en) and len(b.en.split()) <= 4 and b.en[0].isupper()
            and not MARCAS_RE.search(b.en) and not ESPACIOS_RAROS_RE.search(b.en)
            and not is_rule_pair(b.texto))


def grupo(b):
    c = b.contexto or ""
    if LISTA_RE.search(c):
        return "lista"
    return "termino" if TERMINO_RE.search(c) else "resto"


CATEGORIAS_CONTEXTO = [("activesDefs", "habilidad"), ("effectsDefs", "efecto"),
                       ("traitDefs", "rasgo"), ("PerkName", "perk"), ("EntityType", "entidad"),
                       ("LegendArmorLayers", "objeto"), ("HuntingLoot", "objeto")]


def categoria(file, contexto=None):
    """Por el contexto si lo dice (las tablas *Defs de Legends viven en
    config/), y si no por la ruta."""
    por_contexto = next((cat for clave, cat in CATEGORIAS_CONTEXTO if clave in (contexto or "")), None)
    f = file.replace("\\", "/").lower()
    return por_contexto or next((cat for clave, cat in CATEGORIAS if clave in f), "general")


def escribir_glosario(path, terminos):
    filas = ["\t".join(COLUMNAS)]
    for t in sorted(terminos, key=lambda t: (t.categoria, t.en)):
        filas.append("\t".join(getattr(t, c) for c in COLUMNAS))
    escribir(path, "\n".join(filas) + "\n")


def leer_glosario(path):
    filas = path.read_text(encoding="utf-8").splitlines()[1:]
    return [Termino(*f.split("\t")) for f in filas if f]


def terminos_en(texto, glosario):
    """Términos del glosario presentes en `texto`, en orden de aparición.

    Distingue mayúsculas (en los tooltips de Legends los términos van
    capitalizados) y deja que un término largo tape a los cortos que contiene.
    """
    patron, por_en = _patron_glosario(tuple(t.en for t in glosario))
    vistos, res = set(), []
    for m in patron.finditer(texto):
        en = m.group(1)
        if en not in vistos:
            vistos.add(en)
            res.append(glosario[por_en[en]])
    return res


@functools.lru_cache(maxsize=8)
def _patron_glosario(ens):
    """Una alternancia del más largo al más corto: en cada posición casa el
    término más largo, y lo que tapa ya no lo ve uno más corto."""
    orden = sorted(set(ens), key=len, reverse=True)
    patron = re.compile(r"(?<![\w'])(%s)(?![\w'])" % "|".join(map(re.escape, orden)))
    return patron, {en: i for i, en in enumerate(ens)}


MITAD_DE_FRASE_RE = re.compile(r"(?<=[a-z0-9,] )([A-Z][\w']*(?: [A-Z][\w']*)*)")


MINUSCULA_RE = re.compile(r"\b[a-z][\w']*(?: [a-z][\w']*){0,3}")


def usos_a_mitad_de_frase(textos):
    """(mayúsculas, minúsculas): cuántas veces sale cada secuencia de hasta 4
    palabras capitalizada a mitad de frase, que es como el juego escribe sus
    términos ("gain 10 Fatigue"), y cuántas en minúscula."""
    mayus, minus = Counter(), Counter()
    for texto in textos:
        for patron, cuenta in ((MITAD_DE_FRASE_RE, mayus), (MINUSCULA_RE, minus)):
            for m in patron.finditer(texto):
                palabras = m.group(0).split()
                for i in range(len(palabras)):
                    for j in range(i + 1, min(len(palabras), i + 4) + 1):
                        cuenta[" ".join(palabras[i:j])] += 1
    return mayus, minus


def termino_util(t, usos):
    """Filtra del glosario base lo que despistaría al agente: fragmentos de
    nombres compuestos ("Ancient" -> "ancestral") y palabras corrientes, que
    el texto escribe más en minúscula que con mayúscula a mitad de frase
    ("The", y "Armor" -> "Armadura de trol", que solo vale para un objeto)."""
    if t.es[:1].islower():
        return False
    if t.categoria != "general" and " " in t.en:
        return True
    mayus, minus = usos
    # 1 de cada 4 basta: "Resolve" va 19 veces con mayúscula y 40 sin ella;
    # "Armor" 53 y 411, "The" 5 y 27.291.
    return mayus[t.en] >= 2 and 4 * mayus[t.en] >= minus[t.en.lower()]


def glosario_base():
    base = bloques(CORPUS.read_text(encoding="utf-8"))
    usos = usos_a_mitad_de_frase(b.en for b in base if b.en)
    vistos, res = set(), []
    for b in base:
        if (b.es and es_termino(b) and b.en not in vistos and not ESPACIOS_RAROS_RE.search(b.es)
                and not any(r in b.file for r in RUTAS_SIN_TERMINOS)):
            vistos.add(b.en)
            t = Termino(b.en, b.es, categoria(b.file), b.file)
            if termino_util(t, usos):
                res.append(t)
    escribir_glosario(GLOSARIO_BASE, res)
    return res


def terminos():
    base = leer_glosario(GLOSARIO_BASE)
    vistos, res = set(), []
    for b in bloques(CORPUS_LEGENDS.read_text(encoding="utf-8")):
        # Los títulos de pantalla de los eventos son prosa, no terminología.
        if (not b.es and es_termino(b) and grupo(b) == "termino" and b.en not in vistos
                and "\\events\\" not in b.file):
            vistos.add(b.en)
            contiene = [t.en for t in terminos_en(b.en, base)]
            nota = "contiene: " + "; ".join(contiene) if contiene else ""
            res.append(Termino(b.en, "", categoria(b.file, b.contexto), b.file, nota))
    escribir_glosario(GLOSARIO_LEGENDS, res)
    return res


def _arranque(en):
    return " ".join(en.lower().split()[:3])


def indice_base(pares):
    """Pares (en, es) del base agrupados por sus tres primeras palabras."""
    indice = {}
    for en, es in pares:
        indice.setdefault(_arranque(en), []).append((en, es))
    return indice


def pista_base(en, indice):
    """El texto del base que Legends retocó, si lo hay: mismo arranque y al
    menos un 75 % de parecido.

    shortcut: solo ve retoques que conservan las tres primeras palabras;
    ampliar si al traducir aparecen textos retocados sin pista.
    """
    if len(en) <= 20:
        return None
    candidatos = [(difflib.SequenceMatcher(None, en, b).ratio(), b, es)
                  for b, es in indice.get(_arranque(en), [])]
    mejor = max(candidatos, default=None)
    return (mejor[1], mejor[2]) if mejor and mejor[0] >= 0.75 else None


def partir_en_lotes(pendientes, max_entradas=150, max_palabras=6000):
    """Lotes por frontera de `// FILE:`; un fichero que solo ya pasa un límite
    se parte entre pares."""
    lotes_, actual, palabras = [], [], 0
    for _, grupo_file in groupby(pendientes, key=lambda b: b.file):
        grupo_file = list(grupo_file)
        p = sum(len(b.en.split()) for b in grupo_file)
        if actual and (len(actual) + len(grupo_file) > max_entradas or palabras + p > max_palabras):
            lotes_.append(actual)
            actual, palabras = [], 0
        for b in grupo_file:
            n = len(b.en.split())
            if actual and (len(actual) + 1 > max_entradas or palabras + n > max_palabras):
                lotes_.append(actual)
                actual, palabras = [], 0
            actual.append(b)
            palabras += n
    if actual:
        lotes_.append(actual)
    return lotes_


def literal(s):
    return '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def render_lote(n, etiqueta, lote, glosario, indice):
    """El lote como lo verá el agente: cabecera con los términos del glosario
    que aparecen en él y los pares tal cual están en el corpus, cada uno con
    su `// FILE:`, su `// context:` y, si retoca un texto del base, su pista."""
    texto_en = "\n".join(b.en for b in lote)
    lineas = ["// LOTE %04d" % n, "// Legends %s" % etiqueta,
              "// Instrucciones: es_pack/legends/BRIEF.md", "// GLOSARIO:"]
    for t in terminos_en(texto_en, glosario):
        lineas.append("// %s = %s" % (t.en, t.es or "(pendiente)"))
    file = None
    for b in lote:
        if b.file != file:
            file = b.file
            lineas.append("    // FILE: %s" % file)
        if b.contexto:
            lineas.append("    // context: %s" % b.contexto)
        pista = pista_base(b.en, indice)
        if pista:
            lineas.append("    // base: en=%s es=%s" % (literal(pista[0]), literal(pista[1])))
        lineas.append(b.texto)
    return "\n".join(lineas) + "\n"


def partir():
    if LOTES.exists() and any(LOTES.iterdir()):
        sys.exit("%s no está vacío: hay trabajo en curso; fusiona o bórralo antes de volver a partir" % LOTES)
    etiqueta = tomllib.loads(FUENTE_TOML.read_text(encoding="utf-8"))["etiqueta"]
    glosario = leer_glosario(GLOSARIO_LEGENDS) + leer_glosario(GLOSARIO_BASE)
    indice = indice_base((get_field(b, "en"), get_field(b, "es")) for b in load_blocks(CORPUS)
                         if get_field(b, "en") and get_field(b, "es"))
    pendientes = [b for b in bloques(CORPUS_LEGENDS.read_text(encoding="utf-8")) if not b.es]
    lotes_ = partir_en_lotes(pendientes)
    LOTES.mkdir(parents=True, exist_ok=True)
    pistas = 0
    for n, lote in enumerate(lotes_, start=1):
        texto = render_lote(n, etiqueta, lote, glosario, indice)
        pistas += texto.count("\n    // base: ")
        escribir(LOTES / ("%04d.nut" % n), texto)
        escribir(LOTES / ("%04d.orig.nut" % n), texto)
    tamanos = [len(l) for l in lotes_]
    palabras = [sum(len(b.en.split()) for b in l) for l in lotes_]
    print("lotes: %d" % len(lotes_))
    print("entradas por lote: media %d, máximo %d" % (sum(tamanos) / len(tamanos), max(tamanos)))
    print("palabras por lote: media %d, máximo %d" % (sum(palabras) / len(palabras), max(palabras)))
    print("pistas del base: %d" % pistas)


def desverbatim(codigo):
    """Pasa cada cadena verbatim de Squirrel (@"...", con "" por comilla y
    saltos de línea reales) a una cadena normal equivalente.

    shortcut: el extractor de Rosetta 0.5.0 no tokeniza @"..." y descarta el
    fichero entero (perk_strings.nut, runes_*.nut); quitar esto cuando
    upstream lo soporte.
    """
    out, i, n = [], 0, len(codigo)
    while i < n:
        c = codigo[i]
        if codigo.startswith("//", i) or codigo.startswith("#", i):
            fin = codigo.find("\n", i)
            fin = n if fin < 0 else fin
        elif codigo.startswith("/*", i):
            fin = codigo.find("*/", i + 2)
            fin = n if fin < 0 else fin + 2
        elif c in "\"'":
            fin = i + 1
            while fin < n and codigo[fin] != c:
                fin += 2 if codigo[fin] == "\\" else 1
            fin += 1
        elif codigo.startswith('@"', i):
            j, cuerpo = i + 2, []
            while j < n:
                if codigo[j] == '"':
                    if codigo.startswith('""', j):
                        cuerpo.append('"')
                        j += 2
                        continue
                    break
                cuerpo.append(codigo[j])
                j += 1
            texto = "".join(cuerpo).replace("\r\n", "\n")
            texto = (texto.replace("\\", "\\\\").replace('"', '\\"')
                     .replace("\n", "\\n").replace("\t", "\\t"))
            out.append('"%s"' % texto)
            i = j + 1
            continue
        else:
            fin = i + 1
        out.append(codigo[i:fin])
        i = fin
    return "".join(out)


def copia_extraible(origen, destino, rutas):
    """Copia los .nut de la fuente con las cadenas verbatim convertidas."""
    for ruta in rutas:
        for f in (origen / ruta).rglob("*.nut"):
            dest = destino / f.relative_to(origen)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(desverbatim(f.read_bytes().decode("utf-8")).encode("utf-8"))


def escribir(path, texto):
    path.write_bytes(texto.replace("\r\n", "\n").encode("utf-8"))


def git(*args):
    subprocess.run(["git", *args], check=True)


def extraer(forzar):
    if CORPUS_LEGENDS.exists() and not forzar:
        hechos = [b for b in bloques(CORPUS_LEGENDS.read_text(encoding="utf-8")) if b.es]
        if hechos:
            sys.exit("%s ya tiene %d pares traducidos; re-extraer los perdería (--forzar para hacerlo igualmente)"
                     % (CORPUS_LEGENDS.name, len(hechos)))

    fuente = tomllib.loads(FUENTE_TOML.read_text(encoding="utf-8"))
    if not FUENTE.exists():
        git("clone", "--depth", "1", "--branch", fuente["etiqueta"], "--filter=blob:none",
            "--sparse", fuente["repo"], str(FUENTE))
        git("-C", str(FUENTE), "sparse-checkout", "set", *fuente["rutas"])
    head = subprocess.run(["git", "-C", str(FUENTE), "rev-parse", "HEAD"],
                          check=True, capture_output=True, text=True).stdout.strip()
    if head != fuente["commit"]:
        sys.exit("la fuente está en %s y fuente.toml fija %s; fija el commit o borra %s"
                 % (head, fuente["commit"], FUENTE))

    # Se extrae desde dentro de la copia con "." para que los // FILE: queden
    # relativos (scripts\...), como en base_es.nut, y no con la ruta local.
    with tempfile.TemporaryDirectory() as tmp:
        copia_extraible(FUENTE, Path(tmp), fuente["rutas"])
        salida = subprocess.run(
            [sys.executable, str(ROSETTA_PY), ".", "-les", "--context", "-r", str(CORPUS)],
            cwd=tmp, capture_output=True, env={**os.environ, "PYTHONUTF8": "1"})
    sys.stderr.write(salida.stderr.decode("utf-8", "replace"))
    if salida.returncode:
        sys.exit("el extractor terminó con código %d" % salida.returncode)
    texto = salida.stdout.decode("utf-8").replace("\r\n", "\n")
    texto, n = CABECERA_MOD_RE.subn(
        'mod = {id = "%s", version = "%s"}' % (fuente["mod_id"], fuente["etiqueta"]), texto)
    assert n == 1, "la cabecera del extractor ha cambiado"

    total = len(bloques(texto))
    texto, cribados = cribar(texto, ens_base())
    # Con -r, pistas de código distintas confluyen en el mismo patrón del base
    # (hasta base_es.nut lo repite); esos caen en la criba. Lo que la fusión
    # necesita único es lo que queda.
    dups = duplicados(texto)
    if dups:
        print("\n".join(dups[:20]))
        sys.exit("%d `en` repetidos tras la criba; la fusión los necesita únicos" % len(dups))
    resto = bloques(texto)
    escribir(CORPUS_LEGENDS, texto)
    print("pares totales: %d" % total)
    print("cribados (en base_es): %d" % cribados)
    print("pendientes (es vacío): %d" % sum(1 for b in resto if not b.es))
    print("ya con es: %d" % sum(1 for b in resto if b.es))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["extraer"]:
        extraer(forzar="--forzar" in argv)
    elif argv[:1] == ["partir"]:
        partir()
    elif argv[:1] in (["glosario-base"], ["terminos"]):
        res = glosario_base() if argv[0] == "glosario-base" else terminos()
        print("términos: %d" % len(res))
        for cat, n in Counter(t.categoria for t in res).most_common():
            print("  %-10s %5d" % (cat, n))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
