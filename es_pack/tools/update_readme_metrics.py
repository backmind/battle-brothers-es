"""Rellena las cifras del README de portada desde el corpus real.

Mantiene dos bloques de README.md, cada uno entre sus marcadores:

- INSIGNIAS: la primera fila de badges. Las que dependen del repo (build del
  juego verificada, cobertura) salen de las constantes de build_dist.py, las
  mismas que lee la ficha de MSU; las dinámicas (última versión del juego,
  versión del pack, descargas) las resuelve shields.io al mostrarse.
- OBJETIVOS: la tabla "Qué se traduce", una fila por juego o mod traducido,
  sacada de la lista OBJETIVOS de este fichero. De la misma lista salen los
  badges de cobertura de la fila de INSIGNIAS.
- METRICAS: el cuadro de cifras del corpus, contado con el mismo clasificador
  que usa el build.

Así el README nunca miente por desactualización: las cifras salen del corpus
del commit, sin mano humana.

Uso:
    PYTHONUTF8=1 uv run python es_pack/tools/update_readme_metrics.py
    PYTHONUTF8=1 uv run python es_pack/tools/update_readme_metrics.py --check

Sin argumentos reescribe el bloque si ha cambiado. Con --check no escribe:
devuelve 1 si el bloque está desactualizado, que es lo que ejecuta la CI
para impedir que un cambio de corpus llegue sin su cuadro al día.
"""
import re
import sys
from pathlib import Path
from urllib.parse import quote

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "es_pack" / "tools"))

import build_dist

README = REPO / "README.md"
INICIO = "<!-- METRICAS:INICIO"
FIN = "<!-- METRICAS:FIN -->"
INICIO_INS = "<!-- INSIGNIAS:INICIO"
FIN_INS = "<!-- INSIGNIAS:FIN -->"
INICIO_OBJ = "<!-- OBJETIVOS:INICIO"
FIN_OBJ = "<!-- OBJETIVOS:FIN -->"
REPO_GH = "backmind/battle-brothers-es"

# Lo que traduce el pack, uno por juego o mod. Cuando entre la traducción de un
# mod, se añade aquí con sus constantes en build_dist.py, igual que el juego
# base: la tabla del README, su badge y la ficha de MSU salen de lo mismo.
OBJETIVOS = [
    {
        "nombre": "Battle Brothers y sus expansiones",
        "badge": "juego base + DLC",
        "estado": "Disponible",
        "verificada": "Battle Brothers " + build_dist.GAME_VERSION,
        "cobertura": build_dist.COBERTURA_JUEGO,
    },
]
GOG_BUILDS = ("https://content-system.gog.com/products/1590012242/os/windows/"
              "builds?generation=2")


def n(v):
    """Número con separador de miles en estilo español."""
    return format(v, ",d").replace(",", ".")


def medidas():
    bloques = build_dist.load_blocks(build_dist.CORPUS)
    cubos = {"dist": [], "wip": [], "drop": []}
    for b in bloques:
        cubos[build_dist.classify(b)].append(b)
    patrones = sum(1 for b in cubos["dist"] if build_dist.is_rule_pair(b))
    composicion = sum(1 for b in cubos["dist"] if "@composicion" in b)
    corpus = build_dist.CORPUS.read_text(encoding="utf-8")
    internos = len(re.findall(r"^\s*// en = ", corpus, re.M))
    ids = build_dist.IDS.read_text(encoding="utf-8").count('{id = "scripts/')
    # ui/mods/ son scripts propios, no módulos del juego traducidos.
    ui = REPO / "es_pack" / "src" / "ui"
    js = sum(1 for p in ui.rglob("*.js") if p.relative_to(ui).parts[0] != "mods")
    return [
        ("Pares distribuidos", n(len(cubos["dist"]))),
        ("De ellos, patrones con variables", n(patrones)),
        ("De ellos, nacidos fuera de la extracción (composición, MSU, QA)", n(composicion)),
        ("Pares por id (homógrafos)", n(ids)),
        ("En cuarentena de patrones", n(len(cubos["wip"]))),
        ("Sin traducir", n(len(cubos["drop"]))),
        ("Claves internas adjudicadas", n(internos)),
        ("Módulos de interfaz traducidos", n(js)),
    ]


def bloque():
    filas = "\n".join("| %s | %s |" % (k, v) for k, v in medidas())
    return (
        "%s (autogenerado por es_pack/tools/update_readme_metrics.py; "
        "no editar a mano) -->\n"
        "| | |\n|---|---|\n%s\n%s" % (INICIO, filas, FIN)
    )


def estatica(etiqueta, valor, color):
    """URL de un badge estático de shields.io, con su escapado propio."""
    def esc(s):
        return quote(s.replace("-", "--").replace("_", "__"), safe="")
    return "https://img.shields.io/badge/%s-%s-%s" % (esc(etiqueta), esc(valor), color)


def insignias():
    """La primera fila de badges: lo que el jugador quiere saber de un vistazo."""
    gog = ("https://img.shields.io/badge/dynamic/json?url=%s&query=%s"
           "&label=%s&color=1565c0" % (quote(GOG_BUILDS, safe=""),
                                       quote("$.items[0].version_name", safe=""),
                                       quote("última del juego", safe="")))
    return [
        ("Versión del pack",
         "https://img.shields.io/github/v/release/%s?label=%s&color=8b0000"
         % (REPO_GH, quote("versión", safe="")),
         "https://github.com/%s/releases/latest" % REPO_GH),
        ("Verificada en Battle Brothers " + build_dist.GAME_VERSION,
         estatica("verificada en", "Battle Brothers " + build_dist.GAME_VERSION, "2e7d32"),
         "#qué-se-traduce"),
        ("Última versión del juego en GOG", gog,
         "https://www.gog.com/game/battle_brothers"),
    ] + [
        ("%s: %s" % (o["nombre"], o["cobertura"]),
         estatica(o["badge"], o["cobertura"], "2e7d32"), "#qué-se-traduce")
        for o in OBJETIVOS
    ] + [
        ("Descargas",
         "https://img.shields.io/github/downloads/%s/total?label=descargas&color=555" % REPO_GH,
         "https://github.com/%s/releases" % REPO_GH),
    ]


def bloque_objetivos():
    filas = "\n".join("| %s | %s | %s | %s |" % (o["nombre"], o["estado"], o["verificada"], o["cobertura"])
                       for o in OBJETIVOS)
    return ("%s (autogenerado por es_pack/tools/update_readme_metrics.py; "
            "no editar a mano) -->\n"
            "| Qué | Estado | Verificada en | Frases cubiertas |\n|---|---|---|---|\n%s\n%s"
            % (INICIO_OBJ, filas, FIN_OBJ))


def bloque_insignias():
    lineas = "\n".join("[![%s](%s)](%s)" % i for i in insignias())
    return ("%s (autogenerado por es_pack/tools/update_readme_metrics.py; "
            "no editar a mano) -->\n%s\n%s" % (INICIO_INS, lineas, FIN_INS))


def sustituye(texto, inicio, fin, contenido):
    i = texto.find(inicio)
    f = texto.find(fin)
    if i < 0 or f < 0:
        raise SystemExit("README.md no tiene los marcadores %s" % inicio[5:])
    return texto[:i] + contenido + texto[f + len(fin):]


def main(argv):
    texto = README.read_text(encoding="utf-8")
    nuevo = sustituye(texto, INICIO, FIN, bloque())
    nuevo = sustituye(nuevo, INICIO_INS, FIN_INS, bloque_insignias())
    nuevo = sustituye(nuevo, INICIO_OBJ, FIN_OBJ, bloque_objetivos())
    if nuevo == texto:
        print("el cuadro ya está al día")
        return 0
    if "--check" in argv:
        print("el cuadro de métricas del README está DESACTUALIZADO; "
              "pasa update_readme_metrics.py y commitea el resultado")
        return 1
    README.write_text(nuevo, encoding="utf-8", newline="")
    print("cuadro actualizado")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
