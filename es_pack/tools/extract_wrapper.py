"""OBSOLETO desde el 18 de agosto de 2026, se conserva como referencia historica.

Upstream arreglo el bug en b671320 ("fix empty _code for a lone string, no crash
anymore on -r"), construyendo bien el slice de codigo en vez de tolerar el vacio.
Comprobado sobre el caso que lo motivo: rosetta.py pelado procesa los 45 ficheros
de settlements/situations sin abortar y su salida es byte a byte identica a la de
este wrapper. Usa rosetta.py directamente en regeneraciones nuevas.

Lanzador de rosetta.py con workaround para un bug upstream:
_prepare_code(code) crashea con min() sobre lista vacia cuando un bloque
de referencia se refresca con _code vacio, y el fichero entero pierde la
extraccion. Aqui se parchea en memoria (el fichero upstream no se toca);
el bug se reportara upstream. Uso identico a rosetta.py:

    PYTHONUTF8=1 uv run python es_pack/tools/extract_wrapper.py <dir> -les -r <ref> -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "vendor" / "rosetta"))
import rosetta

_orig_prepare_code = rosetta._prepare_code


def _safe_prepare_code(code):
    if not code:
        return ""
    return _orig_prepare_code(code)


rosetta._prepare_code = _safe_prepare_code

if __name__ == "__main__":
    rosetta.main()
