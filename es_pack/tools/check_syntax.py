"""Comprobacion de sintaxis Squirrel del pack generado.

El Makefile del proyecto original hace `squirrel -c` sobre cada .nut, pero
aqui no habia interprete instalado, asi que ese paso se venia saltando. Si
hay uno disponible se usa; si no, se avisa y no se bloquea nada.

El interprete que sirve es el Squirrel 3.0.7 que acompania a las herramientas
de descompilado del juego (sq.exe). Se busca en este orden:
  1. variable de entorno SQ_BIN
  2. sq.exe / squirrel en el PATH
  3. rutas conocidas del arbol de herramientas del juego

Uso directo:  uv run python es_pack/tools/check_syntax.py [fichero.nut ...]
Sin argumentos comprueba los artefactos que genera build_dist.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BUILD = REPO / "es_pack" / "build"

from rutas import HERRAMIENTAS  # noqa: E402  ver rutas.py
RUTAS_CONOCIDAS = [HERRAMIENTAS / "sq.exe"]


def es_squirrel(ruta):
    try:
        r = subprocess.run([str(ruta), "-v"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return False
    return "Squirrel" in (r.stdout + r.stderr)


def localiza_interprete():
    ruta = os.environ.get("SQ_BIN")
    if ruta and Path(ruta).is_file():
        return Path(ruta)
    for nombre in ("sq", "sq.exe", "squirrel", "squirrel.exe"):
        encontrado = shutil.which(nombre)
        # Otros programas se llaman igual (el squirrel.exe de los instaladores
        # de Electron, el sq de Sequoia PGP en Debian): solo vale si dice serlo.
        if encontrado and es_squirrel(encontrado):
            return Path(encontrado)
    for ruta in RUTAS_CONOCIDAS:
        if ruta.is_file():
            return ruta
    return None


def comprueba(ficheros, interprete=None):
    """Devuelve (interprete, [(fichero, salida_de_error)]).

    Si no hay interprete, devuelve (None, []) y el que llama decide.
    """
    interprete = interprete or localiza_interprete()
    if interprete is None:
        return None, []
    fallos = []
    with tempfile.TemporaryDirectory() as tmp:
        salida = Path(tmp) / "out.cnut"
        for f in ficheros:
            if not Path(f).is_file():
                fallos.append((str(f), "no existe"))
                continue
            r = subprocess.run(
                [str(interprete), "-c", "-o", str(salida), str(f)],
                capture_output=True, text=True, errors="replace")
            if r.returncode != 0 or "ERROR" in (r.stdout + r.stderr).upper():
                fallos.append((str(f), (r.stdout + r.stderr).strip()[:400]))
    return interprete, fallos


def artefactos():
    # Los preloads del build salen de todo lo copiado desde src/scripts, no de
    # una lista fija: asi los hooks nuevos entran solos en la comprobacion.
    if (BUILD / "scripts").is_dir():
        preloads = sorted((BUILD / "scripts").rglob("*.nut"))
    else:
        preloads = [BUILD / "scripts" / "!mods_preload" / "mod_battle_brothers_es.nut"]
    return [BUILD / "mod_battle_brothers_es" / "base_es.nut",
            BUILD / "mod_battle_brothers_es" / "ids_es.nut"] + preloads + [
        BUILD / "patterns_wip.nut",
    ]


def main():
    ficheros = [Path(a) for a in sys.argv[1:]] or artefactos()
    interprete, fallos = comprueba(ficheros)
    if interprete is None:
        print("sintaxis: sin interprete Squirrel disponible, no se comprueba")
        print("  (indica uno con SQ_BIN=/ruta/a/sq.exe)")
        return 0
    print("sintaxis: %s" % interprete.name)
    for f, err in fallos:
        print("  FALLA %s\n    %s" % (Path(f).name, err))
    if not fallos:
        print("  %d ficheros compilan" % len(ficheros))
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
