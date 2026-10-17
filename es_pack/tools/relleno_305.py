"""Relleno de los pares con es vacío desde la fuente 3.0.5 de elgranfoca.

Decisión del propietario del 25/08/2026: los vacíos se rellenan ANTES de la v1
con la traducción 3.0.5 (02/08/2026), SOLO los vacíos y sin pisar jamás un par
curado. El árbol 3.0.5 se descompila con el kit de bbros (massdecompile.ps1)
a `spanish_305`, hermano de `spanish_tr`, y este script alinea igual que
`gt_align.py`: mismos ficheros, mismos literales en el mismo orden, difflib
da anclas y huecos, y solo se propone dentro de anclas y de huecos del mismo
tamaño. Lo ambiguo no se propone: resolver por descarte ya demostró ser
conjetura.

Guardas, todas deliberadas:

- Solo pares cuyo es es exactamente "" y cuyo en no lleva placeholders <> (los
  patrones vacíos son trabajo manual, no de alineamiento).
- Si el mismo en ya tiene es no vacío en otra entrada del corpus, se omite: el
  build deduplica por en y esa entrada ya está servida; rellenarla con otro
  valor solo podría crear variantes.
- Si la fuente da valores distintos para el mismo en en ficheros distintos, se
  omite y se informa: conflicto, no evidencia.
- Si el valor de la fuente es igual al inglés, se omite: no es traducción.

Uso:
    PYTHONUTF8=1 uv run python es_pack/tools/relleno_305.py            # propone, escribe build/relleno_305.tsv
    PYTHONUTF8=1 uv run python es_pack/tools/relleno_305.py --aplicar --prefijo scripts/events
                                                                       # aplica al corpus solo esa sección
"""
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
from rutas import ARBOLES  # noqa: E402  ver rutas.py
EN = ARBOLES / "original_current"
NUEVA = ARBOLES / "spanish_305"
CORPUS = REPO / "es_pack" / "corpus" / "base_es.nut"
SALIDA = REPO / "es_pack" / "build" / "relleno_305.tsv"

LITERAL_RE = re.compile(r'"((?:[^"\\\n]|\\.)*)"')
EN_LINEA_RE = re.compile(r'^(\s*)en = "((?:[^"\\]|\\.)*)"\s*$')
ES_VACIO_RE = re.compile(r'^(\s*)es = ""\s*$')
ES_LINEA_RE = re.compile(r'^(\s*)es = "((?:[^"\\]|\\.)*)"\s*$')
FILE_RE = re.compile(r'^\s*// FILE: (?:.*?[\\/]original_current[\\/])?(.*)$')


def alinea(a, b):
    pares = []
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
            pares += list(zip(range(i1, i2), range(j1, j2)))
    return pares


def carga_corpus_lineas():
    return CORPUS.read_text(encoding="utf-8").splitlines(keepends=True)


def recorre(lineas):
    """Genera (indice_linea_es, fichero_rel, en) por cada par con es vacío."""
    fichero = None
    for n, linea in enumerate(lineas):
        m = FILE_RE.match(linea)
        if m:
            fichero = m.group(1).replace("\\", "/")
            continue
        m = EN_LINEA_RE.match(linea)
        if m and n + 1 < len(lineas) and ES_VACIO_RE.match(lineas[n + 1]):
            yield n + 1, fichero, m.group(2)


def valores_no_vacios(lineas):
    """Todos los en que ya tienen algún es no vacío en el corpus."""
    servidos = set()
    for n, linea in enumerate(lineas):
        m = EN_LINEA_RE.match(linea)
        if m and n + 1 < len(lineas):
            m2 = ES_LINEA_RE.match(lineas[n + 1])
            if m2 and m2.group(2) != "":
                servidos.add(m.group(2))
    return servidos


def propone():
    lineas = carga_corpus_lineas()
    servidos = valores_no_vacios(lineas)
    vacios = list(recorre(lineas))
    print(f"pares con es vacío: {len(vacios)}")

    con_hueco = [(n, f, en) for n, f, en in vacios
                 if "<" not in en and ">" not in en and en not in servidos]
    omitidos_patron = sum(1 for _, _, en in vacios if "<" in en or ">" in en)
    omitidos_servidos = len(vacios) - len(con_hueco) - omitidos_patron
    print(f"  con placeholders, fuera: {omitidos_patron}")
    print(f"  ya servidos por otra entrada, fuera: {omitidos_servidos}")
    print(f"  candidatos de verdad: {len(con_hueco)}")

    por_fichero = {}
    for n, f, en in con_hueco:
        por_fichero.setdefault(f, []).append(en)

    propuestas = {}      # en -> valor
    conflictos = {}      # en -> {valores}
    sin_gemelo = sin_ancla = iguales = 0
    for rel, enes in sorted(por_fichero.items()):
        if rel is None:
            continue
        f_en, f_es = EN / rel, NUEVA / rel
        if not f_en.exists() or not f_es.exists():
            sin_gemelo += len(enes)
            continue
        a = LITERAL_RE.findall(f_en.read_text(encoding="utf-8", errors="replace"))
        b = LITERAL_RE.findall(f_es.read_text(encoding="utf-8", errors="replace"))
        mapa = {}
        for i, j in alinea(a, b):
            mapa.setdefault(a[i], set()).add(b[j])
        for en in enes:
            valores = mapa.get(en)
            if not valores:
                sin_ancla += 1
                continue
            if len(valores) > 1:
                conflictos.setdefault(en, set()).update(valores)
                continue
            valor = next(iter(valores))
            if valor == en or valor == "":
                iguales += 1
                continue
            if en in propuestas and propuestas[en] != valor:
                conflictos.setdefault(en, set()).update({propuestas[en], valor})
                continue
            propuestas[en] = valor

    for en in conflictos:
        propuestas.pop(en, None)

    print(f"  sin fichero gemelo en 3.0.5: {sin_gemelo}")
    print(f"  sin alineamiento para su en: {sin_ancla}")
    print(f"  la fuente los deja en inglés: {iguales}")
    print(f"  conflictos entre ficheros, fuera: {len(conflictos)}")
    print(f"PROPUESTAS: {len(propuestas)}")

    SALIDA.parent.mkdir(exist_ok=True)
    with SALIDA.open("w", encoding="utf-8", newline="") as fh:
        for en, valor in sorted(propuestas.items()):
            fh.write(f"{en}\t{valor}\n")
    print(f"escritas en {SALIDA.relative_to(REPO)}")
    if conflictos:
        print("conflictos (los decide el propietario):")
        for en, vs in sorted(conflictos.items())[:20]:
            print(f"  {en[:60]!r}: " + " | ".join(repr(v[:40]) for v in sorted(vs)))
    return propuestas


def aplica(prefijo):
    propuestas = {}
    for linea in SALIDA.read_text(encoding="utf-8").splitlines():
        en, _, valor = linea.partition("\t")
        if valor:
            propuestas[en] = valor
    lineas = carga_corpus_lineas()
    aplicadas = 0
    for n_es, rel, en in list(recorre(lineas)):
        if rel is None or not rel.startswith(prefijo):
            continue
        valor = propuestas.get(en)
        if not valor:
            continue
        sangria = ES_VACIO_RE.match(lineas[n_es]).group(1)
        fin = "\r\n" if lineas[n_es].endswith("\r\n") else "\n"
        lineas[n_es] = f'{sangria}es = "{valor}"{fin}'
        aplicadas += 1
    CORPUS.write_text("".join(lineas), encoding="utf-8", newline="")
    print(f"aplicadas {aplicadas} bajo {prefijo!r}")


if __name__ == "__main__":
    if "--aplicar" in sys.argv:
        i = sys.argv.index("--prefijo") if "--prefijo" in sys.argv else None
        prefijo = sys.argv[i + 1] if i is not None else ""
        aplica(prefijo)
    else:
        propone()
