# CLAUDE.md — Manual de operación de farmacosemiotics

Este archivo le enseña a cualquier sesión de Claude Code cómo trabajar en este
repositorio. **Léelo completo al arrancar.** No improvises el flujo.

---

## Qué es este proyecto

**El conocimiento terapéutico de holonmed.** holonmed diagnostica con
medsemiotics-db; cuando confirma una condición `HM:`, llega aquí para saber qué
fármaco se elige, cómo se dosifica y cómo se usa con seguridad.

El ecosistema Powersemiotics orbita entero alrededor de holonmed, y este
repositorio se reescribió el 09/11/2026 para servirle (decisión del responsable
clínico). Lo que existía para publicar —sitio, reto, índice JSON-LD y JATS,
libro EPUB, cobertura frente a la Lista Modelo, overlay de costos, depósito en
Zenodo— se borró. Queda en el historial de git, y el depósito de Zenodo
(DOI 10.5281/zenodo.22700661) archiva la versión anterior. Si algún día se
vuelve a publicar, será desde otra arquitectura que lea estos YAML, no desde
este repositorio.

Las cuatro entidades se conservan, en el orden de la decisión:

**Parte I — Selección** (`selecciones/`). Un informe por problema de salud
compara los candidatos en los **cuatro ejes** —eficacia, seguridad,
conveniencia y costo— y emite un veredicto. Cada selección declara la
**condición `HM:`** que trata: es el enlace por el que holonmed llega a ella.

**Parte II — Farmacoterapia** (`farmacoterapia/` y `fichas/`). Elegido el
fármaco, cómo se usa: cribado previo, cronograma, umbrales de acción,
interacciones, reproductivo, atención compartida, posología por indicación.

**En camino — Manejo** (`manejo/`, `MAN:`). Una entrada por condición `HM:`
con las acciones estructuradas de manejo —farmacológicas (que apuntan a
`SEL:`), no farmacológicas, procedimiento, ingreso, derivación, educación,
seguimiento—. Todavía no existe: el primer `MAN:` es la faringitis
estreptocócica (`HM:6009`), en su propio ciclo. El diseño está en el proyecto
HolonMed (`farmacosemiotics-reescritura-y-man.md`).

Alcance **internacional**. Las adaptaciones institucionales (el HECAM, el
CNMB) no son publicables y **no entran en este repositorio público**.

Autor y responsable clínico: **Dr. Alcy Edmundo Torres Guerrero**. Toda
decisión clínica final es suya.

## Regla de oro

**Ningún enunciado de eficacia o seguridad sin PMID resoluble.**

Un `HR 0.62 (IC95% 0.51–0.75)` sin procedencia es un número inventado con
formato científico, y mueve la decisión de un clínico. `build.py` lo trata como
error, no como advertencia.

La prueba práctica antes de escribir cualquier cifra: *¿puedo señalar el
fichero de `referencias/` del que sale?* Si no, no se escribe.

## Lo primero al arrancar una sesión

1. `git status` y reporta el estado.
2. Lee `mapa-maestro-farmacosemiotics.md` y di **qué toca**.
3. Comprueba que hay un clon de medsemiotics-db al lado (o en
   `MEDSEMIOTICS_DB`) con la revisión fijada en `dependencias.yaml`.
4. `python scripts/build.py` y reporta las alertas actuales. El contador de
   farmacoterapias da tres cifras, y son tres preguntas distintas: cuántas **sin
   huecos** (no falta nada), cuántas **con huecos declarados** (falta algo y se
   dice cuál) y cuántas **sin declarar qué les falta** (falta algo y nadie lo ha
   dicho). Esa tercera cifra es la única que señala un descuido.

   La cuarta línea —«N de M traen ya cronograma y umbrales»— es el **formato**,
   no el contenido, y no reparte el total. Confundir ambas cosas fue un fallo
   real del contador.

## Mapa del repositorio

```
farmacosemiotics/
├── CLAUDE.md                          ← este archivo
├── mapa-maestro-farmacosemiotics.md   ← QUÉ poblar y en qué orden (léelo siempre)
├── dependencias.yaml                  ← medsemiotics-db FIJADO por revisión
├── farmacos/*.yaml                    ← principio activo: identidad, ATC, LME, seguridad
├── selecciones/*.yaml                 ← PARTE I: qué fármaco gana, y para qué HM:
├── farmacoterapia/*.yaml              ← PARTE II: cómo se usa la molécula (el concepto)
├── fichas/*.yaml                      ← fármaco × indicación: posología, NNT, NNH, GRADE
├── referencias/*.yaml                 ← artículos con PMID y DOI verificados
├── catalogo/lme-oms-2025.yaml         ← secciones de la LME, para validar `lme.seccion`
├── scripts/nuevo.py                   ← crea plantillas de fármaco, selección o ficha
├── scripts/build.py                   ← valida; NO modifica nada
├── scripts/pubmed.py                  ← crea referencias/ desde un PMID
├── scripts/openfda.py                 ← bloque regulatorio desde openFDA
└── scripts/nnt.py                     ← audita NNT/NNH
```

## El desdoblamiento: tres respuestas, no dos

Es la decisión de diseño que más se malinterpreta, y en la que ya se falló una
vez: la capa de monitorización se escribió dentro de `fichas/` cuando el
cronograma de TPMT, los umbrales analíticos y el perfil reproductivo **no
cambian** entre el pénfigo, el lupus y la enfermedad inflamatoria intestinal.
Son propiedades de la molécula.

Antes de añadir un campo, pregúntate **de qué depende el dato**, y elige entre
tres respuestas:

| depende de… | va en | vocabulario |
|---|---|---|
| la molécula, como identidad | `farmacos/` (`FS:`) | — |
| la molécula, como uso seguro | `farmacoterapia/` (`FA:`) | el **concepto** |
| el problema de salud | `selecciones/` (`SEL:`) | el **informe** |
| el par fármaco × indicación | `fichas/` (`FT:`) | el **signo** |

`FA:` va **1:1 con su `FS:`** y la ficha no lo enlaza: lo deduce de su fármaco,
porque un enlace que se deduce no puede quedar apuntando a otro sitio. Cuando
una indicación se aparta en algo del cronograma común, ese poco se declara en
`variaciones` dentro de la ficha —nunca copiando el apartado entero, que es
como dos copias acaban divergiendo—.

La tabla de detalle, por si la duda es sobre un campo concreto:

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
| cribado previo a la primera dosis | `farmacoterapia/` · `cribado_basal` | no |
| dosis según genotipo (TPMT, NUDT15…) | `farmacoterapia/` · `farmacogenetica` | no |
| cronograma de analíticas por fase | `farmacoterapia/` · `monitorizacion` | no |
| punto de corte y conducta ante la anomalía | `farmacoterapia/` · `umbrales_accion` | no |
| interacción que cambia la dosis | `farmacoterapia/` · `interacciones` | no |
| embarazo, lactancia, lavado, anticoncepción | `farmacoterapia/` · `reproductivo` | no |
| reparto especialista / seguimiento | `farmacoterapia/` · `atencion_compartida` | no |
| línea de tratamiento y desescalamiento | `fichas/` · `posicionamiento` | **sí** |
| lo que esta indicación cambia del cronograma | `fichas/` · `variaciones` | **sí** |
| comparación de candidatos en los 4 ejes | `selecciones/` · `candidatos` | por problema |
| qué eje decidió la elección | `selecciones/` · `criterio_decisorio` | por problema |

Un mismo fármaco tiene tantas fichas como indicaciones evaluadas.
`FS:0001` (metformina) puede sostener `FT:0001` (DM2) y una futura ficha de
síndrome de ovario poliquístico, con evidencia y recomendación distintas.

## Códigos

- **`FS:`, `SEL:`, `FA:`, `FT:` (y `MAN:`, cuando exista) son permanentes.** No se renumeran, no se
  reutilizan, no se reasignan. holonmed los cita en cada tic.
  `FA:` comparte número con su `FS:` porque van 1:1 (FS:0009 ↔ FA:0009); los
  otros dos numeran por su cuenta.
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
- **El recuento manda sobre el porcentaje impreso.** Cuando la fuente publica a
  la vez un recuento y un porcentaje que no concuerdan, se escribe el valor
  aritmético que sale del recuento, y el recuento entero —numerador y
  denominador— se cita al lado para que el lector pueda rehacer la cuenta. Un
  porcentaje no es un hallazgo: es una división, y la fuente puede haberla
  redondeado de dos maneras distintas en la misma frase. Pasó con el ensayo de
  nitrofurantoína frente a fosfomicina (`pmid:29710295`), que imprime el mismo
  `5/247` como «2 %» para las náuseas y como «1 %» para la diarrea; `FT:0039` y
  `FT:0040` consignan 2.0 % en los dos casos, con el recuento delante.
  Esto alcanza **solo** al porcentaje que es la división directa de un recuento
  publicado. No autoriza a recalcular un efecto: un HR, un intervalo de
  confianza, una RRA o un NNT se reproducen tal como los da la fuente aunque no
  sean recíprocos entre sí, y la discrepancia se explica en vez de corregirse.
  Ajustar la cifra de la fuente para que cuadre con otra cifra de la fuente es
  publicar un número que nadie midió.
- **Nada de precios.** Una cifra en moneda no va en ningún registro: caduca y
  no cruza fronteras. El eje `costo` de un informe de selección emite
  un **juicio comparativo** —«genérico oral multifuente» frente a «biológico de
  marca de administración hospitalaria»—, que es internacional y no caduca. Es
  el único de los cuatro ejes que no exige `ref` a un artículo, porque su
  sustento es una propiedad del mercado y no un hallazgo publicado.
- **Los cuatro ejes se responden siempre.** En un informe de selección,
  eficacia, seguridad, conveniencia y costo van los cuatro para cada candidato,
  aunque la respuesta sea `juicio: sin_datos`. Callar un eje deja que el lector
  suponga, y lo que suele suponerse es que era favorable.
- **Un informe que no selecciona no ha terminado.** Exactamente un candidato
  queda `seleccionado`; los demás son `alternativa`, `reservado` o
  `no_seleccionado`. Y hacen falta dos candidatos como mínimo: el juicio de
  cada eje es comparativo y sin comparación no significa nada.
- **Todo registro publicable lleva sus metadatos**: `estado`, `fecha`,
  `actualizado`, `autores` y `licencia`, iguales en las cuatro entidades. Sin
  fecha no se puede citar, sin autoría no tiene responsable clínico y sin
  licencia no se puede reutilizar. `actualizado` nunca es anterior a `fecha`:
  cuando lo es, casi siempre se copió de otra entrada.
- **Nada de contexto institucional ni nacional.** Sin CNMB, sin ARCSA, sin
  RPIS, sin IESS, sin MSP. Las adaptaciones del HECAM no son publicables y no
  entran en este repositorio.
- **Toda `condicion:` resuelve en el índice fijado.** `HM:NNNN` y existente en
  medsemiotics-db en la revisión de `dependencias.yaml`. Un código que no
  resuelve no falla en ninguna parte: deja un diagnóstico sin tratamiento.
  `build.py --exigir-indice` lo convierte en error, y así corre en CI.
- **La certeza GRADE necesita razón.** Una certeza distinta de `alta` sin
  `razones_descenso` es un juicio sin argumento.
- **Fecha de consulta obligatoria** en todo dato traído de una API externa
  (`openfda`, `rxnav`). Un dato regulatorio sin fecha no es verificable.
- **Un hueco se declara, no se rellena.** Si no hay fuente que fije un
  cronograma o un punto de corte, el apartado NO se escribe: se anota en
  `huecos_declarados` con su `motivo` y las `refs` de lo que se consultó sin
  éxito. Un apartado ausente y uno olvidado se leen igual para holonmed, y no son
  lo mismo. `build.py` exige el motivo y falla si el hueco declara vacío un
  bloque que en realidad tiene contenido.
- **Tres estados, no dos, en lo que no se ha podido comprobar.** `lme.presente`
  admite `null` además de `true` y `false`. `null` significa «no comprobado». Poner `false` para quitarse el aviso de encima es afirmar algo que
  no se sabe.

## Flujo para añadir una guía

El orden importa: se elige el fármaco antes de decir cómo se usa.

```bash
python scripts/nuevo.py seleccion      SEL0002 "Artritis reumatoide"
python scripts/nuevo.py farmaco        FS0010  "Metotrexato" --atc L04AX03
python scripts/nuevo.py farmacoterapia FA0010  "metotrexato" --farmaco FS0010
python scripts/nuevo.py ficha          FT0010  "Metotrexato en artritis reumatoide" --farmaco FS0010
```

1. **Ubica la condición en el mapa maestro** y comprueba que existe en
   medsemiotics-db (en la revisión fijada). Si no existe, se propone allí.
2. **Escribe primero el informe de selección** (Parte I), con su
   `condicion: HM:NNNN`: los candidatos, los cuatro ejes de cada uno y el
   veredicto. Si la ficha se escribe antes, la
   elección del fármaco queda sin justificar y `build.py` lo avisa.
3. **Comprueba que el fármaco existe** en `farmacos/`. Si no, créalo primero:
   una ficha que apunta a un `FS:` inexistente falla la validación.
4. **Escribe la farmacoterapia** (Parte II) en `farmacoterapia/`, una sola vez
   por molécula: cribado, farmacogenética, cronograma, umbrales, interacciones,
   reproductivo y atención compartida.
5. **Busca la evidencia y trae las referencias**:
   `python scripts/pubmed.py <PMID> <PMID> ...`
6. **Escribe la ficha** (el signo): `seleccion:` apuntando a su `SEL:`, el
   semáforo, el PICO, la evidencia de ESE desenlace, el `posicionamiento` y el
   balance. Cada fila de `evidencia` con su `ref`, su `certeza` y, si baja de
   `alta`, sus `razones_descenso`. Lo que esta indicación cambie del cronograma
   común va en `variaciones`.
7. **Refresca el regulatorio**: `python scripts/openfda.py <nombre>`.
8. Lo que no tenga fuente publicada va a `huecos_declarados`, con su motivo y
   las `refs` de lo que se consultó sin éxito. Nunca escrito de memoria.
9. `python scripts/build.py --exigir-indice`. **No continúes con errores.**
10. `python -m unittest discover -s tests -v`.

## Qué NO hacer

- No inventes un intervalo de confianza «para que quede completo». Si la fuente
  no lo da, el campo se omite.
- No conviertas una asociación observacional en un enunciado de eficacia. El
  campo `diseno` existe para eso y `build.py` lo exige.
- No metas el cronograma, los umbrales ni el reproductivo dentro de una ficha.
  `build.py` lo rechaza con un error que dice adónde va, porque es el fallo que
  ya se cometió una vez y duplica el mismo dato en cada indicación.
- No inventes un punto de corte «porque es el habitual». Un umbral de
  neutrófilos sin PMID es el mismo fallo que un HR sin PMID, y llega más
  directo a una decisión: alguien suspende un fármaco por ese número.
- No metas el texto de la ficha técnica de la FDA en el YAML. Se enlaza y se
  resume; copiarlo lo convierte en una obra derivada que no controlamos.
- No leas medsemiotics-db en vivo ni desde el árbol de trabajo de un clon: la
  revisión que vale es la de `dependencias.yaml`.

## La relación con medsemiotics-db y con holonmed

**medsemiotics-db, fijado.** Este repositorio lee los códigos de condición del
índice clínico en la revisión exacta de `dependencias.yaml`, del historial de
git y no del árbol de trabajo. Nunca un `fetch` en vivo. Cambiar la revisión es
un PR propio. Los hechos que pertenezcan al índice —una condición que falta, un
código— se proponen allí como pull request; aquí no se acuñan `HM:`.

**holonmed, consumidor.** holonmed fija este repositorio igual que fija el
índice, y cada tic registra con qué revisión razonó. Por eso un campo que
holonmed lee no cambia de forma en silencio: cambiar el esquema de una
entidad es un cambio de contrato y se anuncia en el PR.
