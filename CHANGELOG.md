# Cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). El pack numera sus versiones con [versionado semántico](https://semver.org/lang/es/), independiente de la versión del juego.

## [1.0.1] - sin publicar

- **Botones que no cabían.** Los de elegir juramento o ambición se cortaban por los dos lados, porque los botones de evento no parten línea y el castellano había perdido el salto de línea del inglés. Recuperan el salto y se condensan hasta caber, dejando aire al icono, junto con 18 opciones de evento y contrato y las descripciones de origen de la nueva partida que se salían de su columna o quedaban a ras (Cazahombres, Juramentados, Desertores, Cazadores de bestias y otras).
- **Un «[color]» suelto en la presentación de algunos contratos y eventos** (buscar un lugar, el asalto con ariete, los desertores sobornados, el juglar): el castellano había perdido el cierre de un bloque de diálogo.
- **«Cazahombres»** en toda la narrativa, como el origen y el trasfondo.
- **Dos rumores de taberna salían a medias** («Desde what I've heard...»): una regla de otro texto se les adelantaba.
- **«Habilidad cuerpo a cuerpo»** en el rótulo del atributo, que decía «Habilidad a cuerpo a cuerpo».
- **Doce órdenes en vosotros** («Decidles», «Degolladlos») pasan a ustedes, como el resto del texto.
- **Hedge Knight es siempre «caballero errante»**; en tres eventos y en el origen Lobo solitario decía «caballero andante».
- Los textos fijos marcados como patrón se instalan como texto literal, para que ninguna regla se les adelante.
- Dos chequeos nuevos: `ANCHO` mide con la fuente del juego, calibrada en partida, los botones de ambición y las descripciones de origen; `HABLA` avisa de las ramas de diálogo que dejan un color abierto o cerrado de más.

## [1.0.0] - 2026-10-17

Primera versión publicada. Verificada contra Battle Brothers 1.5.2.3 con todas sus expansiones, y requiere Rosetta 0.5.0 o superior.

- **16.099 pares de traducción**, de ellos 1.280 patrones con variables (registro de combate, tooltips con números, composiciones de nombres). Sin cadenas pendientes de traducir ni patrones en cuarentena.
- **Capa de interfaz**, para las pantallas que el juego dibuja en JavaScript y no pasan por Rosetta, con 39 módulos del juego traducidos: menú principal, opciones, pantalla de personaje, diálogos de ciudad, obituario y resultado de combate.
- **Hooks propios** (código que intercepta una función del juego para traducir lo que muestra) para las pantallas cuyo texto no pasaba por Rosetta: negociación de contratos, ambiciones, taberna, séquito, puerto, diálogos del combate táctico y otras.
- **Texto revisado entero** desde la traducción de la comunidad: corrimientos de listas realineados, un censo a ciegas de las tablas de nombres, registro unificado en español neutro y un glosario fijo. El detalle está en la [historia del proyecto](https://github.com/backmind/battle-brothers-es/blob/main/docs/HISTORIA.md).
- **La pantalla de ajustes de MSU en español**, con una página propia del pack: versión, estado de verificación, créditos y enlaces.
- **Seis pasadas de verificación en partida**, con el registro del juego revisado en cada una.

[1.0.0]: https://github.com/backmind/battle-brothers-es/releases/tag/1.0.0
