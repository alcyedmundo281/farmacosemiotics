#!/usr/bin/env python3
"""
VALIDADOR. Lee todo el repositorio y dice qué falta. **No modifica nada.**

    python scripts/build.py
    python scripts/build.py --solo-errores

Expone `cargar()` para que indice.py, sitio.py, reto.py y eml.py trabajen sobre
el mismo estado validado y no cada uno con su propia idea de qué hay dentro.

La regla que más importa está en `regla_de_oro()`: ningún enunciado de eficacia
o seguridad sin PMID resoluble. Es error, no advertencia. Un `HR 0.62` sin
procedencia es un número inventado con formato científico.
"""
import argparse
import re
import sys
from pathlib import Path

import yaml

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent

RE_FS = re.compile(r"^FS:\d{4}$")
RE_FT = re.compile(r"^FT:\d{4}$")
RE_PMID = re.compile(r"^pmid:\d+$")
RE_ATC = re.compile(r"^[A-Z]\d{2}[A-Z]{2}\d{2}$")
RE_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_ARCHIVO_FS = re.compile(r"^FS(\d{4})-[a-z0-9-]+\.yaml$")
RE_ARCHIVO_FT = re.compile(r"^FT(\d{4})-[a-z0-9-]+\.yaml$")
# SEL: el informe de selección, por problema de salud. FA: la farmacoterapia,
# por molécula. Son permanentes igual que FS y FT.
RE_SEL = re.compile(r"^SEL:\d{4}$")
RE_FA = re.compile(r"^FA:\d{4}$")
RE_ARCHIVO_SEL = re.compile(r"^SEL(\d{4})-[a-z0-9-]+\.yaml$")
RE_ARCHIVO_FA = re.compile(r"^FA(\d{4})-[a-z0-9-]+\.yaml$")

# Fuentes que NO son artículos y por eso no viven en referencias/. Cada una
# exige `url` y `consultado` en el bloque donde aparece: un dato regulatorio
# sin fecha de consulta no es verificable, porque la fuente cambia sin avisar.
PREFIJOS_NO_PMID = ("fda:", "ema:", "who:", "oms:", "openfda:", "rxnav:", "dailymed:")

DISENOS = {"metaanalisis", "revision_sistematica", "eca", "ensayo_clinico",
           "cohorte", "casos_controles", "transversal", "serie_casos",
           "guia", "consenso"}
CERTEZAS = {"alta", "moderada", "baja", "muy_baja"}
# Las cinco razones de descenso de GRADE, más una sexta propia para el análisis
# que no era la comparación principal del ensayo. Cerrar la lista evita que el
# mismo motivo se escriba de tres maneras y deje de agregarse en el índice.
RAZONES_DESCENSO = {"riesgo_de_sesgo", "inconsistencia", "evidencia_indirecta",
                    "imprecision", "sesgo_de_publicacion", "caracter_secundario"}
MAGNITUDES = {"grande", "moderado", "pequeno", "trivial", "no_se_sabe"}
DIRECCIONES = {"a_favor", "en_contra", "ninguna"}
FUERZAS = {"fuerte", "condicional"}
ESTADOS = {"borrador", "revisado", "publicado"}
CRITICIDAD = {"critico", "importante", "no_importante"}
SEMAFOROS = {"verde", "amarillo", "rojo"}
GRAVEDADES_SEGURIDAD = {"leve", "moderada", "grave", "letal", "mortal"}

# ── Vocabularios de la capa de guía de práctica clínica ──────────────────
# Una GPC farmacoterapéutica no se distingue de una ficha por escribir más,
# sino por responder a lo que el prescriptor tiene delante: qué pido antes de
# la primera dosis, cada cuánto lo repito, qué hago cuando el análisis se
# tuerce, y qué le digo a quien quiere quedarse embarazada.
FASES = {"basal", "induccion", "mantenimiento", "estable", "post_suspension"}
GRAVEDAD_INTERACCION = {"contraindicada", "mayor", "moderada", "menor"}
# `sin_datos` es una respuesta legítima y frecuente en seguridad reproductiva:
# el hueco se declara, no se rellena con una tranquilidad que nadie midió.
COMPATIBILIDAD = {"compatible", "compatible_con_precaucion", "evitar",
                  "contraindicado", "sin_datos"}
LINEAS = {"primera", "segunda", "tercera", "rescate", "no_recomendada"}
# Quién responde de cada acto. Es lo que un acuerdo de atención compartida
# existe para fijar: sin esto, el cribado basal lo acaba pidiendo nadie.
RESPONSABLES = {"especialista", "seguimiento", "compartida"}

# ── Los cuatro ejes de la selección de medicamentos ──────────────────────
# Eficacia, seguridad, conveniencia y costo. El orden importa y no es
# alfabético: es el de la decisión. Un fármaco que no funciona no se salva por
# ser barato, y uno inseguro no se salva por ser cómodo.
# Todo lo que puede citar un artículo, y por tanto todo lo que pasa por la
# regla de oro, por el veto a los precios y por el veto al contexto de un país.
COLECCIONES_CITABLES = ("farmacos", "farmacoterapias", "selecciones", "fichas")

# ── El contrato de metadatos, igual para las cuatro entidades ────────────
# Un registro sin fecha no se puede citar, uno sin autoría no tiene
# responsable clínico y uno sin licencia no se puede reutilizar. Los tres
# huecos se notan tarde: cuando alguien intenta hacer justo eso.
#
# `idioma` tiene defecto porque el repositorio es en español, pero se declara:
# el día que entre una entrada en otra lengua, el índice y el JATS tienen que
# poder decirlo sin adivinarlo por el texto.
METADATOS = ("estado", "fecha", "actualizado", "autores", "licencia")
IDIOMA_POR_DEFECTO = "es"
# La etiqueta legible de cada tipo, y de paso la lista cerrada de tipos: un
# `tipo:` mal escrito manda el registro a la carpeta equivocada del sitio.
TIPOS = {"farmaco": "principio activo",
         "farmacoterapia": "farmacoterapia",
         "seleccion": "informe de selección",
         "ficha": "guía"}

EJES = ("eficacia", "seguridad", "conveniencia", "costo")
# El juicio es siempre COMPARATIVO —superior a qué— y por eso el informe
# necesita más de un candidato para significar algo.
JUICIOS = {"superior", "equivalente", "inferior", "sin_datos"}
VEREDICTOS = {"seleccionado", "alternativa", "reservado", "no_seleccionado"}
# Los apartados que una guía puede declarar pendientes. Un hueco declarado y
# uno olvidado se leen igual en el documento final, y no son lo mismo: el
# primero dice que se buscó fuente y no la hubo.
BLOQUES_GPC = {"cribado_basal", "farmacogenetica", "monitorizacion",
               "umbrales_accion", "interacciones", "reproductivo",
               "atencion_compartida", "posicionamiento"}

# El repositorio es internacional. Estos términos delatan que se coló contexto
# de un país concreto —el origen de este proyecto fue ecuatoriano— y eso
# pertenece a costos/, no al núcleo.
RE_LOCAL = re.compile(r"\b(CNMB|ARCSA|RPIS|CONAMEI|IESS|MSP)\b")
# Un precio dentro de farmacos/ o fichas/ está en el sitio equivocado.
RE_PRECIO = re.compile(r"(?:USD|EUR|US\$|\$)\s?\d")


class Informe:
    def __init__(self):
        self.errores = []
        self.avisos = []

    def error(self, donde, texto):
        self.errores.append((donde, texto))

    def aviso(self, donde, texto):
        self.avisos.append((donde, texto))


def leer_yaml(ruta, inf):
    try:
        with ruta.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        inf.error(ruta.name, "no es YAML válido: " + str(e))
        return None


def recorrer(nodo, ruta=""):
    """Todos los pares (ruta, valor) del árbol. Base de los chequeos globales."""
    if isinstance(nodo, dict):
        for k, v in nodo.items():
            yield from recorrer(v, ruta + "." + str(k) if ruta else str(k))
    elif isinstance(nodo, list):
        for i, v in enumerate(nodo):
            yield from recorrer(v, ruta + "[" + str(i) + "]")
    else:
        yield ruta, nodo


def refs_de(nodo):
    """Toda `ref` y todo elemento de `refs` del árbol, con su ruta."""
    for ruta, valor in recorrer(nodo):
        if not isinstance(valor, str):
            continue
        hoja = ruta.split(".")[-1]
        if hoja == "ref" or re.match(r"^refs(\[\d+\])?$", hoja):
            yield ruta, valor


# ───────────────────────────── carga ─────────────────────────────

def cargar(inf=None):
    """Lee las cuatro colecciones y el catálogo. No valida: solo lee.

    El reparto sigue la pregunta del desdoblamiento —¿de qué depende el dato?—
    y ahora tiene tres respuestas, no dos:

      farmacos/        de la molécula: identidad, ATC, LME, regulatorio
      farmacoterapia/  de la molécula: cómo se usa con seguridad (el concepto)
      selecciones/     del problema de salud: qué fármaco gana (el informe)
      fichas/          del par fármaco × indicación (el signo)
    """
    inf = inf or Informe()
    estado = {"farmacos": {}, "fichas": {}, "referencias": {},
              "selecciones": {}, "farmacoterapias": {}, "catalogo": None,
              "archivos": {}, "informe": inf}

    for carpeta, clave, patron in (("farmacos", "farmacos", RE_ARCHIVO_FS),
                                   ("farmacoterapia", "farmacoterapias", RE_ARCHIVO_FA),
                                   ("selecciones", "selecciones", RE_ARCHIVO_SEL),
                                   ("fichas", "fichas", RE_ARCHIVO_FT),
                                   ("referencias", "referencias", None)):
        if not (RAIZ / carpeta).is_dir():
            continue
        for ruta in sorted((RAIZ / carpeta).glob("*.yaml")):
            if patron and not patron.match(ruta.name):
                inf.error(ruta.name, "el nombre del fichero no sigue el patrón "
                                     "del ecosistema (FS0001-slug.yaml)")
            reg = leer_yaml(ruta, inf)
            if reg is None:
                continue
            ident = reg.get("id")
            if not ident:
                inf.error(ruta.name, "no tiene `id`")
                continue
            if ident in estado[clave]:
                inf.error(ruta.name, "el id " + str(ident) + " ya lo usa "
                          + estado["archivos"][ident])
                continue
            estado[clave][ident] = reg
            estado["archivos"][ident] = ruta.name

    cat = RAIZ / "catalogo" / "lme-oms-2025.yaml"
    if cat.exists():
        estado["catalogo"] = leer_yaml(cat, inf)
    else:
        inf.aviso("catalogo/", "no hay catálogo de la LME: eml.py no podrá "
                               "medir la cobertura")
    return estado


# ─────────────────────────── chequeos ───────────────────────────

def regla_de_oro(estado, inf):
    """Ningún enunciado de eficacia o seguridad sin PMID resoluble."""
    for coleccion in COLECCIONES_CITABLES:
        for ident, reg in estado[coleccion].items():
            archivo = estado["archivos"][ident]
            for ruta, ref in refs_de(reg):
                if ref.startswith(PREFIJOS_NO_PMID):
                    continue
                if not RE_PMID.match(ref):
                    inf.error(archivo, ruta + ": `" + ref + "` no es un "
                              "`pmid:` ni una fuente institucional reconocida")
                    continue
                if ref not in estado["referencias"]:
                    inf.error(archivo, ruta + ": `" + ref + "` no resuelve. "
                              "Tráelo con `python scripts/pubmed.py "
                              + ref.split(":")[1] + "`")
                    continue
                referencia = estado["referencias"][ref]
                if (referencia.get("verificacion") or {}).get("retractado"):
                    inf.error(archivo, ruta + ": `" + ref + "` está RETRACTADO. "
                              "Un artículo retractado no sostiene un enunciado.")


def revisar_referencia(ident, reg, archivo, inf):
    if not RE_PMID.match(str(ident)):
        inf.error(archivo, "el id `" + str(ident) + "` no tiene la forma pmid:N")
    for campo in ("clave_bibtex", "tipo", "titulo", "publicacion", "anio"):
        if not reg.get(campo):
            inf.error(archivo, "falta `" + campo + "`")
    ver = reg.get("verificacion") or {}
    if not ver.get("pubmed"):
        inf.error(archivo, "no está verificada contra PubMed")
    if not RE_FECHA.match(str(ver.get("fecha", ""))):
        inf.error(archivo, "`verificacion.fecha` debe ser YYYY-MM-DD")


def revisar_farmaco(ident, reg, archivo, estado, inf):
    if not RE_FS.match(str(ident)):
        inf.error(archivo, "el id `" + str(ident) + "` no tiene la forma FS:NNNN")
    m = RE_ARCHIVO_FS.match(archivo)
    if m and str(ident) != "FS:" + m.group(1):
        inf.error(archivo, "el id no concuerda con el número del fichero")

    for campo in ("dci", "dci_en", "mecanismo", "clase_farmacologica"):
        if not reg.get(campo):
            inf.error(archivo, "falta `" + campo + "`")

    atc = reg.get("atc")
    if atc and not RE_ATC.match(str(atc)):
        inf.error(archivo, "`atc: " + str(atc) + "` no es un código ATC de 7 "
                           "caracteres (p. ej. A10BA02)")
    elif not atc:
        inf.aviso(archivo, "sin código ATC: el sitio no podrá agruparlo por clase")

    lme = reg.get("lme")
    if isinstance(lme, dict) and lme.get("presente") is None:
        inf.aviso(archivo, "`lme.presente` sin comprobar: el fármaco no consta "
                           "ni dentro ni fuera de la Lista Modelo, y eml.py lo "
                           "contará como fuera")
    if not isinstance(lme, dict):
        inf.error(archivo, "falta el bloque `lme` (aunque el fármaco no esté "
                           "en la Lista Modelo: entonces `presente: false`)")
    elif lme.get("presente"):
        if not lme.get("seccion"):
            inf.error(archivo, "`lme.presente: true` sin `lme.seccion`")
        if lme.get("categoria") not in ("core", "complementary"):
            inf.error(archivo, "`lme.categoria` debe ser core o complementary")
        secciones = secciones_catalogo(estado)
        sec = str(lme.get("seccion", ""))
        if secciones and sec.split(".")[0] not in secciones:
            inf.error(archivo, "`lme.seccion: " + sec + "` no existe en el "
                               "catálogo de la LME")

    for r in reg.get("seguridad", {}).get("reacciones", []) or []:
        if not r.get("evento"):
            inf.error(archivo, "una reacción adversa sin `evento`")
        if not r.get("ref"):
            inf.error(archivo, "la reacción `" + str(r.get("evento")) + "` no "
                               "tiene `ref`: es un enunciado de seguridad sin "
                               "procedencia")

    for a in reg.get("alertas", []) or []:
        if isinstance(a, dict) and not a.get("consultado"):
            inf.error(archivo, "una alerta sin `consultado`: un dato "
                               "regulatorio sin fecha no es verificable")

    reg_val = reg.get("regulatorio")
    if isinstance(reg_val, list):
        for r in reg_val:
            if isinstance(r, dict):
                if not r.get("agencia"):
                    inf.error(archivo, "una entrada de `regulatorio` sin `agencia`")
                if not r.get("consultado") and not r.get("estado"):
                    inf.error(archivo, "`regulatorio` de " + str(r.get("agencia"))
                              + " sin `consultado`")
    elif isinstance(reg_val, dict):
        for ag, datos in reg_val.items():
            if isinstance(datos, dict) and not datos.get("consultado") and not datos.get("aprobado"):
                pass


def revisar_ficha(ident, reg, archivo, estado, inf):
    if not RE_FT.match(str(ident)):
        inf.error(archivo, "el id `" + str(ident) + "` no tiene la forma FT:NNNN")
    m = RE_ARCHIVO_FT.match(archivo)
    if m and str(ident) != "FT:" + m.group(1):
        inf.error(archivo, "el id no concuerda con el número del fichero")

    farmaco = reg.get("farmaco")
    if not farmaco:
        inf.error(archivo, "falta `farmaco`")
    elif farmaco not in estado["farmacos"]:
        inf.error(archivo, "`farmaco: " + str(farmaco) + "` no existe en "
                           "farmacos/. Crea el fármaco antes que la ficha.")

    # ── Parte I: el informe de selección que sostiene esta ficha ────────
    seleccion = reg.get("seleccion")
    if seleccion and seleccion not in estado["selecciones"]:
        inf.error(archivo, "`seleccion: " + str(seleccion) + "` no existe en "
                           "selecciones/")
    elif not seleccion:
        inf.aviso(archivo, "sin `seleccion`: la guía dice cómo usar el fármaco "
                           "pero no por qué se eligió ese y no otro")

    # ── Parte II: la farmacoterapia se hereda del fármaco, no se enlaza ──
    if farmaco and not farmacoterapia_de(farmaco, estado):
        inf.aviso(archivo, "su fármaco no tiene farmacoterapia en "
                           "farmacoterapia/: la guía saldrá sin cronograma, "
                           "sin umbrales y sin seguridad reproductiva")

    # Guardia de migración: estos bloques vivían en la ficha y ahora son del
    # fármaco. Dejarlos aquí los duplicaría, y dos copias del mismo cronograma
    # divergen en cuanto alguien corrige una.
    intrusos = sorted(b for b in BLOQUES_GPC
                      if b != "posicionamiento" and reg.get(b))
    if intrusos:
        inf.error(archivo, "lleva " + ", ".join("`" + b + "`" for b in intrusos)
                  + ": eso no depende de la indicación y va en "
                    "farmacoterapia/, no en la ficha. `posicionamiento` sí se "
                    "queda, porque la línea de tratamiento sí cambia con el "
                    "problema de salud.")

    # `variaciones`: lo poco que esta indicación cambia de la farmacoterapia
    # base. Es el caso de una molécula que sirve a varias indicaciones.
    for i, v in enumerate(reg.get("variaciones") or []):
        eti = "variaciones[" + str(i) + "]"
        if not isinstance(v, dict):
            inf.error(archivo, eti + " debería ser un bloque con `bloque`")
            continue
        if v.get("bloque") not in BLOQUES_GPC:
            inf.error(archivo, eti + " `bloque: " + str(v.get("bloque"))
                      + "` no es un apartado de la farmacoterapia")
        _exige(inf, archivo, eti, v, ("cambio", "ref"))

    for campo in ("titulo", "indicacion", "poblacion", "conclusion"):
        if not reg.get(campo):
            inf.error(archivo, "falta `" + campo + "`")

    pico = reg.get("pico") or {}
    faltan = [k for k in ("p", "i", "c", "o") if not pico.get(k)]
    if faltan:
        inf.error(archivo, "el PICO está incompleto: falta " + ", ".join(faltan))

    evidencia = reg.get("evidencia") or []
    if not evidencia:
        inf.error(archivo, "sin `evidencia`: una ficha sin desenlaces no es una "
                           "evaluación, es una descripción")
    for i, e in enumerate(evidencia):
        eti = "evidencia[" + str(i) + "]"
        if not e.get("desenlace"):
            inf.error(archivo, eti + " sin `desenlace`")
        if e.get("criticidad") and e["criticidad"] not in CRITICIDAD:
            inf.error(archivo, eti + " `criticidad` debe ser uno de "
                      + ", ".join(sorted(CRITICIDAD)))
        if e.get("diseno") not in DISENOS:
            inf.error(archivo, eti + " `diseno: " + str(e.get("diseno"))
                      + "` no está en la lista. Sin diseño no se puede leer el "
                        "peso de la cifra.")
        certeza = e.get("certeza")
        if certeza not in CERTEZAS:
            inf.error(archivo, eti + " `certeza` debe ser uno de "
                      + ", ".join(sorted(CERTEZAS)))
        elif certeza != "alta" and not e.get("razones_descenso"):
            inf.error(archivo, eti + " certeza `" + certeza + "` sin "
                      "`razones_descenso`: es un juicio GRADE sin argumento")
        for r in e.get("razones_descenso") or []:
            if r not in RAZONES_DESCENSO:
                inf.error(archivo, eti + " `razones_descenso: " + str(r)
                          + "` no está en la lista cerrada ("
                          + ", ".join(sorted(RAZONES_DESCENSO)) + ")")
        if not e.get("ref"):
            inf.error(archivo, eti + " sin `ref`")

    balance = reg.get("balance") or {}
    for campo in ("efectos_deseables", "efectos_indeseables"):
        if balance.get(campo) not in MAGNITUDES:
            inf.error(archivo, "`balance." + campo + "` debe ser uno de "
                      + ", ".join(sorted(MAGNITUDES)))
    if balance.get("certeza_global") not in CERTEZAS:
        inf.error(archivo, "`balance.certeza_global` debe ser uno de "
                  + ", ".join(sorted(CERTEZAS)))

    rec = reg.get("recomendacion") or {}
    if rec.get("direccion") not in DIRECCIONES:
        inf.error(archivo, "`recomendacion.direccion` debe ser uno de "
                  + ", ".join(sorted(DIRECCIONES)))
    if rec.get("direccion") in ("a_favor", "en_contra") and rec.get("fuerza") not in FUERZAS:
        inf.error(archivo, "`recomendacion.fuerza` debe ser fuerte o condicional")
    if not rec.get("enunciado"):
        inf.error(archivo, "`recomendacion` sin `enunciado`")

    # Decisión rápida y semáforo
    dc = reg.get("decision_clinica")
    if dc:
        if dc.get("semaforo") and dc["semaforo"] not in SEMAFOROS:
            inf.error(archivo, "`decision_clinica.semaforo` debe ser uno de "
                      + ", ".join(sorted(SEMAFOROS)))
        if not dc.get("perla_prescripcion"):
            inf.aviso(archivo, "`decision_clinica` sin `perla_prescripcion`")

    # Seguridad cuantitativa (NNH)
    seg_c = reg.get("seguridad_cuantitativa") or []
    for j, s in enumerate(seg_c):
        eti_s = "seguridad_cuantitativa[" + str(j) + "]"
        if not s.get("evento"):
            inf.error(archivo, eti_s + " sin `evento`")
        if s.get("gravedad") and s["gravedad"] not in GRAVEDADES_SEGURIDAD:
            inf.error(archivo, eti_s + " `gravedad` debe ser uno de "
                      + ", ".join(sorted(GRAVEDADES_SEGURIDAD)))
        if not s.get("ref"):
            inf.error(archivo, eti_s + " sin `ref`")

    # Una recomendación fuerte sobre certeza baja es posible, pero es la
    # excepción de GRADE y tiene que estar argumentada, no dejada caer.
    if (rec.get("fuerza") == "fuerte"
            and balance.get("certeza_global") in ("baja", "muy_baja")
            and not rec.get("justificacion_fuerza")):
        inf.aviso(archivo, "recomendación fuerte con certeza "
                  + str(balance.get("certeza_global")) + " y sin "
                  "`justificacion_fuerza`: en GRADE eso es una excepción")


# ─────────────────── la capa de guía de práctica clínica ───────────────────
# Estos bloques son opcionales en el esquema, pero en cuanto uno aparece se
# valida entero. Es deliberado: media tabla de monitorización es peor que
# ninguna, porque parece completa. Y todo enunciado sigue pasando por
# `regla_de_oro()`, que recorre cualquier `ref` del árbol, así que un punto de
# corte sin procedencia no llega al índice.

def _exige(inf, archivo, eti, dic, campos):
    """Campos sin los cuales el bloque no le sirve a quien prescribe."""
    for c in campos:
        if not dic.get(c):
            inf.error(archivo, eti + " sin `" + c + "`")


def _en(inf, archivo, eti, dic, campo, permitidos, obligatorio=False):
    v = dic.get(campo)
    if v is None or v == "":
        if obligatorio:
            inf.error(archivo, eti + " sin `" + campo + "`")
        return
    if v not in permitidos:
        inf.error(archivo, eti + " `" + campo + ": " + str(v) + "` no está en "
                  "la lista cerrada (" + ", ".join(sorted(permitidos)) + ")")


def revisar_gpc(ident, reg, archivo, inf):
    """Cribado, monitorización, umbrales, interacciones, reproductivo,
    atención compartida y posicionamiento."""

    revisar_huecos(reg, archivo, inf)

    # ── Cribado basal: qué se pide ANTES de la primera dosis ──────────────
    for i, c in enumerate(reg.get("cribado_basal") or []):
        eti = "cribado_basal[" + str(i) + "]"
        if not isinstance(c, dict):
            inf.error(archivo, eti + " debería ser un bloque con `prueba`")
            continue
        _exige(inf, archivo, eti, c, ("prueba", "motivo", "ref"))
        _en(inf, archivo, eti, c, "responsable", RESPONSABLES)

    # ── Farmacogenética: la dosis que depende del genotipo ────────────────
    fg = reg.get("farmacogenetica")
    if isinstance(fg, dict):
        _exige(inf, archivo, "farmacogenetica", fg, ("gen",))
        fenotipos = fg.get("fenotipos") or []
        if not fenotipos:
            inf.error(archivo, "`farmacogenetica` sin `fenotipos`: nombrar el "
                               "gen no le dice a nadie qué dosis poner")
        for i, f in enumerate(fenotipos):
            eti = "farmacogenetica.fenotipos[" + str(i) + "]"
            if not isinstance(f, dict):
                inf.error(archivo, eti + " debería ser un bloque")
                continue
            _exige(inf, archivo, eti, f, ("fenotipo", "conducta", "ref"))
    elif fg is not None:
        inf.error(archivo, "`farmacogenetica` debería ser un bloque con `gen`")

    # ── Cronograma de monitorización, por fases ───────────────────────────
    fases_vistas = []
    for i, m in enumerate(reg.get("monitorizacion") or []):
        eti = "monitorizacion[" + str(i) + "]"
        if not isinstance(m, dict):
            inf.error(archivo, eti + " debería ser un bloque con `fase`")
            continue
        _en(inf, archivo, eti, m, "fase", FASES, obligatorio=True)
        _en(inf, archivo, eti, m, "responsable", RESPONSABLES)
        fases_vistas.append(m.get("fase"))
        if not m.get("pruebas"):
            inf.error(archivo, eti + " sin `pruebas`: una fase sin analítica "
                                     "no es un cronograma")
        # La fase basal es la única que no se repite: se hace una vez.
        if m.get("fase") != "basal" and not m.get("frecuencia"):
            inf.error(archivo, eti + " sin `frecuencia`: «monitorizar» sin "
                                     "cada cuánto no es una instrucción")
        if not m.get("ref"):
            inf.error(archivo, eti + " sin `ref`")
    if fases_vistas and "induccion" not in fases_vistas:
        inf.aviso(archivo, "`monitorizacion` sin fase de inducción: el riesgo "
                           "de citopenia se concentra en las primeras semanas")

    # ── Qué hacer cuando el análisis se tuerce ────────────────────────────
    for i, u in enumerate(reg.get("umbrales_accion") or []):
        eti = "umbrales_accion[" + str(i) + "]"
        if not isinstance(u, dict):
            inf.error(archivo, eti + " debería ser un bloque con `parametro`")
            continue
        # `umbral` y `accion` juntos o ninguno: un punto de corte sin conducta
        # deja al clínico con un número y sin decisión, que es donde se falla.
        _exige(inf, archivo, eti, u, ("parametro", "umbral", "accion", "ref"))

    # ── Interacciones que cambian la dosis o la contraindican ─────────────
    for i, x in enumerate(reg.get("interacciones") or []):
        eti = "interacciones[" + str(i) + "]"
        if not isinstance(x, dict):
            inf.error(archivo, eti + " debería ser un bloque con `con`")
            continue
        _exige(inf, archivo, eti, x, ("con", "efecto", "conducta", "ref"))
        _en(inf, archivo, eti, x, "gravedad", GRAVEDAD_INTERACCION,
            obligatorio=True)

    # ── Seguridad reproductiva ────────────────────────────────────────────
    rep = reg.get("reproductivo")
    if isinstance(rep, dict):
        for etapa in ("gestacion", "lactancia"):
            e = rep.get(etapa)
            if e is None:
                continue
            if not isinstance(e, dict):
                inf.error(archivo, "`reproductivo." + etapa + "` debería ser "
                                   "un bloque con `compatibilidad`")
                continue
            eti = "reproductivo." + etapa
            _en(inf, archivo, eti, e, "compatibilidad", COMPATIBILIDAD,
                obligatorio=True)
            # `sin_datos` es la única compatibilidad que no exige enunciado:
            # el hueco ya está dicho por el propio valor.
            campos = ("ref",) if e.get("compatibilidad") == "sin_datos" \
                else ("enunciado", "ref")
            _exige(inf, archivo, eti, e, campos)

        wo = rep.get("washout")
        if isinstance(wo, dict):
            if not (wo.get("mujer") or wo.get("varon")):
                inf.error(archivo, "`reproductivo.washout` sin `mujer` ni "
                                   "`varon`: el periodo de lavado se declara "
                                   "para quien lo necesita, y son dos plazos "
                                   "distintos")
            if not wo.get("ref"):
                inf.error(archivo, "`reproductivo.washout` sin `ref`")
        elif wo is not None:
            inf.error(archivo, "`reproductivo.washout` debería ser un bloque "
                               "con `mujer` y/o `varon`")

        anti = rep.get("anticoncepcion")
        if isinstance(anti, dict):
            _exige(inf, archivo, "reproductivo.anticoncepcion", anti,
                   ("enunciado", "ref"))
        elif anti is not None:
            inf.error(archivo, "`reproductivo.anticoncepcion` debería ser un "
                               "bloque con `enunciado`")
    elif rep is not None:
        inf.error(archivo, "`reproductivo` debería ser un bloque")

    # ── Atención compartida: de quién es cada acto ────────────────────────
    ac = reg.get("atencion_compartida")
    if isinstance(ac, dict):
        if not (ac.get("especialista") or ac.get("seguimiento")):
            inf.error(archivo, "`atencion_compartida` no reparte nada: hacen "
                               "falta `especialista` y `seguimiento`")
        if not ac.get("suspension_inmediata"):
            inf.aviso(archivo, "`atencion_compartida` sin "
                               "`suspension_inmediata`: es el criterio que el "
                               "médico de seguimiento necesita sin consultar")
        if not ac.get("ref"):
            inf.error(archivo, "`atencion_compartida` sin `ref`")
    elif ac is not None:
        inf.error(archivo, "`atencion_compartida` debería ser un bloque")

    # ── Posicionamiento terapéutico y desescalamiento ─────────────────────
    pos = reg.get("posicionamiento")
    if isinstance(pos, dict):
        _en(inf, archivo, "posicionamiento", pos, "linea", LINEAS,
            obligatorio=True)
        if not pos.get("ref"):
            inf.error(archivo, "`posicionamiento` sin `ref`")
        for i, e in enumerate(pos.get("escalonado") or []):
            eti = "posicionamiento.escalonado[" + str(i) + "]"
            if not isinstance(e, dict):
                inf.error(archivo, eti + " debería ser un bloque con `linea`")
                continue
            _en(inf, archivo, eti, e, "linea", LINEAS, obligatorio=True)
            if not e.get("opciones"):
                inf.error(archivo, eti + " sin `opciones`")
        des = pos.get("desescalamiento")
        if isinstance(des, dict):
            _exige(inf, archivo, "posicionamiento.desescalamiento", des,
                   ("enunciado", "ref"))
        elif des is not None:
            inf.error(archivo, "`posicionamiento.desescalamiento` debería ser "
                               "un bloque con `enunciado`")
    elif pos is not None:
        inf.error(archivo, "`posicionamiento` debería ser un bloque")


def revisar_huecos(reg, archivo, inf):
    """`huecos_declarados` convierte una ausencia en una afirmación: se buscó
    fuente para este apartado y no se encontró. Por eso exige motivo, y por
    eso chirría si el bloque que declara vacío está en realidad relleno."""
    for i, h in enumerate(reg.get("huecos_declarados") or []):
        eti = "huecos_declarados[" + str(i) + "]"
        if not isinstance(h, dict):
            inf.error(archivo, eti + " debería ser un bloque con `bloque`")
            continue
        bloque = h.get("bloque")
        if bloque not in BLOQUES_GPC:
            inf.error(archivo, eti + " `bloque: " + str(bloque) + "` no es un "
                      "apartado de la guía (" + ", ".join(sorted(BLOQUES_GPC))
                      + ")")
        elif reg.get(bloque):
            inf.error(archivo, eti + " declara vacío `" + str(bloque)
                      + "`, pero el apartado tiene contenido")
        if not h.get("motivo"):
            inf.error(archivo, eti + " sin `motivo`: un hueco sin explicar no "
                                     "se distingue de un olvido")


def huecos_de(reg):
    return {h.get("bloque") for h in reg.get("huecos_declarados") or []
            if isinstance(h, dict)}


def es_gpc(reg):
    """Una ficha que ya responde como guía: trae cronograma y conducta ante
    la anomalía analítica, no solo el balance NNT/NNH."""
    return bool(reg.get("monitorizacion")) and bool(reg.get("umbrales_accion"))


# ───────────── PARTE I: el informe de selección (por indicación) ─────────────
# Un fármaco no se elige porque funcione, sino porque funciona mejor que las
# alternativas en el balance de los cuatro ejes. Ese juicio depende del
# problema de salud y no de la molécula, y por eso vive aquí y no en
# `farmacos/`: la misma azatioprina gana en una indicación y pierde en otra.

def revisar_metadatos(ident, reg, archivo, tipo_esperado, inf):
    """Lo que todo registro publicable necesita, sea del tipo que sea."""
    if reg.get("tipo") != tipo_esperado:
        inf.error(archivo, "`tipo: " + str(reg.get("tipo")) + "` no concuerda "
                  "con la carpeta: aquí van registros `" + tipo_esperado + "`")

    for campo in METADATOS:
        if not reg.get(campo):
            inf.error(archivo, "falta `" + campo + "`: sin él el registro no "
                      "se puede " + {"estado": "situar en el flujo editorial",
                                     "fecha": "citar",
                                     "actualizado": "comparar con su versión previa",
                                     "autores": "atribuir a un responsable clínico",
                                     "licencia": "reutilizar"}[campo])

    if reg.get("estado") and reg["estado"] not in ESTADOS:
        inf.error(archivo, "`estado` debe ser uno de " + ", ".join(sorted(ESTADOS)))

    fechas = {}
    for campo in ("fecha", "actualizado"):
        v = reg.get(campo)
        if v is None:
            continue
        if not RE_FECHA.match(str(v)):
            inf.error(archivo, "`" + campo + "` debe ser YYYY-MM-DD")
        else:
            fechas[campo] = str(v)
    # Una fecha de actualización anterior a la de creación es casi siempre un
    # copiar y pegar de otra entrada, y falsea el orden del índice.
    if len(fechas) == 2 and fechas["actualizado"] < fechas["fecha"]:
        inf.error(archivo, "`actualizado` (" + fechas["actualizado"] + ") es "
                  "anterior a `fecha` (" + fechas["fecha"] + ")")

    autores = reg.get("autores")
    if autores is not None:
        if not isinstance(autores, list):
            inf.error(archivo, "`autores` debe ser una lista")
        else:
            for i, a in enumerate(autores):
                if not isinstance(a, dict) or not a.get("nombre"):
                    inf.error(archivo, "autores[" + str(i) + "] sin `nombre`")

    idioma = reg.get("idioma", IDIOMA_POR_DEFECTO)
    if not isinstance(idioma, str) or len(idioma) not in (2, 5):
        inf.error(archivo, "`idioma: " + str(idioma) + "` debería ser un "
                           "código ISO 639-1 como `es` o `es-EC`")


def revisar_seleccion(ident, reg, archivo, inf):
    if not RE_SEL.match(str(ident)):
        inf.error(archivo, "el id `" + str(ident) + "` no tiene la forma SEL:NNNN")
    m = RE_ARCHIVO_SEL.match(archivo)
    if m and str(ident) != "SEL:" + m.group(1):
        inf.error(archivo, "el id no concuerda con el número del fichero")

    for campo in ("problema", "pregunta", "conclusion"):
        if not reg.get(campo):
            inf.error(archivo, "falta `" + campo + "`")

    candidatos = reg.get("candidatos") or []
    if len(candidatos) < 2:
        inf.error(archivo, "un informe de selección con menos de dos "
                           "candidatos no compara nada: el juicio de cada eje "
                           "es comparativo y necesita contra qué")

    seleccionados = 0
    for i, c in enumerate(candidatos):
        eti = "candidatos[" + str(i) + "]"
        if not isinstance(c, dict):
            inf.error(archivo, eti + " debería ser un bloque con `dci`")
            continue
        if not c.get("dci"):
            inf.error(archivo, eti + " sin `dci`")
        atc = c.get("atc")
        if atc and not RE_ATC.match(str(atc)):
            inf.error(archivo, eti + " `atc: " + str(atc) + "` no es un código "
                                     "ATC de 7 caracteres")

        _en(inf, archivo, eti, c, "veredicto", VEREDICTOS, obligatorio=True)
        if c.get("veredicto") == "seleccionado":
            seleccionados += 1

        # Los cuatro ejes: ninguno es opcional. Callar uno es dejar que el
        # lector suponga, y lo que suele suponerse es que era favorable.
        for eje in EJES:
            bloque = c.get(eje)
            eti_e = eti + "." + eje
            if bloque is None:
                inf.error(archivo, eti_e + " no está: los cuatro ejes se "
                          "responden siempre, aunque la respuesta sea "
                          "`juicio: sin_datos`")
                continue
            if not isinstance(bloque, dict):
                inf.error(archivo, eti_e + " debería ser un bloque con `juicio`")
                continue
            _en(inf, archivo, eti_e, bloque, "juicio", JUICIOS, obligatorio=True)
            if not bloque.get("sustento"):
                inf.error(archivo, eti_e + " sin `sustento`: un juicio sin "
                                           "argumento no se puede discutir")
            # El costo es el único eje que no exige `ref` a un artículo: su
            # sustento es una propiedad del mercado (genérico multifuente,
            # biológico de marca), no un hallazgo publicado. Las cifras viven
            # en costos/ y no aquí.
            if eje != "costo" and bloque.get("juicio") != "sin_datos" \
                    and not bloque.get("ref"):
                inf.error(archivo, eti_e + " sin `ref`")

    if candidatos and not seleccionados:
        inf.error(archivo, "ningún candidato queda `seleccionado`: un informe "
                           "de selección que no selecciona no ha terminado")
    if seleccionados > 1:
        inf.aviso(archivo, str(seleccionados) + " candidatos `seleccionado`: "
                  "si de verdad empatan, conviene decirlo en `criterio_decisorio`")


# ──────── PARTE II: la farmacoterapia (por molécula, es el concepto) ────────
# El cronograma de TPMT, el reproductivo y los umbrales analíticos no cambian
# entre el pénfigo y el lupus: son propiedades de la molécula. Por eso la
# farmacoterapia se escribe una vez por fármaco y la sirven todas sus
# indicaciones, que declaran en `variaciones` lo poco que difiera.

def revisar_farmacoterapia(ident, reg, archivo, estado, inf):
    if not RE_FA.match(str(ident)):
        inf.error(archivo, "el id `" + str(ident) + "` no tiene la forma FA:NNNN")
    m = RE_ARCHIVO_FA.match(archivo)
    if m and str(ident) != "FA:" + m.group(1):
        inf.error(archivo, "el id no concuerda con el número del fichero")

    farmaco = reg.get("farmaco")
    if not farmaco:
        inf.error(archivo, "falta `farmaco`")
    elif farmaco not in estado["farmacos"]:
        inf.error(archivo, "`farmaco: " + str(farmaco) + "` no existe en "
                           "farmacos/. Crea el fármaco antes que su "
                           "farmacoterapia.")

    for campo in ("titulo", "alcance"):
        if not reg.get(campo):
            inf.error(archivo, "falta `" + campo + "`")

    # Los ocho apartados y sus huecos declarados se validan igual que antes:
    # lo que cambió es dónde viven, no qué se les exige.
    revisar_gpc(ident, reg, archivo, inf)


def farmacoterapia_de(farmaco, estado):
    """La farmacoterapia de un fármaco, o None. Es 1:1, así que la ficha no
    necesita enlazarla: se deduce, y un enlace que se deduce no puede quedar
    apuntando a otro sitio tras un renombrado."""
    for reg in estado["farmacoterapias"].values():
        if reg.get("farmaco") == farmaco:
            return reg
    return None


def secciones_catalogo(estado):
    cat = estado.get("catalogo") or {}
    return {str(s.get("numero")) for s in cat.get("secciones", [])}


def revisar_higiene(estado, inf):
    """Lo que delata que un registro se salió del contrato del repositorio."""
    for coleccion in COLECCIONES_CITABLES:
        for ident, reg in estado[coleccion].items():
            archivo = estado["archivos"][ident]
            for ruta, valor in recorrer(reg):
                if not isinstance(valor, str):
                    continue
                m = RE_LOCAL.search(valor)
                if m:
                    inf.error(archivo, ruta + ": menciona `" + m.group(1)
                              + "`. El núcleo es internacional; lo de un país "
                                "concreto va en costos/.")
                if RE_PRECIO.search(valor):
                    inf.error(archivo, ruta + ": lleva un precio. Los precios "
                              "viven en costos/<pais>.yaml, con su moneda y su "
                              "fecha.")


def revisar_huerfanos(estado, inf):
    citadas = set()
    for coleccion in COLECCIONES_CITABLES:
        for reg in estado[coleccion].values():
            for _, ref in refs_de(reg):
                citadas.add(ref)
    for ident in estado["referencias"]:
        if ident not in citadas:
            inf.aviso(estado["archivos"][ident],
                      "referencia que no cita nadie todavía")

    for ident, reg in estado["farmacoterapias"].items():
        if not es_gpc(reg):
            declarados = huecos_de(reg)
            falta = [n for n, k in (("cronograma de monitorización", "monitorizacion"),
                                    ("umbrales de acción", "umbrales_accion"))
                     if not reg.get(k) and k not in declarados]
            if falta:
                inf.aviso(estado["archivos"][ident],
                          "la farmacoterapia todavía no está completa: le "
                          "falta " + " y ".join(falta))

    con_fa = {f.get("farmaco") for f in estado["farmacoterapias"].values()}
    for ident in estado["farmacos"]:
        if ident not in con_fa:
            inf.aviso(estado["archivos"][ident],
                      "fármaco sin farmacoterapia: nadie ha escrito todavía "
                      "cómo se usa con seguridad")

    con_ficha = {f.get("farmaco") for f in estado["fichas"].values()}
    for ident in estado["farmacos"]:
        if ident not in con_ficha:
            inf.aviso(estado["archivos"][ident],
                      "fármaco sin ninguna ficha: aún no evalúa ninguna indicación")


# ───────────────────────────── informe ─────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Valida el repositorio. No modifica nada.")
    ap.add_argument("--solo-errores", action="store_true",
                    help="calla las advertencias")
    args = ap.parse_args()

    inf = Informe()
    estado = cargar(inf)

    for ident, reg in estado["referencias"].items():
        revisar_referencia(ident, reg, estado["archivos"][ident], inf)
    for ident, reg in estado["farmacos"].items():
        revisar_farmaco(ident, reg, estado["archivos"][ident], estado, inf)
    # El contrato de metadatos primero y para todos: si falla, lo demás se
    # valida igual, pero el informe deja claro que el fallo es editorial y no
    # clínico.
    for coleccion, tipo in (("farmacos", "farmaco"),
                            ("farmacoterapias", "farmacoterapia"),
                            ("selecciones", "seleccion"),
                            ("fichas", "ficha")):
        for ident, reg in estado[coleccion].items():
            revisar_metadatos(ident, reg, estado["archivos"][ident], tipo, inf)

    for ident, reg in estado["selecciones"].items():
        revisar_seleccion(ident, reg, estado["archivos"][ident], inf)
    for ident, reg in estado["farmacoterapias"].items():
        revisar_farmacoterapia(ident, reg, estado["archivos"][ident], estado, inf)
    for ident, reg in estado["fichas"].items():
        revisar_ficha(ident, reg, estado["archivos"][ident], estado, inf)

    regla_de_oro(estado, inf)
    revisar_higiene(estado, inf)
    revisar_huerfanos(estado, inf)

    fa = estado["farmacoterapias"]
    completas = [i for i, r in fa.items() if es_gpc(r)]
    declarados = [i for i, r in fa.items() if not es_gpc(r) and huecos_de(r)]

    print("farmacosemiotics — validación")
    print("  fármacos          " + str(len(estado["farmacos"])))
    print("  selecciones       " + str(len(estado["selecciones"]))
          + "   parte I: qué fármaco gana, por problema de salud")
    print("  farmacoterapias   " + str(len(fa))
          + "   parte II: " + str(len(completas)) + " completas, "
          + str(len(declarados)) + " con huecos declarados")
    print("  guías             " + str(len(estado["fichas"]))
          + "   fármaco × indicación")
    print("  referencias       " + str(len(estado["referencias"])))
    print("")

    if inf.errores:
        print("ERRORES (" + str(len(inf.errores)) + ")")
        for donde, texto in inf.errores:
            print("  " + donde + ": " + texto)
        print("")
    if inf.avisos and not args.solo_errores:
        print("avisos (" + str(len(inf.avisos)) + ")")
        for donde, texto in inf.avisos:
            print("  " + donde + ": " + texto)
        print("")

    if inf.errores:
        print("No continúes con errores.")
        return 1
    print("Sin errores.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
