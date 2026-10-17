"""Avisa de cuándo el juego se ha movido por debajo de la capa JS.

El problema que resuelve: los pares del corpus son una dependencia blanda. Si el
juego cambia, Rosetta deja las frases nuevas en inglés y no se rompe nada. Los
`.js` de `src/ui/` son lo contrario, una dependencia dura: **sustituyen**
ficheros del juego, así que una actualización que toque uno de esos módulos
queda tapada en silencio por nuestra copia, más vieja. No hay aviso, no hay
error en el log, y lo que se pierde es funcionalidad.

Que eso no es teórico ya está comprobado: de los 38 módulos que traía
`trad303.zip`, 37 seguían cuadrando con el juego actual y uno no, el reloj de la
barra superior, al que le faltaba el cuarto botón de velocidad del mapa entero.
Se jugó una partida sin ese botón sin que nadie lo notara.

Uso:
    PYTHONUTF8=1 uv run python es_pack/tools/check_ui_drift.py <ruta>
    PYTHONUTF8=1 uv run python es_pack/tools/check_ui_drift.py <ruta> --detalle

`<ruta>` es la carpeta `data` del juego o directamente el `.dat` que lleva el
`ui/` (hoy `data_001.dat`). Sin argumento se usa DATA_DIR del `.env` si lo hay.

Devuelve 0 si la capa sigue cuadrando y 1 si hay algo que mirar, para poder
ponerlo delante de una release.

## Cómo distingue traducción de código

Sustituye cada literal de cadena por un marcador y normaliza los espacios: lo
que quede de diferencia es código. Traducir cambia literales, y eso no cuenta
como divergencia; que a nuestra copia le falten líneas que el juego sí tiene,
sí.

Los avisos CODIGO con cuentas pequeñas y simétricas suelen ser ruido del
alineamiento del diff cuando una línea traducida reparte los literales de otra
manera. Por eso el aviso no dice "roto" sino "míralo": `--detalle` saca el diff
enmascarado y se juzga en segundos.
"""
import difflib
import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "es_pack" / "src" / "ui"
ENV = REPO / ".env"

# Sin DOTALL a propósito: ninguno de estos .js parte un literal en varias
# líneas, y hay 12 apóstrofos dentro de comentarios ("don't"). Con DOTALL uno de
# esos podría emparejarse con otra comilla lejana y tapar código real como si
# fuera una cadena, que es justo el falso negativo que esta herramienta existe
# para evitar. Comprobado: hoy DOTALL no cambia el enmascarado de ni un fichero.
STR_RE = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")

AUSENTE = "AUSENTE"
CODIGO = "CODIGO"
SIN_TRADUCIR = "SIN_TRADUCIR"

ACEPTADOS = {
    ("ui/screens/character/modules/character_screen_left_panel/"
     "character_screen_left_panel_header_module.js"): (
        (2, 2),
        "el traductor renombró dos claves de objeto, Hitpoints a Vida y "
        "Fatigue a Fatiga, en mLevelUpLeftStatsRows. Inofensivo y también "
        "inútil: la clave se escribe y se lee dentro del mismo fichero "
        "(data('stat', _key) en createLevelUpDialogContentRow, leída en "
        "increaseLevelUpStatValue) y nunca se muestra al jugador, que ve el "
        "icono y el tooltip. Comprobado que MSU no toca esas claves."),
    "ui/screens/world/world_obituary_screen.js": (
        (0, 8),
        "las ocho líneas de más son un comentario nuestro, no código: explica "
        "el reparto de ancho de las tres cabeceras de columna que se corrigió "
        "en la QA del 30/08. El enmascarado quita literales, no comentarios, "
        "y por eso suena. Si el juego mueve ese fichero, las cuentas cambian "
        "y el aviso vuelve."),
}
"""Avisos ya juzgados, con las cuentas que tenían al juzgarlos.

Existe para que el código de salida signifique algo: un aviso resuelto no puede
seguir sonando, o se aprende a ignorar la herramienta entera. Las cuentas van
fijadas a propósito, así que si el juego vuelve a mover ese mismo fichero, las
cuentas cambian y el aviso reaparece para que alguien lo mire de nuevo.
"""


def esqueleto(datos):
    """El fichero sin literales de cadena y sin espacios de más."""
    texto = STR_RE.sub("@S@", datos.decode("utf-8", errors="replace"))
    return [re.sub(r"\s+", " ", ln).strip()
            for ln in texto.splitlines() if ln.strip()]


def abre_datos(ruta):
    """El zip del juego que lleva ui/, sea la carpeta data o el .dat concreto."""
    p = Path(ruta)
    if p.is_dir():
        candidatos = sorted(p.glob("data_*.dat"))
        if not candidatos:
            raise SystemExit("no hay ningún data_*.dat en %s" % p)
        for c in candidatos:
            if zipfile.is_zipfile(c):
                z = zipfile.ZipFile(c)
                if any(n.startswith("ui/") for n in z.namelist()):
                    return c, z
        raise SystemExit("ninguno de los data_*.dat de %s lleva ui/" % p)
    if not p.is_file():
        raise SystemExit("no encuentro %s" % p)
    if not zipfile.is_zipfile(p):
        raise SystemExit("%s no es un archivo que se pueda abrir" % p)
    return p, zipfile.ZipFile(p)


def data_dir_del_env():
    if not ENV.is_file():
        return None
    for linea in ENV.read_text(encoding="utf-8", errors="replace").splitlines():
        if linea.startswith("DATA_DIR="):
            return linea.split("=", 1)[1].strip().replace("\\ ", " ").strip('"')
    return None


def revisa(zjuego, src=None):
    """Compara cada .js de src/ui con el del juego. Devuelve la lista de avisos."""
    src = SRC if src is None else src
    dentro = set(zjuego.namelist())
    avisos = []
    for ruta in sorted(src.rglob("*.js")):
        arco = ruta.relative_to(src.parent).as_posix()
        if arco.startswith("ui/mods/"):
            continue  # scripts propios: no sustituyen nada del juego
        if arco not in dentro:
            avisos.append((AUSENTE, arco, 0, 0))
            continue
        nuestro, suyo = ruta.read_bytes(), zjuego.read(arco)
        # Ignorando el fin de linea a proposito: un fichero que solo difiere en
        # CRLF frente a LF tampoco traduce nada, y es igual de peso muerto.
        if nuestro.replace(b"\r\n", b"\n") == suyo.replace(b"\r\n", b"\n"):
            avisos.append((SIN_TRADUCIR, arco, 0, 0))
            continue
        v, e = esqueleto(suyo), esqueleto(nuestro)
        quita = anade = 0
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
                None, v, e, autojunk=False).get_opcodes():
            if tag in ("delete", "replace"):
                quita += i2 - i1
            if tag in ("insert", "replace"):
                anade += j2 - j1
        if quita or anade:
            avisos.append((CODIGO, arco, quita, anade))
    return avisos


MOTIVOS = {
    AUSENTE: "el juego ya no tiene ese fichero: nuestra copia no sustituye nada",
    CODIGO: "el fichero del juego tiene código que nuestra copia no; míralo",
    SIN_TRADUCIR: "idéntico al del juego: ya no traduce nada, quítalo del pack",
}


def detalle(zjuego, arco):
    v = esqueleto(zjuego.read(arco))
    e = esqueleto((SRC.parent / arco).read_bytes())
    for ln in difflib.unified_diff(v, e, "juego", "pack", lineterm="", n=1):
        if ln.startswith(("+", "-", "@")):
            print("      " + ln[:160])


def esta_aceptado(clase, arco, quita, anade):
    """True si ese aviso exacto ya se juzgó, con las mismas cuentas."""
    if clase != CODIGO or arco not in ACEPTADOS:
        return False
    return ACEPTADOS[arco][0] == (quita, anade)


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    ver_detalle = "--detalle" in argv
    ruta = args[0] if args else data_dir_del_env()
    if not ruta:
        raise SystemExit(
            "dime dónde está el juego: pasa la carpeta data o el data_*.dat, "
            "o pon DATA_DIR en .env")

    fichero, zjuego = abre_datos(ruta)
    total = sum(1 for _ in SRC.rglob("*.js"))
    todos = revisa(zjuego)
    aceptados = [a for a in todos if esta_aceptado(*a)]
    avisos = [a for a in todos if not esta_aceptado(*a)]

    print("juego:  %s" % fichero)
    print("capa:   %d ficheros en %s" % (total, SRC))
    if aceptados:
        print("ya juzgados y aceptados: %d (no cuentan; ACEPTADOS en %s)"
              % (len(aceptados), Path(__file__).name))
    if not avisos:
        print()
        print("Sin divergencias nuevas: los %d cuadran con el juego." % total)
        return 0

    print()
    for clase in (AUSENTE, CODIGO, SIN_TRADUCIR):
        de_esa = [a for a in avisos if a[0] == clase]
        if not de_esa:
            continue
        print("%s (%d): %s" % (clase, len(de_esa), MOTIVOS[clase]))
        for _, arco, quita, anade in de_esa:
            cuenta = "  -%d/+%d" % (quita, anade) if clase == CODIGO else ""
            print("   %s%s" % (arco, cuenta))
            if arco in ACEPTADOS:
                print("      OJO: este fichero ya estaba juzgado con "
                      "-%d/+%d. Las cuentas han cambiado, así que el juego "
                      "lo ha vuelto a mover." % ACEPTADOS[arco][0])
            if ver_detalle and clase == CODIGO:
                detalle(zjuego, arco)
        print()
    print("%d aviso(s) nuevo(s). Nada de esto rompe el juego solo, pero cada"
          % len(avisos))
    print("uno es funcionalidad tapada o peso muerto. Cuando uno se juzgue y")
    print("resulte aceptable, su sitio es ACEPTADOS, con el motivo escrito.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
