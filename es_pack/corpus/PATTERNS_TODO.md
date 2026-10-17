# La cuarentena de patrones

Quedó vacía al publicar la 1.0.0 (`build_dist.py` informaba `wip: 0`), y la CI falla si deja de estarlo. Aquí se explica qué es y cómo se vacía si un parche del juego la vuelve a llenar.

La cuarentena es `es_pack/build/patterns_wip.nut`, un informe que el build regenera desde el corpus y que nunca se edita a mano:

```bash
PYTHONUTF8=1 uv run python es_pack/tools/build_dist.py
```

## Por qué existe la cuarentena

`classify()` en `es_pack/tools/build_dist.py` aplica el contrato real de `validateRule` en `vendor/rosetta/scripts/!mods_preload/!rosetta.nut`. Un patrón marca cada variable con un placeholder `<nombre:tipo>`, y los tipos de subetiqueta que el runtime admite son exactamente estos:

```
int, val, word, str, line, tag, img, int_tag, val_tag, str_tag
```

Un par pasa a `dist` solo si:

- cada placeholder `<...>` en `en` tiene la forma `<nombre:tipo>` con `tipo` en la lista de arriba;
- no hay dos `<...:str>` adyacentes en `en` (el runtime no podría decidir dónde termina uno y empieza el otro);
- cada placeholder `<...>` en `es` (con o sin `:t`) referencia una etiqueta que existe en `en`.

Si alguna de estas condiciones falla, el par cae en `wip`, la cuarentena. Ahí no se carga en el juego (el wrapper generado para `wip` no lleva `::Rosetta.add`, solo un comentario de aviso), pero sigue íntegro en el corpus (`es_pack/corpus/base_es.nut`), listo para corregirlo.

**De ahí que la validación por lote sea automática**: un par convertido correctamente pasa de `wip` a `dist` con volver a correr `build_dist.py`. No hace falta un checker aparte, porque el propio rebuild dice si el lote quedó bien (sube `dist`, baja `wip`) o si sigue mal (se queda en `wip`, o revienta el `load_ref` de upstream, señal de un error de sintaxis más grave en el bloque).

## Cómo se vacía

1. Elegir un lote de 30 a 50 pares de la misma clase en `patterns_wip.nut`.
2. Convertirlos editando `es_pack/corpus/base_es.nut`, siguiendo la [guía de traducción de Rosetta](https://github.com/Suor/battle-brothers-rosetta/blob/master/AGENTS_TRANSLATING.md). Las conversiones habituales:
   - `[color=<this.Const...>]50%[/color]` pasa a `en = "... <x:val_tag> ..."` y en `es` simplemente `<x>`.
   - `<this.Const.Strings.getArticle(...) + item.getName()>` pasa a `<item:str_tag>` o `<item:str>` según el caso; en `es`, `<item>`, o `<item:t>` si ese contenido tiene su propio par literal y llega en inglés. Si llega ya traducido por otro hook, el `:t` mata la regla entera (ver KNOWN_ISSUES.md, punto 1).
   - Los pares que solo llevan `%marcadores%` y ningún `<...>` real suelen poder pasar a literales: basta quitarles `mode = "pattern"`.
   - Los pares con `<ret>`, restos de una concatenación parcial, casi nunca se salvan como patrón, porque el texto completo suele estar ya en otro par.
3. Reconstruir. `dist` sube y `wip` baja exactamente en el tamaño del lote, y esa cuenta es la validación del lote.
4. Cada pocos lotes, instalar el zip y comprobar en partida al menos una frase del lote, con el log del juego sin errores de Rosetta.
