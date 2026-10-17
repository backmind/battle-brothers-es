# Hallazgos de la verificación in-game v0.1.0 (2026-08-15/16)

Log de la sesión de prueba: "Adding 12325 es pairs in vanilla", 0 errores de rosetta y 231 líneas NOT FOUND (informativas; así marca el log de Rosetta cada cadena que no encuentra en el corpus). El juego estaba actualizado a la última versión y el corpus construido sobre el árbol (los scripts descompilados del juego) 1.5.1.8, así que la independencia de versión quedó validada.

## Clases de texto en inglés observadas y su causa

1. Patrones en cuarentena (los que el pack retiene sin distribuir hasta tiparlos; Fase 4, v0.2.0): log de combate ("X uses Y and hits Z (Chance, Rolled)", "has killed", "is confident"), "Paid X daily", "Costs X AP and Y Fatigue", mecánica de habilidades y traits, "Level X", "locked until X more perks", "Act in X turn(s)". Evidencia: aparecen como NOT FOUND en el log con colores resueltos y nombres ya traducidos dentro. La conversión a sintaxis <etiqueta:tipo> los activa (ver [PATTERNS_TODO.md](PATTERNS_TODO.md)).

   CORREGIDO 23/08/2026, en la segunda sesión de verificación. Lo observado es cierto, pero el diagnóstico estaba mal: **el log de combate no está en cuarentena**. La cuarentena bajó de 957 pares a 38 y esa familia salió de ella hace tiempo. El patrón de `base_es.nut:66429` está bien tipado y se distribuye:

       en = "<actor:str_tag> uses <weapon:str> and hits <target:str_tag> (Chance: <chance:int>, Rolled: <rolled:int>)"
       es = "<actor> usa <weapon:t> y acierta a <target> (Probabilidad: <chance>, Tirada: <rolled>)"

   Falla por el flag `:t`, que pide traducir también la pieza capturada. Cuando el juego compone la línea, el nombre de la habilidad **ya viene traducido** por su propio hook (`Batter` a "Abollar", `base_es.nut:59605`). El `:t` busca entonces un par con `en = "Abollar"`, no lo encuentra, y la propiedad de seguridad del `:t` hace que la regla entera devuelva null. De ahí el log bilingüe: los nombres traducidos por sus hooks y el marco en inglés.

   La regla general, que vale para cualquier patrón nuevo: antes de poner `:t` en una pieza, averiguar si esa pieza llega ya traducida. Si otro hook la tradujo antes, el `:t` mata la regla. Son 12 los patrones del corpus que usan `:t` y 11 los que llegan al juego, así que auditarlos todos es barato. Importa especialmente para los nombres de objeto famoso, cuyo diseño se apoya entero en ese flag.

   AUDITADOS los 12 el 24/08/2026, con el árbol del juego delante. Se corrigieron quitando el `:t` los seis del log de combate (`<weapon>`) y los dos de objeto roto y destruido (`<item>`), porque getName de skills e items está enganchado (hooks.nut:150-157) y la pieza llega ya en español. Son correctos y no se tocan los dos `:t` de "<part:t> y sufre <injury:t>", porque Const.Strings.BodyPartName llega cruda en inglés con pares propios (head a cabeza, body a cuerpo), el getNameOnly de lesiones no está enganchado y los nombres de lesión tienen par literal. Dos quedan con matiz, pendientes de verificación en partida. El patrón corto `<actor> ha recibido ... en su <part:t>` tiene doble origen con el mismo lado en: parte del cuerpo, que llega en inglés, y nombre de armadura o casco vía getName, que llega traducido; con `:t` fallan los golpes a armadura sin destruirla, y sin él saldrían head y body en inglés. Y "Contratados por <faction:t>" solo funciona hoy con casas nobles, porque "House X" casa con la regla compuesta `House <name:str>`, mientras que las ciudades estado y las facciones de asentamiento matan la regla. La auditoría descubrió además un matiz nuevo del guardián del `:t` (la propiedad de seguridad de arriba): tampoco distingue "encontrado pero idéntico" (un par cuyo `es` es igual al `en`, caso de los nombres propios), que también mata la regla. El patrón número 12, el que no llega al juego, es la segunda copia de `<actor>'s <part> is hit for <dmg> damage` en la sección de armor.nut: la deduplicación por en idéntico de load_ref se queda con la primera (sección de actor.nut), así que una sola regla sirve a los dos orígenes y no se les puede dar comportamientos distintos mientras compartan lado en.

   Lo que sigue en pie del punto original: los demás casos de la lista ("Costs X AP", "Level X", "locked until X more perks") sí son cuarentena. "Act in X turn(s)" ya no: el 23/08 se vio traducido como "Actúa en 2 turnos".

2. Funnels sin hook, es decir, conductos por los que el texto llega a pantalla sin que nada lo intercepte (no aparecen en NOT FOUND pese a verse en inglés, porque el texto **ni siquiera** pasa por Rosetta): aviso del menú principal (scripts/ui/screens/menu/main_menu_screen.nut), tips de la pantalla de carga (Const.TipOfTheDay hacia ui/screens/loading/loading_screen.js), cuerpo de los eventos (el título **sí** se traduce: viajan por conductos distintos), pantalla post-batalla ("Victory", "The enemy was destroyed in N rounds"). Candidatos a hooks propios del pack o a contribución upstream (issue a Suor).

   RESUELTO en dos tiempos: el 24/08/2026, con los hooks del pack (lote 1, verificados en partida esa tarde), y el 27/08/2026, cuando la propiedad pasó a upstream. Rosetta 0.5.0 trae estos conductos de serie (tras nuestro PR #8, que Suor cerró reimplementándolos), y el pack retiró sus copias salvo la del aviso del menú principal, que upstream no lleva.

3. Capa JS, las pantallas que el juego dibuja en JavaScript y que no pasan por Rosetta: "Background", botones "Show/hide", pestañas "Statistics" y "Loot", botón "Continue". RESUELTO: el pack ya lleva su propia capa, el addon `mod_battle_brothers_es_ui_<version>.zip` que construye `tools/build_ui_addon.py`, y ya no hace falta instalar a mano `trad303.zip` (el zip de JS de la traducción original). Ese zip traía 38 ficheros `.js` (no 62: esa cifra contaba también las 24 entradas de directorio); se distribuyen 36. Los dos que faltan se explican [más abajo](#dos-módulos-js-de-la-traducción-original-que-no-se-distribuyen-23082026).

4. Motor C++ (no interceptable por diseño): rótulos del mapa ("Northern Reaches"). La mitigación histórica de la traducción fan fueron las fuentes del kit gfx y los nombres sin tildes.

5. Doble traducción (inofensivo): la mayoría de los NOT FOUND del log son textos que ya están en español y que Rosetta vuelve a interceptar cuando se redibuja un tooltip.

6. Pares desalineados del bootstrap heurístico (el armado automático del corpus a partir de la traducción original): 1 encontrado y corregido (el tooltip de "kills" mostraba el texto de renombrar personaje). Después se hizo un barrido semántico completo del corpus, contado en [HISTORIA.md](../../docs/HISTORIA.md).

7. MSU (Modding Standards & Utilities, una de las dependencias del pack) referencia gfx/fonts/cinzel en ui/mods/msu/css/misc.css sin distribuir la fuente, lo que deja 1 error IO cosmético en el log. Se silencia reinstalando el kit gfx de la traducción antigua (fuentes Cinzel). Aviso de empaquetado: el renderizador de UI carga las fuentes por **ruta de disco** (data/gfx/fonts/...), no vía zips. Las fuentes deben instalarse como carpeta suelta gfx/ en data/, y el addon de UI (zip) solo debe contener ui/ (js). Verificado 2026-08-16: con las fuentes dentro del zip el error IO persiste; con la carpeta suelta desaparece.

   CORREGIDO 23/08/2026, al empaquetar la capa JS. Lo observado arriba es cierto, pero la causa y el dueño del problema estaban mal: **el fallo no es de MSU ni nuestro**. El propio `ui/fonts.css` del juego pide las dos Cinzel como `coui://data/gfx/fonts/cinzel/...`, con un `data/` que las demás rutas del mismo fichero no llevan (`coui://gfx/fonts/arsenal/...`). Dentro del `.dat` la ruta empacada es `gfx/fonts/cinzel/...`, sin ese prefijo, así que esas dos URL solo resuelven si el fichero está suelto en disco. MSU se limitó a copiar la línea del juego, y el error ocurre también en el juego sin mods.

   El "kit gfx de la traducción antigua" tampoco era de la traducción: era el propio juego extraído a disco, porque las 12 fuentes de `data/gfx/fonts/` son byte a byte las que el juego trae empacadas en `data_001.dat`, licencias `OFL.txt` incluidas. Los `-edited` de FreeUniversal también son de Overhype y no parches de terceros. En consecuencia, el pack no distribuye fuentes, porque no son suyas y no las necesita, y la instalación se queda en copiar dos zips. Además, `arsenal`, que el juego y MSU referencian, no está en ningún `.dat` ni en disco, así que ese error IO lo tiene todo el mundo.

   Lo que sigue en pie del aviso original: el zip del addon lleva solo `ui/`, porque una fuente metida en un zip no puede satisfacer una URL con `data/`.

## Dos módulos JS de la traducción original que no se distribuyen (23/08/2026)

Al empaquetar la capa JS se compararon los 38 `.js` de `trad303.zip` con el `ui/` que traía el juego en su versión 1.5.2.3 (`data_001.dat`), enmascarando los literales de cadena para separar traducción de código. 36 solo cambian texto y entran en el addon sin reservas. Los otros dos no entran:

- `world_screen_topbar_daytime_module.js` viene de una versión del juego anterior y le faltan 29 líneas que el fichero actual sí tiene: el cuarto botón de velocidad del mapa completo (`mTimeVeryFastButton`, avance muy rápido, con sus dos recursos gráficos y su manejador). Distribuirlo traduciría tres cadenas ("Day", "PAUSED", "(Press Spacebar)") a cambio de quitarle al jugador un botón que funciona. Consecuencia visible: el reloj de la barra superior sigue en inglés. Recuperarlo es trabajo de traducción: trasladar esas tres cadenas al fichero actual del juego.
- `character_screen_paperdoll_module.js` es byte a byte idéntico al del juego y no traduce ni una palabra. Distribuirlo solo congelaría esa copia cuando el juego se actualice.

Los dos están en `EXCLUIDOS`, en `tools/build_ui_addon.py`, y hay un test que falla si reaparecen en `src/ui/`.

De los 36 que sí entran, uno lleva una diferencia de código que se revisó y se aceptó: en `character_screen_left_panel_header_module.js` el traductor renombró dos claves de objeto, `Hitpoints` a `Vida` y `Fatigue` a `Fatiga`, dentro de `mLevelUpLeftStatsRows`. Es inofensivo y también inútil, porque la clave se escribe y se lee en el mismo fichero (`data('stat', _key)` al crear la fila, leída en `increaseLevelUpStatValue`) y nunca se muestra al jugador, que ve el icono y el tooltip. Se comprobó que MSU no toca esas claves. Queda registrado en `ACEPTADOS`, en `tools/check_ui_drift.py`, con las cuentas fijadas: si el juego vuelve a mover ese fichero, el aviso reaparece.

Aviso para quien revise el punto 3 con el zip antiguo en la mano: el `mod_rosetta_base_es_ui_0.1.0.zip` que se probó en partida el 16/08/2026 llevaba los 38, así que esa partida se jugó sin el cuarto botón de velocidad. El addon construido (`1.5.2.3-1`) lo devuelve.

## Deuda de medición: cuánto del árbol no cubre el corpus (23/08/2026, resuelta el 17/10/2026)

Los puntos 1 y 2 de arriba se descubrieron leyendo un log de partida. Falta la medida sistemática equivalente: qué literales del juego no captura ningún par.

Tardó en tener cifra porque **no se puede medir comparando cadenas**: el corpus generaliza a propósito, y un solo par cubre decenas de literales:

    // literal del juego
    _event.m.Anatomist.getName() + " gains [color=..]+100[/color] Experience"
    // el par que lo cubre
    en = "<actor:str> gains <v:val_tag> Experience"

Se intentó dos veces por comparación de cadenas (literal exacto, y forma normalizada sustituyendo `<...>` y `[...]`) sobre los 16.095 literales que `rosetta.py -les` saca del árbol. Dieron 907 y 1447 huecos, y al comprobarlos a mano casi todos eran falsos positivos de esa generalización. **Las dos cifras son inservibles: no citarlas.**

El método que sí vale es ejecutar el emparejador de Rosetta sobre la lista de literales y quedarse con los que ningún par captura. Es lo que hace `es_pack/tools/measure_coverage.py`, que corre Squirrel desde el repo igual que `es_pack/tools/sq_probe_ids.nut`. La medida del 17/10/2026 da el 100 % de las frases del juego, con los restos que no son texto revisados uno a uno y listados en la herramienta.

Lo que sí está medido, sobre `scripts/config` y comprobado caso por caso: de 3999 cadenas extraíbles había 27 sin ninguna entrada en el corpus, y las 27 llevaban guion. Se perdieron en el armado original (no en el extractor, que las saca todas, ni por ser contenido nuevo). Se repararon con 23 pares nuevos. El mismo hueco puede seguir en los ~3100 ficheros restantes.

## Clase 8: el juego suma o adorna antes de que Rosetta busque (31/08/2026)

Se descubrió a trozos y se confirmó como clase en la quinta pasada de QA. La búsqueda literal de Rosetta es exacta, así que basta con que el juego toque la cadena entre el par y la pantalla para que no case nada. Hay dos formas, y las dos se han visto ya en tres sitios distintos:

**Cola de espacios.** El juego concatena `"\n\n"` al texto justo antes de construirlo. Le pasa a la pantalla de fin de partida (`asset_manager.nut:1724`, caso 39 del preload) y al texto de "Tu tarea" de todas las ambiciones y juramentos (`ambitions/ambition.nut:114` y `oaths/oath_ambition.nut:31`, caso 40). Se reconoce en el log porque la cadena sale con la cola pegada: `Enter and win 5 fights in the arena of the southern city states.\n\n`. El remedio del pack es un hook que traduce antes de la costura. El remedio limpio sería que el runtime probase la cadena recortada cuando la exacta falla; está pedido aguas arriba en [Suor/battle-brothers-rosetta#15](https://github.com/Suor/battle-brothers-rosetta/issues/15).

**Suma de bloques.** El juego escribe un bloque y le añade otro, y el corpus tiene los dos por separado porque así los vio el extractor. Le pasa a los textos de jubilación (dos bloques de plantilla con dos finales de hermano intercalados, caso 39) y a la cláusula de pago de la negociación de contratos (`negotiation_templates.nut`: `this.Text = <presentación>` y luego `this.Text += <cláusula>`, tres pantallas x tres presentaciones x nueve cláusulas). La negociación se resuelve en el corpus con doce reglas recursivas que pelan su cláusula y devuelven el resto al pipeline con `<intro:t>`, el mismo truco de la lista de provisiones del séquito; los textos de jubilación, con un marcador de control en el hook, porque ahí los trozos no se distinguen una vez sumados.

Para cazarlas en el futuro, la señal en el log es una cadena en inglés puro que **sí** existe en el corpus. El barrido está en el guion de QA y es de dos líneas: filtrar los `NOT FOUND` sin una sola tilde ni palabra funcional castellana, y buscar cada uno en `base_es.nut`. Si aparece, la traducción existe y lo que falla es la costura del juego, es decir, esta clase.
