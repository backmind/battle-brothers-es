"""Auditoría anclada de todo el corpus contra el árbol de enero.

Idea: los ficheros del árbol fan son los MISMOS ficheros del juego traducidos,
así que sus literales van en el mismo orden. Alineando las dos secuencias de
literales se obtiene, para cada cadena inglesa, qué puso el traductor en esa
posición exacta. Eso es verdad de terreno de ALINEAMIENTO, no de calidad.

La alineación se hace con difflib, que da bloques iguales (anclas) y bloques
sustituidos (huecos). Dentro de un hueco del mismo tamaño en los dos lados, la
correspondencia es uno a uno; si los tamaños difieren, es AMBIGUA y no se
propone nada, porque resolver un hueco ambiguo por descarte ya demostró ser
conjetura, no prueba.

La señal de alto valor no es "difiere de la fuente", que casi siempre significa
que nosotros lo mejoramos, sino DESPLAZADO: nuestro valor para una entrada es
exactamente el que la fuente da a OTRA entrada del mismo fichero. Esa es la
firma del corrimiento, y es la que encontró Lindwurms llamados "Trols".

Las comparaciones PLIEGAN los acentos, por dos motivos. Uno, que un
desplazamiento con una tilde de diferencia se veía como simple diferencia y se
escapaba. Y dos, que así las diferencias que son sólo de acentuación salen en su
propio recuento en vez de inflar el de diferencias reales: son unas cien, y en
casi todas la tilde la llevamos nosotros y la fuente no.

Uso:
    PYTHONUTF8=1 uv run python es_pack/tools/gt_align.py [--todos]
"""
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
from rutas import ARBOLES  # noqa: E402  ver rutas.py
EN = ARBOLES / "original_current"
FAN = ARBOLES / "spanish_tr"
CORPUS = REPO / "es_pack" / "corpus" / "base_es.nut"

LITERAL_RE = re.compile(r'"((?:[^"\\\n]|\\.)*)"')
PAR_RE = re.compile(r'\ben\s*=\s*"((?:[^"\\]|\\.)*)"\s*\n\s*es\s*=\s*"((?:[^"\\]|\\.)*)"')


def plegar(texto):
    """Quita tildes y virgulillas, conservando la caja.

    Se compara así para que una tilde de diferencia no esconda un
    desplazamiento: nuestro valor puede ser el que la fuente da a otra entrada y
    llevar además una tilde perdida, y sin plegar los dos hechos se tapan
    mutuamente.
    """
    return "".join(c for c in unicodedata.normalize("NFD", texto)
                   if unicodedata.category(c) != "Mn")


def carga_corpus():
    pares = {}
    for m in PAR_RE.finditer(CORPUS.read_text(encoding="utf-8")):
        pares.setdefault(m.group(1), m.group(2))
    return pares


def alinea(a, b):
    """Devuelve [(i, j)] emparejando literal i de `a` con literal j de `b`.

    Sólo empareja dentro de bloques iguales (anclas) y dentro de bloques
    sustituidos del MISMO tamaño. Los huecos de tamaño distinto se omiten.
    """
    pares, ambiguos = [], 0
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            pares += [(i, j) for i, j in zip(range(i1, i2), range(j1, j2))]
        elif tag == "replace":
            if i2 - i1 == j2 - j1:
                pares += [(i, j) for i, j in zip(range(i1, i2), range(j1, j2))]
            else:
                ambiguos += i2 - i1
    return pares, ambiguos


def main():
    todos = "--todos" in sys.argv
    pares = carga_corpus()
    print(f"pares del corpus: {len(pares)}")

    n_fich = n_sin_gemelo = ambiguos_tot = 0
    coincide = distinto = 0
    desplazados, solo_acentos = [], []
    vistos = set()

    for f in sorted(EN.rglob("*.nut")):
        rel = f.relative_to(EN).as_posix()
        gemelo = FAN / rel
        if not gemelo.exists():
            n_sin_gemelo += 1
            continue
        n_fich += 1
        try:
            a = LITERAL_RE.findall(f.read_text(encoding="utf-8", errors="replace"))
            b = LITERAL_RE.findall(gemelo.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        emparejados, amb = alinea(a, b)
        ambiguos_tot += amb
        # de qué otras posiciones dispone este fichero, para detectar
        # desplazamiento. Se indexa por la forma plegada para que una tilde de
        # diferencia no esconda el desplazamiento.
        fan_por_valor = {}
        for i, j in emparejados:
            fan_por_valor.setdefault(plegar(b[j]), []).append(i)

        for i, j in emparejados:
            en, gt = a[i], b[j]
            es = pares.get(en)
            if not es or (en, rel) in vistos:
                continue
            vistos.add((en, rel))
            if es == gt:
                coincide += 1
                continue
            if plegar(es) == plegar(gt):
                solo_acentos.append((rel, en, es, gt))
                continue
            distinto += 1
            duenos = [k for k in fan_por_valor.get(plegar(es), []) if a[k] != en]
            if duenos:
                desplazados.append((rel, en, es, gt, a[duenos[0]]))

    print(f"ficheros con gemelo en la fuente: {n_fich} (sin gemelo: {n_sin_gemelo})")
    print(f"literales en huecos ambiguos, omitidos: {ambiguos_tot}")
    print()
    print(f"cadenas alineadas y presentes en el corpus:")
    print(f"   coinciden con la fuente:  {coincide}")
    print(f"   sólo difieren en acentos: {len(solo_acentos)}")
    print(f"   difieren de verdad:       {distinto}")
    print(f"   de las que DESPLAZADAS:   {len(desplazados)}")
    print()
    if solo_acentos:
        print("SÓLO ACENTOS (una de las dos lleva una tilde que la otra no):")
        for rel, en, es, gt in (solo_acentos if todos else solo_acentos[:15]):
            print(f"  {en[:34]:36s} nuestro: {es[:30]:32s} fuente: {gt[:30]}")
        if not todos and len(solo_acentos) > 15:
            print(f"  ... y {len(solo_acentos) - 15} más (usa --todos)")
        print()
    print("DESPLAZADAS (nuestro valor es el que la fuente da a otra entrada del mismo fichero):")
    print(f"{'fichero':44s} {'en':22s} {'nuestro es':24s} {'la fuente pone':24s} y ese valor es de")
    print("-" * 150)
    for rel, en, es, gt, otro in (desplazados if todos else desplazados[:60]):
        print(f"{rel[-43:]:44s} {en[:21]:22s} {es[:23]:24s} {gt[:23]:24s} {otro[:28]}")
    if not todos and len(desplazados) > 60:
        print(f"... y {len(desplazados) - 60} más (usa --todos)")


if __name__ == "__main__":
    main()
