#!/usr/bin/env python3
"""
ÍNDICE — modelo PubMed/PMC.

  ÍNDICE (build/index.json) = PubMed. Fichas de metadatos. NUNCA el cuerpo.
  YAML del repositorio        = PMC. El texto estructurado completo.

Ese reparto es lo que permite a la vez un buscador con facetas que carga un
solo fichero, un reto que enlaza con URL relativas y un depósito JATS. Si el
índice llevara el cuerpo, el buscador tendría que descargar el repositorio
entero para filtrar por sección de la LME.

    python scripts/indice.py

Produce en build/:
  index.json      registros ricos → el buscador
  jsonld/*.json   schema.org por registro (Google y sistemas de IA)
  jats/*.xml      JATS por ficha, para depósito y archivo
"""
import datetime as dt
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))

from build import (cargar, RAIZ, es_gpc, huecos_de,  # noqa: E402
                   EJES, farmacoterapia_de)

SALIDA = RAIZ / "build"
BASE = "https://powersemiotics.com/farmacosemiotics/"
REPO = "https://github.com/alcyedmundo281/farmacosemiotics"
AUTOR_POR_DEFECTO = [{"nombre": "Dr. Alcy Edmundo Torres Guerrero"}]


CARPETA = {"ficha": "fichas", "farmaco": "farmacos",
           "seleccion": "selecciones", "farmacoterapia": "farmacoterapia"}


def metadatos(reg):
    """El bloque editorial, idéntico en las cuatro entidades.

    Que sea idéntico es lo que permite ordenar, filtrar y citar el índice
    entero sin saber de qué tipo es cada registro: un buscador que quiera «lo
    actualizado este mes» no debería tener que aprender cuatro esquemas.
    """
    return {
        "estado": reg.get("estado"),
        "fecha": str(reg.get("fecha") or ""),
        "actualizado": str(reg.get("actualizado") or ""),
        "idioma": reg.get("idioma") or "es",
        "licencia": reg.get("licencia"),
        "autores": reg.get("autores") or AUTOR_POR_DEFECTO,
    }


def ruta_relativa(reg):
    """La URL con la que el reto y el buscador citan un registro."""
    slug = reg["_archivo"].replace(".yaml", ".html")
    return CARPETA.get(reg["tipo"], "farmacos") + "/" + slug


# ══════════════════ 1. LA FICHA (el registro tipo PubMed) ══════════════════

def registro_farmaco(reg, fichas):
    lme = reg.get("lme") or {}
    r = {
        "id": reg["id"],
        "tipo": "farmaco",
        "titulo": reg["dci"],
        "titulo_en": reg.get("dci_en"),
        "url": ruta_relativa(reg),
        "atc": reg.get("atc"),
        "clase": reg.get("clase_farmacologica"),
        "sinonimos": reg.get("sinonimos") or [],
        "lme": bool(lme.get("presente")),
        # Tres estados, no dos: dentro, fuera y sin comprobar. Sin esta marca
        # el buscador presentaría como «fuera de la Lista Modelo» un fármaco
        # que solo está pendiente de consulta.
        "lme_sin_comprobar": lme.get("presente") is None,
        "lme_seccion": lme.get("seccion"),
        "lme_categoria": lme.get("categoria"),
        "emlc": bool((lme.get("emlc") or {}).get("presente")),
        "vias": sorted({f.get("via") for f in reg.get("formas") or [] if f.get("via")}),
        "n_alertas": len(reg.get("alertas") or []),
        "n_reacciones": len((reg.get("seguridad") or {}).get("reacciones") or []),
        "agencias": [x.get("agencia") for x in reg.get("regulatorio") or []],
        "fichas": sorted(f["id"] for f in fichas),
        "resumen": " ".join((reg.get("mecanismo") or "").split()),
    }
    r.update(metadatos(reg))
    return {k: v for k, v in r.items() if v not in (None, [], "")}


def registro_ficha(reg, farmaco, farmacoterapia=None):
    balance = reg.get("balance") or {}
    rec = reg.get("recomendacion") or {}
    evidencia = reg.get("evidencia") or []
    lme = (farmaco or {}).get("lme") or {}

    r = {
        "id": reg["id"],
        "tipo": "ficha",
        "titulo": reg["titulo"],
        "titulo_en": reg.get("titulo_en"),
        "url": ruta_relativa(reg),
        "farmaco": reg.get("farmaco"),
        "dci": (farmaco or {}).get("dci"),
        "atc": (farmaco or {}).get("atc"),
        "clase": (farmaco or {}).get("clase_farmacologica"),
        "indicacion": reg.get("indicacion"),
        "indicacion_en": reg.get("indicacion_en"),
        "poblacion": " ".join((reg.get("poblacion") or "").split()),
        "cie11": reg.get("cie11"),
        "lme": bool(lme.get("presente")),
        "lme_seccion": lme.get("seccion"),
        "certeza_global": balance.get("certeza_global"),
        "recomendacion_direccion": rec.get("direccion"),
        "recomendacion_fuerza": rec.get("fuerza"),
        "recomendacion": " ".join((rec.get("enunciado") or "").split()),
        "resumen": " ".join((reg.get("conclusion") or "").split()),
        "linea": (reg.get("posicionamiento") or {}).get("linea"),
        "semaforo": (reg.get("decision_clinica") or {}).get("semaforo"),
        "perla": (reg.get("decision_clinica") or {}).get("perla_prescripcion"),
        "alerta_seguridad": (reg.get("decision_clinica") or {}).get("alerta_seguridad_inmediata"),
        "nnt": evidencia[0].get("nnt") if evidencia else None,
        "nnt_desenlace": evidencia[0].get("desenlace") if evidencia else None,
        "horizonte_nnt": evidencia[0].get("horizonte_nnt") if evidencia else None,
        "nnh": (reg.get("seguridad_cuantitativa") or [{}])[0].get("nnh"),
        "nnh_evento": (reg.get("seguridad_cuantitativa") or [{}])[0].get("evento"),
        "horizonte_nnh": (reg.get("seguridad_cuantitativa") or [{}])[0].get("horizonte_nnh"),
        "desenlaces": [e.get("desenlace") for e in evidencia if e.get("desenlace")],
        "disenos": sorted({e.get("diseno") for e in evidencia if e.get("diseno")}),
        "n_desenlaces": len(evidencia),
        "n_criticos": sum(1 for e in evidencia if e.get("criticidad") == "critico"),
        "refs": reg.get("refs") or [],
    }
    r.update(metadatos(reg))
    r["seleccion"] = reg.get("seleccion")
    # La capa de guía se hereda del fármaco: la ficha no la repite, pero el
    # buscador tiene que poder filtrar por ella igual, o «guías con cronograma
    # de monitorización» dejaría de devolver nada.
    if farmacoterapia is not None:
        r.update(capa_gpc(farmacoterapia))
        r["farmacoterapia"] = farmacoterapia["id"]
    r["variaciones"] = sorted(v.get("bloque") for v in reg.get("variaciones") or []
                              if isinstance(v, dict) and v.get("bloque"))
    r["n_refs"] = len(r["refs"])
    return {k: v for k, v in r.items() if v not in (None, [], "")}


def registro_seleccion(reg):
    """El informe de selección en el índice: la tabla comparativa, resumida.

    Va el veredicto de cada candidato y su juicio en los cuatro ejes, no el
    sustento: el índice es PubMed y el YAML es PMC. Con esto se puede buscar
    «qué informes seleccionaron un biológico pese a costar más», que es
    exactamente la pregunta que un comité quiere poder hacer.
    """
    candidatos = [c for c in reg.get("candidatos") or [] if isinstance(c, dict)]
    r = {
        "id": reg["id"],
        "tipo": "seleccion",
        "titulo": reg.get("problema"),
        "titulo_en": reg.get("problema_en"),
        "url": ruta_relativa(reg),
        "problema": reg.get("problema"),
        "cie11": reg.get("cie11"),
        "pregunta": " ".join((reg.get("pregunta") or "").split()),
        "resumen": " ".join((reg.get("conclusion") or "").split()),
        "n_candidatos": len(candidatos),
        "candidatos": [c.get("dci") for c in candidatos if c.get("dci")],
        "seleccionados": [c.get("dci") for c in candidatos
                          if c.get("veredicto") == "seleccionado"],
        # Los ejes que quedaron sin datos son el hueco de un informe de
        # selección, y merecen ser buscables por la misma razón que los
        # huecos declarados de una farmacoterapia.
        "ejes_sin_datos": sorted({e for c in candidatos for e in EJES
                                  if (c.get(e) or {}).get("juicio") == "sin_datos"}),
        "refs": reg.get("refs") or [],
    }
    r.update(metadatos(reg))
    r["n_refs"] = len(r["refs"])
    return {k: v for k, v in r.items() if v not in (None, [], "")}


def registro_farmacoterapia(reg, farmaco, fichas):
    r = {
        "id": reg["id"],
        "tipo": "farmacoterapia",
        "titulo": reg.get("titulo"),
        "titulo_en": reg.get("titulo_en"),
        "url": ruta_relativa(reg),
        "farmaco": reg.get("farmaco"),
        "dci": (farmaco or {}).get("dci"),
        "atc": (farmaco or {}).get("atc"),
        "clase": (farmaco or {}).get("clase_farmacologica"),
        "resumen": " ".join((reg.get("alcance") or "").split()),
        # Las indicaciones a las que sirve esta misma farmacoterapia: es el
        # dato que hace visible que se escribió una vez y la usan varias.
        "sirve_a": sorted(f.get("indicacion") for f in fichas
                          if f.get("indicacion")),
        "n_indicaciones": len(fichas),
        "refs": reg.get("refs") or [],
    }
    r.update(metadatos(reg))
    r.update(capa_gpc(reg))
    r["n_refs"] = len(r["refs"])
    return {k: v for k, v in r.items() if v not in (None, [], "")}


def capa_gpc(reg):
    """Lo que convierte una ficha en una guía de práctica clínica, resumido
    para el buscador. Igual que el resto del índice, aquí van metadatos y
    nunca el cuerpo: el cronograma completo vive en el YAML y en el libro."""
    fg = reg.get("farmacogenetica") or {}
    rep = reg.get("reproductivo") or {}
    monitor = [m for m in reg.get("monitorizacion") or [] if isinstance(m, dict)]

    return {
        "gpc": es_gpc(reg),
        "fases_monitorizacion": [m.get("fase") for m in monitor if m.get("fase")],
        "n_umbrales": len(reg.get("umbrales_accion") or []),
        "n_interacciones": len(reg.get("interacciones") or []),
        "n_cribado": len(reg.get("cribado_basal") or []),
        "farmacogenetica": fg.get("gen"),
        "gestacion": (rep.get("gestacion") or {}).get("compatibilidad"),
        "lactancia": (rep.get("lactancia") or {}).get("compatibilidad"),
        # Un hueco declarado es un dato del índice, no una ausencia: permite
        # buscar «qué guías no fijan todavía sus puntos de corte».
        "huecos": sorted(h for h in huecos_de(reg) if h),
    }


# ══════════════════ 2. JSON-LD (Google + sistemas de IA) ══════════════════

def jsonld_farmaco(reg):
    ld = {
        "@context": "https://schema.org",
        "@type": "Drug",
        "name": reg["dci"],
        "alternateName": reg.get("dci_en"),
        "inLanguage": "es",
        "url": BASE + ruta_relativa(reg),
        "nonProprietaryName": reg["dci"],
        "drugClass": reg.get("clase_farmacologica"),
        "mechanismOfAction": " ".join((reg.get("mecanismo") or "").split()),
        "isProprietary": False,
        "isAvailableGenerically": True,
        "publisher": {"@type": "Organization", "name": "farmacosemiotics"},
    }
    if reg.get("atc"):
        ld["code"] = {"@type": "MedicalCode", "codingSystem": "ATC",
                      "codeValue": reg["atc"]}
    formas = reg.get("formas") or []
    if formas:
        ld["dosageForm"] = sorted({f["forma"] for f in formas if f.get("forma")})
        ld["administrationRoute"] = sorted({f["via"] for f in formas if f.get("via")})
    contra = [c.get("motivo") for c in
              (reg.get("seguridad") or {}).get("contraindicaciones") or []]
    if contra:
        ld["contraindication"] = contra
    alertas = [" ".join((a.get("asunto") or "").split()) for a in reg.get("alertas") or []]
    if alertas:
        ld["warning"] = alertas
    return {k: v for k, v in ld.items() if v not in (None, [], "")}


def jsonld_seleccion(reg):
    """El informe como `MedicalGuideline`: es lo más cerca que schema.org
    llega de «recomendación razonada sobre qué medicamento usar»."""
    candidatos = [c for c in reg.get("candidatos") or [] if isinstance(c, dict)]
    ld = {
        "@context": "https://schema.org",
        "@type": "MedicalGuideline",
        "name": reg.get("problema"),
        "alternateName": reg.get("problema_en"),
        "inLanguage": "es",
        "url": BASE + ruta_relativa(reg),
        "guidelineSubject": {"@type": "MedicalCondition",
                             "name": reg.get("problema")},
        "abstract": " ".join((reg.get("conclusion") or "").split()),
        "description": " ".join((reg.get("pregunta") or "").split()),
        "isAccessibleForFree": True,
        "publisher": {"@type": "Organization", "name": "farmacosemiotics"},
        "license": "https://creativecommons.org/licenses/by-sa/4.0/",
        "mentions": [{"@type": "Drug", "name": c["dci"]}
                     for c in candidatos if c.get("dci")],
    }
    if reg.get("fecha"):
        ld["datePublished"] = str(reg["fecha"])
    if reg.get("actualizado"):
        ld["dateModified"] = str(reg["actualizado"])
    ld["citation"] = _citas_pmid(reg.get("refs"))
    return {k: v for k, v in ld.items() if v not in (None, [], "")}


def jsonld_farmacoterapia(reg, farmaco):
    ld = {
        "@context": "https://schema.org",
        "@type": "MedicalGuideline",
        "name": reg.get("titulo"),
        "alternateName": reg.get("titulo_en"),
        "inLanguage": "es",
        "url": BASE + ruta_relativa(reg),
        "abstract": " ".join((reg.get("alcance") or "").split()),
        "isAccessibleForFree": True,
        "audience": {"@type": "MedicalAudience", "audienceType": "Physician"},
        "publisher": {"@type": "Organization", "name": "farmacosemiotics"},
        "license": "https://creativecommons.org/licenses/by-sa/4.0/",
    }
    if farmaco:
        ld["guidelineSubject"] = {"@type": "Drug", "name": farmaco.get("dci"),
                                  "url": BASE + ruta_relativa(farmaco)}
    if reg.get("fecha"):
        ld["datePublished"] = str(reg["fecha"])
    if reg.get("actualizado"):
        ld["dateModified"] = str(reg["actualizado"])
    ld["citation"] = _citas_pmid(reg.get("refs"))
    return {k: v for k, v in ld.items() if v not in (None, [], "")}


def _citas_pmid(refs):
    """Las citas explícitas en el JSON-LD: es lo que permite a un sistema que
    lea la página seguir cada cifra hasta PubMed sin abrir el YAML."""
    return [{"@type": "ScholarlyArticle",
             "identifier": ref.replace("pmid:", "PMID:"),
             "url": "https://pubmed.ncbi.nlm.nih.gov/" + ref.split(":")[1] + "/"}
            for ref in refs or [] if str(ref).startswith("pmid:")]


def jsonld_ficha(reg, farmaco):
    autores = reg.get("autores") or AUTOR_POR_DEFECTO
    rec = reg.get("recomendacion") or {}
    ld = {
        "@context": "https://schema.org",
        "@type": "MedicalScholarlyArticle",
        "headline": reg["titulo"],
        "alternativeHeadline": reg.get("titulo_en"),
        "inLanguage": "es",
        "url": BASE + ruta_relativa(reg),
        "mainEntityOfPage": BASE + ruta_relativa(reg),
        "abstract": " ".join((reg.get("conclusion") or "").split()),
        "description": " ".join((rec.get("enunciado") or "").split()),
        "isAccessibleForFree": True,
        "audience": {"@type": "MedicalAudience", "audienceType": "Physician"},
        "learningResourceType": "Rational pharmacotherapy",
        "publisher": {"@type": "Organization", "name": "farmacosemiotics"},
        "license": "https://creativecommons.org/licenses/by-sa/4.0/",
        "author": [{k: v for k, v in {
            "@type": "Person",
            "name": a.get("nombre"),
            "identifier": ("https://orcid.org/" + a["orcid"]) if a.get("orcid") else None,
        }.items() if v} for a in autores],
    }
    if reg.get("fecha"):
        ld["datePublished"] = str(reg["fecha"])
    if reg.get("actualizado"):
        ld["dateModified"] = str(reg["actualizado"])
    if farmaco:
        ld["about"] = {"@type": "Drug", "name": farmaco.get("dci"),
                       "url": BASE + ruta_relativa(farmaco)}
    if reg.get("indicacion"):
        ld["mentions"] = {"@type": "MedicalCondition", "name": reg["indicacion"]}
    # Las citas son el activo del repositorio: van explícitas en el JSON-LD para
    # que un sistema que lea la página pueda seguirlas sin abrir el YAML.
    citas = _citas_pmid(reg.get("refs"))
    if citas:
        ld["citation"] = citas
    if reg.get("seleccion"):
        ld["isPartOf"] = {"@type": "MedicalGuideline",
                          "identifier": reg["seleccion"]}
    # schema.org no tiene un tipo para «guía farmacoterapéutica», así que la
    # capa de GPC viaja como `MedicalGuideline` dentro de `about`: es lo que
    # un sistema que lea la página puede interpretar sin inventarse un
    # vocabulario propio.
    if es_gpc(reg) or reg.get("monitorizacion"):
        ld["guideline"] = {
            "@type": "MedicalGuideline",
            "guidelineSubject": reg.get("indicacion"),
            "evidenceLevel": (reg.get("balance") or {}).get("certeza_global"),
        }
    return {k: v for k, v in ld.items() if v not in (None, [], "")}


# ══════════════════ 3. JATS (depósito y archivo) ══════════════════

def jats_frontal(art, reg, titulo, titulo_en, resumen, claves):
    """Los metadatos del JATS, iguales para las cuatro entidades. Es lo que
    hace que un depósito pueda archivar un informe de selección con el mismo
    lector con que archiva una guía."""
    front = ET.SubElement(art, "front")
    meta_rev = ET.SubElement(front, "journal-meta")
    ET.SubElement(ET.SubElement(meta_rev, "journal-title-group"),
                  "journal-title").text = "farmacosemiotics"
    ET.SubElement(ET.SubElement(meta_rev, "publisher"),
                  "publisher-name").text = "farmacosemiotics"

    meta = ET.SubElement(front, "article-meta")
    ET.SubElement(meta, "article-id",
                  {"pub-id-type": "publisher-id"}).text = reg["id"]
    tg = ET.SubElement(meta, "title-group")
    ET.SubElement(tg, "article-title").text = titulo
    if titulo_en:
        ET.SubElement(ET.SubElement(tg, "trans-title-group",
                                    {"xml:lang": "en"}),
                      "trans-title").text = titulo_en

    cg = ET.SubElement(meta, "contrib-group")
    for a in reg.get("autores") or AUTOR_POR_DEFECTO:
        c = ET.SubElement(cg, "contrib", {"contrib-type": "author"})
        ET.SubElement(ET.SubElement(c, "name"), "surname").text = a.get("nombre", "")

    for campo, tipo_fecha in (("fecha", "pub"), ("actualizado", "rev-recd")):
        if not reg.get(campo):
            continue
        anio, mes, dia = str(reg[campo]).split("-")
        pd = ET.SubElement(meta, "pub-date", {"date-type": tipo_fecha})
        ET.SubElement(pd, "day").text = dia
        ET.SubElement(pd, "month").text = mes
        ET.SubElement(pd, "year").text = anio

    perm = ET.SubElement(meta, "permissions")
    lic = ET.SubElement(perm, "license", {
        "xlink:href": "https://creativecommons.org/licenses/by-sa/4.0/"})
    ET.SubElement(lic, "license-p").text = reg.get("licencia") or "CC BY-SA 4.0"

    if resumen:
        ab = ET.SubElement(meta, "abstract")
        ET.SubElement(ab, "p").text = resumen
    kg = ET.SubElement(meta, "kwd-group")
    for k in filter(None, claves):
        ET.SubElement(kg, "kwd").text = k
    return meta


def jats_raiz(reg):
    # `xmlns:xlink` va declarado a mano: JATS lo usa en <license>, y sin la
    # declaración el fichero no es XML bien formado aunque lo parezca.
    return ET.Element("article", {
        "article-type": "review-article",
        "dtd-version": "1.3",
        "xml:lang": reg.get("idioma") or "es",
        "xmlns:xlink": "http://www.w3.org/1999/xlink",
    })


def jats_bibliografia(art, refs, referencias):
    back = ET.SubElement(art, "back")
    rl = ET.SubElement(back, "ref-list")
    for ref in refs or []:
        datos = referencias.get(ref)
        if not datos:
            continue
        r = ET.SubElement(rl, "ref", {"id": ref.replace(":", "-")})
        cit = ET.SubElement(r, "element-citation",
                            {"publication-type": "journal"})
        ET.SubElement(cit, "article-title").text = datos.get("titulo", "")
        ET.SubElement(cit, "source").text = datos.get("publicacion", "")
        ET.SubElement(cit, "year").text = str(datos.get("anio", ""))
        ids = datos.get("identificadores") or {}
        if ids.get("pmid"):
            ET.SubElement(cit, "pub-id", {"pub-id-type": "pmid"}).text = str(ids["pmid"])
        if ids.get("doi"):
            ET.SubElement(cit, "pub-id", {"pub-id-type": "doi"}).text = str(ids["doi"])


def jats_serializar(art):
    ET.indent(art, space="  ")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            + ET.tostring(art, encoding="unicode"))


def jats_seleccion(reg, referencias):
    """El informe de selección, archivable: la tabla de los cuatro ejes
    convertida en secciones que un depósito puede indexar."""
    candidatos = [c for c in reg.get("candidatos") or [] if isinstance(c, dict)]
    art = jats_raiz(reg)
    jats_frontal(art, reg, reg.get("problema", ""), reg.get("problema_en"),
                 " ".join((reg.get("conclusion") or "").split()),
                 [reg.get("problema"), reg.get("cie11")]
                 + [c.get("dci") for c in candidatos])

    cuerpo = ET.SubElement(art, "body")
    sec = ET.SubElement(cuerpo, "sec", {"sec-type": "pregunta"})
    ET.SubElement(sec, "title").text = "Pregunta"
    ET.SubElement(sec, "p").text = " ".join((reg.get("pregunta") or "").split())

    for c in candidatos:
        s2 = ET.SubElement(cuerpo, "sec", {"sec-type": "candidato"})
        ET.SubElement(s2, "title").text = c.get("dci", "")
        for eje in EJES:
            b = c.get(eje)
            if not isinstance(b, dict):
                continue
            ET.SubElement(s2, "p").text = ("%s: %s. %s" % (
                eje, b.get("juicio", ""),
                " ".join((b.get("sustento") or "").split())))
        ET.SubElement(s2, "p").text = "Veredicto: " + str(c.get("veredicto", ""))

    if reg.get("criterio_decisorio"):
        s3 = ET.SubElement(cuerpo, "sec", {"sec-type": "conclusiones"})
        ET.SubElement(s3, "title").text = "Qué eje decidió"
        ET.SubElement(s3, "p").text = " ".join(reg["criterio_decisorio"].split())

    jats_bibliografia(art, reg.get("refs"), referencias)
    return jats_serializar(art)


def jats_farmacoterapia(reg, farmaco, referencias):
    art = jats_raiz(reg)
    jats_frontal(art, reg, reg.get("titulo", ""), reg.get("titulo_en"),
                 " ".join((reg.get("alcance") or "").split()),
                 [(farmaco or {}).get("dci"), (farmaco or {}).get("atc")])

    cuerpo = ET.SubElement(art, "body")
    for clave, titulo in (("cribado_basal", "Cribado basal"),
                          ("monitorizacion", "Monitorización"),
                          ("umbrales_accion", "Umbrales de acción"),
                          ("interacciones", "Interacciones")):
        filas = [x for x in reg.get(clave) or [] if isinstance(x, dict)]
        if not filas:
            continue
        sec = ET.SubElement(cuerpo, "sec", {"sec-type": clave})
        ET.SubElement(sec, "title").text = titulo
        for x in filas:
            ET.SubElement(sec, "p").text = " · ".join(
                " ".join(str(x[k]).split()) for k in
                ("prueba", "motivo", "fase", "frecuencia", "parametro",
                 "umbral", "accion", "con", "conducta") if x.get(k))
    jats_bibliografia(art, reg.get("refs"), referencias)
    return jats_serializar(art)


def jats(reg, farmaco, referencias):
    """La guía: la decisión situada, con su recomendación y su evidencia."""
    art = jats_raiz(reg)
    jats_frontal(art, reg, reg["titulo"], reg.get("titulo_en"),
                 " ".join((reg.get("conclusion") or "").split()),
                 [reg.get("indicacion"), (farmaco or {}).get("dci"),
                  (farmaco or {}).get("atc"), reg.get("cie11")])

    cuerpo = ET.SubElement(art, "body")
    sec = ET.SubElement(cuerpo, "sec", {"sec-type": "recomendacion"})
    ET.SubElement(sec, "title").text = "Recomendación"
    rec = reg.get("recomendacion") or {}
    ET.SubElement(sec, "p").text = " ".join((rec.get("enunciado") or "").split())

    sec2 = ET.SubElement(cuerpo, "sec", {"sec-type": "evidencia"})
    ET.SubElement(sec2, "title").text = "Evidencia"
    for e in reg.get("evidencia") or []:
        ET.SubElement(sec2, "p").text = ("%s — %s (%s, certeza %s)." % (
            e.get("desenlace", ""), e.get("efecto", ""),
            e.get("diseno", ""), e.get("certeza", "")))

    jats_bibliografia(art, reg.get("refs"), referencias)
    return jats_serializar(art)


# ══════════════════ 4. facetas ══════════════════

def facetas(registros):
    def valores(clave):
        v = set()
        for r in registros:
            x = r.get(clave)
            if isinstance(x, list):
                v.update(x)
            elif x not in (None, ""):
                v.add(x)
        return sorted(v, key=str)

    return {
        "tipo": valores("tipo"),
        "clase": valores("clase"),
        "lme_seccion": valores("lme_seccion"),
        "lme_categoria": valores("lme_categoria"),
        "certeza_global": valores("certeza_global"),
        "recomendacion_fuerza": valores("recomendacion_fuerza"),
        "disenos": valores("disenos"),
        "estado": valores("estado"),
        "linea": valores("linea"),
        "gestacion": valores("gestacion"),
        "lactancia": valores("lactancia"),
        "farmacogenetica": valores("farmacogenetica"),
        "fases_monitorizacion": valores("fases_monitorizacion"),
        "huecos": valores("huecos"),
        "seleccionados": valores("seleccionados"),
        "ejes_sin_datos": valores("ejes_sin_datos"),
        "variaciones": valores("variaciones"),
    }


def main():
    estado = cargar()
    inf = estado["informe"]
    if inf.errores:
        print("El índice no se genera sobre un repositorio con errores.",
              file=sys.stderr)
        for donde, texto in inf.errores:
            print("  " + donde + ": " + texto, file=sys.stderr)
        return 1

    todos = (list(estado["farmacos"].values())
             + list(estado["farmacoterapias"].values())
             + list(estado["selecciones"].values())
             + list(estado["fichas"].values()))
    for reg in todos:
        reg["_archivo"] = estado["archivos"][reg["id"]]

    registros = []
    for ident, reg in sorted(estado["farmacos"].items()):
        fichas = [f for f in estado["fichas"].values() if f.get("farmaco") == ident]
        registros.append(registro_farmaco(reg, fichas))
    for ident, reg in sorted(estado["selecciones"].items()):
        registros.append(registro_seleccion(reg))
    for ident, reg in sorted(estado["farmacoterapias"].items()):
        fs = reg.get("farmaco")
        registros.append(registro_farmacoterapia(
            reg, estado["farmacos"].get(fs),
            [f for f in estado["fichas"].values() if f.get("farmaco") == fs]))
    for ident, reg in sorted(estado["fichas"].items()):
        registros.append(registro_ficha(
            reg, estado["farmacos"].get(reg.get("farmaco")),
            farmacoterapia_de(reg.get("farmaco"), estado)))

    SALIDA.mkdir(exist_ok=True)
    (SALIDA / "jsonld").mkdir(exist_ok=True)
    (SALIDA / "jats").mkdir(exist_ok=True)

    indice = {
        "generado": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "repositorio": REPO,
        "base": BASE,
        "licencia": "https://creativecommons.org/licenses/by-sa/4.0/",
        "aviso": ("Material educativo. No sustituye el juicio clínico ni la "
                  "ficha técnica aprobada por la agencia reguladora del lugar "
                  "de uso."),
        "total": len(registros),
        "facetas": facetas(registros),
        "registros": registros,
    }
    (SALIDA / "index.json").write_text(
        json.dumps(indice, ensure_ascii=False, indent=1), encoding="utf-8")

    n_ld = n_jats = 0
    for ident, reg in estado["farmacos"].items():
        nombre = reg["_archivo"].replace(".yaml", ".json")
        (SALIDA / "jsonld" / nombre).write_text(
            json.dumps(jsonld_farmaco(reg), ensure_ascii=False, indent=1),
            encoding="utf-8")
        n_ld += 1
    for ident, reg in estado["selecciones"].items():
        base = reg["_archivo"].replace(".yaml", "")
        (SALIDA / "jsonld" / (base + ".json")).write_text(
            json.dumps(jsonld_seleccion(reg), ensure_ascii=False, indent=1),
            encoding="utf-8")
        (SALIDA / "jats" / (base + ".xml")).write_text(
            jats_seleccion(reg, estado["referencias"]), encoding="utf-8")
        n_ld += 1
        n_jats += 1
    for ident, reg in estado["farmacoterapias"].items():
        base = reg["_archivo"].replace(".yaml", "")
        farmaco = estado["farmacos"].get(reg.get("farmaco"))
        (SALIDA / "jsonld" / (base + ".json")).write_text(
            json.dumps(jsonld_farmacoterapia(reg, farmaco),
                       ensure_ascii=False, indent=1), encoding="utf-8")
        (SALIDA / "jats" / (base + ".xml")).write_text(
            jats_farmacoterapia(reg, farmaco, estado["referencias"]),
            encoding="utf-8")
        n_ld += 1
        n_jats += 1
    for ident, reg in estado["fichas"].items():
        farmaco = estado["farmacos"].get(reg.get("farmaco"))
        nombre = reg["_archivo"].replace(".yaml", "")
        (SALIDA / "jsonld" / (nombre + ".json")).write_text(
            json.dumps(jsonld_ficha(reg, farmaco), ensure_ascii=False, indent=1),
            encoding="utf-8")
        (SALIDA / "jats" / (nombre + ".xml")).write_text(
            jats(reg, farmaco, estado["referencias"]), encoding="utf-8")
        n_ld += 1
        n_jats += 1

    print("índice generado")
    print("  build/index.json     " + str(len(registros)) + " registros")
    print("  build/jsonld/        " + str(n_ld) + " ficheros")
    print("  build/jats/          " + str(n_jats) + " ficheros")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
