"""Barrido D: la capa de interfaz en JavaScript.

Las tres clases de cobertura.py miran el lado Squirrel. Pero una parte de los
rotulos del juego (botones, titulos de columna, mensajes fijos) esta escrita a
mano en los .js de la interfaz, que Rosetta NO puede tocar: solo se traducen
sustituyendo el fichero entero, que es lo que hace el addon de ui del pack.

Este barrido saca de cada .js del juego los literales que parecen texto de
usuario, mira si el pack sustituye ese fichero y, si lo sustituye, si el
literal sigue en ingles. Lo que salga es rotulo que el jugador ve en ingles.

Uso: PYTHONUTF8=1 uv run python es_pack/tools/cobertura_js.py [-v]
"""
import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
from rutas import DATA  # noqa: E402  ver rutas.py
ADDON = REPO / "es_pack" / "src" / "ui"

# texto entre etiquetas de plantilla: <div ...>Texto</div>
ENTRE = re.compile(r">([A-Z][A-Za-z0-9 ,.:!?'()/-]{2,60})<")
# literales sueltos con pinta de frase
SUELTO = re.compile(r"['\"]([A-Z][a-z]+(?: [A-Za-z0-9,.:!?'()-]+){1,12})['\"]")
# lo que no es texto de usuario aunque lo parezca
RUIDO = re.compile(r"^(Div|Span|Class|Id|Src|Href|Px|Rgb|True|False|Null|Undefined|Function|Object|Array|"
                   r"String|Number|Boolean|Error|Warning|Debug|Info)\b|"
                   r"^[A-Z][a-z]+([A-Z][a-z]+)+$|\.(png|jpg|css|js|html)$|^ui/|^gfx/")


def literales(txt):
    """devuelve (texto, forma) donde forma dice como aparecia: entre etiquetas
    o entre comillas. Hay que conservarlo: el mismo texto puede ser rotulo en
    un sitio y clave de datos en otro (if ('Stash' in _data)), y compararlos
    sin distinguir da falsos positivos."""
    out = {}
    for rx, forma in ((ENTRE, "tag"), (SUELTO, "cita")):
        for m in rx.finditer(txt):
            s = m.group(1).strip()
            if len(s) < 3 or RUIDO.search(s):
                continue
            if not re.search(r"[a-z]", s):
                continue
            out.setdefault(s, forma)
    return list(out.items())


def main():
    verbose = "-v" in sys.argv
    z = zipfile.ZipFile(DATA / "data_001.dat")
    js = [n for n in z.namelist() if n.endswith(".js") and n.startswith("ui/")]
    nuestros = {str(p.relative_to(ADDON).as_posix()): p for p in ADDON.rglob("*.js")}

    tot_lit = tot_sin = ficheros = 0
    sin_cubrir = {}
    for n in sorted(js):
        rel = n[3:]  # quita "ui/"
        txt = z.read(n).decode("utf-8", "replace")
        lits = literales(txt)
        if not lits:
            continue
        tot_lit += len(lits)
        if rel in nuestros:
            mio = nuestros[rel].read_text(encoding="utf-8", errors="replace")
            quedan = []
            for s, forma in lits:
                sigue = ((">" + s + "<") in mio if forma == "tag"
                         else ("'" + s + "'") in mio or ('"' + s + '"') in mio)
                if sigue:
                    quedan.append(s)
        else:
            quedan = [s for s, _ in lits]
        ficheros += 1
        if quedan:
            tot_sin += len(quedan)
            sin_cubrir[rel] = (rel in nuestros, quedan)

    print(f"ficheros .js del juego con texto: {ficheros}")
    print(f"literales de usuario detectados:  {tot_lit}")
    print(f"   sustituidos por el addon:      {tot_lit - tot_sin}")
    print(f"   EN INGLES todavia:             {tot_sin}\n")
    for rel in sorted(sin_cubrir, key=lambda k: -len(sin_cubrir[k][1])):
        tenemos, quedan = sin_cubrir[rel]
        marca = "(fichero ya sustituido)" if tenemos else ""
        print(f"  {rel}  {len(quedan)} {marca}")
        if verbose or len(quedan) <= 6:
            for s in quedan[:12]:
                print(f"       {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
