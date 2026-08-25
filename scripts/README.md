# scripts/

Siete scripts, dos familias, y una línea que los separa:

**Los que traen datos de fuera** escriben o imprimen, y los ejecuta una persona
que revisa el resultado antes de aceptarlo.

**Los que leen el repositorio** no modifican ningún registro, nunca. Ni uno.
Esa restricción es lo que permite que `build.py` sea creíble: si el validador
pudiera arreglar lo que valida, nadie sabría qué se arregló.

| script | qué hace | ¿escribe? |
|---|---|---|
| `nuevo.py` | crea plantillas estandarizadas de fármaco o ficha con NNT/NNH y semáforo | `farmacos/`, `fichas/` |
| `pubmed.py` | trae una referencia por PMID y la verifica contra PubMed | `referencias/` |
| `openfda.py` | arma el bloque regulatorio desde openFDA | imprime; pega una persona |
| `build.py` | valida todo y dice qué falta | **no** |
| `eml.py` | mide la cobertura frente a la Lista Modelo de la OMS | **no** |
| `indice.py` | `build/index.json`, `build/jsonld/`, `build/jats/` | solo `build/` |
| `reto.py` | `build/reto.json` con preguntas de certeza, fuerza y semáforo | solo `build/` |
| `sitio.py` | `build/sitio/` (Ghost Casper layout, index + blog + reto) | solo `build/` |

## El orden

```bash
python scripts/nuevo.py ficha FT0006 "Nombre de la Ficha" --farmaco FS0006
python scripts/build.py      # primero, siempre: sin esto lo demás no corre
python scripts/indice.py
python scripts/reto.py
python scripts/sitio.py
python -m http.server -d build/sitio 8000
```

`indice.py`, `reto.py` y `sitio.py` se niegan a generar nada si `build.py`
encuentra errores. No es celo: publicar un índice sobre registros rotos es
peor que no publicar, porque el error se propaga con formato de dato bueno.

## Dependencias

`PyYAML` y `requests` (ver `requirements.txt`). Las llamadas a PubMed, CrossRef
y openFDA usan `urllib` de la biblioteca estándar, así que en la práctica solo
`PyYAML` es imprescindible para validar y generar sin red.

Las pruebas corren con `unittest`, sin pytest:

```bash
python -m unittest discover -s tests -v
```

## Una nota sobre la codificación

Todos los scripts abren con `sys.stdout.reconfigure(encoding="utf-8")`. En
Windows la salida estándar es cp1252 por defecto y «Anestésicos» sale como
«Anest?sicos» —o revienta el fichero generado, que es peor porque no se nota
hasta que alguien lo lee—. Si añades un script, copia esa línea.

## Añadir un script

Tres condiciones, y la tercera es la que se olvida:

1. Que importe `cargar()` de `build.py` en lugar de releer los YAML por su
   cuenta. Dos ideas distintas de qué hay en el repositorio es el camino a que
   el índice y el sitio discrepen.
2. Que declare en su docstring si escribe y dónde.
3. Que si escribe fuera de `build/`, lo haga solo cuando se lo pidan
   explícitamente por argumento. Un script que toca `fichas/` porque sí
   convierte el repositorio en algo que nadie puede revisar por diff.
