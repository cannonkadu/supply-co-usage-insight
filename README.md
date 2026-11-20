# Supply Co-usage Insight

[![Built with askThili](https://ask.thili.ai/api/v1/public/projects/f4z6xzv3dx/badge.svg)](https://ask.thili.ai/b/f4z6xzv3dx)

**Supply Co-usage Insight** helps hospital administrators optimize medical supply management. By analyzing which medical supply SKUs are frequently used together across clinical procedures, it uncovers high-lift supply bundles to improve sterile cart stock placement, pre-kitting, and bulk procurement efficiency.

## Features

- **Realistic Clinical Procedure Simulator (Milestone 1):** Generates deterministic hospital procedure logs across 6 procedure types (IV Cannulation, Blood Draw & Diagnostics, Wound Suturing, Central Line Insertion, Airway Intubation, Minor Surgical Biopsy) and 20 cataloged medical supply SKUs with unit costs and storage zones.
- **Frequent Itemset & Association Rule Mining (Milestone 2):** Uses `thilimarketbasket.mine` (bitset-accelerated Apriori) to mine frequent co-occurring supply itemsets and high-confidence association rules.
- **Bundle Ranking & Enrichment (Milestone 3):** Filters multi-SKU itemsets, enriches them with human-readable supply names, estimated bundle unit costs, and storage zones, and ranks them by support.
- **Naive Independence Baseline Comparison (Milestone 4):** Compares observed bundle support against expected support under independence (`P(s1) * P(s2) * ... * P(sk)`) to compute **Lift**, **Excess Support**, strength tiers (`Strong Bundle`, `Moderate Co-usage`, `Baseline / Ubiquitous`), and actionable logistics recommendations.
- **Multi-Format Reporting & Interactive Web Dashboard (Milestone 5):** Outputs clean CLI tables, Markdown reports, JSON exports, and a zero-dependency local interactive Web Dashboard (`python -m app.cli serve`).

## Milestones

- [x] **1. Create mock medical procedure data, where each procedure lists used supply SKUs.**
- [x] **2. Implement frequent itemset mining (e.g., using thilimarketbasket).**
- [x] **3. Analyze and display the most frequent co-occurring supply itemsets.**
- [x] **4. Compare the mined itemsets against simple baseline expectations.**
- [x] **5. Generate a report of identified supply bundles.**

## Tech Stack

- **Language:** Python 3.12+
- **Mining Engine:** [`thilimarketbasket`](https://github.com/thili-ai/thilimarketbasket), `numpy`, `pandas`
- **CLI & Web UI:** Python `argparse` + built-in `http.server` with responsive HTML/CSS/JS dashboard
- **Storage & LLM Plumbing:** Local JSON `Store` (`app/storage.py`), OpenAI-compatible `httpx` client (`app/llm.py`)
- **Testing & CI:** `pytest` + GitHub Actions (`.github/workflows/ci.yml`)

## Quick Start

```bash
python -m venv .venv
# Linux / macOS:
source .venv/bin/activate
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 1. Verify setup
```bash
python -m app.cli hello
```

### 2. Run the Co-usage Analysis CLI
```bash
# Formatted CLI table
python -m app.cli analyze

# Custom parameters & Markdown / JSON output
python -m app.cli analyze --procedures 300 --min-support 0.10 --top 15 --format markdown
python -m app.cli analyze --format json --output report.json --save
```

### 3. Launch the Interactive Web Dashboard
```bash
python -m app.cli serve --port 8000
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser to interactively tune support thresholds, inspect supply bundles vs. baseline lift, view association rules, and export JSON reports.

### 4. Run Tests
```bash
pytest -v
```

## Settings and Secrets

Optional LLM settings live in `.env` (copied from `.env.example`), which is ignored by git. **Never commit `.env` or API keys.**
