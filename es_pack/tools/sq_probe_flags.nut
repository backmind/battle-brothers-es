dofile(getenv("STDLIB_DIR") + "load.nut", true);
dofile("vendor/rosetta/mocks.nut", true);
dofile("vendor/rosetta/scripts/!mods_preload/!rosetta.nut", true);

local def = ::Rosetta, Debug = ::std.Debug;

foreach (s in ["<part:t>", "<part:t_raw>", "<part:t:or=raw>", "<part:t?>", "<part>"]) {
    ::print("parseReplacement(\"" + s + "\") -> " + Debug.pp(def.parseReplacement(s)));
}

// Y el efecto real de una regla que use la forma con dos puntos
local rosetta = {mod = {id = "mod_probe", version = "1.0.0"}, lang = "ru"};
def.maps = {};
def.add(rosetta, [
    {
        mode = "pattern"
        en = "<actor:str> was hit in the <part:str>"
        ru = "<actor> ранен в <part:t:or=raw>"
    }
    {en = "head", ru = "голову"}
]);
def.activate("ru");
::print("regla con <part:t:or=raw> -> \"" + def.translate("Bob was hit in the head") + "\"\n");
