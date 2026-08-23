"""Graph RAG (Bonus): Entity-Relation Knowledge Graph Traversal."""
from typing import Any, Dict, List, Set


class PropertyPolicyKnowledgeGraph:
    def __init__(self):
        # Nodes: Entities (Statute, Clause, Property, Role)
        self.entities = {
            "Law 4/1996": {"type": "Statute", "desc": "Egyptian Tenancy Law"},
            "Section 4.2b": {"type": "Clause", "desc": "Alexandria Early Termination"},
            "Section 7.3": {"type": "Clause", "desc": "Commercial Subleasing"},
            "Alexandria Properties": {"type": "PropertyRegion", "desc": "Mediterranean Coastal Portfolio"},
            "Executive Admin": {"type": "Role", "desc": "High-Value Sign-off Authority"},
            "Emergency SLA 8.1c": {"type": "Protocol", "desc": "2-Hour Leak Containment"},
        }
        # Edges: Relationships
        self.edges = [
            ("Section 7.3", "GOVERNED_BY", "Law 4/1996"),
            ("Section 7.3", "REQUIRES_APPROVAL_FROM", "Executive Admin"),
            ("Section 4.2b", "APPLIES_TO", "Alexandria Properties"),
            ("Emergency SLA 8.1c", "PRECEDES_PENALTY", "Section 8.2"),
        ]

    def traverse_relations(self, entity_name: str) -> List[Dict[str, str]]:
        results = []
        for src, rel, dst in self.edges:
            if entity_name.lower() in src.lower() or entity_name.lower() in dst.lower():
                results.append({"source": src, "relation": rel, "target": dst})
        return results

    def query_graph(self, query: str) -> Dict[str, Any]:
        traversed = []
        for ent in self.entities:
            if ent.lower() in query.lower():
                traversed.extend(self.traverse_relations(ent))
        return {"matched_entities": list(set([t["source"] for t in traversed] + [t["target"] for t in traversed])), "paths": traversed}
