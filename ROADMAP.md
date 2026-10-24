# Hoja de ruta

Hacia dónde va el pack. El detalle de cada tarea está en las [issues](https://github.com/backmind/battle-brothers-es/issues), agrupadas por [milestone](https://github.com/backmind/battle-brothers-es/milestones); este documento solo marca la dirección.

## Hecho: el juego base y Legends

La traducción del juego base y sus expansiones está completa desde la 1.0.0. La numeración salta de la 1.0.1 a la 4.0.0 para continuar la de la traducción anterior en Nexus, que llegó a la 3.0.5.

[Legends](https://github.com/Battle-Brothers-Legends/Legends-public), el mod más grande de Battle Brothers, está traducido desde la 5.0.0: unas 15.800 frases, dentro del mismo pack, que se cargan solo si Legends está instalado. Se probó en varias partidas y con una auditoría de su código fuente, en busca de las pantallas que el juego enseña poco.

## Ahora: mantener los dos

Las versiones 5.0.x mantienen el base y Legends: erratas, textos que se cuelan en inglés o no caben en pantalla, y lo que traiga cada parche del juego o cada versión de Legends. Lo pendiente está en las [issues](https://github.com/backmind/battle-brothers-es/issues).

Las versiones de prueba, cuando las haya, se publican como *pre-release* en la página de [releases](https://github.com/backmind/battle-brothers-es/releases), así que el aviso de actualizaciones de MSU no se las ofrece a quien tiene la versión estable; para probar una, hay que bajarla de esa página a mano.

## Rosetta

El pack se apoya en [Rosetta](https://github.com/Suor/battle-brothers-rosetta), y algunas limitaciones del framework se resuelven hoy con arreglos propios del pack. Les hemos propuesto cambios a sus autores. Cuando una versión publicada de Rosetta incluya uno, el pack retira su arreglo y sube la versión mínima de Rosetta que exige. Nunca se retira contra la rama principal de Rosetta, solo contra una release.

| Propuesta en Rosetta | Qué cambiaría en el pack |
|---|---|
| [#19](https://github.com/Suor/battle-brothers-rosetta/pull/19): el tooltip de entidad se engancha dos veces (aceptada; falta que salga en una release) | El texto de los tooltips del mapa dejará de pasar dos veces por el traductor. |
| [#18](https://github.com/Suor/battle-brothers-rosetta/pull/18): el extractor no lee las cadenas `@"..."` | Sobraría el paso propio que las convierte antes de extraer el texto de Legends. |
| [#11](https://github.com/Suor/battle-brothers-rosetta/pull/11) y [#10](https://github.com/Suor/battle-brothers-rosetta/issues/10): `:t` que conserva el hueco sin traducir | Algunas reglas podrían dejar de fallar cuando un hueco no tiene traducción. |
| [#15](https://github.com/Suor/battle-brothers-rosetta/issues/15): probar el texto sin espacios en los bordes | Sobrarían los arreglos de bordes, como el enganche de `::Legends.tooltip`. |
| [#16](https://github.com/Suor/battle-brothers-rosetta/issues/16): las reglas con la misma clave se prueban por orden de carga | Sobraría reordenar en el build las reglas genéricas detrás de las concretas. |
| [#13](https://github.com/Suor/battle-brothers-rosetta/issues/13): una regla sin palabra fija se archiva bajo una clave imposible | Algunas reglas podrían escribirse sin rodeos. |
| [#9](https://github.com/Suor/battle-brothers-rosetta/issues/9): contracciones del español («a el» → «al») | Algunas reglas podrían componer texto sin preocuparse de la contracción. |
| [#17](https://github.com/Suor/battle-brothers-rosetta/issues/17), [#14](https://github.com/Suor/battle-brothers-rosetta/issues/14), [#12](https://github.com/Suor/battle-brothers-rosetta/issues/12), [#6](https://github.com/Suor/battle-brothers-rosetta/issues/6) y [#2](https://github.com/Suor/battle-brothers-rosetta/issues/2) | Otros fallos y límites del extractor y del runtime; cada uno resolvería textos que hoy se tratan a mano. |

## Después: otros mods

Cada mod se traduce en su propio corpus, junto al del juego base, y se carga solo si el mod está instalado. Para elegir el siguiente cuentan cuánta gente lo juega, cuánto texto tiene y que sus autores estén de acuerdo. Si quieres proponer uno, abre una issue.
