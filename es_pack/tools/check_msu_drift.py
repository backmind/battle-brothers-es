"""Avisa de cuándo una versión de MSU toca algo de lo que el pack depende.

El pack traduce MSU por dos vías, y ninguna sustituye ficheros suyos:

- **Sus textos de Squirrel** (tooltips, ajustes, atajos) van por Rosetta como
  el resto del juego, con pares en el corpus. Si MSU cambia o añade un texto,
  no se rompe nada: ese texto sale en inglés. Esta herramienta lo detecta antes
  que un jugador.
- **Sus textos de JS** (botones y cabecera de la pantalla de ajustes, el botón
  "Mod Options") los cambia `src/ui/mods/mod_battle_brothers_es/msu_es.js`
  envolviendo métodos de MSU. Está escrito para que, si MSU renombra algo, los
  textos vuelvan al inglés sin romper su pantalla. Esta herramienta comprueba
  que sigue existiendo cada pieza que toca, y también la API de Squirrel que usa
  el preload para la ficha del pack.

Uso:
    PYTHONUTF8=1 uv run python es_pack/tools/check_msu_drift.py [mod_msu.zip | carpeta]

Sin argumento lee `mod_msu.zip` de DATA_DIR (ver `rutas.py`). La CI le pasa la
última release de MSU cada semana (`.github/workflows/vigilancia.yml`).

Devuelve 0 si todo cuadra y 1 si hay algo que mirar.
"""
import re
import sys
import zipfile
from pathlib import Path

import rutas

CORPUS = rutas.REPO / "es_pack" / "corpus" / "base_es.nut"

# (fichero de MSU, texto que tiene que seguir estando, quién depende de él)
PIEZAS = [
    ("ui/mods/msu/mod_settings/settings_screen.js", "ModSettingsScreen.prototype.createDIV = function", "msu_es.js"),
    ("ui/mods/msu/mod_settings/settings_screen.js", "ModSettingsScreen.prototype.hide = function", "msu_es.js"),
    ("ui/mods/msu/mod_settings/settings_screen.js", "ModSettingsScreen.prototype.switchToPage = function (_panel, _page)", "msu_es.js"),
    ("ui/mods/msu/mod_settings/settings_screen.js", "this.mActiveSettings", "msu_es.js"),
    ("ui/mods/msu/mod_settings/settings_screen.js", "'main-cancel-button'", "msu_es.js"),
    ("ui/mods/msu/mod_settings/settings_screen.js", "'main-reset-button'", "msu_es.js"),
    ("ui/mods/msu/mod_settings/settings_screen.js", "'main-apply-button'", "msu_es.js"),
    ("ui/mods/msu/mod_settings/settings_screen.js", "'main-save-button'", "msu_es.js"),
    ("ui/mods/msu/mod_settings/settings_screen.js", "'Mod Settings'", "msu_es.js"),
    ("ui/mods/msu/mod_settings/settings_screen.js", '"Select a Mod From the List"', "msu_es.js"),
    ("ui/mods/msu/mod_settings/title_setting.js", "var TitleSetting = function", "msu_es.js"),
    ("ui/mods/msu/mod_settings/title_setting.js", "this.title = $(", "msu_es.js"),
    ("ui/mods/msu/mod_settings/title_setting.js", "this.layout = $(", "msu_es.js"),
    ("ui/mods/msu/mod_settings/title_setting.js", "' + _setting.name + '", "ficha del preload (el nombre se pinta como HTML)"),
    ("ui/mods/msu/ui_hooks/main_menu_module.js", "MainMenuModule.prototype.addModOptionsButton = function", "msu_es.js"),
    ("ui/mods/msu/ui_hooks/main_menu_module.js", 'createTextButton("Mod Options"', "msu_es.js"),
    ("msu/systems/mod_settings/mod_settings_mod_addon.nut", "function addPage( _pageID, _pageName = null )", "preload"),
    ("msu/systems/mod_settings/settings_page.nut", "function addTitle( _id, _name, _description = null )", "preload"),
    ("msu/systems/mod_settings/settings_page.nut", "function addDivider( _id )", "preload"),
    ("msu/systems/registry/registry_mod_addon.nut", "function addModSource( _domain, _url, _opts = null )", "preload"),
    ("msu/systems/registry/registry_mod_addon.nut", "function setUpdateSource( _domain )", "preload"),
]

# Ficheros de MSU con textos que ve el jugador.
FICHEROS_TEXTO = [
    r"msu/msu_mod/[^/]+\.nut",
    r"msu/vanilla_mod/[^/]+\.nut",
    r"msu/systems/keybinds/[^/]+\.nut",
    r"msu/systems/mod_settings/[^/]+\.nut",
    r"msu/hooks/states/[^/]+\.nut",
]

# Literales de esos ficheros con forma de texto que no lo son: ids, claves de
# flags, trazas del log y nombres de mod (que se quedan sin par a propósito,
# ver la sección de MSU del corpus). Revisados uno a uno contra MSU 1.9.0.
NO_SON_TEXTO = {
    "Abstract", "Calling keybind", "Checking keybind: ", "ClosePopup",
    "Creating Keybind array for key: ", "Element", "ExpandedItemTooltips",
    "ExpandedSkillTooltips", "Final key string: ", "Keybind", "LocationBattle",
    "LockReason", "Locked", "Log", "ModSetting", "ModSetting.", "ModSettings",
    "Name: ", "NewCampaign", "NewCampaignOnly", "Removing Keybind",
    "ResetAllSettings", "Returning after keybind call returned true.",
    "ShowPopup", "SuppressBaseKeybinds", "Type: ", "Value", "Vanilla (MSU)",
    "VanillaBBCode", "Version",
}

LITERAL = re.compile(r'"((?:[^"\\]|\\.)*)"')
FORMA_DE_TEXTO = re.compile(r"[A-Za-z][A-Za-z ]*[a-z][A-Za-z0-9 .,'()&!?:\\-]*")
LINEA_DE_LOG = re.compile(r"(//|::log(Info|Error|Warning)|throw)")


class Fuente:
    """Los ficheros de MSU, desde su zip o desde una carpeta descomprimida."""

    def __init__(self, ruta):
        self.ruta = Path(ruta)
        if self.ruta.is_file():
            self.zip = zipfile.ZipFile(self.ruta)
            self.nombres = [n for n in self.zip.namelist() if not n.endswith("/")]
        elif self.ruta.is_dir():
            self.zip = None
            self.nombres = [p.relative_to(self.ruta).as_posix()
                            for p in self.ruta.rglob("*") if p.is_file()]
        else:
            raise SystemExit("no encuentro MSU en %s" % self.ruta)

    def lee(self, nombre):
        if nombre not in self.nombres:
            return None
        datos = self.zip.read(nombre) if self.zip else (self.ruta / nombre).read_bytes()
        return datos.decode("utf-8", errors="replace")


def piezas_que_faltan(fuente):
    faltan = []
    for fichero, texto, quien in PIEZAS:
        contenido = fuente.lee(fichero)
        if contenido is None:
            faltan.append((fichero, "el fichero ya no existe", quien))
        elif texto not in contenido:
            faltan.append((fichero, texto, quien))
    return faltan


def textos_de_msu(fuente):
    """{literal con forma de texto: 'fichero:línea' de su primera aparición}."""
    vistos = {}
    for nombre in sorted(fuente.nombres):
        if not any(re.fullmatch(p, nombre) for p in FICHEROS_TEXTO):
            continue
        for i, linea in enumerate(fuente.lee(nombre).splitlines(), 1):
            if LINEA_DE_LOG.match(linea.strip()):
                continue
            for s in LITERAL.findall(linea):
                if FORMA_DE_TEXTO.fullmatch(s) and (" " in s or s[0].isupper()):
                    vistos.setdefault(s, "%s:%d" % (nombre, i))
    return vistos


def textos_sin_par(fuente, corpus_texto):
    con_par = set(re.findall(r'^\s*en = "((?:[^"\\]|\\.)*)"', corpus_texto, re.M))
    return sorted((s, donde) for s, donde in textos_de_msu(fuente).items()
                  if s not in con_par and s not in NO_SON_TEXTO)


def main(argv):
    origen = Path(argv[0]) if argv else rutas.DATA / "mod_msu.zip"
    fuente = Fuente(origen)
    faltan = piezas_que_faltan(fuente)
    sin_par = textos_sin_par(fuente, CORPUS.read_text(encoding="utf-8"))

    print("MSU: %s" % origen)
    if not faltan and not sin_par:
        print("Todo lo que el pack toca de MSU sigue en su sitio, y todos sus textos tienen par.")
        return 0
    for fichero, texto, quien in faltan:
        print("PIEZA  %s" % fichero)
        print("   ya no contiene: %s" % texto)
        print("   depende de ello: %s (esos textos vuelven al inglés)" % quien)
    for s, donde in sin_par:
        print("TEXTO  %s" % donde)
        print("   sin par: %s" % s)
    print()
    print("Una pieza que falta deja en inglés lo que toca, sin romper MSU. Un texto")
    print("sin par se traduce en la sección de MSU del corpus; si no es texto, va a")
    print("NO_SON_TEXTO con el motivo.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
