"""Unit tests for all 5 milestones of Supply Co-usage Insight."""
import json

from app.cli import main
from app.core import (
    SKU_CATALOG,
    milestone_1,
    milestone_2,
    milestone_3,
    milestone_4,
    milestone_5,
    run_full_pipeline,
)


# Milestone 1: Create mock medical procedure data, where each procedure lists used supply SKUs.
def test_milestone_1():
    procedures = milestone_1(n_procedures=100, seed=42)
    assert len(procedures) == 100
    for proc in procedures:
        assert "procedure_id" in proc
        assert "procedure_type" in proc
        assert "department" in proc
        assert isinstance(proc["supplies"], list)
        assert len(proc["supplies"]) >= 4
        assert all(sku in SKU_CATALOG for sku in proc["supplies"])
    # Deterministic with the same seed
    assert procedures == milestone_1(n_procedures=100, seed=42)


# Milestone 2: Implement frequent itemset mining (e.g., using thilimarketbasket).
def test_milestone_2():
    procedures = milestone_1(n_procedures=200, seed=42)
    itemsets = milestone_2(procedures, min_support=0.15, max_size=3)
    assert isinstance(itemsets, dict)
    assert len(itemsets) > 0
    for skus, support in itemsets.items():
        assert isinstance(skus, frozenset)
        assert 1 <= len(skus) <= 3
        assert 0.15 <= support <= 1.0


# Milestone 3: Analyze and display the most frequent co-occurring supply itemsets.
def test_milestone_3():
    procedures = milestone_1(n_procedures=200, seed=42)
    itemsets = milestone_2(procedures, min_support=0.10, max_size=4)
    bundles = milestone_3(itemsets, min_size=2, top_n=10, total_procedures=len(procedures))
    assert 0 < len(bundles) <= 10
    assert all(b["size"] >= 2 for b in bundles)
    supports = [b["support"] for b in bundles]
    assert supports == sorted(supports, reverse=True)


# Milestone 4: Compare the mined itemsets against simple baseline expectations.
def test_milestone_4():
    procedures = milestone_1(n_procedures=200, seed=42)
    itemsets = milestone_2(procedures, min_support=0.10, max_size=4)
    bundles = milestone_3(itemsets, min_size=2, top_n=10, total_procedures=len(procedures))
    evaluated = milestone_4(itemsets, bundles)
    assert len(evaluated) == len(bundles)
    for b in evaluated:
        assert "expected_support" in b
        assert "lift" in b
        assert "excess_support" in b
        assert "strength" in b
        assert "recommendation" in b
        assert b["expected_support"] > 0
        assert b["lift"] > 0
    # Strong co-occurring hospital bundles should exceed naive independence baseline (lift > 1)
    assert any(b["lift"] >= 1.5 for b in evaluated)


# Milestone 5: Generate a report of identified supply bundles.
def test_milestone_5():
    procedures = milestone_1(n_procedures=200, seed=42)
    itemsets = milestone_2(procedures, min_support=0.10, max_size=4)
    bundles = milestone_3(itemsets, min_size=2, top_n=8, total_procedures=len(procedures))
    evaluated = milestone_4(itemsets, bundles)

    text_report = milestone_5(evaluated, procedures=procedures, output_format="text")
    assert "SUPPLY CO-USAGE INSIGHT REPORT" in text_report
    assert "Procedures Analyzed : 200" in text_report

    md_report = milestone_5(evaluated, procedures=procedures, output_format="markdown")
    assert "# Supply Co-usage Insight Report" in md_report
    assert "| Rank |" in md_report

    json_report = milestone_5(evaluated, procedures=procedures, output_format="json")
    parsed = json.loads(json_report)
    assert parsed["summary"]["total_procedures"] == 200
    assert len(parsed["bundles"]) == len(evaluated)


def test_full_pipeline_and_cli_analyze(capsys):
    result = run_full_pipeline(n_procedures=120, min_support=0.12, max_size=3, top_n=8)
    assert result["summary"]["total_procedures"] == 120
    assert len(result["bundles"]) > 0
    assert len(result["rules"]) > 0

    main(["analyze", "--procedures", "120", "--top", "5", "--format", "text"])
    out = capsys.readouterr().out
    assert "SUPPLY CO-USAGE INSIGHT REPORT" in out
