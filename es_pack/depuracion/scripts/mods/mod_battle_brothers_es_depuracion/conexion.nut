// Conexión JS -> Squirrel del modo de depuración (el JS no escribe en el log).
this.conexion <- ::inherit("scripts/mods/msu/js_connection", {
    m = {},

    function connect()
    {
        this.m.JSHandle = ::UI.connect("BattleBrothersEsDepuracion", this);
    }

    function textoIngles( _texto )
    {
        ::logWarning("[es-depuracion] " + _texto);
    }
});
