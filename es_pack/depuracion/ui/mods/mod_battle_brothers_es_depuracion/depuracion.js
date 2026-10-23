// Modo de depuración del pack: busca en lo que se ve en pantalla los textos
// que parecen ingleses y los manda a Squirrel, que los escribe en el log.
// Cada texto se avisa una sola vez por sesión.
var BattleBrothersEsDepuracion = function ()
{
	MSUBackendConnection.call(this);
	this.mVistos = {};
	this.mPendiente = null;
};
BattleBrothersEsDepuracion.prototype = Object.create(MSUBackendConnection.prototype);
BattleBrothersEsDepuracion.prototype.constructor = BattleBrothersEsDepuracion;

// Palabras que no existen en castellano (ni «a», «has», «no» ni «me», que sí).
BattleBrothersEsDepuracion.INGLES = /\b(the|of|and|your|you|with|for|is|are|will|this|that|from|by|to|an|be|can|not|it|its|at|or|more|each|their|they|when|which|was|were|been|into|than|only)\b/gi;

BattleBrothersEsDepuracion.pareceIngles = function (_t)
{
	if (_t.length < 4 || /[áéíóúñ¿¡]/i.test(_t)) return false;
	var m = _t.match(BattleBrothersEsDepuracion.INGLES);
	if (m === null) return false;
	return m.length >= 2 || (m.length === 1 && _t.split(/\s+/).length >= 3);
};

BattleBrothersEsDepuracion.prototype.onConnection = function (_handle)
{
	MSUBackendConnection.prototype.onConnection.call(this, _handle);
	// Primera línea en el log: si no aparece, la conexión no llegó a arrancar.
	SQ.call(this.mSQHandle, 'textoIngles', '(modo de depuración activo)');
	var self = this;
	var programa = function ()
	{
		if (self.mPendiente !== null) return;
		self.mPendiente = setTimeout(function () { self.mPendiente = null; self.revisa(); }, 700);
	};
	if (typeof MutationObserver !== 'undefined')
		new MutationObserver(programa).observe(document.body, { childList: true, subtree: true, characterData: true });
	else
		setInterval(function () { self.revisa(); }, 3000);
	programa();
};

BattleBrothersEsDepuracion.prototype.revisa = function ()
{
	if (this.mSQHandle === null) return;
	var paseo = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
	var nodo;
	while ((nodo = paseo.nextNode()) !== null)
	{
		var t = nodo.nodeValue.replace(/\s+/g, ' ').trim();
		if (t in this.mVistos || !BattleBrothersEsDepuracion.pareceIngles(t)) continue;
		var padre = nodo.parentNode;
		if (padre === null || padre.offsetParent === null) continue;  // oculto
		this.mVistos[t] = true;
		SQ.call(this.mSQHandle, 'textoIngles', t);
	}
};

registerScreen("BattleBrothersEsDepuracion", new BattleBrothersEsDepuracion());
