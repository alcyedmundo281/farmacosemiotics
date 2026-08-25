#!/usr/bin/env python3
"""
NUEVO — Generador de plantilla estandarizada para fármacos y fichas.

Uso:
    python scripts/nuevo.py farmaco FS0006 "Semaglutida" --atc A10BJ06
    python scripts/nuevo.py ficha FT0006 "Semaglutida en diabetes tipo 2 y obesidad" --farmaco FS0006
"""
import argparse
import datetime as dt
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

PLANTILLA_FARMACO = """\
# yaml-language-server: $schema=../esquemas/farmaco.schema.json
id: {ident}
tipo: farmaco
dci: '{dci}'
dci_en: '{dci_en}'
atc: '{atc}'
clase_farmacologica: '{clase}'

lme:
  presente: false
  seccion: null
  categoria: null

mecanismo: >
  Mecanismo de acción del principio activo.

formas:
  - forma: comprimido
    via: oral
    concentraciones:
      - 500 mg

seguridad:
  contraindicaciones:
    - motivo: Hipersensibilidad al principio activo
      ref: pmid:00000000
  embarazo:
    categoria_fda: null
    resumen: Datos limitados en gestación.
    ref: pmid:00000000
  lactancia:
    compatible: false
    resumen: Se desconoce su excreción en leche materna.
    ref: pmid:00000000

refs:
  - pmid:00000000
"""

PLANTILLA_FICHA = """\
# yaml-language-server: $schema=../esquemas/ficha.schema.json
id: {ident}
tipo: ficha
titulo: '{titulo}'
titulo_en: '{titulo_en}'
farmaco: {farmaco}
indicacion: '{indicacion}'
indicacion_en: '{indicacion_en}'
poblacion: '{poblacion}'
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
  perla_prescripcion: >
    Perla clínica en una frase accionable para el médico de primer contacto.
  alerta_seguridad_inmediata: >
    Límite o contraindicación crítica a verificar antes de prescribir.

# ── Pregunta PICO ────────────────────────────────────────────────────────────
pico:
  p: '{poblacion}'
  i: '{titulo}'
  c: 'Placebo o comparador activo estándar'
  o: 'Mortalidad total, eventos cardiovasculares mayores, eventos adversos graves'

# ── Posología Práctica ───────────────────────────────────────────────────────
posologia:
  inicio: 'Dosis inicial de titulación'
  escalado: 'Pauta de ajuste progresivo'
  mantenimiento: 'Dosis estándar de mantenimiento'
  maxima: 'Dosis máxima recomendada'
  ajuste_renal: 'Ajuste según tasa de filtrado glomerular (eGFR)'

# ── Evidencia Clínica Cuantitativa (Eficacia & NNT) ──────────────────────────
evidencia:
  - desenlace: 'Mortalidad global o desenlace primario'
    criticidad: critico
    efecto: 'HR 0.85 (IC 95 % 0.75-0.95)'
    nnt: 20
    horizonte_nnt: 'a 3 años'
    diseno: eca
    estudio: 'Ensayo Pivot (AÑO)'
    certeza: moderada
    razones_descenso:
      - imprecision
    ref: pmid:00000000

# ── Seguridad Cuantitativa (Toxicidad & NNH) ─────────────────────────────────
seguridad_cuantitativa:
  - evento: 'Evento adverso clave de seguridad'
    gravedad: grave
    tasa_intervencion: '2.5 %'
    tasa_control: '1.0 %'
    nnh: 67
    horizonte_nnh: 'a 1 año'
    conducta: 'Monitorización periódica o ajuste de dosis.'
    ref: pmid:00000000

# ── Juicio de Balance GRADE ──────────────────────────────────────────────────
balance:
  efectos_deseables: grande
  efectos_indeseables: pequeno
  certeza_global: moderada
  valores_preferencias: no_hay_incertidumbre_importante
  equidad: probablemente_aumenta
  aceptabilidad: si
  factibilidad: si

# ── Recomendación Formal ─────────────────────────────────────────────────────
recomendacion:
  direccion: a_favor
  fuerza: fuerte
  enunciado: >
    Se recomienda {titulo} en pacientes con {indicacion}.
  ref: pmid:00000000

# ── Alternativas Terapéuticas ────────────────────────────────────────────────
alternativas:
  - dci: 'Fármaco Alternativo'
    atc: 'ATC'
    lme: true
    lme_seccion: '18.5'
    nota: 'Opción terapéutica alternativa en caso de intolerancia o contraindicación.'

conclusion: >
  Síntesis razonada del balance beneficio-riesgo con énfasis en NNT frente a NNH.

refs:
  - pmid:00000000
"""


def slugify(texto):
    s = texto.lower()
    for a, b in [("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n")]:
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def main():
    ap = argparse.ArgumentParser(description="Crea una plantilla estandarizada de fármaco o ficha.")
    ap.add_argument("tipo", choices=["farmaco", "ficha"], help="tipo de registro a crear")
    ap.add_argument("ident", help="identificador oficial (ej. FS0006 o FT0006)")
    ap.add_argument("nombre", help="nombre del fármaco (DCI) o título de la ficha")
    ap.add_argument("--farmaco", default="FS0001", help="id del fármaco asociado (para fichas)")
    ap.add_argument("--atc", default="", help="código ATC")
    args = ap.parse_args()

    ident = args.ident.upper().replace(":", "")
    slug = slugify(args.nombre)
    hoy = dt.date.today().isoformat()

    if args.tipo == "farmaco":
        nombre_fichero = f"{ident}-{slug}.yaml"
        destino = RAIZ / "farmacos" / nombre_fichero
        contenido = PLANTILLA_FARMACO.format(
            ident=ident,
            dci=args.nombre,
            dci_en=args.nombre,
            atc=args.atc,
            clase="Clase farmacológica",
        )
    else:
        nombre_fichero = f"{ident}-{slug}.yaml"
        destino = RAIZ / "fichas" / nombre_fichero
        contenido = PLANTILLA_FICHA.format(
            ident=ident,
            titulo=args.nombre,
            titulo_en=args.nombre,
            farmaco=args.farmaco,
            indicacion=args.nombre,
            indicacion_en=args.nombre,
            poblacion="Población diana con criterios de inclusión",
            fecha=hoy,
        )

    if destino.exists():
        print(f"Error: {destino} ya existe.", file=sys.stderr)
        return 1

    destino.write_text(contenido, encoding="utf-8")
    print(f"✓ Creado: {destino.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
