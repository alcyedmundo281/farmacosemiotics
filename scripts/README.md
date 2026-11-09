# scripts/

Cinco scripts, dos familias, y una línea que los separa:

**Los que traen datos de fuera** escriben o imprimen, y los ejecuta una persona
que revisa el resultado antes de aceptarlo.

**Los que leen el repositorio** no modifican ningún registro, nunca. Esa
restricción es lo que permite que `build.py` sea creíble: si el validador
pudiera arreglar lo que valida, nadie sabría qué se arregló.

| script | qué hace | ¿escribe? |
|---|---|---|
| `nuevo.py` | plantillas de fármaco, selección, farmacoterapia o guía | `farmacos/`, `selecciones/`, `farmacoterapia/`, `fichas/` |
| `pubmed.py` | trae una referencia por PMID y la verifica contra PubMed | `referencias/` |
| `openfda.py` | arma el bloque regulatorio desde openFDA | imprime; pega una persona |
| `nnt.py` | calculadora epidemiológica y auditor de NNT/NNH | **no** |
| `build.py` | valida todo, incluida cada `condicion: HM:` contra medsemiotics-db fijado | **no** |

Los generadores de publicación (índice, sitio, reto, libro, cobertura de la
LME) se borraron en la reescritura de noviembre de 2026: este repositorio sirve
a holonmed. Siguen en el historial de git.

## Validar

```bash
python scripts/build.py                  # el índice que falte es aviso
python scripts/build.py --exigir-indice  # el índice que falte es error (CI)
```

`build.py` busca medsemiotics-db en `MEDSEMIOTICS_DB` o como directorio
hermano, y lee las condiciones de la revisión fijada en `dependencias.yaml`
con `git ls-tree` y `git show`: no mira el árbol de trabajo del clon.

## Dependencias

`PyYAML` y `requests` (ver `requirements.txt`), más `git` en el PATH. Las
pruebas corren con `unittest`, sin pytest:

```bash
python -m unittest discover -s tests -v
```
