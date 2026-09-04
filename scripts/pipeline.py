#!/usr/bin/env python3
"""
PIPELINE — Orquestador de alto rendimiento para farmacosemiotics.

Ejecuta el ciclo de vida completo en un solo comando determinista:
    1. build.py         (Validación de esquemas e higiene)
    2. nnt.py check     (Auditoría de consistencia matemática NNT/NNH)
    3. indice.py        (Generación de index.json, JSON-LD y JATS XML)
    4. reto.py          (Generación del banco de autoevaluación)
    5. sitio.py         (Compilación estática Ghost)
    6. qmd.py           (Proyección a un único .qmd para el EPUB de Quarto)
    7. test_contrato    (Suite completa de pruebas de contrato)

El EPUB en sí no entra en el pipeline: `epub.py` necesita Quarto instalado, y
una etapa que falle por una dependencia externa convertiría el pipeline en
algo que no se puede ejecutar en cualquier máquina. La proyección sí entra,
porque es la que puede romperse al cambiar el esquema.

Uso:
    python scripts/pipeline.py
    python scripts/pipeline.py --serve
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent


def ejecutar_etapa(nombre: str, cmd: list, medir=True):
    inicio = time.perf_counter()
    p = subprocess.run([sys.executable] + cmd, cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")
    duracion = (time.perf_counter() - inicio) * 1000

    if p.returncode != 0:
        print(f"\n❌ FALLO EN ETAPA: {nombre}")
        print(p.stdout)
        print(p.stderr, file=sys.stderr)
        return False, duracion

    tiempo_txt = f"({duracion:.1f} ms)" if medir else ""
    print(f"  ✓ {nombre:<32} {tiempo_txt}")
    return True, duracion


def main():
    ap = argparse.ArgumentParser(description="Orquestador unificado de alto rendimiento para farmacosemiotics.")
    ap.add_argument("--serve", action="store_true", help="inicia servidor HTTP local tras compilar con éxito")
    ap.add_argument("--puerto", type=int, default=8000, help="puerto para --serve (defecto: 8000)")
    args = ap.parse_args()

    print("\n╔══════════════════════════════════════════════════════════════════╗")
    print("║        FARMACOSEMIOTICS — PIPELINE DE PRODUCCIÓN & BENCHMARK    ║")
    print("╚══════════════════════════════════════════════════════════════════╝\n")

    t0 = time.perf_counter()
    etapas = [
        ("1. Validación de Esquemas", ["scripts/build.py"]),
        ("2. Auditoría NNT / NNH", ["scripts/nnt.py", "check"]),
        ("3. Indexación Semántica", ["scripts/indice.py"]),
        ("4. Banco Interactivo", ["scripts/reto.py"]),
        ("5. Compilador Ghost", ["scripts/sitio.py"]),
        ("6. Proyección del Libro", ["scripts/qmd.py"]),
        ("7. Tests de Contrato", ["-m", "unittest", "discover", "-s", "tests", "-v"]),
    ]

    tiempos = []
    for nombre, cmd in etapas:
        ok, dt_ms = ejecutar_etapa(nombre, cmd)
        tiempos.append(dt_ms)
        if not ok:
            print("\n❌ Pipeline abortado debido a errores en la etapa anterior.\n")
            return 1

    total_s = time.perf_counter() - t0
    print("\n" + "─" * 68)
    print(f"✓ Pipeline completado con éxito en {total_s:.3f} s ({sum(tiempos):.1f} ms CPU).")
    print("  Todos los esquemas, índices, reto, HTML, libro y tests aprobados.")
    print("  El EPUB se encuaderna aparte: python scripts/epub.py\n")

    if args.serve:
        print(f"Iniciando servidor local en http://localhost:{args.puerto}/ (Ctrl+C para salir)...\n")
        try:
            subprocess.run([sys.executable, "-m", "http.server", "-d", str(RAIZ / "build" / "sitio"), str(args.puerto)])
        except KeyboardInterrupt:
            print("\nServidor detenido.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

