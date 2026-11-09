# farmacosemiotics

**El conocimiento terapéutico de [holonmed](https://github.com/alcyedmundo281/holonmed).**
Cuando holonmed confirma un diagnóstico —una condición `HM:` de
[medsemiotics-db](https://github.com/alcyedmundo281/medsemiotics-db)—, llega
aquí para saber qué fármaco se elige, cómo se dosifica y cómo se usa con
seguridad. Fichas en YAML, cada enunciado de eficacia o seguridad anclado a un
PMID que resuelve.

```
medsemiotics-db  ──(HM:, fijado)──►  farmacosemiotics  ──(fijado)──►  holonmed
   qué tiene                          qué se hace                    el residente
```

## La reescritura de noviembre de 2026

El ecosistema Powersemiotics orbita entero alrededor de holonmed, y este
repositorio se reescribió para servirle. Se borró todo lo que existía para
publicar: el sitio, el reto, el índice JSON-LD y JATS, el libro EPUB, la
cobertura frente a la Lista Modelo de la OMS, el overlay de costos y la
maquinaria de depósito. Sigue en el historial de git.

La versión publicada anterior está archivada en Zenodo y sigue siendo citable:
[`10.5281/zenodo.22700661`](https://doi.org/10.5281/zenodo.22700661).

## Las entidades

| carpeta | código | depende de… | qué responde |
|---|---|---|---|
| `selecciones/` | `SEL:` | el problema de salud (`condicion: HM:`) | qué fármaco se elige, en eficacia, seguridad, conveniencia y costo |
| `farmacos/` | `FS:` | la molécula | identidad, ATC, regulatorio |
| `farmacoterapia/` | `FA:` | la molécula | cribado, monitorización, umbrales, reproductivo |
| `fichas/` | `FT:` | fármaco × indicación | posología, evidencia, GRADE, NNT/NNH |
| `manejo/` | `MAN:` | la condición `HM:` | **en camino**: el plan de manejo completo |

> **La eficacia no es del fármaco en abstracto. Es del fármaco PARA una
> indicación, en una población, frente a un comparador.**

## Regla de oro

> **Ningún enunciado de eficacia o seguridad sin PMID resoluble.**

`build.py` lo trata como error, no como advertencia.

## Uso

```bash
pip install -r requirements.txt
git clone https://github.com/alcyedmundo281/medsemiotics-db ../medsemiotics-db
python scripts/build.py --exigir-indice     # valida; no modifica nada
python -m unittest discover -s tests -v
```

`build.py` lee medsemiotics-db en la revisión fijada en
[`dependencias.yaml`](dependencias.yaml), del historial de git y no del árbol de
trabajo: da igual en qué rama esté el clon. Si el clon no está al lado, indica
su ruta con `MEDSEMIOTICS_DB`.

## Fuentes

| capa | fuente | por qué |
|---|---|---|
| eficacia y seguridad | **PubMed** (E-utilities) | autoridad para título, año y retractación |
| identidad y normalización | **RxNav / RxNorm** (NLM) | DCI ↔ RxCUI ↔ ATC |
| regulatorio y etiqueta | **openFDA** (`drugsfda`, `label`) | API pública, sin clave, con fecha de consulta |
| condiciones | **medsemiotics-db**, fijado | el código `HM:` por el que holonmed llega aquí |

Alcance internacional. Las adaptaciones institucionales no son publicables y no
entran en este repositorio.

## Aviso

**Plataforma independiente.** El contenido no implica aval ni representación
de ninguna institución sanitaria ni académica. No sustituye el juicio clínico
ni la ficha técnica aprobada por la agencia reguladora que corresponda al lugar
de uso. Autor y responsable clínico: Dr. Alcy Torres.

## Licencia

Contenido bajo [CC BY-SA 4.0](LICENSE). Código de `scripts/` bajo
[MIT](LICENSE-CODIGO).
