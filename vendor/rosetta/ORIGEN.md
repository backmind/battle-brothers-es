# Rosetta, vendorizado

Copia mínima del framework [Rosetta](https://github.com/Suor/battle-brothers-rosetta) de Alexander Schepanovski (hackflow; Suor en GitHub), metida dentro de este repositorio (vendorizada) bajo su licencia BSD (`LICENSE` en esta carpeta).

Origen: tag `0.5.0`, commit `dde98e9`. Solo están las piezas que necesitan las herramientas del pack, con la misma estructura relativa que en el repo original:

- `rosetta.py`: el extractor. `build_dist.py` usa su parser.
- `scripts/!mods_preload/!rosetta.nut`: el runtime, para las sondas con Squirrel y el chequeo de deriva.
- `mocks.nut`: lo que el runtime necesita para cargar fuera del juego.
- `rosetta/hooks.nut` y `rosetta/pack_ru.nut`: el runtime los carga al arrancar. Además, el medidor de cobertura cruza los conductos de `hooks.nut` con los del pack.

**El jugador no usa nada de esto.** Instala Rosetta desde [Nexus](https://www.nexusmods.com/battlebrothers/mods/802), y los zips del pack no llevan código de Rosetta.

**Para adoptar una versión nueva:** copiar estos ficheros desde el repo de Rosetta en la etiqueta nueva, actualizar el origen de arriba y pasar `es_pack/tools/check_upstream_drift.py`, que avisa si la versión nueva toca algo de lo que el pack replica. Aquí no se edita nada a mano.
