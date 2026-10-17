"""Saca la cola de trabajo del estrato ciego: lo que `shift_detect.py` no puede juzgar.

El problema que resuelve: `shift_detect.py` es exhaustivo pero su juez es
estadístico, y necesita que una palabra aparezca en otro par para tener con qué
comparar. Medido sobre el corpus, **el 13,8% de los pares no tiene apoyo léxico
ni a favor ni en contra**, y la ceguera se concentra justo donde viven los
corrimientos: el 59,5% de `item_names.nut` y el 50,6% de `character_names.nut`.
Un corrimiento que caiga entero en zona ciega no lo ve nadie.

Ese estrato pide un juez semántico, o sea una persona o un modelo leyendo. Esto
prepara el trabajo: lo agrupa en ventanas con contexto, descarta lo que no hay
que juzgar y lleva la cuenta de lo hecho, para poder ir por lotes.

Uso:
    PYTHONUTF8=1 uv run python es_pack/tools/blind_census.py
        recalcula la cola (tarda unos tres minutos: entrena el modelo)

    PYTHONUTF8=1 uv run python es_pack/tools/blind_census.py --lote item_names
        saca las ventanas de un fichero, listas para leer

    PYTHONUTF8=1 uv run python es_pack/tools/blind_census.py --pendiente
        qué queda por juzgar, según el registro

La cola vive en `es_pack/build/censo_ciego.tsv`, que se regenera. Los veredictos
van en `es_pack/corpus/CENSO_CIEGO.tsv`, que sí se versiona: es el registro de
lo juzgado y lo que hace que el censo se pueda hacer en tandas.

## Qué NO hay que juzgar

De los 1.586 pares ciegos, sólo se apartan los **470 idénticos al inglés**:
nombres propios que se dejan tal cual, "Skoll" a "Skoll", donde no hay nada que
decidir.

Las 23 que se parecen sin ser iguales van marcadas `translit` como pista, pero
entran en el censo. Antes se apartaban, y esa decisión escondió tres defectos
reales, uno de ellos un corrimiento: ver el comentario de `clase_trivial`.

## Advertencia para quien juzgue

`character_names.nut` lleva guiños deliberados del traductor original. Sorrel es
"Jaskier", el Dandelion de The Witcher. No son defectos y no se arreglan. Ante
un nombre que parece cambiado sin motivo, la pregunta correcta es si es un guiño
antes de si es un error.

Y la regla que no se rompe: **el lado `en` no se toca nunca**. Es la clave con la
que Rosetta encuentra el texto en el juego.
"""
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "es_pack" / "tools"))
import shift_detect as sd  # noqa: E402
from align_score import VACIAS_EN, VACIAS_ES, palabras  # noqa: E402

COLA = REPO / "es_pack" / "build" / "censo_ciego.tsv"
REGISTRO = REPO / "es_pack" / "corpus" / "CENSO_CIEGO.tsv"

CONTEXTO = 2
"""Vecinos a cada lado que se muestran con la ventana. Sin contexto no se puede
decir si un valor pertenece a la entrada de al lado, que es la pregunta."""

TAM_VENTANA = 5


def pliega(s):
    sin = unicodedata.normalize("NFD", s)
    return "".join(c for c in sin if not unicodedata.combining(c)).lower()


def clase_trivial(en, es):
    """Los ciegos que no hay que juzgar, y por qué.

    Sólo se aparta del censo lo IDÉNTICO al inglés: un nombre propio que se
    deja tal cual no admite discusión.

    Las que se parecen sin ser iguales se marcan `translit` como pista, pero
    SIGUEN entrando en el censo. La primera versión las apartaba con la regla
    "uno contiene al otro", y salió mal: entre las 23 apartadas había
    `Barb` a "Barba", que es un falso amigo y era un corrimiento de verdad;
    `Parry!` a "¡Parry!", que es un literal inglés sin traducir; y `Tormentor`
    a "Tormento", que se come el sufijo (es "Atormentador"). La regla vale para
    `Optimist` a "Optimista", y no sabe distinguir eso de un calco.

    Apartar 23 entradas ahorraba minutos y escondía defectos. No compensa.
    """
    if pliega(en) == pliega(es):
        return "identico"
    a, b = pliega(en), pliega(es)
    if len(a) > 3 and (a in b or b in a):
        return "translit"
    return "juzgar"


def hay_que_juzgar(clase):
    """Todo menos lo idéntico al inglés."""
    return clase != "identico"


def calcula_cola():
    """Recorre el corpus y devuelve los pares ciegos con su clase."""
    grupos = sd.pares_por_fichero()
    t, apoyo = sd.modelo(grupos)
    filas = []
    for nombre, pares in grupos:
        pal = [(palabras(en, VACIAS_EN), palabras(es, VACIAS_ES))
               for en, es in pares]
        base = [sd.puntua(t, apoyo, pe, ps) for pe, ps in pal]
        for i in range(len(pares)):
            if base[i] is None or base[i] > sd.PISO:
                continue
            hay_rival = False
            for k in sd.DESPLAZAMIENTOS:
                j = i + k
                if 0 <= j < len(pares):
                    s = sd.puntua(t, apoyo, pal[i][0], pal[j][1])
                    if s is not None and s >= sd.ABS_MIN:
                        hay_rival = True
            if hay_rival:
                continue  # eso lo cubre shift_detect, no es ciego
            en, es = pares[i]
            filas.append((nombre, i, en, es, clase_trivial(en, es)))
    return grupos, filas


def escapa(s):
    """Los valores del corpus llevan saltos de línea de verdad, no la secuencia
    \\n: get_field los interpreta al leer. Sin escaparlos, un solo par con salto
    parte la fila del TSV y la cola se vuelve ilegible."""
    return s.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n")


def desescapa(s):
    salida, i = [], 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            siguiente = s[i + 1]
            salida.append({"n": "\n", "t": "\t", "\\": "\\"}.get(siguiente,
                                                                 "\\" + siguiente))
            i += 2
        else:
            salida.append(s[i])
            i += 1
    return "".join(salida)


def escribe_cola(filas):
    COLA.parent.mkdir(parents=True, exist_ok=True)
    with COLA.open("w", encoding="utf-8", newline="") as f:
        f.write("fichero\tindice\tclase\ten\tes\n")
        for nombre, i, en, es, clase in filas:
            f.write("%s\t%d\t%s\t%s\t%s\n"
                    % (nombre, i, clase, escapa(en), escapa(es)))


def lee_cola():
    if not COLA.is_file():
        raise SystemExit(
            "no hay cola en %s. Genérala primero, sin argumentos." % COLA)
    filas = []
    for linea in COLA.read_text(encoding="utf-8").splitlines()[1:]:
        nombre, i, clase, en, es = linea.split("\t")
        filas.append((nombre, int(i), desescapa(en), desescapa(es), clase))
    return filas


def lee_registro():
    """Veredictos ya emitidos, como {(fichero, en): veredicto}.

    Se reconcilia por el lado `en`, **no por el índice**. El índice es la
    posición del par dentro del bloque, así que en cuanto alguien añada un par a
    un fichero, todo lo que va detrás se desplaza y los veredictos apuntan a
    entradas equivocadas. Y no fallaría a gritos: daría por juzgado lo que no lo
    está y volvería a sacar lo que ya se vio.

    No es hipotético: `TAREA-cobertura.md` mide qué literales del juego no cubre
    el corpus, y su precedente (`d5b9e1f`) añadió 23 pares. El índice se
    conserva en el fichero porque sirve para leerlo y para hablar de una
    entrada, pero no manda.
    """
    if not REGISTRO.is_file():
        return {}
    hecho = {}
    for linea in REGISTRO.read_text(encoding="utf-8").splitlines()[1:]:
        if not linea.strip():
            continue
        campos = linea.split("\t")
        hecho[(campos[0], desescapa(campos[3]))] = campos[2]
    return hecho


def ventanas(filas, nombre_fichero, hecho):
    """Agrupa los pendientes de un fichero en ventanas con sus vecinos."""
    objetivos = sorted(i for f, i, en, _, c in filas
                       if f == nombre_fichero and hay_que_juzgar(c)
                       and (f, en) not in hecho)
    grupos = []
    for i in objetivos:
        if grupos and i - grupos[-1][-1] <= CONTEXTO and len(grupos[-1]) < TAM_VENTANA:
            grupos[-1].append(i)
        else:
            grupos.append([i])
    return grupos


def main(argv):
    if "--pendiente" in argv:
        filas = lee_cola()
        hecho = lee_registro()
        por_fich = {}
        for f, i, en, _, c in filas:
            if not hay_que_juzgar(c):
                continue
            por_fich.setdefault(f, [0, 0])
            por_fich[f][0] += 1
            if (f, en) in hecho:
                por_fich[f][1] += 1
        total = sum(v[0] for v in por_fich.values())
        listo = sum(v[1] for v in por_fich.values())
        print("trabajo real: %d pares | juzgados: %d | quedan: %d"
              % (total, listo, total - listo))
        print()
        for f, (n, ok) in sorted(por_fich.items(), key=lambda x: -(x[1][0] - x[1][1])):
            if n - ok:
                print("   %-34s %4d de %4d pendientes" % (f[:34], n - ok, n))
        return 0

    if "--lote" in argv:
        i = argv.index("--lote")
        patron = argv[i + 1]
        filas = lee_cola()
        hecho = lee_registro()
        grupos_pares = {n: p for n, p in sd.pares_por_fichero()}
        ficheros = sorted({f for f, *_ in filas if patron in f})
        if not ficheros:
            raise SystemExit("ningún fichero coincide con %r" % patron)
        for nombre in ficheros:
            pares = grupos_pares.get(nombre)
            if not pares:
                continue
            vs = ventanas(filas, nombre, hecho)
            if not vs:
                continue
            print("=" * 72)
            print("%s   %d ventanas pendientes" % (nombre, len(vs)))
            print("=" * 72)
            for v in vs:
                lo = max(0, v[0] - CONTEXTO)
                hi = min(len(pares) - 1, v[-1] + CONTEXTO)
                print()
                for j in range(lo, hi + 1):
                    marca = ">>" if j in v else "  "
                    print("%s %4d  %-30s %s"
                          % (marca, j, escapa(pares[j][0])[:30],
                             escapa(pares[j][1])[:44]))
        return 0

    grupos, filas = calcula_cola()
    escribe_cola(filas)
    from collections import Counter
    clases = Counter(c for *_, c in filas)
    print("pares ciegos: %d" % len(filas))
    for c, n in clases.most_common():
        print("   %-12s %5d" % (c, n))
    juzgar = [f for f in filas if f[-1] == "juzgar"]
    por_fich = Counter(f[0] for f in juzgar)
    print()
    print("trabajo real por fichero:")
    for nombre, n in por_fich.most_common(12):
        print("   %-34s %4d" % (nombre[:34], n))
    print()
    print("cola escrita en", COLA)
    print("veredictos en", REGISTRO)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
