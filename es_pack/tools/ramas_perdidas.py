"""Cola de trabajo de las ramas de diálogo que faltan en el español.

Los textos de evento se escriben con bloques de variantes, `{a|b|c}`, y el juego
elige una rama al azar. Hay textos donde el español tiene menos ramas que el
inglés, así que la versión española ofrece menos variedad. No rompe nada: sólo
se ve menos.

LA COLA SE DERIVA DEL CORPUS, no de una lista guardada. Un texto deja de
aparecer en cuanto tiene tantas ramas como el inglés, así que el progreso es
implícito y no hay ningún fichero de estado que se pueda desincronizar. Para
reanudar un trabajo interrumpido basta con volver a ejecutar esto.

Uso:
    PYTHONUTF8=1 uv run python es_pack/tools/ramas_perdidas.py
        lista los textos pendientes, en orden estable

    PYTHONUTF8=1 uv run python es_pack/tools/ramas_perdidas.py N
        vuelca el texto N entero, inglés y español, con las ramas separadas
        y numeradas, que es como se ve cuál falta
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "es_pack" / "tools"))
from checks import ABRE_RE  # noqa: E402

CORPUS = REPO / "es_pack" / "corpus" / "base_es.nut"
from rutas import ARBOLES  # noqa: E402  ver rutas.py
ANTIGUO = ARBOLES / "original"
PAR_RE = re.compile(r'\ben\s*=\s*"((?:[^"\\]|\\.)*)"\s*\n\s*es\s*=\s*"((?:[^"\\]|\\.)*)"')


def pendientes():
    """Textos donde el español tiene menos ramas que el inglés, en orden estable.

    El orden es el del corpus, que sólo cambia si se regenera, así que dos
    ejecuciones seguidas dan la misma numeración.
    """
    vistos, salida = set(), []
    for m in PAR_RE.finditer(CORPUS.read_text(encoding="utf-8")):
        en, es = m.group(1), m.group(2)
        if en in vistos or not es:
            continue
        vistos.add(en)
        if not (ABRE_RE.search(en) or "|" in en):
            continue
        faltan = en.count("|") - es.count("|")
        if faltan > 0:
            salida.append((en, es, faltan))
    return salida


def ramas(texto):
    """Parte por el separador de nivel superior, conservando el resto intacto."""
    return texto.split("|")


def main():
    cola = pendientes()
    if len(sys.argv) > 1:
        n = int(sys.argv[1])
        if not 1 <= n <= len(cola):
            raise SystemExit(f"hay {len(cola)} textos pendientes; pide entre 1 y {len(cola)}")
        en, es, faltan = cola[n - 1]
        print(f"TEXTO {n} de {len(cola)}: al español le faltan {faltan} rama(s)\n")
        for etiqueta, txt in (("INGLÉS", en), ("ESPAÑOL", es)):
            trozos = ramas(txt)
            print(f"===== {etiqueta}: {len(trozos)} rama(s) =====")
            for i, t in enumerate(trozos, 1):
                print(f"--- rama {i} ---")
                print(t)
            print()
        return 0

    total = sum(f for _, _, f in cola)
    print(f"textos pendientes: {len(cola)}   ramas que faltan: {total}\n")
    print(f"{'#':>3}  {'faltan':>6}  {'ramas en':>8}  texto")
    print(f"{'':>3}  {'':>6}  {'en / es':>8}")
    print("-" * 100)
    for i, (en, es, faltan) in enumerate(cola, 1):
        print(f"{i:3d}  {faltan:6d}  {en.count('|') + 1:3d} /{es.count('|') + 1:3d}  {en[:70]}")
    print()
    print("Para ver uno entero:  ramas_perdidas.py <numero>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
