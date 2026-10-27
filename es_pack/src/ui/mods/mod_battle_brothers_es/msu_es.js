// Textos de MSU que van escritos en su JS y no pasan por Rosetta: la cabecera
// y los botones de la pantalla de ajustes, y el botón "Mod Options" de los
// menús. No sustituye ningún fichero de MSU: envuelve sus métodos y cambia
// los textos después.
//
// Si una versión nueva de MSU renombra algo de lo que se toca aquí, el
// envoltorio no se instala o su retoque falla en silencio: MSU sigue
// funcionando igual y esos textos vuelven a salir en inglés. Nunca al revés.
(function ()
{
	var subtitulo = 'Elige un mod de la lista';

	// Envuelve _obj[_nombre] para correr _despues tras el original. Si el
	// método no existe, no hace nada; si _despues falla, lo traga.
	var envuelve = function (_obj, _nombre, _despues)
	{
		if (_obj === undefined || typeof _obj[_nombre] !== 'function') return;
		var original = _obj[_nombre];
		_obj[_nombre] = function ()
		{
			var ret = original.apply(this, arguments);
			try { _despues.apply(this, arguments); } catch (e) {}
			return ret;
		};
	};

	if (typeof ModSettingsScreen !== 'undefined')
	{
		var pantalla = ModSettingsScreen.prototype;

		envuelve(pantalla, 'createDIV', function ()
		{
			this.mDialogContainer.findDialogTitle().html('Ajustes de mods');
			this.mDialogContainer.findDialogSubTitle().html(subtitulo);
			this.mContainer.find('.main-cancel-button').changeButtonText('Cancelar');
			this.mContainer.find('.main-reset-button').changeButtonText('Restablecer');
			this.mContainer.find('.main-apply-button').changeButtonText('Aplicar');
			// "Save" guarda y cierra (MSU lo llama OK): con "Aplicar" al lado,
			// la convención de los diálogos en castellano es "Aceptar".
			this.mContainer.find('.main-save-button').changeButtonText('Aceptar');
		});

		envuelve(pantalla, 'hide', function ()
		{
			this.mDialogContainer.findDialogSubTitle().html(subtitulo);
		});

		// La ficha del pack son títulos de MSU con párrafos dentro. MSU da a
		// cada título una fila de 4rem fija (los párrafos se montarían) y un
		// tooltip con su nombre (enseñaría el HTML): se ajusta la fila y se
		// quita el tooltip. Solo en la página de este pack.
		envuelve(pantalla, 'switchToPage', function (_panel)
		{
			if (_panel.id !== 'mod_battle_brothers_es') return;
			this.mActiveSettings.forEach(function (element)
			{
				if (!(element instanceof TitleSetting)) return;
				element.title.unbindTooltip();
				element.unbindTooltip = function () {};
				if (element.title.find('.es-parrafo').length > 0)
					element.layout.css({ 'height': 'auto', 'margin': '0.6rem 0' });
			});
		});
	}

	// El botón "Mod Options" lo crea addModOptionsButton con el texto escrito
	// en JS. Mientras corre, createTextButton cambia ese rótulo y nada más.
	// El del menú principal ya está dibujado cuando el juego carga este
	// fichero, así que ése se renombra aquí mismo; los menús de partida y de
	// combate se crean después y los cubre el envoltorio.
	try
	{
		$('.ui-control .label').filter(function () { return $(this).text() === 'Mod Options'; })
			.html('Ajustes de mods');
	}
	catch (e) {}

	if (typeof MainMenuModule !== 'undefined'
		&& typeof MainMenuModule.prototype.addModOptionsButton === 'function')
	{
		var addModOptionsButton = MainMenuModule.prototype.addModOptionsButton;
		MainMenuModule.prototype.addModOptionsButton = function ()
		{
			var createTextButton = $.fn.createTextButton;
			$.fn.createTextButton = function (_text)
			{
				var args = Array.prototype.slice.call(arguments);
				if (_text === 'Mod Options') args[0] = 'Ajustes de mods';
				return createTextButton.apply(this, args);
			};
			try { return addModOptionsButton.apply(this, arguments); }
			finally { $.fn.createTextButton = createTextButton; }
		};
	}
})();
