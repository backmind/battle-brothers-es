# Hoja de ruta

Hacia dónde va el pack. El detalle de cada tarea está en las [issues](https://github.com/backmind/battle-brothers-es/issues), agrupadas por [milestone](https://github.com/backmind/battle-brothers-es/milestones); este documento solo marca la dirección.

## Ahora: el juego base

La traducción del juego base y sus expansiones está completa desde la 1.0.0. La numeración salta de la 1.0.1 a la 4.0.0 para continuar la de la traducción anterior en Nexus, que llegó a la 3.0.4. Las versiones 4.0.x mantienen el base: erratas, textos que se cuelan en inglés o no caben en pantalla, y lo que traiga cada parche del juego. Lo pendiente está en el milestone [4.0.1](https://github.com/backmind/battle-brothers-es/milestone/1).

## Siguiente: Legends

[Legends](https://github.com/Battle-Brothers-Legends/Legends-public) es el mod más grande de Battle Brothers y el primero que se traduce. La traducción está hecha y revisada, pero falta probarla en partida. El seguimiento está en el milestone [Legends](https://github.com/backmind/battle-brothers-es/milestone/2).

Antes de que entre en una versión estable habrá betas para probarla. Se publican como *pre-release* en la página de [releases](https://github.com/backmind/battle-brothers-es/releases), así que el aviso de actualizaciones de MSU no se las ofrece a quien tiene la versión estable; para probar una, hay que bajarla de esa página a mano. Legends irá dentro del pack, en la 5.0.0: su traducción se carga solo si Legends está instalado. Las betas se numeran 5.0.0-beta.1, 5.0.0-beta.2 y así sucesivamente.

## Rosetta

El pack se apoya en [Rosetta](https://github.com/Suor/battle-brothers-rosetta), y algunas limitaciones del framework se resuelven hoy con arreglos propios del pack. Les hemos propuesto cambios a sus autores. Cuando una versión publicada de Rosetta incluya uno, el pack retira su arreglo y sube la versión mínima de Rosetta que exige. Nunca se retira contra la rama principal de Rosetta, solo contra una release.

| Propuesta en Rosetta | Qué cambiaría en el pack |
|---|---|
| [#19](https://github.com/Suor/battle-brothers-rosetta/pull/19): el tooltip de entidad se engancha dos veces | El texto de los tooltips del mapa dejaría de pasar dos veces por el traductor. |
| [#18](https://github.com/Suor/battle-brothers-rosetta/pull/18): el extractor no lee las cadenas `@"..."` | Sobraría el paso propio que las convierte antes de extraer el texto de Legends. |
| [#11](https://github.com/Suor/battle-brothers-rosetta/pull/11) y [#10](https://github.com/Suor/battle-brothers-rosetta/issues/10): `:t` que conserva el hueco sin traducir | Algunas reglas podrían dejar de fallar cuando un hueco no tiene traducción. |
| [#15](https://github.com/Suor/battle-brothers-rosetta/issues/15): probar el texto sin espacios en los bordes | Sobrarían los arreglos de bordes, como el enganche de `::Legends.tooltip`. |
| [#16](https://github.com/Suor/battle-brothers-rosetta/issues/16): las reglas con la misma clave se prueban por orden de carga | Sobraría reordenar en el build las reglas genéricas detrás de las concretas. |
| [#13](https://github.com/Suor/battle-brothers-rosetta/issues/13): una regla sin palabra fija se archiva bajo una clave imposible | Algunas reglas podrían escribirse sin rodeos. |
| [#9](https://github.com/Suor/battle-brothers-rosetta/issues/9): contracciones del español («a el» → «al») | Algunas reglas podrían componer texto sin preocuparse de la contracción. |
| [#17](https://github.com/Suor/battle-brothers-rosetta/issues/17), [#14](https://github.com/Suor/battle-brothers-rosetta/issues/14), [#12](https://github.com/Suor/battle-brothers-rosetta/issues/12), [#6](https://github.com/Suor/battle-brothers-rosetta/issues/6) y [#2](https://github.com/Suor/battle-brothers-rosetta/issues/2) | Otros fallos y límites del extractor y del runtime; cada uno resolvería textos que hoy se tratan a mano. |

## Después: otros mods

Cada mod se traduce en su propio corpus, junto al del juego base, y se carga solo si el mod está instalado. Para elegir el siguiente cuentan cuánta gente lo juega, cuánto texto tiene y que sus autores estén de acuerdo. Si quieres proponer uno, abre una issue.
