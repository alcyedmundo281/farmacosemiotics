# CLAUDE.md — Manual de operación de farmacosemiotics

Este archivo le enseña a cualquier sesión de Claude Code cómo trabajar en este
repositorio. **Léelo completo al arrancar.** No improvises el flujo.

---

## Qué es este proyecto

**Guías de práctica clínica farmacoterapéuticas** en YAML, con el índice, el
sitio y el libro derivados de ellas. **Publicador, no proveedor**: a diferencia
de medsemiotics-db —que solo guarda hechos y prohíbe la prosa—, aquí el YAML
*es* el texto completo. Ese es el equivalente a PMC; `build/index.json` es el
equivalente a PubMed.

Cada entrada de `fichas/` es una guía: no se limita a pesar el NNT frente al
NNH, sino que responde a lo que el prescriptor tiene delante —qué pido antes de
la primera dosis, cada cuánto lo repito, qué hago cuando el análisis se tuerce,
qué le digo a quien quiere quedarse embarazada y de quién es cada acto entre el
especialista y el médico de seguimiento—. El estándar de forma son las guías de
las sociedades europeas y británicas (BSR, BAD, EDF/EADV) y la guía CPIC para
lo farmacogenético.

**Una fuente, muchas salidas.** El YAML es la única fuente y es obligatoria.
De ahí salen `build/index.json`, el sitio, el JATS y —en un solo `.qmd`— el
EPUB con todas las guías. Nada de eso se edita a mano: se regenera.

Alcance **internacional**. Lo que dependa de un país va en `costos/`, nunca en
`farmacos/` ni en `fichas/`.

Autor y responsable clínico: **Dr. Alcy Edmundo Torres Guerrero** ([powersemiotics.com](https://powersemiotics.com/)). Toda decisión clínica final es
suya.

## Regla de oro

**Ningún enunciado de eficacia o seguridad sin PMID resoluble.**

Un `HR 0.62 (IC95% 0.51–0.75)` sin procedencia es un número inventado con
formato científico, y mueve la decisión de un clínico. `build.py` lo trata como
error, no como advertencia.

La prueba práctica antes de escribir cualquier cifra: *¿puedo señalar el
fichero de `referencias/` del que sale?* Si no, no se escribe.

## Lo primero al arrancar una sesión

1. `git status` y reporta el estado.
2. Lee `mapa-maestro-farmacosemiotics.md` y di **qué oleada toca**.
3. `python scripts/build.py` y reporta las alertas actuales. Fíjate en cuántas
   guías salen «completas» y cuántas con huecos declarados: esa es la distancia
   real que le queda al repositorio.

## Mapa del repositorio

```
farmacosemiotics/
├── CLAUDE.md                          ← este archivo
├── mapa-maestro-farmacosemiotics.md   ← QUÉ poblar y en qué orden (léelo siempre)
├── farmacos/*.yaml                    ← principio activo: identidad, ATC, LME, seguridad
├── fichas/*.yaml                      ← fármaco × indicación: Semáforo, NNT, NNH, GRADE
├── referencias/*.yaml                 ← artículos con PMID y DOI verificados
├── catalogo/lme-oms-2025.yaml         ← la meta de contenido
├── costos/<pais>.yaml                 ← overlay opcional, fuera del núcleo
├── scripts/nuevo.py                   ← crea plantillas estandarizadas de fármaco o ficha
├── scripts/build.py                   ← valida; NO modifica nada
├── scripts/pubmed.py                  ← crea referencias/ desde un PMID
├── scripts/openfda.py                 ← bloque regulatorio desde openFDA
├── scripts/eml.py                     ← cobertura frente a la LME
├── scripts/indice.py                  ← build/index.json + jsonld/ + jats/
├── scripts/sitio.py                   ← build/sitio/ (Ghost Casper: index, blog/Indice, reto)
├── scripts/reto.py                    ← build/reto.json, URL relativas
├── scripts/qmd.py                     ← proyecta UN solo .qmd con todas las guías
├── scripts/epub.py                    ← lo encuaderna con Quarto → build/*.epub
├── scripts/pipeline.py                ← ejecuta el ciclo entero y cronometra
└── build/                             ← GENERADO, no se versiona
```

El libro se compila en dos pasos y por una razón: `qmd.py` solo necesita Python
y entra en el pipeline; `epub.py` necesita Quarto instalado y por eso queda
fuera, para que el pipeline siga corriendo en cualquier máquina.

## El desdoblamiento fármaco / ficha

Es la decisión de diseño que más se malinterpreta. Antes de añadir un campo,
pregúntate **si el dato cambia según la indicación**:

| dato | dónde va | ¿depende de la indicación? |
|---|---|---|
| ATC, RxCUI, mecanismo de acción | `farmacos/` | no |
| contraindicación general por TFGe | `farmacos/` · `seguridad` | no |
| aprobación FDA/EMA de la molécula | `farmacos/` · `regulatorio` | no |
| Semáforo, perla de prescripción | `fichas/` · `decision_clinica` | **sí** |
| HR de mortalidad, NNT, certeza GRADE | `fichas/` · `evidencia` | **sí** |
| NNH, toxicidad e incidencia | `fichas/` · `seguridad_cuantitativa` | **sí** |
| posología y ajuste renal específico | `fichas/` · `posologia` | **sí** |
| fuerza y dirección de recomendación | `fichas/` · `recomendacion` | **sí** |
| cribado previo a la primera dosis | `fichas/` · `cribado_basal` | **sí** |
| dosis según genotipo (TPMT, NUDT15…) | `fichas/` · `farmacogenetica` | **sí** |
| cronograma de analíticas por fase | `fichas/` · `monitorizacion` | **sí** |
| punto de corte y conducta ante la anomalía | `fichas/` · `umbrales_accion` | **sí** |
| interacción que cambia la dosis | `fichas/` · `interacciones` | **sí** |
| embarazo, lactancia, lavado, anticoncepción | `fichas/` · `reproductivo` | **sí** |
| reparto especialista / seguimiento | `fichas/` · `atencion_compartida` | **sí** |
| línea de tratamiento y desescalamiento | `fichas/` · `posicionamiento` | **sí** |

Un mismo fármaco tiene tantas fichas como indicaciones evaluadas.
`FS:0001` (metformina) puede sostener `FT:0001` (DM2) y una futura ficha de
síndrome de ovario poliquístico, con evidencia y recomendación distintas.

## Códigos

- **`FS:` y `FT:` son permanentes.** No se renumeran, no se reutilizan, no se
  reasignan. El índice, el reto y las URL del sitio los citan.
- Cuatro dígitos, secuenciales por tipo. El nombre del fichero es
  `FS0001-<slug-dci>.yaml` y `FT0001-<slug-farmaco>-<slug-indicacion>.yaml`.
- Antes de acuñar un código nuevo, **busca si el fármaco ya existe**. Duplicar
  un principio activo es el error más caro de deshacer.

## Reglas duras (no se rompen nunca)

- **Citas solo verificadas.** Nunca escribas una referencia de memoria ni
  aceptes una que produjo un modelo sin comprobar el PMID. Este ecosistema ya
  fue salvado de tres referencias inventadas en biosemiotics. Las referencias
  **no se escriben a mano**: `python scripts/pubmed.py <PMID>`.
  Si la red del entorno deniega la salida a `eutils.ncbi.nlm.nih.gov` —pasa en
  las sesiones con política de egreso restrictiva—, la regla no se relaja: se
  usa `python scripts/pubmed.py --desde-json <archivo>`, que ingiere la
  respuesta literal de un servidor MCP de PubMed por el mismo escritor. El
  fichero resultante lo declara con `verificacion.via: pubmed-mcp` y avisa de
  que la retractación solo pudo comprobarse por el tipo de publicación. Cuando
  eutils vuelva a ser alcanzable, se rehace con `--forzar`.
- **PubMed manda sobre CrossRef.** PubMed es autoridad para título, año y
  retractación; CrossRef solo confirma que el DOI resuelve.
- **Un artículo retractado no sostiene un enunciado.** `pubmed.py` marca
  `retractado: true` y `build.py` lo convierte en error.
- **Nada de precios en el núcleo.** Si aparece una cifra en dólares dentro de
  `farmacos/` o `fichas/`, está en el sitio equivocado: va a `costos/`.
- **Nada de contexto ecuatoriano.** Sin CNMB, sin ARCSA, sin RPIS, sin IESS,
  sin MSP. Ecuador es un overlay de `costos/`, como cualquier otro país.
- **La certeza GRADE necesita razón.** Una certeza distinta de `alta` sin
  `razones_descenso` es un juicio sin argumento.
- **Fecha de consulta obligatoria** en todo dato traído de una API externa
  (`openfda`, `rxnav`). Un dato regulatorio sin fecha no es verificable.
- **Un hueco se declara, no se rellena.** Si no hay fuente que fije un
  cronograma o un punto de corte, el apartado NO se escribe: se anota en
  `huecos_declarados` con su `motivo` y las `refs` de lo que se consultó sin
  éxito. Un apartado ausente y uno olvidado se leen igual en el EPUB, y no son
  lo mismo. `build.py` exige el motivo y falla si el hueco declara vacío un
  bloque que en realidad tiene contenido.
- **Tres estados, no dos, en lo que no se ha podido comprobar.** `lme.presente`
  admite `null` además de `true` y `false`. `null` significa «no comprobado» y
  `eml.py` lo cuenta fuera de la Lista Modelo, que es el sesgo conservador
  correcto. Poner `false` para quitarse el aviso de encima es afirmar algo que
  no se sabe.

## Flujo para añadir una guía

1. **Ubica la indicación en el mapa maestro.** Copia su sección de la LME y su
   oleada.
2. **Comprueba que el fármaco existe** en `farmacos/`. Si no, créalo primero:
   una ficha que apunta a un `FS:` inexistente falla la validación.
3. **Busca la evidencia y trae las referencias**:
   `python scripts/pubmed.py <PMID> <PMID> ...`
4. **Escribe la ficha.** Cada fila de `evidencia` con su `ref`, su `certeza` y,
   si baja de `alta`, sus `razones_descenso`.
5. **Refresca el regulatorio**: `python scripts/openfda.py <nombre>`.
6. **Completa la capa de guía** hasta donde llegue la fuente: `cribado_basal`,
   `farmacogenetica`, `monitorizacion`, `umbrales_accion`, `interacciones`,
   `reproductivo`, `atencion_compartida`, `posicionamiento`. Lo que no tenga
   fuente va a `huecos_declarados`, nunca escrito de memoria.
7. `python scripts/build.py`. **No continúes con errores.**
8. `python scripts/pipeline.py` genera índice, reto, sitio y la proyección del
   libro, y pasa las pruebas de contrato.
9. `python scripts/epub.py` encuaderna el EPUB, si tienes Quarto instalado.

## Qué NO hacer

- No inventes un intervalo de confianza «para que quede completo». Si la fuente
  no lo da, el campo se omite.
- No conviertas una asociación observacional en un enunciado de eficacia. El
  campo `diseno` existe para eso y `build.py` lo exige.
- No edites `build/` a mano: se regenera y se pierde. Eso incluye
  `build/quarto/guias-farmacoterapeuticas.qmd`, que parece un documento
  editable y es una salida: corregir ahí una cifra la deja sin arreglar en el
  YAML y sin arreglar en la siguiente compilación.
- No inventes un punto de corte «porque es el habitual». Un umbral de
  neutrófilos sin PMID es el mismo fallo que un HR sin PMID, y llega más
  directo a una decisión: alguien suspende un fármaco por ese número.
- No metas el texto de la ficha técnica de la FDA en el YAML. Se enlaza y se
  resume; copiarlo lo convierte en una obra derivada que no controlamos.
- No hagas que el sitio consulte APIs en tiempo de ejecución. Todo se resuelve
  en el build, como en biosemiotics: el frontend solo lee `index.json`.

## El dominio: se hereda, no se pide

El sitio se publica en **https://powersemiotics.com/farmacosemiotics/**.

No porque este repositorio lo configure, sino porque el sitio de usuario
`alcyedmundo281.github.io` tiene `powersemiotics.com` como dominio propio, y
**todos los sitios de proyecto de la cuenta lo heredan** como
`powersemiotics.com/<repo>/`. Por eso `gh api repos/.../pages` devuelve
`cname: null` para este repositorio: es lo correcto, no un olvido.

> **Nunca generes ni versiones un fichero `CNAME` aquí.** Un `CNAME` con
> `powersemiotics.com` en un sitio de proyecto reclama el vértice del dominio
> para ese proyecto y tumba el sitio principal —y con él a biosemiotics y a
> medsemiotics, que cuelgan del mismo dominio—. Es el error que parece un
> arreglo: alguien ve `cname: null`, lo toma por un fallo y lo «corrige».

Lo que sí pertenece a este repositorio:

- `BASE` en `scripts/indice.py`, que es el prefijo de las URL absolutas del
  JSON-LD. Debe coincidir con el dominio publicado; hay una prueba que lo
  comprueba.
- Todo lo demás es relativo, y por eso el mismo build funciona en Pages, en un
  dominio distinto y abierto desde el disco.

La cuenta tiene HTTPS forzado en el vértice y en este repositorio, y el
certificado cubre `powersemiotics.com` y `www.powersemiotics.com`.

## La asimetría con el resto del ecosistema

farmacosemiotics **lee** identidad clínica de medsemiotics-db cuando le hace
falta (por ejemplo, la condición que trata una indicación), pero **no escribe**
en él. Los hechos que pertenezcan al índice compartido —un umbral, un código—
se proponen allí como pull request. Aquí vive la terapéutica, no el vocabulario.
