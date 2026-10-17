"""Amplía cada hit de corrimiento hasta encontrar sus fronteras reales.

Validada el 23/08/2026 contra el plan de aceptación del final del docstring:
los seis casos pasan. Dos defectos que la primera pasada expuso y están
corregidos: la reparación declaraba huérfana a una entrada cuya fuente estaba
en la extensión incierta (a Madness le negaba "Locura" teniéndolo al lado), y
dos ventanas solapadas con k distinto se informaban como independientes cuando
una es necesariamente falsa.

El problema que resuelve: un hit de `shift_detect.py` delata UN punto del
corrimiento, no su extensión. La ventana 56-59 de `item_names` se detectó por
los índices 57 y 59; los extremos reales eran invisibles porque sus palabras no
tienen apoyo léxico. Y al revés, el censo ciego ve un cruce concreto (la
armadura en 25-26 de `character.nut`) pero nada le dice si la racha sigue.
Nadie responde hoy "¿dónde empieza y dónde acaba?". Esto toma cada semilla y
crece hacia arriba y hacia abajo hasta dar con evidencia de recuperación.

Uso:
    PYTHONUTF8=1 uv run python es_pack/tools/shift_window.py
    PYTHONUTF8=1 uv run python es_pack/tools/shift_window.py --fichero item_names
    PYTHONUTF8=1 uv run python es_pack/tools/shift_window.py \
        --semilla character.nut:25:1
La opción --semilla permite sembrar desde un veredicto humano del censo ciego,
no sólo desde los hits estadísticos: las dos fuentes convergen aquí.

No escribe en el corpus: sólo informa. La reparación la decide una persona.

## Las cuatro decisiones de diseño, y por qué

1. HISTÉRESIS. Sembrar exige el margen alto de shift_detect (15.0): ahí no hay
   contexto y un falso arranque contamina todo lo que crezca de él. Pero dentro
   de una ventana ya sembrada la probabilidad previa del vecino no es la de un
   par cualquiera, así que extender pide menos (3.0). Con un solo umbral la
   ampliación muere en el primer vecino de señal débil y volvemos a las
   ventanas truncadas que motivaron esto.

2. LOS CIEGOS NO PARAN, PERO SE ACOTAN. El corrimiento atraviesa entradas sin
   señal: eso es lo que hace falta arreglar. Sin tope, en un fichero 59% ciego
   como item_names una ventana crecería hasta la tabla entera. Tras
   MAX_CIEGOS_SEGUIDOS sin un solo apoyo se corta, y esa frontera queda
   declarada INCIERTA: ahí el juez es el censo humano, no esta herramienta.

3. PARAR EXIGE EVIDENCIA POSITIVA DE RECUPERACIÓN. Frontera firme es "el
   alineamiento actual del vecino está atestiguado y el desplazado no lo
   mejora". Ausencia de señal NO es frontera: confundir "no veo corrimiento"
   con "no lo hay" es el error que ya costó un detector mudo (MINIMO_TRAMO=2).

4. k CONSTANTE POR VENTANA. Un corrimiento nace de una inserción o un borrado,
   así que el desplazamiento no cambia por dentro. Dos rachas vecinas con k
   distinto son dos ventanas (inserción más borrado cercanos) y se informan
   por separado; fundirlas taparía la estructura real.

## Qué informa de cada ventana

- El núcleo: índices con apoyo o ciegos ENTRE apoyos. La reparación mecánica
  (es[i] <- es[i+k]) sólo se propone aquí.
- Las extensiones inciertas: colas de ciegos entre el último apoyo y la
  frontera. Pueden pertenecer a la ventana (56 pertenecía) pero la máquina no
  puede afirmarlo: van marcadas para el censo.
- Las huérfanas: con k<0 las |k| primeras entradas del núcleo no tienen valor
  de origen (su texto correcto no existe en el fichero); con k>0, las últimas.
  Rellenarlas es traducir, no reparar.
- Los sobrantes: los valores actuales que ninguna entrada reclama tras la
  reparación (el "Buscatripas" del final de 56-59).

## Plan de aceptación, con su resultado (23/08/2026)

1. 56-59 de item_names: núcleo 57-59, el 56 en extensión incierta, sobrante
   "Buscatripas", y la reparación completa (57 Locura, 58 Escultor, 59
   Cuchillo de guerra). PASA.
2. 86-88: la máquina no puede sembrar ahí (zona ciega entera, los valores son
   compuestos únicos), así que el plan original estaba mal escrito: la semilla
   legítima es el veredicto del censo. Sembrando item_names.nut:87:+1 produce
   núcleo 87 con 86 y 88 en extensiones y la propuesta 87 Llevamuerte,
   compatible con el censo y sin tragarse el 89. PASA con ese límite honesto.
3. 130-131 (Pole/Staff): propone 131 Bastón con fuente en zona incierta y
   recupera por ambos lados. PASA.
4. 462/464: salen dos ventanas con k distinto Y AMBAS MARCADAS EN CONFLICTO,
   que es lo correcto: la de k=-2 nace de una coincidencia semántica
   (Sellsword's se parece a Mercenary's) y no pueden ser verdad las dos. El
   plan original pedía "una ventana", y eso era pedirle a la herramienta que
   decidiera lo que le toca al censo. PASA reformulado.
5. character.nut:25:+1 (la armadura): propone 25 Abollada y no se traga la
   escala; fronteras firmes a ambos lados. PASA.
6. Ninguna ventana en los tramos sanos (posesivos of the South..of the Moon).
   PASA.

Los numerales de strings.nut (51-57) salen como ventanas y son la clase de
falso positivo conocida de shift_detect: Twenty-two comparte "twenty" con todo
el tramo. Se descartan a mano en segundos; no se filtran en silencio.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "es_pack" / "tools"))
import shift_detect as sd  # noqa: E402
from align_score import VACIAS_EN, VACIAS_ES, palabras  # noqa: E402

UMBRAL_SEMILLA = sd.MARGEN
UMBRAL_EXTENSION = 3.0
"""Histéresis: dentro de una ventana sembrada, extender pide menos que sembrar."""

MAX_CIEGOS_SEGUIDOS = 4
"""Cuántas entradas sin señal se atraviesan antes de declarar la frontera
incierta. Acota el crecimiento en ficheros mayormente ciegos."""

APOYA = "apoya"
CIEGO = "ciego"
RECUPERA = "recupera"
BORDE = "borde"


def evidencia(t, apoyo, pal, base, i, k, n):
    """Qué dice la entrada i sobre el desplazamiento k.

    APOYA     el desplazado está atestiguado y gana con claridad
    RECUPERA  el alineamiento actual está atestiguado y el desplazado no lo
              mejora: evidencia positiva de que aquí el corrimiento no llega
    CIEGO     ni una cosa ni la otra: no detiene el crecimiento, pero cuenta
    BORDE     el desplazado caería fuera de la tabla
    """
    j = i + k
    if not (0 <= j < n):
        return BORDE
    if base[i] is None:
        return CIEGO
    des = sd.puntua(t, apoyo, pal[i][0], pal[j][1])
    des_atestiguado = des is not None and des >= sd.ABS_MIN
    if des_atestiguado and des - base[i] >= UMBRAL_EXTENSION:
        return APOYA
    defendible = base[i] > sd.PISO
    if defendible and (des is None or des <= base[i]):
        return RECUPERA
    return CIEGO


def crece(t, apoyo, pal, base, semilla, k):
    """Amplía desde la semilla en ambas direcciones hasta frontera o tope.

    Devuelve un dict con estados por índice, núcleo, extensiones inciertas y
    el motivo de cada frontera.
    """
    n = len(pal)
    estados = {semilla: APOYA}
    fronteras = {}
    for paso in (-1, +1):
        i = semilla + paso
        ciegos_seguidos = 0
        while True:
            if not (0 <= i < n):
                fronteras[paso] = BORDE
                break
            e = evidencia(t, apoyo, pal, base, i, k, n)
            if e == APOYA:
                estados[i] = APOYA
                ciegos_seguidos = 0
            elif e == CIEGO:
                estados[i] = CIEGO
                ciegos_seguidos += 1
                if ciegos_seguidos > MAX_CIEGOS_SEGUIDOS:
                    fronteras[paso] = "incierta"
                    break
            else:
                fronteras[paso] = e  # RECUPERA o BORDE: frontera firme
                break
            i += paso

    indices = sorted(estados)
    apoyos = [i for i in indices if estados[i] == APOYA]
    lo, hi = apoyos[0], apoyos[-1]
    nucleo = [i for i in indices if lo <= i <= hi]
    return {
        "k": k,
        "semilla": semilla,
        "estados": estados,
        "nucleo": nucleo,
        "ext_arriba": [i for i in indices if i < lo],
        "ext_abajo": [i for i in indices if i > hi],
        "fronteras": fronteras,
    }


def reparacion(ventana, pares):
    """La propuesta mecánica sobre el núcleo: es[i] <- es[i+k].

    Cada entrada del núcleo se clasifica por dónde está su fuente:
      firme      la fuente está en el propio núcleo
      incierto   la fuente está en la extensión incierta: el valor existe y el
                 movimiento es coherente, pero confirma la pertenencia de esa
                 zona a la ventana, así que lo ratifica el censo
      huerfana   la fuente cae más allá de la frontera, en territorio bien
                 alineado: su valor pertenece a otra entrada y no se puede
                 tomar. El texto correcto no existe en el fichero.

    Los sobrantes son los valores del núcleo que nadie reclama tras el
    movimiento (el "Buscatripas" del final de 56-59).

    La primera versión marcaba huérfana toda entrada cuya fuente quedara fuera
    del núcleo, y la aceptación la desmintió: a Madness (57) le declaraba
    huérfana con "Locura" ahí mismo, en el 56 de la extensión.
    """
    k = ventana["k"]
    nucleo = set(ventana["nucleo"])
    conocidos = set(ventana["estados"])  # nucleo + extensiones inciertas
    firmes, inciertos, huerfanas = [], [], []
    for i in sorted(nucleo):
        j = i + k
        if j in nucleo:
            firmes.append((i, pares[i][1], pares[j][1]))
        elif j in conocidos and 0 <= j < len(pares):
            inciertos.append((i, pares[i][1], pares[j][1]))
        else:
            huerfanas.append((i, pares[i][0]))
    reclamados = {i + k for i, _, _ in firmes + inciertos}
    sobrantes = [(i, pares[i][1]) for i in sorted(nucleo)
                 if i not in reclamados]
    return {
        "mueve": firmes,
        "mueve_incierto": inciertos,
        "huerfanas": huerfanas,
        "sobrantes": sobrantes,
    }


def marca_conflictos(ventanas):
    """Dos ventanas del mismo fichero que se solapan con k distinto no pueden
    ser las dos verdad: una inserción no produce eso. Se marcan las dos y
    decide el censo. La aceptación lo encontró en 462 (k=-2, una coincidencia
    semántica: Sellsword's se parece a Mercenary's) contra 464 (k=-1, el
    corrimiento real)."""
    for a in ventanas:
        alcance_a = set(a["estados"])
        for b in ventanas:
            if b is a or b["fichero"] != a["fichero"] or b["k"] == a["k"]:
                continue
            if alcance_a & set(b["estados"]):
                a.setdefault("conflictos", []).append(b["k"])


def semillas_de_detector(grupos, t, apoyo):
    """Cada hit de shift_detect como semilla: (fichero, indice, k)."""
    salida = []
    for h in sd.revisa(grupos, t, apoyo, UMBRAL_SEMILLA):
        for i in h["indices"]:
            salida.append((h["fichero"], i, h["k"]))
    return salida


def agrupa_ventanas(grupos, t, apoyo, semillas):
    """Crece cada semilla y funde las que caen en la misma ventana y mismo k."""
    por_fichero = {n: p for n, p in grupos}
    hechas = []
    cubiertos = set()  # (fichero, k, indice) ya dentro de una ventana crecida
    for fichero, indice, k in sorted(semillas):
        if (fichero, k, indice) in cubiertos:
            continue
        pares = por_fichero.get(fichero)
        if not pares:
            continue
        pal = [(palabras(en, VACIAS_EN), palabras(es, VACIAS_ES))
               for en, es in pares]
        base = [sd.puntua(t, apoyo, pe, ps) for pe, ps in pal]
        v = crece(t, apoyo, pal, base, indice, k)
        v["fichero"] = fichero
        for i in v["estados"]:
            cubiertos.add((fichero, k, i))
        hechas.append(v)
    return hechas


def informa(ventana, pares):
    v = ventana
    print("%s  k=%+d  nucleo %d-%d" % (v["fichero"], v["k"],
                                       v["nucleo"][0], v["nucleo"][-1]))
    if v.get("conflictos"):
        print("   CONFLICTO: solapa con ventana(s) de k=%s en el mismo "
              "fichero; no pueden ser verdad las dos, decide el censo"
              % ", ".join("%+d" % k for k in v["conflictos"]))
    print("   fronteras: arriba %s, abajo %s"
          % (v["fronteras"].get(-1, "?"), v["fronteras"].get(+1, "?")))
    for etiqueta, ext in (("arriba", v["ext_arriba"]), ("abajo", v["ext_abajo"])):
        if ext:
            print("   extension incierta %s: %s (para el censo humano)"
                  % (etiqueta, ext))
    rep = reparacion(v, pares)
    for i, ahora, propuesto in rep["mueve"]:
        print("   %4d  %-26s ahora %-26s propuesta %s"
              % (i, pares[i][0][:26], ahora[:26], propuesto[:26]))
    for i, ahora, propuesto in rep["mueve_incierto"]:
        print("   %4d  %-26s ahora %-26s propuesta %s  [fuente en zona "
              "incierta: ratificar en censo]"
              % (i, pares[i][0][:26], ahora[:26], propuesto[:26]))
    for i, en in rep["huerfanas"]:
        print("   %4d  %-26s HUERFANA: pide traduccion nueva" % (i, en[:26]))
    for i, valor in rep["sobrantes"]:
        print("   sobrante: %r (estaba en %d)" % (valor[:30], i))
    if rep["mueve_incierto"]:
        print("   nota: si el censo confirma la extension, la huerfana real "
              "pasa al extremo de la extension confirmada")
    print()


def main(argv):
    filtro = None
    manuales = []
    if "--fichero" in argv:
        i = argv.index("--fichero")
        filtro = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    while "--semilla" in argv:
        i = argv.index("--semilla")
        fichero, indice, k = argv[i + 1].rsplit(":", 2)
        manuales.append((fichero, int(indice), int(k)))
        argv = argv[:i] + argv[i + 2:]

    grupos = sd.pares_por_fichero()
    t, apoyo = sd.modelo(grupos)
    semillas = semillas_de_detector(grupos, t, apoyo) + manuales
    if filtro:
        semillas = [s for s in semillas if filtro in s[0]]
    print("semillas: %d" % len(semillas))
    print()

    por_fichero = {n: p for n, p in grupos}
    ventanas = agrupa_ventanas(grupos, t, apoyo, semillas)
    marca_conflictos(ventanas)
    for v in ventanas:
        informa(v, por_fichero[v["fichero"]])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
