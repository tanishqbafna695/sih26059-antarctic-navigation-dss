"""Phase 14 — Explanation Engine (FR-27, FR-28).

Deterministic template-based explanations built ONLY from recorded numbers
(comparison rows + recommendation deltas + vessel limits). No LLM, no
invented causes: every sentence traces to a metric delta, a vessel limit, a
confidence report, or a stated trigger (for route-change explanations).
"""

from .explainer import explain_change, explain_recommendation

__all__ = [
    "explain_recommendation",
    "explain_change",
]
