import math
import re
from typing import List, Dict, Any, Optional

def tokenize(text: str) -> List[str]:
    """Tokenize and normalize text into lowercase terms."""
    return re.findall(r'\w+', text.lower())

class BM25Store:
    """Pure-Python BM25 & Keyword Search engine with zero external dependencies."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: List[Dict[str, Any]] = []  # List of {"id": str, "payload": str, "metadata": dict}
        self.doc_tokens: List[List[str]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0

    def upsert(self, payload: str, metadata: Optional[Dict[str, Any]] = None, doc_id: Optional[str] = None):
        """Add or update a document chunk in the search store."""
        meta = metadata or {}
        document_id = doc_id or f"doc_{len(self.documents) + 1}"
        tokens = tokenize(payload)

        doc_entry = {
            "id": document_id,
            "payload": payload,
            "metadata": meta
        }
        self.documents.append(doc_entry)
        self.doc_tokens.append(tokens)
        self.doc_lengths.append(len(tokens))
        self._recalculate_stats()

    def _recalculate_stats(self):
        if self.doc_lengths:
            self.avg_doc_len = sum(self.doc_lengths) / len(self.doc_lengths)
        else:
            self.avg_doc_len = 0.0

    def query(self, query_text: str, top_k: int = 3, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search stored documents using BM25 ranking algorithm with optional metadata filter."""
        query_terms = tokenize(query_text)
        if not query_terms or not self.documents:
            return []

        N = len(self.documents)
        scores = [0.0] * N

        for term in query_terms:
            # Calculate document frequency df_t
            df = sum(1 for tokens in self.doc_tokens if term in tokens)
            if df == 0:
                continue

            # Inverse Document Frequency (IDF) with standard smoothing
            idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)

            for i, tokens in enumerate(self.doc_tokens):
                # Apply metadata filter if specified
                if filter_metadata:
                    match = all(
                        self.documents[i]["metadata"].get(k) == v
                        for k, v in filter_metadata.items()
                    )
                    if not match:
                        continue

                tf = tokens.count(term)
                if tf > 0:
                    doc_len = self.doc_lengths[i]
                    denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / (self.avg_doc_len or 1.0)))
                    numerator = tf * (self.k1 + 1.0)
                    scores[i] += idf * (numerator / denom)

        # Pair scores with documents and sort descending
        scored_docs = [
            {
                "id": self.documents[i]["id"],
                "payload": self.documents[i]["payload"],
                "metadata": self.documents[i]["metadata"],
                "score": round(score, 4)
            }
            for i, score in enumerate(scores)
            if score > 0.0
        ]
        scored_docs.sort(key=lambda x: x["score"], reverse=True)

        # Fallback substring match if BM25 score is 0 due to non-exact word forms
        if not scored_docs and filter_metadata:
            for doc in self.documents:
                match = all(doc["metadata"].get(k) == v for k, v in filter_metadata.items())
                if match and any(term in doc["payload"].lower() for term in query_terms):
                    scored_docs.append({
                        "id": doc["id"],
                        "payload": doc["payload"],
                        "metadata": doc["metadata"],
                        "score": 0.5
                    })

        return scored_docs[:top_k]

# Global knowledge store instance for Cornerstone Realty Group
knowledge_store = BM25Store()

def seed_cornerstone_knowledge_base():
    """Seed the knowledge store with structured regulatory policies, lease rules, and emergency procedures."""
    if len(knowledge_store.documents) > 0:
        return

    documents = [
        {
            "payload": "Cornerstone Lease Termination Policy (Section 4.1): Tenants must provide a 60-day written notice for early lease termination. A penalty fee equal to 2 months rent applies unless termination is due to documented structural landlord default.",
            "metadata": {"entity_id": "policy_lease_terms", "role_required": "any", "category": "policy"}
        },
        {
            "payload": "Security Deposit Refund Procedure (Section 5.3): Security deposits are fully refundable within 14 business days post move-out inspection. Deductions require itemized repair receipts provided to the tenant.",
            "metadata": {"entity_id": "policy_lease_terms", "role_required": "any", "category": "policy"}
        },
        {
            "payload": "Residential By-Laws & Quiet Hours (Section 8.2): Quiet hours are strictly enforced between 10:00 PM and 7:00 AM daily. Pets under 15 kg are permitted with prior manager approval.",
            "metadata": {"entity_id": "building_bylaws", "role_required": "any", "category": "rules"}
        },
        {
            "payload": "Confidential Commercial Escalation Clause (Executive Annex C): Commercial leases over 50,000 EGP/month carry an annual 7.5% rent escalation clause. Rent waivers >100,000 EGP require written sign-off from Executive Admin.",
            "metadata": {"entity_id": "executive_rules", "role_required": "executive_admin", "category": "confidential"}
        },
        {
            "payload": "Property Manager Emergency Protocol: Water pipe bursts and main electrical outages require dispatching a certified technician within 2 hours of ticket submission.",
            "metadata": {"entity_id": "maintenance_protocol", "role_required": "property_manager", "category": "procedure"}
        }
    ]

    for doc in documents:
        knowledge_store.upsert(payload=doc["payload"], metadata=doc["metadata"])

seed_cornerstone_knowledge_base()
