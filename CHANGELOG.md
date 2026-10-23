# Cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). El pack numera sus versiones con [versionado semántico](https://semver.org/lang/es/), independiente de la versión del juego.

## [5.0.0-beta.1] - sin publicar

- **Traducción de Legends** (19.4.22), en beta.

## [4.0.1] - 2026-10-21

- **El juego podía quedarse congelado al mostrar un texto largo en inglés que el pack no conoce**, sobre todo con mods como Legends: un evento de Legends tardaba más de 14 minutos en pasar por la traducción. Varias reglas del pack (las de «X has Y», «X had Y», «X's Y» y parecidas) prueban a traducir el resto de la frase para saber si les toca, y ese resto vuelve a casar con ellas; con cada «has» o «had» más el trabajo se multiplicaba. Una frase de 86 caracteres con doce de ellos ya costaba 15 segundos, y volver a pasar por la traducción el tooltip de la moral, ya en castellano, 4. Ahora el pack recuerda lo que ya tradujo mientras dura cada texto: las traducciones son exactamente las mismas, y el peor texto de Legends tarda menos de dos décimas de segundo.
- **El tipo de daño que MSU añade a los tooltips de habilidad salía en inglés** («Inflicts Cutting Damage»). Ahora dice «Inflige daño cortante», «perforante», «contundente» o «de fuego», y en las habilidades con dos tipos, cada uno con su porcentaje.
- **El título de la presentación de la partida decía «The» delante del nombre de la compañía** («The Los Focalistas»). Ahora sale solo el nombre, como en el texto.
- **El trasfondo Executioner es «Verdugo»**, como en su descripción; decía «Ejecutor».
- **Aketon Cap es «Gorro de aketon»**, a juego con la «Capucha de aketon»; decía «Sombero de cuero».
- **Frases inglesas que salían a medias con «deja a» o «se une a».** Dos reglas de los eventos de deserción y compañía se comían cualquier frase con «leaves the» o «joins the». Ahora solo se traduce la que acaba en el nombre de tu compañía.
- **«Ventaja» en todo el juego** para los perks, como el resto del texto: el botón y el árbol de la pantalla de personaje, los puntos de ventaja, las ambiciones y los consejos decían «habilidad», «beneficio» o «pericia».
- **Términos unificados:** «troles» (el plural regular) en lugar de «trols» y «trolls», «necrófago» para ghoul, el rasgo «Ojos de águila» como el apodo «Ojo de águila», «cuentacoronas» para Crownling (había cuatro formas distintas), «no muerto» siempre sin guion y Billman es «soldado de guja», como su arma, en lugar de «piquero».
- **Erratas:** «Laureles antiguos», «Regente en ausencia» (decía «en Absenta»), «Poción de segundo aliento» y la «Pasiva de trol».
- **Unos 500 textos de eventos y contratos repasados contra el inglés**, a partir de las notas que dejó la revisión del corpus de Legends: erratas, frases rotas o a medias, sentidos cambiados, calcos y concordancias. Donde la traducción había suavizado el original, recupera su crudeza, como pide la línea del pack. «Sellsword» se dice «mercenario» y «lieutenant», «teniente». Los guiños de la traducción anterior que recoge `GUINOS.md` se quedan como estaban.
- **Textos que mezclaban una frase traducida con un nombre en inglés**: «Mantén el Oath of Valor», «Brigands pasaron recientemente por aquí» en las huellas del mapa, «Reputación: Saintly», «...un ataque normal de Thrust» en Muro de lanzas y la reconstrucción de un lugar cercano. La ventana para ampliar el inventario del séquito salía entera en inglés. Ahora todo sale en castellano: «Mantén el Juramento de Valor», «Bandidos pasaron...», «un Lanzazo normal».
- **La reputación «Cruel» salía en minúscula** en la pantalla de relaciones.
- **«Tú y tus hombres se ganan la vida»** y otras 79 frases con «tú y» más un verbo en plural se reescriben con «tú» como sujeto: «Con tus hombres te ganas la vida», «Necesito que flanquees a sus cañoneros con tus hombres». El pack sigue en castellano neutro, pero esa construcción sonaba muy forzada.
- La descripción del origen Cazadores de bestias cabe en su columna sin que la última línea quede a ras.
- Dos opciones de evento que no cabían en su botón (el soldado retirado y el monje viajero). El chequeo `ANCHO` mide ahora todas las opciones de evento y contrato si tiene delante el código descompilado del juego.

## [4.0.0] - 2026-10-18

El mismo contenido que la 1.0.1, con la numeración nueva. La traducción pasa a publicarse también en la página de Nexus de la traducción anterior, que llegó a la 3.0.4, así que el pack continúa su numeración: la 4 es el cambio de base a Rosetta. Las 1.0.0 y 1.0.1 fueron las dos primeras versiones de este repositorio.

## [1.0.1] - 2026-10-18

- **Botones que no cabían.** Los de elegir juramento o ambición se cortaban por los dos lados, porque los botones de evento no parten línea y el castellano había perdido el salto de línea del inglés. Recuperan el salto y se condensan hasta caber, dejando aire al icono, junto con 18 opciones de evento y contrato y las descripciones de origen de la nueva partida que se salían de su columna o quedaban a ras (Cazahombres, Juramentados, Desertores, Cazadores de bestias y otras).
- **Un «[color]» suelto en la presentación de algunos contratos y eventos** (buscar un lugar, el asalto con ariete, los desertores sobornados, el juglar): el castellano había perdido el cierre de un bloque de diálogo.
- **«Cazahombres»** en toda la narrativa, como el origen y el trasfondo.
- **El último párrafo del final de partida salía en inglés** al retirarse («Now you're sitting in a tavern by yourself...»): al construir cada trozo del texto, el pack le quitaba también los saltos de línea iniciales, y con ellos la traducción ya no casaba. Afecta a los ocho párrafos de cierre de los finales.
- **Textos que el juego compone por partes y salían en inglés**: la presentación de los combates de la arena y del torneo, la elección de campeones contra los Juramentadores, la lista de asentamientos por visitar, el primer párrafo de las ambiciones de visitar asentamientos y de reunir provisiones, y el recuento de combates de los luchadores de la arena cuando son uno o los ganaron todos.
- **Algunas mejoras de los eventos salían mal compuestas** («Hackett ahora es Deathwish», lo mismo con Pulmones de hierro, la experiencia de entrenamiento y la Fatiga): una regla genérica de «X gains Y» se adelantaba a la suya, y convertía en «ahora es» cualquier frase sin traducir que dijera « gains ». Ahora hay una regla por cada rasgo que pueden dar los dos eventos del anatomista.
- **Dos rumores de taberna salían a medias** («Desde what I've heard...»): una regla de otro texto se les adelantaba.
- **«Habilidad cuerpo a cuerpo»** en el rótulo del atributo, que decía «Habilidad a cuerpo a cuerpo».
- **Doce órdenes en vosotros** («Decidles», «Degolladlos») pasan a ustedes, como el resto del texto.
- **Hedge Knight es siempre «caballero errante»**; en tres eventos y en el origen Lobo solitario decía «caballero andante».
- **Cleaver es siempre «cuchilla»**, como la clase de arma: «Cuchilla de carnicero», «Cuchilla de guerra», «Dominio de la Cuchilla», el apodo «el Cuchilla» y el nombre al azar de las armas con nombre, que decía «Navaja». «Navaja» pasa a Razor y Warblade es «Hoja de guerra».
- Los textos fijos marcados como patrón se instalan como texto literal, para que ninguna regla se les adelante.
- Dos chequeos nuevos: `ANCHO` mide con la fuente del juego, calibrada en partida, los botones de ambición y las descripciones de origen; `ETIQUETAS` avisa de las variantes de un texto que dejan sin pareja un color, una negrita, una cursiva, un subrayado o una llave.

## [1.0.0] - 2026-10-17

Primera versión publicada. Verificada contra Battle Brothers 1.5.2.3 con todas sus expansiones, y requiere Rosetta 0.5.0 o superior.

- **16.099 pares de traducción**, de ellos 1.280 patrones con variables (registro de combate, tooltips con números, composiciones de nombres). Sin cadenas pendientes de traducir ni patrones en cuarentena.
- **Capa de interfaz**, para las pantallas que el juego dibuja en JavaScript y no pasan por Rosetta, con 39 módulos del juego traducidos: menú principal, opciones, pantalla de personaje, diálogos de ciudad, obituario y resultado de combate.
- **Hooks propios** (código que intercepta una función del juego para traducir lo que muestra) para las pantallas cuyo texto no pasaba por Rosetta: negociación de contratos, ambiciones, taberna, séquito, puerto, diálogos del combate táctico y otras.
- **Texto revisado entero** desde la traducción de la comunidad: corrimientos de listas realineados, un censo a ciegas de las tablas de nombres, registro unificado en español neutro y un glosario fijo. El detalle está en la [historia del proyecto](https://github.com/backmind/battle-brothers-es/blob/main/docs/HISTORIA.md).
- **La pantalla de ajustes de MSU en español**, con una página propia del pack: versión, estado de verificación, créditos y enlaces.
- **Seis pasadas de verificación en partida**, con el registro del juego revisado en cada una.

[4.0.1]: https://github.com/backmind/battle-brothers-es/releases/tag/4.0.1
[4.0.0]: https://github.com/backmind/battle-brothers-es/releases/tag/4.0.0
[1.0.1]: https://github.com/backmind/battle-brothers-es/releases/tag/1.0.1
[1.0.0]: https://github.com/backmind/battle-brothers-es/releases/tag/1.0.0
