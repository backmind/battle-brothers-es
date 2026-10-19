"""Chequeos de calidad del corpus: avisos, nunca bloqueantes.

Uso:
    PYTHONUTF8=1 uv run python es_pack/tools/checks.py

Cada chequeo corresponde a una familia de fallos que ya apareció de verdad en
este proyecto y que se detectó a mano. La idea es que una regresión de estas
no vuelva a pasar inadvertida:

  IMG        el [img] del inglés y el del español no coinciden, lo que en la
             práctica demostró bloques de texto intercambiados entre eventos.
  DUP_ES     una misma traducción en entradas inglesas no relacionadas, firma
             del relleno espurio que dejó el alineado del bootstrap.
  DUP_VECINO dos entradas inglesas distintas y cercanas de la MISMA tabla con
             idéntica traducción, firma del desplazamiento en tablas de
             nombres: una entrada se queda con el valor de su vecina. DUP_ES no
             lo ve porque sólo mira traducciones de más de 15 caracteres, y los
             nombres de tabla casi siempre son más cortos. Así salieron
             Lindwurms llamados "Trols" y las huellas de Goblins como "Orcos".
             Es un aviso para mirar, no un defecto probado: los que quedan son
             convergencias legítimas, dos formas inglesas que en español dan
             una sola ("An " y "A " dan las dos "Un ", 'Desert' y 'of the
             Desert' dan las dos "del Desierto"), o pares donde el inglés se
             repite a sí mismo con una errata. El recuento no baja a cero, y
             no debe: bajarlo a cero exigiría inventar diferencias que el
             español no tiene.
  VARIANTES  el bloque {a|b|c} del español no tiene la misma estructura que el
             del inglés. El juego elige una rama al azar, así que perder una
             deja ramas inalcanzables o descoloca la elección. Se compara
             INGLÉS contra ESPAÑOL, no el equilibrio interno del español: el
             propio juego trae textos con llaves desparejadas (21 de 23 de
             los casos que parecían rotos lo estaban ya en inglés).
             Los avisos que quedan son 19 y ninguno es deuda: 15 AÑADEN rama,
             repasados uno a uno y legítimos (los traductores metieron variedad
             de su cosecha, y hasta un guiño a The Witcher en el hijo del
             Cazadragones); y 4 tienen las mismas ramas con las llaves
             repartidas de otra forma, que en la práctica no cambia nada porque
             una llave sin ningún separador dentro devuelve su contenido tal
             cual. Eran 22, y no todos inofensivos: tras la 1.0.0 un jugador vio
             un [color] suelto en el contrato de buscar un lugar, que había
             perdido sus llaves interiores, y otros dos casos parecidos estaban
             en este montón. Desde entonces ETIQUETAS mira lo que el recuento de
             llaves no ve.
             Hubo un tercer montón, 37 textos que PERDÍAN rama, y era la deuda
             de es_pack/TAREA-ramas-perdidas.md. Está cerrada: se recuperaron
             las 54 ramas y el recuento de ese montón es 0. Si vuelve a
             aparecer alguno, es una regresión, no trabajo pendiente.
  TOKENS     el español deforma un %token% o usa uno que el inglés del mismo
             texto no menciona nunca. El juego los sustituye en marcha, así
             que uno deformado se le muestra crudo al jugador, y uno que el
             evento no define no tiene con qué rellenarse. Nadie lo vigilaba,
             y un barrido de tildes mío dejó 20 veces %región% en vez de
             %region%. Un token de más que el inglés SÍ usa en otra rama es
             seguro, y a veces es el español corrigiendo al inglés: en
             event_162 el original escribe "you meet with employer", sin los
             signos de porcentaje, y el español pone bien %employer%.
  RECORTE    faltan tokens y sin embargo las ramas cuadran, que es la firma de
             una rama traducida en resumen: el español se salta una frase o
             una escena entera y se lleva por delante sus %SPEECH_ON%. Se
             separó de TOKENS porque no se repara tocando un marcador, sino
             traduciendo lo que falta. Cuando además faltan ramas, el aviso no
             se emite: eso ya lo cuenta VARIANTES y es la misma deuda contada
             dos veces (ver es_pack/TAREA-ramas-perdidas.md).
  PUNTUACION signo de cierre sin su apertura (? sin ¿, ! sin ¡).
  TILDES     palabra sin tilde que el resto del corpus escribe acentuada, con
             lista de homógrafos protegidos para no dar falsos positivos. La
             regla general es de rareza (sólo avisa si la forma sin tilde es
             marginal frente a la acentuada), y por eso dejaba escapar las que
             se repiten: "barbaro" salía 7 veces frente a 71 de "bárbaro". Las
             formas cuya versión sin tilde NO es palabra en español van aparte,
             en SIEMPRE_CON_TILDE, y se avisan sin pasar por ese filtro.
  REGISTRO   formas fuera de la política acordada (usted en interfaz, voseo,
             jerga peninsular). El usted de un personaje hacia el capitán es
             decisión editorial y NO se avisa.
             Aquí decía que el vosotros narrativo también era decisión
             editorial, y era falso: había 40 formas de vosotros y en 15 de los
             25 ficheros convivían con su equivalente en ustedes, hasta el
             punto de que el mismo comandante gritaba "¡CARGAD!" y ordenaba
             "carguen" en el mismo evento. Un recurso no se contradice dentro
             de una línea de diálogo; era el sesgo de quien tradujo esa tanda.
             Y aquí decía a continuación que estaban todas convertidas y que
             por eso no hacía falta vigilarlo, y también era falso: quedaban
             DOCE vivas hasta el 01/09/2026 ("¡Asaltad el fuerte!", "¿Sois
             cazadores de bestias?", "Guardad todo"), y nadie las veía porque
             este chequeo solo miraba voseo y jerga. Dar por hecho que una
             normalización quedó completa, sin un detector que lo sostenga, es
             exactamente como se pierden doce. Ahora se vigila por tres vías:
             formas conjugadas, clítico "os", e imperativo en -ad/-ed/-id
             validado contra el infinitivo en el propio corpus, que es lo que
             evita marcar "ciudad" o "juventud". Probado en los dos sentidos:
             caza las catorce formas de prueba y no da ningún falso positivo.
             Tras la 1.0.0 aparecieron doce más que ninguna vía veía, con el
             clítico pegado ("Decidles", "Degolladlos", "Dadle"): ahora el
             imperativo se busca también con clítico, validado además por el
             participio ("degollado"), y nunca delante de un %token%, que es
             un participio con marca de género.
  CONTROL    carácter de control o invisible dentro de una traducción. Salió de
             la QA del 31/08: una cadena llevaba dos tabuladores verticales
             (U+000B) donde el inglés no tenía ningún salto, y ni se veían al
             leer ni los cazaba nadie. Peor todavía, splitlines() de Python los
             trata como fin de línea, así que partían la línea en dos y los
             barridos escritos con esa función dejaban de ver el par entero sin
             avisar de nada. Se vigilan también el espacio duro, los de ancho
             cero y la marca de orden de bytes, por el mismo motivo: no se ven.
             El recuento tiene que ser 0.
  ANCHO      traducción que no cabe en un recuadro de tamaño fijo. Salió de un
             jugador tras la 1.0.0: los botones de los juramentos se cortaban
             por los dos lados, porque el español había perdido el salto de
             línea del inglés y los botones de evento no parten línea
             (white-space: nowrap), y alguna descripción de origen se salía
             por abajo de su columna, que no tiene barra. Se mide con la
             anchura real de la fuente del juego (ANCHO_CAR), con un margen
             calibrado en partida por lo que el juego ensancha las letras y
             por el icono de los botones (ver BOTON_REM y ORIGEN_REM). Mira dos clases
             que se reconocen sin ambigüedad en el corpus: los botones de
             ambición y juramento (ficheros *_ambition.nut, el único texto con
             un salto de línea suelto) y las descripciones de origen
             (*_scenario.nut, las que empiezan por [p=c][img]). Las opciones de
             evento y contrato normales tienen el mismo presupuesto por línea,
             pero el corpus no las distingue de otros textos sin el código del
             juego delante: si BB_HERRAMIENTAS apunta al árbol descompilado
             (comparer/original_current), se sacan de ahí (el Text de cada
             opción) y se miden también, con la rama más ancha de cada llave.
             Sin el árbol, esa parte se salta. El recuento tiene que ser 0.
  ETIQUETAS  alguna rama del español deja una etiqueta sin pareja, o la cierra
             antes de abrirla, donde ninguna rama del inglés lo hace: [color]
             (también el que pone el juego por %SPEECH_ON% y %SPEECH_OFF%),
             [b], [i] y [u]; o sus llaves no casan donde las del inglés sí.
             En pantalla sale como etiqueta suelta. Salió de un jugador tras la
             1.0.0: la presentación del contrato de buscar un lugar acababa en
             [color]. El español había perdido las llaves de un bloque de
             ramas anidado y VARIANTES lo daba por inofensivo, porque contaba
             llaves y no lo que cada rama abre y cierra. Se evalúan todas las
             ramas, con anidamiento, y el orden dentro de cada una. El
             recuento tiene que ser 0.

Salida: recuento por chequeo y unos pocos ejemplos. Código de salida siempre 0.
"""
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "es_pack" / "tools"))
from build_dist import CORPUS, get_field, load_blocks  # noqa: E402

EJEMPLOS = 4

IMG_RE = re.compile(r"\[img\]([^\[]+)\[/img\]")
# Los %token% los sustituye el juego en marcha y tienen que coincidir
# literalmente con los del ingles. Si el espaniol pierde uno, esa parte del
# texto se queda sin rellenar; si lo deforma, el jugador ve el marcador crudo.
TOKEN_RE = re.compile(r"%[A-Za-z_][A-Za-z0-9_]*%")
# Un token deformado ya no encaja con el patron de arriba, asi que sin esto solo
# se veria como "falta el bueno" y no se sabria que hay uno roto al lado. Exige
# empezar por letra ASCII para no confundirse con un porcentaje del texto.
TOKEN_ROTO_RE = re.compile(r"%[A-Za-z_][A-Za-z0-9_ÁÉÍÓÚÜÑáéíóúüñ]*%")
# Bloques de variantes {a|b|c}: el juego elige una rama al azar. Si el español
# tiene menos ramas que el inglés, la elección puede caer en la equivocada. El
# corpus codifica las llaves como \x7b y \x7d, así que se cuentan las dos formas.
ABRE_RE = re.compile(r"\{|\\x7b")
CIERRA_RE = re.compile(r"\}|\\x7d")
WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{4,}")
VOSEO_RE = re.compile(r"\b(?:tenés|podés|querés|sabés|vení|mirá|dejá|regresás)\b", re.I)
JERGA_RE = re.compile(r"\b(?:molón|molona|chaval|guay|flipar|mola)\b", re.I)
# "vale" solo cuenta como jerga si es interjección: al principio o entre pausas
VALE_INTERJ_RE = re.compile(r'(?:^|[.!?¡¿"\n]\s*)¿?[Vv]ale[.,!?]')
# Caracteres de control sueltos dentro del texto. El corpus solo debe llevar
# tabulador (\t), que sí aparece en algún literal del juego; cualquier otro es
# corrupción. Se encontró así el par de tabuladores verticales del 31/08, que
# el inglés no tenía y que splitlines() partía en dos, escondiendo el fallo a
# los barridos que usaran esa función.
CONTROL_RE = re.compile("[\\x00-\\x08\\x0b-\\x1f\\x7f\\u0085\\u00a0\\u200b\\u2028\\u2029\\ufeff]")

# El vosotros no lo miraba nadie: se dio por eliminado en la normalizacion de
# registro y quedaron doce vivos hasta el 01/09/2026 ("¡Asaltad el fuerte!",
# "¿Sois cazadores de bestias?"). El detector viene del analisis de la 3.0.5 y
# tiene tres vias: formas conjugadas, clitico "os", e imperativo en -ad/-ed/-id
# validado contra el infinitivo en el propio corpus, que es lo que evita los
# falsos positivos. Sin esa validacion, "ciudad" o "juventud" darian aviso.
VOS_FORMAS_RE = re.compile(
    r"\b(vosotros|vosotras|vuestr[oa]s?|habéis|tenéis|podéis|queréis|debéis|sabéis|"
    r"veréis|seréis|haréis|iréis|estáis|sois|vais|decís|venís|hacéis|dais|"
    r"[a-záéíóúñ]{3,}(?:áis|éis))\b", re.I)
# "seis" y sus compuestos acaban en -éis sin ser verbos.
SEIS_RE = re.compile(r"\b(?:seis|dieciséis|dieciseis|veintiséis|veintiseis)\b", re.I)
OS_CLITICO_RE = re.compile(
    r"(?:^|[\s¡¿\"])os\s+(?:he|ha|han|voy|doy|dar|dig|digo|lo|la|los|las|"
    r"le|les|pag|dej|llev|ofrez|espera|juro|prometo|advierto|aseguro|"
    r"ruego|pido|suplico|maldig|mat|vais|dais)", re.I)
IMPERATIVO_VOS_RE = re.compile(r"\b([a-záéíóúñ]{5,}(?:ad|ed|id))\b(?!%)", re.I)
# El mismo imperativo con clítico pegado ("Decidles", "Degolladlos",
# "Barrédlos"): el anterior no lo ve porque la palabra no acaba en -d. La raíz
# se valida igual, contra el infinitivo del corpus.
IMPERATIVO_CLITICO_RE = re.compile(
    r"\b([a-záéíóúñ]+?(?:ad|ed|id|ád|éd|íd))(?:me|te|le|les|lo|la|los|las|nos|se)"
    r"(?:lo|la|los|las)?\b(?!%)", re.I)
# Sustantivos en -ad/-ud/-id que no son imperativos de nada. La validacion
# contra el infinitivo ya filtra casi todo; esto cubre los que coinciden por
# casualidad con un verbo del corpus.
NO_ES_VERBO = set("""ciudad verdad edad mitad libertad voluntad amistad piedad crueldad
maldad bondad lealtad dificultad cantidad calidad oscuridad humanidad realidad
enfermedad necesidad propiedad sociedad autoridad seguridad habilidad capacidad
mortalidad eternidad divinidad santidad brutalidad hostilidad casualidad curiosidad
felicidad gravedad humedad novedad obscuridad salud juventud virtud actitud gratitud
multitud quietud red sed pared merced usted huesped cesped vid ardid id lid sud sur
soledad tempestad majestad heredad deidad unidad utilidad vanidad ansiedad atrocidad
barbaridad castidad claridad comunidad densidad dignidad diversidad entidad facilidad
fertilidad fidelidad generosidad identidad inmortalidad inmensidad intensidad intimidad
localidad moralidad mortandad oportunidad personalidad posibilidad prioridad profundidad
prosperidad pubertad responsabilidad rivalidad sanidad sensibilidad simplicidad
sinceridad solemnidad suciedad superioridad tenacidad totalidad tranquilidad vecindad
velocidad vitalidad abad cavidad impunidad beldad hospitalidad ferocidad agilidad
enemistad orfandad continuidad debilidad david madrid""".split())


# Formas cuya versión sin tilde NO es palabra en español. Se avisan SIEMPRE, sin
# pasar por el filtro de rareza de más abajo. Ese filtro las dejaba escapar
# cuando la forma mala se repite: "barbaro" salía 7 veces frente a 71 de
# "bárbaro", así que no llegaba a marginal y no se avisaba. Aparecieron todas
# revisando world_location_names a mano. La lista crece cuando salga otra.
SIEMPRE_CON_TILDE = {
    "cabana": "cabaña", "cabanas": "cabañas",
    "vegetacion": "vegetación",
    "monticulo": "montículo", "monticulos": "montículos",
    "barbaro": "bárbaro", "barbaros": "bárbaros",
    "barbara": "bárbara", "barbaras": "bárbaras",
    "reunion": "reunión",
    "nomada": "nómada", "nomadas": "nómadas",
    "conclave": "cónclave",
    # segunda tanda, del barrido de todo el corpus
    # "regiones" y "visiones" NO llevan tilde: el plural de región y visión la
    # pierde porque cambia la sílaba tónica. No van en esta lista.
    "region": "región",
    "algun": "algún",
    "golem": "gólem", "golems": "gólems",
    "estupido": "estúpido", "estupidos": "estúpidos",
    "estupida": "estúpida", "estupidas": "estúpidas",
    "rios": "ríos",
    "crias": "crías",
    "jabali": "jabalí", "jabalies": "jabalíes",
    "rapida": "rápida", "rapidas": "rápidas",
    "rapido": "rápido", "rapidos": "rápidos",
    "alquitran": "alquitrán",
    "sequia": "sequía",
    "union": "unión",
    "arrastrandose": "arrastrándose",
    "escandalo": "escándalo",
    "lideres": "líderes",
    "leido": "leído", "leida": "leída",
    "totem": "tótem",
    "imbecil": "imbécil",
    "vision": "visión",
    "dragon": "dragón",
    "caido": "caído", "caida": "caída",
    "paramo": "páramo",
    "subterraneo": "subterráneo", "subterraneos": "subterráneos",
    "subterranea": "subterránea", "subterraneas": "subterráneas",
    # tercera tanda, del barrido de tildes de MÁS. Buscando tildes sobrantes
    # salieron siete "Tumulos" en la tabla de nombres de sitio frente a un solo
    # "Túmulos" bien escrito. La regla de rareza no llegaba: mira si la forma
    # llana es marginal frente a la acentuada, y aquí la marginal era la buena.
    "tumulo": "túmulo", "tumulos": "túmulos",
}

# Homógrafos: la forma sin tilde también existe y es correcta.
PROTEGIDAS = {"asesino", "disparo", "perdida", "perdidas", "ultimo", "publico",
              "practico", "critico", "domino", "acabo", "celebro", "continuo",
              "deposito", "estimulo", "habito", "limite", "termino", "titulo",
              # primera persona del presente, que en boca de un personaje es
              # tan comun como el preterito de tercera: "gano arriesgando",
              # "no compro esa tonteria", "el grupo con el que viajo"
              "gano", "hablo", "trabajo", "pago", "espero", "camino",
              "compro", "dejo", "viajo", "quemo",
              # adjetivos que coinciden con una forma verbal acentuada
              "sabia", "sabias", "continua", "continuas",
              # "canon" es palabra, y ademas sostiene un chiste: el ladron pide
              # que su ejecucion "no sea canon", que es 'cañón' escrito con una-
              "canon"}

# La subordinada delata al subjuntivo. "dondequiera que los encontraran" es
# correcto sin tilde; "los encontraran maniana" seria futuro y la llevaria. Sin
# esto, dieciocho de los veinte avisos de TILDES eran subjuntivos e imperfectos
# perfectamente escritos, y los dos defectos de verdad quedaban enterrados.
# El precio: un futuro mal escrito justo detras de "que" ya no se avisa.
SUBORDINANTE_RE = re.compile(
    r"\b(?:que|si|cuando|aunque|ojal[áa]|quien|donde|dondequiera|mientras|"
    r"hasta|antes|despu[ée]s|para)\b[^.;:!?]{0,40}$", re.I)
SUBJUNTIVO_RE = re.compile(
    r"(?:ara|aras|aran|era|eras|eran|iera|ieras|ieran|ase|ases|asen|"
    r"iese|ieses|iesen|e|es|en)$", re.I)


def sin_tildes(palabra):
    return "".join(c for c in unicodedata.normalize("NFD", palabra.lower())
                   if unicodedata.category(c) != "Mn")


MARCADOR_RE = re.compile(r"<[^<>]*>|%[^%\s]*%|\[[^\[\]]*\]")


def sin_marcadores(texto):
    """Quita los marcadores del juego antes de mirar palabras.

    El interior de `<captura>`, `%token%` y `[color=...]` no es prosa: es
    sintaxis que tiene que coincidir literalmente con el inglés. Si el chequeo de
    tildes lo mira, acaba pidiendo que se acentúe el nombre de una captura, y
    hacerle caso rompe el par y lo manda a cuarentena. Ya pasó dos veces con la
    misma captura, `<vision>`.
    """
    return MARCADOR_RE.sub(" ", texto)


def plegar_acentos(texto):
    """Quita tildes, diéresis y la virgulilla de la eñe, conservando la caja.

    Sirve para COMPARAR traducciones. Dos entradas de la misma tabla que sólo se
    diferencian en una tilde no son dos traducciones distintas: son la misma con
    una errata en alguna de las dos. Comparando así salen sin tener que corregir
    el acento primero, que es como aparecieron "Campamento nómada" repetido en
    Nomad Camp y Nomad Encampment.

    La caja SÍ se conserva a propósito: la usamos para distinguir las variantes
    en mayúscula que el juego mantiene aparte ("the Hound" frente a "The Hound").
    """
    return "".join(c for c in unicodedata.normalize("NFD", texto)
                   if unicodedata.category(c) != "Mn")


def pares():
    for bloque in load_blocks(CORPUS):
        en, es = get_field(bloque, "en"), get_field(bloque, "es")
        if en and es:
            yield en, es


FILE_RE = re.compile(r"^\s*// FILE: (.+)$")
EN_RE = re.compile(r'^en = "(.*)"$')
ES_RE = re.compile(r'^es = "(.*)"$')
# Dos entradas de la misma tabla más separadas que esto ya no son vecinas: que
# compartan traducción deja de ser sospechoso y pasa a ser sinonimia normal.
VENTANA_VECINO = 40


def entradas_en_orden(corpus=CORPUS):
    """(fichero, posición, en, es) en el orden en que viven en el corpus.

    Hace falta el orden y el fichero, que load_blocks no conserva: los
    comentarios `// FILE:` viven entre bloques, no dentro de ellos.
    """
    lineas = Path(corpus).read_text(encoding="utf-8").split("\n")
    fichero, pos = "?", 0
    for i, linea in enumerate(lineas):
        m = FILE_RE.match(linea)
        if m:
            fichero, pos = m.group(1).strip().replace("\\", "/").split("/")[-1], 0
            continue
        m_en = EN_RE.match(linea.strip())
        if not m_en or i + 1 >= len(lineas):
            continue
        m_es = ES_RE.match(lineas[i + 1].strip())
        if m_es:
            yield fichero, pos, m_en.group(1), m_es.group(1)
            pos += 1


def dup_vecino(corpus=CORPUS):
    """Dos entradas inglesas DISTINTAS y cercanas de la misma tabla con idéntica
    traducción.

    Es la firma del desplazamiento en tablas de nombres: una entrada se queda con
    el valor de su vecina y las dos acaban diciendo lo mismo. DUP_ES no lo ve
    porque sólo mira traducciones de más de 15 caracteres, y los nombres de
    tabla son casi siempre más cortos ("Trols", "Orcos", "Piqueros").
    """
    por_fichero = defaultdict(lambda: defaultdict(list))
    for fichero, pos, en, es in entradas_en_orden(corpus):
        if es:
            # se agrupa por la forma sin acentos: si dos entradas solo se
            # diferencian en una tilde, el duplicado esta ahi igualmente
            por_fichero[fichero][plegar_acentos(es)].append((pos, en, es))

    avisos = []
    for fichero, por_es in sorted(por_fichero.items()):
        for _, apariciones in sorted(por_es.items()):
            if len(apariciones) < 2:
                continue
            apariciones.sort()
            for (p1, en1, es1), (p2, en2, es2) in zip(apariciones, apariciones[1:]):
                if en1 == en2 or p2 - p1 > VENTANA_VECINO:
                    continue
                if es1 == es2:
                    avisos.append('%s: %r y %r comparten "%s"'
                                  % (fichero, en1, en2, es1))
                else:
                    avisos.append('%s: %r dice "%s" y %r dice "%s"; solo difieren '
                                  "en acentos" % (fichero, en1, es1, en2, es2))
    return avisos


# Avance de cada carácter en milésimas de em, sacado de la fuente con la que el
# juego pinta botones y descripciones (gfx/fonts/free_universal/
# FreeUniversal-Regular-edited.ttf, ui/fonts.css). Lo que no está aquí mide
# como una "n".
ANCHO_CAR = {}
for _w, _cs in {
    229: "ilí", 254: "’", 261: "IÍ", 275: ",.:;", 286: "j", 300: " ", 319: "-",
    329: "f", 345: "|", 350: "t", 359: "()", 362: "r", 368: "!'¡", 396: "/[\\]",
    436: "“”", 451: '"', 468: "z", 487: "{}", 498: "k", 500: "_–", 503: "s",
    517: "?¿", 521: "c", 529: "L", 534: "vy", 547: "x", 552: "aàá", 557: "eé",
    559: "0123456789", 568: "J", 569: "F", 572: "huúü", 573: "nñ", 590: "bg",
    591: "d", 592: "oó", 599: "pq", 606: "EÉ", 612: "T", 615: "Z", 622: "P",
    629: "R", 653: "V", 656: "*", 661: "S", 664: "K", 665: "Y", 673: "B",
    680: "C", 703: "X", 709: "H", 720: "D", 723: "NÑ", 736: "UÚ", 745: "#",
    750: "AÁ", 761: "G", 766: "&", 773: "OÓ", 784: "Q", 813: "w", 896: "m",
    897: "M", 928: "%", 972: "W", 1000: "+<=>@—",
}.items():
    for _c in _cs:
        ANCHO_CAR[_c] = _w / 1000
# Botones de evento: 1.8 rem en una etiqueta de unos 77 rem. El inglés más
# largo de la clase usa 71.6 (discover unique locations, línea 1), pero el
# texto va centrado y a la izquierda está el icono de la ambición (22 px desde
# 1 rem): en partida, una línea de 71.1 quedaba pegada a él. 67.5 deja algo
# más de 1.5 rem de aire a cada lado del icono.
BOTON_REM, BOTON_FUENTE = 67.5, 1.8
# Descripción de origen: la columna mide 41 rem a 1.6 rem, pero el juego pinta
# las letras algo más anchas que sus avances (el redondeo del hinting a
# píxeles), y la primera medida, a 41 rem y 13 renglones, dejó cuatro orígenes
# saliéndose por abajo en partida. Calibrado contra esa prueba: a 39 rem los
# que se salían, o quedaban a ras, eran exactamente los cuatro de 14 renglones
# (cazahombres, juramentados, desertores, cazadores de bestias), y los de 13 o
# menos cabían.
ORIGEN_REM, ORIGEN_FUENTE, ORIGEN_RENGLONES = 39.0, 1.6, 13
_MARCADO_RE = re.compile(r"\[img\][^\[]*\[/img\]|\[/?[a-z]+(?:=[^\]]*)?\]")


def ancho_rem(texto, fuente):
    """Anchura en rem con que el juego pinta el texto en una línea. Un %token%
    cuenta como un nombre corto, igual en los dos idiomas."""
    texto = TOKEN_RE.sub("Hans", _MARCADO_RE.sub("", texto))
    return sum(ANCHO_CAR.get(c, 0.573) for c in texto) * fuente


def renglones(texto, ancho, fuente):
    """Renglones que ocupa el texto con ajuste por palabras en una columna."""
    n = 0
    for parrafo in _MARCADO_RE.sub("", texto).split("\n"):
        n += 1
        linea = ""
        for palabra in parrafo.split(" "):
            prueba = linea + " " + palabra if linea else palabra
            if linea and ancho_rem(prueba, fuente) > ancho:
                n += 1
                linea = palabra
            else:
                linea = prueba
    return n


def _crudo(s):
    return (s.replace("\\n", "\n").replace("\\x22", '"').replace('\\"', '"')
             .replace("\\x7b", "{").replace("\\x7d", "}"))


def ancho_recuadros(corpus=CORPUS):
    """Traducciones que no caben en su recuadro fijo (ver ANCHO arriba)."""
    avisos = []
    for fichero, _pos, en, es in entradas_en_orden(corpus):
        en, es = _crudo(en), _crudo(es)
        if (fichero.endswith("_ambition.nut") and en.count("\n") == 1
                and "[img]" not in en and "<" not in en):
            lineas = es.split("\n")
            peor = max(ancho_rem(l, BOTON_FUENTE) for l in lineas)
            if peor > BOTON_REM or len(lineas) > 2:
                avisos.append("%s: botón de %d líneas, la más ancha %.1f rem (máximo %s, 2 líneas): %s"
                              % (fichero, len(lineas), peor, BOTON_REM, es[:50]))
        elif fichero.endswith("_scenario.nut") and en.startswith("[p=c][img]"):
            n = renglones(es, ORIGEN_REM, ORIGEN_FUENTE)
            if n > ORIGEN_RENGLONES:
                avisos.append("%s: la descripción ocupa %d renglones (máximo %d)"
                              % (fichero, n, ORIGEN_RENGLONES))
    return avisos


# Una opción de evento o contrato es una tabla que empieza por su Text.
_OPCION_RE = re.compile(r'\{\s*Text = "((?:[^"\\]|\\.)*)"')
_LLAVE_RE = re.compile(r"\{([^{}]*)\}")


def textos_de_opciones(arbol):
    """Los Text de las opciones de events/ y contracts/ del árbol descompilado."""
    textos = set()
    for sub in ("events", "contracts"):
        for f in (arbol / sub).rglob("*.nut"):
            textos.update(_crudo(m.group(1)) for m in
                          _OPCION_RE.finditer(f.read_text(encoding="utf-8", errors="replace")))
    return textos


def linea_mas_ancha(texto):
    """Anchura en botón de la línea más ancha, quedándose con la rama más ancha
    de cada {a | b} (las llaves de dentro primero)."""
    while _LLAVE_RE.search(texto):
        texto = _LLAVE_RE.sub(lambda m: max(m.group(1).split("|"),
                                            key=lambda r: ancho_rem(r.strip(), BOTON_FUENTE)).strip(), texto)
    return max(ancho_rem(l, BOTON_FUENTE) for l in texto.split("\n"))


def ancho_opciones(arbol, corpus=CORPUS):
    """Opciones de evento cuyo español no cabe en el botón y el inglés sí."""
    textos = textos_de_opciones(arbol)
    avisos = []
    for fichero, _pos, en, es in entradas_en_orden(corpus):
        en, es = _crudo(en), _crudo(es)
        if en not in textos or "<" in en:
            continue
        a_en, a_es = linea_mas_ancha(en), linea_mas_ancha(es)
        if a_es > BOTON_REM >= a_en:
            avisos.append("%s: opción de %.1f rem (máximo %s): %s" % (fichero, a_es, BOTON_REM, es[:60]))
    return avisos


# Lo que abre y cierra cada etiqueta en pantalla. El juego cambia %SPEECH_ON%
# (o %SPEECH_START%) por un [color=...] y %SPEECH_OFF% por su [/color].
_ETIQUETAS = ("color", "b", "i", "u")
_MARCAS_RE = re.compile(r"(%SPEECH_(?:ON|START)%|\[color=[^\]]*\]|\[[biu]\])"
                        r"|(%SPEECH_OFF%|\[/(?:color|[biu])\])")
_VACIO = ((0, 0),) * len(_ETIQUETAS)


def _seguir(a, b):
    # (saldo, mínimo de los saldos parciales) de recorrer a y después b
    return tuple((sa + sb, min(ma, sa + mb)) for (sa, ma), (sb, mb) in zip(a, b))


def _marca(m):
    s = m.group(0)
    if s.startswith("%SPEECH"):
        cual = "color"
    else:
        cual = s.strip("[/]").split("=")[0]
    d = 1 if m.group(1) else -1
    return tuple((d, min(0, d)) if e == cual else (0, 0) for e in _ETIQUETAS)


def _estados(texto):
    """Los estados posibles de las etiquetas al elegir el juego una rama de
    cada {a | b}, con anidamiento. Una llave sin pareja cuenta como texto."""
    def trozo(i, fin):
        # estados posibles de texto[i:fin], que no tiene " | " de este nivel
        res, j = {_VACIO}, i
        while j < fin:
            if texto[j] == "{":
                k, prof = j + 1, 1
                while k < fin and prof:
                    prof += {"{": 1, "}": -1}.get(texto[k], 0)
                    k += 1
                if prof == 0:
                    res = {_seguir(s, r) for s in res for r in bloque(j + 1, k - 1)}
                    j = k
                    continue
            m = _MARCAS_RE.match(texto, j)
            if m and m.end() <= fin:
                res = {_seguir(s, _marca(m)) for s in res}
                j = m.end()
                continue
            j += 1
        return res

    def bloque(i, fin):
        # ramas de texto[i:fin] separadas por " | " del primer nivel
        out, ini, prof, j = set(), i, 0, i
        while j < fin:
            prof += {"{": 1, "}": -1}.get(texto[j], 0)
            if prof == 0 and texto.startswith(" | ", j):
                out |= trozo(ini, j)
                ini = j = j + 3
                continue
            j += 1
        return out | trozo(ini, fin)

    return trozo(0, len(texto))


def etiquetas_rotas(texto):
    """Las etiquetas que alguna rama deja abiertas, cerradas de más o
    cerradas antes de abrirse."""
    return {e for estado in _estados(texto)
            for e, (saldo, minimo) in zip(_ETIQUETAS, estado) if saldo or minimo < 0}


def _llaves_casan(texto):
    prof = 0
    for c in texto:
        prof += {"{": 1, "}": -1}.get(c, 0)
        if prof < 0:
            return False
    return prof == 0


def revisar(datos, corpus=CORPUS):
    avisos = defaultdict(list)

    # ETIQUETAS
    for en, es in datos:
        if not re.search(r"[{\[%]", es):
            continue
        if _llaves_casan(en) and not _llaves_casan(es):
            avisos["ETIQUETAS"].append("llaves sin pareja donde el en casa: %s" % es[:60])
            continue
        nuevas = etiquetas_rotas(es) - etiquetas_rotas(en)
        if nuevas:
            avisos["ETIQUETAS"].append("el es puede dejar %s sin pareja donde el en no: %s"
                                       % ("/".join(sorted(nuevas)), es[:60]))

    # DUP_VECINO y ANCHO, que necesitan el fichero de cada par
    try:
        avisos["DUP_VECINO"] = dup_vecino(corpus)
        avisos["ANCHO"] = ancho_recuadros(corpus)
        from rutas import ARBOLES
        if (ARBOLES / "original_current" / "scripts" / "events").is_dir():
            avisos["ANCHO"] += ancho_opciones(ARBOLES / "original_current" / "scripts", corpus)
    except OSError:
        pass  # sin corpus en disco el resto de chequeos sigue valiendo

    # IMG
    for en, es in datos:
        img_en, img_es = IMG_RE.findall(en), IMG_RE.findall(es)
        if img_en and img_es and img_en[0] != img_es[0]:
            avisos["IMG"].append("%s -> es usa %s" % (img_en[0], img_es[0]))

    # VARIANTES
    for en, es in datos:
        if not (ABRE_RE.search(en) or "|" in en):
            continue
        est_en = (len(ABRE_RE.findall(en)), len(CIERRA_RE.findall(en)), en.count("|"))
        est_es = (len(ABRE_RE.findall(es)), len(CIERRA_RE.findall(es)), es.count("|"))
        if est_en == est_es:
            continue
        perdidas = est_en[2] - est_es[2]
        detalle = ("pierde %d rama(s)" % perdidas if perdidas > 0 else
                   "anade %d rama(s)" % -perdidas if perdidas < 0 else
                   "mismas ramas, llaves distintas")
        avisos["VARIANTES"].append(
            "%s; en %s es %s: %s" % (detalle, est_en, est_es, es[:50]))

    # TOKENS y RECORTE
    for en, es in datos:
        deformados = [t for t in TOKEN_ROTO_RE.findall(es) if not TOKEN_RE.fullmatch(t)]
        if deformados:
            avisos["TOKENS"].append("deformado %s en: %s"
                                    % (sorted(set(deformados)), es[:60]))
        te, ts = Counter(TOKEN_RE.findall(en)), Counter(TOKEN_RE.findall(es))
        faltan, sobran = te - ts, ts - te
        # Si ademas faltan ramas, los tokens que faltan se fueron con la rama:
        # es el mismo defecto que ya cuenta VARIANTES, no uno nuevo. Y si hay
        # tokens deformados, el bueno "falta" porque esta ahi mismo mal escrito.
        mismas_ramas = en.count("|") == es.count("|")
        if faltan and mismas_ramas and not deformados:
            avisos["RECORTE"].append("faltan %s en: %s"
                                     % (sorted(faltan), es[:60]))
        # Sobrar un token solo importa si el evento no lo define, y la unica
        # prueba disponible de que lo define es que el ingles lo use en algun
        # sitio de ese mismo texto.
        indefinidos = sorted(t for t in sobran if t not in te)
        if indefinidos:
            avisos["TOKENS"].append("el ingles no usa nunca %s, pero el espanol si: %s"
                                    % (indefinidos, es[:60]))

    # DUP_ES
    por_es = defaultdict(set)
    for en, es in datos:
        if len(es) > 15:
            por_es[es].add(en)
    for es, ens in por_es.items():
        if len(ens) < 2:
            continue
        listado = sorted(ens)
        base = set(re.findall(r"\w+", listado[0].lower()))
        for otro in listado[1:]:
            palabras = set(re.findall(r"\w+", otro.lower()))
            union = base | palabras
            if union and len(base & palabras) / len(union) < 0.3:
                avisos["DUP_ES"].append("%r comparte es con %r" % (listado[0][:40], otro[:40]))
                break

    # PUNTUACION
    for en, es in datos:
        if es.count("?") > es.count("¿") or es.count("!") > es.count("¡"):
            avisos["PUNTUACION"].append(es[:70])

    # TILDES: la forma sin tilde solo es sospechosa si es un caso RARO frente a
    # la acentuada. Si aparece muchas veces, es una palabra legitima distinta
    # (contrato/contrato, trabajo/trabajo, celebro/celebro...) y no se avisa.
    acentuadas, planas = Counter(), Counter()
    for _, es in datos:
        for w in WORD_RE.findall(sin_marcadores(es)):
            if any(c in "áéíóúüñÁÉÍÓÚÜÑ" for c in w):
                acentuadas[w.lower()] += 1
            else:
                planas[w.lower()] += 1
    canon = {}
    for w, n in acentuadas.items():
        if n >= 10:
            canon.setdefault(sin_tildes(w), (w, n))
    for en, es in datos:
        limpio = sin_marcadores(es)
        for m in WORD_RE.finditer(limpio):
            w = m.group(0)
            bajo = w.lower()
            if any(c in "áéíóúüñÁÉÍÓÚÜÑ" for c in w) or bajo in PROTEGIDAS:
                continue
            if bajo in SIEMPRE_CON_TILDE:
                avisos["TILDES"].append(
                    "'%s' debe ser '%s' en: %s"
                    % (w, SIEMPRE_CON_TILDE[bajo], es[:45]))
                break
            if (SUBJUNTIVO_RE.search(bajo)
                    and SUBORDINANTE_RE.search(limpio[:m.start()])):
                continue
            hit = canon.get(sin_tildes(w))
            if not hit or hit[0] == bajo:
                continue
            correcta, n_acc = hit
            n_plana = planas[bajo]
            if n_plana <= max(2, n_acc * 0.02):
                avisos["TILDES"].append(
                    "'%s' (%d) deberia ser '%s' (%d) en: %s"
                    % (w, n_plana, correcta, n_acc, es[:45]))
                break

    # REGISTRO (solo lo que está fuera de la política acordada)
    # El vocabulario del propio corpus hace de diccionario para validar los
    # imperativos: "asaltad" solo cuenta si "asaltar" existe en el corpus.
    # Con clítico pegado vale también el participio ("degollad" por
    # "degollado"), porque los infinitivos cortos ("dar") no pasan de 3 letras
    # y otros ("degollar") no salen nunca en el corpus.
    infinitivos, palabras = set(), set()
    for _en, es in datos:
        for w in WORD_RE.findall(es):
            w = sin_tildes(w)
            palabras.add(w.lower())
            if len(w) > 3 and w.endswith(("ar", "er", "ir")):
                infinitivos.add(w)

    for en, es in datos:
        if VOSEO_RE.search(es):
            avisos["REGISTRO"].append("voseo: %s" % es[:60])
        elif JERGA_RE.search(es) or VALE_INTERJ_RE.search(es):
            avisos["REGISTRO"].append("jerga: %s" % es[:60])
        else:
            limpio = SEIS_RE.sub("6", es)
            if VOS_FORMAS_RE.search(limpio):
                avisos["REGISTRO"].append("vosotros: %s" % es[:60])
                continue
            if OS_CLITICO_RE.search(limpio):
                avisos["REGISTRO"].append("clítico os: %s" % es[:60])
                continue
            for m in [*IMPERATIVO_VOS_RE.finditer(limpio), *IMPERATIVO_CLITICO_RE.finditer(limpio)]:
                w = sin_tildes(m.group(1)).lower()
                if w in NO_ES_VERBO:
                    continue
                participio = m.re is IMPERATIVO_CLITICO_RE and w[:-1] + "do" in palabras
                if w[:-1] + "r" in infinitivos or w[:-2] + "ir" in infinitivos or participio:
                    avisos["REGISTRO"].append("imperativo de vosotros (%s): %s"
                                              % (m.group(1), es[:50]))
                    break

    # CONTROL
    for en, es in datos:
        for m in CONTROL_RE.finditer(es):
            i = m.start()
            avisos["CONTROL"].append("U+%04X en: ...%s..."
                                     % (ord(m.group(0)), es[max(0, i - 30):i + 30]))

    return avisos


def main():
    datos = list(pares())
    avisos = revisar(datos)
    print("pares con traduccion revisados: %d" % len(datos))
    total = 0
    for nombre in ("IMG", "VARIANTES", "TOKENS", "RECORTE", "DUP_ES", "DUP_VECINO",
                   "PUNTUACION", "TILDES", "REGISTRO", "CONTROL", "ANCHO", "ETIQUETAS"):
        items = avisos.get(nombre, [])
        total += len(items)
        print("\n%-11s %d" % (nombre, len(items)))
        for item in items[:EJEMPLOS]:
            print("    %s" % item[:120])
    print("\ntotal de avisos: %d (informativos: no bloquean el build)" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
