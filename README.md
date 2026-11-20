# Supply Co-usage Insight

[![Built with askThili](https://ask.thili.ai/api/v1/public/projects/f4z6xzv3dx/badge.svg)](https://ask.thili.ai/b/f4z6xzv3dx)

This project, "Supply Co-usage Insight," helps hospital administrators optimize medical supply management. By analyzing which supplies are frequently used together across procedures in a healthcare setting, it aims to improve stock placement and procurement efficiency.

## What you are building

**Goal.** You will build a system that analyzes medical procedure data to identify frequently co-occurring medical supplies, helping hospital administrators optimize stock placement and procurement.

**Done when.** The project is complete when it successfully identifies strong co-occurring medical supply sets, outputting a list of frequent itemsets with their support, and presents these as identified supply bundles.

## Milestones

Tick these off as you go, and commit after each one.

- [ ] **1. Create mock medical procedure data, where each procedure lists used supply SKUs.**  
      Hint: Use Python data structures like lists of lists or dictionaries to represent procedures and their associated supply SKUs.
- [ ] **2. Implement frequent itemset mining (e.g., using thilimarketbasket).**  
      Hint: Apply the `lfretail-lfmarketbasket` technique to your mock procedure data.
- [ ] **3. Analyze and display the most frequent co-occurring supply itemsets.**  
      Hint: Filter and sort the results from the mining algorithm to highlight the most significant itemsets.
- [ ] **4. Compare the mined itemsets against simple baseline expectations.**  
      Hint: Consider a naive baseline, such as comparing against individual supply usage frequencies or random combinations.
- [ ] **5. Generate a report of identified supply bundles.**  
      Hint: Format your findings clearly, perhaps as a table or bulleted list, showing itemsets and their support.

## Run it

You need Python 3.12 and git.

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then choose a model; see the comments inside
python -m app.cli hello
pytest
```

Your work goes in `app/core.py` (one stub per milestone) and `tests/test_core.py`. The first tests pass already; they
check the plumbing.

## Settings and secrets

Model settings live in `.env`, which is ignored by git. **Never commit `.env` or paste a key into code.** If a key ever
reaches GitHub, treat it as leaked and make a new one.

## Stretch ideas

- (none)
