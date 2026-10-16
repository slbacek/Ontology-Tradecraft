Project 5 notes

MOWL - machine learning over OWL.
1. pick a CCO ntology module
    extract the definitions (IRI,Label and definition)

2. Use LLM to normalize and enrich the definitions
    standardized, canonical format (NEED TO DEFINE)
    ambuiguity is removed, abbreviation spelled out, terminology is aligned to CCO Style (WHAT IS CCO STYLE?)
3. take enriched definition and create OWL 2 EL compliant candidacte axiom. https://www.w3.org/TR/owl2-profiles/#OWL_2_EL
4. create a train and valid ttl file from CCO_MOdule  keeping ALL classes and properites
5. write a script to train an embedding mdeol, evaluate and record results.  use cosine similarity for helf out sub/super class paris (RESEACRH THIS?
6. score each super/sub pair by MOWL cosine similarity.  query an LLM to rate semantic plausibiloty.  combine scores to create a weighted avaer and return list of axioms meeting threshold.
take was waht created and accepted and merge with CCO-module to an augment ontology and use robot and use 'elk' reasoner. (Validate ontology quality and consistency using ROBOT, ELK, and OOPS!.) WHAT IS OOPS? OWL EL
create a script to execute the full pipeline (above)     and the output will be a report to summarize (mean_cos, chosen T, accepted axiom count, LLM contribution rate and consistency status)
    Are there standards for the above metrics?

    Grading: mean_cos ≥ 0.70, ontology consistent, and at least several new axioms added automatically and must run under one command.

    Required components:
    # Core
mowl==1.0.2
JPype1==1.6.0
torch>=2.2,<3
rdflib==7.0.0
pandas==2.2.2







Delvierables:
- 'data/definitions.csv` — Extracted SKOS definitions (columns: IRI, label, definition).
- `data/definitions_enriched.csv` — LLM-normalized/enriched definitions used for axiom generation.
- `generated/candidate_el.ttl` — OWL 2 EL candidate axioms produced via LLM + pattern prompts.
- `generated/accepted_el.ttl` — Candidates retained after hybrid MOWL cosine + LLM plausibility filtering.
- `reports/mowl_metrics.json` — Training/evaluation metrics (mean cosine, selected τ, and hybrid settings).
- `src/cco-module.ttl` — Original selected CCO module (input ontology).
- `src/train.ttl` — Training split of the ontology (≈ 80% of axioms).
- `src/valid.ttl` — Validation split of the ontology (≈ 20% of axioms).
- `src/module_augmented.ttl` — Final ontology after merging accepted axioms and reasoning with ELK.
- `scripts/extract_definitions.py` — Extracts SKOS definitions into `data/definitions.csv`.
- `scripts/preprocess_definitions_llm.py` — Normalizes/enriches definitions with an LLM.
- `scripts/generate_candidates_llm.py` — Generates EL-compliant candidate axioms from enriched definitions.
- `scripts/train_mowl.py` — Trains ELEmbeddings on `src/train.ttl` and evaluates on `src/valid.ttl`.
- `scripts/filter_candidates_hybrid.py` — Combines MOWL cosine and LLM plausibility to keep axioms.
- `scripts/run_all.py` — One-command driver that executes the entire pipeline end-to-end.       