"""Barrido E: el texto que el juego empuja a la interfaz desde FUERA de las pantallas.

La clase B de cobertura.py mira `scripts/ui/screens/`, que es donde uno espera
encontrar los rotulos. Pero el juego tambien compone tablas de interfaz en la
logica: `skill.getHitFactors()` devuelve las filas de por que aciertas mas o
menos, `party.getTooltip()` la ficha de una partida del mapa,
`world_entity.getTroopComposition()` la lista de tropas. Ninguna esta en
`ui/screens/`, ninguna pasa por un getter traducido, y por tanto ninguna la
veia el barrido anterior. Asi se nos escaparon "Surrounded", "Armed with
shield" y "Distance of 2", que llevaban su par en el corpus desde el principio
(QA 30/08).

Que hace: recorre el arbol entero, busca funciones que asignen texto de usuario
a una clave de interfaz (text, Title, SubTitle, name, tooltip, Description,
error...), y cruza con los hooks que instalan el pack y el runtime. Lo que
queda sin cruzar es conducto candidato.

Lo que NO puede decidir: si ese texto llega a verse. Muchas funciones componen
texto que otro getter ya traducido devuelve luego. Por eso el informe ordena
por cantidad y hay que leerlo, no aplicarlo a ciegas.

Uso:
    PYTHONUTF8=1 uv run python es_pack/tools/cobertura_datos.py [-v]
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
from rutas import ARBOLES  # noqa: E402  ver rutas.py
ARBOL = ARBOLES / "original_current" / "scripts"
HOOKS_PACK = REPO / "es_pack" / "src" / "scripts" / "!mods_preload" / "mod_battle_brothers_es_hooks.nut"
HOOKS_UP = REPO / "vendor" / "rosetta" / "rosetta" / "hooks.nut"

# claves de interfaz: si a una de estas se le asigna una cadena de usuario, eso
# se pinta en algun sitio
CLAVE = re.compile(r'^\s*(text|Text|Title|SubTitle|name|Name|tooltip|Tooltip|'
                   r'Description|description|error|label|header|Header)\s*=\s*"'
                   r'((?:[^"\\]|\\.)*)"')
FUNCION = re.compile(r'^\s*function\s+(\w+)\s*\(')
# lo que parece texto de usuario y no identificador interno
RUIDO = re.compile(r'^(ui/|gfx/|scripts/|[a-z_]+\.[a-z_]+|[a-z]+(_[a-z0-9]+)+$)|'
                   r'\.(png|nut|jpg|ogg)$|^\s*$')


def texto_de_usuario(s):
    if len(s) < 3 or RUIDO.search(s):
        return False
    if not re.search(r"[A-Za-z]", s):
        return False
    # una sola palabra en minuscula suele ser clave interna
    if " " not in s and s[0].islower():
        return False
    return True


# Cubierto por diseno, con el porque. No es una lista de excusas: cada linea
# es un conducto generico que el runtime o el pack ya envuelven, de modo que
# todo el texto que pase por ahi se traduce sin hook propio.
CUBIERTO = [
    ("scripts/contracts/", "el texto de contrato viaja por buildTextFromTemplate "
                           "y por getUIList/getUIButtons, los tres envueltos"),
    ("scripts/events/", "igual que los contratos: el sistema de eventos los pasa "
                        "por el envoltorio de plantillas"),
    ("scripts/ui/screens/tooltip/tooltip_events", "onQueryUI*TooltipData envuelto "
                                                  "por el runtime (hooks.nut:134)"),
    ("scripts/config/", "tablas de datos: se traducen enteras en el primer uso "
                        "(rumores) o casan par literal por getName"),
]


# Funciones que el conducto generico de tooltips ya cubre por su nombre:
# onQuery*TooltipData del runtime devuelve sus filas y translateTooltip les
# traduce el `text`. OJO: solo el de primer nivel. Lo que cuelgue de `children`
# NO se traduce, y por ahi se colaron los factores de acierto de getHitFactors.
PORNOMBRE = {
    "getTooltip": "lo recoge onQuery*TooltipData y lo pasa por translateTooltip",
    "getRosterTooltip": "igual, por la consulta de tooltip del sequito",
    "getDescription": "getter envuelto en el runtime (item, skill, background)",
    "getName": "getter envuelto en el runtime",
}


def cubierto_por_diseno(ruta, fn):
    for pref, razon in CUBIERTO:
        if ruta.startswith(pref):
            return razon
    return PORNOMBRE.get(fn)


def hookeados():
    """(ruta de script, nombre de funcion) que ya envuelve alguien"""
    out = set()
    globales = set()
    for f in (HOOKS_PACK, HOOKS_UP):
        if not f.exists():
            continue
        txt = f.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r'mod\.hook(?:Tree)?\(\s*"([^"]+)"(.*?)\n    \}\)',
                             txt, re.S):
            ruta, cuerpo = m.group(1), m.group(2)
            for fn in re.findall(r"\bq\.(\w+)\s*=", cuerpo):
                out.add((ruta, fn))
        # envoltorios de globales, que cubren una clase entera
        globales.update(re.findall(r"::(\w+)\s*=\s*function", txt))
    return out, globales


def main():
    verbose = "-v" in sys.argv
    if not ARBOL.exists():
        raise SystemExit(f"no encuentro el arbol de referencia: {ARBOL}")

    hooks, globales = hookeados()
    # hookTree sobre una base cubre a sus hijas; se aproxima por prefijo de ruta
    bases = {r for r, _ in hooks}

    por_funcion = defaultdict(list)
    for p in sorted(ARBOL.rglob("*.nut")):
        ruta = "scripts/" + p.relative_to(ARBOL).as_posix()[:-4]
        fn = "?"
        for linea in p.read_text(encoding="utf-8", errors="replace").split("\n"):
            mf = FUNCION.match(linea)
            if mf:
                fn = mf.group(1)
                continue
            mc = CLAVE.match(linea)
            if mc and texto_de_usuario(mc.group(2).replace("\\'", "'")):
                por_funcion[(ruta, fn)].append(mc.group(2))

    cubiertos, disenno, sueltos = [], [], []
    for clave, lits in por_funcion.items():
        ruta, fn = clave
        # cubierto si alguien hookea esa funcion en ese fichero, o en una base
        # cuya ruta es prefijo (hookTree)
        ok = clave in hooks or any(
            (b, fn) in hooks and (ruta.startswith(b.rsplit("/", 1)[0] + "/"))
            for b in bases)
        fila = (len(lits), ruta, fn, lits)
        if ok:
            cubiertos.append(fila)
        elif cubierto_por_diseno(ruta, fn):
            disenno.append(fila)
        else:
            sueltos.append(fila)

    sueltos.sort(reverse=True)
    print(f"funciones que componen texto de usuario: {len(por_funcion)}")
    print(f"   envueltas por un hook con nombre:     {len(cubiertos)}")
    print(f"   cubiertas por un conducto generico:   {len(disenno)}")
    print(f"   SIN cubrir:                           {len(sueltos)}")
    print(f"   envoltorios de globales detectados:   {sorted(globales)}\n")
    print("=== candidatas, de mas texto a menos ===")
    for n, ruta, fn, lits in sueltos:
        if n < 2 and not verbose:
            continue
        print(f"  {n:>3}  {ruta}.{fn}()")
        for s in (lits if verbose else lits[:3]):
            print(f"          {s[:100]}")
    if not verbose:
        n1 = sum(1 for n, *_ in sueltos if n < 2)
        print(f"\n({n1} con un solo literal, ocultas; con -v se listan)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
