# Problemas conocidos

Lo que hoy puede verse raro en partida, por qué pasa y qué hacer. Lo ya resuelto está en el historial de git y en el [CHANGELOG](../../CHANGELOG.md).

## Objetos legendarios con el nombre en inglés

El juego compone el nombre de un objeto legendario en marcha, juntando dos listas, y Rosetta todavía no sabe traducir esa combinación. Está pedido en [Suor/battle-brothers-rosetta#6](https://github.com/Suor/battle-brothers-rosetta/issues/6).

## Nombres de mods y frases nuevas

Los nombres de los mods en la pantalla de ajustes (Modding Standards & Utilities, Modern Hooks) se dejan en inglés a propósito: son su nombre propio. Las frases que traiga un parche del juego o una versión nueva de Legends salen en inglés hasta que se traduzcan.

## Rótulos de región en inglés en partidas empezadas antes de la 5.1.0

El nombre de cada región del mapa ("Northern Reaches") se elige al generar el mundo y el motor lo guarda con la partida; al cargarla no se vuelve a pedir. El pack lo traduce en el momento de la generación (caso 42 de `mod_battle_brothers_es_hooks.nut`), así que solo las campañas nuevas lo muestran en castellano. En las viejas, el mapa sigue en inglés, aunque los contratos ya citan la región en castellano.

## "Day" en el reloj del mapa

El pack traduce la palabra en su copia de `world_screen_topbar_daytime_module.js`. Si alguien ve "Day", ese fichero no se está cargando: falta el pack en `data`, queda un `mod_battle_brothers_es_ui_<versión>.zip` de antes de la 5.0.0, o otro mod trae el módulo entero y se carga después.

## Letras rotas en un rótulo del mapa ("CompaÃ±Ã­a")

Los rótulos que dibuja el motor (partidas y regiones) leen el texto como cp1252, no como UTF-8. El pack convierte los dos que conoce (casos 34 y 42). Si aparece otro rótulo con letras rotas, es esta misma clase y se arregla igual, convirtiendo la cadena antes de dársela al motor.

## Textos en inglés que sí tienen traducción

Rosetta busca la cadena exacta. Si el juego le añade algo antes de mostrarla (una cola `"\n\n"`, o un segundo bloque sumado al primero), no casa nada aunque el par exista. Se ha visto en el fin de partida, en el "Tu tarea" de ambiciones y juramentos, en los textos de jubilación y en la cláusula de pago de la negociación; todos están resueltos con un hook que traduce antes de la costura o con reglas que pelan la cláusula.

Para cazar uno nuevo: en el log, un `NOT FOUND` en inglés puro cuya cadena **sí** está en `base_es.nut`. El arreglo general sería que Rosetta probara la cadena recortada cuando falla la exacta, y está pedido en [Suor/battle-brothers-rosetta#15](https://github.com/Suor/battle-brothers-rosetta/issues/15).

## Ruido en el log

- La mayoría de los `NOT FOUND` son textos ya en castellano que Rosetta vuelve a recibir al redibujar un tooltip. Son inofensivos.
- Un error de IO por las fuentes: el propio `ui/fonts.css` del juego pide las Cinzel con una ruta que solo resuelve si están sueltas en disco, y Arsenal no viene en ningún `.dat`. Lo tiene todo el mundo, con mods o sin ellos. El de Cinzel se silencia extrayendo `gfx/fonts/` de `data_001.dat` a `data/gfx/fonts/`; por eso el pack no mete fuentes en su zip, donde no servirían.
