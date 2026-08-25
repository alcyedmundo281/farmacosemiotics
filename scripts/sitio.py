#!/usr/bin/env python3
"""
SITIO — el frontend estático que sirve GitHub Pages.

    python scripts/sitio.py
    python scripts/sitio.py --salida build/sitio

Produce en build/sitio/:
  index.html                    buscador con facetas (el «UpToDate» del banco)
  reto.html                     el reto, que lee reto.json
  fichas/*.html                 una página por ficha
  farmacos/*.html               una página por fármaco
  estilo.css                    hoja única, sin dependencias
  index.json · reto.json        copiados junto al sitio

Dos decisiones que conviene no deshacer sin pensarlo:

  - **El sitio no consulta ninguna API en tiempo de ejecución.** openFDA y
    PubMed se resuelven en el build y quedan congelados con su fecha de
    consulta. Una página que consulta en vivo enseña algo distinto cada día y
    no se puede citar.
  - **Todos los enlaces son relativos.** Así el mismo build funciona en
    `usuario.github.io/farmacosemiotics/`, en un dominio propio y abierto
    desde el disco. Es también lo que permite que el reto enlace a la ficha
    que sostiene cada respuesta.
"""
import argparse
import html
import json
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))

from build import cargar, RAIZ  # noqa: E402
import indice as mod_indice  # noqa: E402

AVISO = ("Material educativo. No sustituye el juicio clínico ni la ficha "
         "técnica aprobada por la agencia reguladora del lugar de uso.")

# La casa. farmacosemiotics es un sitio de PROYECTO dentro de este dominio, no
# el dominio: vive en powersemiotics.com/farmacosemiotics/ porque el sitio de
# usuario (alcyedmundo281.github.io) tiene powersemiotics.com como dominio
# propio y todos los proyectos de la cuenta lo heredan.
#
# De ahí la regla que NO se rompe: este repositorio nunca genera un fichero
# CNAME. Un CNAME con `powersemiotics.com` aquí reclamaría el vértice del
# dominio para farmacosemiotics y tumbaría el sitio principal y, con él, al
# resto del ecosistema. El dominio se hereda; no se pide.
COMUNIDAD = "https://powersemiotics.com/"

ETI = {
    "alta": "alta", "moderada": "moderada", "baja": "baja", "muy_baja": "muy baja",
    "a_favor": "a favor", "en_contra": "en contra", "ninguna": "sin recomendación",
    "fuerte": "fuerte", "condicional": "condicional",
    "core": "núcleo", "complementary": "complementaria",
    "critico": "crítico", "importante": "importante", "no_importante": "no importante",
    "grande": "grande", "moderado": "moderado", "pequeno": "pequeño",
    "trivial": "trivial", "no_se_sabe": "no se sabe",
    "eca": "ECA", "metaanalisis": "metaanálisis",
    "revision_sistematica": "revisión sistemática", "ensayo_clinico": "ensayo clínico",
    "cohorte": "cohorte", "casos_controles": "casos y controles",
    "transversal": "transversal", "serie_casos": "serie de casos",
    "guia": "guía", "consenso": "consenso",
    "borrador": "borrador", "revisado": "revisado", "publicado": "publicado",
    "riesgo_de_sesgo": "riesgo de sesgo", "inconsistencia": "inconsistencia",
    "evidencia_indirecta": "evidencia indirecta", "imprecision": "imprecisión",
    "sesgo_de_publicacion": "sesgo de publicación",
    "caracter_secundario": "carácter secundario",
    "muy_frecuente": "muy frecuente", "frecuente": "frecuente",
    "poco_frecuente": "poco frecuente", "rara": "rara", "muy_rara": "muy rara",
    "leve": "leve", "mortal": "mortal",
}


def e(x):
    """Escapa y normaliza el espacio: los bloques `>-` de YAML traen saltos."""
    return html.escape(" ".join(str(x or "").split()))


def eti(x):
    return ETI.get(x, str(x or "").replace("_", " "))


CSS = """
:root{
  --tinta:#15191C; --suave:#5C646B; --linea:#E0E4E7; --papel:#FBFCFC;
  --fondo:#FFFFFF; --acento:#1F5C4D; --alerta:#8A3A1F; --aviso:#8A4B00;
  --enlace:#2E5A87; --realce:#F4F7F6;
  --mono:'IBM Plex Mono',ui-monospace,SFMono-Regular,Menlo,monospace;
  --serif:'Literata',Georgia,'Times New Roman',serif;
  --sans:'Archivo',system-ui,-apple-system,'Segoe UI',sans-serif;
}
@media (prefers-color-scheme:dark){
  :root{
    --tinta:#E8EBED; --suave:#9AA3AA; --linea:#2A3035; --papel:#14181B;
    --fondo:#0F1316; --acento:#6FBFA6; --alerta:#E0906F; --aviso:#D9A24A;
    --enlace:#7FAFD9; --realce:#1A2024;
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0;background:var(--papel);color:var(--tinta);
  font-family:var(--serif);line-height:1.65;font-size:17px;
}
.envoltorio{max-width:820px;margin:0 auto;padding:28px 18px 72px}
a{color:var(--enlace)}
a:hover{text-decoration-thickness:2px}

.migas{
  font-family:var(--mono);font-size:11px;text-transform:uppercase;
  letter-spacing:.08em;color:var(--suave);margin-bottom:14px;
}
.migas a{color:var(--suave)}
h1{font-family:var(--sans);font-weight:600;font-size:29px;line-height:1.2;
   letter-spacing:-.015em;margin:0 0 8px}
h2{font-family:var(--sans);font-weight:600;font-size:15px;text-transform:uppercase;
   letter-spacing:.07em;color:var(--suave);margin:38px 0 12px;
   padding-bottom:7px;border-bottom:1px solid var(--linea)}
h3{font-family:var(--sans);font-weight:600;font-size:17px;margin:24px 0 6px}
p{margin:0 0 14px}
.sub{color:var(--suave);font-size:16px;margin:0 0 18px}

.etiquetas{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 22px}
.etiqueta{
  font-family:var(--mono);font-size:10.5px;text-transform:uppercase;
  letter-spacing:.06em;padding:4px 9px;border:1px solid var(--linea);
  border-radius:20px;color:var(--suave);background:var(--fondo);white-space:nowrap;
}
.etiqueta.fuerte{border-color:var(--acento);color:var(--acento)}
.etiqueta.peligro{border-color:var(--alerta);color:var(--alerta)}
.etiqueta.borrador{border-color:var(--aviso);color:var(--aviso)}

.recuadro{
  border-left:3px solid var(--acento);background:var(--realce);
  padding:16px 18px;margin:0 0 24px;border-radius:0 4px 4px 0;
}
.recuadro.peligro{border-left-color:var(--alerta)}
.recuadro.aviso{border-left-color:var(--aviso)}
.recuadro p:last-child{margin-bottom:0}
.recuadro .rotulo{
  font-family:var(--mono);font-size:10.5px;text-transform:uppercase;
  letter-spacing:.08em;color:var(--suave);margin-bottom:6px;display:block;
}

.tabla-scroll{overflow-x:auto;margin:0 0 22px;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:15px;min-width:560px}
th,td{text-align:left;vertical-align:top;padding:9px 11px;
      border-bottom:1px solid var(--linea)}
th{font-family:var(--sans);font-size:12px;text-transform:uppercase;
   letter-spacing:.05em;color:var(--suave);font-weight:600}
td.num{font-family:var(--mono);font-size:13.5px;white-space:nowrap}

dl.pares{display:grid;grid-template-columns:auto 1fr;gap:5px 18px;margin:0 0 22px}
dl.pares dt{font-family:var(--mono);font-size:12px;text-transform:uppercase;
            letter-spacing:.05em;color:var(--suave);padding-top:3px}
dl.pares dd{margin:0}
@media (max-width:560px){
  dl.pares{grid-template-columns:1fr;gap:0 0}
  dl.pares dd{margin:0 0 12px}
}

ul.limpia{list-style:none;padding:0;margin:0 0 20px}
ul.limpia li{padding:9px 0;border-bottom:1px solid var(--linea)}
ul.limpia li:last-child{border-bottom:none}

.ref{font-family:var(--mono);font-size:12px}
.pie{margin-top:52px;padding-top:18px;border-top:1px solid var(--linea);
     font-size:13.5px;color:var(--suave)}

/* ── buscador ── */
#q{
  width:100%;font-family:var(--serif);font-size:19px;padding:13px 15px;
  border:1px solid var(--linea);border-radius:6px;background:var(--fondo);
  color:var(--tinta);
}
#q:focus{outline:2px solid var(--acento);outline-offset:-1px;border-color:var(--acento)}
.grupo{margin:16px 0}
.rotulo-f{font-family:var(--mono);font-size:10px;text-transform:uppercase;
          letter-spacing:.08em;color:var(--suave);margin-bottom:6px}
.chips{display:flex;gap:5px;flex-wrap:wrap}
.chips button{
  font-family:var(--mono);font-size:11px;text-transform:uppercase;
  letter-spacing:.05em;padding:5px 11px;border:1px solid var(--linea);
  border-radius:20px;background:var(--fondo);color:var(--suave);cursor:pointer;
}
.chips button:hover{border-color:var(--suave)}
.chips button[aria-pressed="true"]{background:var(--acento);border-color:var(--acento);color:#fff}
#cuenta{font-family:var(--mono);font-size:11.5px;text-transform:uppercase;
        letter-spacing:.07em;color:var(--suave);margin:22px 0 10px}
.resultado{padding:15px 0;border-bottom:1px solid var(--linea)}
.resultado h3{margin:0 0 4px;font-size:18px}
.resultado h3 a{text-decoration:none}
.resultado h3 a:hover{text-decoration:underline}
.resultado .meta{font-family:var(--mono);font-size:11px;text-transform:uppercase;
                 letter-spacing:.05em;color:var(--suave);margin-bottom:6px}
.resultado p{margin:0;font-size:15px;color:var(--suave)}
mark{background:rgba(111,191,166,.28);color:inherit;padding:0 1px}

/* ── reto ── */
.opcion{
  display:block;width:100%;text-align:left;font-family:var(--serif);
  font-size:16px;padding:12px 14px;margin:0 0 8px;border:1px solid var(--linea);
  border-radius:5px;background:var(--fondo);color:var(--tinta);cursor:pointer;
}
.opcion:hover:not(:disabled){border-color:var(--suave)}
.opcion.bien{border-color:var(--acento);background:var(--realce)}
.opcion.mal{border-color:var(--alerta)}
.opcion:disabled{cursor:default}
.boton{
  font-family:var(--sans);font-weight:600;font-size:15px;padding:11px 22px;
  border:none;border-radius:6px;background:var(--acento);color:#fff;cursor:pointer;
}
"""


def cabeza(titulo, prefijo, jsonld=None, descripcion=""):
    ld = ""
    if jsonld:
        ld = ('<script type="application/ld+json">'
              + json.dumps(jsonld, ensure_ascii=False) + "</script>")
    return (
        '<!doctype html>\n<html lang="es">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>" + e(titulo) + " — farmacosemiotics</title>\n"
        '<meta name="description" content="' + e(descripcion or AVISO) + '">\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
        "family=Archivo:wght@500;600&family=Literata:ital,wght@0,400;0,600;1,400"
        '&family=IBM+Plex+Mono:wght@400;500&display=swap">\n'
        '<link rel="stylesheet" href="' + prefijo + 'estilo.css">\n'
        + ld + "\n</head>\n<body>\n<div class=\"envoltorio\">\n")


def pie(prefijo):
    return (
        '<div class="pie">\n'
        "<p>" + e(AVISO) + "</p>\n"
        '<p>Contenido bajo <a href="https://creativecommons.org/licenses/by-sa/4.0/">'
        "CC BY-SA 4.0</a>. Generado desde los YAML de "
        '<a href="https://github.com/alcyedmundo281/farmacosemiotics">'
        "farmacosemiotics</a>; cada cifra lleva su PMID en el propio registro.</p>\n"
        '<p>Parte de <a href="' + COMUNIDAD + '">Powersemiotics</a>, junto a '
        '<a href="' + COMUNIDAD + 'biosemiotics/">biosemiotics</a> y '
        '<a href="' + COMUNIDAD + 'medsemiotics/">medsemiotics</a>.</p>\n'
        "</div>\n</div>\n</body>\n</html>\n")


def migas(prefijo, actual):
    """El rastro empieza fuera del repositorio, en la comunidad que lo aloja.
    Ese primer enlace es absoluto a propósito: sale del subdirectorio."""
    return ('<nav class="migas"><a href="' + COMUNIDAD + '">Powersemiotics</a> · '
            '<a href="' + prefijo + 'index.html">Buscar</a> · '
            '<a href="' + prefijo + 'reto.html">Reto</a> · ' + e(actual) + "</nav>\n")


def enlace_pubmed(ref):
    if str(ref).startswith("pmid:"):
        n = str(ref).split(":")[1]
        return ('<a class="ref" href="https://pubmed.ncbi.nlm.nih.gov/' + n
                + '/">PMID ' + n + "</a>")
    return '<span class="ref">' + e(ref) + "</span>"


# ══════════════════ página de ficha ══════════════════

def pagina_ficha(reg, farmaco, referencias, jsonld):
    P = []
    A = P.append
    rec = reg.get("recomendacion") or {}
    balance = reg.get("balance") or {}

    A(cabeza(reg["titulo"], "../", jsonld,
             " ".join((rec.get("enunciado") or "").split())))
    A(migas("../", reg["titulo"]))
    A("<h1>" + e(reg["titulo"]) + "</h1>")
    if reg.get("titulo_en"):
        A('<p class="sub">' + e(reg["titulo_en"]) + "</p>")

    etiquetas = []
    if farmaco and farmaco.get("atc"):
        etiquetas.append(("", "ATC " + farmaco["atc"]))
    lme = (farmaco or {}).get("lme") or {}
    if lme.get("presente"):
        etiquetas.append(("", "LME " + str(lme.get("seccion")) + " · "
                          + eti(lme.get("categoria"))))
    if rec.get("fuerza"):
        etiquetas.append(("fuerte" if rec["fuerza"] == "fuerte" else "",
                          "recomendación " + eti(rec.get("fuerza"))))
    if balance.get("certeza_global"):
        etiquetas.append(("", "certeza " + eti(balance["certeza_global"])))
    if reg.get("estado") != "publicado":
        etiquetas.append(("borrador", eti(reg.get("estado"))))
    A('<div class="etiquetas">'
      + "".join('<span class="etiqueta ' + c + '">' + e(t) + "</span>"
                for c, t in etiquetas) + "</div>")

    dc = reg.get("decision_clinica") or {}
    if dc.get("perla_prescripcion"):
        sem = dc.get("semaforo", "verde")
        clase_sem = "fuerte" if sem == "verde" else ("aviso" if sem == "amarillo" else "peligro")
        A('<div class="recuadro ' + clase_sem + '"><span class="rotulo">Decisión Clínica · Semáforo '
          + e(sem.upper()) + "</span><p><strong>Perla de prescripción:</strong> "
          + e(dc["perla_prescripcion"]) + "</p>"
          + ('<p style="margin-top:6px;font-size:14px">⚠️ <strong>Alerta:</strong> ' + e(dc["alerta_seguridad_inmediata"]) + "</p>"
             if dc.get("alerta_seguridad_inmediata") else "")
          + "</div>")
    elif rec.get("enunciado"):
        A('<div class="recuadro"><span class="rotulo">Recomendación · '
          + e(eti(rec.get("direccion"))) + " · " + e(eti(rec.get("fuerza")))
          + '</span><p>' + e(rec["enunciado"]) + "</p>"
          + ('<p class="ref">' + enlace_pubmed(rec["ref"]) + "</p>"
             if rec.get("ref") else "")
          + "</div>")

    A("<h2>Pregunta</h2>")
    pico = reg.get("pico") or {}
    A('<dl class="pares">')
    for k, rot in (("p", "Población"), ("i", "Intervención"),
                   ("c", "Comparador"), ("o", "Desenlaces")):
        if pico.get(k):
            A("<dt>" + rot + "</dt><dd>" + e(pico[k]) + "</dd>")
    A("</dl>")
    if reg.get("poblacion"):
        A("<p>" + e(reg["poblacion"]) + "</p>")

    pos = reg.get("posologia") or {}
    if pos:
        A("<h2>Posología</h2>")
        A('<dl class="pares">')
        for k, rot in (("inicio", "Inicio"), ("escalado", "Escalado"),
                       ("mantenimiento", "Mantenimiento"), ("maxima", "Dosis máxima"),
                       ("ajuste_renal", "Función renal")):
            if pos.get(k):
                A("<dt>" + rot + "</dt><dd>" + e(pos[k]) + "</dd>")
        A("</dl>")

    evidencia = reg.get("evidencia") or []
    if evidencia:
        tiene_nnt = any(x.get("nnt") for x in evidencia)
        A("<h2>Evidencia</h2>")
        A('<div class="tabla-scroll"><table><thead><tr>'
          "<th>Desenlace</th><th>Efecto</th>"
          + ("<th>NNT</th>" if tiene_nnt else "")
          + "<th>Diseño</th><th>Certeza</th><th>Fuente</th></tr></thead><tbody>")
        for x in evidencia:
            desc = e(x.get("desenlace"))
            if x.get("criticidad"):
                desc += ('<br><span class="ref">' + e(eti(x["criticidad"]))
                         + "</span>")
            certeza = e(eti(x.get("certeza")))
            if x.get("razones_descenso"):
                certeza += ('<br><span class="ref">'
                            + e(", ".join(eti(r) for r in x["razones_descenso"]))
                            + "</span>")
            estudio = e(eti(x.get("diseno")))
            if x.get("estudio"):
                estudio += '<br><span class="ref">' + e(x["estudio"]) + "</span>"
            celda_nnt = ""
            if tiene_nnt:
                if x.get("nnt"):
                    celda_nnt = ('<td class="num" style="color:var(--acento);font-weight:bold">'
                                 + "NNT " + e(x["nnt"])
                                 + ('<br><span class="ref">' + e(x["horizonte_nnt"]) + "</span>" if x.get("horizonte_nnt") else "")
                                 + "</td>")
                else:
                    celda_nnt = '<td class="num" style="color:var(--suave)">—</td>'
            A("<tr><td>" + desc + '</td><td class="num">' + e(x.get("efecto"))
              + "</td>" + celda_nnt + "<td>" + estudio + "</td><td>" + certeza + "</td><td>"
              + enlace_pubmed(x.get("ref")) + "</td></tr>")
        A("</tbody></table></div>")
        for x in evidencia:
            if x.get("nota"):
                A('<div class="recuadro aviso"><span class="rotulo">'
                  + e(x.get("desenlace")) + "</span><p>" + e(x["nota"])
                  + "</p></div>")

    seg_c = reg.get("seguridad_cuantitativa") or []
    if seg_c:
        A("<h2>Seguridad Cuantitativa (NNH)</h2>")
        A('<div class="tabla-scroll"><table><thead><tr>'
          "<th>Evento Adverso</th><th>Incidencia (I vs C)</th><th>NNH</th>"
          "<th>Conducta Clínica</th><th>Fuente</th></tr></thead><tbody>")
        for s in seg_c:
            t_i = e(s.get("tasa_intervencion", ""))
            t_c = e(s.get("tasa_control", ""))
            incid = "I: " + t_i + ("<br>C: " + t_c if t_c else "")
            nnh_txt = "NNH " + e(s.get("nnh")) if s.get("nnh") else "—"
            A("<tr><td><strong>" + e(s.get("evento")) + "</strong>"
              + ('<br><span class="ref">' + e(eti(s.get("gravedad"))) + "</span>" if s.get("gravedad") else "")
              + '</td><td class="num">' + incid
              + '</td><td class="num" style="color:var(--alerta);font-weight:bold">' + nnh_txt
              + ('<br><span class="ref">' + e(s["horizonte_nnh"]) + "</span>" if s.get("horizonte_nnh") else "")
              + "</td><td>" + e(s.get("conducta", ""))
              + "</td><td>" + enlace_pubmed(s.get("ref")) + "</td></tr>")
        A("</tbody></table></div>")

    if balance:
        A("<h2>Balance</h2>")
        A('<dl class="pares">')
        for k, rot in (("efectos_deseables", "Efectos deseables"),
                       ("efectos_indeseables", "Efectos indeseables"),
                       ("certeza_global", "Certeza global")):
            if balance.get(k):
                A("<dt>" + rot + "</dt><dd>" + e(eti(balance[k])) + "</dd>")
        for k, rot in (("valores_preferencias", "Valores y preferencias"),
                       ("equidad", "Equidad"), ("aceptabilidad", "Aceptabilidad"),
                       ("factibilidad", "Factibilidad")):
            if balance.get(k):
                A("<dt>" + rot + "</dt><dd>" + e(balance[k]) + "</dd>")
        A("</dl>")

    alternativas = reg.get("alternativas") or []
    if alternativas:
        A("<h2>Alternativas</h2>")
        A('<ul class="limpia">')
        for a in alternativas:
            marca = (' <span class="etiqueta">LME ' + e(a.get("lme_seccion"))
                     + "</span>") if a.get("lme") else ""
            A("<li><strong>" + e(a.get("dci")) + "</strong> "
              + '<span class="ref">' + e(a.get("atc")) + "</span>" + marca
              + "<br>" + e(a.get("nota")) + "</li>")
        A("</ul>")

    if reg.get("conclusion"):
        A("<h2>Conclusión</h2><p>" + e(reg["conclusion"]) + "</p>")
    if rec.get("nota_consenso"):
        A('<div class="recuadro aviso"><span class="rotulo">Matiz</span><p>'
          + e(rec["nota_consenso"]) + "</p></div>")

    refs = reg.get("refs") or []
    if refs:
        A("<h2>Referencias</h2>")
        A('<ul class="limpia">')
        for r in refs:
            d = referencias.get(r) or {}
            cita = (e(d.get("titulo")) + ". <em>" + e(d.get("publicacion"))
                    + "</em>; " + e(d.get("anio"))) if d else e(r)
            A("<li>" + cita + "<br>" + enlace_pubmed(r)
              + (" · " + eti(d.get("tipo")) if d.get("tipo") else "") + "</li>")
        A("</ul>")

    if farmaco:
        A('<p><a href="../' + mod_indice.ruta_relativa(farmaco) + '">Ficha del '
          "principio activo: " + e(farmaco.get("dci")) + "</a></p>")

    A(pie("../"))
    return "\n".join(P)


# ══════════════════ página de fármaco ══════════════════

def pagina_farmaco(reg, fichas, jsonld):
    P = []
    A = P.append
    A(cabeza(reg["dci"], "../", jsonld,
             " ".join((reg.get("mecanismo") or "").split())[:200]))
    A(migas("../", reg["dci"]))
    A("<h1>" + e(reg["dci"]) + "</h1>")
    A('<p class="sub">' + e(reg.get("dci_en")) + " · "
      + e(reg.get("clase_farmacologica")) + "</p>")

    lme = reg.get("lme") or {}
    etiquetas = []
    if reg.get("atc"):
        etiquetas.append("ATC " + reg["atc"])
    if lme.get("presente"):
        etiquetas.append("LME " + str(lme.get("seccion")) + " · "
                         + eti(lme.get("categoria")))
        if (lme.get("emlc") or {}).get("presente"):
            etiquetas.append("LME niños · " + eti(lme["emlc"].get("categoria")))
    if reg.get("codigos", {}).get("rxcui"):
        etiquetas.append("RxCUI " + reg["codigos"]["rxcui"])
    A('<div class="etiquetas">'
      + "".join('<span class="etiqueta">' + e(t) + "</span>" for t in etiquetas)
      + "</div>")

    for al in reg.get("alertas") or []:
        A('<div class="recuadro peligro"><span class="rotulo">'
          + e(al.get("agencia")) + " · advertencia con "
          + e(al.get("tipo")) + "</span><p>" + e(al.get("asunto")) + "</p>"
          + ('<p><a href="' + e(al["url"]) + '">Ficha técnica</a> · consultada el '
             + e(al.get("consultado")) + "</p>" if al.get("url") else "")
          + ("<p>" + e(al["tension_con_la_evidencia"]) + "</p>"
             if al.get("tension_con_la_evidencia") else "")
          + "</div>")

    A("<h2>Mecanismo</h2><p>" + e(reg.get("mecanismo")) + "</p>")
    fc = reg.get("farmacocinetica") or {}
    if fc:
        A('<dl class="pares">')
        for k, rot in (("eliminacion", "Eliminación"),
                       ("implicacion", "Implicación clínica")):
            if fc.get(k):
                A("<dt>" + rot + "</dt><dd>" + e(fc[k]) + "</dd>")
        A("</dl>")

    formas = reg.get("formas") or []
    if formas:
        A("<h2>Formas</h2>")
        A('<div class="tabla-scroll"><table><thead><tr><th>Forma</th>'
          "<th>Concentraciones</th><th>Vía</th></tr></thead><tbody>")
        for f in formas:
            A("<tr><td>" + e(f.get("forma")) + '</td><td class="num">'
              + e(", ".join(f.get("concentraciones") or [])) + "</td><td>"
              + e(f.get("via")) + "</td></tr>")
        A("</tbody></table></div>")

    seg = reg.get("seguridad") or {}
    if seg.get("reacciones"):
        A("<h2>Reacciones adversas</h2>")
        A('<div class="tabla-scroll"><table><thead><tr><th>Evento</th>'
          "<th>Frecuencia</th><th>Gravedad</th><th>Fuente</th>"
          "</tr></thead><tbody>")
        for r in seg["reacciones"]:
            A("<tr><td>" + e(r.get("evento"))
              + ("<br>" + e(r.get("nota")) if r.get("nota") else "")
              + "</td><td>" + e(eti(r.get("frecuencia"))) + "</td><td>"
              + e(eti(r.get("gravedad"))) + "</td><td>"
              + enlace_pubmed(r.get("ref")) + "</td></tr>")
        A("</tbody></table></div>")

    if seg.get("contraindicaciones"):
        A("<h2>Contraindicaciones</h2>")
        A('<ul class="limpia">')
        for c in seg["contraindicaciones"]:
            A("<li>" + e(c.get("motivo")) + "</li>")
        A("</ul>")

    if lme.get("presente"):
        A("<h2>Lista Modelo de la OMS</h2>")
        A('<dl class="pares">')
        A("<dt>Sección</dt><dd>" + e(lme.get("seccion")) + " — "
          + e(lme.get("seccion_titulo_en")) + "</dd>")
        A("<dt>Categoría</dt><dd>" + e(eti(lme.get("categoria"))) + "</dd>")
        if lme.get("formulaciones"):
            A("<dt>Formulaciones</dt><dd>"
              + e("; ".join(lme["formulaciones"])) + "</dd>")
        emlc = lme.get("emlc") or {}
        if emlc.get("presente"):
            A("<dt>LME para niños</dt><dd>" + e(emlc.get("seccion")) + " · "
              + e(eti(emlc.get("categoria"))) + "</dd>")
        A("<dt>Edición</dt><dd>" + e(lme.get("edicion")) + ".ª lista ("
          + e(lme.get("anio")) + "), consultada el " + e(lme.get("consultado"))
          + "</dd>")
        A("</dl>")

    if reg.get("regulatorio"):
        A("<h2>Regulatorio</h2>")
        A('<div class="tabla-scroll"><table><thead><tr><th>Agencia</th>'
          "<th>Estado</th><th>Primera aprobación</th><th>Consultado</th>"
          "</tr></thead><tbody>")
        for r in reg["regulatorio"]:
            A("<tr><td>" + e(r.get("agencia")) + "</td><td>" + e(r.get("estado"))
              + '</td><td class="num">' + e(r.get("primera_aprobacion") or "—")
              + ("<br><span class=\"ref\">" + e(r.get("solicitud")) + "</span>"
                 if r.get("solicitud") else "")
              + '</td><td class="num">' + e(r.get("consultado")) + "</td></tr>")
        A("</tbody></table></div>")
        for r in reg["regulatorio"]:
            if r.get("primera_aprobacion_nota"):
                A('<p class="ref">' + e(r["primera_aprobacion_nota"]) + "</p>")

    if fichas:
        A("<h2>Fichas</h2>")
        A('<ul class="limpia">')
        for f in fichas:
            A('<li><a href="../' + mod_indice.ruta_relativa(f) + '">'
              + e(f.get("titulo")) + "</a></li>")
        A("</ul>")

    A(pie("../"))
    return "\n".join(P)


# ══════════════════ buscador ══════════════════

BUSCADOR_JS = """
const NADA=[];let DATOS=[],F={};
const norm=s=>(s||'').toString().toLowerCase()
  .normalize('NFD').replace(/[\\u0300-\\u036f]/g,'');
const ETI={alta:'alta',moderada:'moderada',baja:'baja',muy_baja:'muy baja',
  fuerte:'fuerte',condicional:'condicional',core:'núcleo',
  complementary:'complementaria',farmaco:'fármaco',ficha:'ficha',
  eca:'ECA',metaanalisis:'metaanálisis',revision_sistematica:'revisión sistemática',
  guia:'guía',cohorte:'cohorte',borrador:'borrador',revisado:'revisado',
  publicado:'publicado'};
const eti=v=>ETI[v]||String(v).replace(/_/g,' ');

const FACETAS=[['tipo','Tipo'],['clase','Clase'],['lme_seccion','Sección LME'],
  ['certeza_global','Certeza'],['recomendacion_fuerza','Fuerza']];

function texto(r){
  return norm([r.titulo,r.titulo_en,r.dci,r.indicacion,r.indicacion_en,r.clase,
    r.atc,r.resumen,r.recomendacion,r.poblacion,
    (r.sinonimos||NADA).join(' '),(r.desenlaces||NADA).join(' ')].join(' '));
}
function realzar(s,q){
  if(!q) return s;
  const i=norm(s).indexOf(norm(q));
  if(i<0) return s;
  return s.slice(0,i)+'<mark>'+s.slice(i,i+q.length)+'</mark>'+s.slice(i+q.length);
}
function filtrar(){
  const q=document.getElementById('q').value.trim();
  const nq=norm(q);
  let res=DATOS.filter(r=>{
    if(nq && !r._t.includes(nq)) return false;
    for(const [k,v] of Object.entries(F)){
      if(!v.size) continue;
      const val=r[k];
      if(Array.isArray(val)){ if(!val.some(x=>v.has(x))) return false; }
      else if(!v.has(val)) return false;
    }
    return true;
  });
  // Los fármacos primero: al buscar un principio activo, lo que se quiere ver
  // antes es su identidad, no la evaluación de una de sus indicaciones.
  res.sort((a,b)=>(a.tipo===b.tipo?0:a.tipo==='farmaco'?-1:1));
  pintar(res,q);
}
function pintar(res,q){
  document.getElementById('cuenta').textContent=
    res.length+(res.length===1?' registro':' registros');
  document.getElementById('res').innerHTML=res.map(r=>{
    const meta=[eti(r.tipo),r.atc,r.lme?('LME '+r.lme_seccion):null,
      r.certeza_global?('certeza '+eti(r.certeza_global)):null,
      r.recomendacion_fuerza?eti(r.recomendacion_fuerza):null]
      .filter(Boolean).join(' · ');
    return '<article class="resultado"><div class="meta">'+meta+'</div>'+
      '<h3><a href="'+r.url+'">'+realzar(r.titulo,q)+'</a></h3>'+
      '<p>'+realzar((r.recomendacion||r.resumen||'').slice(0,230),q)+'</p></article>';
  }).join('')||'<p class="sub">Nada coincide. Prueba con la DCI o el código ATC.</p>';
}
function chips(facetas){
  const cont=document.getElementById('facetas');
  cont.innerHTML=FACETAS.filter(([k])=>(facetas[k]||NADA).length>1).map(([k,rot])=>
    '<div class="grupo"><div class="rotulo-f">'+rot+'</div><div class="chips">'+
    facetas[k].map(v=>'<button data-f="'+k+'" data-v="'+v+'" aria-pressed="false">'+
      eti(v)+'</button>').join('')+'</div></div>').join('');
  cont.addEventListener('click',ev=>{
    const b=ev.target.closest('button'); if(!b) return;
    const k=b.dataset.f,v=b.dataset.v;
    F[k]=F[k]||new Set();
    if(F[k].has(v)){F[k].delete(v);b.setAttribute('aria-pressed','false');}
    else {F[k].add(v);b.setAttribute('aria-pressed','true');}
    filtrar();
  });
}
fetch('index.json',{cache:'no-cache'}).then(r=>r.json()).then(d=>{
  DATOS=d.registros.map(r=>Object.assign(r,{_t:texto(r)}));
  chips(d.facetas);
  document.getElementById('q').addEventListener('input',filtrar);
  filtrar();
}).catch(()=>{
  document.getElementById('res').innerHTML=
    '<p class="sub">No se pudo cargar index.json. '+
    'Genera el sitio con <code>python scripts/sitio.py</code> y sírvelo por HTTP.</p>';
});
"""


def pagina_buscador(total):
    return (cabeza("Buscar", "", None,
                   "Buscador de fichas de terapéutica racional ancladas a PubMed.")
            + '<nav class="migas"><a href="' + COMUNIDAD + '">Powersemiotics</a>'
              ' · farmacosemiotics · <a href="reto.html">Reto</a></nav>\n'
            + "<h1>farmacosemiotics</h1>\n"
            + '<p class="sub">Fichas de uso racional de medicamentos. Cada cifra '
              "de eficacia o seguridad lleva su PMID. La meta de contenido es la "
              "Lista Modelo de Medicamentos Esenciales de la OMS.</p>\n"
            + '<input id="q" type="search" autocomplete="off" '
              'placeholder="Principio activo, indicación, clase o código ATC…" '
              'aria-label="Buscar">\n'
            + '<div id="facetas"></div>\n'
            + '<div id="cuenta">' + str(total) + " registros</div>\n"
            + '<div id="res"></div>\n'
            + "<script>" + BUSCADOR_JS + "</script>\n"
            + pie(""))


RETO_JS = """
let BANCO=[],i=0,aciertos=0;
function baraja(a){for(let j=a.length-1;j>0;j--){const k=Math.floor(Math.random()*(j+1));[a[j],a[k]]=[a[k],a[j]];}return a;}
function pinta(){
  if(i>=BANCO.length){
    document.getElementById('reto').innerHTML=
      '<h2>Resultado</h2><p>'+aciertos+' de '+BANCO.length+'.</p>'+
      '<button class="boton" onclick="location.reload()">Otra vuelta</button>';
    return;
  }
  const p=BANCO[i];
  document.getElementById('reto').innerHTML=
    '<div class="meta ref">'+(i+1)+' / '+BANCO.length+' · '+p.tipo.replace(/_/g,' ')+'</div>'+
    '<h3>'+p.enunciado+'</h3>'+
    '<div id="ops">'+baraja(p.opciones.slice()).map((o,n)=>
      '<button class="opcion" data-n="'+n+'" data-ok="'+(o.correcta?1:0)+'">'+
      o.texto+'</button>').join('')+'</div>'+
    '<div id="tras"></div>';
  document.getElementById('ops').addEventListener('click',ev=>{
    const b=ev.target.closest('.opcion'); if(!b) return;
    const ok=b.dataset.ok==='1';
    if(ok) aciertos++;
    document.querySelectorAll('.opcion').forEach(x=>{
      x.disabled=true;
      if(x.dataset.ok==='1') x.classList.add('bien');
      else if(x===b) x.classList.add('mal');
    });
    document.getElementById('tras').innerHTML=
      '<div class="recuadro'+(ok?'':' peligro')+'"><span class="rotulo">'+
      (ok?'Correcto':'Incorrecto')+'</span><p>'+p.explicacion+'</p>'+
      '<p><a href="'+p.url+'">Ir a la ficha que lo sostiene</a></p></div>'+
      '<button class="boton" id="sig">Siguiente</button>';
    document.getElementById('sig').onclick=()=>{i++;pinta();};
  },{once:false});
}
fetch('reto.json',{cache:'no-cache'}).then(r=>r.json()).then(d=>{
  BANCO=baraja(d.preguntas.slice());pinta();
}).catch(()=>{
  document.getElementById('reto').innerHTML=
    '<p class="sub">No se pudo cargar reto.json. Genéralo con '+
    '<code>python scripts/reto.py</code>.</p>';
});
"""


def pagina_reto():
    return (cabeza("Reto", "", None,
                   "Preguntas derivadas de las fichas, con enlace a la fuente.")
            + '<nav class="migas"><a href="' + COMUNIDAD + '">Powersemiotics</a>'
              ' · <a href="index.html">Buscar</a> · Reto</nav>\n'
            + "<h1>Reto</h1>\n"
            + '<p class="sub">Las preguntas se derivan de las fichas: ningún '
              "distractor está inventado. Cada respuesta enlaza con el registro "
              "que la sostiene.</p>\n"
            + '<div id="reto"></div>\n'
            + "<script>" + RETO_JS + "</script>\n"
            + pie(""))


def main():
    ap = argparse.ArgumentParser(description="Genera el sitio estático.")
    ap.add_argument("--salida", default="build/sitio")
    args = ap.parse_args()

    estado = cargar()
    if estado["informe"].errores:
        print("El sitio no se genera sobre un repositorio con errores.",
              file=sys.stderr)
        return 1

    fuente_indice = RAIZ / "build" / "index.json"
    if not fuente_indice.exists():
        print("Falta build/index.json. Ejecuta antes `python scripts/indice.py`.",
              file=sys.stderr)
        return 1

    salida = RAIZ / args.salida
    if salida.exists():
        shutil.rmtree(salida)
    (salida / "fichas").mkdir(parents=True)
    (salida / "farmacos").mkdir(parents=True)

    for reg in list(estado["farmacos"].values()) + list(estado["fichas"].values()):
        reg["_archivo"] = estado["archivos"][reg["id"]]

    n = 0
    for ident, reg in estado["farmacos"].items():
        fichas = sorted((f for f in estado["fichas"].values()
                         if f.get("farmaco") == ident),
                        key=lambda x: x["id"])
        (salida / mod_indice.ruta_relativa(reg)).write_text(
            pagina_farmaco(reg, fichas, mod_indice.jsonld_farmaco(reg)),
            encoding="utf-8")
        n += 1
    for ident, reg in estado["fichas"].items():
        farmaco = estado["farmacos"].get(reg.get("farmaco"))
        (salida / mod_indice.ruta_relativa(reg)).write_text(
            pagina_ficha(reg, farmaco, estado["referencias"],
                         mod_indice.jsonld_ficha(reg, farmaco)),
            encoding="utf-8")
        n += 1

    total = len(estado["farmacos"]) + len(estado["fichas"])
    (salida / "index.html").write_text(pagina_buscador(total), encoding="utf-8")
    (salida / "reto.html").write_text(pagina_reto(), encoding="utf-8")
    (salida / "estilo.css").write_text(CSS, encoding="utf-8")
    (salida / ".nojekyll").write_text("", encoding="utf-8")
    shutil.copy(fuente_indice, salida / "index.json")
    fuente_reto = RAIZ / "build" / "reto.json"
    if fuente_reto.exists():
        shutil.copy(fuente_reto, salida / "reto.json")
    else:
        print("aviso: no hay build/reto.json; la página del reto quedará vacía.",
              file=sys.stderr)

    print("sitio generado en " + args.salida)
    print("  páginas de registro  " + str(n))
    print("  índice + reto        index.html · reto.html")
    print("")
    print("Para verlo:  python -m http.server -d " + args.salida + " 8000")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
