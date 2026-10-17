# La traducción 3.0.5, medida y adjudicada (01/09/2026)

Este fichero registra por qué el corpus (los pares de traducción inglés-español del pack) no absorbe la revisión 3.0.5 de la traducción comunitaria, con las cifras que sostienen la decisión. La pregunta volverá a salir: quien compare los dos árboles de la traducción comunitaria (las dos copias en disco que se describen [justo abajo](#el-hecho-de-partida-que-no-estaba-escrito-en-ninguna-parte)) encontrará 12.740 diferencias y querrá saber qué se deja fuera.

## El hecho de partida, que no estaba escrito en ninguna parte

Hay **dos** árboles de la traducción comunitaria en disco, y son revisiones distintas:

- `comparer/spanish_tr`, fechado en enero de 2026, 2.345 ficheros. **Es del que se construyó nuestro corpus.**
- `comparer/spanish_305`, la versión 3.0.5, 2.252 ficheros. **Nunca se absorbió en bloque**, aunque sí se ha usado como referencia para valores sueltos (los pares por id, los nombres de trasfondo y de rasgo del 31/08).

La [historia del proyecto](../../docs/HISTORIA.md) dice que partimos de la serie 3.x de ElGranFoca, y en cuanto a la autoría es cierto, pero el árbol concreto que alimentó el corpus es el de enero. La distinción salió a la luz el 31/08, cuando el propietario preguntó por qué "Auxiliar antiguo" y no "Auxiliar Ancestral": lo segundo es lo que dice la 3.0.5.

## La medida

Alineamiento a tres bandas (inglés del juego, enero, 3.0.5) con el método de `gt_align.py`: los ficheros traducidos son los mismos ficheros del juego, así que sus literales van en el mismo orden; se alinea con difflib y solo se emparejan anclas y huecos (los tramos que difflib da por iguales y los que da por distintos) del mismo tamaño. Salen 62.250 tripletas alineadas en 2.202 ficheros, de las que **12.740 (20,5%) tienen traducción distinta en los dos árboles españoles**.

Así se reparte nuestro corpus en esas 12.740, normalizando los escapes que el corpus reescribe (`\'`, `\x7b`, `\x22`; sin normalizar, en un cruce crudo toda cadena con apóstrofo, llave o comilla parece no tener par):

| nuestro valor | filas |
|---|---|
| es el de enero | 6.770 |
| es un tercero, curación propia del proyecto | 3.393 |
| ya es el de la 3.0.5 | 494 |
| la cadena no tiene par | 2.083 |

La segunda fila indica que **una de cada cuatro discrepancias entre los dos árboles ya está resuelta por el pack en un valor que no es ninguno de los dos.**

El ruido de alineamiento se descartó como explicación porque es menor del 1%. El 83,5% de las filas sale de ficheros con recuento idéntico de literales en los tres árboles, donde el alineamiento es la identidad; la firma del corrimiento (el rastro que deja una lista desplazada una posición respecto al inglés) salta en 104 filas (0,8%), y casi todas son falsos positivos de las tablas de nombres.

## Qué es la 3.0.5

La 3.0.5 es una reescritura de estilo más que una revisión de calidad. El 79% de las diferencias son otra redacción de lo mismo, y en la cabeza de la lista de sustituciones más repetidas **no hay una sola corrección de sentido**: "Durante" a "Por" (144), "Después de" a "Tras" (113), "viaje" a "camino" (103), "tal vez" a "quizás" (88), "comienza" a "empieza" (76).

Además trae dos regresiones sistemáticas contra decisiones que el proyecto ya tomó:

- **Mayúsculas calcadas**: añade mayúscula interior a mitad de frase en **2.086 filas** y la quita en 275. Es justo el calco del titulado inglés que `mayusculas.py` caza y que la revisión editorial limpió; por ejemplo, `Near Death` es "Cerca de la Muerte" y `Gravely Wounded` es "Gravemente Herido".
- **Devuelve al inglés 423 cadenas** que enero sí traducía, entre ellas al menos 24 de los 39 guiños registrados en `GUINOS.md` (Sorrel, Ser Jaime, Barad' Dur).

Choca también con el glosario fijo (dice "trasgos" donde el pack dice "goblins", "Determinación" donde el pack dice "Resolución") y con la política de registro (introduce tres casos de voseo). En total, **3.059 de las diferencias caen encima de una decisión ya registrada**, y como una misma fila puede chocar con más de una, el reparto por decisiones suma más: 2.086 de mayúsculas, 603 del censo a ciegas de las tablas de nombres (`CENSO_CIEGO.tsv`), 516 de glosario, 55 de registro, 27 de guiños y 20 de internos adjudicados.

Aparte de lo editorial, hay un detalle incompatible con Rosetta: la 3.0.5 da cinco traducciones distintas a `[/color] Resolve` y seis a `[/color] Melee Skill`, y en el modelo del framework cada `en` tiene un solo par.

## Cuánto vale lo que queda

Descontando todo lo anterior quedan 4.946 filas a juzgar. Se sacó una muestra aleatoria de 220 con semilla fija y se juzgó una a una con el inglés delante (IC 95% es el intervalo de confianza del 95%):

| veredicto | de 220 | tasa | IC 95% | extrapolado |
|---|---|---|---|---|
| mejora estricta | 15 | 6,8% | 3,5%–10,1% | 172–501 |
| regresión estricta | 21 | 9,5% | 5,7%–13,4% | 280–664 |
| preferencia de estilo | 184 | 83,6% | | ~4.100 |

Las mejoras son reales (contrasentidos, falsos amigos, concordancias), y las regresiones también, del mismo calibre y en la misma proporción: la 3.0.5 escribe "escrituras inescrutadas", "un maestro arquero" donde el inglés dice *bowyer* (que fabrica arcos, no los dispara), "los chuches" por *the mutts*, e **inventa frases enteras** que el inglés no tiene. Un detector simétrico de erratas confirma el empate: la 3.0.5 corrige 70 erratas de enero e introduce 53 propias, y de esas 70 nuestro corpus solo arrastraba 10, porque el barrido semántico del proyecto ya había arreglado las otras 60 por su cuenta.

Las 2.083 cadenas sin par tampoco destapan lagunas de cobertura: solo 41 son candidatas limpias, y ninguna aporta nada (ordinales, formatos de millar, logs de depuración que la 3.0.5 traduce por error).

## La decisión

**No hay campaña de absorción.** Con un 6,8% de mejora contra un 9,5% de regresión, y sin ninguna señal automática que las separe, absorber exigiría juzgar 4.946 pares a mano para recuperar unos 340 y evitar unos 470. Sale peor que no hacer nada, y bastante peor que dedicar el mismo esfuerzo a los instrumentos que el proyecto ya tiene (`align_score.py`, `nouns_cross.py`, `erratas.py`), que buscan defectos sin traer el estilo de otro traductor.

Hay además un argumento de identidad: el pack tiene una política escrita (registro neutro, glosario fijo, sin mayúsculas calcadas, guiños conservados, germanismos conservados) y la 3.0.5 contradice las cinco. Absorberla a trozos devolvería al texto la mezcla de dos manos que la revisión editorial quitó.

**Sí se hizo la cosecha dirigida**, el mismo día: 21 filas con evidencia escrita, ninguna de las cuales toca una decisión registrada. Son doce restos del vosotros peninsular, que violan la política de registro neutro (no son cuestión de preferencia), y nueve defectos verificados con el inglés delante, entre ellos "escudo calefactor" por *heater shield*, "Esto está tomando demasiado" por *This shouldn't take long* (que decía lo contrario) y "deje al perro en el suelo" por *put the dog down* en un evento que va de sacrificarlo. El chequeo `REGISTRO` de `checks.py` no detectaba el vosotros, y por eso esos doce seguían ahí desde la normalización; ahora lo detecta.

**Queda anotado para después de la 1.0**, por si alguna vez se quiere volver sobre ello: usar la 3.0.5 como señal de dónde mirar, sin tomar sus valores, y solo en las ~650 filas de reescritura mayor (razón de similitud por debajo de 0,60), que es donde se esconden los contrasentidos. Serían unas 45 correcciones por 650 juicios humanos, una relación pobre pero acotada y repartible en tandas.

## Los instrumentos

El análisis se hizo el 31/08 con scripts de un solo uso que no se versionan; lo que importa de ellos está en este fichero. Para rehacerlo, el método es el de `es_pack/tools/gt_align.py` apuntando a los dos árboles en vez de a uno.
