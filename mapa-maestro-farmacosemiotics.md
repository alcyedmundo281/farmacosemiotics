# Mapa maestro de farmacosemiotics

**Qué poblar y en qué orden.** Léelo al arrancar cualquier sesión y di en voz
alta qué oleada toca antes de escribir nada.

La meta es la **Lista Modelo de Medicamentos Esenciales de la OMS, 24.ª lista
(2025)**, sembrada en [`catalogo/lme-oms-2025.yaml`](catalogo/lme-oms-2025.yaml)
con sus 30 secciones. `python scripts/eml.py` dice en cualquier momento cuánto
falta.

---

## El criterio de orden

No se puebla por orden de número de sección. Se puebla por **densidad de
decisión**: primero los fármacos que un clínico prescribe muchas veces al día y
sobre los que la evidencia manda de verdad. Un antihipertensivo mal usado hace
más daño acumulado que un antineoplásico de nicho, porque se usa mil veces más.

Dentro de cada oleada, primero los **Access** de la clasificación AWaRe y los
del *core list*; los *complementary* después.

---

## Oleada 0 — el piloto (en curso)

Un fármaco y una ficha, para fijar el esquema con un caso que ejercita casi
todos los campos.

| registro | qué prueba |
|---|---|
| `FS:0001` metformina | LME core, EMLc, ATC, contraindicación por función renal, alerta con recuadro de la FDA |
| `FT:0001` metformina en DM2 | evidencia de desenlaces duros, certeza GRADE con descenso razonado, comparador activo |

**Criterio de cierre**: `build.py` limpio, `indice.py` produce JSON-LD válido,
el sitio renderiza y el reto genera al menos una pregunta con URL relativa.

## Oleada 1 — cardiometabólico

Sección 12 (cardiovasculares) y 18.5 (diabetes). Es donde más se prescribe y
donde la evidencia de desenlaces duros es más sólida.

- 12.3 antihipertensivos: enalapril, amlodipino, hidroclorotiazida, losartán
- 12.6 hipolipemiantes: simvastatina, atorvastatina
- 12.5.1 antiagregantes: ácido acetilsalicílico
- 18.5.1 insulinas: insulina humana, análogos de acción prolongada
- 18.5.2 hipoglucemiantes: metformina (hecho), gliclazida, empagliflozina

## Oleada 2 — antiinfecciosos Access

Sección 6.2.1. El eje es AWaRe: la ficha debe decir **por qué este y no el de
espectro más amplio**, que es la decisión que de verdad se toma.

- amoxicilina, amoxicilina + ácido clavulánico, cefalexina
- cotrimoxazol, doxiciclina, metronidazol, nitrofurantoína

## Oleada 3 — dolor y cuidados paliativos

Sección 2. Aquí la ficha tiene que sostener a la vez la eficacia y el daño:
es el terreno donde la prescripción irracional cuesta vidas.

- 2.1 paracetamol, ibuprofeno
- 2.2 morfina, codeína
- 2.3 antieméticos y laxantes de la sección paliativa

## Oleada 4 — salud mental

Sección 24. Fichas largas, comparadores múltiples, certeza casi siempre
moderada o baja. Buen banco de pruebas para el bloque de balance.

## Oleada 5 — migración de los informes de alto costo

Los ~30 informes de la aplicación previa (`informes-conamei-app`): pembrolizumab
(tres indicaciones), secukinumab, ixekizumab, darolutamida, faricimab,
ruxolitinib, trastuzumab deruxtecán, paliperidona, eltrombopag, olaparib,
ribociclib, inmunoglobulina humana.

Van **al final** a propósito. Casi ninguno está en la LME, y el repositorio
tiene que estar maduro antes de aceptar contenido que nació con otra
arquitectura y otro contexto —hay que amputarles todo lo ecuatoriano y
reconstruir la evidencia contra PubMed—.

Al migrar cada uno: el informe original queda como procedencia, **no como
fuente**. Las cifras se vuelven a verificar una por una.

---

## Estado

| oleada | fármacos | fichas | estado |
|---|---|---|---|
| 0 piloto | 1 | 1 | en curso |
| 1 cardiometabólico | 0 | 0 | pendiente |
| 2 antiinfecciosos | 0 | 0 | pendiente |
| 3 dolor y paliativos | 0 | 0 | pendiente |
| 4 salud mental | 0 | 0 | pendiente |
| 5 alto costo | 0 | 0 | pendiente |

## Deudas conocidas

- `catalogo/lme-oms-2025.yaml` tiene `completo: false`: faltan subsecciones que
  el anexo, maquetado a dos columnas, no dejó extraer limpias. Se completan a
  mano contra la fuente, oleada por oleada.
- El catálogo guarda la estructura de secciones, no la lista de medicamentos.
  Cada oleada añade los suyos al poblar, verificados contra el anexo.
- Falta decidir si la 10.ª LME para niños (EMLc) merece fichas propias o solo
  un campo `emlc` en la ficha del adulto. Se decide en la oleada 1, con un caso
  real delante.
