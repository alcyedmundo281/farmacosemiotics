#!/usr/bin/env python3
"""
COBERTURA frente a la Lista Modelo de la OMS.

Responde a la única pregunta que gobierna el orden de trabajo: **cuánto falta,
y dónde**. El mapa maestro dice qué oleada toca; este script dice si la oleada
ya se cerró.

    python scripts/eml.py
    python scripts/eml.py --vacias        # solo las secciones sin nada
    python scripts/eml.py --json

Ojo con lo que este número significa y lo que no: el catálogo guarda la
ESTRUCTURA de secciones de la Lista Modelo, no su censo de medicamentos. Así que
«sección 12 con 3 fármacos» no es «3 de 40»: es «3, y la sección ya no está
vacía». El denominador real se irá poblando oleada a oleada, y hasta entonces
este informe mide avance, no porcentaje.
"""
import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))

from build import cargar  # noqa: E402


def cobertura(estado):
    cat = estado.get("catalogo") or {}
    secciones = cat.get("secciones") or []

    por_seccion = {}
    fuera_de_lista = []
    for ident, reg in estado["farmacos"].items():
        lme = reg.get("lme") or {}
        if not lme.get("presente"):
            fuera_de_lista.append((ident, reg.get("dci")))
            continue
        raiz = str(lme.get("seccion", "")).split(".")[0]
        por_seccion.setdefault(raiz, {"farmacos": [], "fichas": 0})
        por_seccion[raiz]["farmacos"].append((ident, reg.get("dci")))

    for ficha in estado["fichas"].values():
        farmaco = estado["farmacos"].get(ficha.get("farmaco"))
        if not farmaco:
            continue
        raiz = str((farmaco.get("lme") or {}).get("seccion", "")).split(".")[0]
        if raiz in por_seccion:
            por_seccion[raiz]["fichas"] += 1

    filas = []
    for s in secciones:
        n = str(s.get("numero"))
        datos = por_seccion.get(n, {"farmacos": [], "fichas": 0})
        filas.append({
            "numero": s.get("numero"),
            "titulo": s.get("titulo"),
            "titulo_en": s.get("titulo_en"),
            "subsecciones": len(s.get("subsecciones") or []),
            "farmacos": len(datos["farmacos"]),
            "fichas": datos["fichas"],
            "dci": sorted(d for _, d in datos["farmacos"]),
        })
    return filas, fuera_de_lista, cat


def main():
    ap = argparse.ArgumentParser(
        description="Mide la cobertura frente a la Lista Modelo de la OMS.")
    ap.add_argument("--vacias", action="store_true",
                    help="lista solo las secciones sin ningún fármaco")
    ap.add_argument("--json", action="store_true", help="salida en JSON")
    args = ap.parse_args()

    estado = cargar()
    if not estado.get("catalogo"):
        print("No hay catálogo en catalogo/lme-oms-2025.yaml.", file=sys.stderr)
        return 1

    filas, fuera, cat = cobertura(estado)

    if args.json:
        print(json.dumps({"lista": cat.get("lista"), "edicion": cat.get("edicion"),
                          "anio": cat.get("anio"), "secciones": filas,
                          "fuera_de_lista": fuera},
                         ensure_ascii=False, indent=1))
        return 0

    cubiertas = [f for f in filas if f["farmacos"]]
    print("Cobertura frente a la LME " + str(cat.get("edicion")) + ".ª lista ("
          + str(cat.get("anio")) + ")")
    print("  secciones con al menos un fármaco   " + str(len(cubiertas))
          + " de " + str(len(filas)))
    print("  fármacos en la Lista Modelo         "
          + str(sum(f["farmacos"] for f in filas)))
    print("  fichas sobre ellos                  "
          + str(sum(f["fichas"] for f in filas)))
    if not cat.get("completo"):
        print("  el catálogo está marcado `completo: false`: faltan subsecciones")
    print("")

    mostrar = [f for f in filas if not f["farmacos"]] if args.vacias else filas
    for f in mostrar:
        marca = "·" if not f["farmacos"] else str(f["farmacos"])
        print("  %2s  %-3s  %-62s %s fichas" % (
            f["numero"], marca, f["titulo"][:62], f["fichas"]))
        if f["dci"]:
            print("          " + ", ".join(f["dci"]))

    if fuera:
        print("")
        print("Fuera de la Lista Modelo (" + str(len(fuera)) + ")")
        for ident, dci in fuera:
            print("  " + ident + "  " + str(dci))
        print("  No es un defecto: la LME es la meta, no el límite. Pero si esta")
        print("  lista crece más rápido que la de arriba, el repositorio se está")
        print("  desviando de su propio objetivo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
