"""Construye el zip del addon de interfaz: la capa JS del pack en castellano.

El problema que resuelve: parte de la interfaz de Battle Brothers no la dibujan
los scripts sino módulos JavaScript, y ésos no pasan por Rosetta. Se veían en
inglés a menos que el jugador instalara a mano `trad303.zip`, el paquete de la
traducción original. Con esto el pack lleva su propia capa y no depende de esa
instalación manual.

Uso:
    PYTHONUTF8=1 uv run python es_pack/tools/build_ui_addon.py

Lee     es_pack/src/ui/**/*.js
Escribe es_pack/build/mod_battle_brothers_es_ui_<version>.zip (solo para
        revisarlo suelto: desde la 5.0.0 la release no lo publica, porque
        build_dist mete estos mismos .js en el zip del pack, con la misma
        validación de comprueba())

## El zip lleva sólo ui/, y eso no es un detalle de estilo

Aquí no entra nada que no sea `ui/`, y en particular no entran fuentes. El
juego pide dos de ellas con un `data/` de más en la ruta
(`coui://data/gfx/fonts/cinzel/...`), que sólo resuelve si el fichero está
suelto en disco: dentro de un zip no hay forma de satisfacer esa URL. Eso pasa
en el juego sin mods y no es cosa nuestra, y además las fuentes son byte a byte
las que el juego ya trae empacadas, así que el pack no tiene por qué
distribuirlas. El detalle está en `corpus/KNOWN_ISSUES.md`, «Ruido en el log».

## Esta capa es la única dependencia dura del pack

Los pares del corpus son una dependencia blanda: si el juego cambia, Rosetta
deja las frases nuevas en inglés y no rompe nada. Estos `.js` **sustituyen**
ficheros del juego, así que una actualización que toque uno de estos módulos
queda tapada en silencio por nuestra copia. Para eso está
`check_ui_drift.py`, que hay que pasar después de cada actualización del juego.

## Procedencia

Los 36 `.js` de `es_pack/src/ui/` salen de `trad303.zip`
(sha256 2aa289097ff590094eeee5b501bf9805ae7ff888ef7091b2dabebfdfb170da0b),
que traía 38. El permiso para redistribuirlos está concedido por los
mantenedores de la traducción original; los créditos están en el README.

Hubo antes un `mod_rosetta_base_es_ui_0.1.0.zip` armado a mano, con los 38, que
es el que se probó en partida el 16/08/2026. Ése no lo genera nada de aquí y su
numeración no se continúa: lleva contenido distinto (ver más abajo) y una
versión que no dice contra qué build del juego se verificó.

## Los dos que faltan, y por qué

Se compararon los 38 con el `ui/` que el juego trae hoy (`data_001.dat`),
enmascarando los literales de cadena para separar traducción de código. 36 sólo
cambian texto. De los otros dos:

  world_screen_topbar_daytime_module.js
      El de trad303 venía de antes del cuarto botón de velocidad y estuvo
      excluido por eso. El 29/08/2026 se REBASÓ: copia del fichero actual del
      juego (extraído de data_001.dat, con el botón) cambiando solo tres
      literales ("Día", "PAUSADO", "(Presiona Espacio)", los dos últimos
      calcando los pares del corpus). Vuelve a distribuirse.

  character_screen_paperdoll_module.js
      Byte a byte idéntico al del juego: no traduce ni una palabra. Sustituir
      un fichero por sí mismo no aporta nada y congela esa copia cuando el
      juego se actualice. Sigue en EXCLUIDOS para que reaparecer en `src/ui/`
      sea un fallo de construcción y no una regresión silenciosa.

Añadido el 29/08/2026, fuera de la herencia de trad303:

  controls/popup_dialog.js
      El componente compartido de los popups (desbloquear perk, subir de
      nivel): copia del fichero actual del juego con sus dos literales
      ('Aceptar', 'Cancelar'). Era la fuente de los botones "Ok"/"Cancel" en
      inglés de la QA del 28/08.

Añadido el 16/10/2026, por decisión del propietario:

  screens/menu/main_menu_screen.js
      Copia del fichero actual del juego (data_001.dat, 13 KB) con un solo
      literal cambiado: el reclamo "Wishlist our new game!" del menú
      principal, el único rótulo de usuario de la capa JS que seguía en
      inglés. Va como "¡A tu lista de deseados!" porque el hueco mide
      24 rem a 1,6 rem de fuente y no admite más de unos 27 caracteres en
      una línea. Un fichero entero por una línea, asumido a sabiendas; la
      dependencia la vigila check_ui_drift.py como a las demás.
"""
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "es_pack" / "src" / "ui"
BUILD = REPO / "es_pack" / "build"

# Desde la 1.0.0 los dos zips llevan la versión del pack, y la del juego contra
# la que se verificó esta capa va en la portada y en el changelog. Antes iba en
# el nombre, porque esta capa sustituye ficheros del juego; ese aviso lo da
# ahora check_ui_drift.py, que hay que pasar tras cada actualización del juego.
from build_dist import PACK_VERSION as UI_VERSION, entrada_zip  # noqa: E402

EXCLUIDOS = {
    "ui/screens/character/modules/character_screen_left_panel/"
    "character_screen_paperdoll_module.js":
        "byte a byte idéntico al del juego, no traduce nada",
}


def ficheros():
    """Los .js a empaquetar, con su ruta dentro del zip, en orden estable."""
    if not SRC.is_dir():
        raise SystemExit("no encuentro %s" % SRC)
    salida = []
    for ruta in sorted(SRC.rglob("*.js")):
        arco = ruta.relative_to(SRC.parent).as_posix()
        salida.append((ruta, arco))
    return salida


def comprueba(entradas):
    """Aborta si el contenido no es el que el addon debe llevar.

    Vale la pena abortar y no avisar: un zip mal formado aquí sólo se nota
    jugando, y los dos errores que esto detecta (empaquetar lo que no toca,
    o volver a meter un fichero excluido) ya se han cometido a mano una vez.
    """
    if not entradas:
        raise SystemExit("no hay ningún .js en %s" % SRC)
    for _, arco in entradas:
        if not arco.startswith("ui/"):
            raise SystemExit("el addon sólo puede llevar ui/: %s" % arco)
        if arco in EXCLUIDOS:
            raise SystemExit(
                "%s está excluido a propósito (%s). Si de verdad hay que "
                "distribuirlo, quítalo de EXCLUIDOS en %s y di por qué."
                % (arco, EXCLUIDOS[arco], Path(__file__).name))
    vacios = [a for r, a in entradas if r.stat().st_size == 0]
    if vacios:
        raise SystemExit("ficheros vacíos: %s" % ", ".join(vacios))


def construye(destino, entradas=None):
    """Escribe el zip del addon en `destino` y devuelve las rutas que lleva.

    Sin entradas de directorio: el juego no las necesita y así el contenido del
    zip es exactamente la lista de ficheros.
    """
    entradas = ficheros() if entradas is None else entradas
    comprueba(entradas)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for ruta, arco in entradas:
            z.writestr(entrada_zip(arco), ruta.read_bytes())
    return [arco for _, arco in entradas]


def main():
    entradas = ficheros()
    destino = BUILD / ("mod_battle_brothers_es_ui_%s.zip" % UI_VERSION)
    arcos = construye(destino, entradas)
    crudo = sum(r.stat().st_size for r, _ in entradas)

    print("ficheros:  %d  (%.0f KB de js)" % (len(arcos), crudo / 1024))
    print("excluidos: %d  (ver el docstring de %s)"
          % (len(EXCLUIDOS), Path(__file__).name))
    print("zip:       %s  (%.0f KB)"
          % (destino, destino.stat().st_size / 1024))
    print()
    print("Desde la 5.0.0 esta capa va dentro del zip del pack (build_dist):")
    print("este zip suelto es solo para revisarla, no se instala ni se publica.")
    print()
    print("Estos .js sustituyen ficheros del juego, así que son la única parte")
    print("del pack que una actualización puede tapar en silencio. Después de")
    print("cada actualización, pasa check_ui_drift.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
