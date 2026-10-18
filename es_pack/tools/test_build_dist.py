import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_dist import classify, get_field, load_blocks

FIXTURE = '''if (!("Rosetta" in getroottable())) return;

local rosetta = {
    mod = {id = "vanilla", version = "0.0.0"}
    author = "test"
    lang = "es"
}
local pairs = [
    {
        en = "Your Task"
        es = "Tu tarea"
    }
    {
        en = "Not yet translated"
        es = ""
    }
    {
        mode = "pattern"
        en = "You gain <this.Const.Strings.getArticle(item.getName())>"
        es = "Ganas <this.Const.Strings.getArticle(item.getName())>"
    }
    {
        mode = "pattern"
        en = "Has a range of <range:int> tiles"
        es = "Tiene un alcance de <range> casillas"
    }
]
::Rosetta.add(rosetta, pairs);
'''


def test_load_blocks_and_classify(tmp_path):
    f = tmp_path / "fixture_es.nut"
    f.write_text(FIXTURE, encoding="utf-8")
    blocks = load_blocks(f)
    assert len(blocks) == 4
    kinds = [classify(b) for b in blocks]
    # literal traducido -> dist; vacio -> drop; placeholder crudo -> wip;
    # patron tipado valido -> dist
    assert kinds == ["dist", "drop", "wip", "dist"]


FIXTURE2 = '''if (!("Rosetta" in getroottable())) return;

local rosetta = {
    mod = {id = "vanilla", version = "0.0.0"}
    author = "test"
    lang = "es"
}
local pairs = [
    {
        en = "Alpha"
        es = "Alfa"
    }
    {
        en = "Beta"
        es = "Beta"
    }
    {
        en = "Gamma"
        es = "Gama"
    }
]
::Rosetta.add(rosetta, pairs);
'''


def test_load_blocks_is_repeatable(tmp_path):
    # Dos ficheros DISTINTOS: si los globals de rosetta no se limpiaran
    # entre cargas, la segunda carga arrastraria los bloques de la
    # primera (en distintos, sin dedup por REF_BLOCKS[en]) y el conteo
    # no seria el propio del segundo fichero (3).
    f1 = tmp_path / "fixture_es.nut"
    f1.write_text(FIXTURE, encoding="utf-8")
    f2 = tmp_path / "fixture2_es.nut"
    f2.write_text(FIXTURE2, encoding="utf-8")
    assert len(load_blocks(f1)) == 4
    assert len(load_blocks(f2)) == 3


def test_get_field_unescapes():
    block = '{\n en = "a\\nb"\n es = "c \\"d\\""\n}'
    assert get_field(block, "en") == "a\nb"
    assert get_field(block, "es") == 'c "d"'


def test_emit_decodes_hex_escapes(tmp_path):
    from build_dist import emit
    block = ('{\n        en = "He said \\x22hi\\x22 \\x7bA|B\\x7d"\n'
             '        es = "Dijo \\x22hola\\x22 \\x7bA|B\\x7d"\n    }')
    out = tmp_path / "o.nut"
    emit(out, [block])
    text = out.read_text(encoding="utf-8")
    assert "\\x22" not in text and "\\x7b" not in text and "\\x7d" not in text
    assert '\\"hi\\"' in text and "{A|B}" in text


def test_decode_preserves_literal_backslash_x22():
    from build_dist import decode_hex_escapes
    assert decode_hex_escapes(r'"a\\x22"') == r'"a\\x22"'
    assert decode_hex_escapes(r'"a\x22"') == r'"a\""'


# --- F1: contrato real del runtime (validateRule en !rosetta.nut) ---

def test_classify_valid_typed_pattern_is_dist():
    block = ('{\n mode = "pattern"\n'
             ' en = "Has a range of <range:int> tiles"\n'
             ' es = "Tiene un alcance de <range> casillas"\n}')
    assert classify(block) == "dist"


def test_classify_es_label_renamed_is_wip():
    # Shape valida en ambos lados, pero la label de es no existe en en
    # (validateRule: "Label '%s' is in '%s' but not in 'en'").
    block = ('{\n mode = "pattern"\n'
             ' en = "Has a range of <range:int> tiles"\n'
             ' es = "Tiene un alcance de <alcance> casillas"\n}')
    assert classify(block) == "wip"


def test_classify_es_placeholder_without_en_is_wip():
    # en sin placeholders, es con uno: la label no puede existir en en
    # (labels vacio) y antes llegaba a dist, abortando el pack entero.
    block = '{\n en = "Your Task"\n es = "Tu <tarea>"\n}'
    assert classify(block) == "wip"


def test_classify_unsupported_sub_type_is_wip():
    # "integer" no esta en SUBS/subRes -> validateRule lanzaria
    # "Label type 'integer' is not supported".
    block = ('{\n mode = "pattern"\n'
             ' en = "Has <x:integer> value"\n'
             ' es = "Tiene <x> valor"\n}')
    assert classify(block) == "wip"


def test_classify_adjacent_str_placeholders_is_wip():
    # validateRule: "Two :str next to each other not allowed".
    block = ('{\n mode = "pattern"\n'
             ' en = "<a:str><b:str>"\n'
             ' es = "<a><b>"\n}')
    assert classify(block) == "wip"


# --- F4: cuarentena no debe ser un pack cargable ---

def test_emit_wip_has_no_rosetta_add(tmp_path):
    from build_dist import emit_wip
    block = '{\n en = "Foo"\n es = "Bar"\n}'
    out = tmp_path / "patterns_wip.nut"
    emit_wip(out, [block])
    text = out.read_text(encoding="utf-8")
    assert "::Rosetta.add" not in text
    assert "CUARENTENA" in text
    assert "Foo" in text and "Bar" in text


def test_classify_rejects_duplicate_captures():
    from build_dist import classify
    block = ('{\n        mode = "pattern"\n'
             '        en = "Level up <goal:int> times (<progress:int>/<goal:int>)"\n'
             '        es = "Sube <goal> veces (<progress>/<goal>)"\n    }')
    assert classify(block) == "wip"


def test_literal_pair_with_html_tag_is_dist():
    from build_dist import classify
    block = ('{\n        en = "First line<br/>Second line"\n'
             '        es = "Primera linea<br/>Segunda linea"\n    }')
    assert classify(block) == "dist"


def test_literal_pair_with_styled_span_is_dist():
    from build_dist import classify
    block = ('{\n        en = "<span style=\\"color:%negative%;\\"><u>No Cooks</u></span>"\n'
             '        es = "<span style=\\"color:%negative%;\\"><u>Sin cocineros</u></span>"\n    }')
    assert classify(block) == "dist"


def test_literal_pair_with_raw_expression_stays_wip():
    from build_dist import classify
    block = ('{\n        en = "You gain <this.getItem().getName()>"\n'
             '        es = "Ganas <this.getItem().getName()>"\n    }')
    assert classify(block) == "wip"


def test_checks_detecta_img_discrepante():
    from checks import revisar
    datos = [("[img]gfx/ui/events/event_10.png[/img]Text here",
              "[img]gfx/ui/events/event_99.png[/img]Texto aqui")]
    assert len(revisar(datos)["IMG"]) == 1


def test_checks_detecta_es_duplicado_entre_ens_ajenos():
    from checks import revisar
    comun = "Una traduccion compartida bastante larga"
    datos = [("Wolves howl at the moon tonight", comun),
             ("Merchants haggle over grain prices", comun)]
    assert len(revisar(datos)["DUP_ES"]) >= 1


def test_checks_no_avisa_de_puntuacion_correcta():
    from checks import revisar
    datos = [("Are you sure?", "¿Estas seguro?"), ("Watch out!", "¡Cuidado!")]
    assert revisar(datos)["PUNTUACION"] == []


def test_checks_participio_con_token_de_genero_no_es_vosotros():
    from checks import revisar
    datos = [("Plant the banner", "Plantar el estandarte"),
             ("%commander% stands there", "%commander% está plantad%o_commander% ahí"),
             ("Plant it!", "¡Plantad el estandarte!")]
    assert len(revisar(datos)["REGISTRO"]) == 1


def _corpus_falso(tmp_path, secciones):
    """secciones: [(fichero, [(en, es), ...]), ...] -> ruta a un corpus minimo."""
    lineas = []
    for fichero, pares in secciones:
        lineas.append("    // FILE: scripts\\config\\%s" % fichero)
        for en, es in pares:
            lineas += ["    {", '        en = "%s"' % en, '        es = "%s"' % es, "    }"]
    ruta = tmp_path / "corpus_es.nut"
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return ruta


def test_dup_vecino_detecta_valor_del_vecino_en_la_misma_tabla(tmp_path):
    """La firma real: Lindwurms se quedo con "Trols", el valor de Unholds."""
    from checks import dup_vecino
    ruta = _corpus_falso(tmp_path, [("strings.nut", [
        ("Direwolves", "Lobos huargo"),
        ("Lindwurms", "Trols"),
        ("Unholds", "Trols"),
    ])])
    avisos = dup_vecino(ruta)
    assert len(avisos) == 1
    assert "Lindwurms" in avisos[0] and "Unholds" in avisos[0]


def test_dup_vecino_ve_el_duplicado_que_una_tilde_tapaba(tmp_path):
    """Dos entradas que solo se diferencian en una tilde son la misma traduccion
    con una errata en alguna de las dos, no dos distintas. El comparador pliega
    los acentos para que salgan sin corregir el acento primero. Caso real:
    Nomad Camp y Nomad Encampment decian los dos "Campamento nomada", una con
    tilde y otra sin ella."""
    from checks import dup_vecino

    ruta = _corpus_falso(tmp_path, [("strings.nut", [
        ("Nomad Camp", "Campamento nómada"),
        ("Nomad Encampment", "Campamento nomada"),
    ])])
    avisos = dup_vecino(ruta)
    assert len(avisos) == 1
    assert "solo difieren" in avisos[0]
    assert "Nomad Camp" in avisos[0] and "Nomad Encampment" in avisos[0]


def test_dup_vecino_no_pliega_la_caja(tmp_path):
    """La caja se usa a proposito para distinguir las variantes en mayuscula que
    el juego mantiene aparte, asi que "el Perro" y "El Perro" NO son duplicado."""
    from checks import dup_vecino

    ruta = _corpus_falso(tmp_path, [("character_names.nut", [
        ("the Hound", "el Perro"),
        ("The Hound", "El Perro"),
    ])])
    assert dup_vecino(ruta) == []


def test_dup_vecino_ignora_tablas_distintas(tmp_path):
    """Compartir traduccion entre ficheros distintos es normal y no se avisa."""
    from checks import dup_vecino
    ruta = _corpus_falso(tmp_path, [
        ("strings.nut", [("Unholds", "Trols")]),
        ("item_names.nut", [("Trolls", "Trols")]),
    ])
    assert dup_vecino(ruta) == []


def test_tildes_avisa_siempre_de_las_formas_que_no_son_palabra():
    """El filtro de rareza deja escapar la forma mala cuando se repite mucho:
    "barbaro" salia 7 veces frente a 71 de "barbaro" con tilde y no se avisaba.
    Estas formas no son palabra en espaniol, asi que se avisan siempre."""
    from checks import revisar

    datos = [("A barbarian camp", "Campamento barbaro %d" % i) for i in range(20)]
    avisos = revisar(datos)["TILDES"]
    assert len(avisos) == 20
    assert "bárbaro" in avisos[0]


def test_variantes_avisa_de_rama_perdida():
    """El juego elige una rama al azar dentro de {a|b|c}. Si el espaniol tiene
    menos, la eleccion se descoloca."""
    from checks import revisar

    datos = [("{one|two|three}", "{uno|dos}")]
    avisos = revisar(datos)["VARIANTES"]
    assert len(avisos) == 1 and "pierde 1" in avisos[0]


def test_variantes_no_avisa_si_el_ingles_ya_viene_desparejado():
    """El propio juego trae textos con llaves desparejadas. Lo que importa es que
    el espaniol tenga la MISMA estructura que el ingles, no que este equilibrado:
    21 de 23 casos que parecian rotos lo estaban ya en ingles."""
    from checks import revisar

    datos = [("{a|b", "{a|b")]
    assert revisar(datos)["VARIANTES"] == []


def test_variantes_cuenta_las_llaves_codificadas():
    """El corpus guarda las llaves como \\x7b y \\x7d."""
    from checks import revisar

    datos = [("\\x7bone|two\\x7d", "{uno|dos}")]
    assert revisar(datos)["VARIANTES"] == []


def test_tokens_avisa_de_deformado_y_de_indefinido():
    """Un %token% deformado se le muestra crudo al jugador, y uno que el ingles
    no usa nunca no tiene con que rellenarse. Nadie lo vigilaba y un barrido de
    tildes dejo %región% por %region%."""
    from checks import revisar

    deformado = revisar([("Near %region%", "Cerca de %región%")])["TOKENS"]
    indefinido = revisar([("You see %name%", "Ves a %name% en %townname%")])["TOKENS"]
    assert len(deformado) == 1 and "%región%" in deformado[0]
    assert len(indefinido) == 1 and "%townname%" in indefinido[0]
    # el token deformado no cuenta ademas como texto recortado: el bueno no
    # falta, esta ahi mismo mal escrito
    assert revisar([("Near %region%", "Cerca de %región%")])["RECORTE"] == []


def test_tokens_calla_si_el_ingles_ya_usa_ese_token():
    """Repetir un token que el ingles usa en otra rama es seguro: el evento lo
    define. A veces es el espaniol corrigiendo al ingles, que en event_162
    escribe 'you meet with employer' sin los signos de porcentaje."""
    from checks import revisar

    datos = [("Meet employer. | %employer% pays you",
              "Reunete con %employer%. | %employer% te paga")]
    assert revisar(datos)["TOKENS"] == []


def test_recorte_separa_la_rama_resumida_de_la_rama_perdida():
    """Perder un token con las ramas cuadradas es la firma de una rama traducida
    en resumen, y se repara traduciendo, no tocando marcadores. Si ademas faltan
    ramas, el aviso no se emite: eso ya lo cuenta VARIANTES."""
    from checks import revisar

    resumida = revisar([("He speaks.%SPEECH_ON%Hello.%SPEECH_OFF%Then leaves.",
                         "Habla y luego se marcha.")])
    assert len(resumida["RECORTE"]) == 1 and "%SPEECH_ON%" in resumida["RECORTE"][0]
    assert resumida["TOKENS"] == []

    sin_rama = revisar([("Uno | dos con %name%", "Uno")])
    assert sin_rama["RECORTE"] == [] and sin_rama["TOKENS"] == []
    assert len(sin_rama["VARIANTES"]) == 1


def test_tokens_calla_cuando_coinciden():
    from checks import revisar

    assert revisar([("Near %region%, %name% waits", "%name% espera cerca de %region%")])["TOKENS"] == []


def test_tildes_no_mira_dentro_de_los_marcadores():
    """El interior de <captura>, %token% y [color=...] es sintaxis, no prosa.
    Avisar de que le falta una tilde lleva a romper el par: el nombre de la
    captura tiene que coincidir literalmente con el del ingles. Paso dos veces
    con <vision>."""
    from checks import revisar

    datos = [("Vision <vision:val_tag>", "Visión <vision>")] * 5
    assert revisar(datos)["TILDES"] == []


def test_tildes_no_avisa_de_homografos_protegidos():
    """"perdida" es participio y es correcta sin tilde; no debe avisarse aunque
    exista "perdida" con tilde como sustantivo."""
    from checks import revisar

    datos = [("Lost crypt", "Cripta perdida")]
    assert revisar(datos)["TILDES"] == []


def test_tildes_calla_con_el_subjuntivo_detras_de_una_subordinada():
    """"dondequiera que los encontraran" es subjuntivo y va sin tilde;
    "los encontraran maniana" seria futuro y la llevaria. Solo la subordinada
    los distingue, y sin esta regla dieciocho de veinte avisos eran formas
    perfectamente escritas que enterraban los dos defectos de verdad."""
    from checks import revisar

    # el canon se construye con lo que aparece diez veces o mas
    ruido = [("x", "Los encontrarán mañana en el bosque profundo")] * 10
    subjuntivo = [("Wherever", "Juraron vencerlos dondequiera que los encontraran")]
    assert revisar(ruido + subjuntivo)["TILDES"] == []

    # sin subordinada delante, el aviso sigue saliendo
    suelto = [("Later", "Los encontraran en el bosque profundo mañana")]
    assert len(revisar(ruido + suelto)["TILDES"]) == 1


def test_gt_align_empareja_anclas_y_sustituciones_del_mismo_tamano():
    """Dentro de un bloque igual, i con i. Dentro de un bloque sustituido del
    mismo tamano, tambien. Un hueco de tamanos distintos NO se empareja: eso es
    lo que evita resolver por descarte, que ya demostro ser conjetura."""
    from gt_align import alinea

    a = ["Ancla1", "Cambia", "Ancla2"]
    b = ["Ancla1", "Cambiado", "Ancla2"]
    pares, ambiguos = alinea(a, b)
    assert pares == [(0, 0), (1, 1), (2, 2)]
    assert ambiguos == 0


def test_gt_align_no_empareja_huecos_de_tamano_distinto():
    from gt_align import alinea

    a = ["Ancla1", "Uno", "Ancla2"]
    b = ["Ancla1", "Uno-a", "Uno-b", "Ancla2"]
    pares, ambiguos = alinea(a, b)
    assert (1, 1) not in pares          # el hueco no se resuelve
    assert (0, 0) in pares and (2, 3) in pares   # las anclas si
    assert ambiguos == 1


def test_dup_vecino_ignora_entradas_lejanas(tmp_path):
    """Fuera de la ventana ya no son vecinas: es sinonimia, no desplazamiento."""
    from checks import dup_vecino
    from checks import VENTANA_VECINO
    relleno = [("relleno %d" % i, "relleno %d" % i) for i in range(VENTANA_VECINO + 5)]
    ruta = _corpus_falso(tmp_path, [("strings.nut",
                                     [("Unholds", "Trols")] + relleno + [("Ogres", "Trols")])])
    assert dup_vecino(ruta) == []


def test_check_syntax_acepta_nut_valido_y_rechaza_roto(tmp_path):
    """Si hay interprete Squirrel, debe distinguir un .nut valido de uno roto.
    Sin interprete la comprobacion no aplica y el test se salta."""
    import pytest

    from check_syntax import comprueba, localiza_interprete
    if localiza_interprete() is None:
        pytest.skip("sin interprete Squirrel disponible")

    bueno = tmp_path / "bueno.nut"
    bueno.write_text('local pares = [{en = "Hello", es = "Hola"}];\n', encoding="utf-8")
    roto = tmp_path / "roto.nut"
    roto.write_text('local pares = [{en = "Hello", es = "Hola"};\n', encoding="utf-8")

    _, fallos_bueno = comprueba([bueno])
    assert fallos_bueno == []
    _, fallos_roto = comprueba([roto])
    assert len(fallos_roto) == 1


def test_load_blocks_devuelve_el_parser_como_estaba(tmp_path):
    """load_blocks toma prestados los globales de modulo de rosetta.py, asi que
    tiene que dejarlos como los encontro.

    Si no lo hace, el parser se queda en lang="es" con los acumuladores llenos y
    la suite de upstream falla al correr en el mismo proceso que la nuestra: sus
    tests esperan el idioma por defecto y un KNOWN_WORDS limpio.
    """
    import rosetta

    f = tmp_path / "fixture_es.nut"
    f.write_text(FIXTURE, encoding="utf-8")

    antes = {
        "lang": rosetta.OPTS["lang"],
        "quiet": rosetta.OPTS["quiet"],
        "known_words": set(rosetta.KNOWN_WORDS),
        "ref_blocks": dict(rosetta.REF_BLOCKS),
        "ref_pairs": dict(rosetta.REF_PAIRS),
        "dup_blocks": list(rosetta.DUP_BLOCKS),
    }

    assert len(load_blocks(f)) == 4

    assert rosetta.OPTS["lang"] == antes["lang"]
    assert rosetta.OPTS["quiet"] == antes["quiet"]
    assert set(rosetta.KNOWN_WORDS) == antes["known_words"]
    assert dict(rosetta.REF_BLOCKS) == antes["ref_blocks"]
    assert dict(rosetta.REF_PAIRS) == antes["ref_pairs"]
    assert list(rosetta.DUP_BLOCKS) == antes["dup_blocks"]


FIXTURE_DUPS = '''if (!("Rosetta" in getroottable())) return;

local rosetta = {
    mod = {id = "vanilla", version = "0.0.0"}
    author = "test"
    lang = "es"
}
local pairs = [
    {
        en = "Repetido"
        es = "Primero"
    }
    {
        en = "Repetido"
        es = "Segundo"
    }
    {
        en = "Unico"
        es = "Solo"
    }
]
::Rosetta.add(rosetta, pairs);
'''


def test_load_blocks_conserva_el_recuento_de_dups(tmp_path):
    """El recuento de `en` repetidos que informa el build tiene que sobrevivir a
    la restauracion del parser: rosetta.DUP_BLOCKS vuelve a su valor previo al
    salir del contexto, asi que el dato se guarda dentro."""
    from build_dist import DUPS_DEL_ULTIMO_LOAD

    f = tmp_path / "dups_es.nut"
    f.write_text(FIXTURE_DUPS, encoding="utf-8")

    bloques = load_blocks(f)
    assert len(bloques) == 2
    assert len(DUPS_DEL_ULTIMO_LOAD) == 1


def test_ui_addon_lleva_solo_ui_y_ningun_directorio(tmp_path):
    """El criterio que se verifico en partida: el zip del addon contiene solo
    ui/. Las fuentes van en carpeta suelta gfx/ porque el renderizador las carga
    por ruta de disco; metidas en el zip, el error de entrada/salida persiste
    (KNOWN_ISSUES punto 7). Sin entradas de directorio: el contenido del zip es
    exactamente la lista de ficheros."""
    import zipfile

    from build_ui_addon import construye

    destino = tmp_path / "addon.zip"
    arcos = construye(destino)
    assert arcos, "el addon no puede salir vacio"
    with zipfile.ZipFile(destino) as z:
        infos = z.infolist()
    assert [i.filename for i in infos] == arcos
    assert all(i.filename.startswith("ui/") for i in infos)
    assert all(i.filename.endswith(".js") for i in infos)
    assert not any(i.is_dir() for i in infos)


def test_ui_addon_es_determinista(tmp_path):
    """Mismos fuentes, mismo artefacto byte a byte: las entradas llevan fecha
    fija. Asi se puede afirmar que lo construido es lo que se verifico, en vez
    de suponerlo."""
    from build_ui_addon import construye

    a, b = tmp_path / "a.zip", tmp_path / "b.zip"
    construye(a)
    construye(b)
    assert a.read_bytes() == b.read_bytes()


def test_ui_addon_rechaza_lo_que_no_es_ui(tmp_path):
    """Empaquetar algo que no sea ui/ tiene que romper el build, no colarse: el
    fallo solo se nota jugando."""
    import pytest

    from build_ui_addon import construye

    suelto = tmp_path / "misc.css"
    suelto.write_text("body {}", encoding="utf-8")
    with pytest.raises(SystemExit):
        construye(tmp_path / "addon.zip", [(suelto, "ui/mods/msu/css/misc.css"),
                                           (suelto, "gfx/fonts/cinzel/x.ttf")])


def test_ui_addon_no_distribuye_los_ficheros_excluidos(tmp_path):
    """Los dos .js que no se distribuyen no pueden reaparecer en src/ui: uno le
    quita al jugador el cuarto boton de velocidad del mapa y el otro es identico
    al del juego. Volver a meterlos es un fallo de construccion, no una
    regresion silenciosa."""
    import pytest

    from build_ui_addon import EXCLUIDOS, construye, ficheros

    presentes = {arco for _, arco in ficheros()}
    assert not (presentes & set(EXCLUIDOS)), "un excluido volvio a src/ui"

    # y si vuelve, el build aborta en vez de empaquetarlo
    arco = next(iter(EXCLUIDOS))
    suelto = tmp_path / "vuelto.js"
    suelto.write_text("// da igual el contenido", encoding="utf-8")
    with pytest.raises(SystemExit):
        construye(tmp_path / "addon.zip", [(suelto, arco)])


def _juego_falso(tmp_path, ficheros):
    """Un .dat de juego de mentira: un zip con las rutas ui/ que se le pidan."""
    import zipfile

    dat = tmp_path / "data_001.dat"
    with zipfile.ZipFile(dat, "w") as z:
        for arco, texto in ficheros.items():
            z.writestr(arco, texto)
    return dat


def _capa(tmp_path, ficheros):
    """Un src/ui de mentira con los .js que se le pidan."""
    raiz = tmp_path / "src" / "ui"
    for arco, texto in ficheros.items():
        p = raiz.parent / arco
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(texto, encoding="utf-8")
    return raiz


VANILLA_JS = """\
Modulo.prototype.crea = function ()
{
    this.mBoton = layout.createImageButton(Asset.PLAY, function ()
    {
        self.pulsa();
    });
    this.mTexto = $('<div>Day </div>');
};
"""


def test_drift_calla_si_solo_cambia_el_texto(tmp_path):
    """Traducir cambia literales, y eso no es deriva. Si esto no callara, la
    herramienta avisaria de los 36 ficheros y nadie la volveria a mirar."""
    import zipfile

    from check_ui_drift import revisa

    arco = "ui/screens/x.js"
    dat = _juego_falso(tmp_path, {arco: VANILLA_JS})
    src = _capa(tmp_path, {arco: VANILLA_JS.replace("Day ", "Dia ")})
    assert revisa(zipfile.ZipFile(dat), src) == []


def test_drift_ve_el_codigo_que_le_falta_a_nuestra_copia(tmp_path):
    """El fallo real que hay que cazar: el juego gana un boton y nuestra copia,
    mas vieja, lo tapa. Es lo que paso con el reloj de la barra superior."""
    import zipfile

    from check_ui_drift import CODIGO, revisa

    arco = "ui/screens/x.js"
    nuevo = VANILLA_JS.replace(
        "    this.mTexto",
        "    this.mBotonRapido = layout.createImageButton(Asset.FAST);\n"
        "    this.mTexto")
    dat = _juego_falso(tmp_path, {arco: nuevo})
    src = _capa(tmp_path, {arco: VANILLA_JS})

    avisos = revisa(zipfile.ZipFile(dat), src)
    assert [(c, a) for c, a, _, _ in avisos] == [(CODIGO, arco)]
    quita = avisos[0][2]
    assert quita == 1, "la linea que el juego tiene y nosotros no"


def test_drift_avisa_del_fichero_que_ya_no_traduce_nada(tmp_path):
    """Identico al del juego: peso muerto que congela esa copia en la siguiente
    actualizacion. Es el caso de character_screen_paperdoll_module.js."""
    import zipfile

    from check_ui_drift import SIN_TRADUCIR, revisa

    arco = "ui/screens/x.js"
    dat = _juego_falso(tmp_path, {arco: VANILLA_JS})
    src = _capa(tmp_path, {arco: VANILLA_JS})
    assert [c for c, _, _, _ in revisa(zipfile.ZipFile(dat), src)] == [SIN_TRADUCIR]


def test_drift_avisa_del_fichero_que_el_juego_ya_no_tiene(tmp_path):
    """Si el juego renombra o quita el modulo, nuestra copia no sustituye nada."""
    import zipfile

    from check_ui_drift import AUSENTE, revisa

    dat = _juego_falso(tmp_path, {"ui/screens/otro.js": VANILLA_JS})
    src = _capa(tmp_path, {"ui/screens/x.js": VANILLA_JS})
    assert [c for c, _, _, _ in revisa(zipfile.ZipFile(dat), src)] == [AUSENTE]


def test_drift_solo_acepta_el_aviso_con_las_cuentas_que_se_juzgaron():
    """Un aviso ya juzgado no vuelve a sonar, o se aprende a ignorar la
    herramienta. Pero si el juego mueve OTRA VEZ ese fichero, las cuentas
    cambian y tiene que reaparecer: por eso van fijadas."""
    from check_ui_drift import ACEPTADOS, CODIGO, SIN_TRADUCIR, esta_aceptado

    arco, (cuentas, motivo) = next(iter(ACEPTADOS.items()))
    assert motivo.strip(), "un aceptado sin motivo escrito no vale"
    assert esta_aceptado(CODIGO, arco, *cuentas)
    assert not esta_aceptado(CODIGO, arco, cuentas[0] + 1, cuentas[1])
    # y aceptar una divergencia de codigo no perdona las otras clases
    assert not esta_aceptado(SIN_TRADUCIR, arco, 0, 0)


def test_drift_no_hay_deriva_en_la_capa_que_se_distribuye():
    """La capa del repo cuadra con el juego, o el aviso esta juzgado. Si no hay
    juego a mano el test no aplica: no se puede comparar con nada."""
    import pytest

    from check_ui_drift import abre_datos, data_dir_del_env, esta_aceptado, revisa

    ruta = data_dir_del_env()
    if not ruta:
        pytest.skip("sin DATA_DIR en .env: no hay juego con el que comparar")
    _, zjuego = abre_datos(ruta)
    nuevos = [a for a in revisa(zjuego) if not esta_aceptado(*a)]
    assert nuevos == [], "deriva sin juzgar: %s" % nuevos


def test_los_dos_zips_y_los_dos_preloads_declaran_la_misma_version():
    """Una sola version del pack para todo lo que se distribuye. Si un preload
    se queda atras, el juego y MSU reportan una version que no es la del zip."""
    import re as _re

    from build_dist import PACK_VERSION, SRC
    from build_ui_addon import UI_VERSION

    assert UI_VERSION == PACK_VERSION
    assert _re.fullmatch(r"\d+\.\d+\.\d+", PACK_VERSION), PACK_VERSION
    preloads = sorted((SRC / "scripts" / "!mods_preload").glob("*.nut"))
    assert len(preloads) == 2, preloads
    for p in preloads:
        m = _re.search(r'Version = "([^"]+)"', p.read_text(encoding="utf-8"))
        assert m and m.group(1) == PACK_VERSION, (p.name, m and m.group(1))


def test_la_ficha_de_msu_declara_la_build_y_la_cobertura_de_build_dist():
    import re as _re

    from build_dist import COBERTURA_JUEGO, COBERTURA_LEGENDS, GAME_VERSION, LEGENDS_VERSION, SRC

    t = (SRC / "scripts" / "!mods_preload" / "mod_battle_brothers_es.nut").read_text(encoding="utf-8")
    assert _re.search(r'GameVersion = "([^"]+)"', t).group(1) == GAME_VERSION
    assert _re.search(r'Cobertura = "([^"]+)"', t).group(1) == COBERTURA_JUEGO
    assert _re.search(r'LegendsVersion = "([^"]+)"', t).group(1) == LEGENDS_VERSION
    assert _re.search(r'CoberturaLegends = "([^"]+)"', t).group(1) == COBERTURA_LEGENDS


RUNTIME_FALSO = r'''::Rosetta <- {
    ID = "mod_rosetta"
    Version = "%(version)s"

    patternRe = regexp(@"([^<]+)|<(\w+):(\w+)>")
    subRes = (function () {
        local open = @"\[[^\]]+\]", close = @"\[/[^\]]+\]";
        local res = {
%(tipos)s        }
        foreach (key in [%(contag)s])
            res[key + "_tag"] <- open + res[key] + close;

        return Table.mapValues(res, @(k, v) regexp(v));
    })()
    function validateRule(_lang, _rule) {
        local labels = {};
        %(extra)s
    }
    function parsePattern(_pat) {
        return Re.all(_pat, patternRe);
    }
    function parseReplacement(_str) {
        return Re.all(_str, replacePartRe);
    }
}
'''


def _runtime(tipos=("int", "val", "word", "str", "line", "tag", "img"),
             contag=('"int"', '"val"', '"str"'), version="0.4.0", extra=""):
    cuerpo = "".join("            %s = @\"x\"\n" % t for t in tipos)
    return RUNTIME_FALSO % {"tipos": cuerpo, "contag": " ".join(contag),
                            "version": version, "extra": extra}


def test_upstream_los_tipos_de_sub_del_runtime_real_son_los_que_build_dist_cree():
    """El espejo que de verdad importa. build_dist.SUBS es una copia a mano del
    subRes del runtime, y si upstream anade un tipo, el build empieza a mandar a
    cuarentena pares validos sin decir nada. Esto lo deriva del runtime y
    compara, asi que la copia no puede quedarse atras en silencio."""
    from build_dist import SUBS
    from check_upstream_drift import lee_runtime, subs_del_runtime

    texto, _ = lee_runtime()
    assert subs_del_runtime(texto) == SUBS


def test_upstream_ve_un_tipo_de_sub_nuevo():
    """Upstream anade un tipo: hay que enterarse, porque los pares que lo usen
    estan yendo a cuarentena siendo validos."""
    from check_upstream_drift import revisa

    avisos = revisa(_runtime(tipos=("int", "val", "word", "str", "line",
                                    "tag", "img", "date")))
    espejo = [a for a in avisos if a[0] == "ESPEJO"]
    assert len(espejo) == 1
    assert "date" in espejo[0][2]
    assert "cuarentena" in espejo[0][2]


def test_upstream_ve_un_tipo_de_sub_retirado():
    """El caso peligroso, y el mensaje tiene que decir por que: distribuiriamos
    pares que el runtime rechaza al cargar, y eso aborta la traduccion entera en
    la partida de quien lo instale."""
    from check_upstream_drift import revisa

    avisos = revisa(_runtime(tipos=("int", "val", "word", "str", "line", "tag")))
    espejo = [a for a in avisos if a[0] == "ESPEJO"]
    assert len(espejo) == 1
    assert "img" in espejo[0][2]
    assert "aborta" in espejo[0][2]


def test_upstream_ve_que_validateRule_ha_cambiado():
    """No se puede comparar una logica reimplementada con su original, asi que
    se fija el hash y se avisa. Un cambio no significa roto: significa ir a
    leerlo."""
    from check_upstream_drift import revisa

    avisos = revisa(_runtime(extra="if (algo) throw 'regla nueva';"))
    contratos = [a for a in avisos if a[0] == "CONTRATO"]
    assert any(q == "validateRule" for _, q, _ in contratos)


def test_upstream_ve_la_version_declarada_distinta():
    # Una version cualquiera que no sea la esperada, para que el test no
    # caduque cada vez que la adopcion de una release mueva el pin.
    from check_upstream_drift import revisa

    avisos = revisa(_runtime(version="9.9.9"))
    assert any(c == "VERSION" and "9.9.9" in d for c, _, d in avisos)


def test_upstream_falla_a_gritos_si_no_reconoce_el_bloque_subRes():
    """Un espejo que se queda a medias en silencio es peor que un error: manda
    pares buenos a cuarentena sin avisar. Si upstream reestructura ese bloque,
    esto tiene que romper."""
    import pytest

    from check_upstream_drift import subs_del_runtime

    with pytest.raises(SystemExit):
        subs_del_runtime("::Rosetta <- { Version = \"0.4.0\" }")


# --- shift_detect: deteccion de ventanas de corrimiento ---

def test_shift_tramos_agrupa_indices_seguidos_y_respeta_el_margen():
    """Un corrimiento aparece a saltos, no en bloque, asi que un hallazgo de un
    solo indice vale. Los que no llegan al margen no entran."""
    from shift_detect import tramos_positivos

    deltas = {0: 20.0, 1: 18.0, 2: 0.5, 3: 17.0, 4: None, 5: 16.0}
    assert tramos_positivos(deltas, 15.0) == [[0, 1], [3], [5]]
    assert tramos_positivos(deltas, 19.0) == [[0]]


def test_shift_puntua_ignora_los_enlaces_sin_apoyo():
    """El modelo se entrena con el corpus, corrimientos incluidos. Si una pareja
    de palabras sale de un solo par, ese par se avalaria a si mismo. Solo cuentan
    los enlaces atestiguados en dos pares o mas."""
    from shift_detect import APOYO_MIN, PISO, puntua

    t = {"madness": {"locura": 0.9, "escultor": 0.9}}
    apoyo = {("madness", "locura"): 14, ("madness", "escultor"): 1}

    con_apoyo = puntua(t, apoyo, ["madness"], ["locura"])
    sin_apoyo = puntua(t, apoyo, ["madness"], ["escultor"])
    assert APOYO_MIN == 2
    assert con_apoyo > sin_apoyo
    assert sin_apoyo == PISO, "sin apoyo tiene que caer al piso, no puntuar alto"
    assert puntua(t, apoyo, [], ["locura"]) is None


# Bloque de contexto: da apoyo cruzado a lobo/wolf y zorro/fox desde fuera de la
# tabla, que es lo que permite juzgarla sin que se avale a si misma.
CONTEXTO = [
    ("the wolf hunts alone tonight", "el lobo caza solo esta noche"),
    ("a wolf crosses the frozen river", "un lobo cruza el rio helado"),
    ("the wolf pack circles the camp", "la manada de lobo rodea el campamento"),
    ("the fox slips into the henhouse", "el zorro entra en el gallinero"),
    ("a fox watches from the bushes", "un zorro vigila desde los arbustos"),
    ("the fox escapes with a chicken", "el zorro escapa con una gallina"),
]


def test_shift_detecta_una_tabla_con_los_valores_cruzados():
    """La prueba que importa: dos entradas de una tabla con el valor de la otra.
    Es la firma del corrimiento, y el detector tiene que verla apoyandose en el
    lexico que aprendio FUERA de esa tabla."""
    from shift_detect import modelo, revisa

    tabla = [("Wolf", "Zorro"), ("Fox", "Lobo")]
    grupos = [("contexto.nut", CONTEXTO), ("tabla.nut", tabla)]
    t, apoyo = modelo(grupos)

    hallazgos = [h for h in revisa(grupos, t, apoyo) if h["fichero"] == "tabla.nut"]
    assert hallazgos, "no vio la tabla cruzada"
    propuestas = {(i, prop) for h in hallazgos for i, _, _, prop in h["pares"]}
    assert (0, "Lobo") in propuestas or (1, "Zorro") in propuestas


def test_shift_calla_con_una_tabla_bien_alineada():
    """Y no puede gritar cuando la tabla esta bien, o no sirve de nada."""
    from shift_detect import modelo, revisa

    tabla = [("Wolf", "Lobo"), ("Fox", "Zorro")]
    grupos = [("contexto.nut", CONTEXTO), ("tabla.nut", tabla)]
    t, apoyo = modelo(grupos)

    assert [h for h in revisa(grupos, t, apoyo) if h["fichero"] == "tabla.nut"] == []


# --- shift_window: ampliacion de hits hasta sus fronteras reales ---

CONTEXTO_VENTANA = [
    ("the wolf hunts alone", "el lobo caza solo"),
    ("a grey wolf howls", "un lobo gris aulla"),
    ("the fox is cunning", "el zorro es astuto"),
    ("a red fox flees", "un zorro rojo huye"),
    ("the bear sleeps in winter", "el oso duerme en invierno"),
    ("a brown bear roars", "un oso pardo ruge"),
    ("the deer runs through the forest", "el ciervo corre por el bosque"),
    ("a young deer grazes", "un ciervo joven pasta"),
]

# Corrimiento k=-1 sobre 1..3: el valor de cada una esta en la anterior.
# "Qux" y "Plonk" son unicos en el corpus: entradas ciegas, como Bloodthirster.
TABLA_CORRIDA = [
    ("Bear", "Oso"),      # 0 bien alineada
    ("Qux", "Lobo"),      # 1 ciega para si misma, fuente de la 2
    ("Wolf", "Zorro"),    # 2 corrida: su valor esta en 1
    ("Fox", "Plonk"),     # 3 corrida: su valor esta en 2
    ("Deer", "Ciervo"),   # 4 bien alineada: la recuperacion
]


def _ventana_sobre(tabla, semilla, k):
    from align_score import VACIAS_EN, VACIAS_ES, palabras
    from shift_detect import modelo, puntua
    from shift_window import crece

    grupos = [("contexto.nut", CONTEXTO_VENTANA), ("tabla.nut", tabla)]
    t, apoyo = modelo(grupos)
    pal = [(palabras(en, VACIAS_EN), palabras(es, VACIAS_ES))
           for en, es in tabla]
    base = [puntua(t, apoyo, pe, ps) for pe, ps in pal]
    return crece(t, apoyo, pal, base, semilla, k)


def test_ventana_atraviesa_ciegos_y_para_en_la_recuperacion():
    """El corazon de la idea: el crecimiento cruza entradas sin senial (la 1,
    'Qux', es ciega) y solo se detiene ante evidencia POSITIVA de que el vecino
    esta bien alineado (la 4, Deer/Ciervo, atestiguada). Ausencia de senial no
    es frontera."""
    from shift_window import APOYA, CIEGO, crece  # noqa: F401

    v = _ventana_sobre(TABLA_CORRIDA, semilla=2, k=-1)
    assert v["nucleo"] == [2, 3]
    assert v["ext_arriba"] == [1], "la ciega se cruza y queda como incierta"
    assert v["fronteras"][+1] == "recupera"
    assert v["fronteras"][-1] in ("recupera", "borde")


def test_reparacion_distingue_fuente_firme_incierta_y_sobrante():
    """La leccion de la primera aceptacion: a Madness (57) se le declaraba
    huerfana con 'Locura' ahi mismo, en la extension. Una fuente en zona
    incierta se propone, marcada para ratificar; huerfana es solo cuando la
    fuente cae en territorio bien alineado."""
    from shift_window import reparacion

    v = _ventana_sobre(TABLA_CORRIDA, semilla=2, k=-1)
    rep = reparacion(v, TABLA_CORRIDA)
    assert rep["mueve"] == [(3, "Plonk", "Zorro")]
    assert rep["mueve_incierto"] == [(2, "Zorro", "Lobo")]
    assert rep["huerfanas"] == []
    assert rep["sobrantes"] == [(3, "Plonk")]


def test_reparacion_declara_huerfana_cuando_la_fuente_es_de_otro():
    """Semilla manual (estilo censo) pegada a una frontera firme: la fuente de
    la entrada corrida pertenece a un vecino bien alineado y NO se puede tomar.
    Eso si es huerfana: su texto correcto no existe en el fichero."""
    from shift_window import reparacion

    tabla = [
        ("Deer", "Ciervo"),   # 0 bien alineada
        ("Bear", "Oso"),      # 1 bien alineada: su valor no es de nadie mas
        ("Wolf", "Zorro"),    # 2 semilla manual, k=-1: fuente en 1, vetada
        ("Fox", "Un zorro rojo huye"),  # relleno para que 3 no dispare
    ]
    v = _ventana_sobre(tabla, semilla=2, k=-1)
    rep = reparacion(v, tabla)
    assert rep["huerfanas"] == [(2, "Wolf")]
    assert rep["mueve"] == [] and rep["mueve_incierto"] == []
    assert rep["sobrantes"] == [(2, "Zorro")]


def test_ventanas_solapadas_con_k_distinto_quedan_en_conflicto():
    """Una insercion no produce dos desplazamientos distintos sobre el mismo
    tramo: si dos ventanas se solapan con k distinto, una es coincidencia
    semantica (el caso Sellsword's/Mercenary's) y decide el censo."""
    from shift_window import APOYA, CIEGO, marca_conflictos

    a = {"fichero": "f.nut", "k": -1, "estados": {5: APOYA, 6: CIEGO}}
    b = {"fichero": "f.nut", "k": 2, "estados": {6: APOYA}}
    c = {"fichero": "otro.nut", "k": 2, "estados": {6: APOYA}}
    marca_conflictos([a, b, c])
    assert a["conflictos"] == [2]
    assert b["conflictos"] == [-1]
    assert "conflictos" not in c


def test_censo_reconcilia_por_en_y_no_por_indice(tmp_path, monkeypatch):
    """El registro del censo no puede depender de la posicion del par: en cuanto
    alguien anada una entrada a un fichero, todo lo que va detras se desplaza y
    los veredictos apuntarian a entradas equivocadas, sin fallar a gritos.
    TAREA-cobertura mide precisamente eso y su precedente anadio 23 pares."""
    import blind_census as bc

    registro = tmp_path / "CENSO.tsv"
    registro.write_text(
        "fichero\tindice\tveredicto\ten\tes\tnota\n"
        "item_names.nut\t7\tok\tSword\tEspada\t\n",
        encoding="utf-8")
    monkeypatch.setattr(bc, "REGISTRO", registro)

    hecho = bc.lee_registro()
    assert hecho == {("item_names.nut", "Sword"): "ok"}

    # La misma entrada, ahora en la posicion 9 porque se anadieron dos pares
    # antes. Tiene que seguir contando como juzgada.
    filas = [("item_names.nut", 9, "Sword", "Espada", "juzgar"),
             ("item_names.nut", 10, "Axe", "Hacha", "juzgar")]
    assert bc.ventanas(filas, "item_names.nut", hecho) == [[10]]


def test_censo_escapa_los_saltos_de_linea_al_ir_y_al_volver():
    """Los valores del corpus llevan saltos de linea de verdad, no la secuencia
    \n, porque get_field los interpreta al leer. Sin escaparlos, un solo par con
    salto parte la fila del TSV y la cola se vuelve ilegible."""
    from blind_census import desescapa, escapa

    crudo = "linea uno\nlinea dos\tcon tabulador\\y barra"
    assert "\n" not in escapa(crudo) and "\t" not in escapa(crudo)
    assert desescapa(escapa(crudo)) == crudo


# measure_coverage.py necesita el arbol del juego, stdlib descomprimido y un
# interprete Squirrel para su medida real (como check_ui_drift.py y
# gt_align.py, es una excepcion a "ninguna necesita recursos externos"), asi
# que aqui solo se prueban las partes que no dependen de ellos: la
# agrupacion por familia, el parseo de la extraccion, y el cruce contra los
# cubos drop/wip del corpus (que si esta siempre disponible en el repo).

EXTRACCION_FIXTURE = '''    // FILE: /juego/scripts/items/weapons/dagger.nut
    {
        en = "Dagger"
        es = ""
    }
    {
        mode = "pattern"
        en = "<actor> gains <v> Experience"
        es = ""
    }
    // FILE: /juego/scripts/ui/screens/menu/main_menu_screen.nut
    {
        en = "Continue"
        es = ""
    }
'''


def test_medida_familia_es_el_primer_directorio_bajo_scripts():
    from measure_coverage import familia

    scripts_dir = Path("/juego/scripts")
    assert familia("/juego/scripts/items/weapons/dagger.nut", scripts_dir) == "items"
    assert familia("/juego/scripts/ui/screens/x.nut", scripts_dir) == "ui"
    # con separador de Windows, que es como los da rosetta.py -les en este repo
    assert familia(r"D:\juego\scripts\config\strings.nut",
                   Path(r"D:\juego\scripts")) == "config"


def test_medida_parsea_fichero_familia_modo_y_en_en_orden():
    from measure_coverage import parse_literales

    literales = parse_literales(EXTRACCION_FIXTURE, Path("/juego/scripts"))
    assert [(rel, fam, modo, en) for rel, fam, modo, en, in literales] == [
        ("items/weapons/dagger.nut", "items", "", "Dagger"),
        ("items/weapons/dagger.nut", "items", "pattern", "<actor> gains <v> Experience"),
        ("ui/screens/menu/main_menu_screen.nut", "ui", "", "Continue"),
    ]


def test_medida_corpus_pendiente_separa_estatico_de_patron_por_cubo():
    """Reusa el clasificador real de build_dist (dist/wip/drop), no una regla
    propia: si el corpus o build_dist cambian de forma, esto se entera por el
    mismo camino que build_dist en vez de quedarse ciego en silencio."""
    import build_dist
    from measure_coverage import corpus_pendiente

    static_en, drop_pattern_en, wip_pattern_en = corpus_pendiente()
    # Anclado al clasificador real, no a una cadena concreta: el caso que
    # usaba antes (Aalbek, toponimo en drop) dejo de ser pendiente cuando la
    # adjudicacion de vacios del 27/08 lo resolvio con es = en, y cualquier
    # otra cadena concreta caducaria igual. La invariante que si es estable:
    # los tres cubos juntos son exactamente los bloques no-dist con en.
    bloques = build_dist.load_blocks(build_dist.CORPUS)
    no_dist = [b for b in bloques
               if build_dist.classify(b) != "dist"
               and build_dist.get_field(b, "en") is not None]
    assert len(static_en) + len(drop_pattern_en) + len(wip_pattern_en) \
        == len(no_dist)
    assert all(isinstance(en, str) for en in static_en)
    assert all(isinstance(en, str) for en in drop_pattern_en)
    assert all(isinstance(en, str) for en in wip_pattern_en)


def test_medida_sin_mod_carga_solo_el_base_y_con_mod_el_base_y_el_suyo():
    """Un par de Legends no puede inflar la cifra del juego base; al medir
    Legends hacen falta los dos, porque Legends reutiliza textos del juego, y\n    claves.nut delante del suyo, como en el preload."""
    import pytest

    import build_dist
    from measure_coverage import PACK, objetivo

    assert objetivo() == ([build_dist.CORPUS], [PACK])
    legends = build_dist.CORPUS.parent / "mod_legends_es.nut"
    assert objetivo("mod_legends") == ([build_dist.CORPUS, legends],
                                       [PACK, PACK.parent / "claves.nut", PACK.parent / "mod_legends_es.nut"])
    with pytest.raises(SystemExit):
        objetivo("mod_que_no_existe")


def test_la_sonda_de_cobertura_carga_todos_los_packs_que_se_le_pasan(tmp_path, monkeypatch):
    """Con el runtime real: un literal de cada pack sale cubierto y uno que no
    está en ninguno sale hueco. Sin intérprete Squirrel o sin stdlib, se salta."""
    import pytest

    import measure_coverage
    from build_dist import cabecera, emit
    from check_syntax import localiza_interprete

    sq = localiza_interprete()
    if sq is None:
        pytest.skip("sin interprete Squirrel disponible")
    stdlib = _stdlib_descomprimido(tmp_path / "stdlib")
    if stdlib is None:
        pytest.skip("sin stdlib (STDLIB_DIR o DATA_DIR en .env)")
    base, mod = tmp_path / "base_es.nut", tmp_path / "mod_x_es.nut"
    emit(base, ['{\n    en = "Dagger"\n    es = "Daga"\n}'])
    emit(mod, ['{\n    en = "Legend sword"\n    es = "Espada de leyenda"\n}'], cabecera("mod_x", "1.2.3"))
    monkeypatch.setattr(measure_coverage, "DATOS_PROBE", tmp_path / "cov_literales.nut")
    literales = [("a.nut", "a", "", en) for en in ("Dagger", "Legend sword", "Nowhere")]
    measure_coverage.escribe_datos_probe(literales, [], [])
    salida = measure_coverage.corre_sonda(sq, stdlib, [base, mod])
    assert [l.split("\t")[1] for l in salida.splitlines() if l.strip()] == ["OK_DIRECTO", "OK_DIRECTO", "HUECO"]


def test_las_entradas_de_zip_no_dependen_del_sistema():
    """La CI construye en Linux los zips de la release, y tienen que ser los
    mismos byte a byte que los de Windows. zipfile rellena el sistema de origen
    segun la plataforma y la fecha segun el fichero; entrada_zip fija las dos."""
    from build_dist import FECHA_FIJA, entrada_zip

    info = entrada_zip("mod_battle_brothers_es/base_es.nut")
    assert info.create_system == 3
    assert info.date_time == FECHA_FIJA
    assert info.external_attr == 0o644 << 16


def test_el_modo_estricto_falla_solo_por_lo_que_debe():
    """La CI pasa --estricto. Tiene que fallar si sube un aviso, si hay
    cuarentena o si no se pudo comprobar la sintaxis, y nada mas."""
    from build_dist import LINEA_BASE, problemas_estrictos

    assert problemas_estrictos(True, dict(LINEA_BASE), 0) == []
    assert problemas_estrictos(True, {k: 0 for k in LINEA_BASE}, 0) == []
    subido = dict(LINEA_BASE, TILDES=LINEA_BASE["TILDES"] + 1)
    assert len(problemas_estrictos(True, subido, 0)) == 1
    assert len(problemas_estrictos(True, dict(LINEA_BASE, CONTROL=1), 0)) == 1
    assert len(problemas_estrictos(False, dict(LINEA_BASE), 0)) == 1
    assert len(problemas_estrictos(True, dict(LINEA_BASE), 3)) == 1
    assert len(problemas_estrictos(True, None, 0)) == 1


def test_la_vigilancia_de_msu_ve_piezas_que_faltan_y_textos_sin_par(tmp_path):
    from check_msu_drift import Fuente, PIEZAS, piezas_que_faltan, textos_sin_par

    for fichero, texto, _ in PIEZAS:
        f = tmp_path / fichero
        f.parent.mkdir(parents=True, exist_ok=True)
        with f.open("a", encoding="utf-8") as h:
            h.write(texto + "\n")
    teclas = tmp_path / "msu" / "vanilla_mod" / "vanilla_keybinds.nut"
    teclas.parent.mkdir(parents=True, exist_ok=True)
    teclas.write_text('add("x", "Open the Map Screen", "ShowPopup")\n// "Comentado del todo"\n', encoding="utf-8")

    assert piezas_que_faltan(Fuente(tmp_path)) == []
    sin_par = textos_sin_par(Fuente(tmp_path), 'en = "Otro texto"\n')
    assert [s for s, _ in sin_par] == ["Open the Map Screen"]

    boton = tmp_path / "ui/mods/msu/ui_hooks/main_menu_module.js"
    boton.write_text(boton.read_text(encoding="utf-8").replace('"Mod Options"', '"Mod Settings"'), encoding="utf-8")
    assert [t for _, t, _ in piezas_que_faltan(Fuente(tmp_path))] == ['createTextButton("Mod Options"']


def test_cada_mod_tiene_su_corpus_y_el_preload_lo_carga_solo_si_esta():
    """El build mete en el zip un corpus por mod de MODS; si el preload no lo
    incluye, o lo incluye sin mirar si el mod está, la traducción no llega o
    se carga en partidas sin ese mod."""
    import re as _re

    from build_dist import CORPUS, MODS, SRC, corpus_del_pack

    corpus = corpus_del_pack()
    assert corpus[0]["ruta"] == CORPUS and corpus[0]["id"] == "vanilla"
    assert [c["id"] for c in corpus[1:]] == list(MODS)
    t = (SRC / "scripts" / "!mods_preload" / "mod_battle_brothers_es.nut").read_text(encoding="utf-8")
    for c in corpus[1:]:
        assert c["ruta"].is_file(), c["ruta"]
        assert _re.fullmatch(r"\d+(\.\d+)*", c["version"]), c["version"]
        bloque = _re.search(r'mod\.queue\(">%s".*?\n\}\);' % c["id"], t, _re.S)
        assert bloque, "el preload no encola nada tras %s" % c["id"]
        assert '::Hooks.hasMod("%s")' % c["id"] in bloque.group(0)
        assert '::include("mod_battle_brothers_es/%s")' % c["ruta"].stem in bloque.group(0)
    # El corpus base se sigue cargando siempre, fuera de cualquier cola.
    assert '\n::include("mod_battle_brothers_es/base_es");' in t


def test_la_cabecera_de_un_mod_declara_su_id_y_su_version(tmp_path):
    from build_dist import cabecera, emit

    out = tmp_path / "mod_x_es.nut"
    emit(out, ['{\n    en = "A"\n    es = "B"\n}'], cabecera("mod_x", "1.2.3"))
    texto = out.read_text(encoding="utf-8")
    assert 'mod = {id = "mod_x", version = "1.2.3"}' in texto
    assert texto.endswith("::Rosetta.add(rosetta, pairs);\n")


def test_feminizar_titulos():
    from titulos import feminizar

    casos = {
        "el Valiente": "la Valiente",          # -e, solo cambia el artículo
        "el Viejo": "la Vieja",                # -o
        "el Sanador": "la Sanadora",           # -or
        "el Soplón": "la Soplona",             # -ón
        "el Charlatán": "la Charlatana",       # -án
        "el Bailarín": "la Bailarina",         # -ín
        "el Lobo Solitario": "la Loba Solitaria",
        "el Cazador de brujas": "la Cazadora de brujas",  # corta en la preposición
        "el Hijo secreto": "la Hija secreta",
        "el Que no muere": "la Que no muere",
        "el Sin techo": "la Sin techo",
        "el Príncipe del Desierto": "la Princesa del Desierto",  # irregular
        "el Barón Ladrón": "la Baronesa Ladrona",
        "el Hombre cabra": "la Mujer cabra",
        "el Mayor": "la Mayor",                # invariable
        "el Martillo": "la Martillo",
        "el Buitre Dorado": "la Buitre Dorado",  # tras una invariable, se corta
        "el Águila": "el Águila",              # a tónica: no cambia
    }
    for masc, fem in casos.items():
        assert feminizar(masc) == fem, masc
    assert feminizar("Dedo Negro") is None
    assert feminizar("el alcalde") is None


def test_la_tabla_de_titulos_sale_de_los_corpus_y_sus_excepciones_se_usan():
    """Cada excepción tiene que corresponder a un título que existe: si el
    corpus cambia y deja de usarla, sobra; y la tabla no recoge pares que no
    sean «the X» → «el X»."""
    from build_dist import corpus_del_pack
    from titulos import EXCEPCIONES, INVARIABLES, tabla

    pares = [(get_field(b, "en"), get_field(b, "es"))
             for c in corpus_del_pack() for b in load_blocks(c["ruta"])]
    t = tabla(pares)
    assert t["el Valiente"] == "la Valiente"
    assert t["el Penitente"] == "la Penitente"
    assert all(m.startswith("el ") and f.startswith("la ") for m, f in t.items())
    palabras = {p for m in t for p in m.split(" ")}
    assert set(EXCEPCIONES) - palabras == set()
    assert INVARIABLES <= {es for _, es in pares}
    assert not INVARIABLES & set(t)
    assert tabla([("Brave", "el Valiente"), ("the %x%", "el Valiente")]) == {}


def test_sonda_del_enganche_con_legends(tmp_path):
    """Corre sq_probe_legends.nut: los tokens castellanos salen con el género
    de cada personaje del código real de Legends, y los títulos solo pasan a
    femenino para las mujeres. Necesita la fuente de Legends (lotes.py extraer)
    y un intérprete Squirrel; sin ellos, se salta."""
    import os
    import subprocess

    import pytest

    from build_dist import REPO
    from check_syntax import localiza_interprete
    from titulos import emite, tabla

    sq = localiza_interprete()
    legends = REPO / "es_pack" / "legends" / "fuente"
    if sq is None:
        pytest.skip("sin interprete Squirrel disponible")
    if not (legends / "mod_legends" / "config" / "z_legends_language.nut").is_file():
        pytest.skip("sin la fuente de Legends (lotes.py extraer)")
    nut = tmp_path / "titulos_es.nut"
    nut.write_bytes(emite(tabla([("the Brave", "el Valiente"),
                                 ("the Old Wolf", "el Viejo Lobo")])).encode("utf-8"))
    env = dict(os.environ, ROSETTA_DIR=str(REPO), LEGENDS_DIR=str(legends), TITULOS_NUT=str(nut))
    r = subprocess.run([str(sq), str(REPO / "es_pack" / "tools" / "sq_probe_legends.nut")],
                       capture_output=True, env=env)
    salida = (r.stdout + r.stderr).decode("utf-8", errors="replace")
    assert "FALLOS: 0" in salida, salida


def _stdlib_descomprimido(destino):
    """stdlib para la sonda con el runtime real: STDLIB_DIR, o el stdlib.zip de la
    carpeta data del juego (DATA_DIR) descomprimido en un temporal."""
    import zipfile

    from measure_coverage import _valor_env

    v = _valor_env("STDLIB_DIR")
    if v and Path(v).is_dir():
        return Path(v)
    data = _valor_env("DATA_DIR")
    z = Path(data) / "stdlib.zip" if data else None
    if z is None or not z.is_file():
        return None
    with zipfile.ZipFile(z) as f:
        f.extractall(destino)
    return destino


def test_sonda_de_los_textos_que_monta_legends(tmp_path):
    """Corre sq_probe_legends_textos.nut con el runtime real de Rosetta, los pares
    que irían al zip y el código real de Legends: las descripciones de ventajas y
    de runas salen con su par (el enganche de ::Legends.tooltip), la línea de
    grupos sale en castellano y una sola vez, también al volver al menú
    principal, los mensajes compuestos de las tiendas casan, y las reglas que
    casaban con cualquier frase ya no lo hacen. Necesita la fuente de Legends,
    un intérprete Squirrel y stdlib; sin ellos, se salta."""
    import os
    import re
    import subprocess

    import pytest

    from build_dist import IDS, REPO, cabecera, corpus_del_pack, emit
    from check_syntax import localiza_interprete

    sq = localiza_interprete()
    legends = REPO / "es_pack" / "legends" / "fuente"
    if sq is None:
        pytest.skip("sin interprete Squirrel disponible")
    if not (legends / "mod_legends" / "afterHooks" / "perk_tooltips.nut").is_file():
        pytest.skip("sin la fuente de Legends (lotes.py extraer)")
    stdlib = _stdlib_descomprimido(tmp_path / "stdlib")
    if stdlib is None:
        pytest.skip("sin stdlib (STDLIB_DIR o DATA_DIR en .env)")
    packs = []
    for c in corpus_del_pack():
        p = tmp_path / c["ruta"].name
        emit(p, [b for b in load_blocks(c["ruta"]) if classify(b) == "dist"], cabecera(c["id"], c["version"]))
        packs.append(p)
    packs.insert(1, IDS)
    # como el preload: claves.nut va justo antes del corpus de Legends
    packs.insert(2, REPO / "es_pack" / "src" / "mod_battle_brothers_es" / "claves.nut")
    env = dict(os.environ, ROSETTA_DIR=str(REPO), STDLIB_DIR=str(stdlib), LEGENDS_DIR=str(legends),
               SONDA_PACKS=";".join(str(p) for p in packs))
    r = subprocess.run([str(sq), str(REPO / "es_pack" / "tools" / "sq_probe_legends_textos.nut")],
                       capture_output=True, env=env)
    salida = (r.stdout + r.stderr).decode("utf-8", errors="replace")
    assert "FALLOS: 0" in salida, salida[-6000:]
    for que in ("ventajas", "runas"):
        bien, total = map(int, re.search(que + r" en castellano: (\d+) / (\d+)", salida).groups())
        assert bien == total > 30, salida[-6000:]


def test_las_sumas_estaticas_de_legends_estan_enteras_en_el_corpus():
    """Las descripciones de las tiendas del campamento y dos intros de eventos se
    montan sumando literales; Rosetta ve la suma, así que el corpus tiene que
    tenerla entera. Si Legends cambia un trozo, la suma del corpus deja de casar
    y esto lo dice. Necesita la fuente de Legends; sin ella, se salta."""
    import ast
    import re

    import pytest

    from build_dist import REPO, is_rule_pair

    fuente = REPO / "es_pack" / "legends" / "fuente" / "scripts"
    if not fuente.is_dir():
        pytest.skip("sin la fuente de Legends (lotes.py extraer)")
    lit = r'"((?:[^"\\]|\\.)*)"'

    def cadena(s):
        return ast.literal_eval('"' + s.replace("\\'", "'") + '"')

    literales = {get_field(b, "en") for b in load_blocks(REPO / "es_pack" / "corpus" / "mod_legends_es.nut")
                 if not is_rule_pair(b)}
    sumas = {}
    for t in ["commander", "crafting", "enchanter", "fletcher", "gatherer", "healer", "rest", "scout", "training", "workshop"]:
        texto = (fuente / "entity/world/camp/buildings" / (t + "_building.nut")).read_text(encoding="utf-8")
        cuerpo = re.search(r"function getDescription\(\)\s*\{(.*?)return desc;", texto, re.S).group(1)
        sumas[t] = "".join(cadena(m.group(1)) for m in re.finditer(r"desc\s*(?:\+=|=\s*desc\s*\+)\s*" + lit, cuerpo))
    for rel, img, nombre, n in [("legend_escaped_slaves_intro_event.nut", "event_161", "introText", 5),
                                ("escaped_slaves/legend_slave_recovers_event.nut", "event_05", "EventText", 6)]:
        texto = (fuente / "events/events/legends/scenario" / rel).read_text(encoding="utf-8")
        v = {m.group(1): cadena(m.group(2)) for m in re.finditer(r"local (\w+) = " + lit + ";", texto)}
        sumas[rel] = "[img]gfx/ui/events/%s.png[/img]" % img + "".join(v[nombre + str(i)] for i in range(1, n + 1))
    assert [k for k, s in sumas.items() if s not in literales] == []


# Emulación mínima del índice de reglas del runtime (_ruleKey, _iterKeys y
# matchParts de !rosetta.nut) para el test de abajo.
_PARADAS = set("a the of in at to as is be are do has have having not and or"
               " it it's its this that he she his her him ah eh , .".split())
_ETIQUETAS_RE = re.compile(r"\[img[^\]]*\][^\[]+\[/img\w*\]|\[[^\]]+]|&\w+;|<[^>]+>")
_SUBS_RE = {"int": r"[+\-]?\d+", "val": r"[+\-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?",
            "word": r"[^ \t\n,.:;!\[\]()]+", "line": r"[^\n]*(?:\n|$)",
            "tag": r"\[[^\]]+\]", "img": r"\[img\][^\]]+\[/img\]"}


# patternKeyRe: la captura se lleva lo que tiene pegado, salvo < = >.
_CLAVE_RE = re.compile(r"([\w!-;?-~]*)<\w+:(\w+)>([\w!-;?-~]*)")


def _clave_de_regla(en, salta_trozos=False):
    """La clave del runtime; con salta_trozos, la de claves.nut (corpus de mods)."""
    sin = _CLAVE_RE.sub(lambda m: m.group(1) + " " + m.group(3) if m.group(2).endswith("tag") else "", en)
    for w in _ETIQUETAS_RE.sub(" ", sin).lower().split():
        if w not in _PARADAS and not w[0].isdigit() and not (salta_trozos and ("[" in w or "]" in w)):
            return w
    return ""


def test_ninguna_regla_de_mod_queda_bajo_una_clave_imposible():
    """Una regla cuya clave es un trozo de etiqueta ("[color=") no se prueba
    nunca. Las de los mods las rescata claves.nut, y esto comprueba que lo
    consigue. En el juego base queda una, el sobre del rumor de taberna, que
    claves.nut no toca porque el base se carga antes: pendiente de la 4.0.1."""
    from build_dist import corpus_del_pack, is_rule_pair

    imposibles = {"base": [], "mods": []}
    for c in corpus_del_pack():
        for b in load_blocks(c["ruta"]):
            if classify(b) != "dist" or not is_rule_pair(b):
                continue
            en = get_field(b, "en")
            k = _clave_de_regla(en, salta_trozos=c["id"] != "vanilla")
            if "[" in k or "]" in k:
                imposibles["base" if c["id"] == "vanilla" else "mods"].append(en)
    assert imposibles["mods"] == []
    assert [en[:11] for en in imposibles["base"]] == ["<intro:str>"]


def test_la_emulacion_de_la_clave_ve_el_trozo_de_etiqueta():
    assert _clave_de_regla("[color=%positive%]+<n:int>[/color] Melee Skill") == "[color="
    assert _clave_de_regla("[color=%positive%]+<n:int>[/color] Melee Skill", salta_trozos=True) == "melee"
    assert _clave_de_regla("You spend [color=<c:str>]<n:int>[/color] Tools") == "you"


def _regex_de_regla(en):
    partes, pos, capturas = [], 0, list(re.finditer(r"<(\w+):(\w+)>", en))
    for i, m in enumerate(capturas):
        partes.append(re.escape(en[pos:m.start()]))
        sub = m.group(2)
        if sub == "str":
            partes.append(".*" if i == len(capturas) - 1 and m.end() == len(en) else ".*?")
        elif sub.endswith("_tag"):
            partes.append(r"\[[^\]]+\]" + _SUBS_RE.get(sub[:-4], ".*?") + r"\[/[^\]]+\]")
        else:
            partes.append(_SUBS_RE[sub])
        pos = m.end()
    partes.append(re.escape(en[pos:]))
    return re.compile("".join(partes), re.S)


def test_ningun_par_sin_capturas_queda_tapado_por_una_regla_anterior():
    """Un par con mode="pattern" y sin capturas solo casa su cadena exacta,
    pero el runtime lo archiva con las reglas, bajo su primera palabra y en
    orden de carga. Si una regla anterior con la misma clave casa también esa
    cadena, gana ella. Así salían dos rumores de taberna a medias: "From
    <f:str>" (el remitente de una carta) se comía "From what I've heard,
    %settlement% is flooded..." y el jugador leía "Desde what I've heard...".
    Un par literal no tiene el problema, porque el runtime mira los literales
    antes que las reglas.

    shortcut: la emulación solo compara reglas de la misma clave, que es
    donde cae una regla con el mismo arranque literal; una regla cuya clave
    sea otra palabra de la cadena se probaría después y no tapa nada. Y no
    cuenta las reglas con alguna captura <x:t> en el es: el runtime las
    abandona si lo capturado no tiene traducción, que es lo que pasa con un
    trozo de frase ("Some <troops:str>" frente a "Some witch hunters...").
    """
    from build_dist import CORPUS, is_rule_pair

    reglas = [(get_field(b, "en"), get_field(b, "es"), b) for b in load_blocks(CORPUS)
              if classify(b) == "dist" and is_rule_pair(b)]
    vistas = {}
    tapados = []
    for en, es, bloque in reglas:
        clave = _clave_de_regla(en)
        if not re.search(r"<\w+:\w+>", en) and not re.search(r"^\s*(?:plural|split|use)\s*=", bloque, re.M):
            for anterior in vistas.get(clave, []):
                if _regex_de_regla(anterior).fullmatch(en):
                    tapados.append("%r tapa %r" % (anterior[:40], en[:60]))
                    break
        if not re.search(r"<\w+:t>", es):
            vistas.setdefault(clave, []).append(en)
    assert tapados == []


def test_la_emulacion_del_indice_ve_el_rumor_tapado():
    assert _clave_de_regla("From <f:str>") == _clave_de_regla("From what I hear they found a witch") == "from"
    assert _regex_de_regla("From <f:str>").fullmatch("From what I hear, %settlement% burns.")
    assert not _regex_de_regla("Afraid of <m:str>").fullmatch("Not afraid of anything")
    assert _regex_de_regla("Got <n:int> crowns").fullmatch("Got 12 crowns")
    assert not _regex_de_regla("Got <n:int> crowns").fullmatch("Got many crowns")


def test_ancho_mide_con_la_fuente_del_juego():
    """La línea inglesa más ancha de los botones de ambición (discover unique
    locations) mide 71.6 rem con la fuente real; el token cuenta igual en los
    dos idiomas."""
    from checks import BOTON_FUENTE, ancho_rem
    linea = "The wilds are teeming with hidden treasures that others are not bold enough to claim."
    assert 71.0 < ancho_rem(linea, BOTON_FUENTE) < 72.0
    assert ancho_rem("[color=#bcad8c]Hola[/color] %name%", 1.0) == ancho_rem("Hola Hans", 1.0)
    # la línea que en partida quedaba pegada al icono ya no cabe en el presupuesto
    from checks import BOTON_REM
    pegada = "No estaremos a la altura del Joven Anselm si nos obsesionan los asuntos mundanos."
    assert ancho_rem(pegada, BOTON_FUENTE) > BOTON_REM


def test_ancho_avisa_del_boton_sin_salto_y_de_la_descripcion_larga(tmp_path):
    """El caso del jugador: el juramento había perdido el \\n del inglés y el
    botón, que no parte línea, se cortaba por los dos lados."""
    from checks import ancho_recuadros
    en_boton = "Evil-doers skulk and hide away from the walls of the just.\\nLet us take an Oath of Fortification and bring those walls to them!"
    largo = ("Los malhechores se ocultan y se esconden lejos de las murallas de los justos. "
             "¡Tomemos un Juramento de Fortificación y llevemos esas murallas hasta ellos!")
    corto = ("Los malhechores acechan y se esconden lejos de las murallas de los justos.\\n"
             "¡Tomemos un Juramento de Fortificación y llevemos esas murallas hasta ellos!")
    en_origen = "[p=c][img]gfx/ui/events/event_1.png[/img][/p][p]Short.[/p]"
    origen_largo = "[p=c][img]gfx/ui/events/event_1.png[/img][/p][p]" + "Uno.\\n" * 14 + "[/p]"
    ruta = _corpus_falso(tmp_path, [
        ("oath_of_fortification_ambition.nut", [(en_boton, largo)]),
        ("oath_of_honor_ambition.nut", [(en_boton.replace("Fortification", "Honor"), corto),
                                        ("<ret:str>\\n- Beer", "<ret>\\n- " + "Cerveza " * 20)]),
        ("lone_wolf_scenario.nut", [(en_origen, origen_largo)]),
        ("militia_scenario.nut", [(en_origen, "[p=c][img]gfx/ui/events/event_1.png[/img][/p][p]Corto.[/p]")]),
    ])
    avisos = ancho_recuadros(ruta)
    assert len(avisos) == 2
    assert "oath_of_fortification" in avisos[0] and "lone_wolf" in avisos[1]


def test_ancho_no_avisa_de_nada_en_el_corpus():
    from checks import ancho_recuadros
    assert ancho_recuadros() == []


def test_literalizar_solo_quita_el_modo_a_los_pares_sin_capturas():
    from build_dist import is_rule_pair, literalizar
    sin = '{\n        mode = "pattern"\n        en = "From what I hear, %settlement% burns."\n        es = "Dicen que %settlement% arde."\n    }'
    con = '{\n        mode = "pattern"\n        en = "From <f:str>"\n        es = "De <f>"\n    }'
    plural = '{\n        mode = "pattern"\n        plural = "n"\n        en = "Got <n:int> crowns"\n        n1 = "a"\n        n2 = "b"\n    }'
    literal = '{\n        en = "Your Task"\n        es = "Tu tarea"\n    }'
    assert not is_rule_pair(literalizar(sin))
    assert get_field(literalizar(sin), "en") == get_field(sin, "en")
    assert get_field(literalizar(sin), "es") == get_field(sin, "es")
    assert literalizar(con) == con and literalizar(plural) == plural and literalizar(literal) == literal


def test_literalizar_no_cambia_el_cubo_de_ningun_par_del_corpus():
    """Lo emitido cambia de forma, pero no de cubo: el recuento dist/wip/drop
    por par es el mismo que el del corpus fuente."""
    from build_dist import CORPUS, is_rule_pair, literalizar
    bloques = load_blocks(CORPUS)
    assert [classify(literalizar(b)) for b in bloques] == [classify(b) for b in bloques]
    cambiados = [b for b in bloques if literalizar(b) != b]
    assert cambiados and all(classify(b) == "dist" and is_rule_pair(b) for b in cambiados)


def test_registro_ve_el_imperativo_de_vosotros_con_clitico():
    """«Decidles», «Degolladlos» y «Dadle» se le escapaban: la palabra no acaba
    en -d. La raíz se valida con el infinitivo o el participio del corpus."""
    from checks import revisar
    diccionario = [("x", "Hay que decir algo."), ("x", "Lo han degollado."), ("x", "Ya está dado."),
                   ("x", "No te vayas a preocupar.")]
    vos = [("x", "¡Decidles a todos!"), ("x", "Degolladlos. Que sea rápido."), ("x", "Dadle agua."),
           ("x", "¡Barrédlos desde el flanco!")]
    limpios = [("x", "¡Díganles a todos!"), ("x", "Las ciudadelas caen."), ("x", "Está preocupad%o%."),
               ("x", "Rocks in the cradles"), ("x", "Denle agua.")]
    avisos = revisar(diccionario + [("x", "Hay que barrer.")] + vos + limpios)["REGISTRO"]
    assert len(avisos) == 4
    assert all(any(v[1][:10] in a for a in avisos) for v in vos)


def test_etiquetas_ve_el_color_suelto_de_las_llaves_perdidas():
    """El caso del jugador (contrato de buscar un lugar): el inglés anida un
    bloque de ramas dentro de un %SPEECH_ON%...%SPEECH_OFF% y el español
    perdió esas llaves, de modo que una rama abría el [color] y otra lo
    cerraba sin abrirlo."""
    from checks import etiquetas_rotas, revisar
    en = "{A.%SPEECH_ON%B.%SPEECH_OFF% | C.%SPEECH_ON%{D | E}%SPEECH_OFF%}"
    roto = "{A.%SPEECH_ON%B.%SPEECH_OFF% | C.%SPEECH_ON%D | E%SPEECH_OFF%}"
    assert etiquetas_rotas(en) == set()
    assert etiquetas_rotas(roto) == {"color"}
    # el intro de la negociación abre en sus ramas y cierra en el pago: cuadra
    assert etiquetas_rotas("{a%SPEECH_ON%x | %SPEECH_ON%y} {b | c} pago.%SPEECH_OFF%") == set()
    assert etiquetas_rotas("llave { suelta %SPEECH_START%hola%SPEECH_OFF%") == set()
    avisos = revisar([(en, roto), (en, en.replace("B", "Be"))])["ETIQUETAS"]
    assert len(avisos) == 1 and "C.%SPEECH_ON%D" in avisos[0]


def test_etiquetas_ve_el_orden_las_otras_etiquetas_y_las_llaves():
    from checks import etiquetas_rotas, revisar
    # cierra antes de abrir: el saldo cuadra, el orden no
    assert etiquetas_rotas("[/color]a[color=#fff]") == {"color"}
    assert etiquetas_rotas("{[b]a | b}[/b]") == {"b"}
    assert etiquetas_rotas("[i]{a | b}[/i] [u]c[/u]") == set()
    datos = [("[b]A[/b]", "[b]A"),                    # negrita sin cerrar
             ("{A | B}", "{A | B"),                    # llave sin cerrar
             ("[color=x]A", "[color=x]A"),             # el inglés ya viene así
             ("[u]A[/u] {B | C}", "[u]A[/u] {B | C}")]
    avisos = revisar(datos)["ETIQUETAS"]
    assert len(avisos) == 2 and "llaves" in avisos[1]


def test_ancho_ve_el_origen_que_en_partida_se_salia(tmp_path):
    """Los Desertores de la primera 1.0.1 se salían una palabra por abajo en
    partida: con el presupuesto calibrado ocupan 14 renglones y avisa; con la
    versión recortada, no."""
    from checks import ORIGEN_FUENTE, ORIGEN_REM, ORIGEN_RENGLONES, renglones
    img = "[p=c][img]gfx/ui/events/event_88.png[/img][/p][p]"
    c, f = "[color=#bcad8c]", "[/color]"
    antes = (img + "Por demasiado tiempo te han arrastrado de una sangrienta batalla a otra, a merced de señores que se sientan en altas torres. Anoche, te escapaste del campamento junto con otros tres. Todavía están vestidos como soldados, pero son desertores, y la soga será su fin si se quedan aquí por demasiado tiempo.\n\n"
             + c + "Desertores:" + f + " Comienzas con tres desertores y una armadura decente, pero menos fondos y una casa noble que quiere darte caza.\n"
             + c + "Primeros en huir:" + f + " Tus hombres siempre son los primeros en actuar en la primera ronda del combate.[/p]")
    despues = (img + "Demasiado tiempo te han arrastrado de una batalla sangrienta a otra al capricho de señores encerrados en altas torres. Anoche huiste del campamento con otros tres. Aún visten como soldados, pero son desertores, y la soga será su fin si se quedan aquí mucho tiempo.\n\n"
               + c + "Desertores:" + f + " Comienzas con tres desertores y una armadura decente, pero menos fondos y una casa noble que quiere darte caza.\n"
               + c + "Primeros en huir:" + f + " Tus hombres siempre actúan primero en la primera ronda del combate.[/p]")
    assert renglones(antes, ORIGEN_REM, ORIGEN_FUENTE) > ORIGEN_RENGLONES
    assert renglones(despues, ORIGEN_REM, ORIGEN_FUENTE) <= ORIGEN_RENGLONES


def test_el_final_de_partida_solo_recorta_la_cola_de_cada_trozo():
    """El hook del caso 39 parte el texto del final de partida y construye cada
    trozo crudo aparte. Los párrafos de cierre empiezan por "\\n\\n{...}" y así
    los tiene el corpus; si el hook les quita también el borde inicial, el
    último párrafo del retiro sale en inglés. Se ejecuta la función real del
    hook con el intérprete, y se comprueba que el corpus guarda ese borde."""
    import subprocess
    import pytest
    from build_dist import CORPUS, SRC
    from check_syntax import localiza_interprete

    hooks = (SRC / "scripts" / "!mods_preload" / "mod_battle_brothers_es_hooks.nut").read_text(encoding="utf-8")
    recorta = re.search(r"local recorta = function \(_s\) \{.*?\n    \};", hooks, re.S).group(0)
    cierres = [get_field(b, "en") for b in load_blocks(CORPUS)
               if (get_field(b, "en") or "").startswith("\n\n{You haven't gotten word from the others")]
    assert cierres, "el corpus perdió el borde inicial del párrafo de cierre del retiro"

    sq = localiza_interprete()
    if sq is None:
        pytest.skip("sin intérprete Squirrel disponible")
    prueba = Path(__file__).resolve().parents[2] / "es_pack" / "build" / "prueba_recorta.nut"
    prueba.parent.mkdir(parents=True, exist_ok=True)
    prueba.write_text(recorta + '\nforeach (s in ["\\n\\n{A}\\n\\n", "{A}\\n\\n", "\\n\\n", "{A}"]) {\n'
                      '    local p = recorta(s);\n    print(p[0].len() + "," + p[1].len() + ";");\n}\n',
                      encoding="utf-8")
    salida = subprocess.run([str(sq), str(prueba)], capture_output=True, text=True).stdout
    assert salida == "5,2;3,2;0,2;3,0;"


def test_las_reglas_golosas_se_emiten_detras_de_las_concretas():
    """"<ailing:str> gains <trait:str>", sin :t, casa con cualquier "X gains Y"
    y se adelantaba a "<bro:str> gains Deathwish" y compañía. Se reconoce como
    golosa y el build la emite al final; las que llevan :t no se mueven."""
    from build_dist import CORPUS, es_golosa
    regla = '{\n        mode = "pattern"\n        en = "%s"\n        es = "%s"\n    }'
    golosa = regla % ("<ailing:str> gains <trait:str>", "<ailing> ahora es <trait>")
    concreta = regla % ("<bro:str> gains Deathwish", "<bro> gana Temerario")
    con_t = regla % ("<actor:str> has <name:str>", "<actor> goza de <name:t>")
    assert es_golosa(golosa) and not es_golosa(concreta) and not es_golosa(con_t)
    assert sorted([golosa, concreta, con_t], key=es_golosa) == [concreta, con_t, golosa]
    ens = [get_field(b, "en") for b in load_blocks(CORPUS) if es_golosa(b)]
    assert "<who:str> joins the <company:str>" in ens
    # la de "gains" ya no existe: hay una regla por cada rasgo que dan los eventos
    todos = [get_field(b, "en") for b in load_blocks(CORPUS)]
    assert "<ailing:str> gains <trait:str>" not in todos
    assert "<ailing:str> gains Temerario" in todos


def test_ninguna_traduccion_dispara_la_recursion_de_las_reglas_con_t(tmp_path):
    """Las reglas golosas con :t ("<actor:str> has <name:str>", "had", "'s"...)
    traducen la cola para decidir si valen, y la cola vuelve a casar con ellas:
    sin memoria, las llamadas crecen de forma exponencial con los separadores
    (un evento largo de Legends colgaba translate() más de 14 minutos, y una
    frase de 86 caracteres con doce has/had tardaba 15 s). Corre
    sq_probe_cuelgue.nut con el runtime real, los pares que irían al zip y
    la memoria de translate() del preload, con un tope de llamadas por texto: sin
    la memoria falla en segundos en vez de colgarse. Sin intérprete Squirrel o
    sin stdlib, se salta."""
    import os
    import subprocess

    import pytest

    from build_dist import CORPUS, IDS, REPO, SRC, emit, es_golosa, literalizar
    from check_syntax import localiza_interprete

    sq = localiza_interprete()
    if sq is None:
        pytest.skip("sin interprete Squirrel disponible")
    stdlib = _stdlib_descomprimido(tmp_path / "stdlib")
    if stdlib is None:
        pytest.skip("sin stdlib (STDLIB_DIR o DATA_DIR en .env)")
    base = tmp_path / "base_es.nut"
    dist = sorted((b for b in load_blocks(CORPUS) if classify(b) == "dist"), key=es_golosa)
    emit(base, [literalizar(b) for b in dist])
    preload = (SRC / "scripts" / "!mods_preload" / "mod_battle_brothers_es.nut").read_text(encoding="utf-8")
    bloque = re.search(r"\n// Memoria de translate\(\).*?\n\}\)\(::Rosetta\);\n", preload, re.S)
    assert bloque, "el preload perdió la memoria de translate()"
    memo = tmp_path / "memo.nut"
    memo.write_bytes(bloque.group(0).encode("utf-8"))
    env = dict(os.environ, ROSETTA_DIR=str(REPO), STDLIB_DIR=str(stdlib),
               SONDA_PACKS=";".join(str(p) for p in (base, IDS)), SONDA_MEMO=str(memo),
               SONDA_TOPE="1000")
    r = subprocess.run([str(sq), str(REPO / "es_pack" / "tools" / "sq_probe_cuelgue.nut")],
                       capture_output=True, env=env, timeout=300)
    salida = (r.stdout + r.stderr).decode("utf-8", errors="replace")
    assert "FALLOS: 0" in salida, salida[-6000:]
