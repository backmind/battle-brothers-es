import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lotes
from lotes import bloques, cribar, duplicados

FIXTURE = '''if (!("Rosetta" in getroottable())) return;

local rosetta = {
    mod = {id = "mod_", version = "..."}
    author = "..."
    lang = "es"
}
local pairs = [
    // FILE: scripts\\items\\a.nut
    // context: a.create.m.Name
    {
        // this.m.Name = "Hand Axe";
        en = "Hand Axe"
        es = ""
    }
    {
        en = "A crude axe"
        es = ""
    }
    // FILE: scripts\\skills\\b.nut
    {
        en = "Already done"
        es = "Ya hecho"
    }
    {
        mode = "pattern"
        en = "Has a range of <range:int> tiles"
        es = ""
    }
]
::Rosetta.add(rosetta, pairs);
'''


def test_bloques_asigna_file_y_lineas():
    b = bloques(FIXTURE)
    assert len(b) == 4
    assert b[0].file == "scripts\\items\\a.nut"
    assert b[2].file == "scripts\\skills\\b.nut"
    assert b[0].en == "Hand Axe" and b[2].es == "Ya hecho"
    assert b[0].contexto == "a.create.m.Name" and b[1].contexto is None
    for x in b:
        assert x.texto.startswith("    {") and x.texto.endswith("    }")


def test_cribar_sustituye_y_cuenta():
    texto, n = cribar(FIXTURE, {"A crude axe"})
    assert n == 1
    assert '    // en = "A crude axe"\n    // en base_es\n' in texto
    assert len(bloques(texto)) == 3


def test_cribar_identificadores_de_pantalla():
    pantallas = FIXTURE.replace('b.nut\n', 'b.nut\n    // context: e.create.m.Screens.hook()\n')
    pantallas = pantallas.replace('en = "Already done"', 'en = "Success5"')
    texto, n = cribar(pantallas, set())
    assert n == 1
    assert '    // en = "Success5"\n    // identificador de pantalla\n' in texto
    assert len(bloques(texto)) == 3


def test_cribar_sin_coincidencias_es_identidad():
    assert cribar(FIXTURE, set()) == (FIXTURE, 0)


def test_extraer_se_niega_con_traducciones(tmp_path, monkeypatch):
    corpus = tmp_path / "mod_legends_es.nut"
    corpus.write_bytes(FIXTURE.encode("utf-8"))
    monkeypatch.setattr(lotes, "CORPUS_LEGENDS", corpus)
    with pytest.raises(SystemExit):
        lotes.extraer(forzar=False)
    assert corpus.read_bytes() == FIXTURE.encode("utf-8")


def test_desverbatim_convierte_y_respeta_lo_demas():
    codigo = ('a <- @"\nHold ""your"" ground!\n\tC:\\x\n";\n'
              'b <- "no @\\"toca\\"";  // ni @"esto"\n'
              "/* ni @\"esto\" */ c <- '@';\n")
    esperado = ('a <- "\\nHold \\"your\\" ground!\\n\\tC:\\\\x\\n";\n'
                'b <- "no @\\"toca\\"";  // ni @"esto"\n'
                "/* ni @\"esto\" */ c <- '@';\n")
    assert lotes.desverbatim(codigo) == esperado
    assert lotes.desverbatim('x <- @"a\r\nb";') == 'x <- "a\\nb";'


def test_duplicados():
    doble = FIXTURE.replace('en = "A crude axe"', 'en = "Hand Axe"')
    assert duplicados(doble) == ["Hand Axe"]
    assert duplicados(FIXTURE) == []


def _b(en, file=r"scripts\x.nut", contexto=None, extra=""):
    texto = '    {\n%s        en = "%s"\n        es = ""\n    }' % (extra, en)
    return lotes.Bloque(file, 0, 3, texto, en, "", contexto)


def test_es_termino():
    assert lotes.es_termino(_b("Hand Axe"))
    assert not lotes.es_termino(_b("Deals %damage% damage"))
    assert not lotes.es_termino(_b("a sword"))
    assert not lotes.es_termino(_b("One Two Three Four Five"))
    assert not lotes.es_termino(_b("Line\nBreak"))
    assert not lotes.es_termino(_b("Hit <x:int>", extra='        mode = "pattern"\n'))


def test_grupo_por_contexto():
    assert lotes.grupo(_b("Ottmar", contexto="::Const.Strings.CharacterNames")) == "lista"
    assert lotes.grupo(_b("Zig", contexto="::Const.Strings.GoblinNames.extend()")) == "lista"
    assert lotes.grupo(_b("Alchemist", contexto="legend_alchemist_background.create.m.Name")) == "termino"
    assert lotes.grupo(_b("Anchor", contexto="::Const.Strings.PerkName.LegendAnchor")) == "termino"
    assert lotes.grupo(_b("Seance", contexto="activesDefs.push().Name")) == "termino"
    assert lotes.grupo(_b("Join us!", contexto="x.create.m.Screens.push().Options.Text")) == "resto"
    assert lotes.grupo(_b("Cat")) == "resto"


def test_categoria():
    assert lotes.categoria(r"scripts\skills\perks\perk_x.nut") == "perk"
    assert lotes.categoria(r"mod_legends\!!config\perk_strings.nut") == "perk"
    assert lotes.categoria(r"scripts\skills\actives\x.nut") == "habilidad"
    assert lotes.categoria(r"scripts\items\armor\x.nut") == "objeto"
    assert lotes.categoria(r"scripts\events\x.nut") == "general"
    assert lotes.categoria(r"mod_legends\!!config\actives_defs.nut", "activesDefs.push().Name") == "habilidad"
    assert lotes.categoria(r"mod_legends\!!config\x.nut", "::Const.Strings.LegendArmorLayers") == "objeto"


def test_terminos_en_mas_largo_primero_y_con_mayusculas():
    axe = lotes.Termino("Axe", "Hacha", "objeto", "f")
    hand = lotes.Termino("Hand Axe", "Hacha de mano", "objeto", "f")
    assert lotes.terminos_en("Wields a Hand Axe and an Axe.", [axe, hand]) == [hand, axe]
    assert lotes.terminos_en("Wields a Hand Axe.", [axe, hand]) == [hand]
    assert lotes.terminos_en("Axes and an axe", [axe, hand]) == []


def test_termino_util_del_base():
    textos = ["You gain 10 Fatigue and lose Resolve.", "Costs Fatigue to use.",
              "The man smiles. The end.", "Some say so. Some do not.",
              "Kill of The Pious, of The Mad, and the dog, the cat, the end.",
              "the man, the dog, the cat, the end, the hill, the sword, the axe."]
    usos = lotes.usos_a_mitad_de_frase(textos)
    t = lambda en, es, cat="general": lotes.Termino(en, es, cat, "f")
    assert lotes.termino_util(t("Fatigue", "Fatiga"), usos)
    assert not lotes.termino_util(t("The", "El"), usos)
    assert not lotes.termino_util(t("Some", "Algunos"), usos)
    assert not lotes.termino_util(t("Armor", "Armadura de trol", "objeto"), usos)
    assert not lotes.termino_util(t("Ancient", "ancestral", "objeto"), usos)
    assert lotes.termino_util(t("Hand Axe", "Hacha de mano", "objeto"), usos)


def _bloques_de(ficheros):
    """[(file, n, palabras)] -> bloques pendientes con `palabras` palabras cada uno."""
    res = []
    for file, n, palabras in ficheros:
        for i in range(n):
            res.append(_b(" ".join(["w"] * (palabras - 1) + [str(i)]), file=file))
    return res


def test_partir_respeta_file_y_limites():
    bs = _bloques_de([("a.nut", 100, 1), ("b.nut", 100, 1), ("c.nut", 400, 1)])
    lotes_ = lotes.partir_en_lotes(bs, max_entradas=150)
    assert [len(l) for l in lotes_] == [100, 100, 150, 150, 100]
    assert all(len({b.file for b in l}) == 1 for l in lotes_)


def test_partir_junta_ficheros_que_caben():
    bs = _bloques_de([("a.nut", 50, 1), ("b.nut", 60, 1), ("c.nut", 60, 1)])
    assert [len(l) for l in lotes.partir_en_lotes(bs, max_entradas=150)] == [110, 60]


def test_partir_corta_por_palabras():
    bs = _bloques_de([("a.nut", 10, 1000)])
    assert [len(l) for l in lotes.partir_en_lotes(bs, max_palabras=6000)] == [6, 4]


def test_pista_base():
    indice = lotes.indice_base([("You find an old sword in the mud.", "Encuentras una vieja espada en el barro.")])
    assert lotes.pista_base("You find an old sword in the snow.", indice) == (
        "You find an old sword in the mud.", "Encuentras una vieja espada en el barro.")
    assert lotes.pista_base("Something else entirely here.", indice) is None
    assert lotes.pista_base("You find it.", indice) is None


def test_render_lote_contiene_bloques_tal_cual():
    bs = [b for b in bloques(FIXTURE) if not b.es]
    glosario = [lotes.Termino("Hand Axe", "Hacha de mano", "objeto", "f"),
                lotes.Termino("Anchor", "", "perk", "f")]
    texto = lotes.render_lote(7, "19.4.22", bs, glosario, {})
    assert [b.texto for b in bloques(texto)] == [b.texto for b in bs]
    assert texto.startswith("// LOTE 0007")
    assert "// Hand Axe = Hacha de mano" in texto
    assert "Anchor" not in texto
    assert "// context: a.create.m.Name" in texto
    assert texto.count("// FILE:") == 2


CORPUS_T = '''if (!("Rosetta" in getroottable())) return;

local rosetta = {
    mod = {id = "mod_legends", version = "19.4.22"}
    author = "..."
    lang = "es"
}
local pairs = [
    // FILE: scripts\\items\\a.nut
    // context: a.create.m.Name
    {
        en = "Hand Axe"
        es = ""
    }
    // context: a.create.m.Description
    {
        en = "%name% swings {a Hand Axe | an axe} at %their% foe."
        es = ""
    }
    {
        // text = this.m.Name + " attacks";
        en = "<this.m.Name> attacks"
        es = ""
    }
    {
        en = "Nest1"
        es = ""
    }
    {
        en = "Done before"
        es = "Hecho antes"
    }
]
::Rosetta.add(rosetta, pairs);
'''


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    corpus = tmp_path / "mod_legends_es.nut"
    corpus.write_bytes(CORPUS_T.encode("utf-8"))
    gb = tmp_path / "gb.tsv"
    lotes.escribir_glosario(gb, [lotes.Termino("Hand Axe", "Hacha de mano", "objeto", "f")])
    gl = tmp_path / "gl.tsv"
    lotes.escribir_glosario(gl, [])
    monkeypatch.setattr(lotes, "CORPUS_LEGENDS", corpus)
    monkeypatch.setattr(lotes, "LOTES", tmp_path / "lotes")
    monkeypatch.setattr(lotes, "GLOSARIO_BASE", gb)
    monkeypatch.setattr(lotes, "GLOSARIO_LEGENDS", gl)
    monkeypatch.setattr(lotes, "ens_base", lambda: {"Already in base"})
    pendientes = [b for b in bloques(CORPUS_T) if not b.es]
    texto = lotes.render_lote(1, "19.4.22", pendientes, [], {})
    (tmp_path / "lotes").mkdir()
    for nombre in ("0001.nut", "0001.orig.nut"):
        (tmp_path / "lotes" / nombre).write_bytes(texto.encode("utf-8"))

    def editar(*cambios, crlf=False):
        t = texto
        for viejo, nuevo in cambios:
            assert t.count(viejo) == 1, viejo
            t = t.replace(viejo, nuevo)
        if crlf:
            t = t.replace("\n", "\r\n")
        (tmp_path / "lotes" / "0001.nut").write_bytes(t.encode("utf-8"))
    return corpus, editar


ES_AXE = ('en = "Hand Axe"\n        es = ""', 'en = "Hand Axe"\n        es = "Hacha de mano"')
EN_SWING = 'en = "%name% swings {a Hand Axe | an axe} at %their% foe."\n        es = ""'


def _swing(es):
    return (EN_SWING, EN_SWING.replace('es = ""', 'es = "%s"' % es))


def test_ida_y_vuelta_sin_cambios(entorno):
    corpus, editar = entorno
    editar()
    assert lotes.fusionar(1) == 0
    assert corpus.read_bytes() == CORPUS_T.encode("utf-8")


def test_fusion_valida(entorno):
    corpus, editar = entorno
    editar(ES_AXE,
           _swing("%name% lanza un tajo a su enemigo con {un hacha de mano | un hacha}."),
           ('        // text = this.m.Name + " attacks";\n        en = "<this.m.Name> attacks"\n        es = ""',
            '        // text = this.m.Name + " attacks";\n        mode = "pattern"\n        en = "<name:str> attacks"\n        es = "<name> ataca"'),
           ('    {\n        en = "Nest1"\n        es = ""\n    }', '    // en = "Nest1"  // interno: id de pantalla'))
    assert lotes.fusionar(1) == 0
    t = corpus.read_text(encoding="utf-8")
    assert 'es = "Hacha de mano"' in t
    assert 'es = "<name> ataca"' in t and 'en = "<name:str> attacks"' in t
    assert '    // en = "Nest1"  // interno: id de pantalla' in t
    assert 'es = "Hecho antes"' in t


def _rechaza(entorno, *cambios):
    corpus, editar = entorno
    editar(*cambios)
    assert lotes.fusionar(1) == 1
    assert corpus.read_bytes() == CORPUS_T.encode("utf-8")


def test_rechaza_entrada_quitada(entorno):
    _rechaza(entorno, ('    {\n        en = "Nest1"\n        es = ""\n    }\n', ""))


def test_rechaza_en_tocado(entorno):
    _rechaza(entorno, ('en = "Hand Axe"\n        es = ""', 'en = "Hand axe"\n        es = "Hacha"'))


def test_rechaza_dos_str_seguidos(entorno):
    _rechaza(entorno, ('        en = "<this.m.Name> attacks"\n        es = ""',
                       '        mode = "pattern"\n        en = "<a:str><b:str> attacks"\n        es = "<a><b> ataca"'))


def test_rechaza_captura_inventada(entorno):
    _rechaza(entorno, ('        en = "<this.m.Name> attacks"\n        es = ""',
                       '        mode = "pattern"\n        en = "<name:str> attacks"\n        es = "<otro> ataca"'))


def test_rechaza_token_perdido(entorno):
    _rechaza(entorno, _swing("Lanza un tajo a su enemigo con {un hacha de mano | un hacha}."))


def test_acepta_quitar_pronombre_ingles(entorno):
    corpus, editar = entorno
    editar(_swing("%name% lanza un tajo a su enemigo con {un hacha de mano | un hacha}."))
    assert lotes.fusionar(1) == 0


def test_rechaza_token_inventado(entorno):
    _rechaza(entorno, _swing("%name% lanza un tajo a %su% enemigo con {un hacha de mano | un hacha}."))


def test_rechaza_variantes_rotas(entorno):
    _rechaza(entorno, _swing("%name% lanza un tajo a su enemigo con {un hacha de mano}."))


def test_rechaza_barra_sin_espacios(entorno):
    _rechaza(entorno, _swing("%name% lanza un tajo a su enemigo con {un hacha de mano|un hacha}."))


def test_rechaza_en_del_base(entorno):
    _rechaza(entorno, ('        en = "<this.m.Name> attacks"\n        es = ""',
                       '        mode = "pattern"\n        en = "Already in base"\n        es = "Ya"'))


def test_rechaza_comillas_sin_escapar(entorno):
    _rechaza(entorno, _swing('%name% ataca con {un hacha de mano | un hacha} y grita "ya".'))


def test_rechaza_basura_tras_es(entorno):
    _rechaza(entorno, (EN_SWING, EN_SWING.replace('es = ""', 'es = "%name% {a | b}" + foo(')))


def test_rechaza_es_en_comentario(entorno):
    _rechaza(entorno, (EN_SWING, EN_SWING.replace(
        '        es = ""', '        // DUDA: es = "%name% ataca {un hacha de mano | un hacha}"\n        es = "Roto"')))


def test_rechaza_es_duplicado(entorno):
    _rechaza(entorno, (EN_SWING, EN_SWING + '\n        es = "Otro"'))


def test_rechaza_clave_no_permitida(entorno):
    _rechaza(entorno, ('        en = "<this.m.Name> attacks"\n        es = ""',
                       '        mode = "pattern"\n        plural = "n"\n        en = "<name:str> attacks"\n        es = "<name> ataca"'))


def test_rechaza_patron_que_cambia_el_texto(entorno):
    _rechaza(entorno, ('        en = "<this.m.Name> attacks"\n        es = ""',
                       '        mode = "pattern"\n        en = "<a:str> <b:str>"\n        es = "<b> <a>"'))


def test_rechaza_segunda_fusion(entorno):
    corpus, editar = entorno
    editar(ES_AXE)
    assert lotes.fusionar(1) == 0
    despues = corpus.read_bytes()
    assert lotes.fusionar(1) == 1
    assert corpus.read_bytes() == despues


def test_acepta_crlf(entorno):
    corpus, editar = entorno
    editar(ES_AXE, crlf=True)
    assert lotes.fusionar(1) == 0
    assert b"\r" not in corpus.read_bytes()


def test_aviso_glosario_no_rechaza(entorno, capsys):
    corpus, editar = entorno
    editar(_swing("%name% lanza un tajo a su enemigo con {unas hachas de mano | un hacha}."))
    assert lotes.fusionar(1) == 0
    assert "GLOSARIO" not in capsys.readouterr().out
    corpus.write_bytes(CORPUS_T.encode("utf-8"))
    editar(_swing("%name% lanza un tajo a su enemigo con {una segur | un hacha}."))
    assert lotes.fusionar(1) == 0
    assert "GLOSARIO" in capsys.readouterr().out


def test_dudas_lista(entorno, capsys):
    corpus, editar = entorno
    editar(('    {\n        en = "Nest1"', '    {\n        // DUDA: ¿se muestra?\n        en = "Nest1"'))
    lotes.dudas()
    salida = capsys.readouterr().out
    assert "0001" in salida and "Nest1" in salida and "¿se muestra?" in salida


def test_aplicar_glosario(entorno):
    corpus, _ = entorno
    lotes.escribir_glosario(lotes.GLOSARIO_LEGENDS, [lotes.Termino("Hand Axe", "Hacha de mano", "objeto", "f"),
                                                    lotes.Termino("Nest1", "", "general", "f")])
    assert lotes.aplicar_glosario() == 1
    t = corpus.read_text(encoding="utf-8")
    assert 'en = "Hand Axe"\n        es = "Hacha de mano"' in t
    assert 'en = "Nest1"\n        es = ""' in t


def test_checks_acepta_ruta(tmp_path, capsys):
    import checks
    f = tmp_path / "c.nut"
    f.write_bytes(CORPUS_T.encode("utf-8"))
    assert checks.main([str(f)]) == 0
    assert "revisados: 1" in capsys.readouterr().out


def test_glosario_ida_y_vuelta(tmp_path):
    ts = [lotes.Termino("Hand Axe", "Hacha de mano", "objeto", "a.nut", ""),
          lotes.Termino("Anchor", "", "perk", "b.nut", "contiene: Axe")]
    p = tmp_path / "g.tsv"
    lotes.escribir_glosario(p, ts)
    assert b"\r" not in p.read_bytes()
    assert sorted(lotes.leer_glosario(p), key=lambda t: t.en) == sorted(ts, key=lambda t: t.en)


def test_acepta_token_de_genero_castellano(entorno):
    corpus, editar = entorno
    editar(_swing("%name% lanza un tajo, furios%o%, a su enemigo con {un hacha de mano | un hacha}."))
    assert lotes.fusionar(1) == 0


def test_rechaza_token_de_genero_con_otro_sufijo(entorno):
    _rechaza(entorno, _swing("%name% lanza un tajo, furios%o_bro%, a su enemigo con {un hacha de mano | un hacha}."))


def test_rechaza_token_de_genero_sin_pronombre_en_el_ingles(entorno):
    assert lotes.problemas_formales("%name% attacks.", "%name% ataca, furios%o%.", "") != []


def test_acepta_tokens_de_articulo(entorno):
    corpus, editar = entorno
    editar(_swing("%name% lanza un tajo a %art% enemigo, %ese% furios%o%, con {un hacha de mano | un hacha}."))
    assert lotes.fusionar(1) == 0


def test_acepta_repetir_un_token_del_ingles(entorno):
    corpus, editar = entorno
    editar(_swing("%name% lanza un tajo a su enemigo con {un hacha de mano | un hacha}, y %name% sonríe."))
    assert lotes.fusionar(1) == 0


def _mini(cuerpo):
    return 'local pairs = [\n    {\n' + cuerpo + '\n    }\n]\n'


def test_acepta_patron_desde_porcentaje_s():
    orig = lotes.bloques(_mini('        en = "Drive the nomads away from %s."\n        es = ""'))
    nuevo = lotes.entradas_lote(_mini('        mode = "pattern"\n        en = "Drive the nomads away from <town:str>."\n        es = "Expulsa a los nómadas de <town>."'))
    assert lotes.validar(orig, nuevo, set(), [])[0] == []


def test_rechaza_patron_desde_porcentaje_s_que_cambia_el_texto():
    orig = lotes.bloques(_mini('        en = "Drive the nomads away from %s."\n        es = ""'))
    nuevo = lotes.entradas_lote(_mini('        mode = "pattern"\n        en = "Drive <who:str> away from <town:str>."\n        es = "Expulsa a <who> de <town>."'))
    assert lotes.validar(orig, nuevo, set(), [])[0] != []


def test_porcentaje_s_no_confunde_tokens_que_empiezan_por_s():
    orig = lotes.bloques(_mini('        en = "Attack: [color=%skill%]<mhSkill.getName()>[/color]"\n        es = ""'))
    nuevo = lotes.entradas_lote(_mini('        mode = "pattern"\n        en = "Attack: [color=%skill%]<skill:str>[/color]"\n        es = "Ataque: [color=%skill%]<skill>[/color]"'))
    assert lotes.validar(orig, nuevo, set(), [])[0] == []
