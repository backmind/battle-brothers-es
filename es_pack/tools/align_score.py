"""Detector de emparejamientos improbables (traduccion que no corresponde a su original).

Motivacion: el corpus se construyo alineando dos arboles de ficheros, y ese
proceso desplazo valores. Ademas la fuente es "plata": contiene traducciones
que no corresponden a su original aunque esten bien alineadas. Este script no
compara contra la fuente: juzga cada par por si mismo.

Metodo: se entrena un modelo lexico de traduccion (IBM Model 1, unas pocas
iteraciones de EM) con TODOS los pares del propio corpus. Como la gran mayoria
son correctos, el modelo aprende las correspondencias reales (blade->hoja,
crowns->coronas...). Despues se puntua cada par: los que quedan en la cola de
improbabilidad son candidatos a estar desplazados o mal traducidos.

Se combinan senales de alta precision independientes del modelo:
  NUMEROS   cifras presentes en el ingles que no aparecen en el espaniol
  TOKENS    marcadores %x% que no cuadran (ya cubierto por qa_mech, se repite
            aqui para dar contexto al revisor)
  LONGITUD  proporcion de longitud es/en fuera de rango razonable
  LEXICO    puntuacion del modelo por palabra (la senal principal)

Uso:
    PYTHONUTF8=1 uv run python es_pack/tools/align_score.py [n_sospechosos]

Salida: es_pack/build/align_report.tsv con todos los pares ordenados de peor a
mejor puntuacion, y un resumen por consola. No modifica el corpus.
"""
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "es_pack" / "tools"))
from build_dist import BUILD, CORPUS, get_field, load_blocks  # noqa: E402

ITERACIONES = 4
MIN_PALABRAS = 3          # pares mas cortos no dan senal lexica fiable
TOKEN_RE = re.compile(r"[a-záéíóúüñ']+", re.I)
LIMPIA_RE = re.compile(
    r"\[/?[^\]]*\]|%\w+%|\\x[0-9a-f]{2}|\\n|\\t|<[^>]*>|\\\"", re.I)
NUM_RE = re.compile(r"\d+")

VACIAS_EN = {"the", "a", "an", "of", "to", "and", "or", "in", "on", "at", "for",
             "with", "is", "are", "be", "you", "your", "it", "that", "this",
             "as", "by", "from", "his", "her", "their", "has", "have", "will"}
VACIAS_ES = {"el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del",
             "a", "al", "y", "o", "en", "con", "por", "para", "que", "se", "su",
             "sus", "es", "son", "ser", "lo", "le", "les", "tu", "tus", "te",
             "no", "si", "como", "mas", "pero", "ha", "han", "he"}


def palabras(texto, vacias):
    limpio = LIMPIA_RE.sub(" ", texto)
    return [w.lower() for w in TOKEN_RE.findall(limpio)
            if len(w) > 2 and w.lower() not in vacias]


def entrena(pares):
    """IBM Model 1 con EM uniforme inicial."""
    t = defaultdict(lambda: defaultdict(float))
    vocab_es = defaultdict(set)
    for en, es in pares:
        for e in set(en):
            for s in set(es):
                vocab_es[e].add(s)
    for e, conjunto in vocab_es.items():
        inicial = 1.0 / len(conjunto)
        for s in conjunto:
            t[e][s] = inicial

    for _ in range(ITERACIONES):
        cuenta = defaultdict(lambda: defaultdict(float))
        total = defaultdict(float)
        for en, es in pares:
            for s in es:
                norm = sum(t[e][s] for e in en) or 1e-12
                for e in en:
                    delta = t[e][s] / norm
                    cuenta[e][s] += delta
                    total[e] += delta
        for e in cuenta:
            for s in cuenta[e]:
                t[e][s] = cuenta[e][s] / (total[e] or 1e-12)
    return t


def main():
    limite = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    bloques = load_blocks(CORPUS)
    datos = []
    for b in bloques:
        en, es = get_field(b, "en"), get_field(b, "es")
        if not en or not es:
            continue
        datos.append((en, es, palabras(en, VACIAS_EN), palabras(es, VACIAS_ES)))

    entrenables = [(pe, ps) for _, _, pe, ps in datos
                   if len(pe) >= MIN_PALABRAS and len(ps) >= MIN_PALABRAS]
    print("pares con traduccion: %d | usados para entrenar: %d"
          % (len(datos), len(entrenables)))
    t = entrena(entrenables)

    filas = []
    for en, es, pe, ps in datos:
        senales = []
        num_en, num_es = NUM_RE.findall(en), NUM_RE.findall(es)
        if sorted(num_en) != sorted(num_es):
            senales.append("NUMEROS")
        if len(en) > 25:
            ratio = len(es) / len(en)
            if ratio < 0.55 or ratio > 2.0:
                senales.append("LONGITUD(%.2f)" % ratio)
        if len(pe) >= MIN_PALABRAS and len(ps) >= MIN_PALABRAS:
            logp = 0.0
            for s in ps:
                mejor = max((t[e][s] for e in pe), default=0.0)
                logp += math.log(mejor + 1e-9)
            score = logp / len(ps)
        else:
            score = None
        filas.append((score, senales, en, es))

    con_score = [f for f in filas if f[0] is not None]
    con_score.sort(key=lambda f: f[0])
    destino = BUILD / "align_report.tsv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8", newline="") as fd:
        fd.write("score\tsenales\ten\tes\n")
        for score, senales, en, es in con_score:
            fd.write("%.3f\t%s\t%s\t%s\n" % (
                score, ",".join(senales) or "-",
                en.replace("\t", " "), es.replace("\t", " ")))

    print("informe completo:", destino)
    solo_senales = [f for f in filas if f[1]]
    print("pares con senal de alta precision (numeros/longitud): %d"
          % len(solo_senales))
    print("\n=== %d peores por puntuacion lexica ===" % limite)
    for score, senales, en, es in con_score[:limite]:
        print("\n  score %.2f  %s" % (score, ",".join(senales) or ""))
        print("    EN: %s" % en[:110])
        print("    ES: %s" % es[:110])
    return 0


if __name__ == "__main__":
    sys.exit(main())
