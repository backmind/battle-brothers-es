# Cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). El pack numera sus versiones con [versionado semántico](https://semver.org/lang/es/), independiente de la versión del juego.

## [1.0.0] - 2026-10-17

Primera versión publicada. Verificada contra Battle Brothers 1.5.2.3 con todas sus expansiones, y requiere Rosetta 0.5.0 o superior.

- **16.099 pares de traducción**, de ellos 1.280 patrones con variables (registro de combate, tooltips con números, composiciones de nombres). Sin cadenas pendientes de traducir ni patrones en cuarentena.
- **Capa de interfaz**, para las pantallas que el juego dibuja en JavaScript y no pasan por Rosetta, con 39 módulos del juego traducidos: menú principal, opciones, pantalla de personaje, diálogos de ciudad, obituario y resultado de combate.
- **Hooks propios** (código que intercepta una función del juego para traducir lo que muestra) para las pantallas cuyo texto no pasaba por Rosetta: negociación de contratos, ambiciones, taberna, séquito, puerto, diálogos del combate táctico y otras.
- **Texto revisado entero** desde la traducción de la comunidad: corrimientos de listas realineados, un censo a ciegas de las tablas de nombres, registro unificado en español neutro y un glosario fijo. El detalle está en la [historia del proyecto](https://github.com/backmind/battle-brothers-es/blob/main/docs/HISTORIA.md).
- **La pantalla de ajustes de MSU en español**, con una página propia del pack: versión, estado de verificación, créditos y enlaces.
- **Seis pasadas de verificación en partida**, con el registro del juego revisado en cada una.

[1.0.0]: https://github.com/backmind/battle-brothers-es/releases/tag/1.0.0
