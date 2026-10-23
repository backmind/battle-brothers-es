"""Construye el zip del modo de depuración, solo para las pruebas.

Uso:
    PYTHONUTF8=1 uv run python es_pack/tools/build_depuracion.py

Lee     es_pack/depuracion/**
Escribe es_pack/build/mod_battle_brothers_es_depuracion.zip

Con el zip en data, cada texto visible en pantalla que parezca inglés sale una
vez en el log como «[es-depuracion] ...», pase o no por Rosetta. No forma parte
de la release: se quita de data para jugar normal.
"""
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ORIGEN = RAIZ / "depuracion"
DESTINO = RAIZ / "build" / "mod_battle_brothers_es_depuracion.zip"


def main():
    DESTINO.parent.mkdir(exist_ok=True)
    ficheros = sorted(p for p in ORIGEN.rglob("*") if p.is_file())
    with zipfile.ZipFile(DESTINO, "w", zipfile.ZIP_DEFLATED) as z:
        for p in ficheros:
            z.write(p, p.relative_to(ORIGEN).as_posix())
    print("zip:", DESTINO, "(%d ficheros)" % len(ficheros))


if __name__ == "__main__":
    main()
