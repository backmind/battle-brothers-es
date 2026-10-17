"""Detector de erratas que no necesita diccionario.

El corpus es su propio diccionario: son 15.000 pares y millon y medio de
caracteres de castellano, asi que una palabra correcta aparece muchas veces y
una errata aparece una sola. La regla es esa: palabra que sale una o dos veces
y que se parece (una edicion) a otra que sale muchas, es candidata a errata.

Asi salieron "suficietnes" por suficientes, "siemrpe" por siempre, "hueargo"
por huargo y "Danzarínes" por Danzarines, que ningun barrido anterior veia
porque los checks miraban clases concretas (tildes, duplicados, tokens) y no
el lexico.

El indice es el truco de SymSpell: de cada palabra frecuente se guardan sus
variantes con una letra menos; una palabra rara casa con una frecuente si
comparten alguna de esas variantes.

Uso:
    PYTHONUTF8=1 uv run python es_pack/tools/erratas.py [minimo_frecuente]
"""
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CORPUS = REPO / "es_pack" / "corpus" / "base_es.nut"

CAMPO = re.compile(r'^\s*(es|n1|n2|n5)\s*=\s*"(.*)"\s*$')
# fuera etiquetas, marcadores, imagenes y placeholders
LIMPIA = re.compile(r"\[[^\]]*\]|<[^>]*>|%\w+%|\\x[0-9a-f]{2}|\\n|&\w+;")
PALABRA = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{4,}")


def deleciones(p):
    return {p[:i] + p[i + 1:] for i in range(len(p))}


def main():
    verbose = "-v" in sys.argv
    minimo = next((int(a) for a in sys.argv[1:] if a.isdigit()), 8)
    cuenta = Counter()
    donde = {}
    for i, linea in enumerate(CORPUS.read_text(encoding="utf-8").split("\n")):
        m = CAMPO.match(linea)
        if not m:
            continue
        for p in PALABRA.findall(LIMPIA.sub(" ", m.group(2))):
            cuenta[p] += 1
            donde.setdefault(p, i + 1)

    print(f"palabras distintas en el lado castellano: {len(cuenta)}")
    frecuentes = {p for p, n in cuenta.items() if n >= minimo}
    raras = [p for p, n in cuenta.items() if n <= 2 and len(p) >= 5]
    print(f"   frecuentes (>= {minimo}): {len(frecuentes)}   raras (<= 2): {len(raras)}")

    # Solo dos operaciones, que son las que hace un dedo y no hace la
    # morfologia: intercambiar dos letras contiguas, y doblar o colar una
    # letra. Con la distancia de edicion a secas esto daba 4425 candidatas,
    # casi todas flexiones legitimas ("preparando" contra "preparado").
    porbajo = {p.lower(): p for p in frecuentes}

    def transpuestas(b):
        return {b[:i] + b[i + 1] + b[i] + b[i + 2:] for i in range(len(b) - 1)}

    # Un diccionario castellano, si esta disponible, como ultimo filtro: si la
    # palabra rara EXISTE, no es errata aunque se parezca a otra ("preparando"
    # frente a "preparado"). El diccionario solo se usa para descartar, nunca
    # para acusar, que es donde falla: su lista es corta y no trae flexiones.
    conocidas = None
    try:
        from spellchecker import SpellChecker
        conocidas = SpellChecker(language="es").word_frequency.dictionary
        print(f"   filtro de diccionario activo ({len(conocidas)} palabras)")
    except ImportError:
        print("   sin diccionario (uv run --with pyspellchecker para afinar)")

    hallazgos = []
    for r in raras:
        b = r.lower()
        if conocidas is not None and b in conocidas:
            continue
        cands = {porbajo[t] for t in transpuestas(b) if t in porbajo}
        op = "cambiadas" if cands else ""
        for d in deleciones(b):          # sobra una letra en la rara
            if d not in porbajo:
                continue
            # si la letra de mas esta al final es flexion, no errata
            i = next((k for k in range(min(len(b), len(d))) if b[k] != d[k]), len(d))
            if i >= len(b) - 1:
                continue
            cands.add(porbajo[d])
            op = op or "letra de mas"
        if cands:
            hallazgos.append((r, cuenta[r], sorted(cands, key=lambda c: -cuenta[c])[:3], donde[r], op))

    def pelada(s):
        return "".join(c for c in unicodedata.normalize("NFD", s.lower())
                       if unicodedata.category(c) != "Mn")

    # Clase aparte y con su propia busqueda: la misma palabra escrita con y sin
    # tilde. No la encuentran las operaciones de arriba, porque cambiar i por i
    # acentuada es una sustitucion, no una transposicion ni una letra de mas.
    # Asi salio "cosas como aqui" en el tooltip del pueblo.
    porforma = defaultdict(set)
    for p in cuenta:
        porforma[pelada(p)].add(p)
    acentos = []
    for forma, variantes in porforma.items():
        if len(variantes) < 2:
            continue
        conacento = {v for v in variantes if v.lower() != pelada(v)}
        sinacento = variantes - conacento
        if not conacento or not sinacento:
            continue
        mejor = max(conacento, key=lambda v: cuenta[v])
        for v in sinacento:
            # solo si la forma con tilde manda con claridad
            if cuenta[mejor] >= max(4, cuenta[v] * 3):
                acentos.append((v, cuenta[v], [mejor], donde[v], "tilde"))

    tildes = acentos
    resto = hallazgos
    # las letras intercambiadas son la clase limpia: la morfologia del
    # castellano no intercambia letras contiguas, un dedo si
    cambiadas = [h for h in resto if h[4] == "cambiadas"]
    demas = [h for h in resto if h[4] != "cambiadas"]

    def volcar(titulo, lista):
        print(f"\n=== {titulo} ({len(lista)}) ===")
        for r, n, cands, ln, _op in sorted(lista, key=lambda h: h[3]):
            print(f"  l{ln:<6} {r!r} x{n}   ->  " + ", ".join(f"{c} x{cuenta[c]}" for c in cands))

    volcar("LETRAS INTERCAMBIADAS (la clase limpia)", cambiadas)
    volcar("SOLO LA TILDE", tildes)
    if verbose:
        volcar("UNA LETRA DE MAS (ruidosa: mira antes de tocar)", demas)
    else:
        print(f"\n=== UNA LETRA DE MAS: {len(demas)} (con -v se listan; son ruidosas) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
