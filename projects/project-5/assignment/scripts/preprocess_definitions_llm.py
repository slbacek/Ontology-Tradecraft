# --- Project 5, Step 2: normalize definitions with an LLM ---
# Input:  data/definitions.csv  (IRI, label, definition from Step 1)
#         src/cco-module.ttl    (to look up each class's parent)
# Output: data/definitions_enriched.csv
#
# Each class definition is rewritten as "A <label> is a <parent> that <...>."
# Non-class rows (object properties) are copied through unchanged.
#
# Run from the assignment folder:
#   python scripts/preprocess_definitions_llm.py       (all classes)
#   python scripts/preprocess_definitions_llm.py 5     (test: first 5 classes)

import sys
from pathlib import Path
import pandas as pd
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, RDFS, OWL
from llm_helper import ask_llm, MODEL

BASE = Path(__file__).resolve().parent.parent      # the assignment folder
CSV_IN = BASE / "data" / "definitions.csv"
TTL_PATH = BASE / "src" / "cco-module.ttl"
CSV_OUT = BASE / "data" / "definitions_enriched.csv"

# Optional test limit from the command line, e.g. "5"
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else None

# 1) Load the definitions and the module
df = pd.read_csv(CSV_IN)
g = Graph()
g.parse(TTL_PATH, format="turtle")
print(f"Definitions read: {len(df)}")

# 2) Labels, so we can name each class's parent
label_map = {}
for s, o in g.subject_objects(RDFS.label):
    label_map[str(s)] = str(o)

# BFO parents the module uses but does not label itself
label_map["http://purl.obolibrary.org/obo/BFO_0000030"] = "object"
label_map["http://purl.obolibrary.org/obo/BFO_0000019"] = "quality"
label_map["http://purl.obolibrary.org/obo/BFO_0000031"] = "generically dependent continuant"

# 3) What we ask the LLM (the same for every class)
INSTRUCTIONS = """You are an ontology editor for the Common Core Ontologies (CCO), which extend BFO.
Rewrite the given class definition into ONE sentence of the form:
    "A <label> is a <genus> that <differentia>."
Rules:
- Use the supplied parent label as the genus, word for word.
- Keep the original meaning. Do not add facts that are not in the original definition.
- Expand all abbreviations and acronyms.
- Remove ambiguity: replace vague words with precise CCO/BFO terms.
- CCO style: lower-case class names, present tense, singular, no examples, do not use the label to define itself.
- Phrase the differentia with relations that could become OWL restrictions,
  e.g. "is about", "is carrier of", "inheres in", "has participant", "is part of", "designates".
Return JSON only."""

SCHEMA = {
    "type": "object",
    "properties": {
        "enriched_definition": {"type": "string"},
        "genus": {"type": "string"},
        "differentia": {"type": "string"},
    },
    "required": ["enriched_definition", "genus", "differentia"],
    "additionalProperties": False,
}

# 4) Rewrite each class definition
rows = []
sent = 0
for _, row in df.iterrows():
    iri = row["IRI"]
    is_class = (URIRef(iri), RDF.type, OWL.Class) in g

    # named parents only (skip restriction blank nodes)
    parents = [str(p) for p in g.objects(URIRef(iri), RDFS.subClassOf) if isinstance(p, URIRef)]
    parent_label = label_map.get(parents[0], parents[0]) if parents else ""

   ### enriched = row["definition"]           # default: unchanged
    enriched = ""                          # default: Blank (not rewritten)
    genus = ""
    differentia = ""

    if is_class and parents and (LIMIT is None or sent < LIMIT):
        prompt = (
            f"Label: {row['label']}\n"
            f"Parent label (use as genus): {parent_label}\n"
            f"Original definition: {row['definition']}"
        )
        answer = ask_llm(INSTRUCTIONS, prompt, SCHEMA)
        enriched = answer["enriched_definition"]
        genus = answer["genus"]
        differentia = answer["differentia"]
        sent += 1
        print(f"  [{sent}] {row['label']}: {enriched}")

    rows.append({
        "IRI": iri,
        "label": row["label"],
        "definition": row["definition"],
        "entity_type": "class" if is_class else "other",
        "parent_label": parent_label,
        "enriched_definition": enriched,
        "genus": genus,
        "differentia": differentia,
    })

# 5) Save
pd.DataFrame(rows).to_csv(CSV_OUT, index=False)
print(f"Classes rewritten: {sent}   Rows written: {len(rows)}   Model: {MODEL}")
print(f"Saved: {CSV_OUT}")