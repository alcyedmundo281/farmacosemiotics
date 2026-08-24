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

from build import cargar, RAIZ  # noqa: E402

SALIDA = RAIZ / "build"
BASE = "https://powersemiotics.com/farmacosemiotics/"
REPO = "https://github.com/alcyedmundo281/farmacosemiotics"
AUTOR_POR_DEFECTO = [{"nombre": "Alcy Torres"}]


def ruta_relativa(reg):
    """La URL con la que el reto y el buscador citan un registro."""
    slug = reg["_archivo"].replace(".yaml", ".html")
    carpeta = "fichas" if reg["tipo"] == "ficha" else "farmacos"
    return carpeta + "/" + slug


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
    return {k: v for k, v in r.items() if v not in (None, [], "")}


def registro_ficha(reg, farmaco):
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
        "estado": reg.get("estado"),
        "fecha": str(reg.get("fecha") or ""),
        "actualizado": str(reg.get("actualizado") or ""),
        "certeza_global": balance.get("certeza_global"),
        "recomendacion_direccion": rec.get("direccion"),
        "recomendacion_fuerza": rec.get("fuerza"),
        "recomendacion": " ".join((rec.get("enunciado") or "").split()),
        "resumen": " ".join((reg.get("conclusion") or "").split()),
        "desenlaces": [e.get("desenlace") for e in evidencia if e.get("desenlace")],
        "disenos": sorted({e.get("diseno") for e in evidencia if e.get("diseno")}),
        "n_desenlaces": len(evidencia),
        "n_criticos": sum(1 for e in evidencia if e.get("criticidad") == "critico"),
        "refs": reg.get("refs") or [],
        "autores": reg.get("autores") or AUTOR_POR_DEFECTO,
    }
    r["n_refs"] = len(r["refs"])
    return {k: v for k, v in r.items() if v not in (None, [], "")}


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
    citas = []
    for ref in reg.get("refs") or []:
        if ref.startswith("pmid:"):
            citas.append({"@type": "ScholarlyArticle",
                          "identifier": ref.replace("pmid:", "PMID:"),
                          "url": "https://pubmed.ncbi.nlm.nih.gov/"
                                 + ref.split(":")[1] + "/"})
    if citas:
        ld["citation"] = citas
    return {k: v for k, v in ld.items() if v not in (None, [], "")}


# ══════════════════ 3. JATS (depósito y archivo) ══════════════════

def jats(reg, farmaco, referencias):
    # `xmlns:xlink` va declarado a mano: JATS lo usa en <license>, y sin la
    # declaración el fichero no es XML bien formado aunque lo parezca.
    art = ET.Element("article", {
        "article-type": "review-article",
        "dtd-version": "1.3",
        "xml:lang": "es",
        "xmlns:xlink": "http://www.w3.org/1999/xlink",
    })
    front = ET.SubElement(art, "front")
    meta_rev = ET.SubElement(front, "journal-meta")
    ET.SubElement(ET.SubElement(meta_rev, "journal-title-group"),
                  "journal-title").text = "farmacosemiotics"
    ET.SubElement(ET.SubElement(meta_rev, "publisher"),
                  "publisher-name").text = "farmacosemiotics"

    meta = ET.SubElement(front, "article-meta")
    ai = ET.SubElement(meta, "article-id", {"pub-id-type": "publisher-id"})
    ai.text = reg["id"]
    tg = ET.SubElement(meta, "title-group")
    ET.SubElement(tg, "article-title").text = reg["titulo"]
    if reg.get("titulo_en"):
        ET.SubElement(ET.SubElement(tg, "trans-title-group",
                                    {"xml:lang": "en"}),
                      "trans-title").text = reg["titulo_en"]

    cg = ET.SubElement(meta, "contrib-group")
    for a in reg.get("autores") or AUTOR_POR_DEFECTO:
        c = ET.SubElement(cg, "contrib", {"contrib-type": "author"})
        ET.SubElement(ET.SubElement(c, "name"), "surname").text = a.get("nombre", "")

    if reg.get("fecha"):
        anio, mes, dia = str(reg["fecha"]).split("-")
        pd = ET.SubElement(meta, "pub-date", {"date-type": "pub"})
        ET.SubElement(pd, "day").text = dia
        ET.SubElement(pd, "month").text = mes
        ET.SubElement(pd, "year").text = anio

    perm = ET.SubElement(meta, "permissions")
    lic = ET.SubElement(perm, "license", {
        "xlink:href": "https://creativecommons.org/licenses/by-sa/4.0/"})
    ET.SubElement(lic, "license-p").text = "CC BY-SA 4.0"

    ab = ET.SubElement(meta, "abstract")
    ET.SubElement(ab, "p").text = " ".join((reg.get("conclusion") or "").split())

    kg = ET.SubElement(meta, "kwd-group")
    for k in filter(None, [reg.get("indicacion"), (farmaco or {}).get("dci"),
                           (farmaco or {}).get("atc")]):
        ET.SubElement(kg, "kwd").text = k

    cuerpo = ET.SubElement(art, "body")
    sec = ET.SubElement(cuerpo, "sec", {"sec-type": "recomendacion"})
    ET.SubElement(sec, "title").text = "Recomendación"
    rec = reg.get("recomendacion") or {}
    ET.SubElement(sec, "p").text = " ".join((rec.get("enunciado") or "").split())

    sec2 = ET.SubElement(cuerpo, "sec", {"sec-type": "evidencia"})
    ET.SubElement(sec2, "title").text = "Evidencia"
    for e in reg.get("evidencia") or []:
        p = ET.SubElement(sec2, "p")
        p.text = ("%s — %s (%s, certeza %s)." % (
            e.get("desenlace", ""), e.get("efecto", ""),
            e.get("diseno", ""), e.get("certeza", "")))

    back = ET.SubElement(art, "back")
    rl = ET.SubElement(back, "ref-list")
    for ref in reg.get("refs") or []:
        datos = referencias.get(ref)
        if not datos:
            continue
        r = ET.SubElement(rl, "ref", {"id": ref.replace(":", "-")})
        cit = ET.SubElement(r, "element-citation", {"publication-type": "journal"})
        ET.SubElement(cit, "article-title").text = datos.get("titulo", "")
        ET.SubElement(cit, "source").text = datos.get("publicacion", "")
        ET.SubElement(cit, "year").text = str(datos.get("anio", ""))
        ids = datos.get("identificadores") or {}
        if ids.get("pmid"):
            ET.SubElement(cit, "pub-id", {"pub-id-type": "pmid"}).text = str(ids["pmid"])
        if ids.get("doi"):
            ET.SubElement(cit, "pub-id", {"pub-id-type": "doi"}).text = str(ids["doi"])

    ET.indent(art, space="  ")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            + ET.tostring(art, encoding="unicode"))


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

    for reg, archivo in ((r, estado["archivos"][r["id"]])
                         for r in list(estado["farmacos"].values())
                         + list(estado["fichas"].values())):
        reg["_archivo"] = archivo

    registros = []
    for ident, reg in sorted(estado["farmacos"].items()):
        fichas = [f for f in estado["fichas"].values() if f.get("farmaco") == ident]
        registros.append(registro_farmaco(reg, fichas))
    for ident, reg in sorted(estado["fichas"].items()):
        registros.append(registro_ficha(reg, estado["farmacos"].get(reg.get("farmaco"))))

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
