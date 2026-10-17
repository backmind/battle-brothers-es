"""Localiza ventanas de corrimiento: tramos donde el español va desplazado.

El problema que resuelve: los textos del juego viven en tablas, y el corpus se
armó alineando dos árboles de ficheros. Cuando el juego añadió o quitó una
entrada, todo lo que iba detrás se corrió una posición, y cada texto acabó
mostrando el del vecino. Leyendo el corpus no se ve, porque cada línea por
separado parece bien. `CONTRIBUTING.md` lo llama el defecto más frecuente del
proyecto.

`align_score.py` puntúa cada par por separado y saca los improbables, que es
otra pregunta: dice "este par es raro", no "este tramo está desplazado". Esto
prueba la hipótesis del desplazamiento de forma directa.

Uso:
    PYTHONUTF8=1 uv run python es_pack/tools/shift_detect.py [margen]
    PYTHONUTF8=1 uv run python es_pack/tools/shift_detect.py 1.5 --fichero item_names

## Método

Se entrena un modelo léxico de traducción (IBM Model 1) con todos los pares del
corpus, igual que `align_score.py`. Después, para cada fichero y cada
desplazamiento k, se compara par a par la puntuación del alineamiento actual con
la del desplazado:

    d[i] = puntuacion(en[i], es[i+k]) - puntuacion(en[i], es[i])

Un tramo seguido con `d` claramente positivo es un corrimiento: el español de
esas entradas encaja mejor con el inglés de otra. Los tramos de una sola entrada
se descartan, porque una entrada suelta que puntúa mejor desplazada es ruido
normal en tablas de sinónimos.

## Por qué hace falta el filtro de apoyo

El modelo se entrena con el propio corpus, corrimientos incluidos. Si una
palabra inglesa sólo aparece en un par, el modelo memoriza esa pareja y el
alineamiento actual se avala a sí mismo, esté bien o mal. Por eso sólo cuentan
los enlaces con **apoyo en dos pares distintos o más**: así el testimonio viene
siempre de fuera del par que se está juzgando.

Eso es también el límite del método: una palabra que aparece una sola vez en
todo el corpus, como los compuestos inventados de tipo `Skullsplitter`, no deja
señal y su tramo no se puede juzgar así. Para esos casos el instrumento es
`gt_align.py`, que compara contra el árbol de referencia.

## Dos clases de falso positivo conocidas

**Numerales compuestos.** `Twenty-two` sale marcado como si le fuera mejor
"Veinte", porque el tokenizador lo parte en "twenty" y "two", y "twenty" aparece
traducido como "veinte" en decenas de textos. La entrada está bien; lo que falla
es que el detector no ve que "Veintidós" ya contiene ese "veinte". En
`strings.nut` son unas siete entradas seguidas y se reconocen de un vistazo.

**Valores nuevos o únicos.** Una entrada cuya traducción no se parece a nada del
resto del corpus no tiene con qué defenderse, así que gana cualquier vecino que
sí esté atestiguado. Pasó con los modificadores de objeto famoso recién
convertidos a locución: "de solera" o "de recio porte" no aparecían en ningún
otro par, y el detector los marcaba. `ABS_MIN` se lleva la mayoría, porque exige
que el candidato desplazado esté bien atestiguado por sí mismo, pero conviene
saberlo al leer la salida después de una tanda de ediciones.

Ninguna de las dos se filtra en silencio: preferible verlas y descartarlas a
mano que perder un hallazgo real por un filtro demasiado listo.

## Coste

Entrenar el modelo sobre el corpus entero tarda unos tres minutos. No hay caché
a propósito: es una herramienta de auditoría que se pasa de vez en cuando, y una
caché que se quede vieja daría resultados mentirosos.
"""
import re
import sys
from collections import defaultdict
from math import log
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "es_pack" / "tools"))
from align_score import (VACIAS_EN, VACIAS_ES, entrena,  # noqa: E402
                         palabras)
from build_dist import CORPUS, get_field  # noqa: E402

DESPLAZAMIENTOS = (-2, -1, 1, 2)

MARGEN = 15.0
"""Cuánto tiene que ganar el desplazado, en log-probabilidad media por palabra.

15 no es arbitrario. El piso de una pareja de palabras sin apoyo es log(1e-9),
unos -20.7, así que una diferencia cercana a 20 significa que el alineamiento
actual **no tiene ni un apoyo** y el desplazado lo tiene fuerte. Ahí es donde
están los corrimientos de verdad. Por debajo de 15 aparecen los casos en que
ninguno de los dos está bien atestiguado, que son ruido."""

ABS_MIN = -5.0
"""Además del margen, el desplazado tiene que estar bien atestiguado por sí
mismo. Sin esto, cualquier entrada cuyo valor sea nuevo o único en el corpus
sale marcada: su alineamiento actual no se puede defender, y entonces gana
cualquier vecino aunque tampoco tenga apoyo."""

APOYO_MIN = 2
MINIMO_TRAMO = 1
"""Uno, no dos. Un corrimiento deja huella sólo en las entradas cuyas palabras
tienen apoyo, así que aparece a saltos: en la ventana 56-59 de `item_names`
delata a `Madness` y a `War Cleaver` y calla en las dos de en medio, porque
"Escultor" y "Carver" no aparecen en ningún otro par. Exigir dos seguidos hacía
que el detector no encontrara nada."""

PISO = log(1e-9)

FICHERO_RE = re.compile(r"^    // FILE: (.*)$", re.M)


def pares_por_fichero(ruta=None):
    """Los pares del corpus agrupados por fichero del juego, en orden."""
    texto = Path(ruta or CORPUS).read_text(encoding="utf-8")
    trozos = FICHERO_RE.split(texto)
    grupos = []
    for i in range(1, len(trozos), 2):
        nombre = Path(trozos[i].strip().replace("\\", "/")).name
        bloques = re.findall(r"\n    \{.*?\n    \}", trozos[i + 1], re.S)
        pares = []
        for b in bloques:
            en, es = get_field(b, "en"), get_field(b, "es")
            if en and es:
                pares.append((en, es))
        if len(pares) >= 4:
            grupos.append((nombre, pares))
    return grupos


def modelo(grupos):
    """Entrena el modelo y cuenta en cuántos pares distintos se apoya cada enlace."""
    datos = []
    for _, pares in grupos:
        for en, es in pares:
            datos.append((palabras(en, VACIAS_EN), palabras(es, VACIAS_ES)))
    entrenables = [(pe, ps) for pe, ps in datos if pe and ps]
    t = entrena(entrenables)

    apoyo = defaultdict(int)
    for pe, ps in entrenables:
        for e in set(pe):
            for s in set(ps):
                apoyo[(e, s)] += 1
    return t, apoyo


def puntua(t, apoyo, en_pal, es_pal):
    """Log-probabilidad media por palabra española, contando sólo los enlaces
    con apoyo en dos pares o más. Devuelve None si no hay nada que juzgar."""
    if not en_pal or not es_pal:
        return None
    total, contadas = 0.0, 0
    for s in es_pal:
        mejor = 0.0
        for e in en_pal:
            if apoyo.get((e, s), 0) >= APOYO_MIN:
                mejor = max(mejor, t[e][s])
        if mejor > 0.0:
            total += log(mejor)
            contadas += 1
        else:
            total += PISO
            contadas += 1
    return total / contadas if contadas else None


def tramos_positivos(deltas, margen):
    """Tramos seguidos de indices con delta por encima del margen."""
    salida, actual = [], []
    for i, d in sorted(deltas.items()):
        if d is not None and d >= margen and (not actual or i == actual[-1] + 1):
            actual.append(i)
        else:
            if len(actual) >= MINIMO_TRAMO:
                salida.append(actual)
            actual = [i] if (d is not None and d >= margen) else []
    if len(actual) >= MINIMO_TRAMO:
        salida.append(actual)
    return salida


def revisa(grupos, t, apoyo, margen=MARGEN):
    """Los tramos sospechosos, de mas a menos evidencia."""
    hallazgos = []
    for nombre, pares in grupos:
        pal = [(palabras(en, VACIAS_EN), palabras(es, VACIAS_ES))
               for en, es in pares]
        base = [puntua(t, apoyo, pe, ps) for pe, ps in pal]
        for k in DESPLAZAMIENTOS:
            deltas = {}
            for i in range(len(pares)):
                j = i + k
                if not (0 <= j < len(pares)) or base[i] is None:
                    continue
                otro = puntua(t, apoyo, pal[i][0], pal[j][1])
                if otro is None or otro < ABS_MIN:
                    continue  # el desplazado tampoco esta atestiguado: no dice nada
                deltas[i] = otro - base[i]
            for tramo in tramos_positivos(deltas, margen):
                fuerza = sum(deltas[i] for i in tramo) / len(tramo)
                hallazgos.append({
                    "fichero": nombre, "k": k, "indices": tramo,
                    "fuerza": fuerza,
                    "pares": [(i, pares[i][0], pares[i][1], pares[i + k][1])
                              for i in tramo],
                })
    hallazgos.sort(key=lambda h: -h["fuerza"] * len(h["indices"]))
    return hallazgos


def main(argv):
    filtro = None
    if "--fichero" in argv:
        i = argv.index("--fichero")
        filtro = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    margen = float(argv[0]) if argv else MARGEN

    grupos = pares_por_fichero()
    print("ficheros con 4 pares o mas: %d" % len(grupos))
    t, apoyo = modelo(grupos)
    print("enlaces con apoyo suficiente: %d de %d"
          % (sum(1 for v in apoyo.values() if v >= APOYO_MIN), len(apoyo)))

    if filtro:
        grupos = [(n, p) for n, p in grupos if filtro in n]
        print("filtrado a: %s" % ", ".join(n for n, _ in grupos))

    hallazgos = revisa(grupos, t, apoyo, margen)
    print("margen: %.1f | tramos sospechosos: %d" % (margen, len(hallazgos)))
    print()
    for h in hallazgos:
        print("%s  desplazamiento %+d  indices %d-%d  fuerza %.2f"
              % (h["fichero"], h["k"], h["indices"][0], h["indices"][-1],
                 h["fuerza"]))
        for i, en, ahora, propuesto in h["pares"]:
            print("   %4d  %-26s ahora %-26s encaja mejor con %s"
                  % (i, en[:26], ahora[:26], propuesto[:30]))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
