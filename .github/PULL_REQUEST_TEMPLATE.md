## Qué cambia y por qué

<!-- Una o dos frases. Si corrige un issue, enlázalo: "Corrige #12". -->

## Comprobaciones

- [ ] `PYTHONUTF8=1 uv run python es_pack/tools/build_dist.py` termina sin avisos nuevos.
- [ ] `PYTHONUTF8=1 uv run pytest -q` pasa.
- [ ] Si toqué el corpus, regeneré el cuadro de métricas del README con `es_pack/tools/update_readme_metrics.py`.
- [ ] Si cambié una traducción que se aparta del inglés, miré antes su historial (`git log -S "<valor>"`) por si era deliberada.
- [ ] No toqué el lado `en` de ningún par ni los ficheros de `vendor/rosetta/`.
