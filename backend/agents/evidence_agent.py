"""
evidence_agent.py
─────────────────
Location : backend/agents/evidence_agent.py
Purpose  : Agent #3 — searches ChromaDB (pre-indexed RBI/AML PDFs) to
           retrieve supporting regulatory evidence for the fraud finding.

Connects to: rag_pipeline.py (ChromaDB queries), investigation_agent.py
             (receives risk level + reasons), api.py
"""

from loguru import logger
from backend.rag.rag_pipeline import rag_query

# Keywords mapped to regulation categories for targeted retrieval
RISK_QUERY_MAP = {
    "CRITICAL": [
        "suspicious transaction reporting obligation PMLA",
        "immediate STR filing RBI guidelines large cash transfer",
        "AML red flags immediate action",
    ],
    "HIGH": [
        "suspicious transaction report RBI AML KYC",
        "unusual transaction pattern monitoring",
        "high value transaction reporting threshold India",
    ],
    "MEDIUM": [
        "enhanced due diligence KYC RBI",
        "transaction monitoring alert investigation",
    ],
    "LOW": [
        "standard KYC verification RBI guideline",
        "normal transaction monitoring procedure",
    ],
}


class EvidenceAgent:
    name = "EvidenceAgent"

    def run(self, investigation_result: dict, top_k: int = 3) -> dict:
        """
        Parameters
        ----------
        investigation_result : dict
            Output from InvestigationAgent.run()
        top_k : int
            Number of evidence passages to retrieve per query

        Returns
        -------
        dict with keys:
            evidence_passages (list of dicts), sources, agent
        """
        risk_level = investigation_result.get("risk_level", "MEDIUM")
        narrative  = investigation_result.get("narrative", "")

        logger.info(f"[{self.name}] Retrieving evidence for risk level: {risk_level}")

        queries  = RISK_QUERY_MAP.get(risk_level, RISK_QUERY_MAP["MEDIUM"])
        # Also add a semantic query from the narrative itself
        queries.append(narrative[:200])

        all_passages = []
        seen_ids     = set()

        for query in queries:
            results = rag_query(query, top_k=top_k)
            for r in results:
                doc_id = r.get("id")
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_passages.append(r)

        # Sort by relevance score (higher = more relevant)
        all_passages.sort(key=lambda x: x.get("score", 0), reverse=True)
        top_passages = all_passages[:5]  # cap at 5 total

        sources = list({p.get("source", "Unknown") for p in top_passages})

        logger.info(
            f"[{self.name}] Retrieved {len(top_passages)} unique evidence passages "
            f"from {len(sources)} sources."
        )

        return {
            "evidence_passages": top_passages,
            "sources":           sources,
            "agent":             self.name,
        }


evidence_agent = EvidenceAgent()
