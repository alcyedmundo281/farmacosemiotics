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
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
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

    def test_el_recuento_de_farmacoterapias_reparte_el_total(self):
        """El contador de build.py informó mal durante varias oleadas.

        Contaba «completas» las que traían cronograma y umbrales —una
        propiedad del formato— y «con huecos declarados» solo las demás, de
        modo que una farmacoterapia con los dos apartados enteros y tres
        huecos declarados se anunciaba como completa y no aparecía nunca en
        la columna de los huecos. Las dos cifras se leían como un reparto del
        total y no lo eran.

        Los tres conjuntos que las sustituyen sí reparten el total, y esta
        prueba existe para que sigan haciéndolo: sin solaparse y sin dejar
        fuera a nadie.
        """
        estado = build.cargar()
        fa = estado["farmacoterapias"]
        sin_huecos = {i for i, r in fa.items()
                      if build.es_gpc(r) and not build.huecos_de(r)}
        con_huecos = {i for i, r in fa.items() if build.huecos_de(r)}
        mudas = {i for i, r in fa.items()
                 if not build.es_gpc(r) and not build.huecos_de(r)}

        self.assertEqual(sin_huecos | con_huecos | mudas, set(fa),
                         "hay farmacoterapias que no caen en ningún grupo")
        for a, b in ((sin_huecos, con_huecos), (sin_huecos, mudas),
                     (con_huecos, mudas)):
            self.assertEqual(a & b, set(),
                             "los grupos se solapan: " + str(a & b))

        # Y lo que de verdad importa: que sea eso lo que build.py imprime.
        # Comprobar solo las definiciones dejaría pasar un contador que
        # volviera a repartir mal el total, que es el fallo que hubo.
        salida = correr(RAIZ / "scripts" / "build.py").stdout
        m = re.search(r"farmacoterapias\s+(\d+)\s+parte II: (\d+) sin "
                      r"huecos, (\d+) con huecos declarados", salida)
        self.assertIsNotNone(m, "no encuentro la línea del contador:\n"
                                + salida[:400])
        total, dice_sin, dice_con = (int(g) for g in m.groups())
        self.assertEqual(total, len(fa))
        self.assertEqual(dice_sin, len(sin_huecos))
        self.assertEqual(dice_con, len(con_huecos))

        m_mudas = re.search(r"(\d+) sin declarar qué les falta", salida)
        self.assertEqual(int(m_mudas.group(1)) if m_mudas else 0, len(mudas),
                         "el contador calla farmacoterapias a las que les "
                         "falta un apartado sin declararlo")
        self.assertEqual(dice_sin + dice_con + len(mudas), total,
                         "las cifras del contador no reparten el total")

    def test_el_formato_no_se_confunde_con_la_ausencia_de_huecos(self):
        """`es_gpc` responde por el formato, no por el contenido.

        Si alguna vez las dos preguntas coinciden para todos los registros,
        la distinción deja de verse y es fácil volver a colapsarla en el
        contador. Esta prueba no exige que difieran —eso dependería del
        contenido del repositorio—, exige que el código no las trate como
        sinónimos: una farmacoterapia con cronograma, umbrales y huecos
        declarados tiene que salir `es_gpc` y a la vez con huecos.
        """
        reg = {"monitorizacion": [{"fase": "basal"}],
               "umbrales_accion": [{"parametro": "x"}],
               "huecos_declarados": [{"bloque": "reproductivo",
                                      "motivo": "no hay fuente"}]}
        self.assertTrue(build.es_gpc(reg))
        self.assertEqual(build.huecos_de(reg), {"reproductivo"})

    def test_la_seccion_lme_existe_en_el_catalogo(self):
        estado = build.cargar()
        secciones = {str(s["numero"]) for s in estado["catalogo"]["secciones"]}
        for ident, reg in estado["farmacos"].items():
            lme = reg.get("lme") or {}
            if lme.get("presente"):
                self.assertIn(str(lme["seccion"]).split(".")[0], secciones,
                              ident + " cita una sección que no existe")

    def test_el_informe_de_seleccion_compara_y_decide(self):
        estado = build.cargar()
        for ident, reg in estado["selecciones"].items():
            candidatos = reg.get("candidatos") or []
            self.assertGreaterEqual(len(candidatos), 2,
                                    ident + " no compara nada")
            self.assertEqual(
                sum(1 for c in candidatos if c.get("veredicto") == "seleccionado"),
                1, ident + " debe seleccionar exactamente un candidato")
            for c in candidatos:
                for eje in build.EJES:
                    self.assertIn(eje, c, ident + ": " + str(c.get("dci"))
                                  + " no responde al eje " + eje)

    def test_ningun_precio_en_el_eje_costo(self):
        """El costo se juzga, no se cifra: la cifra caduca y cruza mal las
        fronteras. `build.py` lo rechaza, y esta prueba lo deja explícito."""
        estado = build.cargar()
        for ident, reg in estado["selecciones"].items():
            for c in reg.get("candidatos") or []:
                sustento = str((c.get("costo") or {}).get("sustento") or "")
                self.assertNotRegex(sustento, build.RE_PRECIO.pattern,
                                    ident + ": el eje costo lleva una cifra")

    def test_un_hueco_declarado_no_tapa_un_apartado_lleno(self):
        estado = build.cargar()
        for ident, reg in estado["fichas"].items():
            for bloque in build.huecos_de(reg):
                self.assertFalse(reg.get(bloque),
                                 ident + " declara vacío `" + str(bloque)
                                 + "` y tiene contenido")

    def test_todo_umbral_de_accion_trae_conducta(self):
        # Un punto de corte sin qué hacer deja al clínico con un número y sin
        # decisión, que es exactamente donde se falla.
        estado = build.cargar()
        for ident, reg in estado["fichas"].items():
            for u in reg.get("umbrales_accion") or []:
                self.assertTrue(u.get("accion"),
                                ident + ": umbral sin `accion`")
                self.assertTrue(u.get("ref"),
                                ident + ": umbral sin `ref`")

    def test_las_condiciones_resuelven_en_el_indice_fijado(self):
        """El enlace por el que holonmed llega a una selección. Exige el clon
        de medsemiotics-db: sin él no hay nada que comprobar y se salta."""
        if build.localizar_indice() is None:
            self.skipTest("no hay clon de medsemiotics-db al lado")
        inf = build.Informe()
        indice = build.condiciones_del_indice(inf, exigir=True)
        self.assertIsNotNone(indice, inf.errores)
        estado = build.cargar()
        enlazadas = {i: r["condicion"] for i, r in estado["selecciones"].items()
                     if r.get("condicion")}
        self.assertTrue(enlazadas, "ninguna selección declara su condición")
        for ident, cond in enlazadas.items():
            self.assertIn(cond, indice, ident + ": " + cond + " no existe")


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
        self.assertIn("se juzga", r.stdout)

    def test_detecta_una_ficha_sin_farmaco(self):
        repo = self.preparar()
        self.estropear(repo, "farmaco: 'FS:0001'", "farmaco: 'FS:9999'")
        r = self.validar(repo)
        self.assertEqual(r.returncode, 1)
        self.assertIn("no existe en farmacos/", r.stdout)

    # ── La capa de guía: que el validador la vigile de verdad ────────────
    # La capa de guía se mudó a farmacoterapia/: es de la molécula, no del
    # par fármaco × indicación.
    GPC = "farmacoterapia/FA0009-azatioprina.yaml"
    SEL = "selecciones/SEL0001-penfigo-vulgar.yaml"

    def test_detecta_una_fase_de_monitorizacion_sin_frecuencia(self):
        # Se renombra la clave en vez de recortar el bloque: así el YAML sigue
        # siendo válido y lo que se prueba es el validador, no el parser.
        repo = self.preparar()
        # El ancla incluye la primera línea del valor: `frecuencia` aparece
        # antes en farmacogenética, donde es opcional, y sustituir ahí no
        # probaría nada.
        self.estropear(repo,
                       "    frecuencia: >-\n      Antes de cada escalado",
                       "    frecuencia_antigua: >-\n      Antes de cada escalado",
                       fichero=self.GPC)
        r = self.validar(repo)
        self.assertEqual(r.returncode, 1)
        self.assertIn("frecuencia", r.stdout)

    def test_detecta_una_interaccion_sin_gravedad(self):
        repo = self.preparar()
        self.estropear(repo, "    gravedad: mayor\n", "", fichero=self.GPC)
        r = self.validar(repo)
        self.assertEqual(r.returncode, 1)
        self.assertIn("gravedad", r.stdout)

    def test_detecta_un_fenotipo_sin_conducta(self):
        repo = self.preparar()
        self.estropear(repo,
                       "      conducta: No hace falta alterar la dosis de inicio.\n",
                       "", fichero=self.GPC)
        r = self.validar(repo)
        self.assertEqual(r.returncode, 1)
        self.assertIn("conducta", r.stdout)

    def test_detecta_un_hueco_sin_motivo(self):
        repo = self.preparar()
        self.estropear(repo, "  - bloque: atencion_compartida\n    motivo: >-",
                       "  - bloque: atencion_compartida\n    motivo_antiguo: >-",
                       fichero=self.GPC)
        r = self.validar(repo)
        self.assertEqual(r.returncode, 1)
        self.assertIn("olvido", r.stdout)

    def test_detecta_un_hueco_que_declara_vacio_un_bloque_lleno(self):
        repo = self.preparar()
        self.estropear(repo, "  - bloque: umbrales_accion",
                       "  - bloque: monitorizacion", fichero=self.GPC)
        r = self.validar(repo)
        self.assertEqual(r.returncode, 1)
        self.assertIn("tiene contenido", r.stdout)

    def test_detecta_una_compatibilidad_reproductiva_inventada(self):
        repo = self.preparar()
        self.estropear(repo, "    compatibilidad: compatible\n",
                       "    compatibilidad: seguro\n", fichero=self.GPC)
        r = self.validar(repo)
        self.assertEqual(r.returncode, 1)
        self.assertIn("lista cerrada", r.stdout)

    def _con_indice(self, repo, *extra):
        clon = build.localizar_indice()
        if clon is None:
            self.skipTest("no hay clon de medsemiotics-db al lado")
        import os
        entorno = dict(os.environ, MEDSEMIOTICS_DB=str(clon))
        return subprocess.run([sys.executable, str(repo / "scripts" / "build.py")]
                              + list(extra), capture_output=True, text=True,
                              encoding="utf-8", cwd=repo, env=entorno)

    def test_detecta_una_condicion_que_no_existe_en_el_indice(self):
        repo = self.preparar()
        self.estropear(repo, "condicion: 'HM:6009'", "condicion: 'HM:6999'",
                       "selecciones/SEL0027-faringoamigdalitis-estreptococica-del-grupo-a.yaml")
        r = self._con_indice(repo)
        self.assertEqual(r.returncode, 1)
        self.assertIn("no existe en medsemiotics-db", r.stdout)

    def test_detecta_una_condicion_mal_formada(self):
        repo = self.preparar()
        self.estropear(repo, "condicion: 'HM:6009'", "condicion: 'faringitis'",
                       "selecciones/SEL0027-faringoamigdalitis-estreptococica-del-grupo-a.yaml")
        r = self.validar(repo)
        self.assertEqual(r.returncode, 1)
        self.assertIn("HM:NNNN", r.stdout)

    def test_sin_indice_y_exigido_es_error(self):
        repo = self.preparar()
        import os
        entorno = {k: v for k, v in os.environ.items() if k != "MEDSEMIOTICS_DB"}
        r = subprocess.run([sys.executable, str(repo / "scripts" / "build.py"),
                            "--exigir-indice"], capture_output=True, text=True,
                           encoding="utf-8", cwd=repo, env=entorno)
        # El temporal no tiene medsemiotics-db al lado.
        self.assertEqual(r.returncode, 1)
        self.assertIn("no encuentro medsemiotics-db", r.stdout)


class LaCita(unittest.TestCase):
    """CITATION.cff es la única descripción de autoría que queda. El depósito
    de Zenodo archiva la versión anterior a la reescritura y no se toca."""

    def test_el_orcid_supera_su_digito_de_control(self):
        # Un ORCID mal copiado apunta a otra persona, o a nadie. ISO 7064 MOD 11-2.
        import yaml
        cff = yaml.safe_load((RAIZ / "CITATION.cff").read_text(encoding="utf-8"))
        suelto = cff["authors"][0]["orcid"].rsplit("/", 1)[-1]
        self.assertRegex(suelto, r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")
        digitos = suelto.replace("-", "")
        total = 0
        for d in digitos[:15]:
            total = (total + int(d)) * 2
        control = (12 - total % 11) % 11
        self.assertEqual("X" if control == 10 else str(control), digitos[15])


if __name__ == "__main__":
    unittest.main()
