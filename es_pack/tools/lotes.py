"""Prepara la traducción por lotes de un mod grande (hoy, Legends).

Uso:
    PYTHONUTF8=1 uv run python es_pack/tools/lotes.py extraer [--forzar]

  extraer   clona la fuente fijada en es_pack/legends/fuente.toml, saca el
            corpus con el extractor de Rosetta y criba lo que ya traduce
            base_es.nut: Rosetta tiene una sola tabla por idioma con el `en`
            como clave, así que un `en` repetido entre corpus sobra en el
            mejor caso y, en el peor, pisa al del base (ver el spec).

El corpus resultante es la fuente de verdad; todo se escribe por bytes y en LF.
"""
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_dist import CORPUS, REPO, get_field, load_blocks  # noqa: E402

LEGENDS = REPO / "es_pack" / "legends"
FUENTE_TOML = LEGENDS / "fuente.toml"
FUENTE = LEGENDS / "fuente"
LOTES = LEGENDS / "lotes"
CORPUS_LEGENDS = REPO / "es_pack" / "corpus" / "mod_legends_es.nut"
ROSETTA_PY = REPO / "vendor" / "rosetta" / "rosetta.py"
SIN_COMMIT = "<sin fijar>"

FILE_RE = re.compile(r"^\s*// FILE: (.+)$")
EN_LINEA_RE = re.compile(r'^\s*en = ("(?:[^"\\]|\\.)*")\s*$', re.M)
CABECERA_MOD_RE = re.compile(r'mod = \{id = "mod_", version = "\.\.\."\}')


@dataclass
class Bloque:
    file: str
    inicio: int  # líneas inicio..fin inclusive, 0-based, del texto partido por \n
    fin: int
    texto: str
    en: str | None
    es: str | None


def bloques(texto):
    """Los pares del corpus con el `// FILE:` del que salen.

    Cuenta con el formato que emite el extractor: cada par abre con una línea
    que es exactamente "    {" y cierra con la siguiente "    }".
    """
    lineas = texto.split("\n")
    res, file, inicio = [], "?", None
    for i, linea in enumerate(lineas):
        if inicio is None:
            m = FILE_RE.match(linea)
            if m:
                file = m.group(1).strip()
            elif linea == "    {":
                inicio = i
        elif linea == "    }":
            t = "\n".join(lineas[inicio:i + 1])
            res.append(Bloque(file, inicio, i, t, get_field(t, "en"), get_field(t, "es")))
            inicio = None
    return res


def duplicados(texto):
    cuenta = Counter(b.en for b in bloques(texto) if b.en is not None)
    return sorted(en for en, n in cuenta.items() if n > 1)


def ens_base():
    return {get_field(b, "en") for b in load_blocks(CORPUS)} - {None}


def cribar(texto, base):
    """Cambia por `// en = "..."` cada par cuyo `en` ya traduce base_es.nut."""
    lineas = texto.split("\n")
    n = 0
    for b in reversed(bloques(texto)):
        if b.en in base:
            literal = EN_LINEA_RE.search(b.texto).group(1)
            lineas[b.inicio:b.fin + 1] = ["    // en = %s" % literal, "    // en base_es"]
            n += 1
    return "\n".join(lineas), n


def desverbatim(codigo):
    """Pasa cada cadena verbatim de Squirrel (@"...", con "" por comilla y
    saltos de línea reales) a una cadena normal equivalente.

    shortcut: el extractor de Rosetta 0.5.0 no tokeniza @"..." y descarta el
    fichero entero (perk_strings.nut, runes_*.nut); quitar esto cuando
    upstream lo soporte.
    """
    out, i, n = [], 0, len(codigo)
    while i < n:
        c = codigo[i]
        if codigo.startswith("//", i) or codigo.startswith("#", i):
            fin = codigo.find("\n", i)
            fin = n if fin < 0 else fin
        elif codigo.startswith("/*", i):
            fin = codigo.find("*/", i + 2)
            fin = n if fin < 0 else fin + 2
        elif c in "\"'":
            fin = i + 1
            while fin < n and codigo[fin] != c:
                fin += 2 if codigo[fin] == "\\" else 1
            fin += 1
        elif codigo.startswith('@"', i):
            j, cuerpo = i + 2, []
            while j < n:
                if codigo[j] == '"':
                    if codigo.startswith('""', j):
                        cuerpo.append('"')
                        j += 2
                        continue
                    break
                cuerpo.append(codigo[j])
                j += 1
            texto = "".join(cuerpo).replace("\r\n", "\n")
            texto = (texto.replace("\\", "\\\\").replace('"', '\\"')
                     .replace("\n", "\\n").replace("\t", "\\t"))
            out.append('"%s"' % texto)
            i = j + 1
            continue
        else:
            fin = i + 1
        out.append(codigo[i:fin])
        i = fin
    return "".join(out)


def copia_extraible(origen, destino, rutas):
    """Copia los .nut de la fuente con las cadenas verbatim convertidas."""
    for ruta in rutas:
        for f in (origen / ruta).rglob("*.nut"):
            dest = destino / f.relative_to(origen)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(desverbatim(f.read_bytes().decode("utf-8")).encode("utf-8"))


def escribir(path, texto):
    path.write_bytes(texto.replace("\r\n", "\n").encode("utf-8"))


def git(*args):
    subprocess.run(["git", *args], check=True)


def extraer(forzar):
    if CORPUS_LEGENDS.exists() and not forzar:
        hechos = [b for b in bloques(CORPUS_LEGENDS.read_text(encoding="utf-8")) if b.es]
        if hechos:
            sys.exit("%s ya tiene %d pares traducidos; re-extraer los perdería (--forzar para hacerlo igualmente)"
                     % (CORPUS_LEGENDS.name, len(hechos)))

    fuente = tomllib.loads(FUENTE_TOML.read_text(encoding="utf-8"))
    if not FUENTE.exists():
        git("clone", "--depth", "1", "--branch", fuente["etiqueta"], "--filter=blob:none",
            "--sparse", fuente["repo"], str(FUENTE))
        git("-C", str(FUENTE), "sparse-checkout", "set", *fuente["rutas"])
    head = subprocess.run(["git", "-C", str(FUENTE), "rev-parse", "HEAD"],
                          check=True, capture_output=True, text=True).stdout.strip()
    if head != fuente["commit"]:
        sys.exit("la fuente está en %s y fuente.toml fija %s; fija el commit o borra %s"
                 % (head, fuente["commit"], FUENTE))

    # Se extrae desde dentro de la copia con "." para que los // FILE: queden
    # relativos (scripts\...), como en base_es.nut, y no con la ruta local.
    with tempfile.TemporaryDirectory() as tmp:
        copia_extraible(FUENTE, Path(tmp), fuente["rutas"])
        salida = subprocess.run(
            [sys.executable, str(ROSETTA_PY), ".", "-les", "-r", str(CORPUS)],
            cwd=tmp, capture_output=True, env={**os.environ, "PYTHONUTF8": "1"})
    sys.stderr.write(salida.stderr.decode("utf-8", "replace"))
    if salida.returncode:
        sys.exit("el extractor terminó con código %d" % salida.returncode)
    texto = salida.stdout.decode("utf-8").replace("\r\n", "\n")
    texto, n = CABECERA_MOD_RE.subn(
        'mod = {id = "%s", version = "%s"}' % (fuente["mod_id"], fuente["etiqueta"]), texto)
    assert n == 1, "la cabecera del extractor ha cambiado"

    total = len(bloques(texto))
    texto, cribados = cribar(texto, ens_base())
    # Con -r, pistas de código distintas confluyen en el mismo patrón del base
    # (hasta base_es.nut lo repite); esos caen en la criba. Lo que la fusión
    # necesita único es lo que queda.
    dups = duplicados(texto)
    if dups:
        print("\n".join(dups[:20]))
        sys.exit("%d `en` repetidos tras la criba; la fusión los necesita únicos" % len(dups))
    resto = bloques(texto)
    escribir(CORPUS_LEGENDS, texto)
    print("pares totales: %d" % total)
    print("cribados (en base_es): %d" % cribados)
    print("pendientes (es vacío): %d" % sum(1 for b in resto if not b.es))
    print("ya con es: %d" % sum(1 for b in resto if b.es))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["extraer"]:
        extraer(forzar="--forzar" in argv)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
