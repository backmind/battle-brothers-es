# Cómo contribuir a la traducción

Cada traducción vive en un archivo de texto de `es_pack/corpus/`: la del juego base y sus expansiones, en `base_es.nut`, y la de cada mod, en el suyo (ver [Traducir un mod](#traducir-un-mod)). Corregir algo es editar una línea y abrir un pull request, la propuesta de cambio que GitHub te ofrece al guardar una edición desde la web. No hace falta saber programar.

## Qué aporta más valor

La lista va de más a menos útil, y lo primero no requiere saber nada del proyecto.

1. **Jugar y reportar con captura lo que se vea mal.** Es lo más útil que puede hacer alguien aquí, porque el defecto más frecuente solo se ve jugando (el porqué está en [Reportar algo que se ve mal en el juego](#reportar-algo-que-se-ve-mal-en-el-juego)).
2. **Convertir patrones tras un parche.** Los textos con partes variables (el log de combate, la mecánica numérica de las habilidades) necesitan la sintaxis `<nombre:tipo>` de los [patrones](#los-textos-con-variables), y hasta que la tienen salen en inglés enteros. La [cuarentena](#los-textos-con-variables) quedó vacía al publicar la 1.0.0, pero un parche puede volver a llenarla. Convertirlos rinde mucho, porque un solo patrón cubre decenas de frases del juego. El procedimiento está en [es_pack/corpus/PATTERNS_TODO.md](es_pack/corpus/PATTERNS_TODO.md).
3. **Revisar sospechosos que las auditorías ya han listado.** `align_score.py` deja en `es_pack/build/align_report.tsv` los pares ordenados de peor a mejor, y `nouns_cross.py` saca tablas de nombres cruzadas. El trabajo es confirmar o descartar, mirando el inglés y el español, sin traducir nada.
4. **Traducir lo que traigan los parches del juego.** La cola de sin traducir quedó a cero al publicar la 1.0.0, y funciona como detector: cuando el juego se actualice, las cadenas nuevas caerán ahí. El recuento vivo está en el cuadro de cifras del [README](README.md).
5. **Traducir un mod.** Es el trabajo más grande, y empieza por pedir permiso a sus autores; está explicado en [Traducir un mod](#traducir-un-mod).

Y en esto el esfuerzo **no** rinde:

- Los rótulos que el motor dibuja sobre el mapa, que por diseño no se pueden interceptar.
- Los nombres de objeto legendario, bloqueados en el propio Rosetta ([Suor/battle-brothers-rosetta#6](https://github.com/Suor/battle-brothers-rosetta/issues/6)).
- Traducir JavaScript de forma nativa. Es el [js-plan de Rosetta](https://github.com/Suor/battle-brothers-rosetta/blob/master/docs/js-plan.md), tiene nueve preguntas de diseño sin decidir y la decisión es de quien mantiene Rosetta. No hay que confundirlo con la capa JS que el pack ya distribuye, que es otro mecanismo y ya está hecha.
- "Corregir" las excepciones de estilo deliberadas, listadas en [Estilo](#estilo). Si una traducción parece libre de más, mira antes si es intencionada.

## Alcance

Este repositorio contiene el pack de traducción. Lo que entra: el texto del juego base y sus expansiones y el de los mods que se vayan traduciendo, cada uno en su corpus; la capa de interfaz en JavaScript, que se empaqueta aparte; y las herramientas que construyen y comprueban todo ello.

Lo que no entra: el framework Rosetta, que es de hackflow, y lo que el motor dibuja sin pasar por script. De Rosetta solo hay aquí una copia mínima en `vendor/rosetta/` para que funcionen las herramientas. Esa copia no se edita, y los cambios al framework van como pull request a [Suor/battle-brothers-rosetta](https://github.com/Suor/battle-brothers-rosetta).

## Traducir un mod

Las traducciones de mods viven en este mismo repositorio y salen en el mismo zip que la del juego base, así que el jugador instala un solo pack. Cada mod tiene su propio corpus al lado del base, con el ID del mod en el nombre: `es_pack/corpus/<id_del_mod>_es.nut` (por ejemplo, `mod_legends_es.nut`). Dentro de `mod_battle_brothers_es_<versión>.zip` viaja junto a `base_es.nut`, y el preload del pack solo lo carga si ese mod está instalado (`::Hooks.hasMod`), de modo que a quien no lo usa no le cuesta nada. Todo el pack lleva una sola versión, y cada traducción tiene su fila en la tabla «Qué se traduce» del README, con la versión del mod contra la que se verificó y su cobertura.

Antes de empezar:

1. **El permiso de los autores del mod.** Su texto es suyo, y sin su permiso para distribuirlo traducido no entra. Anótalo en la incidencia.
2. **Una incidencia o una discusión** que diga qué mod y qué versión, para no duplicar trabajo.
3. **El corpus se saca con el extractor de Rosetta** sobre las fuentes del mod: `PYTHONUTF8=1 uv run python vendor/rosetta/rosetta.py <carpeta del mod> -les > es_pack/corpus/<id_del_mod>_es.nut`. Lo que el mod reutiliza del juego base ya está traducido en `base_es.nut`, y el glosario y el estilo son los mismos.

Legends, el primer mod en marcha, tiene su propia herramienta: `es_pack/tools/lotes.py`. La fuente está fijada en `es_pack/legends/fuente.toml`, y `lotes.py extraer` saca el corpus con el contexto de código de cada par y quita lo que ya traduce `base_es.nut`. Las cadenas verbatim de Squirrel (`@"..."`) las convierte antes, porque el extractor no las lee. El trabajo se reparte en lotes (`lotes.py partir`) que se devuelven al corpus con `lotes.py fusionar`; la fusión rechaza el lote entero si algún par rompería el juego. Las instrucciones para traducir un lote están en [es_pack/legends/BRIEF.md](es_pack/legends/BRIEF.md).

Para que un mod nuevo entre en el zip, se añade a `MODS` en `build_dist.py` y a la cola del preload (`mod_battle_brothers_es.nut`), con su `::Hooks.hasMod`; un test comprueba que los dos coinciden. Si el mod necesita algo más que sus pares, como Legends con sus tokens de género y sus títulos en femenino, el enganche va en `es_pack/src/mod_battle_brothers_es/`. La fila de la tabla «Qué se traduce» se añade a `OBJETIVOS` en `update_readme_metrics.py` cuando la traducción se publique.

## El formato

Cada corpus es una lista de pares. Cada uno tiene el texto inglés que el juego usa y su traducción:

```squirrel
    {
        en = "Your Task"
        es = "Tu tarea"
    }
```

Los pares van agrupados por el archivo del juego del que salen, marcado con un comentario `// FILE:`. Eso sirve para saber en qué contexto aparece un texto, que es la información más útil cuando dudas de una traducción.

Un par con `es = ""` está sin traducir. El build (el script que genera el pack, ver [Antes de abrir el pull request](#antes-de-abrir-el-pull-request)) lo deja fuera del pack, así que el juego lo muestra en inglés.

Hay además líneas sueltas con la forma `// en = "..."`, sin bloque. Marcan cadenas que el juego usa por dentro y jamás muestra (claves de plantilla, identificadores de pantalla, rutas), adjudicadas una a una con el código del juego delante. Déjalas como están y ahórrate el tiempo de traducirlas; el registro de esa criba, con el porqué de cada clase, está en [es_pack/corpus/VACIOS.md](es_pack/corpus/VACIOS.md).

## Reglas que no se pueden romper

**No se toca el lado `en`.** Es la clave con la que Rosetta encuentra el texto en el juego. Si lo cambias, ese par deja de aplicarse y el texto vuelve al inglés.

**Los tokens se copian tal cual.** Cosas como `%name%`, `%randombrother%`, `%SPEECH_ON%`, `[img]gfx/ui/events/event_92.png[/img]` o `[color=#000000]` son marcadores que el juego sustituye o interpreta. Tienen que aparecer en el `es` igual que en el `en`, con la misma grafía. Puedes moverlos de sitio dentro de la frase si el castellano lo pide.

**Las llaves y las barras de variante también.** Los textos con `{una cosa | otra cosa}` dejan que el juego elija entre alternativas. El `es` tiene que tener el mismo número de llaves y de barras que el `en`, y **cada barra va con un espacio a cada lado**, como en el inglés: el juego solo parte las variantes por ` | `, y sin el espacio enseña las alternativas enteras con las barras a la vista.

**Las secuencias `\x7b`, `\x7d` y `\x22`** son llaves y comillas codificadas. Déjalas como están; el build las convierte al empaquetar.

## Los textos con variables

Algunos textos llevan partes que el juego rellena en marcha. Se marcan con `mode = "pattern"` y capturas con nombre y tipo:

```squirrel
    {
        mode = "pattern"
        en = "Has a range of <range:int> tiles"
        es = "Tiene un alcance de <range> casillas"
    }
```

En el `en` la captura lleva nombre y tipo (`<range:int>`); en el `es` solo el nombre (`<range>`). Los tipos disponibles y sus reglas están en la [guía de traducción de Rosetta](https://github.com/Suor/battle-brothers-rosetta/blob/master/AGENTS_TRANSLATING.md). El runtime (la parte de Rosetta que corre dentro del juego) impone dos restricciones más: no puede haber dos capturas de tipo `str` pegadas, y toda captura que uses en el `es` tiene que existir en el `en`.

Si un par tiene una captura que no cumple esas reglas, el build lo manda a cuarentena en vez de al pack, y no llega al juego. Es a propósito, porque un par mal formado abortaría la carga completa de la traducción en la partida de quien lo instale.

## Estilo

El texto va en **español neutro**. En la práctica:

- Tuteo para el singular y "ustedes" para el plural. Nada de "vosotros" ni de voseo.
- Sin léxico marcado regionalmente.
- Un término, una traducción. Si dudas de cómo se llama algo, busca en el archivo cómo está traducido en otros sitios y sigue ese criterio.

Hay dos excepciones deliberadas que no hay que "corregir": el habla propia de algunos personajes, y unos usos de "usted" que caracterizan a alguien concreto frente al capitán.

Los guiños y homenajes que dejó el equipo original se conservan. Si te topas con una traducción que parece libre de más, mira antes si es intencionada.

## Antes de abrir el pull request

Con Python 3.12 o superior y [uv](https://docs.astral.sh/uv/) instalados:

```bash
PYTHONUTF8=1 uv run python es_pack/tools/build_dist.py
```

Eso reconstruye el pack y dice cuántos pares entran, cuántos van a cuarentena y cuántos quedan sin traducir. Cada cifra de esa línea está definida en [es_pack/tools/README.md](es_pack/tools/README.md). Al final lanza unos chequeos de calidad que avisan de imágenes de evento que no cuadran entre idiomas, traducciones repetidas en entradas vecinas, signos de interrogación o exclamación sin su pareja de apertura, tildes que faltan y registro fuera de política. En local son avisos informativos. La CI (la integración continua de GitHub, que comprueba cada pull request) pasa el mismo build con `--estricto`, que falla si alguno sube sobre su línea base, si queda algún patrón en cuarentena o si la sintaxis Squirrel (el lenguaje de scripts del juego) no pasa; si tu cambio no sube ninguno, va bien.

Si tu cambio toca el corpus, regenera también el cuadro de métricas del README, que la CI comprueba:

```bash
PYTHONUTF8=1 uv run python es_pack/tools/update_readme_metrics.py
```

Los tests se pasan con:

```bash
PYTHONUTF8=1 uv run pytest -q
```

## Reportar algo que se ve mal en el juego

Abrir una incidencia (un issue de GitHub) con la captura ya es una ayuda enorme. Hay [tres plantillas](https://github.com/backmind/battle-brothers-es/issues/new/choose): texto en inglés en pantalla, errata o traducción mejorable, y fallo del juego. Para dudas que no son un fallo están las [Discussions](https://github.com/backmind/battle-brothers-es/discussions).

Las capturas se piden porque el defecto más frecuente es una traducción correcta puesta en el sitio de otra: cuando el juego añade o quita una entrada de una lista, todo lo que va detrás se corre una posición y cada texto acaba mostrando el del vecino. Leyendo el archivo pasa inadvertido, porque cada línea por separado parece bien, y en partida se ve en cuanto aparece el texto.

Si puedes, di también en qué situación apareció (qué contrato, qué evento, qué pantalla). Con eso se localiza el `// FILE:` y se arregla ese texto junto con toda la lista corrida.

Lo que ayuda de verdad en una incidencia, por orden: la captura, la pantalla o el evento donde salió, y el texto tal como se lee. Suma la versión del juego y la del pack si las tienes a mano. No hace falta que propongas la corrección ni que busques el archivo.

Antes de abrir una, mira si ya es un caso conocido, para no gastar tu tiempo. Si el texto sale en inglés o se ve raro, puede que tenga la causa escrita en [es_pack/corpus/KNOWN_ISSUES.md](es_pack/corpus/KNOWN_ISSUES.md), con su causa y qué hacer.

## Para quien quiera tocar las herramientas

El inventario completo está en [es_pack/tools/README.md](es_pack/tools/README.md): qué hace cada una, cuándo se usa y con qué comando. Las tres que se usan a diario son `build_dist.py` para generar el pack, `checks.py` para los avisos de calidad (ya va dentro del build) y `check_ui_drift.py`, que hay que pasar después de cada actualización del juego.

No se editan los archivos de `vendor/rosetta/`. Son una copia del framework de hackflow, y cómo se actualiza está en su [ORIGEN.md](vendor/rosetta/ORIGEN.md); los cambios al framework van como pull request a [Suor/battle-brothers-rosetta](https://github.com/Suor/battle-brothers-rosetta).

## Convivencia

Este proyecto sigue el [código de conducta](CODE_OF_CONDUCT.md) del Contributor Covenant. Al participar, te comprometes a respetarlo.
