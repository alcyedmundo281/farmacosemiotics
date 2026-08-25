# Mapa maestro de farmacosemiotics

**Qué poblar y en qué orden.** Léelo al arrancar cualquier sesión y di en voz
alta qué oleada toca antes de escribir nada.

La meta es la **Lista Modelo de Medicamentos Esenciales de la OMS, 24.ª lista
(2025)**, sembrada en [`catalogo/lme-oms-2025.yaml`](catalogo/lme-oms-2025.yaml)
con sus 30 secciones, complementada con el catálogo de terapias dirigidas e
inmunooncología de alto impacto. `python scripts/eml.py` mide la cobertura
frente a la LME.

---

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
| **1. Cardiometabólico & Trombosis** | Sección 12 (Cardiovascular) y 18.5 (Diabetes) | `FS0002` (Apixabán) | `FT0002` (Apixabán en FA) | **En curso** |
| **2. Antiinfecciosos AWaRe** | Sección 6.2.1 (Antibióticos Access / Watch) | — | — | Pendiente |
| **3. Dolor & Paliativos** | Sección 2 (Analgésicos, AINEs, Opioides) | — | — | Pendiente |
| **4. Salud Mental & Neuro** | Sección 24 (Antidepresivos, Antipsicóticos) | — | — | Pendiente |
| **5. Terapias Dirigidas & Alto Costo** | Terapias biológicas, oncológicas e inmunomoduladores | `FS0003` (Pembro)<br>`FS0004` (Gusel)<br>`FS0005` (Ibrutinib) | `FT0003` (Pembro en CPNM)<br>`FT0004` (Gusel en PsA)<br>`FT0005` (Ibrutinib en LLC) | **En curso** |

---

## Detalle y Próximos Temas por Oleada

### Oleada 1 — Cardiometabólico & Trombosis (Próximos temas prioritarios)
- [x] **`FT0002` Apixabán en Fibrilación Auricular no valvular** (Anticoagulación de elección frente a warfarina, NNT 59 ictus, NNH menor en hemorragia mayor).
- [ ] **Enalapril / Losartán en Insuficiencia Cardíaca y Nefropatía** (IECA/ARA-II: NNT mortalidad y protección renal, NNH hiperpotasemia/tos).
- [ ] **Amlodipino en Hipertensión Arterial Esencial** (Calcioantagonista: NNT reducción de eventos cardiovasculares, NNH edema maleolar).
- [ ] **Empagliflozina / Dapagliflozina en IC e Insuficiencia Renal Crónica** (iSGLT2: NNT hospitalización por IC, NNH infecciones micóticas).
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
```
