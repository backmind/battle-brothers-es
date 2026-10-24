// Rosetta archiva cada regla bajo la primera palabra de su en, una vez quitadas
// las capturas con lo que llevan pegado. Si la captura va dentro de una
// etiqueta ("[color=%positive%]+<n:int>[/color] Melee Skill"), lo que queda es
// "[color=", que ningún texto real tiene suelto porque translate() quita las
// etiquetas enteras: la regla no se prueba nunca (es la familia de
// Suor/battle-brothers-rosetta#13). Aquí la clave salta esos trozos (y el «=»
// suelto que deja "[color=<c:str>]") y toma la
// siguiente palabra. Lo incluye el preload antes de cada corpus de mod; el del
// juego base ya está cargado y no cambia.
local R = ::Rosetta;
R._ruleKey = function ( _pat ) {
    local str = ::std.Re.replace(_pat, R.patternKeyRe, function ( _prefix, _sub, _suffix ) {
        return _sub == "tag" || ::std.Str.endswith(_sub, "_tag") ? (_prefix || "") + " " + (_suffix || "") : "";
    });
    foreach (w in R._iterKeys(str))
        if (w.find("[") == null && w.find("]") == null && w.find("=") == null) return w;
};
