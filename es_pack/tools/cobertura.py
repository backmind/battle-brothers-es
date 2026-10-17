"""Los tres barridos de cobertura REAL, que es distinta de la cobertura del
corpus.

El build dice "dist 15410, wip 0" y suena a 100%, pero eso mide otra cosa: que
todo lo que el extractor encontro tiene traduccion. Hay tres maneras de que
una linea salga en ingles en pantalla, y solo la primera se ve en las metricas
de siempre:

  A. UNIVERSO. La cadena esta en un fichero que el arbol de referencia no
     tiene, asi que la extraccion nunca la vio. No aparece ni en el corpus ni
     en el log: no existe para nosotros. Asi se perdieron los 71 consejos de
     los cinco ficheros de DLC.

  B. VENTANA (conducto). El par existe y esta bien, pero el juego empuja ese
     texto a la interfaz sin pasarlo por Rosetta. No sale como NOT FOUND en el
     log porque nadie pregunta. Asi salian en ingles la ventana de negociacion,
     los dos dialogos del combate tactico y los tooltips de ambicion.

  C. COMPOSICION. El juego pega el literal con una variable y el runtime recibe
     la SUMA, que no casa ningun par suelto. Asi salia "Cut down by Hoggart la
     Comadreja" y asi seguian en ingles las entradas del historial de relacion.

Uso:  PYTHONUTF8=1 uv run python es_pack/tools/cobertura.py [a|b|c]
Sin argumento corre los tres.
"""
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
from rutas import ARBOLES, DATA  # noqa: E402  ver rutas.py
ARBOL = ARBOLES / "original_current"
CORPUS = REPO / "es_pack" / "corpus" / "base_es.nut"
HOOKS_UP = REPO / "vendor" / "rosetta" / "rosetta" / "hooks.nut"
HOOKS_PACK = REPO / "es_pack" / "src" / "scripts" / "!mods_preload" / "mod_battle_brothers_es_hooks.nut"


def _corpus():
    """literales y trozos literales de los patrones"""
    literales, trozos = set(), []
    for l in CORPUS.read_text(encoding="utf-8").split("\n"):
        s = l.strip()
        if not (s.startswith('en = "') and s.endswith('"')):
            continue
        v = (s[6:-1].replace("\\'", "'").replace("\\x7b", "{")
             .replace("\\x7d", "}").replace("\\x22", '"'))
        if "<" in v and ">" in v:
            trozos += [t.strip() for t in re.split(r"<[^>]+>", v) if len(t.strip()) >= 4]
        else:
            literales.add(v)
    return literales, "\n".join(trozos)


def barrido_a():
    """Universo: scripts que carga el juego frente a los del arbol."""
    print("== A. UNIVERSO DE EXTRACCION ==")
    if not DATA.exists():
        print("   (sin acceso a la carpeta data del juego, se salta)")
        return
    juego = set()
    for dat in sorted(DATA.glob("data_*.dat")):
        with zipfile.ZipFile(dat) as z:
            juego |= {n[:-5] for n in z.namelist() if n.endswith(".cnut")}
    arbol = {str(p.relative_to(ARBOL).as_posix())[:-4] for p in ARBOL.rglob("*.nut")}
    faltan = sorted(juego - arbol)
    print(f"   scripts en el juego: {len(juego)}   en el arbol: {len(arbol)}")
    print(f"   EN EL JUEGO Y NO EN EL ARBOL: {len(faltan)}")
    for f in faltan:
        print(f"      {f}")


def barrido_b():
    """Ventanas: puntos de empuje a interfaz y si estan hookeados."""
    print("\n== B. VENTANAS (conductos sin hookear) ==")
    hookeado = HOOKS_UP.read_text(encoding="utf-8") + "\n" + HOOKS_PACK.read_text(encoding="utf-8")
    FUNC = re.compile(r"function\s+(\w+)\s*\(", re.M)
    LITERAL = re.compile(r'"([A-Z][^"\\]{5,}|[^"\\]*\s[^"\\]{5,})"')
    CAMPO = re.compile(r"\b(Title|SubTitle|Text|Name|Description|Tooltip|Header|Label)\s*=")
    filas = []
    for f in sorted(ARBOL.rglob("*.nut")):
        rel = str(f.relative_to(ARBOL).as_posix())
        if not (rel.startswith("scripts/ui/") or rel.endswith("data_helper.nut")):
            continue
        txt = f.read_text(encoding="utf-8", errors="replace")
        pos = [(m.group(1), m.start()) for m in FUNC.finditer(txt)]
        for k, (nombre, ini) in enumerate(pos):
            fin = pos[k + 1][1] if k + 1 < len(pos) else len(txt)
            cuerpo = txt[ini:fin]
            lits = [x for x in LITERAL.findall(cuerpo)
                    if not x.startswith(("gfx/", "ui/", "sounds/", "scripts/"))]
            if not lits and not CAMPO.search(cuerpo):
                continue
            modulo = rel[:-4].split("/")[-1]
            filas.append((rel, nombre, modulo in hookeado, len(lits)))
    sin = defaultdict(int)
    for rel, nombre, hk, n in filas:
        if not hk:
            sin[rel] += n * 2 + 1
    print(f"   funciones de interfaz con texto: {len(filas)}")
    print(f"   en modulos hookeados:            {sum(1 for x in filas if x[2])}")
    print(f"   en modulos SIN hookear:          {sum(1 for x in filas if not x[2])}")
    for rel in sorted(sin, key=lambda k: -sin[k])[:8]:
        print(f"      {rel}")


def barrido_c():
    """Composiciones: literales pegados con + sin patron que los case."""
    print("\n== C. COMPOSICIONES ==")
    literales, trozos = _corpus()
    COMPO = re.compile(r'"((?:[^"\\]|\\.){4,120})"\s*\+|\+\s*"((?:[^"\\]|\\.){4,120})"')
    TEC = re.compile(r"^[a-z_.]+$|^gfx/|^sounds/|^scripts/|\.png$|\.nut$|^[A-Z_]+$|^\W+$")
    PROSA = re.compile(r"^ ?[A-Za-z][A-Za-z',.!?%\- ]{8,}$")
    sitios = defaultdict(list)
    for f in ARBOL.rglob("*.nut"):
        rel = str(f.relative_to(ARBOL).as_posix())
        for m in COMPO.finditer(f.read_text(encoding="utf-8", errors="replace")):
            lit = (m.group(1) or m.group(2)).replace("\\'", "'")
            if TEC.match(lit) or " " not in lit:
                continue
            sitios[lit].append(rel)
    cubiertos = riesgo = 0
    resto = []
    for lit, files in sitios.items():
        n = lit.strip()
        if n in trozos:
            cubiertos += 1
        elif n in literales:
            riesgo += 1
        elif PROSA.match(lit):
            resto.append((lit, files[0]))
    print(f"   literales concatenados: {len(sitios)}")
    print(f"      con patron que los case:              {cubiertos}")
    print(f"      con par suelto pero sin patron:       {riesgo}")
    print(f"      prosa sin par ni patron:              {len(resto)}")
    por_f = defaultdict(list)
    for lit, f in resto:
        por_f[f].append(lit)
    for f in sorted(por_f, key=lambda k: -len(por_f[k]))[:8]:
        print(f"      {f}  ({len(por_f[f])})")


def main():
    cual = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    if cual in ("", "a"):
        barrido_a()
    if cual in ("", "b"):
        barrido_b()
    if cual in ("", "c"):
        barrido_c()
    return 0


if __name__ == "__main__":
    sys.exit(main())
