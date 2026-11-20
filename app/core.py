"""Core analytics pipeline for Supply Co-usage Insight.

Implements the five milestones for hospital medical supply co-usage analysis:
1. Mock medical procedure dataset generation (procedures -> supply SKUs).
2. Frequent itemset mining via `thilimarketbasket.mine`.
3. Filtering, ranking, and enrichment of co-occurring supply itemsets.
4. Baseline comparison (observed support vs. independence expectation & lift).
5. Formatted report generation of identified supply bundles.
"""
from __future__ import annotations

import json
import math
import random
from typing import Any

from thilimarketbasket.mine import frequent_itemsets, rules as mine_rules

# Realistic hospital medical supply catalog: SKU -> metadata
SKU_CATALOG: dict[str, dict[str, Any]] = {
    "SKU-GLV-NIT": {"name": "Nitrile Exam Gloves (Pair)", "category": "PPE", "unit_cost": 0.45, "zone": "Zone A - PPE"},
    "SKU-GLV-STR": {"name": "Sterile Surgical Gloves", "category": "PPE", "unit_cost": 2.80, "zone": "Zone A - Sterile"},
    "SKU-ALC-SWB": {"name": "Alcohol Prep Pads (70% IPA)", "category": "Sterile Prep", "unit_cost": 0.15, "zone": "Zone B - Prep"},
    "SKU-CHG-APP": {"name": "Chlorhexidine Skin Applicator", "category": "Sterile Prep", "unit_cost": 3.20, "zone": "Zone B - Prep"},
    "SKU-IVC-20G": {"name": "IV Catheter 20G Safety", "category": "Vascular Access", "unit_cost": 4.50, "zone": "Zone C - Vascular"},
    "SKU-SAL-FLS": {"name": "Normal Saline Flush 10mL", "category": "Vascular Access", "unit_cost": 0.85, "zone": "Zone C - Vascular"},
    "SKU-TEG-DRS": {"name": "Transparent Film Dressing", "category": "Wound Care", "unit_cost": 1.60, "zone": "Zone D - Dressings"},
    "SKU-TRN-DSP": {"name": "Disposable Tourniquet", "category": "Vascular Access", "unit_cost": 0.35, "zone": "Zone C - Vascular"},
    "SKU-GAZ-4X4": {"name": "Sterile Gauze Sponges 4x4", "category": "Wound Care", "unit_cost": 0.60, "zone": "Zone D - Dressings"},
    "SKU-SUT-NYL": {"name": "Nylon Suture 3-0 w/ Needle", "category": "Surgical", "unit_cost": 6.40, "zone": "Zone E - Surgical"},
    "SKU-LID-1PC": {"name": "Lidocaine 1% Vial 10mL", "category": "Anesthesia", "unit_cost": 2.90, "zone": "Zone F - Meds"},
    "SKU-SYR-10M": {"name": "Sterile Syringe 10mL Luer", "category": "Vascular Access", "unit_cost": 0.55, "zone": "Zone C - Vascular"},
    "SKU-DRP-STR": {"name": "Fenestrated Sterile Drape", "category": "Sterile Prep", "unit_cost": 5.10, "zone": "Zone A - Sterile"},
    "SKU-CVC-KIT": {"name": "Central Venous Catheter Tray", "category": "Vascular Access", "unit_cost": 42.00, "zone": "Zone C - Vascular"},
    "SKU-ETT-75": {"name": "Endotracheal Tube 7.5mm", "category": "Airway", "unit_cost": 8.75, "zone": "Zone G - Airway"},
    "SKU-LAR-BLD": {"name": "Laryngoscope Blade #3", "category": "Airway", "unit_cost": 11.50, "zone": "Zone G - Airway"},
    "SKU-BVM-ADU": {"name": "Bag-Valve-Mask Resuscitator", "category": "Airway", "unit_cost": 14.20, "zone": "Zone G - Airway"},
    "SKU-VAC-TUB": {"name": "Vacutainer Blood Tube Set", "category": "Diagnostics", "unit_cost": 1.25, "zone": "Zone H - Lab"},
    "SKU-NED-21G": {"name": "Butterfly Blood Collection Needle", "category": "Diagnostics", "unit_cost": 1.40, "zone": "Zone H - Lab"},
    "SKU-MED-TAP": {"name": "Hypoallergenic Medical Tape", "category": "Wound Care", "unit_cost": 0.90, "zone": "Zone D - Dressings"},
}

# Procedure templates: (procedure_type, department, weight, core_skus, optional_skus)
_PROCEDURE_TEMPLATES: list[tuple[str, str, float, list[str], list[tuple[str, float]]]] = [
    (
        "IV Cannulation",
        "Emergency",
        0.28,
        ["SKU-GLV-NIT", "SKU-ALC-SWB", "SKU-IVC-20G", "SKU-SAL-FLS", "SKU-TEG-DRS"],
        [("SKU-TRN-DSP", 0.85), ("SKU-GAZ-4X4", 0.35), ("SKU-MED-TAP", 0.40)],
    ),
    (
        "Blood Draw & Diagnostics",
        "Outpatient Lab",
        0.24,
        ["SKU-GLV-NIT", "SKU-ALC-SWB", "SKU-TRN-DSP", "SKU-VAC-TUB", "SKU-NED-21G"],
        [("SKU-GAZ-4X4", 0.80), ("SKU-MED-TAP", 0.65)],
    ),
    (
        "Wound Suturing",
        "Emergency",
        0.18,
        ["SKU-GLV-STR", "SKU-CHG-APP", "SKU-GAZ-4X4", "SKU-SUT-NYL", "SKU-LID-1PC", "SKU-SYR-10M"],
        [("SKU-DRP-STR", 0.80), ("SKU-TEG-DRS", 0.55), ("SKU-MED-TAP", 0.45)],
    ),
    (
        "Central Line Insertion",
        "ICU",
        0.12,
        ["SKU-GLV-STR", "SKU-CHG-APP", "SKU-DRP-STR", "SKU-CVC-KIT", "SKU-SAL-FLS", "SKU-TEG-DRS"],
        [("SKU-LID-1PC", 0.90), ("SKU-SYR-10M", 0.90), ("SKU-SUT-NYL", 0.85)],
    ),
    (
        "Airway Intubation",
        "ICU",
        0.10,
        ["SKU-GLV-NIT", "SKU-ETT-75", "SKU-LAR-BLD", "SKU-BVM-ADU", "SKU-SYR-10M"],
        [("SKU-MED-TAP", 0.85), ("SKU-GAZ-4X4", 0.30)],
    ),
    (
        "Minor Surgical Biopsy",
        "Operating Room",
        0.08,
        ["SKU-GLV-STR", "SKU-CHG-APP", "SKU-DRP-STR", "SKU-LID-1PC", "SKU-SYR-10M", "SKU-GAZ-4X4"],
        [("SKU-SUT-NYL", 0.75), ("SKU-TEG-DRS", 0.80)],
    ),
]


# --- Milestone 1: Create mock medical procedure data, where each procedure lists used supply SKUs.
def milestone_1(n_procedures: int = 200, seed: int = 42) -> list[dict[str, Any]]:
    """Generate deterministic mock medical procedure records with associated supply SKUs.

    Each record contains:
      - `procedure_id`: unique identifier (e.g., "PROC-0001")
      - `procedure_type`: clinical procedure name
      - `department`: hospital department
      - `supplies`: sorted list of unique SKU codes used in the procedure
    """
    if n_procedures <= 0:
        raise ValueError("n_procedures must be a positive integer.")

    rng = random.Random(seed)
    weights = [tpl[2] for tpl in _PROCEDURE_TEMPLATES]
    procedures: list[dict[str, Any]] = []

    for idx in range(1, n_procedures + 1):
        proc_type, department, _, core_skus, optional_skus = rng.choices(
            _PROCEDURE_TEMPLATES, weights=weights, k=1
        )[0]
        skus = set(core_skus)
        for sku, prob in optional_skus:
            if rng.random() < prob:
                skus.add(sku)

        procedures.append(
            {
                "procedure_id": f"PROC-{idx:04d}",
                "procedure_type": proc_type,
                "department": department,
                "supplies": sorted(skus),
            }
        )

    return procedures


# --- Milestone 2: Implement frequent itemset mining (e.g., using thilimarketbasket).
def milestone_2(
    procedures: list[dict[str, Any]] | None = None,
    min_support: float = 0.10,
    max_size: int = 4,
) -> dict[frozenset[str], float]:
    """Mine frequent co-occurring supply SKU itemsets using `thilimarketbasket.mine`."""
    if procedures is None:
        procedures = milestone_1()
    if not procedures:
        return {}

    baskets = [proc["supplies"] for proc in procedures if proc.get("supplies")]
    if not baskets:
        return {}

    return frequent_itemsets(baskets, min_support=min_support, max_size=max_size)


# --- Milestone 3: Analyze and display the most frequent co-occurring supply itemsets.
def milestone_3(
    itemsets: dict[frozenset[str], float] | None = None,
    min_size: int = 2,
    top_n: int = 15,
    total_procedures: int = 200,
) -> list[dict[str, Any]]:
    """Filter multi-SKU itemsets and sort them to highlight the strongest co-occurring bundles."""
    if itemsets is None:
        procedures = milestone_1()
        total_procedures = len(procedures)
        itemsets = milestone_2(procedures)

    bundles: list[dict[str, Any]] = []
    for skus, support in itemsets.items():
        if len(skus) < min_size:
            continue
        sorted_skus = sorted(skus)
        names = [SKU_CATALOG.get(s, {}).get("name", s) for s in sorted_skus]
        unit_cost = round(sum(SKU_CATALOG.get(s, {}).get("unit_cost", 0.0) for s in sorted_skus), 2)
        zones = sorted({SKU_CATALOG.get(s, {}).get("zone", "General") for s in sorted_skus})
        bundles.append(
            {
                "skus": sorted_skus,
                "names": names,
                "size": len(sorted_skus),
                "support": round(float(support), 4),
                "procedure_count": round(float(support) * total_procedures),
                "bundle_unit_cost": unit_cost,
                "storage_zones": zones,
            }
        )

    bundles.sort(key=lambda b: (-b["support"], -b["size"], b["skus"]))
    return bundles[:top_n] if top_n > 0 else bundles


# --- Milestone 4: Compare the mined itemsets against simple baseline expectations.
def milestone_4(
    itemsets: dict[frozenset[str], float] | None = None,
    bundles: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Compare mined supply bundles against a naive independence baseline.

    For each bundle B = {s1, s2, ..., sk}:
      - `expected_support` = product of individual SKU supports P(s1) * P(s2) * ... * P(sk)
      - `lift` = observed_support / expected_support
      - `excess_support` = observed_support - expected_support

    Bundles with lift > 1.5 represent genuinely co-used supplies rather than random overlap.
    """
    if itemsets is None:
        procedures = milestone_1()
        itemsets = milestone_2(procedures)
        if bundles is None:
            bundles = milestone_3(itemsets, total_procedures=len(procedures))
    elif bundles is None:
        bundles = milestone_3(itemsets)

    single_support: dict[str, float] = {
        next(iter(k)): float(v) for k, v in itemsets.items() if len(k) == 1
    }

    evaluated: list[dict[str, Any]] = []
    for bundle in bundles:
        skus = bundle["skus"]
        observed = float(bundle["support"])
        expected = math.prod(single_support.get(sku, 0.0) for sku in skus)
        lift = round(observed / expected, 2) if expected > 0 else 0.0
        excess = round(observed - expected, 4)

        if lift >= 2.0:
            strength = "Strong Bundle"
            recommendation = "Pre-kit as sterile procedure pack & bulk-procure together"
        elif lift >= 1.25:
            strength = "Moderate Co-usage"
            recommendation = "Co-locate on adjacent supply cart shelves"
        else:
            strength = "Baseline / Ubiquitous"
            recommendation = "Stock independently as high-turnover general consumables"

        evaluated.append(
            {
                **bundle,
                "expected_support": round(expected, 4),
                "lift": lift,
                "excess_support": excess,
                "strength": strength,
                "recommendation": recommendation,
            }
        )

    evaluated.sort(key=lambda b: (-b["lift"], -b["support"]))
    return evaluated


# --- Milestone 5: Generate a report of identified supply bundles.
def milestone_5(
    evaluated_bundles: list[dict[str, Any]] | None = None,
    procedures: list[dict[str, Any]] | None = None,
    output_format: str = "text",
) -> str:
    """Format identified supply bundles into a clear report (`text`, `markdown`, or `json`)."""
    if procedures is None:
        procedures = milestone_1()
    if evaluated_bundles is None:
        itemsets = milestone_2(procedures)
        bundles = milestone_3(itemsets, total_procedures=len(procedures))
        evaluated_bundles = milestone_4(itemsets, bundles)

    total_procs = len(procedures)
    unique_skus = len({sku for p in procedures for sku in p.get("supplies", [])})
    strong_count = sum(1 for b in evaluated_bundles if b.get("lift", 0) >= 2.0)

    if output_format == "json":
        payload = {
            "summary": {
                "total_procedures": total_procs,
                "unique_skus": unique_skus,
                "bundles_identified": len(evaluated_bundles),
                "strong_bundles": strong_count,
            },
            "bundles": evaluated_bundles,
        }
        return json.dumps(payload, indent=2)

    if output_format == "markdown":
        lines = [
            "# Supply Co-usage Insight Report",
            "",
            f"- **Procedures Analyzed:** {total_procs}",
            f"- **Unique Medical Supply SKUs:** {unique_skus}",
            f"- **Identified Supply Bundles:** {len(evaluated_bundles)} ({strong_count} strong bundles with Lift >= 2.0x)",
            "",
            "| Rank | Supply Bundle (SKUs) | Support | Baseline | Lift | Strength | Action |",
            "|---:|---|---:|---:|---:|---|---|",
        ]
        for idx, b in enumerate(evaluated_bundles, start=1):
            sku_str = " + ".join(b["skus"])
            lines.append(
                f"| {idx} | `{sku_str}` | {b['support']*100:.1f}% | "
                f"{b['expected_support']*100:.1f}% | {b['lift']:.2f}x | "
                f"{b['strength']} | {b['recommendation']} |"
            )
        return "\n".join(lines)

    # Default: clean CLI text table
    lines = [
        "=" * 92,
        "SUPPLY CO-USAGE INSIGHT REPORT",
        "=" * 92,
        f"Procedures Analyzed : {total_procs}",
        f"Unique Supply SKUs  : {unique_skus}",
        f"Bundles Identified  : {len(evaluated_bundles)} ({strong_count} strong bundles, Lift >= 2.0x)",
        "-" * 92,
        f"{'#':<3} {'Supply Bundle':<40} {'Support':>8} {'Baseline':>9} {'Lift':>7}  {'Strength'}",
        "-" * 92,
    ]
    for idx, b in enumerate(evaluated_bundles, start=1):
        sku_str = " + ".join(b["skus"])
        if len(sku_str) > 38:
            sku_str = sku_str[:35] + "..."
        lines.append(
            f"{idx:<3} {sku_str:<40} {b['support']*100:>7.1f}% {b['expected_support']*100:>8.1f}% "
            f"{b['lift']:>6.2f}x  {b['strength']}"
        )
    lines.append("=" * 92)
    return "\n".join(lines)


def run_full_pipeline(
    n_procedures: int = 200,
    min_support: float = 0.10,
    max_size: int = 4,
    top_n: int = 15,
    seed: int = 42,
) -> dict[str, Any]:
    """Run all 5 milestones end-to-end and return structured results for CLI and Web UI."""
    procedures = milestone_1(n_procedures=n_procedures, seed=seed)
    itemsets = milestone_2(procedures, min_support=min_support, max_size=max_size)
    bundles = milestone_3(itemsets, min_size=2, top_n=top_n, total_procedures=len(procedures))
    evaluated = milestone_4(itemsets, bundles)
    raw_rules = mine_rules(itemsets, min_confidence=0.60)
    assoc_rules = [
        {
            "antecedent": sorted(ant),
            "consequent": sorted(cons),
            "support": round(float(sup), 4),
            "confidence": round(float(conf), 4),
            "lift": round(float(lift), 2),
        }
        for ant, cons, sup, conf, lift in raw_rules[:20]
    ]

    dept_counts: dict[str, int] = {}
    proc_type_counts: dict[str, int] = {}
    for p in procedures:
        dept_counts[p["department"]] = dept_counts.get(p["department"], 0) + 1
        proc_type_counts[p["procedure_type"]] = proc_type_counts.get(p["procedure_type"], 0) + 1

    return {
        "summary": {
            "total_procedures": len(procedures),
            "unique_skus": len({sku for p in procedures for sku in p["supplies"]}),
            "frequent_itemsets_total": len(itemsets),
            "bundles_identified": len(evaluated),
            "strong_bundles": sum(1 for b in evaluated if b["lift"] >= 2.0),
            "min_support": min_support,
            "max_size": max_size,
        },
        "departments": dept_counts,
        "procedure_types": proc_type_counts,
        "bundles": evaluated,
        "rules": assoc_rules,
        "catalog": SKU_CATALOG,
    }
