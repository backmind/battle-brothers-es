"""Barrido de coherencia de guiños: si un nombre en se sustituyó por un guiño,
cualquier otro par cuyo en mencione ese nombre debe llevar el guiño en su es."""
import re

from pathlib import Path

RUTA = Path(__file__).resolve().parents[1] / "corpus" / "base_es.nut"
PAR_RE = re.compile(r'\ben = "((?:[^"\\]|\\.)*)"\s*\n\s*es = "((?:[^"\\]|\\.)*)"')

GUINOS = {
    "Sorrel": "Jaskier", "Wargasharak": "Barad-Dur", "Thrak Talun": "Naz' Gul",
    "Vras Ushtar": "Barad' Dur", "Gla-Oth": "Kayran", "Maruk Blot": "Bal Guldur",
    "Dunspike": "Púaoscura", "Antlerfold": "Bosque de los Cien Acres",
    "Grudgebringers": "Los Rencorosos", "Amira": "Altair", "Ibn Sahr": "Ibn Laha'ad",
    "Sir Erkenbrand": "Ser Jaime", "Sir Silvan": "Ser Aegon", "Sir Burkhard": "Ser Dunk",
    "Oswald": "Reginhard", "Skarbrand": "Ragnarr", "Warshout": "Espadachín Negro",
    "Blankenfeste": "Pyke", "Kampfeste": "Desembarco del Caballero",
    "Grunfeste": "Roca Caster", "Blankenstadt": "Puerto Blanco",
    "Holnisland": "Aguasdulces", "Brammingborg": "Castillo Negro",
    "Gunnborg": "Winterfell", "Hammarborg": "Último Hogar", "Groneborg": "Invernalia",
    "Haellborg": "Bastión de Cerwyn", "Halshovel": "Torreón de Crasterr",
    "Quadim": "Lanza del Sol", "Skjoldwold": "Hornwood", "Schwarzmark": "Flotsam",
    "Muckenmark": "Vergen", "Torfmark": "Loc Muinne", "Wolkenstein": "Mahakam",
    "Grunlandfeste": "Praven", "Hoberfeste": "Windsor", "Feldfeste": "Warwick",
    "Finsterwall": "Fuerte Greenkeep", "Gelbburg": "Guarida de Ornlu",
}

src = open(RUTA, encoding="utf-8").read()
incoherentes = 0
for m in PAR_RE.finditer(src):
    en, es = m.group(1), m.group(2)
    if es == "":
        continue
    for nombre, guino in GUINOS.items():
        if en == nombre:
            continue  # el par del guiño en sí
        if re.search(r"\b" + re.escape(nombre) + r"\b", en):
            if guino not in es:
                linea = src[:m.start()].count("\n") + 1
                incoherentes += 1
                print(f"L{linea}: en menciona {nombre!r}, es no lleva {guino!r}")
                print(f"   en: {en[:120]}")
                print(f"   es: {es[:120]}")
print(f"\nincoherencias: {incoherentes}")
