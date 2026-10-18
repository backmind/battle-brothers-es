"""Avisa de cuándo Rosetta se mueve por debajo de lo que el pack replica.

El problema que resuelve: el pack no sólo *usa* Rosetta, en dos sitios la
**duplica**. `build_dist.py` decide qué par se distribuye y qué par va a
cuarentena reimplementando el contrato de `validateRule`, y lleva copiado a mano
el conjunto de tipos de sub que el runtime admite. Si upstream añade un tipo o
cambia una regla, nada avisa: el build sigue en verde y empieza a mandar a
cuarentena pares buenos, o al revés, a distribuir pares que el runtime
rechazará al cargar, y eso último aborta la traducción entera en la partida de
quien lo instale.

Vigilar "si upstream se movió" no sirve: se mueve en cada commit y el aviso se
aprende a ignorar. Esto vigila sólo las piezas concretas de las que dependemos.

Uso:
    PYTHONUTF8=1 uv run python es_pack/tools/check_upstream_drift.py
    PYTHONUTF8=1 uv run python es_pack/tools/check_upstream_drift.py --ref master
    PYTHONUTF8=1 uv run python es_pack/tools/check_upstream_drift.py <ruta al .nut>

Sin argumentos usa el runtime del árbol de trabajo. Con `--ref` lo lee de una
rama, que es lo que permite automatizarlo: `git fetch upstream` y después
`--ref upstream/master` dice si la versión nueva nos afecta antes de adoptarla.

Devuelve 0 si nada de lo nuestro se ha movido y 1 si hay que mirar algo.

## Dos clases de vigilancia, porque hay dos clases de acoplamiento

**Espejo.** Tenemos una copia de un dato que vive en el runtime, así que no hace
falta fijar nada: se compara la copia con el original y basta. Es el caso de los
tipos de sub, que se derivan del `subRes` del runtime y se comparan con la
constante `SUBS` de `build_dist.py`.

**Contrato.** Hemos reimplementado una lógica, y una copia no se puede comparar
con su original. Ahí se fija el hash del cuerpo de la función y se avisa cuando
cambie, para ir a leer qué cambió. Es el caso de `validateRule` y de las dos
funciones que definen la sintaxis de patrones que `classify()` da por supuesta.

Un hash que cambia no significa que algo se haya roto: puede ser un comentario.
Significa "ve a leerlo". Cuando se lea y no afecte, se actualiza el pin con el
motivo, igual que `ACEPTADOS` en `check_ui_drift.py`.
"""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "es_pack" / "tools"))

# La ruta dentro del repo de Suor, que es la que vale para --ref; en este
# repo la copia de trabajo vive en vendor/rosetta con la misma estructura.
RUNTIME_REL = "scripts/!mods_preload/!rosetta.nut"
VENDOR = REPO / "vendor" / "rosetta"

# Cuerpos de función fijados, con el ref del que se tomaron y qué nos importa de
# cada uno. Al adoptar una versión nueva de Rosetta se leen los que hayan
# cambiado y se actualiza el hash con el motivo.
PINES = {
    "validateRule": (
        "b35e7ac31d8fccb0",
        "es el contrato que classify() reimplementa en build_dist.py: capturas "
        "duplicadas, dos :str seguidos, tipo de sub no soportado y label del es "
        "que no existe en el en. Si cambia, classify() puede clasificar mal."),
    "parsePattern": (
        "4db00fe7a0605795",
        "define qué es una captura en el lado en. classify() da por supuesto "
        "que la forma es <nombre:tipo> y nada más."),
    "parseReplacement": (
        "ce06a7fec757bbc2",
        "define qué es una captura en el lado traducido, donde el tipo es "
        "opcional (<nombre> o <nombre:flag>)."),
    "translate": (
        "7e16a34e55acbfbd",
        "el preload mod_battle_brothers_es.nut la envuelve con memoria: da por "
        "supuestos su firma (_str, _id, _skip_rule) y que el resultado solo "
        "depende del texto durante una llamada. Si upstream añade memoria "
        "propia o cambia la firma, el envoltorio sobra o pierde argumentos."),
}
PIN_REF = "dde98e9"
"""Ref de upstream del que salieron los hashes de PINES. En la adopción de la
0.5.0 (dde98e9) ninguno de los tres contratos se movió: el cambio del runtime
fue la regex de :val (separador de miles), que no toca ni los nombres de sub
ni validateRule, así que los hashes se conservan y solo sube la referencia."""

VERSION_ESPERADA = "0.5.0"
"""La que el pack exige en su cabecera. Un runtime más nuevo no rompe nada; que
el runtime declare MENOS que esto sí, porque el pack no cargaría."""


def lee_runtime(origen=None, ref=None):
    """El texto del runtime, del árbol de trabajo o de una rama."""
    if ref:
        try:
            return subprocess.run(
                ["git", "-C", str(REPO), "show", f"{ref}:{RUNTIME_REL}"],
                capture_output=True, text=True, check=True,
                encoding="utf-8").stdout, f"{ref}:{RUNTIME_REL}"
        except subprocess.CalledProcessError as e:
            raise SystemExit("no puedo leer %s en %s: %s"
                             % (RUNTIME_REL, ref, e.stderr.strip()))
    ruta = Path(origen) if origen else VENDOR / RUNTIME_REL
    if not ruta.is_file():
        raise SystemExit(
            "no encuentro el runtime en %s. Pásame la ruta al !rosetta.nut, o "
            "--ref <rama> si está en una rama de este repositorio." % ruta)
    return ruta.read_text(encoding="utf-8", errors="replace"), str(ruta)


def subs_del_runtime(texto):
    """Los tipos de sub que el runtime admite, derivados de su tabla subRes.

    Si upstream reestructura ese bloque, esto falla en vez de devolver un
    conjunto a medias: un espejo que se queda corto en silencio es peor que un
    error, porque manda pares buenos a cuarentena sin decir nada.
    """
    bloque = re.search(r"subRes\s*=\s*\(function\s*\(\)\s*\{(.*?)\n    \}\)\(\)",
                       texto, re.S)
    if not bloque:
        raise SystemExit("no localizo el bloque subRes en el runtime: upstream "
                         "lo ha reestructurado y hay que revisar este parser")
    cuerpo = bloque.group(1)
    tabla = re.search(r"local\s+res\s*=\s*\{(.*?)\n\s*\}", cuerpo, re.S)
    if not tabla:
        raise SystemExit("localizo subRes pero no su tabla res: revisar este "
                         "parser contra el runtime nuevo")
    tipos = set(re.findall(r"^\s*(\w+)\s*=", tabla.group(1), re.M))
    # los derivados: res[key + "_tag"] para cada key de una lista foreach
    for sufijo in re.findall(r'res\[key\s*\+\s*"(\w+)"\]', cuerpo):
        for lista in re.findall(r"foreach\s*\(\s*key\s+in\s*\[([^\]]*)\]", cuerpo):
            tipos |= {k + sufijo for k in re.findall(r'"(\w+)"', lista)}
    return tipos


def cuerpo_de(texto, nombre):
    """El cuerpo de una función del runtime, normalizado de espacios."""
    m = re.search(r"\n    function %s\b.*?\n    \}" % re.escape(nombre),
                  texto, re.S)
    if not m:
        return None
    return re.sub(r"\s+", " ", m.group(0)).strip()


def huella(cuerpo):
    return hashlib.sha256(cuerpo.encode("utf-8")).hexdigest()[:16]


def version_declarada(texto):
    m = re.search(r'^\s*Version\s*=\s*"([^"]+)"', texto, re.M)
    return m.group(1) if m else None


def revisa(texto):
    """Lista de (clase, qué, detalle) con lo que se ha movido."""
    avisos = []

    from build_dist import SUBS
    del_runtime = subs_del_runtime(texto)
    if del_runtime != SUBS:
        faltan = del_runtime - SUBS
        sobran = SUBS - del_runtime
        detalle = []
        if faltan:
            detalle.append("el runtime admite y build_dist no conoce: %s "
                           "(se están mandando a cuarentena pares válidos)"
                           % ", ".join(sorted(faltan)))
        if sobran:
            detalle.append("build_dist cree soportados y el runtime no: %s "
                           "(se distribuirían pares que el runtime rechaza al "
                           "cargar, y eso aborta la traducción entera)"
                           % ", ".join(sorted(sobran)))
        avisos.append(("ESPEJO", "SUBS en build_dist.py", "; ".join(detalle)))

    for nombre, (pin, porque) in PINES.items():
        cuerpo = cuerpo_de(texto, nombre)
        if cuerpo is None:
            avisos.append(("AUSENTE", nombre,
                           "ya no existe con ese nombre en el runtime. %s" % porque))
            continue
        actual = huella(cuerpo)
        if actual != pin:
            avisos.append(("CONTRATO", nombre,
                           "cambió (%s -> %s). %s" % (pin, actual, porque)))

    v = version_declarada(texto)
    if v is None:
        avisos.append(("VERSION", "Version", "no la encuentro en el runtime"))
    elif v != VERSION_ESPERADA:
        avisos.append(("VERSION", "Version",
                       "el runtime declara %s y el pack exige %s en su "
                       "cabecera. Si es mayor, no rompe nada y toca revisar "
                       "qué trae la versión; si es menor, el pack no cargaría."
                       % (v, VERSION_ESPERADA)))
    return avisos


def main(argv):
    ref = None
    if "--ref" in argv:
        i = argv.index("--ref")
        if i + 1 >= len(argv):
            raise SystemExit("--ref necesita una rama")
        ref = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    origen = argv[0] if argv else None

    texto, de_donde = lee_runtime(origen, ref)
    avisos = revisa(texto)

    print("runtime:  %s" % de_donde)
    print("pines de: %s" % PIN_REF)
    if not avisos:
        print()
        print("Nada de lo que el pack replica se ha movido.")
        return 0

    print()
    for clase, que, detalle in avisos:
        print("%s  %s" % (clase, que))
        print("   %s" % detalle)
        print()
    print("%d aviso(s). Esto no significa que algo esté roto: significa que hay"
          % len(avisos))
    print("que ir a leerlo. Si no nos afecta, se actualiza el pin de este")
    print("fichero con el motivo, en el mismo commit que adopta la versión.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
