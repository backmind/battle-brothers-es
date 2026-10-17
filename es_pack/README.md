# Manual del mantenedor

Este directorio contiene todo lo propio del pack: los corpus, sus registros y las herramientas. La presentación del proyecto, la instalación para jugadores y los créditos están en el [README de portada](../README.md); la guía para colaborar, en [CONTRIBUTING.md](../CONTRIBUTING.md).

## El corpus y sus registros

Cada traducción tiene su corpus en `corpus/`, en formato Rosetta y agrupado por archivo de origen: el del juego base y sus expansiones es `corpus/base_es.nut`, y cada mod que se traduzca tendrá el suyo al lado, `corpus/<id_del_mod>_es.nut`, con la convención que explica [CONTRIBUTING.md](../CONTRIBUTING.md#traducir-un-mod). Cada entrada es un par: una cadena inglesa (`en`) y su traducción (`es`), que puede ser un literal o un patrón con variables. Hay tres clases de entrada: pares traducidos, pares con `es = ""` que son deuda pendiente, y líneas `// en = "..."` que marcan claves internas adjudicadas (cadenas que el juego usa como identificador y nunca muestra, revisadas y descartadas a propósito).

Al corpus del juego base lo acompañan varios registros, que guardan el trabajo hecho y las decisiones tomadas para que nadie rehaga lo uno ni deshaga lo otro por accidente:

- `corpus/VACIOS.md`: la adjudicación completa de los vacíos, con la política de nombres propios, la taxonomía de claves internas y las claves que romperían el juego si alguien las rellena.
- `corpus/CENSO_CIEGO.tsv`: los veredictos del censo a ciegas de las tablas de nombres, que blindan los guiños, las licencias de traducción y las decisiones editoriales.
- `corpus/GUINOS.md`: el catálogo de guiños y homenajes del equipo original, confirmados por decisión expresa.
- `corpus/KNOWN_ISSUES.md`: hallazgos de la verificación en partida, con su causa y su estado.
- `corpus/PATTERNS_TODO.md`: el procedimiento para vaciar la cuarentena de patrones, si un parche la vuelve a llenar.
- `corpus/ids_es.nut`: los pares por id que resuelven homógrafos de `m.Name` (una misma palabra inglesa que pide traducciones distintas según el objeto que la lleva), con Rosetta 0.5.0 o superior. Antes de añadir uno, pasar `tools/ids_census.py`.
- `corpus/FUENTE-305.md`: por qué no se adoptó en bloque la revisión 3.0.5 de la traducción original, con las cifras.

Ante una traducción que se aparta del literal inglés, mirar el historial de esa línea antes de corregirla (`git log -S "<valor>"`). Varias son decisiones deliberadas y están comentadas en el propio corpus con su porqué.

## Los builds

Cada comando por separado, leyendo su salida:

```bash
PYTHONUTF8=1 uv run python es_pack/tools/build_dist.py
PYTHONUTF8=1 uv run python es_pack/tools/build_ui_addon.py
PYTHONUTF8=1 uv run pytest -q
PYTHONUTF8=1 uv run python es_pack/tools/update_readme_metrics.py
```

El primero genera el zip del pack desde el corpus y lanza los chequeos de calidad; cada cifra de su línea de salida está definida en [tools/README.md](tools/README.md). El segundo empaqueta la capa de interfaz desde `src/ui/`: los `.js` de las pantallas que el juego dibuja en JavaScript, que no pasan por Rosetta. El tercero pasa los tests. El cuarto regenera el cuadro de métricas del README de portada, y la CI comprueba que esté al día.

Los hooks propios del pack están en `src/scripts/!mods_preload/`, con el porqué de cada caso comentado en el código. Instalar es copiar los zips de `build/` a la carpeta `data` del juego, borrando antes la versión anterior de cada uno.

## Tras cada actualización del juego

1. `PYTHONUTF8=1 uv run python es_pack/tools/check_ui_drift.py "<ruta>/Battle Brothers/data"`. Hace falta porque la capa JS sustituye archivos del juego, mientras que el corpus aguanta cualquier versión: si un parche toca uno de los 39 módulos, nuestra copia lo taparía en silencio. La herramienta devuelve 1 mientras quede algo sin juzgar, así que sirve de puerta antes de publicar.
2. Regenerar el corpus contra el árbol descompilado nuevo, `PYTHONUTF8=1 uv run python vendor/rosetta/rosetta.py <árbol>/scripts -les -r es_pack/corpus/base_es.nut -q > base_es.nut.nuevo`, y fusionar el resultado a mano, con el diff delante. Las cadenas nuevas del parche entran como pares vacíos y caen en el cubo `drop` del build (los pares sin traducir), que está a cero justamente para detectarlas.
3. Si además hay versión nueva de Rosetta, pasar `PYTHONUTF8=1 uv run python es_pack/tools/check_upstream_drift.py <ruta>/!rosetta.nut` con el runtime nuevo y, si no avisa de nada, copiar las piezas a `vendor/rosetta/` como dice su `ORIGEN.md`.

## Publicar una versión

1. Subir `PACK_VERSION` en `tools/build_dist.py` y la `Version` de los dos preloads de `src/scripts/!mods_preload/`; un test impide que se separen.
2. Añadir el apartado de la versión a `CHANGELOG.md`, con la versión del juego contra la que se verificó.
3. Construir, instalar los dos zips y arrancar el juego una vez antes de etiquetar.
4. Etiquetar y empujar con `git tag 1.2.3 && git push origin 1.2.3`, sin `v`, porque el aviso de actualizaciones de MSU solo entiende semver puro. La CI pasa las comprobaciones, construye los zips, idénticos byte a byte a los locales, y crea la release de GitHub con las notas del changelog.
5. Si el pack tiene página en Nexus, subir allí los mismos dos zips como ficheros principales y archivar los de la versión anterior.

## Configurar la máquina

El build, los chequeos y los tests funcionan sin configurar nada. Las herramientas que leen el juego instalado o los árboles descompilados (cobertura, censos, deriva de la capa JS) toman sus rutas del `.env` de la raíz: copia `.env.example` y ajústalo. El detalle está en `tools/rutas.py`.

## Trabajo abierto

- **Las traducciones de mods.** La 1.0.0 sale con un solo corpus. La primera traducción de un mod que entre tiene que enseñar a `build_dist.py` a empaquetar varios corpus en el mismo zip, añadir al preload la carga condicional de cada uno (`mod.queue` con `::Hooks.hasMod`, igual que el registro en MSU) y sumar su fila a `OBJETIVOS` en `tools/update_readme_metrics.py`.
- **Los nombres de objeto famoso.** Los 62 modificadores están traducidos y al final del corpus hay una tanda piloto de plantillas, pero el juego compone esos nombres en marcha y la vía para traducirlos en volumen está por decidir. Depende en parte de [Suor/battle-brothers-rosetta#6](https://github.com/Suor/battle-brothers-rosetta/issues/6).
