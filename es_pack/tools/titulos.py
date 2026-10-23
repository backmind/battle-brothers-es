"""Los títulos que van tras el nombre, en femenino para los personajes mujer.

El problema: Legends deja que cualquier personaje sea mujer, pero el título
(«the Brave», «the Penitent») es un literal sin tokens de género, compartido
por hombres y mujeres. El corpus lo traduce en masculino («el Valiente») y el
pack lo pasa a femenino en partida cuando el personaje es mujer: el preload
engancha getName/getTitle (ver src/mod_battle_brothers_es/legends.nut) y busca
el título en la tabla que sale de aquí.

La regla (decisión del propietario): «el» pasa a «la», y cada palabra de la
cabeza del título, hasta la primera preposición, pasa a femenino: -o → -a,
-or → -ora, -ón → -ona, -án → -ana, -ín → -ina. Lo demás no cambia (las
palabras en -e, en -a o en consonante ya valen para los dos géneros). Las
palabras que la regla estropea (invariables o con femenino irregular) van en
EXCEPCIONES, sacadas del barrido de los títulos de los dos corpus; tras una
invariable, la cabeza se corta. «el Águila» y «el Hacha» no cambian.

Puede dar un falso positivo: la tabla se construye con todos los pares
«the X» → «el X», sean títulos o no. Es inofensivo, porque solo se consulta
con el título de un personaje mujer.

Uso, para revisar la tabla entera:
    PYTHONUTF8=1 uv run python es_pack/tools/titulos.py
"""
import re

# Lo que corta la cabeza del título: tras ella, nada concuerda con el personaje
# («la Cazadora de brujas», «la Que no muere», «la Sin techo»).
CORTES = {"de", "del", "la", "las", "los", "el", "con", "sin", "Sin", "que",
          "Que", "no", "No", "y", "en", "a"}

# Palabra masculina → su forma femenina, cuando la regla no la da. Si el valor
# es la misma palabra, es invariable: un objeto, un animal epiceno o un
# extranjerismo, al que solo le cambia el artículo («la Martillo»).
EXCEPCIONES = {
    # Femeninos irregulares.
    "Barón": "Baronesa",
    "Héroe": "Heroína",
    "Hombre": "Mujer",
    "Monje": "Monja",
    "Padre": "Madre",
    "Príncipe": "Princesa",
    "Rey": "Reina",
    "Infante": "Infanta",
    "Caballo": "Yegua",
    "Diablo": "Diablesa",
    "Grandote": "Grandota",
    "Gigante": "Giganta",
    # Comparativos, invariables.
    "Mayor": "Mayor",
    "Menor": "Menor",
    # Cosas, ideas, animales y oficios sin femenino propio (o cuyo femenino
    # es otra cosa: correa, caballa, barda): solo cambia el artículo, y lo que
    # venga detrás concuerda con la palabra, no con el personaje («la Buitre
    # Dorado», «la Colmillo Negro»).
    "Abismo": "Abismo",
    "Arbusto": "Arbusto",
    "Azor": "Azor",
    "Bardo": "Bardo",
    "Buitre": "Buitre",
    "Colmillo": "Colmillo",
    "Correo": "Correo",
    "Espectro": "Espectro",
    "Eunuco": "Eunuco",
    "Gusano": "Gusano",
    "Heraldo": "Heraldo",
    "Paladín": "Paladín",
    "Prodigio": "Prodigio",
    "Retoño": "Retoño",
    "Sabueso": "Sabueso",
    "Soldado": "Soldado",
    "Toro": "Toro",
    "Verdugo": "Verdugo",
    "Zorrillo": "Zorrillo",
    # Decisión del propietario: «caballera» no es la mujer caballero,
    # y «perra» y «zorra» son insultos que el masculino no lleva.
    "Caballero": "Caballero",
    "Perro": "Perro",
    "Zorro": "Zorro",
    "Aguijón": "Aguijón",
    "Anzuelo": "Anzuelo",
    "Azote": "Azote",
    "Búho": "Búho",
    "Cascarón": "Cascarón",
    "Clavo": "Clavo",
    "Comodín": "Comodín",
    "Cuervo": "Cuervo",
    "Error": "Error",
    "Escorpión": "Escorpión",
    "Espejismo": "Espejismo",
    "Estudio": "Estudio",
    "Filo": "Filo",
    "Fuego": "Fuego",
    "Futuro": "Futuro",
    "Halcón": "Halcón",
    "Honor": "Honor",
    "Huracán": "Huracán",
    "Látigo": "Látigo",
    "Martillo": "Martillo",
    "Murciélago": "Murciélago",
    "Rayo": "Rayo",
    "Relámpago": "Relámpago",
    "Repuesto": "Repuesto",
    "Sacrificio": "Sacrificio",
    "Secreto": "Secreto",
    "Sello": "Sello",
    "Serrucho": "Serrucho",
    "Trueno": "Trueno",
    "Zumbido": "Zumbido",
    # «el Largo Alcance»: el adjetivo va con «Alcance», no con el personaje.
    "Largo": "Largo",
}

# Títulos que se quedan enteros: el sustantivo ya es femenino y lleva «el» por
# empezar por a tónica («el Águila», «el Hacha»), que vale igual para ella.
INVARIABLES = {"el Águila", "el Hacha"}

TITULO_RE = re.compile(r"^el [A-ZÁÉÍÓÚÑ]")
_FINALES = (("or", "ora"), ("ón", "ona"), ("án", "ana"), ("ín", "ina"), ("o", "a"))


def feminizar_palabra(palabra):
    if palabra in EXCEPCIONES:
        return EXCEPCIONES[palabra]
    for masc, fem in _FINALES:
        if palabra.endswith(masc):
            return palabra[: -len(masc)] + fem
    return palabra


def feminizar(titulo):
    """«el Viejo Lobo» → «la Vieja Loba». None si no es un título en «el X»."""
    if not TITULO_RE.match(titulo):
        return None
    if titulo in INVARIABLES:
        return titulo
    palabras = titulo.split(" ")[1:]
    for i, p in enumerate(palabras):
        if p in CORTES:
            break
        palabras[i] = feminizar_palabra(p)
        if EXCEPCIONES.get(p) == p:
            break  # lo que sigue concuerda con la palabra invariable
    return " ".join(["la"] + palabras)


def tabla(pares):
    """{título masculino: femenino} de los pares (en, es) «the X» → «el X»."""
    res = {}
    for en, es in pares:
        if en and es and en.startswith("the ") and "%" not in en:
            fem = feminizar(es)
            if fem is not None and fem != es:
                res[es] = fem
    return dict(sorted(res.items()))


def emite(tabla_fem):
    """El .nut que el preload incluye cuando está Legends."""
    def lit(s):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    # Squirrel pide coma tras cada [clave] = valor, no basta el salto de línea.
    filas = ",\n".join("    [%s] = %s" % (lit(m), lit(f)) for m, f in tabla_fem.items())
    return (
        "// Generado por es_pack/tools/build_dist.py desde los corpus (ver\n"
        "// tools/titulos.py). No editar: se corrige el corpus o la tabla de\n"
        "// excepciones de titulos.py.\n"
        'if (!("BattleBrothersEs" in getroottable())) ::BattleBrothersEs <- {};\n'
        "::BattleBrothersEs.TitulosFemeninos <- {\n%s\n};\n" % filas
    )


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import build_dist
    pares = []
    for corpus in build_dist.corpus_del_pack():
        pares += [(build_dist.get_field(b, "en"), build_dist.get_field(b, "es"))
                  for b in build_dist.load_blocks(corpus["ruta"])]
    for m, f in tabla(pares).items():
        print("%s\t%s" % (m, f))
