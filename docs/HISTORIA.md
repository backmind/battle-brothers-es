# Historia del proyecto

De dónde viene el texto de [Battle Brothers en Español](../README.md) y qué se hizo con él para llevarlo a Rosetta.

## De dónde viene el texto

Este pack adapta la [Traducción completa al Castellano](https://www.nexusmods.com/battlebrothers/mods/640) de NexusMods, un trabajo comunitario de años que reunió más de medio millón de palabras traducidas. La escribieron MagnusLioncaster, Hjensikk, AMarauder y ElGranFoca, que además la mantuvo al día con cada parche del juego y la reconstruyó en su serie 3.x, la base de la que partimos (en concreto el árbol de enero de 2026; por qué no se adoptó en bloque la revisión posterior está medido y razonado en [FUENTE-305.md](../es_pack/corpus/FUENTE-305.md)).

Sin esa traducción previa este pack habría tardado años en existir. Sus autores dieron permiso expreso para usar aquí su contenido, incluida la capa de interfaz, y la mejor forma de agradecérselo es pasarte por [su página de Nexus](https://www.nexusmods.com/battlebrothers/mods/640) y dejarles tu endorse.

Aquella traducción sustituía los archivos del juego, así que cada parche oficial la rompía y obligaba a rehacerla. Este pack la mueve a Rosetta para que sobreviva a los parches.

## Lo que ha hecho este proyecto

Migrar medio millón de palabras entre dos sistemas de traducción incompatibles obliga a alinear cada frase inglesa con su castellano, y el alineamiento automático se equivoca de formas silenciosas. La más traicionera es el corrimiento: cuando una versión del juego añade o quita una entrada de una lista, todo lo que va detrás se desplaza una posición y cada texto acaba luciendo la traducción del vecino. Cada línea del archivo parece correcta por separado, y solo en partida se ve que los Lindwurms se llaman "Trols".

Contra eso se construyeron instrumentos a medida. Una auditoría anclada compara el corpus (el archivo con todos los pares inglés-español del pack) con el árbol de la traducción original como verdad de terreno y busca la firma exacta del corrimiento; unos detectores de ventanas, que examinan los pares vecinos de cada hallazgo, lo amplían hasta sus fronteras reales; y un medidor de cobertura ejecuta el emparejador real de Rosetta sobre los textos extraídos del juego, con el resultado de que, al publicar la 1.0.0, el pack cubría el 100 % de las frases que el jugador puede leer. Con esos instrumentos se realinearon más de 1.700 pares.

El texto pasó además dos revisiones completas de otra naturaleza. Un barrido semántico recorrió el corpus entero en una docena larga de sesiones y dejó cientos de correcciones puntuales. Y un censo a ciegas juzgó una a una 1.114 entradas de las tablas de nombres, sin mirar la referencia para no heredar sus vicios, con sus veredictos registrados en [CENSO_CIEGO.tsv](../es_pack/corpus/CENSO_CIEGO.tsv); ese registro protege también los guiños y homenajes que sembró el equipo original, que siguen todos ahí.

La revisión editorial unifica el registro en español neutro. El "vosotros" pasa a tuteo y a "ustedes", así que "¿podéis ayudarme?" queda en "¿pueden ayudarme?" y "vuestro capitán" en "su capitán". El léxico marcado como peninsular se sustituye por equivalentes neutros, de modo que "chaval" queda en "muchacho" y "vale" en "de acuerdo". Un glosario fijo mantiene una sola traducción por término, para que la misma criatura o la misma arma se llame igual en todas partes. Se conserva el habla propia de los personajes que la tienen, y unos usos de "usted" que caracterizan a alguien concreto frente al capitán.

Battle Brothers se juega en todo el ámbito hispanohablante y un texto sin marcas regionales le llega a más gente. Con el vocabulario fijado también se lee mejor, porque aprendes cómo se llaman las cosas y dejas de tropezar con tres nombres para lo mismo.

Hubo también trabajo de ingeniería que acabó beneficiando a más gente que a este pack. Los textos con variables se convirtieron al formato de patrones de Rosetta, y la cuarentena (los pares que el script de empaquetado aparta porque su patrón aún no es válido) bajó de 957 a cero. Se escribieron hooks propios, código que intercepta una función del juego para traducir lo que muestra, en pantallas cuyo texto ni siquiera pasaba por el framework; varios de ellos se ofrecieron aguas arriba, al repositorio de Rosetta, y forman ya parte de Rosetta 0.5.0. Múltiples pasadas de QA (control de calidad jugando una partida), con el registro del juego revisado en cada una, destaparon defectos que ningún análisis del archivo habría visto. Al publicar la 1.0.0, cada cadena del juego tenía dueño: estaba traducida, tenía su patrón, estaba adjudicada como clave interna que el juego nunca muestra, o estaba bloqueada aguas arriba con su incidencia abierta.

Esta es la razón por la que este proyecto, llevado adelante por una sola persona, ha tardado diez meses en publicarse.