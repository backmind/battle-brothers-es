// Textos de Legends que van escritos en su JS y no pasan por Rosetta. Legends
// sustituye varios ficheros que este pack también sustituye (main_menu_module,
// new_campaign_menu_module...) y gana Legends, así que el menú y la pantalla
// de nueva campaña salían en inglés. Aquí no se sustituye ningún fichero: se
// envuelven los métodos de Legends y se cambian los textos después, con las
// mismas formas que los .js traducidos del pack, para que el juego base y
// Legends digan lo mismo. El modo de fallo es siempre el mismo: si Legends
// renombra algo, el envoltorio no se instala o su retoque falla en silencio y
// ese texto vuelve a salir en inglés; Legends sigue funcionando igual.
(function ()
{
	var propio = function (_obj, _clave) { return Object.prototype.hasOwnProperty.call(_obj, _clave); };
	var tr = function (_mapa, _texto) { return typeof _texto === 'string' && propio(_mapa, _texto) ? _mapa[_texto] : _texto; };

	// Envuelve _obj[_nombre] para correr _despues tras el original. Si el
	// método no existe, no hace nada; si _despues falla, lo traga.
	var envuelve = function (_obj, _nombre, _despues)
	{
		if (_obj === undefined || _obj === null || typeof _obj[_nombre] !== 'function') return;
		var original = _obj[_nombre];
		_obj[_nombre] = function ()
		{
			var ret = original.apply(this, arguments);
			try { _despues.apply(this, arguments); } catch (e) {}
			return ret;
		};
	};

	// Cambia el texto de los elementos hoja de _raiz que coinciden palabra por
	// palabra con una clave de _mapa. Lo que no está en el mapa no se toca.
	var retoca = function (_raiz, _selector, _mapa)
	{
		_raiz.find(_selector).each(function ()
		{
			var e = $(this);
			if (e.children().length === 0 && propio(_mapa, e.text())) e.html(_mapa[e.text()]);
		});
	};

	// Menú principal, de partida y de combate. Mientras corre _fn (conTextos),
	// los botones y el título de los diálogos que crea se traducen por _mapa.
	var menu = {
		'New Campaign': 'Nueva campaña',
		'Load Campaign': 'Cargar campaña',
		'Scenarios': 'Escenarios',
		'Options': 'Opciones',
		'Tutorial Videos': 'Videos tutoriales',
		'Credits': 'Créditos',
		'Quit': 'Salir',
		'Resume': 'Reanudar',
		'Save Campaign': 'Guardar campaña',
		'Retire': 'Retirarse',
		'Retreat': 'Retirarse',
		'Save & Quit': 'Guardar y salir',
		'Are you sure you want to retire from the company? This will permanently end your campaign and leave the men in charge.':
			'¿Seguro que quieres retirarte de la compañía? Tu campaña terminará para siempre y los hombres quedarán al mando.'
	};

	var conTextos = function (_mapa, _fn, _this, _args)
	{
		var crea = $.fn.createTextButton;
		var popup = $.fn.createPopupDialog;
		if (typeof crea === 'function')
			$.fn.createTextButton = function (_texto)
			{
				var args = Array.prototype.slice.call(arguments);
				args[0] = tr(_mapa, _texto);
				// El diálogo de "Retirarse" se crea al pulsar, ya fuera de _fn.
				if (_texto === 'Retire' && typeof args[1] === 'function')
				{
					var click = args[1];
					args[1] = function () { return conTextos(_mapa, click, this, arguments); };
				}
				return crea.apply(this, args);
			};
		if (typeof popup === 'function')
			$.fn.createPopupDialog = function (_titulo)
			{
				var args = Array.prototype.slice.call(arguments);
				args[0] = tr(_mapa, _titulo);
				return popup.apply(this, args);
			};
		try { return _fn.apply(_this, _args); }
		finally { $.fn.createTextButton = crea; $.fn.createPopupDialog = popup; }
	};

	if (typeof MainMenuModule !== 'undefined')
	{
		var modulo = MainMenuModule.prototype;
		['createMainMenuButtons', 'createWorldMapMenuButtons', 'createTacticalMapMenuButtons'].forEach(function (_nombre)
		{
			if (typeof modulo[_nombre] !== 'function') return;
			var original = modulo[_nombre];
			modulo[_nombre] = function () { return conTextos(menu, original, this, arguments); };
		});

		envuelve(modulo, 'createWorldMapMenuButtons', function ()
		{
			this.mButtonContainer.find('.is-map-seed').each(function ()
			{
				$(this).html($(this).html().replace('Map Seed:', 'Semilla:'));
			});
		});

		if (typeof modulo.createRetireDialogContent === 'function')
		{
			var contenido = modulo.createRetireDialogContent;
			modulo.createRetireDialogContent = function ()
			{
				var ret = contenido.apply(this, arguments);
				try { retoca(ret, '.row div', menu); } catch (e) {}
				return ret;
			};
		}
	}

	// El menú principal ya está dibujado cuando el juego carga este fichero.
	try { retoca($('.main-menu-module'), '.label', menu); } catch (e) {}

	// El aviso de abajo a la derecha (setMOTD, que Legends llama en connect).
	// También llega pintado antes que este fichero: se envuelve para las
	// siguientes veces y se repinta el que ya está.
	var motd = {
		'Welcome to Legends. \n\n To report bugs, share strategies and ideas, or try out new test builds, join us on https://discord.gg/ZfCHGuC':
			'Te damos la bienvenida a Legends. \n\n Para informar de errores, compartir estrategias e ideas o probar nuevas versiones de prueba, únete a nosotros en https://discord.gg/ZfCHGuC'
	};
	if (typeof MainMenuScreen !== 'undefined' && typeof MainMenuScreen.prototype.setMOTD === 'function')
	{
		var setMOTD = MainMenuScreen.prototype.setMOTD;
		MainMenuScreen.prototype.setMOTD = function (_data) { return setMOTD.call(this, tr(motd, _data)); };
		try
		{
			var pintado = $('.motd');
			Object.keys(motd).forEach(function (_en)
			{
				if (pintado.text().indexOf('Welcome to Legends.') !== 0) return;
				pintado.html(XBBCODE.process({ text: motd[_en], removeMisalignedTags: false, addInLineBreaks: true }).html);
			});
		} catch (e) {}
	}

	// Pantalla de nueva campaña. Sus rótulos son HTML a pelo dentro de
	// createDIV, y los botones de pie cambian de texto al navegar entre los
	// tres paneles con changeButtonText: se retocan los rótulos al acabar de
	// dibujarla y se traduce el cambio de texto de esos dos botones.
	var campania = {
		'New Campaign': 'Nueva campaña',
		'Company Origin': 'Origen de la compañía',
		'Company Name': 'Nombre de la compañía',
		'Late Game Crisis': 'Crisis de juego tardío',
		'Random': 'Aleatorio',
		'Nobles at War': 'Guerra de nobles',
		'Greenskin Invasion': 'Invasión de pieles verdes',
		'Undead Scourge': 'Plaga de no muertos',
		'Holy War': 'Guerra santa',
		'Permanent Destruction': 'Destrucción permanente',
		'Economic Difficulty': 'Dificultad económica',
		'Starting Funds': 'Fondos iniciales',
		'Combat Difficulty': 'Dificultad de combate',
		'Beginner': 'Principiante',
		'Veteran': 'Veterano',
		'Expert': 'Experto',
		'Legendary': 'Legendario',
		'High': 'Altos',
		'Medium': 'Medios',
		'Low': 'Bajos',
		'None': 'Ninguno',
		'Ironman Mode': 'Modo Hombre de hierro',
		'Ironman': 'Hombre de hierro',
		'Unexplored Map': 'Mapa inexplorado',
		'Map Seed': 'Semilla de mapa',
		'Next': 'Siguiente',
		'Previous': 'Volver',
		'Cancel': 'Cancelar',
		'Start': 'Empezar'
	};

	var traduceCampania = function (_m)
	{
		if (!_m || !_m.mContainer) return;
		var titulo = _m.mDialogContainer.findDialogTitle();
		titulo.html(tr(campania, titulo.text()));
		retoca(_m.mContainer, 'label, .title, .label', campania);
		['mStartButton', 'mCancelButton'].forEach(function (_nombre)
		{
			var boton = _m[_nombre];
			if (!boton || boton.es_legends) return;
			boton.es_legends = true;
			boton.changeButtonText = function (_texto) { return $.fn.changeButtonText.call(this, tr(campania, _texto)); };
		});
	};

	if (typeof NewCampaignMenuModule !== 'undefined')
		envuelve(NewCampaignMenuModule.prototype, 'createDIV', function () { traduceCampania(this); });
	try { traduceCampania(Screens.MainMenuScreen.mNewCampaignModule); } catch (e) {}

	// Ajustes de mods (MSU): los botones de los ajustes de lista enseñan el
	// valor tal cual, que es inglés y es también lo que Legends compara (por
	// ejemplo "Enabled"). Solo se cambia lo que se pinta, nunca el valor, y
	// solo si todos los valores del ajuste tienen traducción: así no se mezclan
	// idiomas dentro de un mismo botón.
	var ajustes = {
		'Disabled': 'Desactivado',
		'Enabled': 'Activado',
		'Enabled (Cosmetic)': 'Activado (estético)',
		'Left': 'Izquierda',
		'Middle': 'Centro',
		'Right': 'Derecha',
		'Below': 'Debajo',
		'All Ingredients Available': 'Todos los ingredientes disponibles',
		'One Ingredient Available': 'Un ingrediente disponible',
		'Always': 'Siempre',
		'Default': 'Por defecto',
		'Limited': 'Limitado'
	};

	var traduceBoton = function (_ajuste)
	{
		var valores = _ajuste.data.array;
		if (!valores.every(function (_v) { return propio(ajustes, _v); })) return;
		_ajuste.button.changeButtonText(tr(ajustes, _ajuste.data.value));
	};

	if (typeof EnumSetting !== 'undefined')
	{
		envuelve(EnumSetting.prototype, 'cycle', function () { traduceBoton(this); });
		envuelve(EnumSetting.prototype, 'updateValue', function () { traduceBoton(this); });

		if (typeof ModSettingsScreen !== 'undefined')
			envuelve(ModSettingsScreen.prototype, 'switchToPage', function ()
			{
				this.mActiveSettings.forEach(function (_ajuste)
				{
					if (_ajuste instanceof EnumSetting) traduceBoton(_ajuste);
				});
			});
	}

	// Pantallas que Legends añade o sustituye (campamento, obituario, séquito,
	// tiendas, cargar y guardar, cabecera del personaje). Sus textos fijos van
	// escritos en el JS, así que se retocan los elementos hoja ya dibujados, con
	// el mismo mapa exacto. Lo que Squirrel manda a esas pantallas (títulos y
	// subtítulos del campamento, nombres de tienda, el aviso del menú) no se toca
	// aquí: lo traduce Rosetta o un enganche de Squirrel. Los textos son los que
	// el pack ya usa en sus .js traducidos del juego base.
	var interfaz = {
		// Botones
		'Leave': 'Salir',
		'Camp': 'Campamento',
		'Save': 'Guardar',
		'Load': 'Cargar',
		'Cancel': 'Cancelar',
		'Close': 'Cerrar',
		'Delete': 'Borrar',
		'Hire': 'Contratar',
		'Try out': 'Probar',
		'Dismiss': 'Despedir',
		'Accept': 'Aceptar',
		'Confirm': 'Confirmar',
		'Craft': 'Elaborar',
		'Craft Forever': 'Fabricar siempre',
		'Building': 'Edificio',
		// Títulos de diálogos y ventanas emergentes
		'Obituary': 'Obituario',
		'Load Campaign': 'Cargar campaña',
		'Save Campaign': 'Guardar campaña',
		'Enter Name': 'Ingresar nombre',
		'Change Name & Title': 'Cambiar nombre y título',
		'Level Up': 'Sube de nivel',
		'Configuration': 'Configuración',
		'Customize Preset Name': 'Personalizar nombre del preajuste',
		'Hire Follower': 'Contratar seguidor',
		'Barber': 'Barbero',
		'Taxidermist': 'Taxidermista',
		'Fletcher': 'Flechero',
		'Gather': 'Recolección',
		'Hunting': 'Caza',
		'Painter': 'Pintura',
		'Rest': 'Descanso',
		'Scout': 'Exploración',
		'Training': 'Entrenamiento',
		// Cabeceras y rótulos
		'Name': 'Nombre',
		'Name:': 'Nombre:',
		'Title': 'Título',
		'Fate': 'Destino',
		'Lv': 'Nv',
		'Traits': 'Rasgos',
		'Perks': 'Ventajas',
		'Show Perks': 'Mostrar ventajas',
		'Swap Stat Order': 'Cambiar orden de atributos',
		'Stacked Stars': 'Estrellas apiladas',
		'Stash': 'Alijo',
		'Shop': 'Tienda',
		'Repairs': 'Reparaciones',
		'Salvage': 'Recuperación',
		'Armor': 'Armadura',
		'Helmet': 'Casco',
		'Weapon': 'Arma',
		'Shield': 'Escudo',
		'Crafting Queue': 'Cola de fabricación',
		'Components Required': 'Componentes requeridos',
		'Injury Queue': 'Cola de heridas',
		'Injuries List': 'Lista de heridas',
		'Effects': 'Efectos',
		'Requirements': 'Requisitos',
		'Costs': 'Coste',
		'Up Front': 'Inicial',
		'Daily': 'Diario',
		'Variant:': 'Variante:',
		'New Savegame': 'Nuevo guardado',
		'Add to obituary?': '¿Añadir al obituario?',
		'Click here to level up!': '¡Sube de nivel!',
		'Nothing can be crafted from your combination of trophies.': 'No se puede fabricar nada a partir de tu combinación de trofeos.',
		'No one has been assigned to this tent.': 'No hay nadie asignado a esta tienda.'
	};

	// Textos con partes variables, como pares [expresión, sustitución] sobre el
	// HTML de un elemento. El nombre del personaje o de la partida se conserva.
	var variables = [
		[/^Really dismiss (.*)\?$/, '¿Quieres despedir a $1?'],
		[/^Really free (.*)\?$/, '¿Quieres liberar a $1?'],
		[/^(.*) will permanently leave you and place his <br\/?>current equipment in the stash\.$/, '$1 te dejará de forma permanente y colocará <br/>su equipo actual en el inventario.'],
		[/^Pay (<img[^>]*>)(\d+) Compensation$/, 'Paga $1$2 de compensación'],
		[/^Pay (<img[^>]*>)(\d+) Reparations$/, 'Paga $1$2 por reparaciones'],
		[/^Permanently delete the campaign (<span[^>]*>.*<\/span>)\?$/, '¿Eliminar definitivamente la campaña $1?']
	];

	var retocaVariables = function (_raiz, _selector)
	{
		_raiz.find(_selector).each(function ()
		{
			var e = $(this);
			var html = e.html();
			for (var i = 0; i < variables.length; i++)
			{
				if (variables[i][0].test(html)) { e.html(html.replace(variables[i][0], variables[i][1])); break; }
			}
		});
	};

	// Cada contenedor se retoca una sola vez. La marca va en el contenedor y no
	// en el módulo, porque el juego puede volver a dibujar el módulo entero.
	var traduceVista = function (_m)
	{
		if (!_m || !_m.mContainer || _m.mContainer.data('es_legends')) return;
		_m.mContainer.data('es_legends', true);
		retoca(_m.mContainer, '*', interfaz);
	};

	// Variantes de envuelve: el original devuelve algo que hay que retocar, o se
	// necesita el valor de retorno además de los argumentos.
	var envuelveRet = function (_obj, _nombre, _despues)
	{
		if (_obj === undefined || _obj === null || typeof _obj[_nombre] !== 'function') return;
		var original = _obj[_nombre];
		_obj[_nombre] = function ()
		{
			var ret = original.apply(this, arguments);
			try { _despues.call(this, ret, arguments); } catch (e) {}
			return ret;
		};
	};

	// Creadores de contenido de ventanas emergentes: se retocan la ventana (su
	// título y sus botones, que ya existen) y el contenido que devuelven.
	var envuelvePopup = function (_obj, _nombre)
	{
		envuelveRet(_obj, _nombre, function (_ret, _args)
		{
			var ventana = _args[0] || this.mCurrentPopupDialog;
			if (ventana) retoca(ventana, '*', interfaz);
			if (_ret)
			{
				retoca(_ret, '*', interfaz);
				retocaVariables(_ret, '*');
			}
		});
	};

	['CampScreenMainDialogModule', 'CampScreenCommanderDialogModule', 'CampScreenCraftingDialogModule',
		'CampScreenFletcherDialogModule', 'CampScreenGathererDialogModule', 'CampScreenHealerDialogModule',
		'CampScreenHunterDialogModule', 'CampScreenPainterDialogModule', 'CampScreenRepairDialogModule',
		'CampScreenRestDialogModule', 'CampScreenScoutDialogModule', 'CampScreenTrainingDialogModule',
		'CampScreenWorkshopDialogModule', 'WorldObituaryScreen', 'WorldCampfireScreenMainDialogModule',
		'WorldCampfireScreenHireDialogModule', 'WorldTownScreenBarberDialogModule', 'WorldTownScreenHireDialogModule',
		'WorldTownScreenMainDialogModule', 'WorldTownScreenShopDialogModule', 'WorldTownScreenTaxidermistDialogModule',
		'LoadCampaignMenuModule', 'SaveCampaignMenuModule'].forEach(function (_nombre)
	{
		var clase = window[_nombre];
		if (typeof clase !== 'function') return;
		// Al dibujarse, y al mostrarse por si ya estaba dibujado cuando cargó este fichero.
		envuelve(clase.prototype, 'createDIV', function () { traduceVista(this); });
		envuelve(clase.prototype, 'show', function () { traduceVista(this); });
	});

	// Ventanas emergentes que se crean al pulsar un botón.
	if (typeof CampScreenCommanderDialogModule !== 'undefined')
		['showPresetNamePopupDialog', 'showHunterPopupDialog'].forEach(function (_nombre)
		{
			envuelve(CampScreenCommanderDialogModule.prototype, _nombre, function ()
			{
				if (this.mPopupDialog) retoca(this.mPopupDialog, '*', interfaz);
			});
		});

	if (typeof CharacterScreenLeftPanelHeaderModule !== 'undefined')
		['createDismissDialogContent', 'createChangeNameAndTitleDialogContent', 'createLevelUpDialogContent'].forEach(function (_nombre)
		{
			envuelvePopup(CharacterScreenLeftPanelHeaderModule.prototype, _nombre);
		});

	[typeof LoadCampaignMenuModule !== 'undefined' ? LoadCampaignMenuModule : null,
		typeof SaveCampaignMenuModule !== 'undefined' ? SaveCampaignMenuModule : null].forEach(function (_clase)
	{
		if (!_clase) return;
		envuelvePopup(_clase.prototype, 'createDeleteDialogContent');
		envuelvePopup(_clase.prototype, 'createEnterNameDialogContent');
	});

	if (typeof SaveCampaignMenuModule !== 'undefined')
		envuelve(SaveCampaignMenuModule.prototype, 'addNewSavegameEntryToList', function ()
		{
			retoca(this.mListScrollContainer, '.label', interfaz);
		});

	// Barra de experiencia de la cabecera del personaje.
	if (typeof $.fn.changeProgressbarLabel === 'function')
	{
		var etiqueta = $.fn.changeProgressbarLabel;
		$.fn.changeProgressbarLabel = function (_texto)
		{
			var args = Array.prototype.slice.call(arguments);
			args[0] = tr(interfaz, _texto);
			return etiqueta.apply(this, args);
		};
	}

	// Botones, pestañas y títulos de ventanas emergentes que Legends escribe en
	// inglés en los ficheros que sustituye (lista de hermanos, ventajas, botín,
	// formaciones, diálogo táctico). Los .js del pack ya los crean en castellano,
	// así que una clave inglesa de este mapa solo puede venir de Legends.
	var fijos = {
		'Start Battle': 'Empezar batalla',
		'Statistics': 'Estadísticas',
		'Loot': 'Botín',
		'Continue': 'Continuar',
		'Leave': 'Salir',
		'Yes': 'Sí',
		'Close': 'Cerrar',
		'Unlock Perk': 'Desbloquear ventaja',
		'Notice': 'Aviso',
		'Stash Size Changed': 'Cambio de tamaño del inventario',
		'Change Formation Name': 'Cambiar nombre de la formación'
	};
	['createTextButton', 'createTabTextButton', 'changeButtonText', 'createPopupDialog'].forEach(function (_nombre)
	{
		var original = $.fn[_nombre];
		if (typeof original !== 'function') return;
		$.fn[_nombre] = function (_texto)
		{
			var args = Array.prototype.slice.call(arguments);
			args[0] = tr(fijos, _texto);
			return original.apply(this, args);
		};
	});

	// Barbero: los rótulos de cada control llegan como primer argumento.
	if (typeof WorldTownScreenBarberDialogModule !== 'undefined')
	{
		var barbero = {
			'Hair Color': 'Color del pelo',
			'Head': 'Cabeza',
			'Hair': 'Pelo',
			'Beard': 'Barba',
			'Body': 'Cuerpo',
			'Tattoo': 'Tatuaje',
			'Head Tattoo': 'Tatuaje (cabeza)'
		};
		var control = WorldTownScreenBarberDialogModule.prototype.createAppearanceControlDIV;
		if (typeof control === 'function')
			WorldTownScreenBarberDialogModule.prototype.createAppearanceControlDIV = function (_label)
			{
				var args = Array.prototype.slice.call(arguments);
				args[0] = tr(barbero, _label);
				return control.apply(this, args);
			};
	}

	// Tienda: avisos al vender. Solo se traduce lo que se pinta (Prompt y Text).
	if (typeof WorldTownScreenShopDialogModule !== 'undefined')
		envuelveRet(WorldTownScreenShopDialogModule.prototype, 'getSwapConfirmationOptionsFromResult', function (_ret)
		{
			var venta = {
				'Are you sure?': '¿Estás seguro?',
				'Not sellable.': 'No vendible.',
				'This item may not be acquirable later if you sell it.': 'Es posible que este artículo no pueda adquirirse más adelante si lo vendes.',
				'This item is unique and can\'t be acquired again later!': '¡Este artículo es único y no podrá adquirirse nuevamente más tarde!',
				'This item cannot be sold.': 'Este objeto no puede ser vendido.'
			};
			_ret.Prompt = tr(venta, _ret.Prompt);
			_ret.Text = tr(venta, _ret.Text);
		});

	// Resultado del combate: cabecera del botín y aviso de inventario reducido.
	if (typeof TacticalCombatResultScreenLootPanel !== 'undefined')
		envuelve(TacticalCombatResultScreenLootPanel.prototype, 'createDIV', function ()
		{
			retoca(this.mContainer, '.is-header', { 'Found Loot': 'Botín encontrado' });
		});
	if (typeof TacticalCombatResultScreen !== 'undefined')
		envuelveRet(TacticalCombatResultScreen.prototype, 'createStashResizeHeader', function (_ret)
		{
			var e = _ret.find('.header-text');
			e.html(e.html().replace(/^By continuing you would delete the last (\d+) items in your stash\.$/,
				'Si continúas, se borrarán los últimos $1 objetos de tu inventario.'));
		});

	// Aviso de la barra superior al acampar: Legends lo parte en varias líneas
	// sin centrarlas, y en castellano se nota más porque los rótulos son largos.
	if (typeof WorldScreenTopbarDayTimeModule !== 'undefined')
		envuelve(WorldScreenTopbarDayTimeModule.prototype, 'showMessage', function ()
		{
			this.mPausedDiv.css('text-align', 'center');
			this.mPausedSpacebarDiv.css('text-align', 'center');
		});

	// Menú principal: el anuncio lleva una imagen dentro, así que se cambia
	// solo su primer nodo de texto.
	var anuncio = function (_m)
	{
		var nodo = _m.mMarketing.contents().get(0);
		if (nodo && nodo.nodeType === 3 && nodo.nodeValue === 'Wishlist our new game!') nodo.nodeValue = '¡A tu lista de deseados!';
	};
	if (typeof MainMenuScreen !== 'undefined')
		envuelve(MainMenuScreen.prototype, 'addCrossMarketing', function () { anuncio(this); });
	try { anuncio(Screens.MainMenuScreen); } catch (e) {}

	// Obituario: el subtítulo lo escribe loadFromData con .text() cada vez que
	// llega la lista, y el número de caídos va dentro de la frase.
	if (typeof WorldObituaryScreen !== 'undefined')
		envuelve(WorldObituaryScreen.prototype, 'loadFromData', function ()
		{
			var subtitulo = this.mDialogContainer.findDialogSubTitle();
			var texto = subtitulo.text();
			var n = /^(\d+) men have fallen since you took command$/.exec(texto);
			if (n) subtitulo.text('Han caído ' + n[1] + ' hombres desde que asumiste el mando');
			else subtitulo.text(tr({
				'No one has fallen since you took command': 'Nadie ha caído desde que asumiste el mando',
				'A single man has fallen since you took command': 'Un solo hombre ha caído desde que asumiste el mando'
			}, texto));
		});
})();
