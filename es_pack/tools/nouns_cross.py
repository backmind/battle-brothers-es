"""Detector determinista de desplazamiento en tablas de nombres.

Los embeddings solo cazan el desplazamiento cuando las dos entradas son
semanticamente lejanas. Entre sinonimos ("Skullsmasher's Grotto" con
"Guarida de los Rompe Cabezas") la similitud sale alta y el error pasa.

Este detector no mira semantica: mira el sustantivo de tipo. Si el ingles
dice Grotto y el espaniol dice Guarida (que es Den), el par esta cruzado,
por muy parecido que sea el resto. Solo avisa cuando el espaniol carece del
termino que le toca Y ademas contiene el de otro tipo distinto: asi un
"Cueva asquerosa" traducido con libertad no genera ruido.

Uso:
    PYTHONUTF8=1 uv run python es_pack/tools/nouns_cross.py [ruta_corpus]
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CORPUS = Path(sys.argv[1]) if len(sys.argv) > 1 else (
    REPO / "es_pack" / "corpus" / "base_es.nut")

# tipo ingles -> terminos espanioles admisibles
TIPOS = {
    "cavern": ("caverna",),
    "cave": ("cueva", "caverna"),
    "grotto": ("gruta", "grruta"),
    "den": ("guarida", "madriguera"),
    "lair": ("guarida", "cubil"),
    "hideout": ("escondite", "guarida"),
    "camp": ("campamento", "campo"),
    "outpost": ("puesto",),
    "ruins": ("ruinas",),
    "tower": ("torre", "atalaya"),
    "watchtower": ("atalaya", "torre"),
    "keep": ("torreón", "fortaleza"),
    "fort": ("fuerte", "fortaleza"),
    "stronghold": ("bastión", "fortaleza"),
    "village": ("aldea",),
    "hamlet": ("aldea", "caserío"),
    "city": ("ciudad",),
    "town": ("ciudad", "villa"),
    "bridge": ("puente",),
    "mill": ("molino",),
    "mine": ("mina",),
    "quarry": ("cantera",),
    "hut": ("cabaña", "choza"),
    "huts": ("cabañas", "chozas"),
    "shack": ("cabaña", "choza"),
    "shacks": ("cabañas", "chozas"),
    "hovel": ("tugurio", "chabola"),
    "hovels": ("tugurios", "chabolas"),
    "tent": ("tienda", "toldo"),
    "tents": ("tiendas", "toldos"),
    "graveyard": ("cementerio",),
    "crypt": ("cripta",),
    "barrow": ("túmulo",),
    "tomb": ("tumba", "sepulcro"),
    "swamp": ("pantano", "ciénaga"),
    "bog": ("ciénaga", "pantano"),
    "mire": ("ciénaga", "lodazal"),
    "forest": ("bosque",),
    "woods": ("bosque",),
    "grove": ("arboleda", "bosquecillo"),
    "hill": ("colina", "loma"),
    "hills": ("colinas", "lomas"),
    "lake": ("lago",),
    "river": ("río",),
    "pass": ("paso", "puerto"),
    "monastery": ("monasterio",),
    "chapel": ("capilla",),
    "shrine": ("santuario", "altar"),
    "temple": ("templo",),
    "shelter": ("refugio",),
    "retreat": ("retiro",),
    "manor": ("casona", "mansión"),
    "castle": ("castillo",),
    "harbor": ("puerto",),
    "harbour": ("puerto",),
    "inn": ("posada",),
    "tavern": ("taberna",),
    "well": ("pozo",),
    "pit": ("foso", "fosa", "pozo"),
    "nest": ("nido",),
    "warren": ("madriguera",),
}


def normaliza(s):
    return s.lower()


texto = CORPUS.read_text(encoding="utf-8")
lineas = texto.split("\n")
pares = []
fichero = "?"
for i, l in enumerate(lineas):
    if l.startswith("// FILE:"):
        fichero = l[8:].strip()
    if l.startswith('        en = "') and i + 1 < len(lineas) and lineas[i + 1].startswith('        es = "'):
        en = l[len('        en = "'):-1]
        es = lineas[i + 1][len('        es = "'):-1]
        if es and len(en) <= 70 and "<" not in en and "%" not in en:
            pares.append((fichero, en, es, i + 1))

avisos = []
for fichero, en, es, linea in pares:
    pal_en = set(re.findall(r"[a-z']+", normaliza(en)))
    tipos_en = [t for t in TIPOS if t in pal_en]
    if not tipos_en:
        continue
    es_n = normaliza(es)
    # el espaniol acierta si contiene algun termino admisible de algun tipo presente
    if any(term in es_n for t in tipos_en for term in TIPOS[t]):
        continue
    # y solo avisamos si en su lugar lleva el termino de otro tipo
    cruzados = sorted({t for t, terms in TIPOS.items()
                       if t not in tipos_en and any(term in es_n for term in terms)})
    if cruzados:
        avisos.append((fichero, linea, en, es, tipos_en, cruzados))

print("pares con sustantivo cruzado: %d (de %d candidatos)\n" % (len(avisos), len(pares)))
for fichero, linea, en, es, tipos_en, cruzados in avisos:
    print("%s:%d" % (fichero.replace("\\", "/").split("/")[-1], linea))
    print("   EN: %-52s [%s]" % (en[:52], ",".join(tipos_en)))
    print("   ES: %-52s [%s]" % (es[:52], ",".join(cruzados)))
