# Mapa maestro de farmacosemiotics

**Qué poblar y en qué orden.** Léelo al arrancar cualquier sesión y di en voz
alta qué oleada toca antes de escribir nada.

La meta es la **Lista Modelo de Medicamentos Esenciales de la OMS, 24.ª lista
(2025)**, sembrada en [`catalogo/lme-oms-2025.yaml`](catalogo/lme-oms-2025.yaml)
con sus 30 secciones, complementada con el catálogo de terapias dirigidas e
inmunooncología de alto impacto. `python scripts/eml.py` mide la cobertura
frente a la LME.

---

## El híbrido: primero se elige, luego se usa

El repositorio dejó de ser un catálogo de fichas para ser dos cosas encadenadas,
en el orden de la decisión clínica:

**Parte I — Selección** (`selecciones/`, código `SEL:`). Un informe por problema
de salud que compara los candidatos en **eficacia, seguridad, conveniencia y
costo** y emite un veredicto. Los ejes van en ese orden y no en orden
alfabético: un fármaco que no funciona no se salva por ser barato, y uno
inseguro no se salva por ser cómodo.

**Parte II — Farmacoterapia** (`farmacoterapia/`, código `FA:`, más `fichas/`).
Cómo se usa la molécula elegida.

La división entre `FA:` y `FT:` responde a la pregunta de siempre —¿de qué
depende el dato?— y es la que estructura el libro:

| | va por | es |
|---|---|---|
| `SEL:` | problema de salud | el informe |
| `FA:` | molécula | el **concepto**: sirve a todas sus indicaciones |
| `FT:` | fármaco × indicación | el **signo**: la decisión situada |

Una farmacoterapia se escribe **una sola vez** y la usan todas las indicaciones
de su fármaco. Lo poco que una cambie va en `variaciones`, dentro de su ficha.

## Qué es ahora una entrada del índice

El índice dejó de ser un catálogo de fichas de evidencia para ser un catálogo
de **guías de práctica clínica farmacoterapéuticas**. La diferencia no es de
extensión sino de pregunta: una ficha pesa el beneficio contra el daño; una
guía dice además qué se pide antes de la primera dosis, cada cuánto se repite,
qué se hace cuando el análisis se tuerce, qué se le dice a quien quiere
quedarse embarazada y de quién es cada acto entre el especialista y el médico
que sigue al paciente.

El estándar de forma son las guías de las sociedades europeas y británicas
—BSR para monitorización y para embarazo y lactancia, BAD para dermatología,
EDF/EADV para las dermatosis autoinmunes graves— y la guía CPIC para la
dosificación por genotipo.

### Los ocho apartados de la capa de guía

| Apartado | Responde a |
|---|---|
| `cribado_basal` | Qué pido antes de la primera dosis, y quién lo pide |
| `farmacogenetica` | De qué genotipo depende la dosis de inicio |
| `monitorizacion` | Qué analítica, cada cuánto, en qué fase |
| `umbrales_accion` | Qué hago con este número anómalo delante |
| `interacciones` | Qué asociación cambia la dosis o la contraindica |
| `reproductivo` | Embarazo, lactancia, periodo de lavado, anticoncepción |
| `atencion_compartida` | De quién es cada acto, y cuándo se suspende sin consultar |
| `posicionamiento` | En qué línea va, y cómo se desescala |

Ninguno es obligatorio, pero **en cuanto uno aparece se valida entero**: media
tabla de monitorización es peor que ninguna, porque parece completa. Y lo que
no tenga fuente publicada no se escribe: se declara en `huecos_declarados` con
su motivo y las referencias que se consultaron sin éxito.

**El trío del pénfigo vulgar es la plantilla:** `SEL0001` compara rituximab,
azatioprina y micofenolato en los cuatro ejes; `FA0009` dice cómo se usa la
azatioprina con seguridad; `FT0009` es la decisión situada en esa indicación.
`FA0009` es además la primera que declara sus huecos en vez de rellenarlos.

## El libro: un solo .qmd, un EPUB, dos partes

`scripts/qmd.py` proyecta TODAS las guías a un único
`build/quarto/guias-farmacoterapeuticas.qmd`, con la bibliografía derivada de
`referencias/` en BibLaTeX y cada cifra citada como `[@clave]`. `scripts/epub.py`
lo encuaderna con Quarto.

El libro sale en dos partes: los informes de selección primero, y después las
farmacoterapias agrupadas **por molécula**, con cada indicación como sección
dentro de su capítulo. Agrupar por molécula es lo que hace visible el caso que
motivó la estructura: una misma farmacoterapia sirviendo a varias indicaciones,
escrita una sola vez.

Que sea un solo fichero es deliberado: el libro se lee y se busca como un
vademécum continuo, y el índice de Quarto ya da la navegación que daría el
troceado. El vínculo con PubMed sobrevive a la encuadernación porque cada
entrada del `.bib` lleva su PMID.

## El depósito: el DOI y la comunidad

El repositorio está archivado en **Zenodo**, dentro de la comunidad
**powersemiotics**, desde el 11 de septiembre de 2026.

| DOI | Qué identifica | Cuándo usarlo |
|---|---|---|
| [`10.5281/zenodo.22700661`](https://doi.org/10.5281/zenodo.22700661) | Todas las versiones | Por defecto. Resuelve siempre a la última |
| [`10.5281/zenodo.22700662`](https://doi.org/10.5281/zenodo.22700662) | Sólo `v0.1.0` | Cuando importe reproducir ese estado exacto del corpus |

Que sean dos números y no uno es lo único que hay que recordar de todo esto, y
es justo lo que ya se confundió una vez: se anunció el de versión como si fuera
el de concepto, y quien hubiera citado por esa etiqueta habría citado la
`v0.1.0` congelada creyendo citar la última. Una prueba del contrato lo vigila
desde entonces —`doi` y la insignia del README han de ser el de concepto—,
porque un identificador que no lleva adonde dice es un `HR` sin PMID con otro
formato.

**Cada release nueva acuña su propio DOI de versión** y lo cuelga del mismo DOI
de concepto. El procedimiento entero está en
[deposito-zenodo.md](deposito-zenodo.md), con la trampa de orden por delante:
Zenodo sólo acuña DOI para las releases posteriores a activar su integración
con GitHub, así que una release cortada antes queda sin DOI para siempre.

Antes de cortar una: subir `version` en `.zenodo.json` **y** en `CITATION.cff`
—los dos, que es lo que se olvida— y `build.py` en verde. Lo que se deposita
queda citable para siempre.

## El Modelo Editorial Ghost & Estándar de Contenido

Cada ficha terapéutica (`fichas/FTxxxx.yaml`) se compila como un **artículo de blog editorial Ghost completo** (`build/sitio/fichas/FTxxxx.html`) y se indexa en el portal principal (`index.html`), revista/catálogo (`blog.html`) y banco de autoevaluación (`reto.html`).

### Estructura Estandarizada Obligatoria por Ficha:
1. **Identidad y Autoría:** ID oficial (`FTxxxx`), título PICO claro, autoría unificada (`Dr. Alcy Edmundo Torres Guerrero` — `powersemiotics.com`).
2. **Decisión Rápida (`decision_clinica`):**
   * **Semáforo:** `verde` (primera línea / beneficio neto), `amarillo` (segunda línea / condicional), `rojo` (desfavorable / no recomendado).
   * **Perla de prescripción:** Una frase accionable para el médico de primer contacto.
   * **Alerta de seguridad inmediata:** Límite crítico (eGFR, interacción letal o contraindicación mayor).
3. **Pregunta PICO:** Población (`p`), Intervención (`i`), Comparador (`c`), Desenlaces (`o`).
4. **Posología Práctica:** Inicio, escalado, mantenimiento, dosis máxima y ajuste por función renal.
5. **Evidencia Cuantitativa (`evidencia`):** Desenlace, criticidad, efecto con IC 95%, **NNT con horizonte temporal**, diseño del estudio, certeza GRADE con razones de descenso, y `pmid:` verificable.
6. **Seguridad Cuantitativa (`seguridad_cuantitativa`):** Evento adverso clave, gravedad (`leve`, `moderada`, `grave`, `letal`, `mortal`), incidencia intervención vs control, **NNH con horizonte temporal**, conducta clínica, y `pmid:` verificable.
7. **Juicio de Balance GRADE & Recomendación:** Magnitud de efectos deseables/indeseables, certeza global, dirección (`a_favor`, `en_contra`, `ninguna`), fuerza (`fuerte`, `condicional`) y justificación.
8. **Alternativas Terapéuticas & Conclusión:** Opciones terapéuticas con código ATC y marca LME si aplica, y síntesis del balance NNT vs NNH.

---

## El Criterio de Priorización por Oleadas

No se puebla por orden ciego de sección. Se puebla por **densidad de decisión clínica**:
primero los fármacos de altísima frecuencia en atención primaria donde el balance NNT/NNH
manda, seguido de los antiinfecciosos AWaRe, dolor, salud mental y las terapias dirigidas de alto costo.

---

## Estado Actual de las Oleadas

La tabla lleva la Parte I delante, que es el orden de la decisión: una guía sin
su informe de selección dice cómo usar un fármaco sin decir por qué se eligió
ése, y `build.py` lo avisa.

| Oleada | Temática / Área Clínica | Selección (`SEL`) | Fármacos (`FS`) | Guías (`FT`) | Estado |
|---|---|---|---|---|---|
| **0. Piloto** | Fármaco modelo y validación de contrato | — *(precede al híbrido)* | `FS0001` (Metformina) | `FT0001` (Metformina en DM2) | **Completada** |
| **1. Cardiometabólico & Trombosis** | Sección 12 (Cardiovascular) y 18.5 (Diabetes) | `SEL0004` (FA no valvular)<br>`SEL0005` (ERC en DM2)<br>`SEL0006` (IC-FEr) | `FS0002` (Apixabán)<br>`FS0006` (Enalapril)<br>`FS0007` (Empagliflozina)<br>`FS0008` (Amlodipino)<br>`FS0011` (Finerenona)<br>`FS0012` (Dapagliflozina) | `FT0002` (Apixabán en FA)<br>`FT0006` (Enalapril en IC-FEr)<br>`FT0007` (Empagliflozina en IC)<br>`FT0008` (Amlodipino en HTA)<br>`FT0012` (Finerenona en ERC-DM2)<br>`FT0013` (Dapagliflozina en IC-FEr) | **En curso (6/8)** |
| **2. Antiinfecciosos AWaRe** | Sección 6.2.1 (Antibióticos Access / Watch) | — | — | — | Pendiente |
| **3. Dolor & Paliativos** | Sección 2 (Analgésicos, AINEs, Opioides) | — | — | — | Pendiente |
| **4. Salud Mental & Neuro** | Sección 24 (Antidepresivos, Antipsicóticos) | `SEL0010` (Esquizofrenia LAI) | `FS0017` (Paliperidona) | `FT0018` (Paliperidona en Esquizofrenia) | **Iniciada (1/3)** |
| **6. Inmunosupresión & Dermatosis Autoinmunes** | Sección 8.1 (Inmunomoduladores para enfermedad no maligna) | `SEL0001` (Pénfigo vulgar)<br>`SEL0002` (Artritis reumatoide)<br>`SEL0003` (Artritis psoriásica) | `FS0009` (Azatioprina)<br>`FS0010` (Metotrexato)<br>`FS0018` (Tofacitinib) | `FT0009` (Azatioprina en pénfigo)<br>`FT0010` (Metotrexato en AR)<br>`FT0011` (Metotrexato en APs)<br>`FT0019` (Tofacitinib en AR) | **En curso (4/6)** — estrena la capa de GPC |
| **5. Terapias Dirigidas & Alto Costo** | Terapias biológicas, oncológicas e inmunomoduladores | `SEL0003` *(compartida con la 6)*<br>`SEL0007` (CPRCnm)<br>`SEL0008` (CPNM EGFR)<br>`SEL0009` (Mama HER2+)<br>`SEL0011` (LLC R/R) | `FS0003` (Pembro)<br>`FS0004` (Gusel)<br>`FS0005` (Ibrutinib)<br>`FS0013` (Secukinumab)<br>`FS0014` (Darolutamida)<br>`FS0015` (Osimertinib)<br>`FS0016` (Trastuzumab deruxtecán)<br>`FS0019` (Acalabrutinib) | `FT0003` (Pembro en CPNM)<br>`FT0004` (Gusel en PsA)<br>`FT0005` (Ibrutinib en LLC)<br>`FT0014` (Secukinumab en psoriasis)<br>`FT0015` (Darolutamida en CPRCnm)<br>`FT0016` (Osimertinib en CPNM)<br>`FT0017` (T-DXd en mama HER2+)<br>`FT0020` (Acalabrutinib en LLC)<br>`FT0021` (Gusel en psoriasis) | **En curso (9/12)** |

Que `SEL0003` aparezca en dos oleadas no es un error de clasificación: es el
híbrido funcionando. Un mismo problema de salud —la artritis psoriásica—
compara un csDMARD clásico contra un biológico, y cada candidato acaba con su
guía en la oleada que le corresponde por coste y por vía.

---

## Detalle y Próximos Temas por Oleada

### Oleada 1 — Cardiometabólico & Trombosis (Próximos temas prioritarios)
- [x] **`FT0002` Apixabán en Fibrilación Auricular no valvular** (Anticoagulación de elección frente a warfarina, NNT 59 ictus, NNH menor en hemorragia mayor).
- [x] **`FT0006` Enalapril en Insuficiencia Cardíaca con FEVI reducida** (IECA: NNT 23 mortalidad global, NNT 10 hospitalización por IC, NNH 53 tos).
- [x] **`FT0007` Empagliflozina en Insuficiencia Cardíaca crónica** (iSGLT2: NNT 20 muerte CV u hospitalización en 16 meses, NNH 56 micosis).
- [x] **`FT0008` Amlodipino en Hipertensión Arterial Esencial** (DHP-CCB: NNT 100 ictus a 5.5 años, NNH 14 edema maleolar).
- [x] **`FT0012` Finerenona en Enfermedad Renal Crónica asociada a Diabetes Tipo 2** (nsMRA: NNT 31 fallo renal o muerte renal a 2.6 años, NNT 56 eventos CV, NNH 72 hiperpotasemia).
- [x] **`FT0013` Dapagliflozina en Insuficiencia Cardíaca con FEVI reducida** (iSGLT2: NNT 21 muerte CV o empeoramiento de IC a 18 meses, NNT 53 muerte CV, NNH 112 micosis).
- [ ] **Atorvastatina / Rosuvastatina en Prevención Secundaria y Primaria** (Estatinas de alta potencia: NNT eventos vasculares mayores vs NNH miopatía).
- [ ] **Ácido Acetilsalicílico en Prevención Secundaria Cardiovascular** (Antiagregación plaquetaria: NNT eventos isquémicos vs NNH hemorragia digestiva).

### Oleada 2 — Antiinfecciosos AWaRe (Access & Watch)
- [ ] **Amoxicilina en Neumonía Adquirida en la Comunidad y Faringitis Estreptocócica**.
- [ ] **Amoxicilina + Ácido Clavulánico en Infecciones Polimicrobianas / Mordeduras**.
- [ ] **Nitrofurantoína / Fosfomicina en Infección del Tracto Urinario no Complicada**.
- [ ] **Cefalexina / Cefazolina en Infecciones de Piel y Partes Blandas**.
- [ ] **Doxiciclina en Neumonía Atípica e Infecciones Transmitidas por Vectores**.
- [ ] **Metronidazol en Infecciones Anaerobias y Giardiasis**.

### Oleada 3 — Dolor & Cuidados Paliativos
- [ ] **Paracetamol en Dolor Leve-Moderado y Fiebre** (Seguridad hepática, NNT analgesia).
- [ ] **Ibuprofeno / Naproxeno en Dolor Inflamatorio Agudo** (AINEs: balance NNT dolor vs NNH hemorragia gastrointestinal y riesgo renal/cardiovascular).
- [ ] **Morfina oral en Dolor Oncológico Moderado a Severo** (Titulación, manejo de estreñimiento preventivo).
- [ ] **Tramadol en Dolor Moderado** (Límite de uso, NNH mareo/náuseas/interacciones serotoninérgicas).

### Oleada 4 — Salud Mental & Neuropsiquiatría
- [x] **`FT0018` Palmitato de Paliperidona en Esquizofrenia** (LAI atípico: NNT 5 prevención de recaídas a 1 año, HR 3.60, baja carga extrapiramidal).
- [ ] **Sertralina / Escitalopram en Trastorno Depresivo Mayor y Ansiedad Generalizada** (ISRS: tiempo de latencia, NNT remisión vs NNH disfunción sexual/síndrome serotoninérgico).
- [ ] **Risperidona en Psicosis y Agitación Aguda** (Antipsicótico: NNT control síntomas vs NNH extrapiramidalismo/metabólico).

### Oleada 5 — Terapias Biológicas, Inmunooncología & Alto Costo
- [x] **`FT0003` Pembrolizumab en Cáncer de Pulmón no Microcítico metastásico** (Anti-PD-1: NNT 8 supervivencia global).
- [x] **`FT0004` Guselkumab en Artritis Psoriásica activa** (Anti-IL-23: NNT 4 respuesta ACR20).
- [x] **`FT0005` Ibrutinib en Leucemia Linfocítica Crónica en primera línea** (Inhibidor BTK: NNT 10 supervivencia libre de progresión).
- [x] **`FT0014` Secukinumab en Psoriasis en Placas moderada a grave** (Anti-IL-17A: NNT 2 respuesta PASI 75 a 12 semanas, NNH 29 candidiasis).
- [x] **`FT0015` Darolutamida en Cáncer de Próstata no metastásico resistente a la castración** (Antiandrógeno 2ª gen: NNT 3 MFS a 2 años, NNT 17 SG a 3 años, sin neurotoxicidad).
- [x] **`FT0016` Osimertinib en Cáncer de Pulmón no Microcítico avanzado EGFR mutado** (TKI 3ª gen: NNT 4 SLP a 18 meses vs TKI activo, NNT 10 SG a 3 años, NNH 48 neumonitis).
- [x] **`FT0017` Trastuzumab Deruxtecán en Cáncer de Mama Metastásico HER2-positivo** (ADC anti-HER2: NNT 3 SLP a 12 meses vs T-DM1, NNT 13 SG, NNH 12 neumonitis).
- [x] **`FT0020` Acalabrutinib en Leucemia Linfocítica Crónica en recaída o refractaria** (Inhibidor selectivo BTK 2ª gen: no-inferioridad SLP vs ibrutinib, NNT 16 daño arrítmico evitado a 41 meses).
- [x] **`FT0021` Guselkumab en Psoriasis en Placas moderada a grave** (Anti-IL-23p19: NNT 2 PASI 90 vs placebo a 16 semanas, NNT 5 vs adalimumab).
- [ ] **Faricimab en Degeneración Macular Asociada a la Edad y Edema Macular Diabético**.
- [ ] **Ruxolitinib en Mielofibrosis y Policitemia Vera**.

### Oleada 6 — Inmunosupresión & Dermatosis Autoinmunes
Es la oleada que estrena la capa de guía, porque es donde la monitorización
manda sobre la eficacia y donde la pregunta reproductiva llega antes que la
terapéutica.
- [x] **`FT0009` Azatioprina en el pénfigo vulgar** (Dosis de inicio por
  genotipo de TPMT y NUDT15, compatible con embarazo y lactancia, desplazada a
  segunda línea por el rituximab. Huecos declarados: umbrales analíticos y
  acuerdo de atención compartida).
- [x] **`FT0010` Metotrexato en artritis reumatoide** (El csDMARD con el
  cronograma de monitorización mejor establecido, y el seleccionado de
  `SEL0002` contra leflunomida, sulfasalazina e hidroxicloroquina).
- [x] **`FT0011` Metotrexato en artritis psoriásica** (Misma molécula, misma
  `FA0010`: el caso que motivó desdoblar la farmacoterapia de la ficha. Lo
  poco que esta indicación cambia del cronograma común va en `variaciones`,
  no en una segunda copia).
- [x] **`FT0019` Tofacitinib en artritis reumatoide tras respuesta inadecuada a metotrexato** (Inhibidor de JAK oral: NNT 5 respuesta ACR20 a 6 meses; balance de seguridad cardiovascular ORAL Surveillance con NNH 34 en herpes zóster).
- [ ] **Rituximab en el pénfigo vulgar moderado y grave** (Primera línea
  aprobada en Europa y Estados Unidos; es la comparación que FT0009 cita y
  todavía no tiene guía propia).
- [ ] **Micofenolato de mofetilo como adyuvante del corticoide** (El otro
  ahorrador clásico, y el contrario de la azatioprina en seguridad
  reproductiva: exige suspenderlo seis semanas antes de concebir).

**El hueco más visible de esta oleada** es que `SEL0001` selecciona el
rituximab y el rituximab no tiene todavía ni `FS:` ni guía. El informe elige
uno y lo único escrito es su alternativa, la azatioprina. Mientras siga así, la
Parte I y la Parte II de esta oleada no se dan la mano.

**Lo que hace falta para cerrar los huecos de esta oleada:** el texto completo
de la guía BSR de csDMARD 2025 (`pmid:41235543`) y de la guía BAD de
azatioprina (`pmid:21950502`). Ninguna de las dos estaba accesible desde el
entorno de compilación cuando se escribió FT0009.

---

## Flujo de Trabajo para Cada Nuevo Tema

```bash
# 1. Crear el principio activo y la ficha con la plantilla oficial
python scripts/nuevo.py seleccion      SEL0002 "Problema de salud"
python scripts/nuevo.py farmaco        FS0010  "NombreMolecula" --atc C09AA02
python scripts/nuevo.py farmacoterapia FA0010  "nombremolecula" --farmaco FS0010
python scripts/nuevo.py ficha          FT0010  "Título de la guía" --farmaco FS0010

# 2. Descargar y verificar referencias con PubMed
python scripts/pubmed.py <PMID_EVIDENCIA>
python scripts/pubmed.py <PMID_SEGURIDAD>

# 3. Completar el YAML con NNT, NNH, GRADE, Semáforo y Posología
# 4. Validar el repositorio (sin errores)
python scripts/build.py

# 5. Generar índices, reto y portal Ghost
python scripts/indice.py
python scripts/reto.py
python scripts/sitio.py

# 6. Probar y verificar contratos
python -m unittest discover -s tests -v

# ...o los pasos 4-6 de una vez, cronometrados
python scripts/pipeline.py

# 7. Encuadernar el EPUB con todas las guías (necesita Quarto)
python scripts/epub.py
```
