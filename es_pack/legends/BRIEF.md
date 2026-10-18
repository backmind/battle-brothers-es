# Traducir un lote de Legends

Instrucciones para quien traduzca un lote de `es_pack/legends/lotes/`, sea una persona o un agente. El lote es un trozo del corpus `es_pack/corpus/mod_legends_es.nut` con los pares pendientes de unos cuantos ficheros de Legends, y se devuelve al corpus con `lotes.py fusionar`, que lo rechaza entero si algo está mal.

## Qué recibes y qué entregas

Recibes `NNNN.nut`. Lo editas en el sitio y no tocas nada fuera de él: ni el corpus, ni el `NNNN.orig.nut`, ni otros lotes.

La cabecera trae el número de lote, la versión de Legends y, bajo `// GLOSARIO:`, los términos que aparecen en el lote con la traducción fijada. Cada par lleva encima su `// FILE:` (el fichero de Legends del que sale) y su `// context:` (la ruta de código que lo usa: `create.m.Name` es un nombre, `Options.Text` un botón de evento, `m.Description` una descripción). Si Legends retocó un texto del juego base, el par lleva además `// base: en="..." es="..."` con el texto original y su traducción de la 1.0: parte de ella, cambia lo que cambió el inglés y corrige lo que la 1.0 tenga mal frente al inglés (sentido, añadidos que el inglés no tiene, crudeza rebajada, erratas). Cada corrección se anota dentro del bloque, antes del `en`, con una línea `        // corrige base: ...` que diga qué y por qué, para llevarla después a la 1.0.

Con cada par puedes hacer cuatro cosas, y nada más:

1. **Rellenar `es`.**
2. **Convertir una pista del extractor en patrón.** Si el `en` lleva expresiones de código entre `<...>` (`<this.m.Name> attacks`), reescríbelo como `mode = "pattern"` con capturas válidas (`<name:str> attacks`, y en el `es` solo `<name>`). Es el único caso en que el `en` cambia.
3. **Marcar una cadena interna.** Si el texto no se muestra nunca (un identificador de pantalla como `Nest1`, una clave), sustituye el bloque entero por una línea `    // en = "<el en tal cual>"  // motivo`, con el motivo detrás, en la misma línea.
4. **Dejar una duda.** Si no lo tienes claro (dos sentidos posibles, un término que el glosario da como `(pendiente)`, un posible guiño), deja `es = ""` y añade dentro del bloque, antes del `en`, una línea `        // DUDA: ...` que diga qué dudas. Mejor una duda anotada que una traducción adivinada.

## Reglas

Las reglas que no se pueden romper, los textos con variables y el estilo están en [CONTRIBUTING.md](../../CONTRIBUTING.md): «Reglas que no se pueden romper», «Los textos con variables» y «Estilo». Léelas antes del primer lote. La fusión comprueba las formales (tokens, `[img]`, `[color]`, variantes con ` | `, capturas) y rechaza el lote con una sola que falle.

## Criterio

- Traduce con el inglés delante y el contexto a la vista. Un texto de botón no se traduce igual que una descripción.
- Antes de inventar, busca en `es_pack/corpus/base_es.nut` cómo se dijo lo mismo en el juego base. Legends reutiliza mucho vocabulario del base y tiene que sonar al mismo juego.
- Los términos del glosario de la cabecera se usan tal cual, sin sinónimos. Si un término aparece como `(pendiente)`, deja una duda.
- En textos de interfaz (botones, nombres, etiquetas), longitud parecida a la del inglés: el hueco es el mismo.
- Respeta el registro del personaje que habla. La voz del corpus es americana (tuteo y "ustedes", nunca "vosotros") y se conserva la crudeza del original sin rebajarla.
- Los nombres de pila y los topónimos inventados (Ottmar, Wiesendorf, Urug Wargash) se dejan como están. Lo que tiene significado transparente en inglés se traduce: epítetos ("the Pious", "el Piadoso"), lugares descriptivos ("Dark Vault", "Cripta oscura"), nombres de objetos ("Warblade", "Cuchilla de guerra").

## Vocabulario de mecánica

Lo que la 1.0 fijó y el glosario automático no recoge, porque el juego lo escribe casi siempre en minúscula:

| Inglés | Español |
|---|---|
| Hitpoints | Puntos de vida |
| Crowns | coronas |
| Damage | daño |
| Experience | experiencia |
| Renown | renombre |
| Morale | moral |
| Armor | armadura |
| Resolve | Resolución |
| Initiative | Iniciativa |
| Action Points | Puntos de acción |
| Maximum Fatigue | Fatiga máxima |
| sellsword | mercenario |
| company | compañía |
| brother | hermano |
| retinue | séquito |
| contract | contrato |
| ambition | ambición |
| origin | origen |
| camp | campamento |
| Ammunition, Medicine, Tools | munición, medicina, herramientas |
| perk | talento |
| perk point | punto de talento |
| perk tree | árbol de talentos |
| skill | habilidad |

**"perk" es "talento"**, nunca "habilidad", "ventaja", "pericia" ni "beneficio", aunque la 1.0 los usara: "habilidad" es "skill", y en Legends los dos conviven en el mismo tooltip.

## Sutilezas ya verificadas

- **Enclíticos, por sus dos lados.** Lleva tilde si queda esdrújula o sobresdrújula (*ignóralo*, *míralo*, *cuéntamelo*) y no la lleva si queda llana (*dime*, *hazlo*, *vete*, *dilo*, *dame*).
- **Formas con dos análisis.** Antes de corregir una forma, mira qué la rige: *jactase* es subjuntivo legítimo ("si él se jactase"), pero tras preposición va el infinitivo ("terminó de jactarse").
- **Falsos amigos que en este corpus resultaron correctos**, verificados uno a uno: *large* (traducía "long"), *rope* ("clothes"), *rest* ("the rest of"), *attend*, *notice*, *discuss*, *character*, *argument*, *condition*, *ultimate*, *convenient*, *miserable*.
- **Anglicismos decididos.** *Apparently* abriendo oración es "por lo visto" o "al parecer"; *aparentemente* solo traduce *seemingly*. *Assume* es "suponer". *Ignorar* en el sentido de no hacer caso se queda, salvo donde se confunda con desconocer.

## Género

Legends escribe los pronombres de sus personajes con tokens que el juego sustituye por palabras inglesas: `%they%`, `%their_employer%`, `%person_dude%` y familia (la lista completa está en `mod_legends/config/z_legends_language.nut`). En español no sirven: "%their% sword" es "su espada".

Omite los tokens ingleses que en castellano no hacen falta ("%their% sword" es "su espada"); la fusión permite quitarlos. **Donde el castellano concuerde con el género** del personaje, usa los tokens castellanos que el pack añade a la tabla de Legends, en vez de dar un rodeo para evitarlo (sin género, el juego pone el masculino):

| Token | Hombre | Mujer | Ejemplo |
|---|---|---|---|
| `%o%` | o | a | `cansad%o%` |
| `%el%` | él | ella | `con %el%` |
| `%lo%`, `%Lo%` | lo | la | `%lo% mira` |
| `%un%`, `%Un%` | un | una | `%un% mercenari%o%` |
| `%hombre%`, `%Hombre%` | hombre | mujer | `%un% %hombre%` |
| `%art%`, `%Art%` | el | la | `%art% flagelante` |
| `%del%`, `%Del%` | del | de la | `las manos %del% erudit%o%` |
| `%al%`, `%Al%` | al | a la | `mira %al% erudit%o%` |
| `%ese%`, `%Ese%` | ese | esa | `%ese% %hombre%` |

Solo valen si el inglés del par lleva un token de pronombre del mismo personaje: si el inglés usa `%their_bro%`, el castellano usa `%o_bro%`; si usa `%their%`, `%o%`. No hay `%El%`: el juego no sabe poner en mayúscula la «é», y en castellano el sujeto casi siempre se omite. La fusión rechaza cualquier otro token que no esté en el inglés.

Un sustantivo que nombra a un personaje con género variable («el flagelante», «el monje», «el idiota») nunca lleva artículo ni demostrativo fijo: usa `%art%`, `%del%`, `%al%` o `%ese%`, con el sufijo del personaje, y concuerda también el resto de la frase («sosteniéndo%lo%»). Los tokens solo sirven con sustantivos cuyo femenino se forma con `%o%` (erudit%o%, mercenari%o%) o que son comunes en cuanto al género (el/la idiota, el/la flagelante, el/la guía). Si el femenino es otra palabra (monje/monja, historiador/historiadora, maestro de sabuesos), nombra al personaje por su token (`%monk%`) o usa una palabra común en cuanto al género, sin perífrasis largas.

Si el personaje no tiene tokens de género en el inglés del par (un recluta, un ladrón o un caballero nombrados solo por `%thief%`, `%hedgeknight%`), no puedes usar los castellanos, porque el juego no los rellena: redacta sin concordancia de género (sin artículo ni adjetivo marcado delante o detrás del personaje), salvo que la fuente fije su género (por ejemplo, `setStartValuesEx(..., true, 1)` crea siempre una mujer).

Los tokens con verbo de Legends (`%they're%`, `%they are%`, `%they were%` y familia) se quitan siempre: el castellano conjuga el verbo y omite el sujeto.

## Patrones

La guía de capturas y tipos es la de Suor: [AGENTS_TRANSLATING.md](https://github.com/Suor/battle-brothers-rosetta/blob/master/AGENTS_TRANSLATING.md). El runtime añade dos límites que la fusión comprueba: no puede haber dos capturas `str` pegadas en el `en`, y toda captura del `es` tiene que existir en el `en`. Si no ves cómo convertir una pista en un patrón válido, deja una duda.

## Lo que todavía no cubre el corpus

- Los ficheros `.js` de la interfaz de Legends: el extractor solo lee `.nut`.
- 19 cadenas sueltas en 8 ficheros que el extractor de Rosetta 0.5.0 no sabe leer.
- Las descripciones de perks pasan en partida por `::Legends.tooltip()`, que sustituye marcadores como `%passive%` y les añade texto; hay que comprobar en el juego que el par traducido llega a aplicarse.
- Traducir nombres de objetos, trasfondos o lugares como literal global puede romper mecánicas de Legends que comparan nombres (lo ha documentado la traducción al japonés, `SUSANO-OOO/battle-brothers-jp`). Antes de fusionar lotes de nombres hay que comprobar cuáles admiten traducción global.
