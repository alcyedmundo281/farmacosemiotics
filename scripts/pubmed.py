#!/usr/bin/env python3
"""
REFERENCIA POR PMID — la única puerta de entrada a `referencias/`.

Las referencias NO se escriben a mano. Se traen de PubMed y se verifican allí:
PubMed es la autoridad para título, año y estado de retractación. CrossRef solo
confirma que el DOI resuelve; sus títulos vienen truncados o con erratas con
frecuencia suficiente como para no compararlos.

    python scripts/pubmed.py 9742977
    python scripts/pubmed.py 9742977 32391934 --sin-crossref
    python scripts/pubmed.py 9742977 --forzar        # reescribe si ya existe

Escribe referencias/pmid-<PMID>.yaml y no toca nada más.
"""
import argparse
import datetime as dt
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "referencias"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
CROSSREF = "https://api.crossref.org/works/"
AGENTE = "farmacosemiotics/1.0 (https://github.com/alcyedmundo281/farmacosemiotics)"


def pedir(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def texto(nodo):
    """Texto plano de un nodo con hijos (<i>, <sub>...), como traen los títulos."""
    if nodo is None:
        return ""
    return " ".join("".join(nodo.itertext()).split())


def slug_bibtex(apellido, anio, existentes):
    base = re.sub(r"[^a-z]", "", (apellido or "anon").lower()) or "anon"
    clave = base + str(anio)
    if clave not in existentes:
        return clave
    for sufijo in "abcdefghijklmnopqrstuvwxyz":
        if clave + sufijo not in existentes:
            return clave + sufijo
    return clave + str(len(existentes))


def claves_en_uso():
    usadas = set()
    if not DESTINO.exists():
        return usadas
    for f in DESTINO.glob("*.yaml"):
        for linea in f.read_text(encoding="utf-8").splitlines():
            if linea.startswith("clave_bibtex:"):
                usadas.add(linea.split(":", 1)[1].strip())
    return usadas


def parsear(art):
    """Extrae el registro de un <PubmedArticle>. Solo lo que PubMed afirma."""
    cita = art.find("MedlineCitation")
    articulo = cita.find("Article")

    pmid = texto(cita.find("PMID"))
    titulo = texto(articulo.find("ArticleTitle")).rstrip(".")

    # Autores personales y colectivos: los ensayos grandes firman en colectivo
    # (UKPDS Group), y esa firma es la que hay que respetar en la clave BibTeX.
    autores = []
    apellido_primero = ""
    for a in articulo.findall("./AuthorList/Author"):
        colectivo = texto(a.find("CollectiveName"))
        if colectivo:
            autores.append(colectivo)
            apellido_primero = apellido_primero or colectivo.split()[0]
            continue
        apellido = texto(a.find("LastName"))
        iniciales = texto(a.find("Initials"))
        if apellido:
            autores.append((apellido + " " + iniciales).strip())
            apellido_primero = apellido_primero or apellido

    revista = articulo.find("Journal")
    publicacion = texto(revista.find("ISOAbbreviation")) or texto(revista.find("Title"))
    ed = revista.find("./JournalIssue")
    anio = texto(ed.find("./PubDate/Year"))
    if not anio:
        medline = texto(ed.find("./PubDate/MedlineDate"))
        m = re.search(r"(1[89]\d{2}|20\d{2})", medline)
        anio = m.group(1) if m else ""
    volumen = texto(ed.find("Volume"))
    numero = texto(ed.find("Issue"))
    paginas = texto(articulo.find("./Pagination/MedlinePgn"))

    doi = pmc = ""
    for ident in art.findall(".//ArticleIdList/ArticleId"):
        tipo = ident.get("IdType")
        if tipo == "doi" and not doi:
            doi = texto(ident)
        elif tipo == "pmc" and not pmc:
            pmc = texto(ident)

    tipos = [texto(t) for t in
             articulo.findall("./PublicationTypeList/PublicationType")]

    # Retractación: el artículo marcado como tal, o un aviso que lo retracta.
    retractado = "Retracted Publication" in tipos
    for cc in cita.findall("./CommentsCorrectionsList/CommentsCorrections"):
        if cc.get("RefType") in ("RetractionIn", "RetractedandRepublishedIn"):
            retractado = True

    return {
        "pmid": pmid, "titulo": titulo, "autores": autores,
        "apellido_primero": apellido_primero, "publicacion": publicacion,
        "anio": anio, "volumen": volumen, "numero": numero, "paginas": paginas,
        "doi": doi, "pmc": pmc, "tipos": tipos, "retractado": retractado,
    }


def clasificar(tipos):
    """El tipo que le importa a build.py: qué peso puede sostener la cita."""
    t = set(tipos)
    if "Meta-Analysis" in t:
        return "metaanalisis"
    if "Systematic Review" in t:
        return "revision_sistematica"
    if "Randomized Controlled Trial" in t:
        return "eca"
    if "Practice Guideline" in t or "Guideline" in t:
        return "guia"
    if "Clinical Trial" in t:
        return "ensayo_clinico"
    if "Review" in t:
        return "revision"
    return "articulo"


def doi_resuelve(doi):
    if not doi:
        return False
    try:
        pedir(CROSSREF + urllib.parse.quote(doi), timeout=20)
        return True
    except Exception:
        return False


def yaml_escapar(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def escribir(reg, clave, crossref, hoy):
    L = []
    A = L.append
    A("# Registro de referencia. Generado por scripts/pubmed.py contra PubMed.")
    A("# No se edita a mano: para corregirlo, vuelve a generarlo con --forzar.")
    A("")
    A('id: "pmid:' + reg["pmid"] + '"')
    A("clave_bibtex: " + clave)
    A("tipo: " + clasificar(reg["tipos"]))
    A("titulo: " + yaml_escapar(reg["titulo"]))
    A("autores:")
    for a in reg["autores"] or ["Anónimo"]:
        A("  - " + yaml_escapar(a))
    A("publicacion: " + yaml_escapar(reg["publicacion"]))
    A("anio: " + (reg["anio"] or "null"))
    if reg["volumen"]:
        A("volumen: " + yaml_escapar(reg["volumen"]))
    if reg["numero"]:
        A("numero: " + yaml_escapar(reg["numero"]))
    if reg["paginas"]:
        A("paginas: " + yaml_escapar(reg["paginas"]))
    A("")
    A("identificadores:")
    A("  pmid: " + reg["pmid"])
    A("  doi: " + (yaml_escapar(reg["doi"]) if reg["doi"] else "null"))
    A("  pmc: " + (yaml_escapar(reg["pmc"]) if reg["pmc"] else "null"))
    A("")
    A("tipos_pubmed:")
    for t in reg["tipos"]:
        A("  - " + yaml_escapar(t))
    A("")
    A("verificacion:")
    A("  pubmed: true")
    A("  fecha: '" + hoy + "'")
    A("  retractado: " + ("true" if reg["retractado"] else "false"))
    if crossref is None:
        # `null` cubre dos casos distintos y conviene no confundirlos con `false`:
        # no se comprobó, o el registro no trae DOI que comprobar.
        motivo = "sin DOI que comprobar" if not reg["doi"] else "no comprobado"
        A("  crossref: null   # " + motivo)
    else:
        A("  crossref: " + ("true" if crossref else "false"))
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(
        description="Crea referencias/ desde uno o más PMID.")
    ap.add_argument("pmids", nargs="+", help="uno o más PMID")
    ap.add_argument("--sin-crossref", action="store_true",
                    help="no comprueba que el DOI resuelva")
    ap.add_argument("--forzar", action="store_true",
                    help="reescribe el fichero si ya existe")
    ap.add_argument("--clave", metavar="CLAVE",
                    help="clave BibTeX explícita; solo con un PMID. Para los "
                         "ensayos que PubMed indexa sin autor personal (UKPDS, "
                         "HOPE, 4S): la clave derivada saldría 'anon<año>'.")
    args = ap.parse_args()

    if args.clave and len(args.pmids) != 1:
        ap.error("--clave solo tiene sentido con un único PMID")

    DESTINO.mkdir(parents=True, exist_ok=True)
    hoy = dt.date.today().isoformat()
    usadas = claves_en_uso()

    pendientes = []
    for p in args.pmids:
        p = p.strip()
        if (DESTINO / ("pmid-" + p + ".yaml")).exists() and not args.forzar:
            print("  ya existe   pmid:" + p + "  (usa --forzar para reescribir)")
            continue
        pendientes.append(p)
    if not pendientes:
        return 0

    url = EUTILS + "?db=pubmed&retmode=xml&id=" + ",".join(pendientes)
    try:
        raiz = ET.fromstring(pedir(url))
    except Exception as e:
        print("ERROR: PubMed no respondió: " + str(e), file=sys.stderr)
        return 1

    vistos = set()
    problemas = 0
    for art in raiz.findall("PubmedArticle"):
        reg = parsear(art)
        vistos.add(reg["pmid"])
        clave = args.clave or slug_bibtex(reg["apellido_primero"], reg["anio"], usadas)
        usadas.add(clave)

        crossref = None
        if not args.sin_crossref and reg["doi"]:
            crossref = doi_resuelve(reg["doi"])
            time.sleep(0.4)

        (DESTINO / ("pmid-" + reg["pmid"] + ".yaml")).write_text(
            escribir(reg, clave, crossref, hoy), encoding="utf-8")

        marca = "   RETRACTADO" if reg["retractado"] else ""
        print("  escrito     pmid:" + reg["pmid"] + "  " + clave + "  "
              + reg["titulo"][:58] + "…" + marca)
        if reg["retractado"]:
            print("              ^ un artículo retractado NO sostiene un enunciado.",
                  file=sys.stderr)
            problemas += 1
        if not args.sin_crossref and reg["doi"] and not crossref:
            print("              ^ el DOI " + reg["doi"] + " no resolvió en CrossRef.",
                  file=sys.stderr)

    for p in pendientes:
        if p not in vistos:
            print("ERROR: PubMed no devolvió nada para pmid:" + p, file=sys.stderr)
            problemas += 1

    return 1 if problemas else 0


if __name__ == "__main__":
    raise SystemExit(main())
