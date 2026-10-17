"""Censo de homógrafos de m.Name para los pares por id de Rosetta 0.5.0.

El problema que resuelve: hasta la 0.5.0, getName de objetos, habilidades y
entidades no pasaba id, así que un mismo literal inglés usado por dos clases
distintas sólo podía tener UNA traducción (el par literal), y cada homógrafo se
resolvía dando el valor al uso visible y sacrificando el otro. La 0.5.0 pasa
`<ruta del script>.Name` como id y `translate()` mira ese mapa antes que el
literal, o sea que el uso sacrificado se puede recuperar par a par sin tocar el
par literal, que sigue sirviendo a los consumidores sin id (tablas de config,
concatenaciones).

Qué hace: recorre los árboles de comparación (el inglés y el de la traducción
de referencia, las mismas rutas fijas que gt_align.py), saca los `m.Name` de
cada fichero de los árboles con conducto de id (items, skills, entity), los
empareja POSICIONALMENTE con los del fichero gemelo de la referencia (misma
ruta, mismo orden; si los recuentos difieren el fichero queda AMBIGUO y no se
propone nada), y compara el valor de la referencia con el que hoy da nuestro
par literal del corpus.

La clasificación, y su porqué:

- `cubierto`: la referencia coincide con el corpus (plegando tildes: una
  diferencia sólo de acentuación es curación nuestra y no discrepancia). El
  par literal ya sirve a ese fichero y no hace falta id.
- `candidato`: el literal aparece en VARIOS ficheros del ámbito y para éste la
  referencia da otro valor que el corpus. Es el uso sacrificado con conducto:
  un par `{id = "<ruta>.Name", es = "<valor>"}` lo recupera. El valor viene de
  la referencia, o sea SIN censar: se aplica con revisión, no a granel.
- `discrepancia-solitaria`: el literal sólo aparece en un fichero y aun así la
  referencia difiere del corpus. Eso es curación nuestra (el par se alineó con
  ese mismo fichero y se mejoró después): NO se toca, se lista para saberlo.
  Es la lección del git log -S: ante un valor que se aparta, historial antes
  que corrección.
- `sin-par`: el literal no está en el corpus. Informativo.

Lo que este censo NO propone: voltear el par literal para dar su valor al uso
sin conducto (el caso Dagger/"Último Beso", donde el otro lado es una lista de
config sin id). Ese volteo envenenaría a cualquier consumidor sin id del mismo
literal (p. ej. las tablas Const que hooks.nut traduce en el sitio), así que
esos usos siguen esperando a la vía de los nombres compuestos (issue #6).

Uso:
    PYTHONUTF8=1 uv run python es_pack/tools/ids_census.py
    PYTHONUTF8=1 uv run python es_pack/tools/ids_census.py --tsv

Con --tsv vuelca el detalle a es_pack/build/ids_census.tsv (build no se
versiona). Sin él imprime el resumen y los candidatos.
"""
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
from rutas import ARBOLES  # noqa: E402  ver rutas.py
EN = ARBOLES / "original_current"
FAN = ARBOLES / "spanish_tr"
CORPUS = REPO / "es_pack" / "corpus" / "base_es.nut"

# Los árboles con conducto de id en la 0.5.0: getName va con makeGetter("Name")
# en items, skills, actores y entidades de mundo (rosetta/hooks.nut). Los
# escenarios ya iban por id desde antes y sus pares están alineados; config no
# tiene conducto.
AMBITO = ["scripts/items", "scripts/skills", "scripts/entity"]

NAME_RE = re.compile(r'\bm\.Name\s*=\s*"((?:[^"\\]|\\.)*)"')
PAR_RE = re.compile(r'\ben\s*=\s*"((?:[^"\\]|\\.)*)"\s*\n\s*es\s*=\s*"((?:[^"\\]|\\.)*)"')


def plegar(texto):
    """Sin tildes, conservando la caja: una diferencia sólo de acentuación es
    curación nuestra, no discrepancia con la referencia."""
    return "".join(c for c in unicodedata.normalize("NFD", texto)
                   if unicodedata.category(c) != "Mn")


def desescapa(texto):
    """El árbol decompilado escapa comillas simples (\\') que el corpus guarda
    sin escapar; sin normalizar, cada nombre con posesivo sale como sin-par."""
    return texto.replace("\\'", "'").replace('\\"', '"')


def carga_corpus():
    pares = {}
    for m in PAR_RE.finditer(CORPUS.read_text(encoding="utf-8")):
        pares.setdefault(desescapa(m.group(1)), desescapa(m.group(2)))
    return pares


def nombres_de(ruta):
    try:
        texto = ruta.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return [desescapa(n) for n in NAME_RE.findall(texto)]


def censa():
    corpus = carga_corpus()
    usos = []          # (relpath sin .nut, en, fan_es | None si ambiguo)
    ambiguos = []
    sin_gemelo = []
    for raiz in AMBITO:
        for f in sorted((EN / raiz).rglob("*.nut")):
            en_names = nombres_de(f)
            if not en_names:
                continue
            rel = f.relative_to(EN).as_posix()[:-len(".nut")]
            fan_names = nombres_de(FAN / f.relative_to(EN))
            if fan_names is None:
                sin_gemelo.append(rel)
                fan_names = []
            if len(fan_names) != len(en_names):
                ambiguos.append((rel, len(en_names), len(fan_names)))
                fan_names = [None] * len(en_names)
            for en_lit, fan_es in zip(en_names, fan_names):
                if en_lit:  # m.Name = "" es un nombre interno, no un texto
                    usos.append((rel, en_lit, fan_es))

    por_literal = defaultdict(list)
    for rel, en_lit, fan_es in usos:
        por_literal[en_lit].append((rel, fan_es))

    filas = []  # (clase, en, rel, fan_es, corpus_es)
    for en_lit, sitios in sorted(por_literal.items()):
        corpus_es = corpus.get(en_lit)
        homografo = len({rel for rel, _ in sitios}) > 1
        for rel, fan_es in sitios:
            if corpus_es is None:
                clase = "sin-par"
            elif fan_es is None:
                clase = "ambiguo"
            elif plegar(fan_es) == plegar(corpus_es):
                clase = "cubierto"
            elif fan_es == en_lit:
                # La referencia lo dejó en inglés: no aporta valor para este
                # uso, y el par literal ya le da el castellano que tenemos.
                clase = "ref-sin-traducir"
            elif plegar(fan_es).lower() == plegar(corpus_es).lower():
                # Solo difiere la caja: curación nuestra, no uso sacrificado.
                clase = "cubierto"
            elif homografo:
                clase = "candidato"
            else:
                clase = "discrepancia-solitaria"
            filas.append((clase, en_lit, rel, fan_es or "", corpus_es or ""))
    return filas, ambiguos, sin_gemelo


def main(argv):
    filas, ambiguos, sin_gemelo = censa()
    cuentas = defaultdict(int)
    for clase, *_ in filas:
        cuentas[clase] += 1
    print("usos de m.Name en el ámbito:", len(filas))
    for clase in ("cubierto", "candidato", "discrepancia-solitaria",
                  "ref-sin-traducir", "sin-par", "ambiguo"):
        print("  %-24s %d" % (clase, cuentas[clase]))
    if ambiguos:
        print("ficheros ambiguos (recuentos en/fan distintos):")
        for rel, ne, nf in ambiguos:
            print("  %s (%d vs %d)" % (rel, ne, nf))
    if sin_gemelo:
        print("sin gemelo en la referencia: %d" % len(sin_gemelo))

    if "--tsv" in argv:
        salida = REPO / "es_pack" / "build" / "ids_census.tsv"
        salida.parent.mkdir(parents=True, exist_ok=True)
        with open(salida, "w", encoding="utf-8", newline="") as fd:
            fd.write("clase\ten\tfichero\treferencia\tcorpus\n")
            for fila in filas:
                fd.write("\t".join(fila) + "\n")
        print("detalle:", salida)
    else:
        print()
        for clase, en_lit, rel, fan_es, corpus_es in filas:
            if clase == "candidato":
                print("CANDIDATO  %-28s %s\n           ref: %-30s corpus: %s"
                      % (en_lit, rel, fan_es, corpus_es))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
