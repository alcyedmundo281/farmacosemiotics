#!/usr/bin/env python3
"""
RETO — banco de preguntas derivado de las fichas.

Ninguna pregunta se escribe a mano y ningún distractor se inventa: las opciones
salen o bien de una escala cerrada del propio esquema (las cuatro certezas de
GRADE, las dos fuerzas de recomendación), o bien de otro registro real del
repositorio. Un distractor inventado enseña algo que no existe.

Cada pregunta lleva la **URL relativa** de la ficha que la sostiene, igual que
en biosemiotics: el reto se puede servir desde cualquier ruta de Pages sin
reescribir enlaces, y quien falla puede ir a leer de dónde salía la respuesta.

    python scripts/reto.py
    python scripts/reto.py --min-opciones 3

Produce build/reto.json.
"""
import argparse
import datetime as dt
import json
import random
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))

from build import (cargar, RAIZ, CERTEZAS, FUERZAS,  # noqa: E402
                   DIRECCIONES, EJES, JUICIOS, VEREDICTOS,
                   FASES, COMPATIBILIDAD)

SALIDA = RAIZ / "build"

ETIQUETA_RAZON = {
    "riesgo_de_sesgo": "riesgo de sesgo", "inconsistencia": "inconsistencia",
    "evidencia_indirecta": "evidencia indirecta", "imprecision": "imprecisión",
    "sesgo_de_publicacion": "sesgo de publicación",
    "caracter_secundario": "carácter secundario",
}

ETIQUETA_CERTEZA = {"alta": "Alta", "moderada": "Moderada",
                    "baja": "Baja", "muy_baja": "Muy baja"}
ETIQUETA_FUERZA = {"fuerte": "Fuerte", "condicional": "Condicional"}
ETIQUETA_DIRECCION = {"a_favor": "A favor de la intervención",
                      "en_contra": "En contra de la intervención",
                      "ninguna": "Sin recomendación en ningún sentido"}
ETIQUETA_SEMAFORO = {
    "verde": "Verde (Elección preferente / beneficio neto demostrado)",
    "amarillo": "Amarillo (Condicional / segunda línea o beneficio modesto)",
    "rojo": "Rojo (No recomendado / balance desfavorable)"
}


def url_ficha(archivo):
    return "fichas/" + archivo.replace(".yaml", ".html")


def razones(e):
    """Las razones de descenso en prosa. Son la mitad útil de la explicación:
    saber que la certeza es moderada sin saber por qué no enseña nada."""
    r = e.get("razones_descenso") or []
    if not r:
        return "."
    return ", por " + ", ".join(ETIQUETA_RAZON.get(x, x.replace("_", " "))
                                for x in r) + "."


def opciones(correcta, universo, etiquetas):
    """Baraja la escala completa. Con escalas cerradas no hay que inventar nada."""
    valores = sorted(universo)
    return [{"texto": etiquetas.get(v, v), "valor": v,
             "correcta": v == correcta} for v in valores]


def slug(texto):
    """Trozo de id legible y estable. No es una URL: solo tiene que distinguir
    dos preguntas del mismo registro y no cambiar al recompilar."""
    t = str(texto or "").lower()
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"),
                 ("ñ", "n")):
        t = t.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:40] or "x"


def url_de(reg, archivo):
    """La URL relativa de cualquier entidad, por su tipo."""
    carpeta = {"seleccion": "selecciones", "farmacoterapia": "farmacoterapia",
               "farmaco": "farmacos"}.get(reg.get("tipo"), "fichas")
    return carpeta + "/" + archivo.replace(".yaml", ".html")


ETIQUETA_JUICIO = {"superior": "Superior a los demás candidatos",
                   "equivalente": "Equivalente a los demás",
                   "inferior": "Inferior a los demás",
                   "sin_datos": "Sin datos para juzgarlo"}
ETIQUETA_FASE = {"basal": "Basal, antes de la primera dosis",
                 "induccion": "Inducción", "mantenimiento": "Mantenimiento",
                 "estable": "Fase estable",
                 "post_suspension": "Tras la suspensión"}
ETIQUETA_COMPAT = {"compatible": "Compatible",
                   "compatible_con_precaucion": "Compatible con precaución",
                   "evitar": "Evitar", "contraindicado": "Contraindicado",
                   "sin_datos": "Sin datos"}


def preguntas_de_seleccion(reg, archivo, rnd):
    """La Parte I se evalúa por lo que de verdad enseña: qué se eligió, y con
    qué juicio en cada eje. Los distractores son los otros candidatos reales
    del mismo informe, no fármacos inventados para rellenar."""
    url = url_de(reg, archivo)
    base = {"ficha": reg["id"], "url": url, "problema": reg.get("problema")}
    candidatos = [c for c in reg.get("candidatos") or [] if isinstance(c, dict)]
    salida = []

    elegidos = [c for c in candidatos if c.get("veredicto") == "seleccionado"]
    if len(candidatos) >= 2 and len(elegidos) == 1:
        correcto = elegidos[0]["dci"]
        salida.append(dict(base, **{
            "id": reg["id"] + "-seleccion",
            "tipo": "seleccion",
            "enunciado": "En " + str(reg.get("problema")) + ", ¿qué fármaco "
                         "selecciona el informe frente a los demás candidatos?",
            "opciones": [{"texto": c["dci"], "valor": c["dci"],
                          "correcta": c["dci"] == correcto}
                         for c in candidatos if c.get("dci")],
            "explicacion": " ".join((reg.get("criterio_decisorio") or "").split()),
        }))

    for c in candidatos:
        for eje in EJES:
            bloque = c.get(eje)
            if not isinstance(bloque, dict) or not bloque.get("juicio"):
                continue
            salida.append(dict(base, **{
                "id": reg["id"] + "-eje-" + eje + "-" + slug(c.get("dci")),
                "tipo": "eje_seleccion",
                "enunciado": "En " + str(reg.get("problema")) + ", ¿cómo juzga "
                             "el informe la " + eje + " de " + str(c.get("dci"))
                             + " frente a los demás candidatos?",
                "opciones": opciones(bloque["juicio"], JUICIOS, ETIQUETA_JUICIO),
                "explicacion": " ".join((bloque.get("sustento") or "").split()),
            }))
    return salida


def preguntas_de_farmacoterapia(reg, archivo, farmaco, rnd):
    """La Parte II se evalúa donde se falla en la consulta: en qué fase toca
    cada prueba, y qué se le puede decir a quien busca embarazo."""
    url = url_de(reg, archivo)
    base = {"ficha": reg["id"], "url": url, "dci": (farmaco or {}).get("dci"),
            "atc": (farmaco or {}).get("atc")}
    salida = []

    for m in reg.get("monitorizacion") or []:
        if not isinstance(m, dict) or not m.get("fase") or not m.get("pruebas"):
            continue
        pruebas = m["pruebas"] if isinstance(m["pruebas"], list) else [m["pruebas"]]
        salida.append(dict(base, **{
            "id": reg["id"] + "-fase-" + str(m["fase"]),
            "tipo": "fase_monitorizacion",
            "enunciado": "En la farmacoterapia con " + str((farmaco or {}).get("dci"))
                         + ", ¿en qué fase corresponde «" + str(pruebas[0]) + "»?",
            "opciones": opciones(m["fase"], FASES, ETIQUETA_FASE),
            "explicacion": ("Frecuencia: " + " ".join(str(m["frecuencia"]).split())
                            if m.get("frecuencia") else
                            "Es la fase basal: se hace una vez, antes de la "
                            "primera dosis."),
        }))

    rep = reg.get("reproductivo") or {}
    for etapa, rotulo in (("gestacion", "el embarazo"), ("lactancia", "la lactancia")):
        e = rep.get(etapa)
        if not isinstance(e, dict) or not e.get("compatibilidad"):
            continue
        salida.append(dict(base, **{
            "id": reg["id"] + "-" + etapa,
            "tipo": "reproductivo",
            "enunciado": "¿Cuál es la compatibilidad de "
                         + str((farmaco or {}).get("dci")) + " con " + rotulo + "?",
            "opciones": opciones(e["compatibilidad"], COMPATIBILIDAD,
                                 ETIQUETA_COMPAT),
            "explicacion": " ".join((e.get("enunciado") or "").split()),
        }))

    for u in reg.get("umbrales_accion") or []:
        if not isinstance(u, dict) or not u.get("umbral"):
            continue
        salida.append(dict(base, **{
            "id": reg["id"] + "-umbral-" + slug(u.get("parametro")),
            "tipo": "umbral",
            "enunciado": "En la farmacoterapia con "
                         + str((farmaco or {}).get("dci")) + ", ¿cuál es el "
                         "punto de corte de " + str(u.get("parametro")) + "?",
            # Los distractores son los umbrales reales de los OTROS parámetros
            # de esta misma farmacoterapia: confundirlos es el error clínico
            # que la pregunta busca detectar.
            "opciones": [{"texto": str(x.get("umbral")), "valor": str(x.get("umbral")),
                          "correcta": x is u}
                         for x in reg["umbrales_accion"]
                         if isinstance(x, dict) and x.get("umbral")],
            "explicacion": " ".join((u.get("accion") or "").split()),
        }))
    return salida


def preguntas_de_ficha(reg, archivo, farmaco, rnd):
    url = url_ficha(archivo)
    base = {
        "ficha": reg["id"],
        "url": url,
        "dci": (farmaco or {}).get("dci"),
        "atc": (farmaco or {}).get("atc"),
        "lme_seccion": ((farmaco or {}).get("lme") or {}).get("seccion"),
        "indicacion": reg.get("indicacion"),
    }
    salida = []

    # 1. Certeza GRADE de un desenlace crítico.
    criticos = [e for e in reg.get("evidencia") or []
                if e.get("criticidad") == "critico" and e.get("certeza")]
    for e in criticos:
        salida.append(dict(base, **{
            "id": reg["id"] + "-certeza-" + str(len(salida)),
            "tipo": "certeza_grade",
            "enunciado": ("En «" + reg["titulo"] + "», ¿qué certeza GRADE tiene "
                          "el desenlace «" + e["desenlace"] + "»?"),
            "opciones": opciones(e["certeza"], CERTEZAS, ETIQUETA_CERTEZA),
            "explicacion": ("Certeza " + ETIQUETA_CERTEZA[e["certeza"]].lower()
                            + razones(e) + " Efecto: "
                            + " ".join(str(e.get("efecto", "")).split()) + "."),
            "ref": e.get("ref"),
        }))

    # 2. Fuerza y dirección de la recomendación.
    rec = reg.get("recomendacion") or {}
    if rec.get("direccion"):
        salida.append(dict(base, **{
            "id": reg["id"] + "-direccion",
            "tipo": "recomendacion",
            "enunciado": ("¿En qué sentido va la recomendación de «"
                          + reg["titulo"] + "»?"),
            "opciones": opciones(rec["direccion"], DIRECCIONES, ETIQUETA_DIRECCION),
            "explicacion": " ".join((rec.get("enunciado") or "").split()),
        }))
    if rec.get("fuerza"):
        salida.append(dict(base, **{
            "id": reg["id"] + "-fuerza",
            "tipo": "fuerza",
            "enunciado": ("¿Con qué fuerza se recomienda lo que propone «"
                          + reg["titulo"] + "»?"),
            "opciones": opciones(rec["fuerza"], FUERZAS, ETIQUETA_FUERZA),
            "explicacion": ("Certeza global "
                            + str((reg.get("balance") or {}).get("certeza_global"))
                            + ". " + " ".join((rec.get("enunciado") or "").split())),
        }))

    # 3. Semáforo de decisión clínica
    dc = reg.get("decision_clinica") or {}
    if dc.get("semaforo"):
        salida.append(dict(base, **{
            "id": reg["id"] + "-semaforo",
            "tipo": "semaforo",
            "enunciado": ("¿Cuál es la calificación semafórica de la decisión clínica en «"
                          + reg["titulo"] + "»?"),
            "opciones": opciones(dc["semaforo"], ("verde", "amarillo", "rojo"), ETIQUETA_SEMAFORO),
            "explicacion": ("Semáforo " + dc["semaforo"].upper() + ". Perla: "
                            + str(dc.get("perla_prescripcion", ""))),
        }))

    # 4. El desenlace que va con su efecto. Los distractores son los efectos de
    #    los OTROS desenlaces de la misma ficha: reales, y por eso difíciles.
    con_efecto = [e for e in reg.get("evidencia") or []
                  if e.get("efecto") and e.get("desenlace")]
    if len(con_efecto) >= 3:
        elegido = rnd.choice(con_efecto)
        distractores = [e for e in con_efecto if e is not elegido]
        rnd.shuffle(distractores)
        candidatos = [elegido] + distractores[:3]
        rnd.shuffle(candidatos)
        salida.append(dict(base, **{
            "id": reg["id"] + "-efecto",
            "tipo": "efecto",
            "enunciado": ("En «" + reg["titulo"] + "», ¿qué efecto se midió para "
                          "«" + elegido["desenlace"] + "»?"),
            "opciones": [{"texto": " ".join(str(c["efecto"]).split()),
                          "valor": c["desenlace"],
                          "correcta": c is elegido} for c in candidatos],
            "explicacion": (str(elegido.get("estudio", "")) + ", "
                            + str(elegido.get("diseno", "")) + ". "
                            + str(elegido.get("efecto", ""))),
            "ref": elegido.get("ref"),
        }))
    return salida


def preguntas_de_farmaco(reg, archivo, todos, rnd):
    """Contraindicaciones: los distractores son contraindicaciones de OTROS
    fármacos del repositorio. Con un solo fármaco no hay banco, y la pregunta
    simplemente no se genera: es preferible a rellenar con inventos."""
    url = "farmacos/" + archivo.replace(".yaml", ".html")
    contras = [c.get("motivo") for c in
               (reg.get("seguridad") or {}).get("contraindicaciones") or []
               if c.get("motivo")]
    if not contras:
        return []

    ajenas = []
    for otro in todos:
        if otro["id"] == reg["id"]:
            continue
        for c in (otro.get("seguridad") or {}).get("contraindicaciones") or []:
            if c.get("motivo"):
                ajenas.append(c["motivo"])
    if len(ajenas) < 2:
        return []

    correcta = rnd.choice(contras)
    rnd.shuffle(ajenas)
    candidatos = [correcta] + ajenas[:3]
    rnd.shuffle(candidatos)
    return [{
        "id": reg["id"] + "-contraindicacion",
        "tipo": "contraindicacion",
        "farmaco": reg["id"],
        "url": url,
        "dci": reg.get("dci"),
        "atc": reg.get("atc"),
        "enunciado": "¿Cuál de estas es una contraindicación de " + reg["dci"] + "?",
        "opciones": [{"texto": c, "valor": c, "correcta": c == correcta}
                     for c in candidatos],
        "explicacion": "Contraindicaciones registradas: " + "; ".join(contras) + ".",
    }]


def main():
    ap = argparse.ArgumentParser(description="Genera build/reto.json desde las fichas.")
    ap.add_argument("--min-opciones", type=int, default=2,
                    help="descarta preguntas con menos opciones que esto")
    ap.add_argument("--semilla", type=int, default=20260824,
                    help="semilla del barajado; fija por defecto para que el "
                         "reto sea reproducible entre corridas")
    args = ap.parse_args()

    estado = cargar()
    if estado["informe"].errores:
        print("El reto no se genera sobre un repositorio con errores.",
              file=sys.stderr)
        return 1

    rnd = random.Random(args.semilla)
    todas = []
    for ident, reg in sorted(estado["fichas"].items()):
        todas += preguntas_de_ficha(reg, estado["archivos"][ident],
                                    estado["farmacos"].get(reg.get("farmaco")), rnd)
    farmacos = list(estado["farmacos"].values())
    for ident, reg in sorted(estado["farmacos"].items()):
        todas += preguntas_de_farmaco(reg, estado["archivos"][ident], farmacos, rnd)
    for ident, reg in sorted(estado["selecciones"].items()):
        todas += preguntas_de_seleccion(reg, estado["archivos"][ident], rnd)
    for ident, reg in sorted(estado["farmacoterapias"].items()):
        todas += preguntas_de_farmacoterapia(
            reg, estado["archivos"][ident],
            estado["farmacos"].get(reg.get("farmaco")), rnd)

    todas = [p for p in todas if len(p["opciones"]) >= args.min_opciones]

    SALIDA.mkdir(exist_ok=True)
    (SALIDA / "reto.json").write_text(json.dumps({
        "generado": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "total": len(todas),
        "tipos": sorted({p["tipo"] for p in todas}),
        "preguntas": todas,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    print("reto generado")
    print("  build/reto.json      " + str(len(todas)) + " preguntas")
    for t in sorted({p["tipo"] for p in todas}):
        print("    " + t + "  " + str(sum(1 for p in todas if p["tipo"] == t)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
