# Battle Brothers en Español

<!-- INSIGNIAS:INICIO (autogenerado por es_pack/tools/update_readme_metrics.py; no editar a mano) -->
[![Versión del pack](https://img.shields.io/github/v/release/backmind/battle-brothers-es?label=versi%C3%B3n&color=8b0000)](https://github.com/backmind/battle-brothers-es/releases/latest)
[![Verificada en Battle Brothers 1.5.2.3](https://img.shields.io/badge/verificada%20en-Battle%20Brothers%201.5.2.3-2e7d32)](#qué-se-traduce)
[![Última versión del juego en GOG](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fcontent-system.gog.com%2Fproducts%2F1590012242%2Fos%2Fwindows%2Fbuilds%3Fgeneration%3D2&query=%24.items%5B0%5D.version_name&label=%C3%BAltima%20del%20juego&color=1565c0)](https://www.gog.com/game/battle_brothers)
[![Battle Brothers y sus expansiones: 100 %](https://img.shields.io/badge/juego%20base%20%2B%20DLC-100%20%25-2e7d32)](#qué-se-traduce)
[![Descargas](https://img.shields.io/github/downloads/backmind/battle-brothers-es/total?label=descargas&color=555)](https://github.com/backmind/battle-brothers-es/releases)
<!-- INSIGNIAS:FIN -->

[![CI](https://github.com/backmind/battle-brothers-es/actions/workflows/ci.yml/badge.svg)](https://github.com/backmind/battle-brothers-es/actions/workflows/ci.yml)
[![Rosetta](https://img.shields.io/github/v/tag/Suor/battle-brothers-rosetta?sort=semver&filter=*.*.*&label=Rosetta&color=555)](https://github.com/Suor/battle-brothers-rosetta)
[![MSU](https://img.shields.io/github/v/release/MSUTeam/MSU?label=MSU&color=555)](https://github.com/MSUTeam/MSU)
[![Licencia](https://img.shields.io/badge/licencia-por%20piezas-555)](#licencias)

Traducción al español de Battle Brothers, de todas sus expansiones y, poco a poco, de sus mods: eventos, contratos, combate, interfaz y tooltips, en español neutro para todo el ámbito hispanohablante. No toca ningún archivo del juego, así que un parche no la rompe.

![Negociación de un contrato, en español](es_pack/media/contrato.png)

[Capturas](docs/CAPTURAS.md) · [Historia del proyecto](docs/HISTORIA.md) · [Problemas conocidos](es_pack/corpus/KNOWN_ISSUES.md) · [Hoja de ruta](ROADMAP.md) · [Colaborar](CONTRIBUTING.md)

## Por qué existe

Battle Brothers es, en buena parte, un juego de leer: los contratos se negocian leyendo y los eventos son pequeños relatos, de los que el juego tiene cientos. La comunidad hispanohablante lleva años con una [traducción completa al castellano](https://www.nexusmods.com/battlebrothers/mods/640), pero sustituía los archivos del juego y cada parche la dejaba fuera de juego hasta que alguien la rehacía.

Este pack toma aquel texto, lo revisa entero, establece una línea editorial homogénea, lo completa y lo monta sobre [Rosetta](https://github.com/Suor/battle-brothers-rosetta). Rosetta es la clave: un framework que traduce los textos mientras juegas, desde la memoria, en lugar de reemplazar archivos. Si un parche trae frases nuevas, esas salen en inglés hasta que se traduzcan, y todo lo demás sigue en español. Cómo se hizo, con sus tropiezos, está en la [historia del proyecto](docs/HISTORIA.md).

## Qué se traduce

<!-- OBJETIVOS:INICIO (autogenerado por es_pack/tools/update_readme_metrics.py; no editar a mano) -->
| Qué | Estado | Verificada en | Frases cubiertas |
|---|---|---|---|
| Battle Brothers y sus expansiones | Disponible | Battle Brothers 1.5.2.3 | 100 % |
<!-- OBJETIVOS:FIN -->

Las traducciones de mods se irán sumando a esta tabla, cada una con su cobertura. La cobertura se mide contra el juego instalado con `measure_coverage.py`: cuenta las frases que el jugador puede leer y descarta las claves internas y las trazas de depuración. Los restos que el extractor toma por texto sin serlo (condiciones de código, trozos de frases que en partida llegan enteras, etcétera) están revisados uno a uno y listados en la propia herramienta.

Ninguna medida estática ve una pantalla cuyo texto no pase por Rosetta. Eso solo lo destapa jugar, y para eso están las [incidencias](https://github.com/backmind/battle-brothers-es/issues/new/choose).

## Instalación

Copia estos siete archivos `.zip` en la carpeta `data` del juego, tal cual, sin descomprimir ni renombrar. Está en `<instalación>\Battle Brothers\data` en GOG y en `<Steam>\steamapps\common\Battle Brothers\data` en Steam.

| | Archivo | Descarga |
|---|---|---|
| 1 | Modding Script Hooks | [Nexus](https://www.nexusmods.com/battlebrothers/mods/42) |
| 2 | Modern Hooks | [Nexus](https://www.nexusmods.com/battlebrothers/mods/685) |
| 3 | MSU, 1.6.0 o superior | [Nexus](https://www.nexusmods.com/battlebrothers/mods/479) |
| 4 | stdlib, 2.5 o superior | [Nexus](https://www.nexusmods.com/battlebrothers/mods/676) |
| 5 | Rosetta, 0.5.0 o superior | [Nexus](https://www.nexusmods.com/battlebrothers/mods/802) |
| 6 | `mod_battle_brothers_es_<versión>.zip`, la traducción | [Releases](https://github.com/backmind/battle-brothers-es/releases/latest) |
| 7 | `mod_battle_brothers_es_ui_<versión>.zip`, los menús y pantallas que el juego dibuja en JavaScript | [Releases](https://github.com/backmind/battle-brothers-es/releases/latest) |

Arranca el juego; no hay nada que configurar. Para comprobar que ha cargado, entra en **Ajustes de mods** desde el menú principal: en la lista sale «Battle Brothers en Español», con su versión y la del juego contra la que se verificó.

**Para actualizar**, borra los dos zips (`mod_battle_brothers_es_<versión>.zip` y `mod_battle_brothers_es_ui_<versión>.zip`) de la versión anterior y copia los nuevos. Cuando sale una versión nueva, MSU la anuncia en el menú principal.

**Para desinstalar**, borra esos dos zips. Las partidas guardadas siguen funcionando.

## Preguntas frecuentes

**¿Sirve para una partida ya empezada?** Sí. El juego guarda dentro de la partida algunos textos que genera al crearlos (biografías de hermanos ya contratados, descripciones de facciones), y esos se quedan en el idioma en que nacieron. Lo que se genere a partir de ahí saldrá en español.

**¿Steam o GOG?** Los dos. La traducción no depende de la tienda, solo de la versión del juego.

**¿Y con otros mods?** Rosetta traduce los textos por coincidencia exacta, así que lo que un mod reutilice del juego base sale en español y lo que añada de su cosecha se queda en inglés. Las traducciones de mods que vayan entrando en el pack aparecen en [Qué se traduce](#qué-se-traduce). No se ha probado a fondo con los mods grandes (Legends, Reforged); si encuentras algo raro, [cuéntalo](https://github.com/backmind/battle-brothers-es/issues/new/choose).

**¿Por qué siete archivos?** Cinco son el andamiaje que comparten muchos mods del juego, y probablemente ya tengas alguno. Los dos últimos son el pack: uno con el texto y otro con las pantallas que el juego dibuja en JavaScript, que son las únicas que no pasan por Rosetta.

**Ha salido una versión del juego y el pack dice otra. ¿Funciona?** Con total probabilidad: lo que la actualización cambie saldrá en inglés y el resto en español. Los badges de arriba comparan la versión verificada con la última publicada, y en cuanto se verifica la nueva se actualizan.

## El corpus en cifras

Las cifras del juego base y sus expansiones salen del corpus de este repositorio, y la CI comprueba en cada cambio que siguen al día.

<!-- METRICAS:INICIO (autogenerado por es_pack/tools/update_readme_metrics.py; no editar a mano) -->
| | |
|---|---|
| Pares distribuidos | 16.133 |
| De ellos, patrones con variables | 1.311 |
| De ellos, nacidos fuera de la extracción (composición, MSU, QA) | 967 |
| Pares por id (homógrafos) | 28 |
| En cuarentena de patrones | 0 |
| Sin traducir | 0 |
| Claves internas adjudicadas | 765 |
| Módulos de interfaz traducidos | 39 |
<!-- METRICAS:FIN -->

## Limitaciones conocidas

- **Los objetos legendarios** conservan su nombre en inglés. El juego los compone en marcha juntando dos listas, y Rosetta todavía no sabe traducir esa combinación ([Suor/battle-brothers-rosetta#6](https://github.com/Suor/battle-brothers-rosetta/issues/6)).
- **Los nombres de los mods** en la pantalla de ajustes de mods (Modding Standards & Utilities, Modern Hooks) se dejan en inglés a propósito: son su nombre propio.
- **Las frases nuevas de un parche** salen en inglés hasta que se traduzcan.
- **Un aviso de fuentes en el log** lo trae el propio juego, también sin mods, y es cosmético. Se silencia extrayendo `gfx/fonts/` de `data_001.dat` a `data/gfx/fonts/`.

El detalle está en [KNOWN_ISSUES.md](es_pack/corpus/KNOWN_ISSUES.md).

## Colaborar

Si ves un texto en inglés, una errata o una traducción mejorable, [abre una incidencia](https://github.com/backmind/battle-brothers-es/issues/new/choose) con una captura. No hace falta saber programar ni traer la corrección hecha. Para corregirlo tú, la guía está en [CONTRIBUTING.md](CONTRIBUTING.md), y el manual del mantenedor, con los builds y las herramientas, en [es_pack/README.md](es_pack/README.md).

## Créditos

- **Traducción original**: MagnusLioncaster, Hjensikk, AMarauder y ElGranFoca, autores de la [Traducción completa al Castellano](https://www.nexusmods.com/battlebrothers/mods/640). Sin sus años de trabajo este pack no existiría. Si te gusta, pásate por su página y déjales tu endorse.
- **Revisión, traducción y mantenimiento**: backmind. Revisión completa del texto heredado, traducción de todo lo que faltaba, revisión de la línea editorial y adaptación a Rosetta.
- **Framework**: [Rosetta](https://github.com/Suor/battle-brothers-rosetta), de Suor.

Si eres uno de los autores originales y quieres cambiar algo de la atribución o del uso de tu texto, abre una incidencia y se arregla cuanto antes.

## Licencias

El repositorio reúne piezas de autores distintos, y cada una conserva la suya:

- **Código propio** (herramientas, hooks del pack, CI): [MIT](LICENSE).
- **Texto de la traducción** (`es_pack/corpus/`): de sus autores originales, usado con su permiso expreso. No lleva licencia libre: no se puede reutilizar fuera de este proyecto sin permiso de sus autores, ni usar en mods de pago o con puntos de donación.
- **Capa de interfaz** (`es_pack/src/ui/`): ficheros del juego, propiedad de Overhype Studios, con los textos traducidos. Se distribuyen como es costumbre en los mods del juego, sin reclamar licencia sobre ellos.
- **Rosetta vendorizado** (`vendor/rosetta/`): de Suor, bajo su [licencia BSD](vendor/rosetta/LICENSE).

> *English: a Spanish translation of Battle Brothers and all its DLCs, built on Suor's [Rosetta](https://github.com/Suor/battle-brothers-rosetta) framework. Install the seven zips listed above into the game's `data` folder.*
