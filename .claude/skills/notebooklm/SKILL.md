---
name: notebooklm
description: Controla NotebookLM (https://notebooklm.google.com) por automatización del navegador con la extensión de Claude para Chrome. Úsala siempre que el usuario quiera operar sobre sus cuadernos de NotebookLM — leer contenido, sacar resúmenes o ideas clave, añadir fuentes (URL, texto, ficheros, enlaces de YouTube), generar salidas de Studio (infografías, presentaciones, audio overviews, guías de estudio, briefings, mapas mentales, cronologías, FAQ) o crear cuadernos nuevos. Dispara con cualquier mención de NotebookLM — "abre NotebookLM", "mira mi cuaderno de X", "pregúntale a mi cuaderno sobre X", "añade esto a NotebookLM", "haz una infografía en NotebookLM", "genera un audio overview", "qué dice mi cuaderno sobre X", "open NotebookLM", "add source to my notebook", y cualquier variante donde el objetivo pase por NotebookLM. En la duda, usa la skill — no intentes replicar a mano lo que hace NotebookLM.
---

# NotebookLM

Esta skill maneja NotebookLM por navegador (Claude in Chrome). Cubre cuatro
acciones: leer/extraer, añadir fuentes, generar salidas de Studio y crear
cuadernos.

## Requisito de entorno

Necesita las herramientas de navegador de la extensión de Claude para Chrome
(`tabs_context_mcp`, `computer`, `find`, `navigate`, `form_input`,
`file_upload`). **En una sesión sin esas herramientas —Claude Code en la web o
cualquier contenedor remoto sin extensión— la skill no puede ejecutarse.** Si no
están, dilo de entrada y no finjas el resultado: no hay forma de sustituir la
sesión autenticada de Google del usuario.

---

## Paso 0: siempre aquí

Antes de nada:

1. Llama a `tabs_context_mcp` para obtener un `tabId` válido — todas las
   herramientas de navegador lo exigen.
2. Llama a `computer` (action: `screenshot`) para ver el estado del navegador.
3. Decide si navegar o trabajar desde la página actual.

Si no estás ya en NotebookLM:

```
navigate(url: "https://notebooklm.google.com", tabId: <tab_id>)
```

Y otra captura para confirmar la carga. **Si aparece la pantalla de acceso de
Google, párate y dile al usuario que inicie sesión.** No intentes resolver el
login por tu cuenta.

---

## Abrir el cuaderno correcto

La portada muestra los cuadernos como tarjetas en cuadrícula.

1. Captura para ver qué hay en la página.
2. `find("<nombre del cuaderno> card", tabId)`.
3. Haz clic con el `ref` que devuelve `find`, o por coordenadas de la captura.

Si el usuario no dijo cuál y hay varios, captura la portada y **pregúntale**
antes de seguir. Abrir el cuaderno equivocado y añadirle una fuente es un
desorden que luego limpia él.

---

## Acción: leer / extraer

El chat del cuaderno es la vía de extracción, no el panel de fuentes.

1. Abre el cuaderno.
2. Captura — la caja de chat está abajo al centro.
3. `find("chat input", tabId)` o clic directo desde la captura.
4. Escribe la pregunta con `computer` (action: `type`).
5. Enter: `computer` (action: `key`, text: `Return`).
6. Espera 3–5 s y captura para recoger la respuesta.
7. Devuélvela **formateada y legible**, no el volcado crudo del chat.

El chat está anclado a las fuentes del cuaderno y cita en línea. Para
extracciones amplias («dame todos los puntos clave»), pregunta tal como lo
dirías en voz alta.

---

## Acción: añadir fuentes

Valen URL, enlaces de YouTube, texto pegado, Google Docs/Drive, ficheros
locales — o contenido que generes tú en el momento.

1. Abre el cuaderno.
2. Captura — el panel de Fuentes es la barra izquierda.
3. Pulsa **«+ Add source»** (arriba del panel izquierdo).
4. Se abre un diálogo con los tipos de fuente:

   - **URL / web / YouTube**: opción de enlace, y la URL al campo con
     `form_input` o `type`.
   - **Texto pegado**: «Copied text», clic en el área de texto, y escribe.
   - **Fichero local**: `file_upload` con la ruta absoluta y el `ref` del
     `input` de fichero. **No pulses el botón del selector**: abre un diálogo
     nativo con el que no puedes interactuar.
   - **Google Doc**: opción de Google Docs y sigue el selector de Drive.

5. Confirma con el botón de añadir/subir.
6. Espera la ingesta —NotebookLM muestra un spinner—: `computer`
   (action: `wait`, duration: 5) y captura para verificar que entró.

### Sintetizar contenido y meterlo como fuente

A veces lo que se pide es *crear* el contenido y luego añadirlo: «convierte esta
conversación en un podcast», «investiga X y métemelo en el cuaderno».

1. **Genera o reúne el contenido primero** — investígalo, resúmelo, extráelo o
   redáctalo a partir de lo que el usuario señaló.
2. **Añádelo como «Copied text»**.
3. **Luego** haz lo que pidió (por ejemplo, generar el Audio Overview).

Es el patrón potente: le das a NotebookLM una fuente curada y preprocesada en
vez de una URL cruda, y la salida suele ser bastante mejor.

---

## Acción: salidas de Studio

Studio es el panel derecho, el que genera salidas estructuradas a partir de las
fuentes.

**Tipos disponibles:** Audio Overview (conversación tipo pódcast), Study Guide,
Briefing Doc, Timeline, FAQ, Table of Contents, Infographic, y Slides / Mind Map
(recientes; pueden estar bajo «Discover more»).

1. Abre el cuaderno.
2. Captura — busca el panel Studio a la derecha. Si no lo ves, busca la pestaña
   o el conmutador «Studio».
3. `find` del botón: `find("Infographic button", tabId)`,
   `find("Audio Overview button", tabId)`.
4. **Abre primero el menú de personalización** — cada botón tiene una flechita o
   chevron a su derecha que abre el diálogo de prompt. Pulsa esa, no el botón
   principal.
5. **Escribe un prompt detallado.** No lo dejes en blanco ni te quedes con el
   de por defecto: la diferencia en la salida es grande. Ejemplos:
   - Audio Overview: «Conversación dinámica entre dos presentadores realmente
     entusiasmados con el tema. Céntrate en lo más sorprendente o
     contraintuitivo. Ejemplos concretos, nada de jerga corporativa, accesible
     para público general, energía alta de principio a fin.»
   - Infographic: «Destaca los 5–7 conceptos más importantes con jerarquía
     visual clara. Enfatiza comparaciones y relaciones entre ideas. Flujo lógico
     de arriba abajo.»
   - Study Guide: «Enfoque en aplicación práctica. Escenarios reales en las
     preguntas. Sección de términos clave exhaustiva y con definiciones claras.»
   - Si el usuario dio dirección específica, incorpórala.
6. Confirma el prompt y pulsa Generate.
7. **No esperes a que termine.** Las salidas de Studio —el Audio Overview sobre
   todo— tardan mucho. Confirma que arrancó la generación, dile al usuario que
   está en curso y que NotebookLM le avisará, y cierra ese paso.

Si Infographic, Slides o Mind Map no aparecen, baja el scroll o busca un «+» o
«Discover more»: son funciones recientes y a veces están escondidas.

---

## Acción: crear un cuaderno

1. Desde la portada, «New notebook» o el «+».
2. Se abre vacío.
3. Título: localiza el campo de arriba, clic y escribe.
4. Añade fuentes con el flujo de arriba.
5. NotebookLM genera solo el resumen y las notas cuando acabe de procesar.

---

## Guardar lo que salga

Lo que extraigas y el usuario quiera conservar, guárdalo en su espacio de
trabajo con `Write`, en `.md`. Los ficheros descargados (audio, etc.) caen en la
carpeta de descargas del navegador: dile dónde están.

---

## La frontera con la regla de oro de este repositorio

Esto es lo que esta skill **no** habilita, y es la parte que importa aquí.

**Ninguna salida de NotebookLM entra en un YAML.** Ni en `farmacos/`, ni en
`selecciones/`, ni en `farmacoterapia/`, ni en `fichas/`, ni —sobre todo— en
`referencias/`. Un resumen de NotebookLM es prosa generada a partir de fuentes
que el cuaderno interpretó: no es una cita verificada, y un `HR 0.62 (IC95%
0.51–0.75)` que salga de un chat es exactamente el número inventado con formato
científico contra el que existe la regla de oro.

En concreto:

- **Las referencias siguen naciendo de `python scripts/pubmed.py <PMID>`**, o de
  `--desde-json` con la respuesta literal del MCP de PubMed. Jamás escritas a
  mano desde lo que dijo un cuaderno.
- **Un PMID que mencione NotebookLM es una pista, no una fuente.** Se resuelve
  por `pubmed.py` antes de que sostenga nada.
- **Un umbral, un punto de corte o un cronograma leídos en un cuaderno no se
  escriben.** Si no hay artículo detrás, el apartado va a `huecos_declarados`
  con su motivo, como manda CLAUDE.md.

Para qué sí sirve aquí: reconocer terreno antes de escribir —qué guías existen
para una indicación, qué ejes comparan los candidatos, qué discute la
literatura—, y **divulgar hacia fuera** lo ya publicado (un audio overview o una
infografía a partir del EPUB o de guías ya validadas por `build.py`). Es decir:
NotebookLM va **antes** de la búsqueda formal o **después** del build, nunca en
medio, y nunca como fuente.

---

## Consejos generales

- **Captura constantemente.** NotebookLM es una SPA dinámica y la interfaz varía
  según la cuenta y el despliegue de funciones. En la duda, captura antes de
  actuar.
- **`find` antes de clicar**: devuelve refs estables, más fiables que las
  coordenadas.
- **Espera los procesos asíncronos.** La ingesta de fuentes y la generación de
  Studio lo son. No des nada por hecho sin una captura que lo confirme.
- **El chat es la mejor herramienta de extracción**: preguntarle al cuaderno gana
  casi siempre a raspar el panel de fuentes.
- **Una acción cada vez**: haz el paso, confirma con captura, sigue.

---

## Al terminar

1. Captura final (`save_to_disk: true`) si hay algo visual que enseñar.
2. Resumen claro: qué cuaderno se usó, qué se hizo y cuál fue el resultado.
3. Si extrajiste información, preséntala formateada, no en crudo.
4. Si generaste una salida de Studio, di qué se creó y dónde está.
