"""Saca las cadenas de un .cnut del juego, sin depender del arbol descompilado.

Los .cnut vienen cifrados dentro de los .dat; bbsq.exe -d los descifra en
sitio, y a partir de ahi el bytecode de Squirrel guarda cada literal como
longitud (4 bytes little endian) mas el texto. Eso es todo lo que hace falta
para comparar el corpus con EL JUEGO en vez de con el arbol de referencia, que
es un espejo que puede quedarse viejo (asi se perdieron los cinco ficheros de
DLC y este evento del origen cultista).

Uso:
    PYTHONUTF8=1 uv run python es_pack/tools/cnut_strings.py <ruta/en/el/dat>
    PYTHONUTF8=1 uv run python es_pack/tools/cnut_strings.py --todos > salida.tsv

Requiere bbsq.exe, que vive con las herramientas de descompilado del juego.
"""
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from rutas import DATA, HERRAMIENTAS as BIN  # noqa: E402  ver rutas.py
BBSQ = BIN / "bbsq.exe"


def descifrar(datos):
    """bbsq -d trabaja en sitio, asi que se le da una copia temporal"""
    tmp = Path(tempfile.mkdtemp(prefix="cnut_"))
    try:
        p = tmp / "x.cnut"
        p.write_bytes(datos)
        r = subprocess.run([str(BBSQ), "-d", str(p)], capture_output=True, cwd=str(BIN))
        if r.returncode != 0:
            return None
        return p.read_bytes()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


IMPRIMIBLE = re.compile(rb"[\x09\x0a\x0d\x20-\x7e\x80-\xff]{2,}")


def cadenas(datos):
    """literales con su longitud delante, que es como los guarda Squirrel"""
    out, vistos = [], set()
    for m in IMPRIMIBLE.finditer(datos):
        ini, fin = m.span()
        # la longitud puede estar en cualquier posicion previa del bloque
        for desp in range(0, min(64, fin - ini)):
            pos = ini + desp
            if pos < 4:
                continue
            largo = struct.unpack_from("<i", datos, pos - 4)[0]
            if 2 <= largo <= fin - pos:
                s = datos[pos:pos + largo]
                try:
                    txt = s.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                if txt not in vistos:
                    vistos.add(txt)
                    out.append(txt)
    return out


def del_dat(ruta):
    for dat in sorted(DATA.glob("data_*.dat")):
        with zipfile.ZipFile(dat) as z:
            if ruta in z.namelist():
                return z.read(ruta)
    return None


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    if sys.argv[1] == "--todos":
        for dat in sorted(DATA.glob("data_*.dat")):
            with zipfile.ZipFile(dat) as z:
                for n in z.namelist():
                    if not n.endswith(".cnut"):
                        continue
                    d = descifrar(z.read(n))
                    if d is None:
                        print(f"{n}\tERROR", file=sys.stderr)
                        continue
                    for s in cadenas(d):
                        if len(s) > 3 and " " in s:
                            print(f"{n}\t{s}".replace("\n", "\\n"))
        return 0
    datos = del_dat(sys.argv[1])
    if datos is None:
        print("no esta en ningun .dat:", sys.argv[1])
        return 1
    d = descifrar(datos)
    if d is None:
        print("bbsq no pudo descifrarlo")
        return 1
    for s in cadenas(d):
        print(repr(s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
