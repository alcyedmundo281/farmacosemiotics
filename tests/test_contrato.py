#!/usr/bin/env python3
"""
El contrato del repositorio, en pruebas.

Se ejecutan con la biblioteca estándar, sin pytest:

    python -m unittest discover -s tests -v

Dos clases de prueba, y la segunda es la que de verdad importa:

  - que el repositorio real valide y genere;
  - que el validador **falle** cuando debe. Un validador que nunca ha fallado
    en una prueba no es un validador, es un adorno: pasaría igual de limpio
    sobre un repositorio con las cifras inventadas.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import build  # noqa: E402


def correr(*args):
    return subprocess.run([sys.executable] + [str(a) for a in args],
                          capture_output=True, text=True, encoding="utf-8",
                          cwd=RAIZ)


class ElRepositorioReal(unittest.TestCase):

    def test_valida_sin_errores(self):
        r = correr(RAIZ / "scripts" / "build.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_toda_ref_resuelve(self):
        estado = build.cargar()
        for coleccion in ("farmacos", "fichas"):
            for ident, reg in estado[coleccion].items():
                for ruta, ref in build.refs_de(reg):
                    if ref.startswith(build.PREFIJOS_NO_PMID):
                        continue
                    self.assertIn(ref, estado["referencias"],
                                  ident + " · " + ruta + " no resuelve")

    def test_ninguna_referencia_retractada(self):
        estado = build.cargar()
        for ident, reg in estado["referencias"].items():
            self.assertFalse((reg.get("verificacion") or {}).get("retractado"),
                             ident + " está retractada y sigue en el banco")

    def test_toda_ficha_apunta_a_un_farmaco_existente(self):
        estado = build.cargar()
        for ident, ficha in estado["fichas"].items():
            self.assertIn(ficha.get("farmaco"), estado["farmacos"],
                          ident + " apunta a un fármaco inexistente")

    def test_la_seccion_lme_existe_en_el_catalogo(self):
        estado = build.cargar()
        secciones = {str(s["numero"]) for s in estado["catalogo"]["secciones"]}
        for ident, reg in estado["farmacos"].items():
            lme = reg.get("lme") or {}
            if lme.get("presente"):
                self.assertIn(str(lme["seccion"]).split(".")[0], secciones,
                              ident + " cita una sección que no existe")


class LasSalidas(unittest.TestCase):
    """Se generan una sola vez para toda la clase: son tres subprocesos."""

    @classmethod
    def setUpClass(cls):
        for script in ("indice.py", "reto.py", "sitio.py"):
            r = correr(RAIZ / "scripts" / script)
            if r.returncode != 0:
                raise unittest.SkipTest(script + " falló: " + r.stderr)
        cls.sitio = RAIZ / "build" / "sitio"
        cls.indice = json.loads(
            (RAIZ / "build" / "index.json").read_text(encoding="utf-8"))

    def test_toda_url_del_indice_existe_en_el_sitio(self):
        for r in self.indice["registros"]:
            self.assertTrue((self.sitio / r["url"]).exists(),
                            r["id"] + " apunta a " + r["url"] + ", que no existe")

    def test_las_urls_son_relativas(self):
        # Si una URL se vuelve absoluta, el sitio deja de funcionar bajo el
        # subdirectorio de Pages y el reto deja de enlazar con su ficha.
        for r in self.indice["registros"]:
            self.assertFalse(r["url"].startswith(("/", "http")),
                             r["id"] + " tiene una URL no relativa")

    def test_el_reto_enlaza_solo_con_paginas_que_existen(self):
        reto = json.loads((RAIZ / "build" / "reto.json").read_text(encoding="utf-8"))
        self.assertGreater(reto["total"], 0)
        for p in reto["preguntas"]:
            self.assertTrue((self.sitio / p["url"]).exists(),
                            p["id"] + " enlaza con " + p["url"])

    def test_cada_pregunta_tiene_una_sola_respuesta_correcta(self):
        reto = json.loads((RAIZ / "build" / "reto.json").read_text(encoding="utf-8"))
        for p in reto["preguntas"]:
            correctas = [o for o in p["opciones"] if o["correcta"]]
            self.assertEqual(len(correctas), 1, p["id"])

    def test_el_jats_esta_bien_formado(self):
        for x in (RAIZ / "build" / "jats").glob("*.xml"):
            ET.parse(x)

    def test_el_sitio_no_lleva_cname(self):
        # Un CNAME en un sitio de PROYECTO reclama el vértice del dominio y
        # tumbaría powersemiotics.com y todo lo que cuelga de él. El dominio se
        # hereda del sitio de usuario; aquí no se pide.
        self.assertEqual(list(self.sitio.rglob("CNAME")), [],
                         "el sitio generó un CNAME: eso secuestra el dominio")

    def test_la_base_del_jsonld_es_el_dominio_publicado(self):
        import indice
        self.assertEqual(indice.BASE,
                         "https://powersemiotics.com/farmacosemiotics/",
                         "las URL absolutas del JSON-LD apuntarían fuera del sitio")
        for j in (RAIZ / "build" / "jsonld").glob("*.json"):
            ld = json.loads(j.read_text(encoding="utf-8"))
            self.assertTrue(str(ld.get("url", "")).startswith(indice.BASE), j.name)

    def test_el_jsonld_declara_contexto_y_tipo(self):
        for j in (RAIZ / "build" / "jsonld").glob("*.json"):
            ld = json.loads(j.read_text(encoding="utf-8"))
            self.assertEqual(ld.get("@context"), "https://schema.org", j.name)
            self.assertIn(ld.get("@type"), ("Drug", "MedicalScholarlyArticle"),
                          j.name)


class ElValidadorFalla(unittest.TestCase):
    """Copia el repositorio a un temporal, lo estropea a propósito y comprueba
    que build.py lo detecta. Sin estas pruebas no sabríamos si valida algo."""

    def preparar(self):
        tmp = Path(tempfile.mkdtemp())
        destino = tmp / "repo"
        shutil.copytree(RAIZ, destino, ignore=shutil.ignore_patterns(
            "build", ".git", "__pycache__", "node_modules"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        return destino

    def validar(self, repo):
        return subprocess.run([sys.executable, str(repo / "scripts" / "build.py")],
                              capture_output=True, text=True, encoding="utf-8",
                              cwd=repo)

    def estropear(self, repo, viejo, nuevo, fichero="fichas/FT0001-metformina-diabetes-tipo-2.yaml"):
        ruta = repo / fichero
        texto = ruta.read_text(encoding="utf-8")
        self.assertIn(viejo, texto, "el texto a sustituir ya no está en la ficha")
        ruta.write_text(texto.replace(viejo, nuevo, 1), encoding="utf-8")

    def test_detecta_una_ref_que_no_resuelve(self):
        repo = self.preparar()
        self.estropear(repo, "ref: 'pmid:9742977'", "ref: 'pmid:99999999'")
        r = self.validar(repo)
        self.assertEqual(r.returncode, 1)
        self.assertIn("no resuelve", r.stdout)

    def test_detecta_una_certeza_sin_razones(self):
        repo = self.preparar()
        self.estropear(repo,
                       "    certeza: moderada\n    razones_descenso:\n      - riesgo_de_sesgo\n",
                       "    certeza: moderada\n")
        r = self.validar(repo)
        self.assertEqual(r.returncode, 1)
        self.assertIn("razones_descenso", r.stdout)

    def test_detecta_una_referencia_retractada(self):
        repo = self.preparar()
        ruta = repo / "referencias" / "pmid-9742977.yaml"
        ruta.write_text(ruta.read_text(encoding="utf-8")
                        .replace("retractado: false", "retractado: true"),
                        encoding="utf-8")
        r = self.validar(repo)
        self.assertEqual(r.returncode, 1)
        self.assertIn("RETRACTADO", r.stdout)

    def test_detecta_contexto_de_un_pais(self):
        repo = self.preparar()
        self.estropear(repo, "cie11: 5A11",
                       "cie11: 5A11\nnota_local: incluido en el CNMB")
        r = self.validar(repo)
        self.assertEqual(r.returncode, 1)
        self.assertIn("internacional", r.stdout)

    def test_detecta_un_precio_en_el_nucleo(self):
        repo = self.preparar()
        self.estropear(repo, "cie11: 5A11",
                       "cie11: 5A11\nprecio_mes: USD 4.20")
        r = self.validar(repo)
        self.assertEqual(r.returncode, 1)
        self.assertIn("costos/", r.stdout)

    def test_detecta_una_ficha_sin_farmaco(self):
        repo = self.preparar()
        self.estropear(repo, "farmaco: 'FS:0001'", "farmaco: 'FS:9999'")
        r = self.validar(repo)
        self.assertEqual(r.returncode, 1)
        self.assertIn("no existe en farmacos/", r.stdout)


if __name__ == "__main__":
    unittest.main()
