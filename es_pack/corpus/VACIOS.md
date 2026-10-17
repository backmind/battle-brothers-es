# Los pares con es vacío: adjudicación completa (27/08/2026)

El corpus arrastraba desde el armado original (la primera construcción del corpus a partir de la traducción comunitaria) 1.723 pares con `es = ""`, que `build_dist.py` cuenta como `drop` y el informe de cobertura como "deuda de traducción". El 27/08 se adjudicaron todos, con el propietario en sesión: cuáles son nombres propios (convención `es = en`), cuáles claves internas que el juego jamás muestra y cuáles texto visible de verdad, que se tradujeron. Este fichero registra esa adjudicación para que ninguna auditoría futura la rehaga.

## Los dos estados, y por qué se distinguen en el propio corpus

La representación la fijó una objeción del propietario (28/08): la idea de que "un es vacío es deliberado" no se sostiene tras un bump (una subida de versión del juego base), porque la regeneración del corpus traerá cadenas nuevas con `es` vacío que son deuda real y no descartes. Por eso los dos estados se codifican de forma distinta, con la propia convención de upstream (el Rosetta original de Suor):

- **Interno adjudicado** = línea `// en = "..."` sin bloque (la forma "visto y descartado" de `load_ref`): sobrevive a una regeneración con `-r` (la opción de `rosetta.py` que reextrae respetando una traducción de referencia), el chequeo `-c` no lo cuenta como NEW, y no computa en ningún cubo (las categorías en que `build_dist.py` reparte los pares). Son 765 a día de hoy: los 722 de la adjudicación, más 53 del residuo y 13 de la criba del 28/08 (abajo), menos los 23 que la QA del 31/08 devolvió a par activo ([abajo](#el-barrido-que-cierra-la-clase-de-los-homógrafos-31082026)). Son logs con marcador `::`, URLs de tienda, descriptores `tacticalentity(...)`, rutas de imagen, ids de pantalla compuestos y residuos del extractor. `build_dist.py` los cuenta aparte ("internos adjudicados").
- **Vacío pendiente** = bloque con `es = ""`: deuda de traducción real, que es lo único que mide el cubo `drop` desde esta fecha. Tras un bump, las cadenas nuevas caen aquí y no se confunden con lo descartado.

Tras la conversión el cubo pendiente quedó en 44, y **el 28/08 se vació del todo** (drop 0). La criba, hecha uno a uno con el árbol del juego delante, dio esto:

- **13 más resultaron internos** y pasaron a `// en`: los "is unconscious."/"has died." con punto (son `logDebug`; el "has died" visible, sin punto, ya tenía gemelo tipado, es decir, un patrón con variables `<nombre:tipo>` que lo cubre), los ids de pantalla del mercado negro ("Brain", "Bunk", "Heart", "Gland"), el discriminador "win"/"loose" del resultado táctico, dos tooltips ("+15% chance to hit the head", "100% chance to stun") con gemelo tipado idéntico en dist (los pares que se distribuyen), el título del evento de acceso anticipado (una regla `The <x>` sería letalmente golosa), el fragmento de dificultad del menú de carga (sin conducto, es decir, su texto no pasa por Rosetta; el arreglo sería un hook) y una etiqueta de ambición "(n/8)" cubierta por el patrón gemelo.
- **31 eran deuda real y quedaron tipados y traducidos**: nueve líneas del log de combate ("vuelve a empuñar su arma", "trasciende la muerte", "se enfurece", golpes a escudo y armadura natural, las resistencias por "fisiología antinatural", "pierde la concentración", "queda aturdido por el Abrazo del Dorador"), cinco tooltips con valor vivo (flechas restantes, probabilidades, el efecto Sangrando de la poción de hiena, el "-50%" del ataque debilitante), la descripción del perk Duelista (era el resto de cuarentena visible), cinco patrones de progreso de ambición ("<text:t> (n/8..25)"), la recompensa del Juramento de fortificación, la variante "por cabeza que llegue" de la negociación, y las composiciones de nombre: "Héroe caído descabezado" (`:t`, la marca que pide traducir también la pieza capturada), `Wiederganger <name>`, `Escudo de <name>`, `<name> (liberado)` (sin `:t` a propósito: la pieza llega ya traducida), `(x<n>)` del efecto Abrumado (`:t`) y el título nobiliario `von <name>` (identidad).
- **Conducto nuevo, caso 18 del preload** (los hooks de `mod_battle_brothers_es_hooks.nut` van numerados por casos): el texto de ambición de la barra superior iba de `ambition_manager` a JS sin pasar por Rosetta, así que no se veían ni los literales con par ni las variantes con progreso. El hook traduce en la frontera y los cinco patrones hacen el resto.

Nota de línea base: "dups omitidos" sube de 379 a 380 porque el tipado del `assault_skill` produce el mismo `en` y el mismo `es` que un patrón ya existente de otra fuente. Se conservan los dos bloques porque cada comentario de código ancla su fichero para la regeneración con `-r`.

## La política de nombres propios, confirmada por el propietario

Topónimos y nombres de pila llevan `es = en` a propósito. El sabor original es intencional y, sobre todo, **los rótulos del mapa los dibuja el motor y no son interceptables**, así que un exónimo (la forma castellana de un nombre extranjero) dejaría el mapa y los textos en desacuerdo para siempre. Lo que sí se traduce, en una tanda curada, son los apodos con significado (el Tuerto, la Comadreja), práctica que ya existía. El paréntesis aclaratorio ("Bosque Oscuro (Dunkelwald)") se evaluó y se descartó porque revienta los widgets cortos ya documentados y rompe el casado de las piezas que capturan los patrones.

## El barrido es = en (984 pares, de drop a dist)

| ámbito | pares | qué son |
|---|---|---|
| `config/character_names.nut` | 231 | nombres de pila y patronímicos ("Ingrid", "Ibn Tayib") |
| `config/world_location_names.nut` | 84 | topónimos goblin/orcos ("Blukat Gash", "Shex Shex Shex") |
| `entity/world/settlements/*` (mayúscula inicial) | 668 | pools de nombres de pueblo por tipo ("Aalbek", "Sommerstad") |
| `locations/goblin_city_location.nut` | 1 | "Rul'gazhix" |

Esto cubre, entre otros, los ~44 topónimos que los logs de QA veían como NOT FOUND (la línea del log de Rosetta para una cadena sin par). Las ~11 entradas en minúscula de los mismos ficheros de settlements ("shop", "shipname", "fish", "wood") son claves internas y quedaron como internos adjudicados (`// en`).

## Lote eventos y contratos (522 filas): 518 internas, 4 visibles

Se auditó con el árbol del juego delante. Esta es la taxonomía, con el mecanismo de cada clase:

| clase | filas | mecanismo (evidencia) |
|---|---|---|
| clave de plantilla (`bro`, `amount`, `prizename`) | 324 | primer elemento de `vars.push([clave, valor])`; `buildTextFromTemplate` la usa para localizar `%clave%`, nunca se imprime (`event.nut:320-383`, `contract.nut:519-603`) |
| id de pantalla o estado (`A`, `B1`, `Task`, `Running`, `Success`) | 175 | `ID =` en `m.Screens`/`m.States`, referenciado por `setScreen`/`getScreen`/`setState`/`return` (`event.nut:47-53,108-116`, `contract.nut:285-322`) |
| CombatID (`Arena`, `Duel`, `Vampires`...) | 9 | `p.CombatID = "X"` y comparación en `onCombatFinished` |
| id de logro de Steam (`Kingmaker`, `Savior`...) | 5 | `updateAchievement("<APIName>", ...)`; el nombre visible lo sirve Steam localizado |
| fragmento de ruta de script (`falchion`, `warbrand`) | 3 | se concatena en `this.new("scripts/items/weapons/" + x)`; el nombre visible lo pone el item |
| capa de sprite, propiedad de casilla, clave de Flags | 3 | `getSprite("selection")`, `Properties.set("Corpse")`, `Flags.set("Bribe1")` |

Los ids internos son seguros aunque el corpus tenga pares con el mismo `en` ("Success", "Noble"): `setScreen`/`Flags.get` no pasan por ningún hook.

Las 4 visibles, traducidas el 27/08:

- `find_artifact_contract` "General" → "General" (mote del némesis vía `%nemesisS%`; sus siete hermanos ya estaban traducidos).
- `hunting_alps_contract` "aufhockers" → "aufhockers" (segundo germanismo del mixto de bestias nocturnas decidido el 25/08; además el `toupper()` de Squirrel es ASCII y un valor con eñe saldría mal en `%enemyC%`).
- `adopt_wardog_event` "Battle Brother" → "Hermano de Batalla" (nombre del collar del perro adoptado y del perro en combate; el registro común "hermanos de batalla" ya existe en el corpus).
- `oathtaker_joins_event` "Hugo." → "Hugo." (botón de opción del acertijo; su hermano "Young Anselm." → "Joven Anselm." ya estaba, conservando el punto).

## Lote IA y estados (99 filas): 85 internas, 14 rescatadas

Este lote lo gobierna un hallazgo: **el extractor deduplica por `en`, así que el fichero de origen del par es donde vio la cadena primero, no donde se consume**. La sección `config/ai.nut` del corpus retiene en exclusiva literales que en realidad son nombres de habilidad visibles (el mismo literal sirve para el comportamiento de IA, que jamás se pinta, y para la habilidad, que sí). Por eso "nunca salió en NOT FOUND" es prueba débil para los homógrafos (cadenas inglesas idénticas con usos distintos): solo dice que esa superficie no se tocó en esas partidas.

Se rescataron 11 habilidades por par de id en `ids_es.nut` (Enganchar, Arengar, Vuelo oscuro, Grito de guerra, Cargar, Horror, Miasma, Encantar, Adormecer, Marchitar, Explotar; el literal suelto queda vacío a propósito, como Hex y Drag), y 3 rellenos de literal: "Conqueror" → "Conquistador" (pieza de AxeNames; la clave de noticia homónima no pasa por el traductor), "Patrol" → "Patrulla" (título del contrato de patrulla) y "Altar" → "Altar" (tooltip del altar bárbaro, por identidad).

Las internas, con su evidencia: los nombres de comportamiento táctico solo los lee `behavior.getName()`, consumido por cuatro `logInfo` tras banderas que siempre son false (`VerboseMode`/`BenchmarkMode`, sin setter en el árbol); los de mundo, por un `getName()` sin ningún llamante; las claves de órdenes ("Conqueror"/"Defeated"/"City" como claves de noticia, "Falling back" hacia un `setOrders()` vacío y una etiqueta con `Visible = false`).

**Claves de sistema que NO deben rellenarse jamás** (romperían lógica, renderizado o partidas guardadas): `progressbar` (discriminador de tooltip), `miasma`/`fire`/`smoke` (tipos de efecto de casilla comparados por igualdad), `autosave`/`quicksave` (nombres de fichero de guardado), `groupname`/`banner`/`difficulty`/`difficulty2`/`ironman` (claves de metadatos del save), `pickaxe`/`bludgeon`/`shortsword` (fragmentos de ruta de script del botín).

## Lote miscelánea (118 filas): 108 internas, 10 con destino propio

Rellenos directos: "tundra" → "tundra" (el hueco 13 de `TerrainShort`; sus doce hermanos ya estaban), "Ijirok" → "Ijirok" (materia prima; la línea visible del tooltip de notas del anatomista es compuesta, "Ijirok: Elixir of the Mad God", y pide pares literales propios que dependen del lote de pociones sin traducir), "Voulge" → "Voulge" (como Bardiche: la lista de astas conserva extranjerismos), y los tres nombres de perro que faltaban en `WardogNames`: "Snapper" → "Mordisco", "Catchaser" → "Cazagatos", "Quickpaw" → "Zarpa veloz".

Adjudicadas internas: etiquetas de audio "Music"/"Effects"/"Ambience" (array `ChannelName` sin consumidores; las visibles de Opciones viven en JS vanilla y ya las cubre el addon del pack), claves de plantilla de ambiciones (los `%placeholder%` deben quedarse en inglés), los siete escenarios de demo (solo `logDebug`; los títulos visibles los sirve el caso 3b), capas de sprite, colores de pelo (se concatenan en ids de brocha), ids de logro de Steam (el nombre localizado lo sirve la plataforma), y `%produce%` (variable preparada y jamás usada por ninguna plantilla del árbol; si un mod la usara, saldría en inglés, y el remedio sería el mismo hook de `onPrepareVariables` que se anota abajo).

## Hallazgos colaterales de la auditoría (27/08)

1. **Los tres patrones de perro van sin `:t` a propósito.** El auditor propuso añadirlo y el guardián del `:t` (la propiedad que anula la regla entera si la pieza capturada no tiene par) lo vetó: 17 de los 64 nombres de `WardogNames` son pares idénticos (Brock, Cujo, Varg, Skoll...) y el `:t` mata la regla también con "encontrado pero idéntico", así que 17 líneas enteras caerían al inglés a cambio de traducir 44 nombres. Son el segundo caso de uso del `:t_raw` del PR #11; el patrón del lobo, que además conservaba la expresión cruda del extractor en su lado `en`, quedó reparado a la forma de sus hermanos.
2. **El escudo famoso de lindwurm arrastraba un espacio final de vanilla** (`named_lindwurm_shield.nut:43`) que dejaba inertes seis prefijos ya traducidos: reparado con el caso 17 del preload del pack (recorte en `createRandomName`). Los dos prefijos sin traducir quedaron resueltos en tanda ese mismo día: "Lindwurm's" → "Escama de lindwurm" y "Lizard's" → "Piel de lagarto", sintagmas autónomos como sus seis hermanos, porque aquí el prefijo es el nombre completo.
3. **Corrimiento en `OldWeaponPrefix` confirmado con la referencia delante** (un corrimiento es una lista cuyos valores quedaron desplazados respecto al inglés): la lista vieja no tenía "Curio" y el bootstrap corrió dos valores. Reparado en tanda el 27/08: Remnant → "de reliquia" y Keepsake → "de recuerdo" (de la referencia, con "el Recuerdo" adaptado a forma componible), Empire's → "del Imperio", Legion's → "de la Legión", y Curio → "de coleccionista" (acuñación nuestra, sin fuente, comentada en el corpus).
4. **`TerrainShort` y `getProduceAsString` comparten patología**: el valor de la variable se inyecta después de que el wrapper global traduzca la plantilla. Hoy solo "tundra" tiene consumidor real (resuelto por identidad); si aparecieran valores no idénticos, el remedio es un hook de `onPrepareVariables` en el contrato consumidor.

## El barrido que cierra la clase de los homógrafos (31/08/2026)

La QA en partida de la quinta pasada trajo un caso que la adjudicación del 27/08 había dado por interno y no lo era: el tooltip de un hermano decía "Trasfondo: Vagabond", con el nombre del trasfondo en inglés y su descripción en castellano justo debajo. El propietario avisó de que había visto seis y sospechaba que hubiera más.

La causa es la ya escrita arriba, aplicada a otra superficie: **el extractor deduplica por `en`**, y "Vagabond" aparece dos veces en el árbol, una como id de pantalla del evento `march_wear_and_tear` (interno de verdad) y otra como `m.Name` del trasfondo (visible). La adjudicación vio la primera, marcó la cadena como interna, y con ella se fue el uso visible. Los 52 nombres de trasfondo que no colisionaban con ningún id de evento nunca tuvieron el problema.

En vez de reparar los seis, se barrió la clase entera: **todos los `m.Name`, `m.NameOnly` y `m.Title` del árbol del juego contra el corpus**, descartando `mapgen/` (nombres de plantilla táctica, internos por construcción). Quedan 45 cadenas sin par activo, y todas están adjudicadas:

| grupo | cuántas | veredicto |
|---|---|---|
| Nombres de trasfondo | 18 | **Mal adjudicados**: reparados con par literal en su sección |
| Nombres de rasgo | 5 | **Mal adjudicados** (Brave, Cocky, Superstitious, Survivor, Tiny): reparados igual |
| Habilidades de `skills/actives` y el efecto de maleficio | 15 | Ya rescatados por id en `ids_es.nut` desde el 27/08 |
| `goblin_shaman_racial` "Shaman" | 1 | Interno correcto: `IsHidden = true` y descripción "TODO" |
| `arena_building` "Arena" | 1 | Identidad en castellano; un par no aportaría nada |
| `early_access_intro_event` y su gemelo sureño, "The" | 2 | Interno a propósito, ya razonado arriba |
| `last_stand_contract` "Defend", `siege_fortification_contract` "Siege", `zombie_knight` "Headless" | 3 | Falsos positivos del barrido: son el primer sumando de una concatenación (`"Defend " + origen`), y de la suma se encargan los patrones |

Los 23 mal adjudicados dejan de ser marcadores y pasan a bloque con `es`, porque un mismo texto no puede estar en los dos estados a la vez sin mentirle a la regeneración con `-r`. Por eso "internos adjudicados" baja de 788 a 765.

Dos de los rasgos reparados no admiten par literal, porque su cadena ya pertenece a otro uso visible: "Quick" es un prefijo de objeto famoso ("veloz") y "Strong" el descriptor de fuerza de partida ("fuerte"). Van por id, como "Old", y con su pieza de composición ("un Rápido", "un Fuerte") para el mensaje de rasgo ganado.

Los valores salen de la referencia 3.0.5, fichero a fichero, cotejados con lo que la propia sección del corpus ya decía en su descripción. En dos nombres el corpus se contradecía consigo mismo, y los decidió el propietario en sesión el mismo día, con el barrido completo detrás en los dos casos.

El de perros es **"Maestro de sabuesos"**, y el término se unificó. El corpus tenía seis formas distintas para el mismo `houndmaster` inglés: adiestrador, entrenador, domador y amo de perros, perrero, y maestro de sabuesos. Once apariciones pasaron a la forma única. No se tocaron las tres que no son ese hermano: el NPC rival del evento de peleas de perros, que en inglés es `%doghandler%`; las dos veces que el inglés varía a propósito ("the dog trainer", "I'm a dog handler at heart"); ni el apodo "el Maestro perrero", que viene de "the Kennelmaster" y es clase protegida por el censo.

El del minstrel es **"Juglar"**, y aquí la razón la da el propio juego: usa tres palabras distintas (minstrel, bard, troubadour) y el castellano tiene exactamente tres para ellas. El anuncio de la taberna ya las distinguía dentro de una sola frase ("el famoso juglar %randomname% {el Ave Cantora | el Bardo | ...}"). Quince apariciones pasaron a juglar, incluido el seguidor del séquito "The Minstrel", que se llamaba "El Bardo" mientras su propia descripción, dos líneas más abajo, ya decía "El juglar". Bardo queda para bard y trovador para troubadour.

Para el próximo bump del juego: **la adjudicación de una cadena a interna no puede hacerse mirando una sola aparición**. El barrido de este apartado es reproducible y barato, y hay que repetirlo cuando el árbol cambie.
