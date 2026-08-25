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
  --tinta:#15171a; --suave:#738a94; --tenue:#94A3B8; --linea:#e5eff5; --linea-suave:#f0f0f0;
  --papel:#FFFFFF; --fondo:#FFFFFF; --acento:#962828; --acento-hover:#7d2121;
  --enlace:#962828; --realce:#f4f5f6;
  --verde:#10B981; --verde-bg:#ECFDF5; --verde-txt:#065F46;
  --amarillo:#F59E0B; --amarillo-bg:#FFFBEB; --amarillo-txt:#92400E;
  --rojo:#EF4444; --rojo-bg:#FEF2F2; --rojo-txt:#991B1B;
  --mono:'IBM Plex Mono',ui-monospace,SFMono-Regular,Menlo,monospace;
  --serif:'Literata',Georgia,serif;
  --sans:'Inter',system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
}
@media (prefers-color-scheme:dark){
  :root{
    --tinta:#E8EBED; --suave:#9AA3AA; --tenue:#64748B; --linea:#2A3035; --linea-suave:#1E2429;
    --papel:#0F1316; --fondo:#14181B; --acento:#E05656; --acento-hover:#F06A6A;
    --enlace:#E05656; --realce:#1A2024;
    --verde:#10B981; --verde-bg:#064E3B; --verde-txt:#6EE7B7;
    --amarillo:#F59E0B; --amarillo-bg:#78350F; --amarillo-txt:#FDE68A;
    --rojo:#EF4444; --rojo-bg:#7F1D1D; --rojo-txt:#FCA5A5;
  }
}
*{box-sizing:border-box;margin:0;padding:0}
html{-webkit-text-size-adjust:100%}
body{
  margin:0;background:var(--papel);color:var(--tinta);
  font-family:var(--sans);line-height:1.65;font-size:16px;
}
.envoltorio{max-width:1040px;margin:0 auto;padding:0 24px 80px}
a{color:var(--enlace);text-decoration:none}
a:hover{text-decoration:underline}

/* ── Ghost Header (3 Column Navbar) ── */
.ghost-header{
  display:grid;grid-template-columns:1fr auto 1fr;align-items:center;
  padding:24px 0;border-bottom:1px solid var(--linea-suave);margin-bottom:32px;
}
.ghost-nav-left{
  display:flex;align-items:center;gap:20px;
}
.ghost-nav-item{
  font-size:15px;font-weight:700;color:var(--tinta);text-decoration:none;
}
.ghost-nav-item:hover{color:var(--acento);text-decoration:none}
.ghost-nav-item.active{color:var(--acento)}

.ghost-logo{
  text-align:center;
}
.ghost-logo a{
  font-family:var(--sans);font-size:26px;font-weight:800;letter-spacing:-.04em;
  color:var(--tinta);text-decoration:none;
}

.ghost-nav-right{
  display:flex;align-items:center;justify-content:flex-end;gap:16px;
}
.ghost-search-btn{
  background:none;border:none;color:var(--tinta);cursor:pointer;display:flex;align-items:center;padding:4px;
}
.ghost-subscribe-btn{
  background:var(--acento);color:#fff!important;padding:8px 20px;border-radius:9999px;
  font-size:14px;font-weight:600;text-decoration:none;transition:background .2s ease;display:inline-block;
}
.ghost-subscribe-btn:hover{background:var(--acento-hover);text-decoration:none}

@media (max-width:768px){
  .ghost-header{grid-template-columns:1fr 1fr;gap:16px}
  .ghost-logo{text-align:left;grid-column:1/-1}
  .ghost-nav-left{order:2}
  .ghost-nav-right{order:3}
}

/* ── Ghost Hero Section ── */
.ghost-hero{
  text-align:center;padding:24px 0 44px;
}
.ghost-hero-headline{
  font-size:26px;font-weight:700;line-height:1.35;color:var(--tinta);
  max-width:820px;margin:0 auto 28px;letter-spacing:-.015em;
}
.ghost-subscribe-form{
  display:flex;max-width:480px;margin:0 auto;background:var(--realce);
  border-radius:9999px;padding:5px;border:1px solid var(--linea);
}
.ghost-subscribe-input{
  flex:1;border:none;background:transparent;padding:10px 18px;font-size:15px;
  color:var(--tinta);font-family:var(--sans);outline:none;
}
.ghost-subscribe-submit{
  background:var(--acento);color:#fff;border:none;border-radius:9999px;
  padding:10px 24px;font-weight:600;font-size:14px;cursor:pointer;transition:background .2s ease;
}
.ghost-subscribe-submit:hover{background:var(--acento-hover)}

/* ── Section Header ── */
.ghost-section-header{
  padding-bottom:12px;border-bottom:1px solid var(--linea);margin-bottom:32px;
  display:flex;justify-content:space-between;align-items:center;
}
.ghost-section-title{
  font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--tinta);
}
#cuenta{font-size:12px;font-weight:700;color:var(--suave);letter-spacing:.05em}

/* ── Ghost Post List Row ── */
.ghost-post-list{
  display:flex;flex-direction:column;gap:32px;
}
.ghost-post-row{
  display:flex;gap:28px;padding-bottom:32px;border-bottom:1px solid var(--linea-suave);
  align-items:flex-start;text-decoration:none;color:inherit;
}
.ghost-post-thumb{
  width:270px;height:160px;border-radius:6px;background:#15171A;color:#fff;
  flex-shrink:0;display:flex;flex-direction:column;justify-content:space-between;
  padding:16px;box-sizing:border-box;position:relative;overflow:hidden;
  box-shadow:0 2px 8px rgba(0,0,0,0.08);text-decoration:none;
}
.ghost-post-thumb:hover{text-decoration:none}
.ghost-thumb-top{
  display:flex;justify-content:space-between;align-items:center;
}
.ghost-thumb-atc{
  font-family:var(--mono);font-size:11px;font-weight:700;text-transform:uppercase;
  background:rgba(255,255,255,0.15);padding:3px 8px;border-radius:4px;color:#fff;
}
.ghost-thumb-sem{
  font-family:var(--mono);font-size:10px;font-weight:700;text-transform:uppercase;
  padding:3px 7px;border-radius:4px;
}
.ghost-thumb-sem.verde{background:rgba(16,185,129,0.25);color:#34D399;border:1px solid #10B981}
.ghost-thumb-sem.amarillo{background:rgba(245,158,11,0.25);color:#FBBF24;border:1px solid #F59E0B}
.ghost-thumb-center{
  font-size:15px;font-weight:700;color:#fff;line-height:1.25;
}
.ghost-thumb-bottom{
  display:flex;justify-content:space-between;align-items:center;
}
.ghost-thumb-nnt{
  font-family:var(--mono);font-size:12px;font-weight:700;color:#38BDF8;
}
.ghost-thumb-lme{
  font-family:var(--mono);font-size:10.5px;color:#94A3B8;
}

.ghost-post-content{flex:1}
.ghost-post-title{
  font-size:22px;font-weight:700;line-height:1.3;margin:0 0 10px;
}
.ghost-post-title a{
  color:var(--acento);text-decoration:none;
}
.ghost-post-title a:hover{text-decoration:underline}
.ghost-post-excerpt{
  font-size:15px;line-height:1.55;color:#555;margin:0 0 14px;
}
@media (prefers-color-scheme:dark){
  .ghost-post-excerpt{color:#9AA3AA}
}
.ghost-post-meta{
  font-size:13px;color:var(--suave);
}

@media (max-width:680px){
  .ghost-post-row{flex-direction:column;gap:16px}
  .ghost-post-thumb{width:100%;height:140px}
}

/* ── Ghost Article Page ── */
.ghost-article{
  padding:20px 0;
}
.migas{
  font-family:var(--mono);font-size:11.5px;text-transform:uppercase;
  letter-spacing:.06em;color:var(--suave);margin-bottom:20px;
}
.migas a{color:var(--suave)}
h1{font-family:var(--sans);font-weight:800;font-size:34px;line-height:1.2;
   letter-spacing:-.02em;margin:0 0 12px;color:var(--tinta)}
h2{font-family:var(--sans);font-weight:700;font-size:20px;
   letter-spacing:-.01em;color:var(--tinta);margin:42px 0 18px;
   padding-bottom:10px;border-bottom:2px solid var(--linea)}
h3{font-family:var(--sans);font-weight:700;font-size:18px;margin:22px 0 10px}
p{margin:0 0 16px}
.sub{color:var(--suave);font-size:17px;margin:0 0 24px}

.ghost-tag{
  font-family:var(--mono);font-size:11px;font-weight:700;text-transform:uppercase;
  letter-spacing:.06em;padding:4px 10px;border-radius:6px;background:var(--realce);color:var(--suave);
}
.semaforo-pill{
  font-family:var(--mono);font-size:11px;font-weight:700;text-transform:uppercase;
  padding:4px 12px;border-radius:14px;
}
.semaforo-pill.verde{background:var(--verde-bg);color:var(--verde-txt);border:1px solid var(--verde)}
.semaforo-pill.amarillo{background:var(--amarillo-bg);color:var(--amarillo-txt);border:1px solid var(--amarillo)}
.semaforo-pill.rojo{background:var(--rojo-bg);color:var(--rojo-txt);border:1px solid var(--rojo)}

.recuadro{
  border-left:4px solid var(--acento);background:var(--realce);
  padding:20px 24px;margin:0 0 28px;border-radius:0 10px 10px 0;
}
.recuadro.fuerte{border-left-color:var(--verde);background:var(--verde-bg);color:var(--verde-txt)}
.recuadro.peligro{border-left-color:var(--rojo);background:var(--rojo-bg);color:var(--rojo-txt)}
.recuadro.aviso{border-left-color:var(--amarillo);background:var(--amarillo-bg);color:var(--amarillo-txt)}
.recuadro p:last-child{margin-bottom:0}
.recuadro .rotulo{
  font-family:var(--mono);font-size:11px;font-weight:700;text-transform:uppercase;
  letter-spacing:.08em;margin-bottom:8px;display:block;
}

.tabla-scroll{overflow-x:auto;margin:0 0 28px;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:14.5px;min-width:600px;background:var(--fondo);border:1px solid var(--linea);border-radius:10px;overflow:hidden}
th,td{text-align:left;vertical-align:top;padding:13px 16px;
      border-bottom:1px solid var(--linea)}
th{font-family:var(--mono);font-size:11.5px;text-transform:uppercase;
   letter-spacing:.05em;color:var(--suave);font-weight:700;background:var(--realce)}
td.num{font-family:var(--mono);font-size:13.5px}

dl.pares{display:grid;grid-template-columns:160px 1fr;gap:10px 24px;margin:0 0 28px;background:var(--fondo);padding:20px;border:1px solid var(--linea);border-radius:12px}
dl.pares dt{font-family:var(--mono);font-size:12px;text-transform:uppercase;
            letter-spacing:.05em;color:var(--suave);padding-top:2px}
dl.pares dd{margin:0}
@media (max-width:640px){
  dl.pares{grid-template-columns:1fr;gap:4px 0}
  dl.pares dd{margin:0 0 14px}
}

ul.limpia{list-style:none;padding:0;margin:0 0 24px}
ul.limpia li{padding:12px 0;border-bottom:1px solid var(--linea-suave)}
ul.limpia li:last-child{border-bottom:none}

.ref{font-family:var(--mono);font-size:11.5px}
.pie{margin-top:64px;padding-top:28px;border-top:1px solid var(--linea);
     font-size:14px;color:var(--suave);text-align:center}

/* ── reto ── */
.opcion{
  display:block;width:100%;text-align:left;font-family:var(--sans);
  font-size:15.5px;padding:14px 16px;margin:0 0 10px;border:1px solid var(--linea);
  border-radius:8px;background:var(--fondo);color:var(--tinta);cursor:pointer;
}
.opcion:hover:not(:disabled){border-color:var(--suave);background:var(--realce)}
.opcion.bien{border-color:var(--verde);background:var(--verde-bg);color:var(--verde-txt)}
.opcion.mal{border-color:var(--rojo);background:var(--rojo-bg);color:var(--rojo-txt)}
.opcion:disabled{cursor:default}
.boton{
  font-family:var(--sans);font-weight:600;font-size:14.5px;padding:12px 24px;
  border:none;border-radius:8px;background:var(--acento);color:#fff;cursor:pointer;
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
        + ld + "\n</head>\n<body>\n<div class=\"envoltorio\">\n"
        '<header class="ghost-header">\n'
        '  <nav class="ghost-nav-left">\n'
        '    <a href="' + prefijo + 'index.html" class="ghost-nav-item">Home</a>\n'
        '    <a href="' + prefijo + 'blog.html" class="ghost-nav-item">Fichas</a>\n'
        '    <a href="' + prefijo + 'reto.html" class="ghost-nav-item">Reto</a>\n'
        '    <a href="' + COMUNIDAD + '" class="ghost-nav-item">About</a>\n'
        '  </nav>\n'
        '  <div class="ghost-logo">\n'
        '    <a href="' + prefijo + 'index.html">farmacosemiotics</a>\n'
        '  </div>\n'
        '  <div class="ghost-nav-right">\n'
        '    <button class="ghost-search-btn" onclick="document.getElementById(\'q\')?document.getElementById(\'q\').focus():window.location.href=\'' + prefijo + 'blog.html\'" aria-label="Buscar">\n'
        '      <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>\n'
        '    </button>\n'
        '    <a href="' + prefijo + 'reto.html" class="ghost-subscribe-btn">Subscribe</a>\n'
        '  </div>\n'
        '</header>\n')


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
            '<a href="' + prefijo + 'index.html">Inicio</a> · '
            '<a href="' + prefijo + 'blog.html">Blog / Revista</a> · '
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
    dc = reg.get("decision_clinica") or {}
    sem = dc.get("semaforo", "verde")

    A(cabeza(reg["titulo"], "../", jsonld,
             " ".join((rec.get("enunciado") or "").split())))
    A(migas("../", reg["titulo"]))
    
    # Cabecera de artículo Ghost
    A('<article class="ghost-article">')
    
    # Tags superiores
    etiquetas = []
    if farmaco and farmaco.get("atc"):
        etiquetas.append(('<span class="ghost-tag">' + e(farmaco["atc"]) + "</span>"))
    if reg.get("indicacion"):
        etiquetas.append(('<span class="ghost-tag">' + e(reg["indicacion"]) + "</span>"))
    lme = (farmaco or {}).get("lme") or {}
    if lme.get("presente"):
        etiquetas.append(('<span class="ghost-tag" style="color:var(--acento)">LME OMS ' + e(str(lme.get("seccion"))) + "</span>"))
    
    sem_pill = '<span class="semaforo-pill ' + sem + '">● SEMÁFORO ' + sem.upper() + '</span>'
    
    A('<div class="ghost-badge-row" style="margin-bottom:16px">'
      + '<div style="display:flex;gap:6px;flex-wrap:wrap">' + "".join(etiquetas) + '</div>'
      + sem_pill
      + '</div>')

    A('<h1 style="font-size:36px;margin-bottom:12px">' + e(reg["titulo"]) + "</h1>")
    if reg.get("titulo_en"):
        A('<p class="sub" style="font-size:18px;margin-bottom:20px;color:var(--suave)">' + e(reg["titulo_en"]) + "</p>")

    # Byline de autoría Ghost
    fecha_txt = str(reg.get("actualizado") or reg.get("fecha") or "2026-08-24")
    A('<div class="ghost-byline" style="margin:20px 0 32px;padding:16px 0;border-top:1px solid var(--linea);border-bottom:1px solid var(--linea)">'
      '<div class="ghost-author">'
        '<div class="ghost-avatar" style="width:36px;height:36px;font-size:13px">AETG</div>'
        '<div>'
          '<div style="font-weight:700;color:var(--tinta);font-size:14.5px">Dr. Alcy Edmundo Torres Guerrero</div>'
          '<div style="font-size:12px;color:var(--suave)">Editor & Fundador · PowerSemiotics</div>'
        '</div>'
      '</div>'
      '<div style="font-size:13px;color:var(--suave);text-align:right">'
        '<div>' + fecha_txt + ' · 5 min de lectura</div>'
        '<div style="font-size:11.5px">Licencia CC BY-SA 4.0</div>'
      '</div>'
      '</div>')

    # Tarjeta de Decisión Rápida / Perla de Prescripción
    if dc.get("perla_prescripcion"):
        clase_sem = "fuerte" if sem == "verde" else ("aviso" if sem == "amarillo" else "peligro")
        A('<div class="recuadro ' + clase_sem + '" style="font-size:16.5px;line-height:1.6"><span class="rotulo">⚡ Decisión Rápida en Punto de Atención · Semáforo '
          + e(sem.upper()) + "</span><p style=\"font-weight:600;margin-bottom:8px\">Perla de prescripción: "
          + e(dc["perla_prescripcion"]) + "</p>"
          + ('<p style="margin-top:8px;font-size:15px;color:inherit">⚠️ <strong>Alerta inmediata:</strong> ' + e(dc["alerta_seguridad_inmediata"]) + "</p>"
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

    A('</article>')

    # Tarjeta de Firma Editorial del Autor y Reto Clínico
    A('<div class="recuadro" style="margin-top:40px;background:var(--fondo);border:1px solid var(--linea);border-left:4px solid var(--acento);border-radius:12px;padding:24px">'
      '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px">'
        '<div style="display:flex;align-items:center;gap:14px">'
          '<div class="ghost-avatar" style="width:48px;height:48px;font-size:16px">AETG</div>'
          '<div>'
            '<div style="font-weight:700;font-size:16px;color:var(--tinta)">Dr. Alcy Edmundo Torres Guerrero</div>'
            '<div style="font-size:13px;color:var(--suave)">Editor & Fundador de PowerSemiotics · Especialista en Semiología Médica</div>'
          '</div>'
        '</div>'
        '<div style="display:flex;gap:10px">'
          '<a href="../reto.html" class="boton" style="font-size:13.5px;padding:9px 18px">🎯 Reto de esta Ficha</a>'
          '<a href="../blog.html" class="ghost-nav-link" style="font-size:13.5px">📰 Ver más Artículos</a>'
        '</div>'
      '</div>'
      '</div>')

    if farmaco:
        A('<p style="margin-top:20px"><a href="../' + mod_indice.ruta_relativa(farmaco) + '">← Ver registro del '
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
const e=s=>(s==null?'':String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'));
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
    res.length+(res.length===1?' post':' posts');
  document.getElementById('res').innerHTML=res.map(r=>{
    const esFicha = r.tipo === 'ficha';
    const sem = r.semaforo || (r.recomendacion_direccion === 'a_favor' ? 'verde' : 'amarillo');
    const semPill = esFicha ? ('<span class="ghost-thumb-sem ' + sem + '">● ' + sem.toUpperCase() + '</span>') : ('<span class="ghost-thumb-sem verde">● FÁRMACO</span>');
    const atcTxt = r.atc || (r.clase || 'ATC');
    const nntTxt = r.nnt ? ('NNT ' + r.nnt) : (r.dci || 'FÁRMACO');
    const excerptTxt = r.perla || r.resumen || r.recomendacion || '';
    const fechaTxt = r.actualizado || r.fecha || '24 Aug 2026';
    const autorTxt = 'Alcy Edmundo Torres Guerrero';

    return '<article class="ghost-post-row">' +
      '<a href="' + r.url + '" class="ghost-post-thumb">' +
        '<div class="ghost-thumb-top">' +
          '<span class="ghost-thumb-atc">' + e(atcTxt) + '</span>' +
          semPill +
        '</div>' +
        '<div class="ghost-thumb-center">' + e(r.dci || r.titulo) + '</div>' +
        '<div class="ghost-thumb-bottom">' +
          '<span class="ghost-thumb-nnt">' + e(nntTxt) + '</span>' +
          '<span class="ghost-thumb-lme">5 min</span>' +
        '</div>' +
      '</a>' +
      '<div class="ghost-post-content">' +
        '<h2 class="ghost-post-title"><a href="' + r.url + '">' + realzar(r.titulo, q) + '</a></h2>' +
        '<p class="ghost-post-excerpt">' + realzar(excerptTxt.slice(0, 240), q) + (excerptTxt.length > 240 ? '...' : '') + '</p>' +
        '<div class="ghost-post-meta">By ' + autorTxt + ' — ' + fechaTxt + '</div>' +
      '</div>' +
    '</article>';
  }).join('')||'<p class="sub" style="text-align:center;padding:40px 0">Nada coincide con la búsqueda. Prueba con otro término clínico o código ATC.</p>';
}
function chips(facetas){
  const cont=document.getElementById('facetas');
  cont.innerHTML=FACETAS.filter(([k])=>(facetas[k]||NADA).length>1).map(([k,rot])=>
    '<div class="grupo" style="display:inline-block;margin:0 12px 10px 0"><span class="rotulo-f" style="display:inline;margin-right:6px;font-size:11px;font-weight:700;color:var(--suave)">'+rot+':</span><span class="chips" style="display:inline-flex;gap:4px">'+
    facetas[k].map(v=>'<button data-f="'+k+'" data-v="'+v+'" aria-pressed="false" style="font-size:11.5px;padding:3px 10px;border-radius:12px;border:1px solid var(--linea);background:var(--realce);color:var(--suave);cursor:pointer">'+
      eti(v)+'</button>').join('')+'</span></div>').join('');
  cont.addEventListener('click',ev=>{
    const b=ev.target.closest('button'); if(!b) return;
    const k=b.dataset.f,v=b.dataset.v;
    F[k]=F[k]||new Set();
    if(F[k].has(v)){F[k].delete(v);b.setAttribute('aria-pressed','false');b.style.background='var(--realce)';b.style.color='var(--suave)';}
    else {F[k].add(v);b.setAttribute('aria-pressed','true');b.style.background='var(--acento)';b.style.color='#fff';}
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


def pagina_blog(total):
    return (cabeza("Blog Clínico & Revista Editorial — Farmacosemiotics", "", None,
                   "Publicación médica independiente: Fichas de terapéutica racional, balanza NNT/NNH y evidencia GRADE anclada a PubMed.")
            + '<section class="ghost-hero">\n'
            + '  <h1 class="ghost-hero-headline">Terapéutica racional para el médico de primer contacto. Una ficha, un NNT/NNH, una decisión — cada semana.</h1>\n'
            + '  <div class="ghost-subscribe-form">\n'
            + '    <input id="q" type="search" class="ghost-subscribe-input" placeholder="jamie@example.com o buscar fármaco..." autocomplete="off" aria-label="Buscar">\n'
            + '    <button class="ghost-subscribe-submit" onclick="document.getElementById(\'q\').focus()">Subscribe</button>\n'
            + '  </div>\n'
            + '</section>\n'
            + '<div class="ghost-section-header">\n'
            + '  <span class="ghost-section-title">LATEST</span>\n'
            + '  <span id="cuenta"></span>\n'
            + '</div>\n'
            + '<div id="facetas" style="margin-bottom:24px"></div>\n'
            + '<div id="res" class="ghost-post-list"></div>\n'
            + "<script>" + BUSCADOR_JS + "</script>\n"
            + pie(""))


def pagina_index(total):
    return (cabeza("Farmacosemiotics — Terapéutica Racional & Evidencia Clínica", "", None,
                   "Portal principal de Farmacosemiotics: Ecosistema de terapéutica racional, balanza de impacto NNT/NNH y biblioteca clínica.")
            + '<section class="ghost-hero">\n'
            + '  <h1 class="ghost-hero-headline">Terapéutica racional para el médico de primer contacto. Una ficha, un NNT/NNH, una decisión — cada semana.</h1>\n'
            + '  <div class="ghost-subscribe-form">\n'
            + '    <input id="q" type="search" class="ghost-subscribe-input" placeholder="jamie@example.com o buscar fármaco..." autocomplete="off" aria-label="Buscar">\n'
            + '    <button class="ghost-subscribe-submit" onclick="document.getElementById(\'q\').focus()">Subscribe</button>\n'
            + '  </div>\n'
            + '</section>\n'
            + '<div class="ghost-section-header">\n'
            + '  <span class="ghost-section-title">LATEST</span>\n'
            + '  <span id="cuenta"></span>\n'
            + '</div>\n'
            + '<div id="facetas" style="margin-bottom:24px"></div>\n'
            + '<div id="res" class="ghost-post-list"></div>\n'
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
    return (cabeza("Reto Clínico — farmacosemiotics", "", None,
                   "Preguntas derivadas de las fichas, con enlace a la fuente.")
            + '<div class="ghost-section-header" style="margin-top:20px">\n'
            + '  <span class="ghost-section-title">🎯 RETO CLÍNICO & AUTOEVALUACIÓN</span>\n'
            + '</div>\n'
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
    (salida / "index.html").write_text(pagina_index(total), encoding="utf-8")
    (salida / "blog.html").write_text(pagina_blog(total), encoding="utf-8")
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
    print("  índice + blog + reto index.html · blog.html · reto.html")
    print("")
    print("Para verlo:  python -m http.server -d " + args.salida + " 8000")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
