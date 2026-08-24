#!/usr/bin/env python3
"""
BLOQUE REGULATORIO desde openFDA.

No usamos un MCP para esto a propósito: ataría la generación a una sesión
interactiva. Este script corre igual en tu portátil y en CI, y deja la fecha de
consulta dentro del propio registro, que es lo que lo hace verificable.

    python scripts/openfda.py "metformin hydrochloride"
    python scripts/openfda.py pembrolizumab --solo-nda
    python scripts/openfda.py metformin --json          # crudo, para depurar

IMPRIME el bloque YAML por la salida estándar. **No escribe en farmacos/.**
Igual que build.py, ningún script de este repositorio modifica un registro: lo
pega una persona, que es quien responde por lo que entra.

Dos avisos que este script te dará y conviene leer:

  - openFDA indexa combinaciones a fuerza bruta. Buscar «metformin» trae
    ZITUVIMET (sitagliptina + metformina). El script lista las marcas que
    encontró para que veas si te coló una combinación.
  - `drugsfda` no tiene un campo «fecha de primera aprobación». Se deriva de la
    submission ORIG más antigua con estado AP, y para moléculas antiguas eso
    puede quedarse corto: la base arranca en 1939 y muchos registros previos a
    los años noventa están incompletos.
"""
import argparse
import datetime as dt
import json
import sys
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://api.fda.gov/drug/"
AGENTE = "farmacosemiotics/1.0 (https://github.com/alcyedmundo281/farmacosemiotics)"


def consultar(recurso, busqueda, limite=100):
    # openFDA usa `+` como separador dentro de las comillas de una frase; un
    # espacio literal en la URL revienta urllib antes de salir de la máquina.
    busqueda = busqueda.replace(" ", "+")
    url = (BASE + recurso + ".json?search="
           + urllib.parse.quote(busqueda, safe=':"+()[]') + "&limit=" + str(limite))
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"results": [], "meta": {"results": {"total": 0}}}
        raise


def fecha_iso(compacta):
    """openFDA usa YYYYMMDD. Sin guiones no es una fecha, es un número."""
    s = str(compacta or "")
    if len(s) == 8 and s.isdigit():
        return s[:4] + "-" + s[4:6] + "-" + s[6:]
    return None


def aprobaciones(nombre, solo_nda):
    datos = consultar("drugsfda", 'openfda.generic_name:"%s"' % nombre)
    resultados = datos.get("results", [])

    primera = None
    marcas, formas, vias, patrocinadores = set(), set(), set(), set()
    n_nda = n_anda = n_bla = 0

    for r in resultados:
        appl = r.get("application_number", "")
        if appl.startswith("NDA"):
            n_nda += 1
        elif appl.startswith("ANDA"):
            n_anda += 1
        elif appl.startswith("BLA"):
            n_bla += 1
        if solo_nda and appl.startswith("ANDA"):
            continue

        patrocinadores.add(r.get("sponsor_name", ""))
        for p in r.get("products", []):
            if p.get("brand_name"):
                marcas.add(p["brand_name"])
            if p.get("dosage_form"):
                formas.add(p["dosage_form"])
            if p.get("route"):
                vias.add(p["route"])
        for s in r.get("submissions", []):
            if s.get("submission_type") == "ORIG" and s.get("submission_status") == "AP":
                f = fecha_iso(s.get("submission_status_date"))
                if f and (primera is None or f < primera):
                    primera = f

    return {
        "total": datos.get("meta", {}).get("results", {}).get("total", 0),
        "primera_aprobacion": primera,
        "marcas": sorted(marcas), "formas": sorted(formas), "vias": sorted(vias),
        "patrocinadores": sorted(x for x in patrocinadores if x),
        "n_nda": n_nda, "n_anda": n_anda, "n_bla": n_bla,
    }


def etiqueta(nombre):
    datos = consultar("label", 'openfda.generic_name:"%s"' % nombre, limite=20)
    res = datos.get("results", [])
    if not res:
        return None

    # La etiqueta más reciente manda: es la que un clínico consultaría hoy.
    res.sort(key=lambda r: str(r.get("effective_time") or ""), reverse=True)
    r = res[0]
    of = r.get("openfda", {})
    recuadro = r.get("boxed_warning")
    return {
        "set_id": r.get("set_id"),
        "vigencia": fecha_iso(r.get("effective_time")),
        "marca": (of.get("brand_name") or [None])[0],
        "clase_epc": of.get("pharm_class_epc") or [],
        "unii": of.get("unii") or [],
        "rxcui": of.get("rxcui") or [],
        "recuadro": " ".join(recuadro[0].split())[:400] if recuadro else None,
        "con_contraindicaciones": bool(r.get("contraindications")),
    }


def bloque_yaml(nombre, ap, et, hoy):
    L = []
    A = L.append
    A("# --- pegar en farmacos/<ficha>.yaml ---")
    A("# Generado por scripts/openfda.py. Revisa las marcas antes de pegar:")
    A("# si aparece una combinación, la consulta trajo más de lo que pediste.")
    A("")
    A("regulatorio:")
    A("  - agencia: FDA")
    A("    estado: aprobado")
    if ap["primera_aprobacion"]:
        A("    primera_aprobacion: '" + ap["primera_aprobacion"] + "'")
        A("    primera_aprobacion_nota: >-")
        A("      Derivada de la submission ORIG/AP más antigua de openFDA, no de un")
        A("      campo oficial de primera aprobación.")
    else:
        A("    primera_aprobacion: null   # openFDA no expuso ninguna ORIG/AP")
    A("    solicitudes:")
    A("      nda: " + str(ap["n_nda"]))
    A("      anda: " + str(ap["n_anda"]))
    A("      bla: " + str(ap["n_bla"]))
    A("    fuente: 'openfda:drugsfda'")
    A("    consulta: 'openfda.generic_name:\"" + nombre + "\"'")
    A("    consultado: '" + hoy + "'")

    if et:
        A("")
        A("etiqueta_fda:")
        A("  set_id: '" + str(et["set_id"]) + "'")
        A("  vigencia: '" + str(et["vigencia"]) + "'")
        A("  url: https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid="
          + str(et["set_id"]))
        A("  fuente: 'openfda:label'")
        A("  consultado: '" + hoy + "'")
        if et["recuadro"]:
            A("")
            A("# Advertencia con recuadro. Se RESUME, no se copia: el texto íntegro")
            A("# de la ficha técnica es obra ajena y además cambia sin avisar.")
            A("alertas:")
            A("  - agencia: FDA")
            A("    tipo: recuadro")
            A("    asunto: RESUMIR A MANO   # ← primeras palabras abajo, para orientarte")
            A("    url: https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid="
              + str(et["set_id"]))
            A("    consultado: '" + hoy + "'")
            A("    # openFDA devolvió: " + et["recuadro"][:160].replace("\n", " "))
    return "\n".join(L)


def main():
    ap_ = argparse.ArgumentParser(
        description="Imprime el bloque regulatorio de un fármaco desde openFDA.")
    ap_.add_argument("nombre", help="nombre genérico tal como lo indexa openFDA")
    ap_.add_argument("--solo-nda", action="store_true",
                     help="ignora los ANDA (genéricos) al derivar formas y marcas")
    ap_.add_argument("--json", action="store_true",
                     help="vuelca lo recogido en crudo, para depurar")
    args = ap_.parse_args()

    hoy = dt.date.today().isoformat()
    try:
        aprob = aprobaciones(args.nombre, args.solo_nda)
        etiq = etiqueta(args.nombre)
    except Exception as e:
        print("ERROR: openFDA no respondió: " + str(e), file=sys.stderr)
        return 1

    if aprob["total"] == 0 and etiq is None:
        print("openFDA no conoce '" + args.nombre + "' como nombre genérico.",
              file=sys.stderr)
        print("Prueba la forma de sal completa: 'metformin hydrochloride'.",
              file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"aprobaciones": aprob, "etiqueta": etiq},
                         ensure_ascii=False, indent=2))
        return 0

    print(bloque_yaml(args.nombre, aprob, etiq, hoy))

    print("", file=sys.stderr)
    print("Comprueba antes de pegar:", file=sys.stderr)
    print("  solicitudes encontradas: " + str(aprob["total"]), file=sys.stderr)
    print("  marcas: " + ", ".join(aprob["marcas"][:8] or ["(ninguna)"]),
          file=sys.stderr)
    if etiq and etiq["clase_epc"]:
        print("  clase EPC de la etiqueta: " + ", ".join(etiq["clase_epc"]),
              file=sys.stderr)
        print("  ^ si esa clase no es la del fármaco que pediste, la consulta"
              " trajo una combinación.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
