# Registro de guiños del corpus, CERRADO el 25/08/2026

Un guiño es un homenaje que el equipo de la traducción original sembró a propósito en el texto: un nombre de otra franquicia en lugar del literal inglés, o un detalle de sabor añadido a la prosa. Decisión del propietario en sesión interactiva del 25/08/2026: **el catálogo entero se conserva en bloque, a propósito**. Este fichero existe por lo mismo que `CENSO_CIEGO.tsv` (el registro del censo a ciegas de las tablas de nombres): para que ninguna auditoría futura "corrija" un guiño deliberado. Ante una entrada de esta lista, la regla es no tocarla, y ante la duda, buscarla antes de nada en este fichero y en `CENSO_CIEGO.tsv`.

Al cerrar, el propietario puso una condición, la **coherencia en las referencias**: si un nombre sustituido apareciera mencionado dentro de otro par, el `es` de ese par debe conservar el guiño. El barrido se hizo el mismo día sobre los 39 nombres sustituidos y no encontró ninguna referencia cruzada en el lado `en` de otros pares (las tablas de generador no se citan en la prosa), así que hoy la condición se cumple por vacuidad. Si el corpus crece, hay que repetir el barrido (`es_pack/tools/coherencia_guinos.py`).

Lo que ya se resolvió antes del censo, para no volver a decidirlo: MC Hammer eliminado, el título de la misión del Rey Bárbaro es "El Rey Bárbaro" y solo queda "el Matarreyes" opcional, las tildes de las monedas antiguas corregidas, Krumburg ya no es duplicado ("Torreón del Estuario") y Quadim se quedó "Lanza del Sol" al resolver el duplicado con Grafenschein. El himno argentino de la pintura azul y blanca se **conserva** por decisión del 25/08, con la coma vocativa corregida ("Oíd, mortales, el grito sagrado...").

## Sustitutivos (nombre de otra franquicia u obra en lugar del literal)

| en | es | referencia |
|---|---|---|
| Sorrel | Jaskier | The Witcher; el TSV lo marca "el guiño canónico, no tocar" |
| Gla-Oth the Endless Maw | Kayran el Devorabarcos | The Witcher |
| Schwarzmark / Muckenmark / Torfmark | Flotsam / Vergen / Loc Muinne | The Witcher |
| Wolkenstein | Mahakam | The Witcher |
| Wargasharak | Barad-Dur | Tolkien |
| Vras Ushtar | Barad' Dur | Tolkien; la grafía distinta de Wargasharak es deliberada y está anotada en el TSV |
| Thrak Talun | Naz' Gul | Tolkien |
| Maruk Blot | Bal Guldur | Tolkien (Dol Guldur) |
| Dunspike | Púaoscura | Tolkien (Montaña Solitaria) |
| Blankenfeste | Pyke | Juego de Tronos |
| Kampfeste | Desembarco del Caballero | Juego de Tronos |
| Grunfeste | Roca Caster | Juego de Tronos (forma truncada de Casterly Rock, anotada) |
| Blankenstadt | Puerto Blanco | Juego de Tronos |
| Holnisland | Aguasdulces | Juego de Tronos (Riverrun) |
| Brammingborg | Castillo Negro | Juego de Tronos |
| Gunnborg | Winterfell (sin traducir) | Juego de Tronos; cerrado en tanda el 24/08 |
| Hammarborg / Groneborg | Último Hogar / Invernalia | Juego de Tronos; asignación editorial del 24/08 anotada en el corpus |
| Haellborg | Bastión de Cerwyn | Juego de Tronos |
| Halshovel | Torreón de Crasterr | Juego de Tronos (la doble erre es del traductor) |
| Quadim | Lanza del Sol | Juego de Tronos (Sunspear) |
| Skjoldwold | Hornwood | Juego de Tronos |
| Sir Erkenbrand / Sir Silvan / Sir Burkhard | Ser Jaime / Ser Aegon / Ser Dunk | Juego de Tronos, con la grafía "Ser" de la saga |
| Grudgebringers | Los Rencorosos | Juego de Tronos (Second Sons) |
| Antlerfold | Bosque de los Cien Acres | Winnie the Pooh |
| Amira / Ibn Sahr | Altair / Ibn Laha'ad | Assassin's Creed |
| Grunlandfeste | Praven | Mount and Blade |
| Hoberfeste / Feldfeste | Windsor / Warwick | castillos ingleses reales |
| Gelbburg | Guarida de Ornlu | confirmado deliberado por verdad de terreno |
| Finsterwall | Fuerte Greenkeep | ambiguo, se lee como nombre compuesto autónomo |
| Oswald / Skarbrand / Warshout | Reginhard / Ragnarr / el Espadachín Negro | sustituciones del traductor sin franquicia, misma clase que Jaskier |

## Aditivos (sabor añadido a la prosa, sin franquicia o con ella)

Son la ballesta pesada (la prohibición "injusta, cobarde y profana"), la daga rondel (el visor del casco), el sombrero de duelista, las monedas de oro antiguas ("¿Orens? ¿Florines?...", guiño a The Witcher), "rómpete una pierna" (Broken Leg), los tornillos del cultista, el acento campechano del peón de granja, el juego de cartas "Went" (Gwent, de The Witcher) y la flecha en la rodilla (Skyrim). A ellos se suman los siete añadidos de la traducción fan verificados carácter a carácter contra la fuente: las justas, el ladrón de melones, los dados con %gambler%, el cultista resucitado, el hombre pájaro, la troupe con la Casa Kaltenborn y la canción "Ved al carnicero arder" del trovador.
