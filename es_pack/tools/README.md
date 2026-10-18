# Inventario de herramientas

Esta guía explica para qué sirve cada herramienta de `es_pack/tools/` y cuándo se usa. Cómo editar la traducción está en [CONTRIBUTING.md](../../CONTRIBUTING.md).

Todo se ejecuta desde la raíz del repositorio y con `uv`:

```bash
PYTHONUTF8=1 uv run python es_pack/tools/<herramienta>.py
```

`PYTHONUTF8=1` es obligatorio. El corpus lleva acentos, eñes y comillas tipográficas, y sin esa variable Windows lo lee con la codificación de la consola y las herramientas fallan o, peor, corrompen texto al escribir.

Ninguna necesita red, claves de API ni el juego instalado, con las excepciones señaladas abajo: `check_ui_drift.py`, `gt_align.py`, `ids_census.py` y `measure_coverage.py` leen el juego o sus árboles descompilados, y `check_msu_drift.py` lee el zip de MSU instalado (o el que se le pase). Ninguna modifica el corpus: las que escriben lo hacen en `es_pack/build/`, que no va al repositorio.

## Construir lo que se distribuye

| Herramienta | Para qué |
|---|---|
| `build_dist.py` | Genera desde el corpus el pack de pares (cada par es una cadena inglesa y su traducción, literal o con variables). Es la herramienta principal. |
| `build_ui_addon.py` | Genera el addon de interfaz, la capa JS: las pantallas que el juego dibuja en JavaScript, que no pasan por Rosetta. |
| `update_readme_metrics.py` | Regenera el cuadro de métricas del README de portada desde el corpus real. Con `--check` no escribe y devuelve 1 si está desactualizado; es lo que ejecuta la CI. |

**`build_dist.py`** lee `corpus/base_es.nut` y escribe `build/mod_battle_brothers_es_<versión>.zip`. Clasifica cada par en tres cubos: `dist` va al pack; `wip` va a cuarentena en `build/patterns_wip.nut` porque su placeholder (el marcador `<nombre:tipo>` de una variable) no cumple la sintaxis que el runtime exige; y `drop` son los que están sin traducir. Al final comprueba la sintaxis del pack generado y lanza los avisos de calidad. Es lo que hay que pasar después de tocar el corpus.

La cuarentena existe porque un par mal formado abortaría la carga completa de la traducción en la partida de quien lo instale.

### La línea de salida de `build_dist.py`, cifra a cifra

Las cifras cumplen `total = dist + wip + drop`; las demás cuentan poblaciones aparte, que no entran en esa suma. Sirve de ejemplo el build de la 1.0.0:

- **`dups omitidos` (402)**: bloques del corpus cuyo `en` repite el de un bloque anterior; el cargador se queda con el primero y descarta el resto ANTES de contar. Por eso no están en `total`: los bloques físicos del fichero son `total + dups` (16.501). Casi todos son legítimos: la misma cadena compuesta extraída de dos ficheros distintos, cada bloque con el comentario de código que ancla su fichero para la regeneración con `-r`.
- **`internos adjudicados` (765)**: las líneas `// en = "..."` del corpus, la forma de marcar algo como "visto y descartado a propósito" (claves internas que jamás se muestran, adjudicadas en `corpus/VACIOS.md`). No son bloques y no computan en ningún cubo; se cuentan aparte para vigilar que nadie las convierta en bloques por accidente, ni al revés.
- **`total` (16.099)**: bloques únicos que el cargador entrega a la clasificación. Es la suma exacta de los tres cubos.
- **`dist` (16.099)**: lo que se distribuye, literales sanos y patrones bien tipados, emitidos al `base_es.nut` del zip.
- **`wip` (0)**: la cuarentena, pares con pinta de patrón cuyo placeholder no cumple la sintaxis `<nombre:tipo>` del runtime. Van a `build/patterns_wip.nut`, que nunca se instala.
- **`drop` (0)**: deuda de traducción real, bloques con `es` vacío. Desde la adjudicación del 27-28/08 este cubo está a cero y funciona como detector: tras un bump del juego, las cadenas nuevas caen aquí.
- **`ids` (28)**: los pares por id de `corpus/ids_es.nut`, un fichero aparte que viaja al zip tal cual (los homógrafos de `m.Name`, Rosetta >= 0.5.0). No pasan por la clasificación ni suman en `total`.
- **`sintaxis`**: compila con `sq.exe` los artefactos del build (pares, ids y preloads). Por sí sola avisa a gritos pero no rompe el build; con `--estricto`, que es como lo lanza la CI, un fallo de sintaxis sí lo rompe.
- **`avisos de calidad`**: los chequeos de `checks.py` sobre los pares (línea base `DUP_VECINO 18, TILDES 2, TOKENS 1, VARIANTES 19, REGISTRO 0, CONTROL 0, ANCHO 0, HABLA 0`). La disciplina es que no suban, y cada uno está documentado en su chequeo. `CONTROL` y `REGISTRO` deben estar siempre a cero, y los dos aprendieron algo el 31/08 y el 01/09. `CONTROL` es nuevo: cualquier carácter invisible dentro de una traducción es corrupción, y el primero que apareció eran dos tabuladores verticales que además partían la línea en dos para `splitlines()`, con lo que los barridos escritos con esa función dejaban de ver el par sin avisar. `REGISTRO` ya existía, pero solo miraba voseo y jerga, y su propia nota daba por eliminado el vosotros cuando quedaban doce vivos. Ahora los caza por tres vías, con el infinitivo del propio corpus como diccionario para no confundir "ciudad" con un imperativo. `DUP_VECINO` subió de 14 a 18 el 31/08 al añadir las doce reglas recursivas de la cláusula de pago de la negociación: cada una repite el aviso que ya daba su par literal (tres redacciones inglesas de "per head you bring back / arrive with / return with" con la misma traducción), de modo que la subida cuenta dos veces el mismo aviso.

**`build_ui_addon.py`** empaqueta los `.js` de `src/ui/` en `build/mod_battle_brothers_es_ui_<versión>.zip`. El zip lleva solo `ui/` y sale igual byte a byte en cualquier máquina. Dos ficheros de la traducción original quedan fuera a propósito, con el motivo escrito en `EXCLUIDOS`, y un test falla si reaparecen.

## Comprobar antes de publicar

| Herramienta | Para qué |
|---|---|
| `test_build_dist.py` | La suite de tests de todo esto. Se lanza con pytest (comando debajo de esta tabla). |
| `checks.py` | Avisos de calidad del corpus. Ya va cableado dentro de `build_dist.py`. |
| `check_syntax.py` | Compila el pack generado con un intérprete de Squirrel, si hay uno. |
| `check_ui_drift.py` | Avisa de si una actualización del juego ha dejado obsoleta la capa JS. |
| `check_upstream_drift.py` | Avisa de si una versión nueva de Rosetta afecta a lo que el pack replica. |
| `check_msu_drift.py` | Avisa de si una versión nueva de MSU deja en inglés algo de lo que el pack traduce de ella. |

```bash
PYTHONUTF8=1 uv run pytest -q
```

**`checks.py`** se puede lanzar suelto para ver solo los avisos, sin reconstruir el pack. Cada familia corresponde a una clase de fallo que ya apareció de verdad: `IMG` (imagen de evento que no cuadra entre idiomas), `DUP_VECINO` y `DUP_ES` (una entrada con la traducción de otra, la firma del corrimiento), `TOKENS` (marcadores `%x%` deformados o ausentes), `VARIANTES` y `RECORTE` (bloques `{a|b}` desparejados, y ramas resumidas en una), `PUNTUACION` (interrogación o exclamación sin su signo de apertura), `TILDES`, `REGISTRO` (vosotros o voseo, que están fuera de política), `NFD` (acentos descompuestos, que se ven bien y no coinciden al comparar) , `ANCHO` (botones de ambición y descripciones de origen que no caben en su recuadro, medidos con la anchura real de la fuente del juego) y `HABLA` (una rama del español que deja un `%SPEECH_ON%` sin cerrar, que en pantalla sale como `[color]` suelto).

Ningún aviso bloquea el build, porque en cada familia hay casos legítimos; lo que se pide es que tu cambio no suba la cuenta.

**`check_ui_drift.py`** necesita el juego instalado, porque compara contra sus ficheros:

```bash
PYTHONUTF8=1 uv run python es_pack/tools/check_ui_drift.py "<ruta>/Battle Brothers/data"
```

Hay que pasarlo **después de cada actualización del juego**, porque el corpus y la capa JS fallan de formas distintas. Los pares son una dependencia blanda, y lo que no esté traducido sale en inglés sin romper nada; los `.js`, en cambio, sustituyen ficheros del juego, así que una actualización que toque uno de esos módulos queda tapada por nuestra copia sin error y sin aviso. Devuelve 1 si hay algo sin juzgar, de modo que sirve de puerta antes de publicar. Los avisos ya revisados van en `ACEPTADOS`, con las cuentas fijadas para que reaparezcan si el juego vuelve a mover ese fichero.

Si no le pasas ruta, la busca en `DATA_DIR` del `.env`.

**`check_upstream_drift.py`** es el equivalente para el otro lado de la dependencia: upstream, el repositorio original de Rosetta, de Suor. Además de usar Rosetta, el pack duplica dos piezas suyas: `build_dist.py` decide qué par se distribuye reimplementando el contrato de `validateRule`, y lleva copiado a mano el conjunto de tipos de sub (los `tipo` admitidos en `<nombre:tipo>`) que el runtime acepta. Si upstream añade un tipo, el build manda a cuarentena pares válidos sin decir nada; si retira uno, distribuiríamos pares que el runtime rechaza al cargar, y eso aborta la traducción entera en la partida de quien lo instale.

Sin argumentos revisa la copia vendorizada de `vendor/rosetta/`. Para juzgar una versión nueva antes de adoptarla, se le pasa su runtime, o se trae el repo de Suor como remoto:

```bash
PYTHONUTF8=1 uv run python es_pack/tools/check_upstream_drift.py <ruta>/scripts/!mods_preload/!rosetta.nut
# o bien
git remote add suor https://github.com/Suor/battle-brothers-rosetta.git
git fetch suor
PYTHONUTF8=1 uv run python es_pack/tools/check_upstream_drift.py --ref suor/master
```

Vigila solo esas piezas, porque avisar de cualquier cambio de upstream sería ruido en cada commit. Los tipos de sub los deriva del runtime y los compara con nuestra copia, así que ahí no hay nada que fijar a mano. Lo que no se puede derivar, porque es lógica reimplementada, va con el hash del cuerpo de la función fijado en `PINES`: un hash distinto pide volver a leer la función, sin que eso indique que algo esté roto. Lo que se decida se anota junto al pin, en el commit que adopta la versión.

**`check_msu_drift.py`** hace lo mismo con MSU, que el pack traduce sin sustituir ninguno de sus ficheros: sus textos de Squirrel van por Rosetta, y los de su JS los cambia `src/ui/mods/mod_battle_brothers_es/msu_es.js` envolviendo métodos suyos. Comprueba dos cosas: que siguen existiendo las piezas que ese JS y la ficha del preload tocan, y que cada texto de MSU tiene par en el corpus. Un fallo en cualquiera de las dos deja texto en inglés, sin romper nada. Sin argumento lee el `mod_msu.zip` instalado; también acepta otro zip o una carpeta.

Los dos los pasa cada lunes `.github/workflows/vigilancia.yml` contra la última release de MSU y la etiqueta más alta de Rosetta. El mismo trabajo compara además la última versión pública del juego en GOG con `GAME_VERSION`. Si algo cambia, abre una issue.

## Medir cobertura: qué literal no cubre ningún par

Medir cobertura es buscar ausencias: literales del juego que ningún par captura, ni bien ni mal. Se confunde con facilidad con el corrimiento de la [sección siguiente](#auditar-el-corpus-buscando-defectos), que mira pares que existen y capturan bien pero cuyo valor español pertenece a otra entrada.

| Herramienta | Para qué |
|---|---|
| `measure_coverage.py` | Cuántos literales del árbol del juego no cubre ningún par del corpus, y de qué familia son. |
| `sq_probe_coverage.nut` | La sonda de Squirrel que `measure_coverage.py` invoca: ejecuta `::Rosetta.translate()` de verdad sobre cada literal. |
| `ids_census.py` | Censo de homógrafos de `m.Name` (una misma palabra inglesa que pide traducciones distintas según el objeto) para los pares por id de `corpus/ids_es.nut` (Rosetta >= 0.5.0). Necesita los dos árboles de comparación, como `gt_align.py`. |
| `sq_stdlib_load.nut` | El `load.nut` que `test.nut` espera y el zip instalable de stdlib no trae: copiado junto al stdlib descomprimido, la batería completa de upstream corre en local. Instrucciones en su cabecera. |

**`measure_coverage.py`** no compara cadenas contra el corpus. Eso ya se probó dos veces y dio cifras inservibles por los falsos positivos que genera la generalización de los patrones (un par tipado cubre decenas de literales concretos distintos). En su lugar arranca Squirrel de verdad, carga el runtime y el pack construido, y pasa cada literal extraído por el emparejador real. Para los literales de patrón (plantillas sin tipar que salen de una concatenación y que nunca existirán tal cual como string en el juego) usa `_iterKeys()`, la pieza real con la que `translate()` decide qué reglas probar, en vez de fingir un valor. El porqué completo, con los casos reales que lo motivan, está en su docstring.

```bash
PYTHONUTF8=1 uv run python es_pack/tools/measure_coverage.py [ruta_scripts]
```

Como `check_ui_drift.py` y `gt_align.py`, necesita recursos que no están en cualquier máquina: el árbol descompilado del juego, `stdlib.zip` descomprimido (`STDLIB_DIR`) y un intérprete Squirrel. Sin argumento busca el árbol en `SCRIPTS_DIR` del `.env` o en la ruta conocida del árbol de herramientas del juego. Escribe en `es_pack/build/` la extracción cruda, los huecos con fichero y familia, los candidatos de patrón sin confirmar del todo y un resumen agregado, sin tocar el corpus ni el pack.

## Auditar el corpus buscando defectos

Estas herramientas no arreglan nada: producen listas de sospechosos para revisar a mano. Sirven para el defecto más frecuente del proyecto, por delante de la mala traducción: el corrimiento, una traducción correcta puesta en el sitio de otra porque el juego añadió o quitó una entrada de una lista y todo lo que iba detrás se corrió una posición.

| Herramienta | Señal que busca |
|---|---|
| `shift_detect.py` | Ventanas de corrimiento: tramos donde el español va desplazado. |
| `shift_window.py` | Amplía cada hit hasta sus fronteras reales, cruzando las entradas ciegas. |
| `align_score.py` | Pares improbables, juzgando cada uno por sí mismo. |
| `nouns_cross.py` | Tablas de nombres cruzadas, mirando el sustantivo de tipo. |
| `ramas_perdidas.py` | Ramas de diálogo que el español perdió. Hoy es un test de regresión. |
| `gt_align.py` | Desplazamientos, comparando con el árbol de la traducción de referencia. |
| `erratas.py` | Erratas de dedo, usando el corpus como su propio diccionario. |
| `mayusculas.py` | Mayúsculas interiores calcadas del titulado inglés. |
| `cobertura.py` | Los tres barridos del lado Squirrel: universo, conductos y composiciones. |
| `cobertura_datos.py` | El texto de interfaz que el juego compone fuera de `ui/screens/`. |
| `cobertura_js.py` | El barrido de la capa JS: rótulos del juego que el addon deja en inglés. |
| `cnut_strings.py` | Saca los literales de un `.cnut` del juego, para cuando no hay fuente. |
| `blind_census.py` | Prepara por lotes el censo a ciegas: los pares que `shift_detect.py` no puede juzgar por falta de apoyo léxico, agrupados en ventanas con contexto. |
| `coherencia_guinos.py` | Comprueba que ningún par cite por su nombre inglés un guiño que en otro sitio se sustituyó (ver `corpus/GUINOS.md`). |

**`erratas.py` y `mayusculas.py`** van juntas porque comparten el mismo truco: el corpus es su propio diccionario. Son miles de pares y más de un millón de caracteres de castellano, así que una palabra correcta aparece muchas veces y una errata aparece una sola. `erratas.py` busca la palabra rara que se parece a una frecuente, con las dos operaciones que hace un dedo y no hace la morfología (intercambiar letras contiguas, colar una de más), más una clase aparte para la misma palabra con y sin tilde. Así salieron "suficietnes", "siemrpe", "hueargo" y "cosas como aqui", que ningún barrido anterior veía porque todos miraban clases concretas y no el léxico. `mayusculas.py` busca la palabra que aparece muchas veces en minúscula y una vez en mayúscula a mitad de frase, que es un calco del titulado inglés ("Guerreros Orcos", "Danzarines de Cuchillas"); un nombre propio de verdad no se acusa nunca porque nunca aparece en minúscula. Además separa los rótulos de la prosa, que no se juzgan igual.

**`cobertura.py` y `cobertura_js.py`** responden a por qué seguían apareciendo textos en inglés después de tantas revisiones. Había tres clases de hueco, cada una visible de forma distinta: el hueco de universo (una cadena que ninguna partida ha pedido nunca, invisible en todas partes), el conducto (una ventana entera que no pasa por Rosetta, invisible en el log porque nadie pregunta) y la composición (piezas cubiertas al cien por cien que al juntarse no casan ningún par). El docstring de `cobertura.py` lo cuenta entero. `cobertura_js.py` mira la capa JS, que Rosetta no puede tocar y que solo se traduce sustituyendo el fichero.

**`cobertura_datos.py`** tapa el punto ciego que dejaban las dos anteriores. La clase de conductos de `cobertura.py` mira `scripts/ui/screens/`, que es donde uno espera los rótulos, pero el juego también compone tablas de interfaz desde la lógica: `skill.getHitFactors()` arma las filas de por qué aciertas más o menos, `party.getTooltip()` la ficha de una partida del mapa, `tactical_state` el tooltip de una casilla en llamas. Nada de eso está en `ui/screens/`, así que el barrido anterior no lo veía, y por ahí se colaron "Surrounded", "Armed with shield" y "Distance of 2", que tenían su par en el corpus desde el primer día. Recorre el árbol entero buscando funciones que asignen texto de usuario a una clave de interfaz y las cruza con los hooks del pack y del runtime; lo que queda sin cruzar es candidato. Trae una lista explícita de lo que está **cubierto por diseño** (el texto de contrato y de evento viaja por `buildTextFromTemplate`, los `getTooltip` los recoge `onQuery*TooltipData`), cada línea con su porqué, para que el informe no liste funciones que ya están cubiertas.

**`shift_detect.py`** prueba la hipótesis del desplazamiento de forma directa: señala tramos que van corridos, mientras que `align_score.py` señala pares raros uno a uno. Para cada entrada y cada desplazamiento compara la puntuación del alineamiento actual con la del desplazado, y saca los sitios donde el desplazado gana con claridad.

```bash
PYTHONUTF8=1 uv run python es_pack/tools/shift_detect.py [margen] [--fichero X]
```

Solo cuentan los enlaces de palabras atestiguados en dos pares o más, para que un par no pueda avalar su propio alineamiento, porque el modelo se entrena con el corpus, corrimientos incluidos. Ese es también su límite, y está escrito en el docstring junto con las dos clases de falso positivo conocidas. Tarda unos tres minutos, lo que cuesta entrenar el modelo.

**`shift_window.py`** responde a la pregunta que un hit deja abierta: dónde empieza y dónde acaba el corrimiento. Toma cada hit como semilla y crece hacia arriba y hacia abajo, cruzando las entradas sin señal léxica (que es por donde un corrimiento se esconde), hasta encontrar evidencia positiva de que el vecino está bien alineado. Sin escribir en el corpus, informa del núcleo confirmado con su reparación propuesta, de las extensiones inciertas que le tocan al censo humano, de las huérfanas y de los sobrantes. Con `--semilla fichero:indice:k` se siembra desde un veredicto del censo, de modo que los hits del detector y los del censo acaban en la misma herramienta.

```bash
PYTHONUTF8=1 uv run python es_pack/tools/shift_window.py --semilla character.nut:25:1
```

**`align_score.py`** entrena un modelo léxico de traducción ([IBM Model 1](https://en.wikipedia.org/wiki/IBM_alignment_models#Model_1)) con los propios pares del corpus. Como la mayoría son correctos, el modelo aprende las correspondencias reales, y los pares que quedan en la cola de improbabilidad son los candidatos. Escribe `build/align_report.tsv` con todo ordenado de peor a mejor.

```bash
PYTHONUTF8=1 uv run python es_pack/tools/align_score.py [n_sospechosos]   # por defecto 40
```

**`nouns_cross.py`** cubre el hueco que el método anterior no ve: entre sinónimos la similitud sale alta y el error pasa. En lugar de la semántica mira el sustantivo de tipo, así que caza un `Grotto` traducido como `Guarida`, que es `Den`, por parecido que sea el resto.

**`ramas_perdidas.py`** era la cola de trabajo de la tarea de ramas de diálogo, ya cerrada. Ahora sirve de regresión: si vuelve a listar algo, es que se ha perdido una rama otra vez.

**`gt_align.py`** es la única que un colaborador externo no puede pasar: las rutas a los dos árboles que compara están fijas en el fichero, en las constantes `EN` y `FAN`, y apuntan al disco del mantenedor. Alinea los literales del árbol inglés con los del árbol de la traducción de referencia y busca la firma del corrimiento, que es que nuestro valor para una entrada sea exactamente el que la referencia da a otra entrada del mismo fichero. Así se encontró que los Lindwurms se llamaban "Trols".

## Histórico, no usar

Se conservan como explicación de decisiones del corpus y ya no se ejecutan.

| Herramienta | Estado |
|---|---|
| `extract_wrapper.py` | Obsoleta desde el 18/08/2026. Upstream arregló el bug que la obligaba. |
| `quote_fix.py` | Obsoleta desde el 18/08/2026, por lo mismo. |
| `relleno_305.py` | De un solo uso, ya gastado: rellenó los pares con `es` vacío desde la revisión 3.0.5 de la traducción original, sin pisar ningún par curado (ver `corpus/FUENTE-305.md`). |
| `normalize_seed.py` | De un solo uso, ya gastado: convirtió el corpus del compilador antiguo al formato que el parser de upstream lee. |

## Ficheros de apoyo

`rutas.py` reúne las rutas de la máquina (el juego instalado y las herramientas de descompilado), que cada herramienta lee del `.env` de la raíz; ver `.env.example`.

Cinco guiones de Squirrel para interrogar al runtime real desde el repositorio, sin arrancar el juego. `sq_bootstrap.nut` monta los pocos globales que stdlib y Rosetta tocan al cargarse, y es lo que permite ejecutar los otros tres; lleva además un shim de `assert` de dos argumentos (sintaxis de Squirrel 3.2 que el `!rosetta.nut` usa en `matchParts`), porque el `sq.exe` 3.0.7 de las herramientas del juego solo admite uno y revienta en cuanto una regla dispara ese camino. `sq_probe.nut` comprueba que los nombres que el juego compone en marcha, como los de objeto legendario, no se traduzcan a trozos con los pares de las piezas. `sq_probe_ids.nut` comprueba si los pares por `id` resuelven los homógrafos; el caso real es "Dagger", que es a la vez el tipo de arma y una entrada de la lista de nombres legendarios. `sq_probe_coverage.nut` es la sonda de `measure_coverage.py`, descrita arriba. `sq_probe_flags.nut` comprueba cómo interpreta el runtime cada variante de la marca `:t` (`<part:t>`, `<part:t_raw>`…) y qué efecto tiene en una regla real.

Son el precedente que hace viable medir la cobertura de verdad, ejecutando el emparejador de Rosetta sobre la lista de literales en vez de comparar cadenas, el método que ya dio dos cifras inservibles. La historia está en [KNOWN_ISSUES.md](../corpus/KNOWN_ISSUES.md).

## Si añades una herramienta

Lo que se espera, a la vista de las que hay: un docstring que empiece por el problema que resuelve y no por lo que hace, la línea de `Uso:` con el comando completo, rutas derivadas de `Path(__file__).resolve().parents[2]` y nunca absolutas, y escribir solo en `es_pack/build/`. Si la herramienta puede dar un falso positivo, decirlo en el docstring, para que quien lea un aviso sepa cuándo puede descartarlo.

Los tests van en `test_build_dist.py`, que a pesar de su nombre es el único módulo de tests del pack.
