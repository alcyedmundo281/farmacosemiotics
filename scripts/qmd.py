#!/usr/bin/env python3
"""
PROYECCIÓN A QUARTO — un solo .qmd con todas las guías.

    python scripts/qmd.py

Produce en build/quarto/:
  guias-farmacoterapeuticas.qmd   TODAS las guías en un único documento
  referencias.bib                 BibLaTeX derivado de referencias/
  _quarto.yml                     el proyecto que epub.py renderiza

La fuente única y obligatoria sigue siendo el YAML del repositorio. Este
módulo no decide nada clínico: transcribe el estado ya validado a la forma que
Quarto sabe encuadernar. Por eso no toca la red, no completa huecos y no
reordena la evidencia; si una guía no trae cronograma de monitorización, el
EPUB sale sin ese apartado en vez de con uno inventado.

Un solo fichero, y no un capítulo por guía, es deliberado: el libro se lee
—y se busca— como un vademécum continuo, y el índice de Quarto ya da la
navegación que daría el troceado.

Las citas salen como `[@clave]` contra referencias.bib, de modo que el vínculo
con el PMID sobrevive al EPUB: quien lea el libro puede resolver cada cifra
hasta PubMed, que es la única razón por la que este repositorio existe.
"""
import argparse
import datetime as dt
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))

from build import (cargar, RAIZ, es_gpc, EJES,  # noqa: E402
                   farmacoterapia_de)

SALIDA = RAIZ / "build" / "quarto"
NOMBRE = "guias-farmacoterapeuticas"
AUTOR = "Dr. Alcy Edmundo Torres Guerrero"
SITIO = "https://powersemiotics.com/farmacosemiotics/"
REPO = "https://github.com/alcyedmundo281/farmacosemiotics"

SEMAFORO_TEXTO = {
    "verde": "Verde — primera línea o beneficio neto claro",
    "amarillo": "Amarillo — segunda línea o recomendación condicional",
    "rojo": "Rojo — balance desfavorable",
}
LINEA_TEXTO = {
    "primera": "primera línea", "segunda": "segunda línea",
    "tercera": "tercera línea", "rescate": "rescate",
    "no_recomendada": "no recomendada",
}
FASE_TEXTO = {
    "basal": "Basal (antes de la primera dosis)",
    "induccion": "Inducción",
    "mantenimiento": "Mantenimiento",
    "estable": "Estable",
    "post_suspension": "Tras la suspensión",
}
JUICIO_TEXTO = {
    "superior": "superior", "equivalente": "equivalente",
    "inferior": "inferior", "sin_datos": "sin datos",
}
VEREDICTO_TEXTO = {
    "seleccionado": "**Seleccionado**",
    "alternativa": "Alternativa",
    "reservado": "Reservado",
    "no_seleccionado": "No seleccionado",
}
EJE_TEXTO = {"eficacia": "Eficacia", "seguridad": "Seguridad",
             "conveniencia": "Conveniencia", "costo": "Costo"}

RESPONSABLE_TEXTO = {
    "especialista": "Especialista",
    "seguimiento": "Médico de seguimiento",
    "compartida": "Compartida",
}


# ─────────────────────────── utilidades de texto ───────────────────────────

def t(valor):
    """Un escalar del YAML como texto de una línea, sin los saltos del bloque."""
    if valor is None:
        return ""
    return " ".join(str(valor).split())


def celda(valor):
    """Texto apto para una celda: la barra vertical rompería la tabla."""
    return t(valor).replace("|", "\\|") or "—"


def lista(valor):
    """Una lista del YAML como enumeración en prosa."""
    if not valor:
        return ""
    if isinstance(valor, str):
        return t(valor)
    return "; ".join(t(x) for x in valor if x not in (None, ""))


class Doc:
    """Acumulador de líneas Markdown que se despreocupa de los saltos dobles.

    `desplazamiento` existe porque los mismos renderizadores de apartado
    —cribado, monitorización, evidencia— sirven a la farmacoterapia y a la
    guía, que cuelgan de niveles distintos. Sin él ambos escribirían `###` y
    el índice del EPUB saldría plano, con los apartados de una guía como
    hermanos suyos en vez de como hijos.
    """

    def __init__(self, desplazamiento=0):
        self.lineas = []
        self.desplazamiento = desplazamiento

    def p(self, texto=""):
        self.lineas.append(texto)
        return self

    def blanco(self):
        if self.lineas and self.lineas[-1] != "":
            self.lineas.append("")
        return self

    def titulo(self, nivel, texto, ident=None, absoluto=False):
        self.blanco()
        marca = " {#" + ident + "}" if ident else ""
        if not absoluto:
            nivel += self.desplazamiento
        self.lineas.append("#" * min(nivel, 6) + " " + texto + marca)
        self.blanco()
        return self

    def parrafo(self, texto):
        texto = t(texto)
        if texto:
            self.blanco()
            self.lineas.append(texto)
            self.blanco()
        return self

    def tabla(self, cabeceras, filas):
        """Solo escribe la tabla si hay al menos una fila con contenido."""
        filas = [f for f in filas if any(t(c) for c in f)]
        if not filas:
            return self
        self.blanco()
        self.lineas.append("| " + " | ".join(cabeceras) + " |")
        self.lineas.append("|" + "|".join(["---"] * len(cabeceras)) + "|")
        for f in filas:
            self.lineas.append("| " + " | ".join(celda(c) for c in f) + " |")
        self.blanco()
        return self

    def pares(self, cabeceras, filas):
        """Tabla de etiqueta y valor. La fila sin valor no se escribe: un
        guion en «Ajuste hepático» diría que se miró y no hay, cuando lo que
        pasa es que el campo no está."""
        return self.tabla(cabeceras, [(a, b) for a, b in filas if t(b)])

    def puntos(self, elementos):
        elementos = [t(e) for e in elementos if t(e)]
        if not elementos:
            return self
        self.blanco()
        for e in elementos:
            self.lineas.append("- " + e)
        self.blanco()
        return self

    def texto(self):
        salida = "\n".join(self.lineas)
        while "\n\n\n" in salida:
            salida = salida.replace("\n\n\n", "\n\n")
        return salida.strip() + "\n"


# ─────────────────────────────── bibliografía ───────────────────────────────

def clave(ref, referencias):
    """La clave BibLaTeX de una `ref`, o None si no la sostiene un artículo."""
    datos = referencias.get(ref)
    return datos.get("clave_bibtex") if datos else None


def cita(ref, referencias):
    """`pmid:9742977` → `[@ukpds1998]`. Las fuentes institucionales, en texto:
    no tienen entrada bibliográfica y fingir una las volvería incomprobables."""
    if not ref:
        return ""
    k = clave(ref, referencias)
    if k:
        return " [@" + k + "]"
    etiqueta = t(ref).split(":", 1)[0].upper()
    return " (" + etiqueta + ")"


def citas(refs, referencias):
    claves = [clave(r, referencias) for r in refs or []]
    claves = [k for k in claves if k]
    return " [" + "; ".join("@" + k for k in claves) + "]" if claves else ""


def bib_escapar(s):
    return t(s).replace("{", "").replace("}", "").replace("\\", "")


def bibliografia(referencias):
    """BibLaTeX desde referencias/. El PMID viaja como campo propio para que
    el vínculo con PubMed sobreviva a la encuadernación."""
    salida = ["% Generado por scripts/qmd.py desde referencias/.",
              "% No se edita: se regenera. La fuente es el YAML del repositorio.",
              ""]
    for ident in sorted(referencias):
        reg = referencias[ident]
        k = reg.get("clave_bibtex")
        if not k:
            continue
        ids = reg.get("identificadores") or {}
        campos = [
            ("author", " and ".join(t(a) for a in reg.get("autores") or [])),
            ("title", bib_escapar(reg.get("titulo"))),
            ("journaltitle", bib_escapar(reg.get("publicacion"))),
            ("year", t(reg.get("anio"))),
            ("volume", t(reg.get("volumen"))),
            ("number", t(reg.get("numero"))),
            ("pages", t(reg.get("paginas"))),
            ("doi", t(ids.get("doi"))),
            ("eprint", t(ids.get("pmid"))),
            ("eprinttype", "pubmed" if ids.get("pmid") else ""),
            ("urldate", t((reg.get("verificacion") or {}).get("fecha"))),
        ]
        salida.append("@article{" + k + ",")
        for campo, valor in campos:
            if valor:
                salida.append("  " + campo + " = {" + valor + "},")
        salida.append("}")
        salida.append("")
    return "\n".join(salida)


# ──────────────────────────── las guías, en orden ────────────────────────────

def orden(estado):
    """Por código FT, que es el orden en que se publicaron. Un vademécum
    reordenado por clase cada vez que entra un fármaco deja de ser citable."""
    return [estado["fichas"][i] for i in sorted(estado["fichas"])]


def seccion_identidad(d, farmaco, referencias):
    if not farmaco:
        return
    d.titulo(3, "El principio activo")
    filas = [
        ("DCI", farmaco.get("dci")),
        ("Código ATC", farmaco.get("atc")),
        ("Clase farmacológica", farmaco.get("clase_farmacologica")),
    ]
    lme = farmaco.get("lme") or {}
    if lme.get("presente"):
        filas.append(("Lista Modelo de la OMS",
                      "sección " + t(lme.get("seccion")) + ", "
                      + t(lme.get("categoria"))))
    vias = sorted({f.get("via") for f in farmaco.get("formas") or []
                   if f.get("via")})
    if vias:
        filas.append(("Vías", ", ".join(vias)))
    d.pares(["Dato", "Valor"], filas)
    if farmaco.get("mecanismo"):
        d.parrafo("**Mecanismo.** " + t(farmaco["mecanismo"])
                  + cita(farmaco.get("mecanismo_ref"), referencias))


def seccion_decision(d, reg, referencias):
    dc = reg.get("decision_clinica") or {}
    if not dc:
        return
    d.titulo(3, "Decisión en el punto de atención")
    if dc.get("semaforo"):
        d.parrafo("**Semáforo.** "
                  + SEMAFORO_TEXTO.get(dc["semaforo"], t(dc["semaforo"])))
    if dc.get("perla_prescripcion"):
        d.parrafo("**Perla de prescripción.** " + t(dc["perla_prescripcion"]))
    if dc.get("alerta_seguridad_inmediata"):
        d.parrafo("> **Alerta de seguridad.** "
                  + t(dc["alerta_seguridad_inmediata"]))


def seccion_pregunta(d, reg):
    pico = reg.get("pico") or {}
    if not pico:
        return
    d.titulo(3, "La pregunta")
    d.pares(["", "Pregunta PICO"],
            [("Población", pico.get("p")), ("Intervención", pico.get("i")),
             ("Comparador", pico.get("c")), ("Desenlaces", pico.get("o"))])


def seccion_posicionamiento(d, reg, referencias):
    pos = reg.get("posicionamiento")
    if not isinstance(pos, dict):
        return
    d.titulo(3, "Posicionamiento terapéutico")
    d.parrafo("**Línea de tratamiento.** "
              + LINEA_TEXTO.get(pos.get("linea"), t(pos.get("linea")))
              + cita(pos.get("ref"), referencias))
    if pos.get("justificacion"):
        d.parrafo(t(pos["justificacion"]))
    d.tabla(["Línea", "Opciones", "Nota"],
            [(LINEA_TEXTO.get(e.get("linea"), t(e.get("linea"))),
              lista(e.get("opciones")), t(e.get("nota")))
             for e in pos.get("escalonado") or [] if isinstance(e, dict)])
    des = pos.get("desescalamiento")
    if isinstance(des, dict):
        d.parrafo("**Desescalamiento.** " + t(des.get("enunciado"))
                  + cita(des.get("ref"), referencias))


def seccion_posologia(d, reg, referencias):
    p = reg.get("posologia") or {}
    if not p:
        return
    d.titulo(3, "Posología")
    d.pares(["Fase", "Pauta"],
            [("Inicio", p.get("inicio")), ("Escalado", p.get("escalado")),
             ("Mantenimiento", p.get("mantenimiento")),
             ("Dosis máxima", p.get("maxima")),
             ("Ajuste renal", p.get("ajuste_renal")),
             ("Ajuste hepático", p.get("ajuste_hepatico"))])
    if p.get("ref"):
        k = clave(p["ref"], referencias)
        origen = "[@" + k + "]" if k else t(p["ref"])
        d.parrafo("*Fuente de la posología:* " + origen
                  + (", consultada el " + t(p["consultado"])
                     if p.get("consultado") else ""))


def seccion_farmacogenetica(d, reg, referencias):
    fg = reg.get("farmacogenetica")
    if not isinstance(fg, dict):
        return
    d.titulo(3, "Estratificación farmacogenética")
    encabezado = "**Gen.** " + t(fg.get("gen"))
    if fg.get("prueba"):
        encabezado += " — prueba: " + t(fg["prueba"])
    d.parrafo(encabezado)
    if fg.get("nota"):
        d.parrafo(t(fg["nota"]))
    d.tabla(["Fenotipo", "Frecuencia", "Dosis de inicio", "Conducta"],
            [(f.get("fenotipo"), f.get("frecuencia"), f.get("dosis"),
              t(f.get("conducta")) + cita(f.get("ref"), referencias))
             for f in fg.get("fenotipos") or [] if isinstance(f, dict)])


def seccion_cribado(d, reg, referencias):
    filas = [(c.get("prueba"), c.get("motivo"),
              RESPONSABLE_TEXTO.get(c.get("responsable"), ""),
              t(c.get("condicion")) + cita(c.get("ref"), referencias))
             for c in reg.get("cribado_basal") or [] if isinstance(c, dict)]
    if not filas:
        return
    d.titulo(3, "Cribado antes de la primera dosis")
    d.tabla(["Prueba", "Para qué", "Quién", "Nota"], filas)


def seccion_monitorizacion(d, reg, referencias):
    filas = [(FASE_TEXTO.get(m.get("fase"), t(m.get("fase"))),
              t(m.get("desde")) or t(m.get("periodo")),
              lista(m.get("pruebas")),
              t(m.get("frecuencia")),
              RESPONSABLE_TEXTO.get(m.get("responsable"), "")
              + cita(m.get("ref"), referencias))
             for m in reg.get("monitorizacion") or [] if isinstance(m, dict)]
    if not filas:
        return
    d.titulo(3, "Cronograma de monitorización")
    d.tabla(["Fase", "Periodo", "Pruebas", "Frecuencia", "Quién"], filas)


def seccion_umbrales(d, reg, referencias):
    filas = [(u.get("parametro"), u.get("umbral"),
              t(u.get("accion")) + cita(u.get("ref"), referencias))
             for u in reg.get("umbrales_accion") or [] if isinstance(u, dict)]
    if not filas:
        return
    d.titulo(3, "Qué hacer ante la anomalía analítica")
    d.tabla(["Parámetro", "Punto de corte", "Conducta"], filas)


def seccion_interacciones(d, reg, referencias):
    filas = [(x.get("con"), t(x.get("gravedad")), x.get("efecto"),
              t(x.get("conducta")) + cita(x.get("ref"), referencias))
             for x in reg.get("interacciones") or [] if isinstance(x, dict)]
    if not filas:
        return
    d.titulo(3, "Interacciones que cambian la conducta")
    d.tabla(["Con", "Gravedad", "Efecto", "Conducta"], filas)


def seccion_evidencia(d, reg, referencias):
    ev = reg.get("evidencia") or []
    if not ev:
        return
    d.titulo(3, "Evidencia")
    d.tabla(["Desenlace", "Diseño", "Efecto", "NNT", "Certeza"],
            [(e.get("desenlace"), e.get("diseno"), e.get("efecto"),
              (t(e.get("nnt")) + (" a " + t(e["horizonte_nnt"])
                                  if e.get("horizonte_nnt") else ""))
              if e.get("nnt") else "",
              t(e.get("certeza")) + cita(e.get("ref"), referencias))
             for e in ev if isinstance(e, dict)])
    descensos = [(e.get("desenlace"), lista(e.get("razones_descenso")))
                 for e in ev
                 if isinstance(e, dict) and e.get("razones_descenso")]
    if descensos:
        d.parrafo("**Por qué desciende la certeza.**")
        d.puntos([a + ": " + b for a, b in descensos])


def seccion_seguridad(d, reg, referencias):
    seg = reg.get("seguridad_cuantitativa") or []
    if not seg:
        return
    d.titulo(3, "Seguridad cuantitativa")
    d.tabla(["Evento", "Gravedad", "Intervención", "Control", "NNH", "Conducta"],
            [(s.get("evento"), s.get("gravedad"), s.get("tasa_intervencion"),
              s.get("tasa_control"),
              (t(s.get("nnh")) + (" a " + t(s["horizonte_nnh"])
                                  if s.get("horizonte_nnh") else ""))
              if s.get("nnh") else "",
              t(s.get("conducta")) + cita(s.get("ref"), referencias))
             for s in seg if isinstance(s, dict)])


def seccion_reproductivo(d, reg, referencias):
    rep = reg.get("reproductivo")
    if not isinstance(rep, dict):
        return
    d.titulo(3, "Seguridad reproductiva")
    filas = []
    for etiqueta, campo in (("Gestación", "gestacion"),
                            ("Lactancia", "lactancia")):
        e = rep.get(campo)
        if isinstance(e, dict):
            filas.append((etiqueta, t(e.get("compatibilidad")).replace("_", " "),
                          t(e.get("enunciado")) + cita(e.get("ref"), referencias)))
    d.tabla(["Etapa", "Compatibilidad", "Enunciado"], filas)

    wo = rep.get("washout")
    if isinstance(wo, dict):
        d.parrafo("**Periodo de lavado antes de la concepción.**"
                  + cita(wo.get("ref"), referencias))
        d.puntos([("Mujer: " + t(wo["mujer"])) if wo.get("mujer") else "",
                  ("Varón: " + t(wo["varon"])) if wo.get("varon") else ""])
    anti = rep.get("anticoncepcion")
    if isinstance(anti, dict):
        d.parrafo("**Anticoncepción.** " + t(anti.get("enunciado"))
                  + cita(anti.get("ref"), referencias))


def seccion_atencion_compartida(d, reg, referencias):
    ac = reg.get("atencion_compartida")
    if not isinstance(ac, dict):
        return
    d.titulo(3, "Atención compartida")
    d.parrafo("*Reparto de responsabilidades entre el especialista que indica "
              "y el médico que sigue.*" + cita(ac.get("ref"), referencias))
    for etiqueta, campo in (("Corresponde al especialista", "especialista"),
                            ("Corresponde al médico de seguimiento", "seguimiento"),
                            ("Comprobaciones antes de iniciar", "checklist_preinicio"),
                            ("Suspensión inmediata si", "suspension_inmediata")):
        valores = ac.get(campo)
        if valores:
            d.parrafo("**" + etiqueta + ".**")
            d.puntos(valores if isinstance(valores, list) else [valores])


BLOQUE_TEXTO = {
    "cribado_basal": "Cribado antes de la primera dosis",
    "farmacogenetica": "Estratificación farmacogenética",
    "monitorizacion": "Cronograma de monitorización",
    "umbrales_accion": "Conducta ante la anomalía analítica",
    "interacciones": "Interacciones",
    "reproductivo": "Seguridad reproductiva",
    "atencion_compartida": "Atención compartida",
    "posicionamiento": "Posicionamiento terapéutico",
}


def seccion_huecos(d, reg, referencias, que="esta guía"):
    """Lo que esta guía todavía no puede responder, y por qué. Va impreso: un
    lector que no vea el apartado de umbrales necesita saber si es que no
    aplica, o que no se encontró fuente que lo fijara."""
    huecos = [h for h in reg.get("huecos_declarados") or []
              if isinstance(h, dict)]
    if not huecos:
        return
    d.titulo(3, "Lo que " + que + " todavía no cubre")
    for h in huecos:
        nombre = BLOQUE_TEXTO.get(h.get("bloque"), t(h.get("bloque")))
        linea = "**" + nombre + ".** " + t(h.get("motivo"))
        if h.get("buscado_en"):
            linea += " Se buscó en: " + t(h["buscado_en"])
        linea += citas(h.get("refs"), referencias)
        d.parrafo(linea)


def seccion_recomendacion(d, reg, referencias):
    bal = reg.get("balance") or {}
    rec = reg.get("recomendacion") or {}
    if not (bal or rec):
        return
    d.titulo(3, "Balance y recomendación")
    d.pares(["Juicio GRADE", "Valor"],
            [("Efectos deseables", bal.get("efectos_deseables")),
             ("Efectos indeseables", bal.get("efectos_indeseables")),
             ("Certeza global", bal.get("certeza_global")),
             ("Aceptabilidad", bal.get("aceptabilidad"))])
    if rec.get("enunciado"):
        direccion = t(rec.get("direccion")).replace("_", " ")
        d.parrafo("> **Recomendación " + direccion + ", "
                  + t(rec.get("fuerza")) + ".** " + t(rec["enunciado"])
                  + cita(rec.get("ref"), referencias))
    if rec.get("justificacion_fuerza"):
        d.parrafo(t(rec["justificacion_fuerza"]))
    if rec.get("nota_consenso"):
        d.parrafo(t(rec["nota_consenso"]))


def seccion_alternativas(d, reg):
    filas = [(a.get("dci"), a.get("atc"),
              "sí" if a.get("lme") else "no", a.get("nota"))
             for a in reg.get("alternativas") or [] if isinstance(a, dict)]
    if not filas:
        return
    d.titulo(3, "Alternativas")
    d.tabla(["Alternativa", "ATC", "En la LME", "Nota"], filas)


def ancla(ident):
    return ident.replace(":", "").lower()


# ══════════════ PARTE I: el informe de selección, por problema ══════════════

def informe_seleccion(reg, referencias):
    """Qué fármaco gana para este problema de salud, y por qué.

    La tabla resume; la ficha de cada candidato argumenta. Ese doble paso es
    deliberado: un informe que solo diera la tabla escondería el juicio detrás
    de tres adjetivos, y uno que solo diera la prosa no se podría comparar de
    un vistazo.
    """
    d = Doc()
    d.titulo(2, t(reg.get("problema")), ancla(reg["id"]))

    encabezado = ["**" + t(reg["id"]) + "**"]
    for etiqueta, campo in (("Estado", "estado"), ("Actualizado", "actualizado")):
        if reg.get(campo):
            encabezado.append(etiqueta + ": " + t(reg[campo]))
    d.parrafo(" · ".join(encabezado))

    if reg.get("pregunta"):
        d.parrafo("> **Pregunta.** " + t(reg["pregunta"]))
    if reg.get("poblacion"):
        d.parrafo("**Población.** " + t(reg["poblacion"]))
    if reg.get("contexto"):
        d.parrafo(t(reg["contexto"]))

    candidatos = [c for c in reg.get("candidatos") or [] if isinstance(c, dict)]

    d.titulo(3, "Comparación en los cuatro ejes")
    d.tabla(["Candidato"] + [EJE_TEXTO[e] for e in EJES] + ["Veredicto"],
            [[t(c.get("dci"))]
             + [JUICIO_TEXTO.get((c.get(e) or {}).get("juicio"), "—")
                for e in EJES]
             + [VEREDICTO_TEXTO.get(c.get("veredicto"), t(c.get("veredicto")))]
             for c in candidatos])

    for c in candidatos:
        titulo = t(c.get("dci"))
        if c.get("atc"):
            titulo += " (" + t(c["atc"]) + ")"
        d.titulo(3, titulo)
        if c.get("clase"):
            d.parrafo("*" + t(c["clase"]) + "*")
        d.tabla(["Eje", "Juicio", "Sustento"],
                [(EJE_TEXTO[e],
                  JUICIO_TEXTO.get((c.get(e) or {}).get("juicio"), "—"),
                  t((c.get(e) or {}).get("sustento"))
                  + cita((c.get(e) or {}).get("ref"), referencias))
                 for e in EJES if c.get(e)])
        veredicto = VEREDICTO_TEXTO.get(c.get("veredicto"), t(c.get("veredicto")))
        linea = "**Veredicto:** " + veredicto
        if c.get("nota"):
            linea += ". " + t(c["nota"])
        d.parrafo(linea)

    if reg.get("criterio_decisorio"):
        d.titulo(3, "Qué eje decidió")
        d.parrafo(t(reg["criterio_decisorio"]))
    if reg.get("conclusion"):
        d.titulo(3, "Conclusión del informe")
        d.parrafo(t(reg["conclusion"]))
    if reg.get("refs"):
        d.parrafo("*Referencias del informe:*" + citas(reg["refs"], referencias))
    return d.texto()


# ══════════ PARTE II: la farmacoterapia (molécula) y sus guías ══════════

def farmacoterapia(reg, referencias):
    """Cómo se usa la molécula con seguridad. Vale para todas sus
    indicaciones: lo que una cambie se declara en su guía, no aquí."""
    d = Doc()
    d.titulo(3, "Farmacoterapia", ancla(reg["id"]), absoluto=True)
    d.desplazamiento = 1
    encabezado = ["**" + t(reg["id"]) + "**"]
    if reg.get("estado"):
        encabezado.append("Estado: " + t(reg["estado"]))
    if reg.get("actualizado"):
        encabezado.append("Actualizada: " + t(reg["actualizado"]))
    d.parrafo(" · ".join(encabezado))
    if reg.get("alcance"):
        d.parrafo("**Alcance.** " + t(reg["alcance"]))

    seccion_farmacogenetica(d, reg, referencias)
    seccion_cribado(d, reg, referencias)
    seccion_monitorizacion(d, reg, referencias)
    seccion_umbrales(d, reg, referencias)
    seccion_interacciones(d, reg, referencias)
    seccion_reproductivo(d, reg, referencias)
    seccion_atencion_compartida(d, reg, referencias)
    seccion_huecos(d, reg, referencias, "esta farmacoterapia")
    return d.texto()


def seccion_variaciones(d, reg, referencias):
    """Lo poco que esta indicación se aparta de la farmacoterapia base."""
    variaciones = [v for v in reg.get("variaciones") or [] if isinstance(v, dict)]
    if not variaciones:
        return
    d.titulo(3, "En qué se aparta esta indicación")
    d.tabla(["Apartado", "Cambio"],
            [(BLOQUE_TEXTO.get(v.get("bloque"), t(v.get("bloque"))),
              t(v.get("cambio")) + cita(v.get("ref"), referencias))
             for v in variaciones])


def guia(reg, farmaco, seleccion, tiene_fa, referencias):
    """La decisión situada: lo que cambia con la indicación."""
    d = Doc()
    d.titulo(3, t(reg.get("titulo")), ancla(reg["id"]), absoluto=True)
    d.desplazamiento = 1

    encabezado = ["**" + t(reg["id"]) + "**"]
    if reg.get("indicacion"):
        encabezado.append("Indicación: " + t(reg["indicacion"]))
    if reg.get("estado"):
        encabezado.append("Estado: " + t(reg["estado"]))
    if reg.get("actualizado"):
        encabezado.append("Actualizada: " + t(reg["actualizado"]))
    d.parrafo(" · ".join(encabezado))

    # Los dos enlaces que hacen del libro un híbrido y no dos libros pegados.
    enlaces = []
    if seleccion:
        enlaces.append("Por qué este fármaco: [informe de selección](#"
                       + ancla(seleccion["id"]) + ")")
    if tiene_fa:
        enlaces.append("Cómo se usa: la farmacoterapia de este capítulo")
    if enlaces:
        d.parrafo("*" + " · ".join(enlaces) + ".*")

    if reg.get("poblacion"):
        d.parrafo("**Población.** " + t(reg["poblacion"]))

    seccion_decision(d, reg, referencias)
    seccion_pregunta(d, reg)
    seccion_posicionamiento(d, reg, referencias)
    seccion_posologia(d, reg, referencias)
    seccion_variaciones(d, reg, referencias)
    seccion_evidencia(d, reg, referencias)
    seccion_seguridad(d, reg, referencias)
    seccion_recomendacion(d, reg, referencias)
    seccion_alternativas(d, reg)
    seccion_huecos(d, reg, referencias)

    if reg.get("conclusion"):
        d.titulo(3, "Conclusión")
        d.parrafo(t(reg["conclusion"]))
    if reg.get("refs"):
        d.parrafo("*Referencias de esta guía:*" + citas(reg["refs"], referencias))
    return d.texto()


def capitulo_molecula(farmaco, fa, fichas, estado, referencias):
    """Un capítulo por molécula: su farmacoterapia y todas sus indicaciones.

    Agrupar por molécula y no por indicación es lo que hace visible el caso que
    motivó esta estructura: una misma farmacoterapia sirviendo a varias
    indicaciones, escrita una sola vez.
    """
    d = Doc()
    nombre = t((farmaco or {}).get("dci")) or t(fichas[0].get("titulo"))
    d.titulo(2, nombre, ancla((farmaco or fichas[0])["id"]))
    partes = [d.texto()]

    if farmaco:
        e = Doc()
        seccion_identidad(e, farmaco, referencias)
        partes.append(e.texto())

    if fa:
        partes.append(farmacoterapia(fa, referencias))
    else:
        e = Doc()
        e.parrafo("> **Sin farmacoterapia todavía.** Este fármaco no tiene "
                  "aún el apartado que dice cómo se usa con seguridad "
                  "—cribado, cronograma, umbrales, reproductivo—. Las guías "
                  "que siguen dan la decisión, no el seguimiento.")
        partes.append(e.texto())

    for f in fichas:
        seleccion = estado["selecciones"].get(f.get("seleccion"))
        partes.append(guia(f, farmaco, seleccion, bool(fa), referencias))
    return "\n\n".join(x for x in partes if x.strip())


# ─────────────────────────── el documento entero ───────────────────────────

def portada(estado, hoy):
    n_sel = len(estado["selecciones"])
    n_fa = len(estado["farmacoterapias"])
    n_ft = len(estado["fichas"])
    completas = sum(1 for r in estado["farmacoterapias"].values() if es_gpc(r))

    return "\n".join([
        "---",
        'title: "Selección de medicamentos y farmacoterapia"',
        'subtitle: "Informes de selección y guías de práctica clínica '
        'farmacoterapéuticas, con procedencia verificable"',
        'author: "' + AUTOR + '"',
        "date: " + hoy,
        "lang: es",
        "bibliography: referencias.bib",
        "link-citations: true",
        'reference-section-title: "Bibliografía"',
        "format:",
        "  epub:",
        "    toc: true",
        "    toc-depth: 3",
        "    number-sections: false",
        "    epub-title-page: true",
        "  html:",
        "    toc: true",
        "    toc-depth: 3",
        "    embed-resources: true",
        "---",
        "",
        "# Cómo está armado este libro",
        "",
        "Un medicamento se elige antes de usarse, y son dos preguntas "
        "distintas. Este libro las separa en dos partes y las responde en ese "
        "orden.",
        "",
        "**Parte I — Selección.** " + str(n_sel) + " informe(s), uno por "
        "problema de salud. Compara los candidatos en los cuatro ejes "
        "—eficacia, seguridad, conveniencia y costo— y dice cuál se "
        "selecciona. El juicio de cada eje es comparativo: superior o "
        "inferior *a los otros candidatos de esa misma tabla*, nunca en "
        "abstracto.",
        "",
        "**Parte II — Farmacoterapia.** " + str(n_fa) + " farmacoterapia(s) y "
        + str(n_ft) + " guía(s), agrupadas por molécula. Aquí no se elige: se "
        "usa. Qué se pide antes de la primera dosis, cada cuánto se repite, "
        "qué se hace cuando el análisis se tuerce, qué se le dice a quien "
        "quiere quedarse embarazada, y de quién es cada acto entre el "
        "especialista y el médico que sigue al paciente.",
        "",
        "## Por qué la farmacoterapia va por molécula y la selección por "
        "problema",
        "",
        "Es la misma pregunta repetida en cada apartado: **¿de qué depende "
        "este dato?**",
        "",
        "El cronograma de vigilancia de la azatioprina, su dosificación según "
        "el genotipo y su perfil en el embarazo no cambian entre el pénfigo, "
        "el lupus y la enfermedad inflamatoria intestinal: son propiedades de "
        "la molécula, y se escriben una sola vez. Que la azatioprina sea o no "
        "la elegida sí cambia con el problema, porque compite contra "
        "candidatos distintos en cada uno.",
        "",
        "De ahí la estructura: un capítulo por molécula, con su "
        "farmacoterapia una vez y debajo cada indicación que la usa. Cuando "
        "una indicación se aparta en algo del cronograma común, ese poco "
        "aparece como «en qué se aparta esta indicación», y no como una copia "
        "entera del apartado que acabaría divergiendo.",
        "",
        "## La regla que sostiene el libro",
        "",
        "**Ningún enunciado de eficacia o seguridad sin PMID resoluble.** Cada "
        "cifra de estas páginas —un NNT, un intervalo de confianza, un punto "
        "de corte de neutrófilos— arrastra la cita del artículo del que sale, "
        "y esa cita se trajo de PubMed con una herramienta, no de memoria. El "
        "compilador trata como error, no como advertencia, cualquier cifra que "
        "no pueda seguirse hasta su origen.",
        "",
        "La consecuencia se nota en los huecos. De las " + str(n_fa) + " "
        "farmacoterapias, " + str(completas) + " traen ya el cronograma y los "
        "umbrales que completan el formato; el resto declara, apartado por "
        "apartado, qué falta y por qué no se encontró fuente. Un hueco "
        "declarado informa; uno rellenado con lo verosímil, no. Lo mismo vale "
        "en los informes de selección, donde un eje puede quedar «sin datos» "
        "y eso también es un resultado.",
        "",
        "## El precio no está aquí",
        "",
        "El eje `costo` de la Parte I emite un juicio comparativo —genérico "
        "oral multifuente frente a biológico de marca de administración "
        "hospitalaria— y no una cifra. Es deliberado: un juicio así es "
        "internacional y no caduca, mientras que un precio vuelve el informe "
        "falso en cuanto cruza una frontera y envejece sin que se note. Las "
        "cifras en moneda viven en el repositorio como capa aparte, por país "
        "y con su fecha de consulta.",
        "",
        "## Aviso",
        "",
        "Material educativo. No sustituye el juicio clínico ni la ficha "
        "técnica aprobada por la agencia reguladora del lugar de uso. Las "
        "dosis, los puntos de corte y los cronogramas se transcriben de las "
        "fuentes citadas y pueden no coincidir con la práctica local.",
        "",
        "Se compila desde el repositorio [farmacosemiotics](" + REPO + "), "
        "cuyo YAML es la única fuente: este documento es derivado y se "
        "regenera entero en cada compilación.",
        "",
        "Publicado en <" + SITIO + "> bajo licencia CC BY-SA 4.0.",
        "",
    ])


def documento(estado, hoy):
    """Primero la selección, luego la farmacoterapia. En ese orden, porque es
    el de la decisión: quién se elige antes que cómo se usa."""
    referencias = estado["referencias"]
    partes = [portada(estado, hoy)]

    # ── Parte I ──────────────────────────────────────────────────────────
    partes.append("# Parte I — Selección del medicamento\n")
    if estado["selecciones"]:
        for ident in sorted(estado["selecciones"]):
            partes.append(informe_seleccion(estado["selecciones"][ident],
                                            referencias))
    else:
        partes.append("*Todavía no hay informes de selección.*\n")

    # ── Parte II, agrupada por molécula ──────────────────────────────────
    partes.append("# Parte II — Farmacoterapia\n")
    fichas = orden(estado)
    por_farmaco = {}
    for f in fichas:
        por_farmaco.setdefault(f.get("farmaco"), []).append(f)

    # El orden lo marca el código del fármaco, que es el de publicación: un
    # vademécum que se reordena solo deja de ser citable.
    for fs in sorted(por_farmaco, key=lambda x: str(x)):
        farmaco = estado["farmacos"].get(fs)
        fa = farmacoterapia_de(fs, estado) if fs else None
        partes.append(capitulo_molecula(farmaco, fa, por_farmaco[fs],
                                        estado, referencias))
    return "\n\n".join(partes).rstrip() + "\n"


def proyecto():
    """El _quarto.yml que epub.py renderiza. Un solo documento, dos salidas."""
    return "\n".join([
        "# Generado por scripts/qmd.py. No se edita: se regenera.",
        "project:",
        "  type: default",
        "  output-dir: .",
        "",
        "# El .qmd lleva su propio bloque `format`; aquí solo van los ajustes",
        "# del proyecto, para que `quarto render` no necesite argumentos.",
        "editor: source",
        "",
    ])


def main():
    ap = argparse.ArgumentParser(
        description="Proyecta el repositorio a un único .qmd para Quarto.")
    ap.add_argument("--salida", type=Path, default=SALIDA,
                    help="directorio de destino (por defecto build/quarto/)")
    args = ap.parse_args()

    estado = cargar()
    inf = estado["informe"]
    if inf.errores:
        print("El libro no se proyecta sobre un repositorio con errores.",
              file=sys.stderr)
        for donde, texto in inf.errores:
            print("  " + donde + ": " + texto, file=sys.stderr)
        return 1

    args.salida.mkdir(parents=True, exist_ok=True)
    hoy = dt.date.today().isoformat()

    qmd = args.salida / (NOMBRE + ".qmd")
    qmd.write_text(documento(estado, hoy), encoding="utf-8")
    bib = args.salida / "referencias.bib"
    bib.write_text(bibliografia(estado["referencias"]), encoding="utf-8")
    (args.salida / "_quarto.yml").write_text(proyecto(), encoding="utf-8")

    def corta(ruta):
        """--salida puede apuntar fuera del repositorio (las pruebas lo hacen)."""
        try:
            return str(ruta.relative_to(RAIZ))
        except ValueError:
            return str(ruta)

    fa = estado["farmacoterapias"]
    completas = sum(1 for f in fa.values() if es_gpc(f))
    print("proyección a Quarto")
    print("  " + corta(qmd))
    print("     parte I    " + str(len(estado["selecciones"]))
          + " informes de selección")
    print("     parte II   " + str(len(fa)) + " farmacoterapias ("
          + str(completas) + " completas), " + str(len(estado["fichas"]))
          + " guías")
    print("     total      "
          + str(len(qmd.read_text(encoding="utf-8").splitlines())) + " líneas")
    print("  " + corta(bib) + "   " + str(len(estado["referencias"]))
          + " entradas")
    print("")
    print("  Ahora: python scripts/epub.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
