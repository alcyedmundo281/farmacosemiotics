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
    """Lee farmacos/, fichas/, referencias/ y el catálogo. No valida: solo lee."""
    inf = inf or Informe()
    estado = {"farmacos": {}, "fichas": {}, "referencias": {}, "catalogo": None,
              "archivos": {}, "informe": inf}

    for carpeta, clave, patron in (("farmacos", "farmacos", RE_ARCHIVO_FS),
                                   ("fichas", "fichas", RE_ARCHIVO_FT),
                                   ("referencias", "referencias", None)):
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
    for coleccion in ("farmacos", "fichas"):
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
        if not a.get("consultado"):
            inf.error(archivo, "una alerta sin `consultado`: un dato "
                               "regulatorio sin fecha no es verificable")

    for r in reg.get("regulatorio", []) or []:
        if not r.get("agencia"):
            inf.error(archivo, "una entrada de `regulatorio` sin `agencia`")
        if not r.get("consultado"):
            inf.error(archivo, "`regulatorio` de " + str(r.get("agencia"))
                      + " sin `consultado`")


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

    for campo in ("titulo", "indicacion", "poblacion", "fecha", "conclusion"):
        if not reg.get(campo):
            inf.error(archivo, "falta `" + campo + "`")

    if reg.get("estado") not in ESTADOS:
        inf.error(archivo, "`estado` debe ser uno de " + ", ".join(sorted(ESTADOS)))

    for campo in ("fecha", "actualizado"):
        v = reg.get(campo)
        if v and not RE_FECHA.match(str(v)):
            inf.error(archivo, "`" + campo + "` debe ser YYYY-MM-DD")

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

    # Una recomendación fuerte sobre certeza baja es posible, pero es la
    # excepción de GRADE y tiene que estar argumentada, no dejada caer.
    if (rec.get("fuerza") == "fuerte"
            and balance.get("certeza_global") in ("baja", "muy_baja")
            and not rec.get("justificacion_fuerza")):
        inf.aviso(archivo, "recomendación fuerte con certeza "
                  + str(balance.get("certeza_global")) + " y sin "
                  "`justificacion_fuerza`: en GRADE eso es una excepción")


def secciones_catalogo(estado):
    cat = estado.get("catalogo") or {}
    return {str(s.get("numero")) for s in cat.get("secciones", [])}


def revisar_higiene(estado, inf):
    """Lo que delata que un registro se salió del contrato del repositorio."""
    for coleccion in ("farmacos", "fichas"):
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
    for coleccion in ("farmacos", "fichas"):
        for reg in estado[coleccion].values():
            for _, ref in refs_de(reg):
                citadas.add(ref)
    for ident in estado["referencias"]:
        if ident not in citadas:
            inf.aviso(estado["archivos"][ident],
                      "referencia que no cita nadie todavía")

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
    for ident, reg in estado["fichas"].items():
        revisar_ficha(ident, reg, estado["archivos"][ident], estado, inf)

    regla_de_oro(estado, inf)
    revisar_higiene(estado, inf)
    revisar_huerfanos(estado, inf)

    print("farmacosemiotics — validación")
    print("  fármacos      " + str(len(estado["farmacos"])))
    print("  fichas        " + str(len(estado["fichas"])))
    print("  referencias   " + str(len(estado["referencias"])))
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
