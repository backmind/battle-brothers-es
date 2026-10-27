// La línea del pack bajo el aviso del menú principal (el de abajo a la
// derecha). Sale con cualquier aviso: el de vanilla (siempre el mismo, los DLC
// no lo cambian) o el de Legends, que lo sustituye. Se añade DESPUÉS de que el
// aviso se pinte, así que da igual el orden en que se envuelva setMOTD: si
// legends_es.js lo traduce antes o después, la línea va siempre al final.
//
// VERSION tiene que coincidir con la del pack: lo comprueba test_build_dist.
(function ()
{
	var VERSION = '5.1.0';
	var linea = 'Juegas con Battle Brothers en Español ' + VERSION + '. ¡Gracias por jugar en castellano!';

	var pon = function ()
	{
		var motd = $('.motd');
		if (motd.length === 0) return;
		motd.find('.es-motd').remove();
		motd.append($('<div class="es-motd"/>').css({ 'margin-top': '1.0rem' }).text(linea));
		// Legends da al recuadro un alto fijo (12.4rem) que su bienvenida ya
		// llena: la línea quedaba fuera. Anclado por abajo, crece hacia arriba.
		motd.closest('.motd-container').css({ 'height': 'auto' });
	};

	if (typeof MainMenuScreen !== 'undefined' && typeof MainMenuScreen.prototype.setMOTD === 'function')
	{
		var setMOTD = MainMenuScreen.prototype.setMOTD;
		MainMenuScreen.prototype.setMOTD = function (_data)
		{
			var ret = setMOTD.apply(this, arguments);
			try { pon(); } catch (e) {}
			return ret;
		};
	}

	// El aviso ya está pintado cuando el juego carga este fichero. Con Legends,
	// legends_es.js lo repinta traducido al cargarse (y se lleva la línea): por
	// eso queda a mano para que lo llame tras repintar, y además se repone un
	// momento después, cargue antes o después que este fichero.
	window.BattleBrothersEsPortada = pon;
	try { pon(); } catch (e) {}
	setTimeout(function () { try { pon(); } catch (e) {} }, 500);
})();
