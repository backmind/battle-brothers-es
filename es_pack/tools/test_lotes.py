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
