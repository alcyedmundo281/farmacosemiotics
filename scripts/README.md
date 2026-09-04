# scripts/

Siete scripts, dos familias, y una línea que los separa:

**Los que traen datos de fuera** escriben o imprimen, y los ejecuta una persona
que revisa el resultado antes de aceptarlo.

**Los que leen el repositorio** no modifican ningún registro, nunca. Ni uno.
Esa restricción es lo que permite que `build.py` sea creíble: si el validador
pudiera arreglar lo que valida, nadie sabría qué se arregló.

| script | qué hace | ¿escribe? |
|---|---|---|
| `pipeline.py` | **orquestador unificado y benchmark de alto rendimiento** | `build/` |
| `nnt.py` | calculadora epidemiológica y auditor matemático de NNT/NNH | **no** |
| `nuevo.py` | plantillas de fármaco, selección, farmacoterapia o guía | `farmacos/`, `selecciones/`, `farmacoterapia/`, `fichas/` |
| `pubmed.py` | trae una referencia por PMID y la verifica contra PubMed | `referencias/` |
| `openfda.py` | arma el bloque regulatorio desde openFDA | imprime; pega una persona |
| `build.py` | valida todo y dice qué falta | **no** |
| `eml.py` | mide la cobertura frente a la Lista Modelo de la OMS | **no** |
| `indice.py` | `build/index.json`, `build/jsonld/`, `build/jats/` | solo `build/` |
| `reto.py` | `build/reto.json` con preguntas de certeza, fuerza y semáforo | solo `build/` |
| `sitio.py` | `build/sitio/` (Ghost Casper layout, index + blog + reto) | solo `build/` |
| `qmd.py` | proyecta TODAS las guías a un único `.qmd` más su BibLaTeX | solo `build/` |
| `epub.py` | encuaderna ese `.qmd` con Quarto → `build/*.epub` | solo `build/` |

## El ciclo completo en un solo comando

```bash
python scripts/pipeline.py          # valida, audita, indexa, compila y testea
python scripts/pipeline.py --serve  # compila y lanza el servidor local
```

`indice.py`, `reto.py` y `sitio.py` se niegan a generar nada si `build.py`
encuentra errores. No es celo: publicar un índice sobre registros rotos es
peor que no publicar, porque el error se propaga con formato de dato bueno.

## El libro, en dos pasos

`qmd.py` y `epub.py` están separados a propósito. El primero solo necesita
Python y por eso entra en el pipeline: es el que puede romperse cuando cambia
el esquema. El segundo necesita Quarto instalado, y una etapa que falle por una
dependencia externa convertiría el pipeline en algo que no corre en cualquier
máquina.

```bash
python scripts/qmd.py      # build/quarto/guias-farmacoterapeuticas.qmd + .bib
python scripts/epub.py     # lo anterior + quarto render → build/*.epub
python scripts/epub.py --solo-render   # da por buena la proyección de antes
python scripts/epub.py --a html        # la misma fuente, otra salida
```

Sin Quarto, `epub.py` sale con código 2 y dice dónde descargarlo, en vez de
dejar un EPUB a medias.

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
