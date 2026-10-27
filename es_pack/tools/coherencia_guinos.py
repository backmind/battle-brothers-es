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
    "Seefeste": "Roca Caster", "Blankenstadt": "Puerto Blanco",
    "Holnisland": "Aguasdulces", "Vardeborg": "Castillo Negro",
    "Gunnborg": "Winterfell", "Hammarborg": "Último Hogar", "Groneborg": "Invernalia",
    "Haellborg": "Bastión de Cerwyn", "Halshovel": "Torreón de Crasterr",
    "Quadim": "Lanza del Sol", "Skjoldwold": "Hornwood", "Schwarzmark": "Flotsam",
    "Hohenfeste": "Vergen", "Waldfeste": "Loc Muinne", "Wolkenstein": "Mahakam",
    "Grunlandfeste": "Praven", "Hoberfeste": "Windsor", "Feldfeste": "Warwick",
    "Finsterwall": "Fuerte Greenkeep", "Holzburg": "Guarida de Ornlu",
    "Koppelstadt": "Dhirrim", "Schwanstadt": "Altojardín", "Eulenmark": "Nottinhem",
    "Sattelfeste": "Nido de Águilas", "Kampaborg": "Fuerte Terror", "Schollburg": "Cuernomartillo",
    "Seedock": "Kayce", "Weissenhaus": "Septo de Piedra", "Seestadt": "Antigua",
    "Blankhoom": "Los Escudos", "Weidefeld": "Uxkhal", "Taubenmoos": "Seto de Piedra",
    "Windburg": "Abismo de Helming", "Scharfenburg": "Puertas de la Luna",
    "Donnersgard": "Torre Sombría", "Tanghaug": "Windholm", "Torvaholm": "Guardiagris",
    "Kargburg": "Campoestrella", "Wikhavn": "Volmark", "Varehaug": "Dedo de Pedernal",
    "Hageburg": "Picaestrella", "Wiesenwacht": "Grimston", "Herrmanswacht": "Darry",
    "Rosenhof": "Amere", "Seeturm": "Reposo del Grajo", "Seedorf": "Yalen",
    "Wolfhaiden": "Veluca", "Felswacht": "Los Dedos", "Oberwallheim": "Jelkala",
    "Birkturm": "Velen", "Gulgash Ghul": "Uruk-Hai", "Highrise": "La Montaña Solitaria",
    "Tomb of Tombe": "Salones del Rey Gris",
    # Reinos Olvidados
    "Wikstadt": "Aguas Profundas", "Kleifeste": "Nunca Invierno", "Otterfeste": "Puerta de Baldur",
    "Seeburg": "Luskan", "Tondersted": "Bryn Shander", "Tonder": "Targos",
    "Lydersholm": "Termalaine", "Wolfenfeste": "Mithril Hall", "Tannenfeste": "Luna Plateada",
    "Tannburg": "Evereska", "Westerholz": "Valle de las Sombras", "Saxdorf": "Vado de la Daga",
    "Kochendorf": "Beregost", "Goldhoft": "Nashkel", "Dahab": "Calimport", "Kabira": "Memnon",
    "Seven Hills Castle": "Candlekeep", "Mossy Ruins": "Myth Drannor",
    "Lost Palace": "Menzoberranzán", "Scragglands": "Valle del Viento Helado",
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

# Y cada guiño tiene que estar en su propio par: una recolocación a medias
# dejaría el nombre en el sitio viejo y el nuevo sin él.
PROPIO_RE = re.compile(r'\ben = "((?:[^"\\]|\\.)*)"\n(?:\s*//[^\n]*\n)*\s*es = "((?:[^"\\]|\\.)*)"')
propios = {m.group(1): m.group(2) for m in PROPIO_RE.finditer(src)}
for nombre, guino in GUINOS.items():
    if nombre in propios and guino not in propios[nombre]:
        incoherentes += 1
        print(f"{nombre!r} no lleva su guiño {guino!r}: {propios[nombre]!r}")
print(f"\nincoherencias: {incoherentes}")
