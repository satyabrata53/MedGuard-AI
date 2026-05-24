from difflib import SequenceMatcher

from app.llm.gemini_client import GeminiClient
from app.models.schemas import ResolvedDrug
from app.utils.normalize import normalize_drug_name


class EntityResolver:
    def __init__(self, drugs: list[dict], aliases: list[dict]) -> None:
        self.drugs_by_norm = {d["generic_name_normalized"]: d for d in drugs}
        self.display_by_norm = {d["generic_name_normalized"]: d["generic_name"] for d in drugs}
        self.aliases = {normalize_drug_name(a["alias"]): normalize_drug_name(a["actual_drug"]) for a in aliases}
        self.known_terms = list(self.drugs_by_norm.keys()) + list(self.aliases.keys())
        self.llm = GeminiClient()

    def resolve(self, text: str) -> ResolvedDrug:
        raw = (text or "").strip()
        normalized = normalize_drug_name(raw)

        exact = self._exact_or_alias(normalized)
        if exact:
            return exact

        extracted = self._extract_candidate(raw)
        if extracted and extracted != normalized:
            exact = self._exact_or_alias(extracted)
            if exact:
                exact.input = raw
                exact.normalized_input = extracted
                return exact
            normalized = extracted

        match = self._best_match(normalized)
        if match:
            candidate, score = match
            actual_norm = self.aliases.get(candidate, candidate)
            confidence = round(score, 2)
            candidate_names = self._candidate_names(normalized, minimum_score=0.55)
            if score >= 0.72 and actual_norm in self.drugs_by_norm and self.display_by_norm[actual_norm] not in candidate_names:
                candidate_names.insert(0, self.display_by_norm[actual_norm])
            candidate_names = self._expand_candidates_by_class(candidate_names)
            if score >= 0.72 or candidate_names:
                clarification = self._safe_clarification_message(raw, candidate_names)
                return ResolvedDrug(
                    input=raw,
                    normalized_input=normalized,
                    status="needs_clarification",
                    confidence=confidence,
                    match_type="candidate_confirmation_required",
                    candidates=candidate_names,
                    message=clarification or self._clarification_message(candidate_names),
                    confidence_explanation="The input is not an exact validated drug name. Confirm the intended medication before deterministic safety checks execute.",
                )

        return ResolvedDrug(
            input=raw,
            normalized_input=normalized,
            status="drug_not_found",
            confidence=0,
            match_type="none",
            candidates=self._candidate_names(normalized, minimum_score=0.45)[:5],
            message="Drug not found in validated clinical database. Manual pharmacist review recommended.",
            confidence_explanation="No exact, alias, or conservative fuzzy match reached the validated safety threshold.",
        )

    def _exact_or_alias(self, normalized: str) -> ResolvedDrug | None:
        if normalized in self.drugs_by_norm:
            return ResolvedDrug(
                input=normalized,
                normalized_input=normalized,
                status="resolved",
                resolved_name=self.display_by_norm[normalized],
                resolved_normalized=normalized,
                confidence=1,
                match_type="exact",
                confidence_explanation="Exact match to validated drug table.",
            )
        if normalized in self.aliases and self.aliases[normalized] in self.drugs_by_norm:
            actual = self.aliases[normalized]
            return ResolvedDrug(
                input=normalized,
                normalized_input=normalized,
                status="needs_clarification",
                confidence=1,
                match_type="alias_confirmation_required",
                candidates=[self.display_by_norm[actual]],
                message=f"Did you mean {self.display_by_norm[actual]}?",
                confidence_explanation="Alias matched a validated drug, but confirmation is required before the safety pipeline runs.",
            )
        return None

    def _extract_candidate(self, text: str) -> str | None:
        normalized = normalize_drug_name(text)
        stopwords = {
            "can",
            "could",
            "should",
            "may",
            "i",
            "we",
            "add",
            "start",
            "give",
            "use",
            "prescribe",
            "try",
            "the",
            "a",
            "an",
            "for",
            "to",
            "this",
            "that",
            "patient",
            "please",
        }
        tokens = [t for t in normalized.split("-") if t and t not in stopwords]
        spans = []
        for size in range(min(4, len(tokens)), 0, -1):
            for idx in range(len(tokens) - size + 1):
                spans.append("-".join(tokens[idx : idx + size]))
        for span in spans:
            if span in self.drugs_by_norm or span in self.aliases:
                return span
        return spans[0] if spans else normalized

    def _best_match(self, normalized: str) -> tuple[str, float] | None:
        best: tuple[str, float] | None = None
        for choice in self.known_terms:
            ratio = SequenceMatcher(None, normalized, choice).ratio()
            token_bonus = 0.08 if normalized and (choice.startswith(normalized) or normalized.startswith(choice)) else 0
            score = min(1.0, ratio + token_bonus)
            if best is None or score > best[1]:
                best = (choice, score)
        return best

    def _candidate_names(self, normalized: str, minimum_score: float = 0.35) -> list[str]:
        scored: list[tuple[str, float]] = []
        for choice in self.known_terms:
            ratio = SequenceMatcher(None, normalized, choice).ratio()
            is_prefix = bool(choice.startswith(normalized) and normalized)
            is_contains = bool(normalized and normalized in choice)
            prefix_bonus = 0.25 if is_prefix else 0
            contains_bonus = 0.08 if is_contains else 0
            score = min(1.0, ratio + prefix_bonus + contains_bonus)
            if is_prefix or is_contains or ratio >= max(minimum_score, 0.72):
                actual_norm = self.aliases.get(choice, choice)
                display = self.display_by_norm.get(actual_norm)
                if display:
                    scored.append((display, score))
        deduped: dict[str, float] = {}
        for name, score in scored:
            deduped[name] = max(score, deduped.get(name, 0))
        return [name for name, _ in sorted(deduped.items(), key=lambda item: item[1], reverse=True)[:5]]

    def _expand_candidates_by_class(self, candidate_names: list[str]) -> list[str]:
        if not candidate_names:
            return []
        by_display = {drug["generic_name"]: drug for drug in self.drugs_by_norm.values()}
        first = by_display.get(candidate_names[0])
        if not first:
            return candidate_names
        klass = first["drug_class"].lower()
        expanded = list(candidate_names)
        if "macrolide" in klass:
            for drug in self.drugs_by_norm.values():
                if drug["generic_name"] not in expanded and drug["drug_class"].lower() == klass:
                    expanded.append(drug["generic_name"])
                if len(expanded) >= 3:
                    break
        return expanded[:5]

    def _clarification_message(self, candidate_names: list[str]) -> str:
        if not candidate_names:
            return "Please clarify the intended medication before safety checks continue."
        if len(candidate_names) == 1:
            return f"Did you mean {candidate_names[0]}?"
        bullets = "\n".join(f"- {name}" for name in candidate_names)
        return f"Did you mean one of these validated medications?\n{bullets}"

    def _safe_clarification_message(self, raw_input: str, candidate_names: list[str]) -> str:
        deterministic = self._clarification_message(candidate_names)
        if not candidate_names:
            return deterministic
        ai_message = self.llm.clarify_drug_name(raw_input, candidate_names)
        if ai_message and all(candidate.lower() in ai_message.lower() for candidate in candidate_names):
            return ai_message
        return deterministic
