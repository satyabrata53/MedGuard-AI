from dataclasses import dataclass
from typing import Literal


ClinicalIntent = Literal["DRUG_QUERY", "REVIEW_QUERY", "CALCULATOR_QUERY", "GENERAL_QUERY"]


@dataclass(frozen=True)
class ClassifiedIntent:
    intent: ClinicalIntent
    confidence: float
    matched_terms: list[str]


class IntentClassifier:
    REVIEW_TERMS = (
        "review",
        "audit",
        "analyze current",
        "analyse current",
        "current medications",
        "dangerous interactions",
        "high-risk combination",
        "high risk combination",
        "high-risk combinations",
        "high risk combinations",
        "combinations already present",
        "already present",
        "present in this patient",
        "any interactions",
        "any high-risk",
        "check contraindications",
        "medication list",
        "full medication",
        "safest antibiotic",
        "antibiotic option",
        "antibiotic choice",
        "considering medications",
        "considering allergies",
        "considering kidney",
    )
    CALCULATOR_TERMS = (
        "stroke risk",
        "cha2ds2",
        "cha₂ds₂",
        "vasc",
        "calculate",
        "score",
        "egfr",
        "renal function",
        "kidney function",
        "anticoagulation",
        "anticoagulant",
    )
    DRUG_TERMS = (
        "prescribe",
        "add",
        "start",
        "give",
        "use",
        "safe",
        "dose",
        "treatment",
        "medicine",
        "medication",
        "drug",
        "tablet",
        "capsule",
    )

    def classify(self, query: str, proposed_drug: str | None = None) -> ClassifiedIntent:
        text = (query or "").lower()
        if proposed_drug:
            return ClassifiedIntent(intent="DRUG_QUERY", confidence=1.0, matched_terms=["proposed_drug"])
        if self._looks_like_bare_drug_fragment(text):
            return ClassifiedIntent(intent="DRUG_QUERY", confidence=0.7, matched_terms=["bare_drug_fragment"])

        review_matches = self._matches(text, self.REVIEW_TERMS)
        calculator_matches = self._matches(text, self.CALCULATOR_TERMS)
        drug_matches = self._matches(text, self.DRUG_TERMS)

        if review_matches:
            return ClassifiedIntent(intent="REVIEW_QUERY", confidence=self._confidence(review_matches), matched_terms=review_matches)
        if calculator_matches and not drug_matches:
            return ClassifiedIntent(intent="CALCULATOR_QUERY", confidence=self._confidence(calculator_matches), matched_terms=calculator_matches)
        if drug_matches:
            return ClassifiedIntent(intent="DRUG_QUERY", confidence=self._confidence(drug_matches), matched_terms=drug_matches)
        return ClassifiedIntent(intent="GENERAL_QUERY", confidence=0.65, matched_terms=[])

    def _matches(self, text: str, terms: tuple[str, ...]) -> list[str]:
        return [term for term in terms if term in text]

    def _confidence(self, matches: list[str]) -> float:
        return min(0.98, 0.72 + (0.08 * len(matches)))

    def _looks_like_bare_drug_fragment(self, text: str) -> bool:
        compact = text.strip().replace("-", "").replace(" ", "")
        return bool(compact.isalpha() and 3 <= len(compact) <= 24 and len(text.strip().split()) <= 2)
