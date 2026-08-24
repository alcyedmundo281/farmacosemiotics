# farmacosemiotics

**Uso racional de medicamentos, en fuente abierta y verificable.** Fichas
terapéuticas en YAML, cada enunciado de eficacia o seguridad anclado a un PMID
que resuelve. Motor en Python. Índice JSON-LD.

→ **[powersemiotics.com/farmacosemiotics](https://powersemiotics.com/farmacosemiotics/)**

Parte de **[Powersemiotics](https://powersemiotics.com/)**, del que también
cuelgan [biosemiotics](https://powersemiotics.com/biosemiotics/) (atlas POCUS) y
[medsemiotics](https://powersemiotics.com/medsemiotics/) (plataforma educativa).
Fuera del dominio, el ecosistema lo completan
[medsemiotics-db](https://github.com/alcyedmundo281/medsemiotics-db) (índice
clínico) y [holonmed](https://github.com/alcyedmundo281/holonmed)
(razonamiento local).

El dominio **se hereda**: `powersemiotics.com` está configurado en el sitio de
usuario de la cuenta, y cada repositorio de proyecto se sirve bajo
`powersemiotics.com/<repo>/`. Por eso este repositorio **no lleva ni genera un
fichero `CNAME`** —un `CNAME` en un sitio de proyecto reclamaría el vértice del
dominio y tumbaría el sitio principal—. Hay una prueba que lo vigila.

La meta de contenido es la **Lista Modelo de Medicamentos Esenciales de la OMS**
—24.ª lista, 2025, y la 10.ª LME para niños—. No es un catálogo nacional: es
internacional por diseño, y lo que depende del país vive en `costos/`, aparte.

## La arquitectura, en una frase

> **El índice es PubMed. Los YAML son PubMed Central.**

`build/index.json` lleva metadatos —el registro que se busca y se filtra—. Los
YAML llevan el texto estructurado completo. Es el mismo reparto que usa
biosemiotics, y es lo que hace posible a la vez un buscador con facetas, un
reto de preguntas con URL relativas y un depósito JATS.

## El desdoblamiento

```
farmacos/   un YAML por principio activo    identidad, ATC, LME, regulatorio, seguridad
fichas/     un YAML por fármaco × indicación   PICO, evidencia, GRADE, balance, recomendación
```

No es burocracia de carpetas. Es la misma lógica por la que medsemiotics-db
pone el cociente de verosimilitud en la arista concepto→condición y no en el
concepto suelto:

> **La eficacia no es del fármaco en abstracto. Es del fármaco PARA una
> indicación, en una población, frente a un comparador.**

La metformina no «funciona»: reduce desenlaces en diabetes tipo 2 del adulto
comparada con dieta sola. Ese enunciado pertenece a la ficha, no al fármaco.
El mecanismo de acción, el ATC y la contraindicación por filtrado glomerular
sí pertenecen al fármaco, y valen para todas sus indicaciones.

## Regla de oro

> **Ningún enunciado de eficacia o seguridad sin PMID resoluble.**
> Un `HR 0.62 (IC95% 0.51–0.75)` sin procedencia es un número inventado con
> formato científico, y mueve la decisión de un clínico.

`scripts/build.py` la hace cumplir: una `ref` que no resuelve a un fichero de
`referencias/` es un error, no una advertencia.

## Mapa

```
farmacosemiotics/
├── CLAUDE.md                          manual de operación de la sesión
├── mapa-maestro-farmacosemiotics.md   QUÉ poblar y en qué orden
├── farmacos/      FS0001-metformina.yaml
├── fichas/        FT0001-metformina-diabetes-tipo-2.yaml
├── referencias/   pmid-9742977.yaml            verificadas contra PubMed
├── catalogo/      lme-oms-2025.yaml            la meta de contenido
├── costos/        <pais>.yaml                  overlay opcional, nunca el núcleo
├── scripts/       build · pubmed · openfda · eml · indice · sitio · reto
├── sitio/         plantillas del frontend
└── build/         GENERADO — no se versiona
```

## Uso

```bash
pip install -r requirements.txt
python scripts/build.py          # valida; no modifica nada
python scripts/indice.py         # build/index.json + build/jsonld/ + build/jats/
python scripts/sitio.py          # build/sitio/ listo para Pages
python scripts/eml.py            # cobertura frente a la Lista Modelo de la OMS
```

Añadir una referencia (no se escriben a mano):

```bash
python scripts/pubmed.py 9742977
```

Refrescar el bloque regulatorio desde openFDA (imprime el YAML; lo pega una
persona, que es quien responde por lo que entra):

```bash
python scripts/openfda.py "metformin hydrochloride"
```

## Fuentes

| capa | fuente | por qué |
|---|---|---|
| eficacia y seguridad | **PubMed** (E-utilities) | autoridad para título, año y retractación |
| identidad y normalización | **RxNav / RxNorm** (NLM) | DCI ↔ RxCUI ↔ ATC |
| regulatorio y etiqueta | **openFDA** (`drugsfda`, `label`) | API pública, sin clave, versionable en CI |
| meta de contenido | **LME OMS 24.ª lista, 2025** (TRS 1064) | sembrada en `catalogo/` |
| costos | overlay por país en `costos/` | no hay fuente internacional libre y comparable |

No usamos un MCP para la FDA a propósito: ataría la generación a una sesión
interactiva. `scripts/openfda.py` corre en CI, es reproducible y deja huella
auditable con la fecha de consulta en el propio registro.

## Costos: por qué no están en el núcleo

No existe una fuente de precios internacional libre, comparable y actualizada.
Meter un precio en la ficha internacional la volvería falsa en cuanto cruza una
frontera, y la haría envejecer mal. Por eso el precio vive en
`costos/<pais>.yaml`, cada dato con fuente, moneda y fecha de consulta, y el
motor lo superpone solo si se lo pides.

## Estado

| capa | registros |
|---|---|
| fármacos | 1 |
| fichas | 1 |
| referencias | 0 |
| cobertura LME | 1 / ~600 |

Ver [mapa-maestro-farmacosemiotics.md](mapa-maestro-farmacosemiotics.md).

## Aviso

Material educativo. No sustituye el juicio clínico ni la ficha técnica
aprobada por la agencia reguladora que corresponda al lugar de uso. Autor y
responsable clínico: Dr. Alcy Torres.

## Licencia

Contenido —fichas, fármacos, catálogo— bajo
[CC BY-SA 4.0](LICENSE). Código de `scripts/` y `sitio/` bajo
[MIT](LICENSE-CODIGO).
