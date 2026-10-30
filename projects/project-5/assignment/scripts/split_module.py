
# --- Project 5, Step 4: create the train (~80%) and valid (~20%) ttl files 
# Input:  src/cco-module.ttl
# Output: src/train.ttl   the whole module MINUS the held-out 'subClassOf' axioms
#         src/valid.ttl   all declarations PLUS the held-out 'subClassOf' axioms
#
# Sections 2 and 3 reuse documentation/embedding_example.py
# (connectivity-preserving split). Lines marked "CHANGED" differ from it.
#'
#   python scripts/split_module.py

import random, rdflib, networkx as nx
from pathlib import Path
from rdflib import URIRef
from rdflib.namespace import RDF, RDFS, OWL

random.seed(42)                                     # same as embedding_example.py
#random.seed(42); np.random.seed(42)


BASE = Path(__file__).resolve().parent.parent       # the assignment folder
TTL_IN = BASE / "src" / "cco-module.ttl"
TRAIN_OUT = BASE / "src" / "train.ttl"
VALID_OUT = BASE / "src" / "valid.ttl"

# Load cco-module - use my local file
g = rdflib.Graph(); # create the empty graph
g.parse(TTL_IN, format="turtle") #load the empty graph with the coo module data

# Parse and extract classes + rdfs:subClassOf edges   same as embedding_example.py
def iri(u):
    return str(u) if isinstance(u, URIRef) else None 

classes = set() #Unique Named Classes
for s, p, o in g.triples((None, RDF.type, OWL.Class)):  
    u = iri(s)
    if u: classes.add(u)

edges = []
for s, p, o in g.triples((None, RDFS.subClassOf, None)):
    u, v = iri(s), iri(o)
    if u and v:
        classes.add(u); classes.add(v)
        edges.append((u, v))  #create the edge as a pair

edges = [(u, v) for (u, v) in edges if u in classes and v in classes] #only edges whose ends are BOTH in classes.
edges = sorted(set(edges))   #remove duplicates and put in alphabetical order sort so the seed gives the same split every run
print(f"Classes: {len(classes):,}  SubClassOf edges: {len(edges):,}")  #print the result set

# Connectivity-preserving split
#   1st pass  80/20 (train/valid) instead of 80/10/10; no test set in Project 5
UG_full = nx.Graph(); UG_full.add_nodes_from(classes); UG_full.add_edges_from(edges) #UG - undirected graph
target_train = int(0.8 * len(edges))
target_valid = len(edges) - target_train

def can_remove_edge(edge_list, a, b):               # same as embedding_example.py
    deg = {}
    for x, y in edge_list:
        deg[x] = deg.get(x, 0) + 1
        deg[y] = deg.get(y, 0) + 1
    return deg.get(a,0) > 1 and deg.get(b,0) > 1

train_set = set(edges)
deg_full = dict(UG_full.degree())
candidates = [(u,v) for (u,v) in edges if deg_full.get(u,0) >= 2 and deg_full.get(v,0) >= 2]
random.shuffle(candidates)

valid_edges = []
for (u,v) in candidates:
    if len(valid_edges) < target_valid and (u,v) in train_set:
        tmp = list(train_set); tmp.remove((u,v))
        if can_remove_edge(tmp, u, v): train_set.remove((u,v)); valid_edges.append((u,v))
    if len(valid_edges) >= target_valid:
        break
first_pass = len(valid_edges)

# 2nd pass, only if the first pass is short.
#     Looser rule: both classes keep at least ONE edge in train (still connected).
def keeps_one_edge(edge_list, a, b):
    deg = {}
    for x, y in edge_list:
        deg[x] = deg.get(x, 0) + 1
        deg[y] = deg.get(y, 0) + 1
    return deg.get(a, 0) >= 1 and deg.get(b, 0) >= 1

if len(valid_edges) < target_valid:
    rest = sorted(train_set)
    random.shuffle(rest)
    for (u, v) in rest:
        if len(valid_edges) >= target_valid:
            break
        tmp = list(train_set)
        tmp.remove((u, v))
        if keeps_one_edge(tmp, u, v):
            train_set.remove((u, v))
            valid_edges.append((u, v))

train_edges = sorted(train_set)
valid_edges = sorted(valid_edges)
print(f"Split sizes: train={len(train_edges)}, valid={len(valid_edges)}")
print(f"  (first pass {first_pass}, second pass {len(valid_edges) - first_pass})")

# write the split as two Turtle files for MOWL

#  BFO parents are used in the module but not declared there.
#     Make a declaration (Class rdf:type owl:Class) for each one.
missing_declarations = []
for c in sorted(classes):
    triple = (URIRef(c), RDF.type, OWL.Class)
    if triple not in g:
        missing_declarations.append(triple)

#  train.ttl = the whole module, minus the held-out edges,
#     plus the missing BFO declarations
train_g = rdflib.Graph()
train_g.parse(TTL_IN, format="turtle")          # a fresh copy of the module
for (u, v) in valid_edges:
    train_g.remove((URIRef(u), RDFS.subClassOf, URIRef(v)))
for triple in missing_declarations:
    train_g.add(triple)

#  valid.ttl = every declaration (rdf:type triple for a named entity),
#     plus the missing BFO declarations, plus the held-out edges
valid_g = rdflib.Graph()
for prefix, namespace in g.namespaces():        # keep the same prefixes (cco:, obo: ...)
    valid_g.bind(prefix, namespace)
for s, p, o in g.triples((None, RDF.type, None)):
    if isinstance(s, URIRef):                   # skip blank nodes (restrictions)
        valid_g.add((s, p, o))
for triple in missing_declarations:
    valid_g.add(triple)
for (u, v) in valid_edges:
    valid_g.add((URIRef(u), RDFS.subClassOf, URIRef(v)))

train_g.serialize(TRAIN_OUT, format="turtle")
valid_g.serialize(VALID_OUT, format="turtle")

#  simple checks to show in your PR

#  No held-out edge may still be in train
overlap = 0
for (u, v) in valid_edges:
    if (URIRef(u), RDFS.subClassOf, URIRef(v)) in train_g:
        overlap += 1
print("Check - held-out edges still in train (should be 0):", overlap)

#  Train + valid should add up to all edges
print("Check - train + valid = all edges:", len(train_edges) + len(valid_edges) == len(edges))

#  Every class in a held-out edge must still have an edge in train
train_classes = set()
for (u, v) in train_edges:
    train_classes.add(u)
    train_classes.add(v)
isolated = 0
for (u, v) in valid_edges:
    if u not in train_classes or v not in train_classes:
        isolated += 1
print("Check - held-out edges with a class missing from train (should be 0):", isolated)

#  Both files should declare the same number of named classes
train_class_count = 0
for c in set(train_g.subjects(RDF.type, OWL.Class)):
    if isinstance(c, URIRef):                   # count named classes only
        train_class_count += 1
valid_class_count = 0
for c in set(valid_g.subjects(RDF.type, OWL.Class)):
    if isinstance(c, URIRef):
        valid_class_count += 1
print(f"Check - classes declared: train={train_class_count}, valid={valid_class_count}")

print(f"Saved: {TRAIN_OUT}")
print(f"Saved: {VALID_OUT}")