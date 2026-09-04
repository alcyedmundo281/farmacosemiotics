# Mapa maestro de farmacosemiotics

**Qué poblar y en qué orden.** Léelo al arrancar cualquier sesión y di en voz
alta qué oleada toca antes de escribir nada.

La meta es la **Lista Modelo de Medicamentos Esenciales de la OMS, 24.ª lista
(2025)**, sembrada en [`catalogo/lme-oms-2025.yaml`](catalogo/lme-oms-2025.yaml)
con sus 30 secciones, complementada con el catálogo de terapias dirigidas e
inmunooncología de alto impacto. `python scripts/eml.py` mide la cobertura
frente a la LME.

---

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

**FT0009 (azatioprina en el pénfigo vulgar) es la plantilla.** Es la primera
guía que estrena la capa completa, y también la primera que declara sus huecos
en vez de rellenarlos.

## El libro: un solo .qmd, un EPUB

`scripts/qmd.py` proyecta TODAS las guías a un único
`build/quarto/guias-farmacoterapeuticas.qmd`, con la bibliografía derivada de
`referencias/` en BibLaTeX y cada cifra citada como `[@clave]`. `scripts/epub.py`
lo encuaderna con Quarto.

Que sea un solo fichero y no un capítulo por guía es deliberado: el libro se lee
y se busca como un vademécum continuo, y el índice de Quarto ya da la navegación
que daría el troceado. El vínculo con PubMed sobrevive a la encuadernación
porque cada entrada del `.bib` lleva su PMID.

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

| Oleada | Temática / Área Clínica | Fármacos (`FS`) | Fichas (`FT`) | Estado |
|---|---|---|---|---|
| **0. Piloto** | Fármaco modelo y validación de contrato | `FS0001` (Metformina) | `FT0001` (Metformina en DM2) | **Completada** |
| **1. Cardiometabólico & Trombosis** | Sección 12 (Cardiovascular) y 18.5 (Diabetes) | `FS0002` (Apixabán)<br>`FS0006` (Enalapril)<br>`FS0007` (Empagliflozina)<br>`FS0008` (Amlodipino) | `FT0002` (Apixabán en FA)<br>`FT0006` (Enalapril en IC-FEr)<br>`FT0007` (Empagliflozina en IC)<br>`FT0008` (Amlodipino en HTA) | **En curso (4/6)** |
| **2. Antiinfecciosos AWaRe** | Sección 6.2.1 (Antibióticos Access / Watch) | — | — | Pendiente |
| **3. Dolor & Paliativos** | Sección 2 (Analgésicos, AINEs, Opioides) | — | — | Pendiente |
| **4. Salud Mental & Neuro** | Sección 24 (Antidepresivos, Antipsicóticos) | — | — | Pendiente |
| **6. Inmunosupresión & Dermatosis Autoinmunes** | Sección 8.1 (Inmunomoduladores para enfermedad no maligna) | `FS0009` (Azatioprina) | `FT0009` (Azatioprina en pénfigo vulgar) | **En curso (1/4)** — estrena la capa de GPC |
| **5. Terapias Dirigidas & Alto Costo** | Terapias biológicas, oncológicas e inmunomoduladores | `FS0003` (Pembro)<br>`FS0004` (Gusel)<br>`FS0005` (Ibrutinib) | `FT0003` (Pembro en CPNM)<br>`FT0004` (Gusel en PsA)<br>`FT0005` (Ibrutinib en LLC) | **En curso (3/8)** |

---

## Detalle y Próximos Temas por Oleada

### Oleada 1 — Cardiometabólico & Trombosis (Próximos temas prioritarios)
- [x] **`FT0002` Apixabán en Fibrilación Auricular no valvular** (Anticoagulación de elección frente a warfarina, NNT 59 ictus, NNH menor en hemorragia mayor).
- [x] **`FT0006` Enalapril en Insuficiencia Cardíaca con FEVI reducida** (IECA: NNT 23 mortalidad global, NNT 10 hospitalización por IC, NNH 53 tos).
- [x] **`FT0007` Empagliflozina en Insuficiencia Cardíaca crónica** (iSGLT2: NNT 20 muerte CV u hospitalización en 16 meses, NNH 56 micosis).
- [x] **`FT0008` Amlodipino en Hipertensión Arterial Esencial** (DHP-CCB: NNT 100 ictus a 5.5 años, NNH 14 edema maleolar).
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
- [ ] **Sertralina / Escitalopram en Trastorno Depresivo Mayor y Ansiedad Generalizada** (ISRS: tiempo de latencia, NNT remisión vs NNH disfunción sexual/síndrome serotoninérgico).
- [ ] **Risperidona en Psicosis y Agitación Aguda** (Antipsicótico: NNT control síntomas vs NNH extrapiramidalismo/metabólico).

### Oleada 5 — Terapias Biológicas, Inmunooncología & Alto Costo
- [x] **`FT0003` Pembrolizumab en Cáncer de Pulmón no Microcítico metastásico** (Anti-PD-1: NNT 8 supervivencia global).
- [x] **`FT0004` Guselkumab en Artritis Psoriásica activa** (Anti-IL-23: NNT 4 respuesta ACR20).
- [x] **`FT0005` Ibrutinib en Leucemia Linfocítica Crónica en primera línea** (Inhibidor BTK: NNT 10 supervivencia libre de progresión).
- [ ] **Secukinumab / Ixekizumab en Espondiloartritis y Psoriasis**.
- [ ] **Trastuzumab Deruxtecán en Cáncer de Mama HER2-positivo y HER2-low**.
- [ ] **Darolutamida / Enzalutamida en Cáncer de Próstata Resistente a la Castración**.
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
- [ ] **Rituximab en el pénfigo vulgar moderado y grave** (Primera línea
  aprobada en Europa y Estados Unidos; es la comparación que FT0009 cita y
  todavía no tiene guía propia).
- [ ] **Micofenolato de mofetilo como adyuvante del corticoide** (El otro
  ahorrador clásico, y el contrario de la azatioprina en seguridad
  reproductiva: exige suspenderlo seis semanas antes de concebir).
- [ ] **Metotrexato en artritis reumatoide** (El csDMARD con el cronograma de
  monitorización mejor establecido; el candidato natural para ser la primera
  guía con `umbrales_accion` completos).

**Lo que hace falta para cerrar los huecos de esta oleada:** el texto completo
de la guía BSR de csDMARD 2025 (`pmid:41235543`) y de la guía BAD de
azatioprina (`pmid:21950502`). Ninguna de las dos estaba accesible desde el
entorno de compilación cuando se escribió FT0009.

---

## Flujo de Trabajo para Cada Nuevo Tema

```bash
# 1. Crear el principio activo y la ficha con la plantilla oficial
python scripts/nuevo.py farmaco FS0006 "NombreMolecula" --atc C09AA02
python scripts/nuevo.py ficha FT0006 "Título de la Ficha Clínica" --farmaco FS0006

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
