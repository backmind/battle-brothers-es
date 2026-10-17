"""Las rutas de esta máquina: el juego instalado y las herramientas de descompilado.

Ninguna herramienta lleva una ruta de disco escrita. Se configuran en el
`.env` de la raíz del repo (hay un `.env.example`) o como variables de entorno:

    DATA_DIR         la carpeta data del juego
    BB_HERRAMIENTAS  la carpeta de las herramientas de descompilado: sq.exe,
                     bbsq.exe y comparer/ con los árboles descompilados
                     (original, original_current, spanish_tr, spanish_305)

Las herramientas que solo trabajan con el corpus (el build, los chequeos, los
tests) no necesitan nada de esto. Las demás fallan con un mensaje claro si la
ruta que piden no existe.
"""
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ENV = REPO / ".env"
SIN_CONFIGURAR = Path("<sin configurar>")


def valor(nombre):
    """La variable de entorno, o la línea NOMBRE=valor del .env, o None."""
    v = os.environ.get(nombre)
    if v:
        return v
    if ENV.is_file():
        for linea in ENV.read_text(encoding="utf-8", errors="replace").splitlines():
            if linea.startswith(nombre + "="):
                return linea.split("=", 1)[1].strip().strip('"').replace("\\ ", " ")
    return None


def ruta(nombre):
    v = valor(nombre)
    return Path(v) if v else SIN_CONFIGURAR


DATA = ruta("DATA_DIR")
HERRAMIENTAS = ruta("BB_HERRAMIENTAS")
ARBOLES = HERRAMIENTAS / "comparer"
