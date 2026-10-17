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


def test_glosario_ida_y_vuelta(tmp_path):
    ts = [lotes.Termino("Hand Axe", "Hacha de mano", "objeto", "a.nut", ""),
          lotes.Termino("Anchor", "", "perk", "b.nut", "contiene: Axe")]
    p = tmp_path / "g.tsv"
    lotes.escribir_glosario(p, ts)
    assert b"\r" not in p.read_bytes()
    assert sorted(lotes.leer_glosario(p), key=lambda t: t.en) == sorted(ts, key=lambda t: t.en)
