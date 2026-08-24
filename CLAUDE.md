# CLAUDE.md — Manual de operación de farmacosemiotics

Este archivo le enseña a cualquier sesión de Claude Code cómo trabajar en este
repositorio. **Léelo completo al arrancar.** No improvises el flujo.

---

## Qué es este proyecto

Fichas de terapéutica racional en YAML, con el índice y el sitio derivados de
ellas. **Publicador, no proveedor**: a diferencia de medsemiotics-db —que solo
guarda hechos y prohíbe la prosa—, aquí el YAML *es* el texto completo. Ese es
el equivalente a PMC; `build/index.json` es el equivalente a PubMed.

Alcance **internacional**. Lo que dependa de un país va en `costos/`, nunca en
`farmacos/` ni en `fichas/`.

Autor y responsable clínico: Dr. Alcy Torres. Toda decisión clínica final es
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
3. `python scripts/build.py` y reporta las alertas actuales.

## Mapa del repositorio

```
farmacosemiotics/
├── CLAUDE.md                          ← este archivo
├── mapa-maestro-farmacosemiotics.md   ← QUÉ poblar y en qué orden (léelo siempre)
├── farmacos/*.yaml                    ← principio activo: identidad, ATC, LME, seguridad
├── fichas/*.yaml                      ← fármaco × indicación: PICO, evidencia, GRADE
├── referencias/*.yaml                 ← artículos con PMID y DOI verificados
├── catalogo/lme-oms-2025.yaml         ← la meta de contenido
├── costos/<pais>.yaml                 ← overlay opcional, fuera del núcleo
├── scripts/build.py                   ← valida; NO modifica nada
├── scripts/pubmed.py                  ← crea referencias/ desde un PMID
├── scripts/openfda.py                 ← bloque regulatorio desde openFDA
├── scripts/eml.py                     ← cobertura frente a la LME
├── scripts/indice.py                  ← build/index.json + jsonld/ + jats/
├── scripts/sitio.py                   ← build/sitio/ para GitHub Pages
├── scripts/reto.py                    ← build/reto.json, URL relativas
└── build/                             ← GENERADO, no se versiona
```

## El desdoblamiento fármaco / ficha

Es la decisión de diseño que más se malinterpreta. Antes de añadir un campo,
pregúntate **si el dato cambia según la indicación**:

| dato | dónde va | ¿depende de la indicación? |
|---|---|---|
| ATC, RxCUI, mecanismo de acción | `farmacos/` | no |
| contraindicación por TFGe | `farmacos/` | no |
| aprobación FDA/EMA de la molécula | `farmacos/` · `regulatorio` | no |
| HR de mortalidad, NNT, certeza GRADE | `fichas/` · `evidencia` | **sí** |
| posología | `fichas/` | **sí** |
| fuerza de la recomendación | `fichas/` · `recomendacion` | **sí** |

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

## Flujo para añadir una ficha

1. **Ubica la indicación en el mapa maestro.** Copia su sección de la LME y su
   oleada.
2. **Comprueba que el fármaco existe** en `farmacos/`. Si no, créalo primero:
   una ficha que apunta a un `FS:` inexistente falla la validación.
3. **Busca la evidencia y trae las referencias**:
   `python scripts/pubmed.py <PMID> <PMID> ...`
4. **Escribe la ficha.** Cada fila de `evidencia` con su `ref`, su `certeza` y,
   si baja de `alta`, sus `razones_descenso`.
5. **Refresca el regulatorio**: `python scripts/openfda.py <nombre>`.
6. `python scripts/build.py`. **No continúes con errores.**
7. `python scripts/indice.py && python scripts/sitio.py` para ver el resultado.

## Qué NO hacer

- No inventes un intervalo de confianza «para que quede completo». Si la fuente
  no lo da, el campo se omite.
- No conviertas una asociación observacional en un enunciado de eficacia. El
  campo `diseno` existe para eso y `build.py` lo exige.
- No edites `build/` a mano: se regenera y se pierde.
- No metas el texto de la ficha técnica de la FDA en el YAML. Se enlaza y se
  resume; copiarlo lo convierte en una obra derivada que no controlamos.
- No hagas que el sitio consulte APIs en tiempo de ejecución. Todo se resuelve
  en el build, como en biosemiotics: el frontend solo lee `index.json`.

## La asimetría con el resto del ecosistema

farmacosemiotics **lee** identidad clínica de medsemiotics-db cuando le hace
falta (por ejemplo, la condición que trata una indicación), pero **no escribe**
en él. Los hechos que pertenezcan al índice compartido —un umbral, un código—
se proponen allí como pull request. Aquí vive la terapéutica, no el vocabulario.
