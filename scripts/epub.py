#!/usr/bin/env python3
"""
EPUB — encuaderna con Quarto el .qmd único que proyecta qmd.py.

    python scripts/epub.py                 # proyecta y renderiza
    python scripts/epub.py --solo-render   # da por buena la proyección actual
    python scripts/epub.py --a html        # la misma fuente, otra salida

Deja build/guias-farmacoterapeuticas.epub.

Este módulo no sabe nada de terapéutica: llama a qmd.py para que proyecte el
repositorio y luego a Quarto para que encuaderne. Ese reparto es lo que
permite que el libro se regenere entero sin que nadie edite una salida.

Quarto no viene con el repositorio ni se instala desde aquí. Si no está, este
script lo dice y sale con error en vez de dejar un EPUB a medias: se descarga
de <https://quarto.org/docs/download/>.
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))

from qmd import NOMBRE, SALIDA, main as proyectar  # noqa: E402
from build import RAIZ  # noqa: E402

DESTINO = RAIZ / "build"
EXTENSION = {"epub": ".epub", "html": ".html", "pdf": ".pdf", "docx": ".docx"}


def quarto():
    """La ruta al ejecutable, o None. Se busca también donde lo deja el
    instalador de usuario, que no siempre queda en el PATH de un CI."""
    hallado = shutil.which("quarto")
    if hallado:
        return hallado
    for candidato in (Path.home() / ".local/bin/quarto",
                      Path("/usr/local/bin/quarto"),
                      Path("/opt/quarto/bin/quarto")):
        if candidato.exists() and os.access(candidato, os.X_OK):
            return str(candidato)
    return None


def falta_quarto():
    print("Quarto no está instalado, así que el EPUB no puede encuadernarse.",
          file=sys.stderr)
    print("", file=sys.stderr)
    print("  La proyección sí está hecha y es válida:", file=sys.stderr)
    print("    " + str((SALIDA / (NOMBRE + ".qmd"))), file=sys.stderr)
    print("", file=sys.stderr)
    print("  Instálalo desde https://quarto.org/docs/download/ y repite:",
          file=sys.stderr)
    print("    python scripts/epub.py --solo-render", file=sys.stderr)
    return 2


def render(ejecutable, formato):
    fuente = SALIDA / (NOMBRE + ".qmd")
    if not fuente.exists():
        print("No hay nada que encuadernar: falta " + str(fuente)
              + ". Ejecuta `python scripts/qmd.py`.", file=sys.stderr)
        return 1

    orden = [ejecutable, "render", fuente.name, "--to", formato]
    print("  " + " ".join(orden) + "   (en " + str(SALIDA.relative_to(RAIZ)) + ")")
    proceso = subprocess.run(orden, cwd=SALIDA, capture_output=True, text=True)
    if proceso.returncode != 0:
        print("Quarto falló:", file=sys.stderr)
        for linea in (proceso.stderr or proceso.stdout).splitlines()[-25:]:
            print("  " + linea, file=sys.stderr)
        return 1

    producido = SALIDA / (NOMBRE + EXTENSION.get(formato, "." + formato))
    if not producido.exists():
        print("Quarto terminó bien pero no encuentro " + producido.name
              + " en " + str(SALIDA) + ".", file=sys.stderr)
        return 1

    DESTINO.mkdir(parents=True, exist_ok=True)
    final = DESTINO / producido.name
    # El libro se deja junto a index.json y no dentro de la carpeta de
    # trabajo de Quarto: es una salida del repositorio, no un intermedio.
    if producido.resolve() != final.resolve():
        shutil.move(str(producido), str(final))

    tam = final.stat().st_size
    print("")
    print("  " + str(final.relative_to(RAIZ)) + "   "
          + str(round(tam / 1024)) + " KB")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="Encuaderna con Quarto el .qmd único de todas las guías.")
    ap.add_argument("--a", default="epub", choices=sorted(EXTENSION),
                    help="formato de salida (por defecto epub)")
    ap.add_argument("--solo-render", action="store_true",
                    help="no reproyecta: usa el .qmd que ya está en build/")
    args = ap.parse_args()

    if not args.solo_render:
        codigo = proyectar()
        if codigo:
            return codigo
        print("")

    ejecutable = quarto()
    if not ejecutable:
        return falta_quarto()
    return render(ejecutable, args.a)


if __name__ == "__main__":
    raise SystemExit(main())
