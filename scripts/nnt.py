#!/usr/bin/env python3
"""
NNT / NNH — Calculadora epidemiológica y auditor matemático para farmacosemiotics.

Uso clínico:
    # 1. Calcular NNT desde tasas (Control: 15%, Intervención: 9%)
    python scripts/nnt.py calc --cer 0.15 --eer 0.09

    # 2. Calcular NNH desde tasas (Control: 1%, Intervención: 3%)
    python scripts/nnt.py harm --cer 0.01 --eer 0.03

    # 3. Auditar consistencia matemática de todas las fichas del repositorio
    python scripts/nnt.py check
"""
import argparse
import math
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))

from build import cargar  # noqa: E402


def calcular_nnt(cer: float, eer: float):
    """
    CER: Tasa de eventos en el grupo control (0.0 a 1.0)
    EER: Tasa de eventos en el grupo intervención (0.0 a 1.0)
    """
    if cer <= 0:
        raise ValueError("CER debe ser mayor que 0.")
    if eer >= cer:
        raise ValueError("EER debe ser menor que CER para calcular reducción de riesgo (beneficio).")

    arr = cer - eer
    rrr = arr / cer
    rr = eer / cer
    nnt = math.ceil(1.0 / arr)

    return {
        "cer": cer,
        "eer": eer,
        "arr": arr,
        "arr_pct": round(arr * 100, 2),
        "rrr": rrr,
        "rrr_pct": round(rrr * 100, 2),
        "rr": round(rr, 3),
        "nnt": nnt,
    }


def calcular_nnh(cer: float, eer: float):
    """
    CER: Tasa de eventos adversos en el grupo control (0.0 a 1.0)
    EER: Tasa de eventos adversos en el grupo intervención (0.0 a 1.0)
    """
    if eer <= cer:
        raise ValueError("EER debe ser mayor que CER para calcular incremento de daño (toxicidad).")

    ari = eer - cer
    rri = (ari / cer) if cer > 0 else float("inf")
    rr = (eer / cer) if cer > 0 else float("inf")
    nnh = math.ceil(1.0 / ari)

    return {
        "cer": cer,
        "eer": eer,
        "ari": ari,
        "ari_pct": round(ari * 100, 2),
        "rri": rri,
        "rri_pct": round(rri * 100, 2) if rri != float("inf") else "inf",
        "rr": round(rr, 3) if rr != float("inf") else "inf",
        "nnh": nnh,
    }


def extraer_porcentaje(texto: str):
    """Extrae un número de porcentaje desde cadenas como '10.3%' o '10,3 %'."""
    if not texto:
        return None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*%", str(texto))
    if m:
        return float(m.group(1).replace(",", ".")) / 100.0
    return None


def auditar_repositorio():
    """Verifica que las cifras de NNT y NNH en las fichas concuerden con las tasas."""
    estado = cargar()
    fichas = estado["fichas"]
    print(f"Auditando coherencia matemática en {len(fichas)} fichas...\n")

    alertas = 0
    verificados = 0

    for fid, reg in sorted(fichas.items()):
        archivo = estado["archivos"][fid]
        evidencia = reg.get("evidencia") or []
        for i, ev in enumerate(evidencia):
            nnt = ev.get("nnt")
            rra = extraer_porcentaje(ev.get("rra"))
            if nnt and rra:
                nnt_teorico = math.ceil(1.0 / rra)
                # Permitir margen de redondeo ±1
                if isinstance(nnt, (int, float)) and abs(nnt - nnt_teorico) > 1:
                    print(f"  ⚠ {archivo} (evidencia[{i}]): NNT declarado={nnt}, pero con RRA={rra*100}% el NNT es {nnt_teorico}")
                    alertas += 1
                else:
                    verificados += 1

        seg_c = reg.get("seguridad_cuantitativa") or []
        for j, s in enumerate(seg_c):
            nnh = s.get("nnh")
            ria = extraer_porcentaje(s.get("ria"))
            if nnh and ria and ria > 0:
                nnh_teorico = math.ceil(1.0 / ria)
                if isinstance(nnh, (int, float)) and abs(nnh - nnh_teorico) > 1:
                    print(f"  ⚠ {archivo} (seguridad[{j}]): NNH declarado={nnh}, pero con RIA={ria*100}% el NNH es {nnh_teorico}")
                    alertas += 1
                else:
                    verificados += 1

    print(f"\n✓ Auditoría finalizada: {verificados} cálculos matemáticos verificados, {alertas} discrepancias.")
    return 0 if alertas == 0 else 1


def main():
    ap = argparse.ArgumentParser(description="Calculadora y auditor de NNT / NNH para farmacosemiotics.")
    sub = ap.add_subparsers(dest="comando", help="comando a ejecutar")

    p_calc = sub.add_parser("calc", help="calcular NNT (Eficacia / Beneficio)")
    p_calc.add_argument("--cer", type=float, required=True, help="Tasa en grupo control (ej. 0.15)")
    p_calc.add_argument("--eer", type=float, required=True, help="Tasa en grupo intervención (ej. 0.09)")

    p_harm = sub.add_parser("harm", help="calcular NNH (Toxicidad / Daño)")
    p_harm.add_argument("--cer", type=float, required=True, help="Tasa de eventos en control (ej. 0.01)")
    p_harm.add_argument("--eer", type=float, required=True, help="Tasa de eventos en intervención (ej. 0.03)")

    sub.add_parser("check", help="auditar la coherencia de NNT y NNH en el repositorio")

    args = ap.parse_args()

    if args.comando == "calc":
        r = calcular_nnt(args.cer, args.eer)
        print("\n── Balance Cuantitativo de Eficacia (NNT) ──")
        print(f"  Control Event Rate (CER):      {r['cer']*100:.2f} %")
        print(f"  Experimental Event Rate (EER): {r['eer']*100:.2f} %")
        print(f"  Reducción Absoluta (RRA/ARR):  {r['arr_pct']:.2f} %")
        print(f"  Reducción Relativa (RRR):      {r['rrr_pct']:.2f} %")
        print(f"  Riesgo Relativo (RR):          {r['rr']}")
        print(f"  → NNT (Número Necesario a Tratar): {r['nnt']}")
        print(f"  Interpretación clínica: Hay que tratar a {r['nnt']} pacientes para evitar 1 evento adicional.\n")

    elif args.comando == "harm":
        r = calcular_nnh(args.cer, args.eer)
        print("\n── Balance Cuantitativo de Seguridad (NNH) ──")
        print(f"  Control Event Rate (CER):      {r['cer']*100:.2f} %")
        print(f"  Experimental Event Rate (EER): {r['eer']*100:.2f} %")
        print(f"  Incremento Absoluto (RIA/ARI): {r['ari_pct']:.2f} %")
        print(f"  Incremento Relativo (RRI):     {r['rri_pct']} %")
        print(f"  Riesgo Relativo (RR):          {r['rr']}")
        print(f"  → NNH (Número Necesario para Dañar): {r['nnh']}")
        print(f"  Interpretación clínica: Por cada {r['nnh']} pacientes tratados, ocurre 1 evento adverso adicional.\n")

    elif args.comando == "check":
        return auditar_repositorio()

    else:
        ap.print_help()

    return 0


if __name__ == "__main__":
    sys.exit(main())
