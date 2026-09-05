#!/usr/bin/env python3
"""
NUEVO — Generador de plantilla estandarizada para fármacos y fichas.

Uso:
    python scripts/nuevo.py farmaco FS0009 "Atorvastatina" --atc C10AA05
    python scripts/nuevo.py ficha FT0009 "Atorvastatina en prevención secundaria cardiovascular" --farmaco FS0009
"""
import argparse
import datetime as dt
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent

PLANTILLA_FARMACO = """\
id: '{ident_id}'
tipo: farmaco
dci: {dci}
dci_en: {dci_en}
sinonimos: []
atc: {atc}
clase_farmacologica: '{clase}'
clase_farmacologica_en: ''

lme:
  presente: false
  lista: EML
  edicion: 24
  anio: 2025
  seccion: null
  categoria: null

mecanismo: >-
  Mecanismo de acción detallado del principio activo.
mecanismo_ref: 'fda:label'

farmacocinetica:
  eliminacion: 'Metabolismo hepático / excreción renal'
  vida_media: 'X horas'
  implicacion: >-
    Implicación clínica y consideraciones en insuficiencia renal o hepática.
  ref: 'fda:label'

seguridad:
  reacciones:
    - evento: 'Reacción adversa principal'
      frecuencia: frecuente
      gravedad: leve
      nota: >-
        Descripción clínica y conducta terapéutica recomendada.
      ref: 'fda:label'
"""

PLANTILLA_FICHA = """\
id: '{ident_id}'
tipo: ficha
farmaco: '{farmaco_id}'
titulo: {titulo}
indicacion: {indicacion}
indicacion_en: {indicacion_en}
poblacion: {poblacion}
cie11: ''
estado: borrador
fecha: '{fecha}'
actualizado: '{fecha}'
autores:
  - nombre: Dr. Alcy Edmundo Torres Guerrero
licencia: CC BY-SA 4.0

# ── Decisión Rápida en Punto de Atención ────────────────────────────────────
decision_clinica:
  semaforo: verde  # verde | amarillo | rojo
  perla_prescripcion: >-
    Perla clínica directa y accionable para el médico en punto de atención.
  alerta_seguridad_inmediata: >-
    Límite crítico de seguridad (eGFR, interacción letal o contraindicación mayor).

# ── Pregunta PICO ────────────────────────────────────────────────────────────
pico:
  p: '{poblacion}'
  i: '{titulo}'
  c: 'Placebo o comparador activo estándar'
  o: 'Mortalidad por todas las causas, eventos clínicos mayores, toxicidad grave'

# ── Posología Práctica ───────────────────────────────────────────────────────
posologia:
  inicio: 'Dosis inicial recomendada'
  escalado: 'Pauta de titulación y ajuste progresivo'
  mantenimiento: 'Dosis de mantenimiento'
  maxima: 'Dosis máxima recomendada'
  ajuste_renal: 'Ajuste según filtrado glomerular (eGFR)'
  ref: 'fda:label'

# ── Evidencia Clínica Cuantitativa (Eficacia & NNT) ──────────────────────────
evidencia:
  - desenlace: 'Desenlace primario o mortalidad'
    criticidad: critico
    efecto: 'Reducción relativa (HR 0.80, IC 95 % 0.70–0.90)'
    rra: '4.0%'
    rrr: '20.0%'
    nnt: 25
    horizonte_nnt: a 3 años
    diseno: eca
    estudio: 'Ensayo Pivote (Año)'
    comparador: Placebo
    n: 1000
    certeza: alta
    razones_descenso: []
    ref: 'fda:label'

# ── Seguridad Cuantitativa (Toxicidad & NNH) ─────────────────────────────────
seguridad_cuantitativa:
  - evento: 'Evento adverso clave'
    gravedad: moderada
    tasa_intervencion: '3.0 %'
    tasa_control: '1.0 %'
    ria: '2.0%'
    nnh: 50
    horizonte_nnh: a 1 año
    conducta: 'Conducta clínica ante la aparición del evento.'
    ref: 'fda:label'

# ── La capa de guía de práctica clínica ──────────────────────────────────────
# Todo lo que sigue es OPCIONAL, pero en cuanto un apartado aparece se valida
# entero: media tabla de monitorización es peor que ninguna, porque parece
# completa. Borra los que no apliquen y declara en `huecos_declarados` los que
# apliquen pero no tengan fuente publicada que citar.
#
# Cada `ref` pasa por la regla de oro igual que las de `evidencia`. Un punto de
# corte de neutrófilos sin PMID es el mismo fallo que un HR sin PMID, y llega
# más directo a una decisión: alguien suspende un fármaco por ese número.

# cribado_basal:
#   - prueba: 'Hemograma completo'
#     motivo: 'Qué decisión cambia este resultado antes de la primera dosis'
#     responsable: especialista        # especialista | seguimiento | compartida
#     ref: 'pmid:00000000'

# farmacogenetica:
#   gen: 'TPMT'
#   prueba: 'genotipado antes de la primera dosis'
#   fenotipos:
#     - fenotipo: 'metabolizador lento'
#       frecuencia: '1 de cada 300'
#       dosis: '10 % de la dosis diana'
#       conducta: 'Qué se hace con este fenotipo delante'
#       ref: 'pmid:00000000'

# monitorizacion:
#   - fase: basal                      # basal es la única sin `frecuencia`
#     pruebas: ['Hemograma completo']
#     responsable: especialista
#     ref: 'pmid:00000000'
#   - fase: induccion                  # induccion | mantenimiento | estable
#     periodo: 'Primeras 6 semanas'    # post_suspension
#     pruebas: ['Hemograma completo', 'ALT']
#     frecuencia: 'cada 2 semanas'
#     responsable: compartida
#     ref: 'pmid:00000000'

# umbrales_accion:
#   - parametro: 'Neutrófilos'
#     umbral: '< 1,6 x 10^9/L'
#     accion: 'Suspender y repetir en 1-2 semanas'
#     ref: 'pmid:00000000'

# interacciones:
#   - con: 'Alopurinol'
#     gravedad: mayor                  # contraindicada | mayor | moderada | menor
#     efecto: 'Qué le pasa al fármaco'
#     conducta: 'Qué hace el prescriptor'
#     ref: 'pmid:00000000'

# reproductivo:
#   gestacion:
#     compatibilidad: compatible       # compatible | compatible_con_precaucion
#     enunciado: 'Lo que dice la fuente'   # evitar | contraindicado | sin_datos
#     ref: 'pmid:00000000'
#   lactancia:
#     compatibilidad: sin_datos        # `sin_datos` no exige enunciado: el
#     ref: 'pmid:00000000'             # hueco ya lo dice el propio valor
#   washout:
#     mujer: 'al menos 1 mes antes de concebir'
#     varon: 'no se exige'
#     ref: 'pmid:00000000'
#   anticoncepcion:
#     requerida: true
#     enunciado: 'De alta eficacia durante el tratamiento y 6 meses después'
#     ref: 'pmid:00000000'

# atencion_compartida:
#   especialista: ['Indicar y titular', 'Pedir el cribado basal']
#   seguimiento: ['Repetir la analítica del cronograma']
#   checklist_preinicio: ['Cribado basal completo']
#   suspension_inmediata: ['Neutropenia', 'Ictericia', 'Fiebre sin foco']
#   ref: 'pmid:00000000'

# posicionamiento:
#   linea: primera                     # primera | segunda | tercera | rescate
#   justificacion: 'Por qué va en esa línea'   # no_recomendada
#   escalonado:
#     - linea: primera
#       opciones: ['Fármaco A']
#       nota: 'Cuándo'
#   desescalamiento:
#     enunciado: 'Cómo se baja la dosis'
#     ref: 'pmid:00000000'
#   ref: 'pmid:00000000'

# ── Huecos declarados ────────────────────────────────────────────────────────
# Se buscó fuente para este apartado y no se encontró. Declararlo es lo que
# impide que la guía parezca completa, y silencia el aviso de build.py para ese
# bloque concreto. `bloque` debe ser uno de los ocho de arriba.
#
# huecos_declarados:
#   - bloque: umbrales_accion
#     motivo: >-
#       Por qué no hay tabla aquí. Escribir un umbral verosímil sería
#       justamente el fallo que este repositorio existe para impedir.
#     buscado_en: 'Qué se consultó sin éxito'
#     refs: ['pmid:00000000']

# ── Juicio de Balance GRADE ──────────────────────────────────────────────────
balance:
  efectos_deseables: grande
  efectos_indeseables: pequeno
  certeza_global: alta
  valores_preferencias: no_hay_incertidumbre_importante
  equidad: probablemente_aumenta
  aceptabilidad: si
  factibilidad: si

# ── Recomendación Formal ─────────────────────────────────────────────────────
recomendacion:
  direccion: a_favor
  fuerza: fuerte
  enunciado: >-
    Se recomienda {titulo} en pacientes con {indicacion}.
  ref: 'fda:label'

# ── Alternativas Terapéuticas ────────────────────────────────────────────────
alternativas:
  - dci: 'Fármaco Alternativo'
    atc: 'ATC'
    lme: true
    lme_seccion: '12.3'
    nota: 'Alternativa terapéutica de primera línea.'

conclusion: >-
  Síntesis del balance clínico beneficio-riesgo con base en NNT y NNH.

refs:
  - 'fda:label'
"""


PLANTILLA_SELECCION = """\
# PARTE I — Informe de selección del medicamento.
#
# Va por PROBLEMA DE SALUD, no por fármaco: la pregunta es «de todos los
# candidatos, ¿cuál se elige?», y solo tiene sentido comparando. Por eso hacen
# falta dos candidatos como mínimo y los cuatro ejes en cada uno.
#
# Los ejes van en el orden de la decisión: un fármaco que no funciona no se
# salva por ser barato, y uno inseguro no se salva por ser cómodo.
#
# `sin_datos` es una respuesta legítima. En una enfermedad rara suele ser la
# verdadera, y declararla vale más que suponer una equivalencia que nadie midió.

id: '{ident_id}'
tipo: seleccion
problema: {problema}
problema_en: TODO
cie11: TODO

poblacion: >-
  TODO: a quién se aplica esta decisión.

pregunta: >-
  TODO: en <población>, ¿qué fármaco se selecciona según eficacia, seguridad,
  conveniencia y costo?

estado: borrador
fecha: '{fecha}'
actualizado: '{fecha}'
idioma: es
autores:
  - nombre: Dr. Alcy Edmundo Torres Guerrero
licencia: CC BY-SA 4.0

estrategia:
  - base: PubMed
    consulta: 'TODO[MeSH] AND guideline[pt]'
    fecha: '{fecha}'

# ── Los candidatos ──────────────────────────────────────────────────────
# El juicio es COMPARATIVO: superior o inferior *a los otros de esta tabla*.
#   juicio:    superior | equivalente | inferior | sin_datos
#   veredicto: seleccionado | alternativa | reservado | no_seleccionado
candidatos:
  - dci: TODO Primer candidato
    atc: TODO
    clase: TODO
    eficacia:
      juicio: superior
      sustento: >-
        TODO: por qué, y frente a quién.
      ref: 'pmid:00000000'
    seguridad:
      juicio: equivalente
      sustento: TODO
      ref: 'pmid:00000000'
    conveniencia:
      juicio: equivalente
      sustento: TODO
      ref: 'pmid:00000000'
    costo:
      # El único eje sin `ref` a un artículo: su sustento es una propiedad del
      # mercado. Las cifras en moneda van a costos/<pais>.yaml, nunca aquí.
      juicio: equivalente
      sustento: 'TODO: genérico oral multifuente / biológico de marca / …'
    veredicto: seleccionado
    nota: TODO

  - dci: TODO Segundo candidato
    atc: TODO
    eficacia: {{juicio: inferior, sustento: TODO, ref: 'pmid:00000000'}}
    seguridad: {{juicio: equivalente, sustento: TODO, ref: 'pmid:00000000'}}
    conveniencia: {{juicio: superior, sustento: TODO, ref: 'pmid:00000000'}}
    costo: {{juicio: superior, sustento: TODO}}
    veredicto: alternativa

criterio_decisorio: >-
  TODO: qué eje decidió, y por qué los otros tres no bastaron para moverlo.

conclusion: >-
  TODO: qué se selecciona, qué queda como alternativa y qué huecos deja el
  informe.

refs:
  - 'pmid:00000000'
"""

PLANTILLA_FARMACOTERAPIA = """\
# PARTE II — Farmacoterapia: cómo se usa esta molécula con seguridad.
#
# Es el CONCEPTO y va por molécula, no por indicación: el cronograma, los
# umbrales y el perfil reproductivo no cambian entre un problema y otro. Una
# farmacoterapia sirve a todas las indicaciones de su fármaco; lo poco que una
# cambie se declara en `variaciones` dentro de su ficha, nunca duplicando aquí.
#
# El código FA: es permanente y va 1:1 con su FS:. La ficha no lo enlaza: lo
# deduce de su fármaco.
#
# Los apartados de abajo son opcionales, pero en cuanto uno aparece se valida
# entero. Lo que no tenga fuente publicada va a `huecos_declarados`, con su
# motivo: un apartado ausente y uno olvidado se leen igual, y no son lo mismo.

id: '{ident_id}'
tipo: farmacoterapia
farmaco: '{farmaco_id}'

titulo: Farmacoterapia con {nombre}
titulo_en: TODO

alcance: >-
  TODO: a qué indicaciones sirve tal cual, y qué queda fuera por depender de
  la indicación (dosis diana, línea de tratamiento, balance).

estado: borrador
fecha: '{fecha}'
actualizado: '{fecha}'
idioma: es
autores:
  - nombre: Dr. Alcy Edmundo Torres Guerrero
licencia: CC BY-SA 4.0

# Copia aquí los apartados que apliquen. La plantilla comentada completa está
# en scripts/nuevo.py, en PLANTILLA_FICHA: cribado_basal, farmacogenetica,
# monitorizacion, umbrales_accion, interacciones, reproductivo y
# atencion_compartida.

# huecos_declarados:
#   - bloque: umbrales_accion
#     motivo: >-
#       TODO: por qué no hay tabla aquí.
#     buscado_en: 'TODO'
#     refs: ['pmid:00000000']

refs:
  - 'pmid:00000000'
"""


def slugify(texto):
    s = texto.lower()
    for a, b in [("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n")]:
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def normalizar_id(ident, prefijo):
    limpio = str(ident).upper().replace(":", "").replace("-", "")
    if limpio.startswith(prefijo):
        num = limpio[len(prefijo):]
    else:
        num = limpio
    num = num.zfill(4)
    return f"{prefijo}{num}", f"{prefijo}:{num}"


def main():
    ap = argparse.ArgumentParser(
        description="Crea la plantilla de un fármaco, una selección, una "
                    "farmacoterapia o una guía.")
    ap.add_argument("tipo",
                    choices=["farmaco", "seleccion", "farmacoterapia", "ficha"],
                    help="tipo de registro a crear")
    ap.add_argument("ident",
                    help="identificador oficial (FS0006, SEL0002, FA0006, FT0006)")
    ap.add_argument("nombre",
                    help="DCI, problema de salud o título, según el tipo")
    ap.add_argument("--farmaco", default="FS0001", help="id del fármaco asociado (para fichas)")
    ap.add_argument("--atc", default="", help="código ATC")
    args = ap.parse_args()

    slug = slugify(args.nombre)
    hoy = dt.date.today().isoformat()

    if args.tipo == "seleccion":
        id_fichero, id_yaml = normalizar_id(args.ident, "SEL")
        nombre_fichero = f"{id_fichero}-{slug}.yaml"
        destino = RAIZ / "selecciones" / nombre_fichero
        contenido = PLANTILLA_SELECCION.format(
            ident_id=id_yaml, problema=args.nombre, fecha=hoy)
    elif args.tipo == "farmacoterapia":
        id_fichero, id_yaml = normalizar_id(args.ident, "FA")
        _, farmaco_yaml = normalizar_id(args.farmaco, "FS")
        nombre_fichero = f"{id_fichero}-{slug}.yaml"
        destino = RAIZ / "farmacoterapia" / nombre_fichero
        contenido = PLANTILLA_FARMACOTERAPIA.format(
            ident_id=id_yaml, farmaco_id=farmaco_yaml,
            nombre=args.nombre, fecha=hoy)
    elif args.tipo == "farmaco":
        id_fichero, id_yaml = normalizar_id(args.ident, "FS")
        nombre_fichero = f"{id_fichero}-{slug}.yaml"
        destino = RAIZ / "farmacos" / nombre_fichero
        contenido = PLANTILLA_FARMACO.format(
            ident_id=id_yaml,
            dci=args.nombre,
            dci_en=args.nombre,
            atc=args.atc,
            clase="Clase farmacológica",
        )
    else:
        id_fichero, id_yaml = normalizar_id(args.ident, "FT")
        _, farmaco_yaml = normalizar_id(args.farmaco, "FS")
        nombre_fichero = f"{id_fichero}-{slug}.yaml"
        destino = RAIZ / "fichas" / nombre_fichero
        contenido = PLANTILLA_FICHA.format(
            ident_id=id_yaml,
            farmaco_id=farmaco_yaml,
            titulo=args.nombre,
            indicacion=args.nombre,
            indicacion_en=args.nombre,
            poblacion="Población diana con criterios de inclusión",
            fecha=hoy,
        )

    if destino.exists():
        print(f"Error: {destino} ya existe.", file=sys.stderr)
        return 1

    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(contenido, encoding="utf-8")
    print(f"✓ Creado con éxito: {destino.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
