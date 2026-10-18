"""Mide cuantos literales del arbol del juego no cubre ningun par del corpus,
ejecutando el emparejador REAL de Rosetta (::Rosetta.translate) fuera del
juego. No compara cadenas.

## Por que comparar cadenas no sirve

El corpus generaliza a proposito. Un solo par tipado

    en = "<actor:str> gains <v:val_tag> Experience"

cubre decenas de literales concretos distintos del juego. El extractor
(`rosetta.py -les`) no puede reconstruir esos valores en tiempo estatico:
para una expresion armada por concatenacion solo puede sacar una PLANTILLA
con marcadores sin tipo ("<actor> gains <v> Experience"), que no es un
literal real y no se puede comparar de forma fiable contra el par tipado del
corpus. Comparar cadenas contra esas plantillas es justo el metodo que ya se
probo dos veces (23/08/2026) y dio 907 y 1447 huecos, casi todos falsos
positivos de esa generalizacion: no se repite aqui, y esas cifras no se citan.

## El metodo que si vale

Arranca Squirrel de verdad (fuera del juego, via `sq_bootstrap.nut`), carga el
runtime (`!rosetta.nut`) y el pack construido (`build_dist.py`), y ejecuta el
propio `::Rosetta.translate()` sobre cada literal extraido (`sq_probe_coverage.nut`
hace la sonda; este modulo prepara sus datos y agrega su salida):

- Los literales ESTATICOS (texto fijo, sin concatenacion) SON el string real
  que aparece en el juego: se pasan a `translate()` tal cual y el resultado es
  la respuesta real del emparejador. Para distinguir "no encontrado" de "un
  par cuyo `es` es identico al `en`" (~576 casos conocidos, nombres propios,
  ya auditados y no repetidos aqui) se comprueba ademas la pertenencia directa
  al mapa `strs` del runtime, expuesto por la sonda.
- Los literales de PATRON (plantillas de una concatenacion, `mode="pattern"`
  en la salida del extractor) no son un string real y no se pueden probar
  igual: la sonda usa `_iterKeys()`, la funcion real con la que `translate()`
  decide que reglas intentar. Si ninguna clave no vacia de la plantilla tiene
  reglas en el mapa `rules` del pack cargado, es un hueco real (ninguna regla
  podria aplicar, con certeza). Si alguna clave si tiene reglas, se cuenta
  como CANDIDATO: hay una regla real que podria aplicar, pero el casado
  completo (tipos de las capturas) no queda demostrado sin el valor real que
  solo pone el juego en marcha. Ver el docstring de `sq_probe_coverage.nut`
  para el detalle de por que la clave vacia de `_iterKeys()` se descarta.

## Los cuatro casos del corpus, y donde entra cada uno aqui

Un literal sin ningun par (caso 1 de TAREA-cobertura.md) sale HUECO. Un par
con `es` vacio (caso 2, "drop") no esta en el pack cargado, asi que un
literal que solo tiene ese par tambien sale HUECO aqui; para no confundirlo
con ausencia real, este modulo cruza los huecos contra los cubos "drop" y
"wip" que `build_dist.classify()` ya calcula sobre el corpus completo, y
anota los que ya tienen un par sin embarcar como deuda de traduccion, no de
cobertura. El caso 3 (par traducido a si mismo) ya esta medido y agotado
(23/08/2026, ver KNOWN_ISSUES.md) y no se repite aqui. El caso 4 (par
correcto que el juego nunca consulta porque falta un hook) es INVISIBLE a
este metodo por construccion: el literal esta cubierto, y lo esta; ver el
aviso de limite en el informe.

## Alcance: solo el lado Squirrel

`rosetta.py -les` solo procesa `*.nut`, asi que los 36 modulos `.js` del addon
de interfaz (case cerrado en TAREA-js-addon.md) no entran nunca en la lista de
literales: no hace falta apartarlos a mano, el propio extractor ya no los ve.
Los rotulos que dibuja el motor C++ (region del mapa) tampoco son literales
`.nut` por si mismos casi siempre, pero si el nombre de origen SI vive en un
literal Squirrel (tablas de entidades, nombres de facciones), puede aparecer
en la lista y salir HUECO por no ser interceptable por diseno: es'thing que
hay que revisar a mano entre los huecos grandes y apartar en el informe, no
algo que esta herramienta pueda descartar sola con una regla general.

Uso:
    PYTHONUTF8=1 uv run python es_pack/tools/measure_coverage.py [ruta_scripts]
    PYTHONUTF8=1 uv run python es_pack/tools/measure_coverage.py --mod mod_legends [ruta]

Con `--mod <id>` (un mod de build_dist.MODS) mide la fuente fijada de ese mod
(por defecto la carpeta `fuente/` junto a su `fuente.toml`) con el pack del
juego base y el del mod cargados a la vez, que es lo que ve el jugador: el mod
reutiliza textos del juego que solo cubre el corpus base. Sin `--mod` se carga
solo el pack base, para que un par del mod no infle la cifra del juego.

`ruta_scripts` es la carpeta `scripts/` del arbol descompilado del juego. Si
se omite, se busca `SCRIPTS_DIR` en el entorno o en `.env`, y si tampoco esta
se prueba la ruta conocida del arbol de herramientas del juego (la misma idea
que `RUTAS_CONOCIDAS` en `check_syntax.py`). Necesita ademas:

- `STDLIB_DIR` (entorno o `.env`): la carpeta donde se descomprimio
  `stdlib.zip`, para el arranque de Squirrel fuera del juego.
- Un interprete Squirrel: se localiza igual que en `check_syntax.py`
  (`SQ_BIN`, PATH, o la ruta conocida).
- El pack construido en `es_pack/build/mod_battle_brothers_es/base_es.nut`
  (correr `build_dist.py` primero si no existe).

Como `check_ui_drift.py` y `gt_align.py`, esta herramienta SI necesita
recursos externos (el arbol del juego, stdlib descomprimido y un interprete
Squirrel) y no se puede correr en cualquier maquina: por eso no hay test de
extremo a extremo en la suite, solo de las partes que no dependen de ellos
(agrupacion por familia, cruce contra drop/wip). Si algo de esto falta, el
mensaje de error dice exactamente que falta y como darselo.

Escribe en `es_pack/build/` (no toca el corpus ni el pack):

- `cov_extraccion.nut`   la salida cruda de `rosetta.py -les` sobre el arbol
- `cov_literales.nut`    los mismos literales, listos para que los lea la sonda
- `cov_huecos.tsv`       huecos estaticos y de patron, con fichero y familia
- `cov_candidatos.tsv`   candidatos de patron sin confirmar del todo
- `cov_resumen.txt`      cifras agregadas, por clase y por familia
"""
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parent
BUILD = REPO / "es_pack" / "build"
ENV_FILE = REPO / ".env"

sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(REPO / "vendor" / "rosetta"))
import build_dist  # noqa: E402  buckets reales del corpus, get_field
import check_syntax  # noqa: E402  localiza_interprete
import rosetta  # noqa: E402  nutstr

PACK = BUILD / "mod_battle_brothers_es" / "base_es.nut"
EXTRACCION = BUILD / "cov_extraccion.nut"
DATOS_PROBE = BUILD / "cov_literales.nut"
PROBE_NUT = TOOLS / "sq_probe_coverage.nut"
HUECOS_TSV = BUILD / "cov_huecos.tsv"
CANDIDATOS_TSV = BUILD / "cov_candidatos.tsv"
RESUMEN_TXT = BUILD / "cov_resumen.txt"

from rutas import ARBOLES  # noqa: E402  ver rutas.py
RUTA_CONOCIDA_SCRIPTS = ARBOLES / "original_current" / "scripts"

FICHERO_RE = re.compile(r"^    // FILE: (.*)$", re.M)
BLOQUE_RE = re.compile(r"\n    \{.*?\n    \}", re.S)


def _valor_env(nombre):
    v = os.environ.get(nombre)
    if v:
        return v
    if ENV_FILE.is_file():
        for linea in ENV_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
            if linea.startswith(nombre + "="):
                return linea.split("=", 1)[1].strip().strip('"').replace("\\ ", " ")
    return None


def localiza_scripts_dir(arg=None):
    if arg:
        ruta = Path(arg)
    else:
        v = _valor_env("SCRIPTS_DIR")
        ruta = Path(v) if v else RUTA_CONOCIDA_SCRIPTS
    if not ruta.is_dir():
        raise SystemExit(
            "no encuentro el arbol del juego en %s. Pasa la ruta a scripts/, "
            "pon SCRIPTS_DIR en .env, o exportala como variable de entorno." % ruta)
    return ruta


def localiza_stdlib_dir():
    v = _valor_env("STDLIB_DIR")
    if not v or not Path(v).is_dir():
        raise SystemExit(
            "no encuentro stdlib: pon STDLIB_DIR en .env o exportala (la "
            "carpeta donde se descomprimio stdlib.zip)")
    return Path(v)


def extrae(scripts_dir):
    """Corre `rosetta.py -les <scripts_dir>` como subproceso y guarda su
    salida cruda. Va por subproceso y no por import para medir exactamente lo
    que produce el comando documentado (TAREA-cobertura.md), sin que una
    diferencia entre usar la libreria y usar la CLI se cuele en la cifra."""
    env = dict(os.environ, PYTHONUTF8="1")
    r = subprocess.run(
        [sys.executable, str(REPO / "vendor" / "rosetta" / "rosetta.py"), "-les", str(scripts_dir)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    if r.returncode != 0:
        raise SystemExit("rosetta.py -les fallo:\n" + r.stderr[-4000:])
    BUILD.mkdir(parents=True, exist_ok=True)
    EXTRACCION.write_text(r.stdout, encoding="utf-8")
    print("extraidos: %s (ficheros procesados, ver %s)"
          % (r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "?",
             EXTRACCION.name))
    return r.stdout


def familia(ruta_abs, scripts_dir):
    """Directorio de primer nivel bajo scripts/, para agrupar huecos por
    familia en vez de en una lista plana de miles de cadenas."""
    s = str(ruta_abs).replace("\\", "/")
    base = str(scripts_dir).replace("\\", "/").rstrip("/") + "/"
    rel = s[len(base):] if s.startswith(base) else s
    partes = rel.split("/")
    return partes[0] if partes and partes[0] else "?"


def parse_literales(texto, scripts_dir):
    """(fichero_relativo, familia, modo, en) por cada literal extraido, en el
    mismo orden en que aparecen (el indice en esta lista es el que usa la
    sonda de Squirrel para reportar sin tener que ir y volver el texto)."""
    trozos = FICHERO_RE.split(texto)
    out = []
    for i in range(1, len(trozos), 2):
        ruta_abs = trozos[i].strip()
        fam = familia(ruta_abs, scripts_dir)
        s = str(ruta_abs).replace("\\", "/")
        base = str(scripts_dir).replace("\\", "/").rstrip("/") + "/"
        rel = s[len(base):] if s.startswith(base) else s
        for b in BLOQUE_RE.findall(trozos[i + 1]):
            en = build_dist.get_field(b, "en")
            if en is None:
                continue
            modo = "pattern" if 'mode = "pattern"' in b else ""
            out.append((rel, fam, modo, en))
    return out


def objetivo(mod_id=None):
    """Los corpus que se miden y los packs construidos que carga la sonda, uno
    por corpus. Sin mod, solo el juego base; con mod, el base y el del mod."""
    ids = ("vanilla", mod_id)
    if mod_id is not None and mod_id not in build_dist.MODS:
        raise SystemExit("mod desconocido: %s (los de build_dist.MODS: %s)"
                         % (mod_id, ", ".join(build_dist.MODS)))
    corpus = [c["ruta"] for c in build_dist.corpus_del_pack() if c["id"] in ids]
    packs = [PACK.parent / c.name for c in corpus]
    if mod_id is not None:
        # como el preload: claves.nut va antes del corpus del mod
        packs.insert(1, PACK.parent / "claves.nut")
    return corpus, packs


def copia_de_la_fuente(mod_id):
    """La fuente fijada del mod tal como la ve la extracción de su corpus
    (lotes.py extraer): solo sus rutas y con las cadenas @"..." convertidas,
    que el extractor de Rosetta no lee y por las que descarta ficheros enteros."""
    import shutil
    import tomllib

    import lotes

    toml = build_dist.MODS[mod_id]
    destino = BUILD / ("cov_fuente_" + mod_id)
    shutil.rmtree(destino, ignore_errors=True)
    rutas = tomllib.loads(toml.read_text(encoding="utf-8"))["rutas"]
    lotes.copia_extraible(toml.parent / "fuente", destino, rutas)
    return destino


def corpus_pendiente(corpus=(build_dist.CORPUS,)):
    """Los `en` del corpus completo (dist+wip+drop) que NO llegan al pack
    cargado, separados en estaticos y de patron, para anotar huecos como
    deuda de traduccion en vez de ausencia real. Usa el clasificador real de
    build_dist.py, no una regla propia: si upstream o el corpus cambian de
    forma, esto se entera por el mismo camino que build_dist."""
    bloques = [b for c in corpus for b in build_dist.load_blocks(c)]
    static_en = set()
    pattern_en_drop, pattern_en_wip = [], []
    for b in bloques:
        clase = build_dist.classify(b)
        if clase == "dist":
            continue
        en = build_dist.get_field(b, "en")
        if en is None:
            continue
        if build_dist.is_rule_pair(b):
            (pattern_en_drop if clase == "drop" else pattern_en_wip).append(en)
        elif clase == "drop":
            static_en.add(en)
    return static_en, pattern_en_drop, pattern_en_wip


def escribe_datos_probe(literales, drop_pattern_en, wip_pattern_en):
    DATOS_PROBE.parent.mkdir(parents=True, exist_ok=True)
    with DATOS_PROBE.open("w", encoding="utf-8", newline="\n") as f:
        f.write("::COV_LITERALES <- [\n")
        for _rel, _fam, modo, en in literales:
            f.write('{mode=%s en=%s}\n' % (rosetta.nutstr(modo), rosetta.nutstr(en)))
        f.write("]\n")
        f.write("::COV_DROP_PATTERN_EN <- [\n")
        for en in drop_pattern_en:
            f.write(rosetta.nutstr(en) + "\n")
        f.write("]\n")
        f.write("::COV_WIP_PATTERN_EN <- [\n")
        for en in wip_pattern_en:
            f.write(rosetta.nutstr(en) + "\n")
        f.write("]\n")


def corre_sonda(sq_bin, stdlib_dir, packs=(PACK,)):
    env = dict(os.environ)
    env["ROSETTA_DIR"] = str(REPO)
    env["STDLIB_DIR"] = str(stdlib_dir)
    env["COV_PACK"] = ";".join(str(p) for p in packs)
    env["COV_DATOS"] = str(DATOS_PROBE)
    r = subprocess.run([str(sq_bin), str(PROBE_NUT)],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env)
    if r.returncode != 0 or "AN ERROR HAS OCCURED" in r.stdout.upper():
        raise SystemExit("la sonda de Squirrel fallo:\nSTDOUT:\n%s\nSTDERR:\n%s"
                         % (r.stdout[-4000:], r.stderr[-4000:]))
    return r.stdout


# Restos que la medicion del 17/10/2026 dejo como hueco de frase y que se
# revisaron uno a uno: ninguno es texto que el jugador lea en ingles. Se
# descuentan por cadena exacta, nunca por regla, para que un texto nuevo de
# un parche siga saliendo como hueco y baje la cifra.
REVISADOS = {
    # progreso de ambicion escrito como codigo: lo cubren los patrones "<text:str> (<n:int>/N)" via el hook de la barra superior (caso 18)
    '<this.m.UIText> (<d>/25)',
    '<this.m.UIText> (<this.Math.min(12, this.World.Statistics.getFlags().get(ItemsCrafted))>/12)',
    '<this.m.UIText> (<this.Math.min(2, this.getBrosWithMastery())>/2)',
    '<this.m.UIText> (<this.Math.min(3, this.getBrosWithMastery())>/3)',
    '<this.m.UIText> (<this.Math.min(4, d)>/4)',
    '<this.m.UIText> (<this.Math.min(5, d)>/5)',
    '<this.m.UIText> (<this.Math.min(5, this.getBrosWithMastery())>/5)',
    '<this.m.UIText> (<this.Math.min(8, d)>/8)',
    '<this.m.UIText> (<this.m.Defeated>/4)',
    '<this.m.UIText> (<this.m.LocationsDiscovered>/3)',
    '<this.m.UIText> (<this.m.LocationsDiscovered>/8)',
    # condicion de codigo que el extractor toma por texto
    '<!this.isKindOf(_actor, , , player)&&!this.isKindOf(_actor, , , human)>',
    '<!this.isKindOf(_target, , , player)&&!this.isKindOf(_target, , , human)>',
    '<!this.isKindOf(target, , , player)||target.getBackground()==null||target.getBackground().getID()!=>background.slave',
    '<start + this.removeFromBeginningOfText(The , this.Const.Strings.EntityName[i])>',
    '<this.isKindOf(_killer, , , player)&&_killer.getSkills().hasSkill(effects.charmed)>',
    '<this.isKindOf(_target, , , wardog)||this.isKindOf(_target, , , warhound)&&_target.getFaction()==this.Const.Faction.PlayerAnimals&&_skill!=null>',
    '<this.isKindOf(target, , , human)&&this.m.SoundOnHit.len()!=0>',
    '<this.isKindOf(target, , , player)||this.isKindOf(target, , , firstborn)||this.isKindOf(target, , , envoy)>',
    # trozo de una frase que en partida llega entera y la traduce su propio par
    "'s morale is now steady",
    '<desc + heal.MedicineMax>[/color] Medical Supplies.',
    '<desc + repair.ArmorParts>[/color] tools and supplies.',
    '<rumor>The patrons talk about this and that.',
    '<this.m.Name> (x<this.m.Count>)',
    # depuracion, nombre interno o clave adjudicada: solo sale en el log
    'Battle Brothers',
    'Desert Raiders',
    'Falling back',
    'Generic Item',
    'Info: Battle ended after <this.m.CurrentRound> Round(s).',
    'Load campaign: <_campaignFileName>',
    'No good tile in range, engaging in the general direction of the enemy!',
    'ORIENTAL CITY #2',
    'ORIENTAL CITY #3',
    'Save campaign: <_campaignLabel>',
    'undefined bridge brush',
    'undefined crossing brush',
    'undefined river brush',
    'undefined road brush',
    'undefined shore brush',
    # Legends (19/10/2026): trozo que en partida llega dentro de una frase que traduce su propio par (patrones compuestos, sumas, la linea de grupos de ventajas, las formas de los tokens de genero)
    ' The arena master',
    ' feels more comfortable with their weapon',
    ' figures out what end of the weapon to hold',
    ' finally nails the fancy parry they have been been practicing',
    ' finds a stance that can improve his experience in the next battle',
    ' finds a stance that feels more natural',
    ' had their ego bruised and wants an outlet for frustration',
    ' has perfected a new skill in practice',
    ' has practiced a skill so much it has become second nature',
    ' invents an overly showy move',
    ' is ready to learn more in the next battle',
    ' learned a new move',
    ' learned how to get most of the next battle',
    ' learns how to adjust the new armor so it fits better',
    ' left the training dummy as nothing more than a pile of splinters',
    ' remembers that you can move your legs as well as your arms',
    ' sets a new personal best in training',
    '<array[array.len()-2]> or ',
    '<colorizeInGreen( (100%))>',
    '<colorizeInRed( (0%))>',
    "<colorizeInRed(Can't loot any equipment from this entity)>",
    '<this.m.Name> (x<this.m.RageStacks>)',
    '<this.m.Name> (x<this.m.Stacks>)',
    '<this.m.Name> (x<this.m.Threads>)',
    '<this.m.Name>[color=<this.Const.UI.Color.RuneColor>] (Runed)[/color]',
    'The arena master',
    '[color=#0b0084]From the ',
    '[img]gfx/ui/icons/bravery_va11.png[/img] <a.Bravery[0]> to <a.Bravery[1] + bufferBravery>&nbsp;&nbsp;&nbsp;[img]gfx/ui/icons/melee_defense_va11.png[/img] <a.MeleeDefense[0]> to <a.MeleeDefense[1]>',
    '[img]gfx/ui/icons/fatigue_va11.png[/img] <a.Fatigue[0]> to <a.Fatigue[1] + bufferFatigue>&nbsp;&nbsp;&nbsp;[img]gfx/ui/icons/ranged_skill_va11.png[/img] <a.RangedSkill[0]> to <a.RangedSkill[1]>',
    '[img]gfx/ui/icons/health_va11.png[/img] <a.Hitpoints[0]> to <a.Hitpoints[1] + bufferHealth>&nbsp;&nbsp;&nbsp;[img]gfx/ui/icons/melee_skill_va11.png[/img] <a.MeleeSkill[0]> to <a.MeleeSkill[1]>',
    '[img]gfx/ui/icons/initiative_va11.png[/img] <a.Initiative[0]> to <a.Initiative[1] + bufferInitiative>&nbsp;&nbsp;&nbsp;[img]gfx/ui/icons/ranged_defense_va11.png[/img] <a.RangedDefense[0]> to <a.RangedDefense[1]>',
    'a few',
    'are they',
    'color=#0b0084]From the <mid + ap>',
    'he is',
    'he was',
    'he will',
    'is he',
    'is she',
    'perk group[/color]',
    'perk groups[/color]',
    'she is',
    'she was',
    'she will',
    'they are',
    'they were',
    'they will',
    'was he',
    'was she',
    'were they',
    # Legends: condicion o busqueda de codigo que el extractor toma por texto
    '<!this.isKindOf(_targetEntity, , , player)&&!this.isKindOf(_targetEntity, , , human)>',
    '<_app[>Corpse<p + s]>',
    '<_tooltip.text.find(skills build up)!=null>',
    '<modifier[>Fast Adaption<]>',
    '<modifier[>Height advantage<]>',
    '<modifier[>Height disadvantage<]>',
    '<modifier[>Line of fire blocked<]>',
    '<this.isKindOf(_targetedEntity, , , actor)&&_activeEntity.isPlayerControlled()&&_targetedEntity!=null>',
    '<tooltip.text.find(Is empty and useless)!=null>',
    # Legends: depuracion, clave interna o nombre propio de un mod: solo sale en el log o no se muestra
    ' skill cost (<item.m.FatigueOnSkillUse>),',
    'Armors (<armorsNum>):',
    'Helmets (<helmetsNum>):',
    'Shields (<shieldsNum>):',
    'Weapons (<weaponsNum>):',
    ' ammo (+<item.m.AmmoMax>),',
    ' but it could not be found in any Category',
    '(x=<_t.X> y=<_t.Y>)',
    '<armorsNum>° [<armor.slice(0, 1).toupper() + armor.slice(1)>] ',
    '<helmetsNum>° [<helmet.slice(0, 1).toupper() + helmet.slice(1)>] ',
    '<shieldsNum>° [<shield.slice(0, 1).toupper() + shield.slice(1)>] ',
    '<weaponsNum>° [<weapon.slice(0, 1).toupper() + weapon.slice(1)>]',
    'AI_ENGAGE_MELEE: Illegal path after clipping.',
    'AI_ENGAGE_MELEE: Illegal potential destination.',
    'AI_ENGAGE_MELEE: Spearwall hasNextTile Bug',
    'Broad Head',
    'Contract Overhaul: Missing Category for settlement contract: ',
    'Dropped net on this tile',
    'ERROR: Legends Requires Modding Standards & Utilities (MSU) to function.<br><a style="color: lightblue; text-decoration: underline;"onclick="openURL(\'https://www.nexusmods.com/battlebrothers/mods/479\')">Get MSU from Nexusmods</a>',
    'Events and Ambitions Delayed Fix',
    'Index <_index> greater than length of m.PresetNames',
    'Legend Tournament',
    'MovementCosts.End Pos: <movementCosts.End.X>,<movementCosts.End.Y>',
    'MovementCosts.Tiles: <movementCosts.Tiles>',
    'Target Destination Tile: <t.Tile.X>,<t.Tile.Y>',
    'armor_upgrades/<split(upgrade[4], .)[2]>, <_armor.getUpgradeVariant(4)>',
    'chain/<split(upgrade[0], .)[2]>, <_armor.getUpgradeVariant(0)>',
    'cloak/<split(upgrade[3], .)[2]>, <_armor.getUpgradeVariant(3)>',
    'helm/<split(upgrade[0], .)[2]>, <_helmet.getUpgradeVariant(0)>',
    'on get',
    'on grant',
    'on has',
    'on remove',
    'perks before: <perks>',
    'plate/<split(upgrade[1], .)[2]>, <_armor.getUpgradeVariant(1)>',
    'tabard/<split(upgrade[2], .)[2]>, <_armor.getUpgradeVariant(2)>',
    'tnf_debugMode | Roster [min-max] attributes values up to veteran level:',
    'top/<split(upgrade[1], .)[2]>, <_helmet.getUpgradeVariant(1)>',
    'vanity/<split(upgrade[2], .)[2]>, <_helmet.getUpgradeVariant(2)>',
}


def es_texto(en):
    """Si un literal es una frase que puede leer el jugador. Fuera quedan las
    claves internas (ids de pantalla de evento, nombres de variable: sin un
    solo espacio) y las trazas de depuracion (codigo con :: o con llamadas).
    La regla se aplica igual a cubiertos y a huecos, asi que no infla nada.
    REVISADOS descuenta ademas los restos ya revisados a mano."""
    if " " not in en.strip() or en in REVISADOS:
        return False
    return not any(m in en for m in ("::", "();", "()>", " : <"))


def main(argv):
    argv = list(argv)
    mod_id = None
    if "--mod" in argv:
        i = argv.index("--mod")
        mod_id = argv[i + 1] if i + 1 < len(argv) else None
        if mod_id is None:
            raise SystemExit("--mod necesita el id de un mod de build_dist.MODS")
        del argv[i:i + 2]
    corpus, packs = objetivo(mod_id)
    for p in packs:
        if not p.is_file():
            raise SystemExit(
                "no encuentro %s. Corre primero:\n"
                "  PYTHONUTF8=1 uv run python es_pack/tools/build_dist.py" % p)

    if mod_id is not None and not argv:
        argv = [str(copia_de_la_fuente(mod_id))]
    scripts_dir = localiza_scripts_dir(argv[0] if argv else None)
    stdlib_dir = localiza_stdlib_dir()
    sq_bin = check_syntax.localiza_interprete()
    if sq_bin is None:
        raise SystemExit(
            "no encuentro interprete Squirrel: pon SQ_BIN=/ruta/a/sq.exe")

    texto = extrae(scripts_dir)
    literales = parse_literales(texto, scripts_dir)
    print("literales extraidos: %d (%d de patron)"
          % (len(literales), sum(1 for *_, m, _ in literales if m == "pattern")))

    static_pendiente, drop_pattern_en, wip_pattern_en = corpus_pendiente(corpus)

    escribe_datos_probe(literales, drop_pattern_en, wip_pattern_en)
    salida = corre_sonda(sq_bin, stdlib_dir, packs)

    resultados = {}
    for linea in salida.splitlines():
        if not linea.strip():
            continue
        partes = linea.split("\t")
        idx, clase = int(partes[0]), partes[1]
        detalle = partes[2] if len(partes) > 2 else ""
        resultados[idx] = (clase, detalle)

    if len(resultados) != len(literales):
        raise SystemExit(
            "la sonda devolvio %d lineas para %d literales: algo se ha "
            "desincronizado, no se puede fiar el resultado"
            % (len(resultados), len(literales)))

    clases = Counter()
    huecos_por_familia = Counter()
    candidatos_por_familia = Counter()
    filas_huecos = []
    filas_candidatos = []
    texto_total = texto_huecos = 0

    for i, (rel, fam, modo, en) in enumerate(literales):
        clase, detalle = resultados[i]
        clases[clase] += 1
        texto = es_texto(en)
        texto_total += texto

        if clase == "HUECO":
            anotado = "drop" if en in static_pendiente else ""
            filas_huecos.append((fam, rel, modo, anotado, en))
            if not anotado:
                huecos_por_familia[fam] += 1
                texto_huecos += texto
        elif clase == "PAT_HUECO":
            filas_huecos.append((fam, rel, modo, detalle, en))
            if not detalle:
                huecos_por_familia[fam] += 1
                texto_huecos += texto
        elif clase == "PAT_CANDIDATO":
            filas_candidatos.append((fam, rel, en))
            candidatos_por_familia[fam] += 1

    HUECOS_TSV.parent.mkdir(parents=True, exist_ok=True)
    with HUECOS_TSV.open("w", encoding="utf-8", newline="") as f:
        f.write("familia\tfichero\tmodo\tanotacion\ten\n")
        for fam, rel, modo, anotado, en in sorted(filas_huecos):
            f.write("%s\t%s\t%s\t%s\t%s\n"
                    % (fam, rel, modo or "literal", anotado, en.replace("\t", " ").replace("\n", "\\n")))

    with CANDIDATOS_TSV.open("w", encoding="utf-8", newline="") as f:
        f.write("familia\tfichero\ten\n")
        for fam, rel, en in sorted(filas_candidatos):
            f.write("%s\t%s\t%s\n" % (fam, rel, en.replace("\t", " ").replace("\n", "\\n")))

    total = len(literales)
    reales = sum(v for k, v in clases.items())
    cubiertos = clases["OK_DIRECTO"] + clases["OK_IDENTICO"] + clases["PAT_OK_DIRECTO"]
    huecos_reales = sum(huecos_por_familia.values())
    huecos_anotados = clases["HUECO"] + clases["PAT_HUECO"] - huecos_reales
    candidatos = clases["PAT_CANDIDATO"]

    with RESUMEN_TXT.open("w", encoding="utf-8") as f:
        def out(s=""):
            print(s)
            f.write(s + "\n")

        out("literales medidos: %d" % total)
        out("por clase:")
        for c, n in clases.most_common():
            out("   %-16s %5d" % (c, n))
        out()
        out("cubiertos (directo o identico): %d" % cubiertos)
        out("candidatos de patron (clave real, sin confirmar del todo): %d" % candidatos)
        out("huecos reales (sin par, sin candidato, sin explicar por drop/wip): %d"
            % huecos_reales)
        out("huecos ya explicados por un par sin embarcar (drop/wip, deuda de "
            "traduccion, no de cobertura): %d" % huecos_anotados)
        out()
        cobertura = 100.0 * (total - huecos_reales) / total if total else 0.0
        out("cobertura del corpus sobre literales extraidos: %.2f%%  "
            "((%d - %d) / %d, contando candidatos de patron como cubiertos)"
            % (cobertura, total, huecos_reales, total))
        cob_texto = 100.0 * (texto_total - texto_huecos) / texto_total if texto_total else 0.0
        out("restos revisados a mano y descontados (REVISADOS): %d" % len(REVISADOS))
        out("cobertura de frases (sin claves internas ni trazas): %.2f%%  "
            "((%d - %d) / %d)" % (cob_texto, texto_total, texto_huecos, texto_total))
        out()
        out("huecos reales por familia:")
        for fam, n in huecos_por_familia.most_common():
            out("   %-20s %5d" % (fam, n))
        out()
        out("candidatos de patron por familia:")
        for fam, n in candidatos_por_familia.most_common():
            out("   %-20s %5d" % (fam, n))

    print()
    print("huecos en", HUECOS_TSV)
    print("candidatos en", CANDIDATOS_TSV)
    print("resumen en", RESUMEN_TXT)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
