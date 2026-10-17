"""Detector de mayusculas calcadas del ingles.

El ingles titula: "Orc Warrior", "Blade Dancer", "Beasts of Winter". El
castellano no: solo la inicial del rotulo, y dentro todo minuscula salvo
nombre propio. Traducir palabra a palabra arrastra la mayuscula y deja
"Guerreros Orcos", "Danzarines de Cuchillas", "Bestias del Invierno".

El truco es el mismo que usa erratas.py: el corpus es su propio diccionario.
Si "orcos" aparece en minuscula cincuenta veces, entonces "Orcos" a mitad de
frase es un calco, no un nombre propio. Y al reves, "Davkul" o "Kayce" no
aparecen nunca en minuscula, asi que nunca se acusan.

Se miran solo las palabras que NO abren frase: se descarta la primera del
valor y toda la que venga detras de punto, dos puntos, comillas, apertura de
parentesis, signo de interrogacion o exclamacion, imagen o salto de linea.

El informe separa dos poblaciones porque no se juzgan igual:

  ROTULOS   valores cortos, que son nombres de unidad, de objeto y de
            habilidad. Aqui una mayuscula interior es casi siempre calco, y
            es la lista sobre la que se actua.
  PROSA     descripciones y eventos, donde abundan los nombres propios
            legitimos ("el Joven Anselm", "el Rey Nomada"). Solo se cuenta.

Uso:
    PYTHONUTF8=1 uv run python es_pack/tools/mayusculas.py [-v] [minimo]
"""
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CORPUS = REPO / "es_pack" / "corpus" / "base_es.nut"

CAMPO = re.compile(r'^\s*(es|n1|n2|n5)\s*=\s*"(.*)"\s*$')
# lo que abre parrafo se sustituye por el salto, que si abre frase
PARRAFO = re.compile(r"\[img[^\]]*\][^\[]*\[/img\w*\]|\[/?p[^\]]*\]|\\n")
# el resto de etiquetas y marcadores no abre nada: hueco simple
HUECO = re.compile(r"\[[^\]]*\]|<[^>]*>|%\w+%|\\x[0-9a-f]{2}|&\w+;|\\\\")
TOKEN = re.compile(r"([A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{2,})")
ABRE = set(".:!?¿¡\"'([{-–—/|\n")
CORTO = 9   # palabras: por encima de esto es prosa, no rotulo


def abre_frase(texto, ini):
    i = ini - 1
    while i >= 0 and texto[i] in " \t":
        i -= 1
    return i < 0 or texto[i] in ABRE


def main():
    verbose = "-v" in sys.argv
    minimo = next((int(a) for a in sys.argv[1:] if a.isdigit()), 3)

    valores = []
    for i, linea in enumerate(CORPUS.read_text(encoding="utf-8").split("\n")):
        m = CAMPO.match(linea)
        if m:
            v = HUECO.sub(" ", PARRAFO.sub("\n", m.group(2)))
            valores.append((i + 1, v))

    minus = Counter()
    for _ln, v in valores:
        for m in TOKEN.finditer(v):
            if m.group(1).islower():
                minus[m.group(1)] += 1

    print(f"valores en castellano: {len(valores)}")
    print(f"palabras vistas en minuscula: {len(minus)}")

    rotulos, prosa = defaultdict(list), Counter()
    for ln, v in valores:
        corto = len(v.split()) <= CORTO
        for m in TOKEN.finditer(v):
            w = m.group(1)
            if w[0].islower() or w.upper() == w:      # ni minuscula ni SIGLA
                continue
            if abre_frase(v, m.start()):
                continue
            n = minus.get(w.lower(), 0)
            if n < minimo:                             # nombre propio: nunca en minuscula
                continue
            if corto:
                rotulos[w].append((ln, n, v))
            else:
                prosa[w] += 1

    tot = sum(len(v) for v in rotulos.values())
    print(f"\n=== ROTULOS: {tot} apariciones en {len(rotulos)} palabras ===\n")
    for w in sorted(rotulos, key=lambda x: (-len(rotulos[x]), x)):
        casos = rotulos[w]
        print(f"  {w!r} x{len(casos)}   (en minuscula {casos[0][1]} veces)")
        for ln, _n, v in (casos if verbose else casos[:4]):
            print(f"       l{ln:<7} {v.strip()}")
    print(f"\n=== PROSA: {sum(prosa.values())} apariciones en {len(prosa)} palabras "
          f"(nombres propios legitimos mezclados; solo se cuenta) ===")
    for w, n in prosa.most_common(25):
        print(f"  {w!r} x{n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
