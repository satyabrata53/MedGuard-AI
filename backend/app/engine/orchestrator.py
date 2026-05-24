from app.database.queries import ClinicalRepository
from app.engine.allergy_engine import AllergyEngine
from app.engine.calculator_engine import CalculatorEngine
from app.engine.constraint_generator import ConstraintGenerator
from app.engine.entity_resolver import EntityResolver
from app.engine.intent_classifier import IntentClassifier
from app.engine.interaction_engine import InteractionEngine
from app.engine.renal_engine import RenalEngine
from app.models.alerts import SafetyAlert
from app.models.schemas import Patient, ResolvedDrug, SafetyCheckResponse
from app.utils.logger import log_clinical_event
from app.utils.severity import importance_for


class SafetyOrchestrator:
    def __init__(self, repository: ClinicalRepository) -> None:
        self.repository = repository
        self.refresh()

    def refresh(self) -> None:
        self.drugs = self.repository.get_drugs()
        self.drugs_by_norm = {drug["generic_name_normalized"]: drug for drug in self.drugs}
        self.aliases = self.repository.get_aliases()
        self.cross = self.repository.get_allergy_cross_reactivity()
        self.resolver = EntityResolver(self.drugs, self.aliases)
        self.interactions = InteractionEngine()
        self.allergies = AllergyEngine(self.drugs, self.cross)
        self.renal = RenalEngine(self.drugs)
        self.calculators = CalculatorEngine()
        self.constraints = ConstraintGenerator()
        self.intent_classifier = IntentClassifier()

    def check(self, patient: Patient, query: str, proposed_drug: str | None = None) -> SafetyCheckResponse:
        classified = self.intent_classifier.classify(query, proposed_drug)
        scores = self.calculators.calculate(patient.model_dump())
        alerts: list[SafetyAlert] = []
        review_summary: dict = {}
        resolved = self._empty_resolved(query)

        if classified.intent == "REVIEW_QUERY":
            alerts = self.run_full_medication_review(patient)
            if self._is_antibiotic_option_query(query):
                alerts.extend(self._antibiotic_option_alerts(patient))
            review_summary = self._review_summary(alerts, patient)
        elif classified.intent == "CALCULATOR_QUERY":
            alerts = self._calculator_alerts(scores, query)
        elif classified.intent == "GENERAL_QUERY":
            pass
        else:
            drug_text = proposed_drug or query
            resolved = self.resolver.resolve(drug_text)
            if resolved.status == "resolved" and resolved.resolved_normalized:
                alerts.extend(self.interactions.check_existing(patient.medications))
                alerts.extend(self.interactions.check(resolved.resolved_normalized, patient.medications))
                alerts.extend(self.allergies.check(resolved.resolved_normalized, patient.allergies))
                alerts.extend(self.renal.check(resolved.resolved_normalized, patient.labs))
            elif resolved.status in {"needs_clarification", "clarify"}:
                alerts.append(self._clarification_alert(resolved))
            else:
                alerts.append(self._unknown_drug_alert(resolved))
        alerts.extend(self._override_attempt_alerts(query))

        alerts = sorted(alerts, key=lambda alert: alert.importance, reverse=True)
        constraints = self.constraints.generate(alerts, scores, query, classified.intent)
        why_changed = self._why_safe_ai_changed(alerts, scores, classified.intent)
        log_clinical_event(
            "safety_check",
            patient_id=patient.id,
            intent=classified.intent,
            intent_confidence=classified.confidence,
            query=query,
            proposed_drug=proposed_drug,
            resolved_drug=resolved.resolved_name,
            resolved_status=resolved.status,
            alert_count=len(alerts),
            alert_types=[alert.type for alert in alerts],
            max_importance=max([alert.importance for alert in alerts], default=0),
        )
        return SafetyCheckResponse(
            alerts=alerts,
            scores=scores,
            resolved_drug=resolved,
            constraints=constraints,
            intent=classified.intent,
            review_summary=review_summary,
            why_safe_ai_changed=why_changed,
        )

    def run_full_medication_review(self, patient: Patient) -> list[SafetyAlert]:
        alerts: list[SafetyAlert] = []
        alerts.extend(self.interactions.check_existing(patient.medications))
        for medication in patient.medications:
            resolved = self.resolver.resolve(medication)
            if resolved.status != "resolved" or not resolved.resolved_normalized:
                alerts.append(self._unknown_drug_alert(resolved))
                continue
            alerts.extend(self.allergies.check(resolved.resolved_normalized, patient.allergies))
            alerts.extend(self.renal.check(resolved.resolved_normalized, patient.labs))
            alerts.extend(self._monitoring_alerts(resolved.resolved_normalized, patient.labs))
        return alerts

    def _calculator_alerts(self, scores: dict, query: str) -> list[SafetyAlert]:
        query_norm = query.lower()
        alerts: list[SafetyAlert] = []
        if any(term in query_norm for term in ["stroke", "cha", "vasc", "anticoag"]):
            score = scores.get("cha2ds2_vasc")
            risk = scores.get("stroke_risk_pct_year")
            if score is not None:
                severity = "SEVERE" if score >= 2 else "MINOR"
                recommendation = (
                    f"CHA2DS2-VASc is {score}; estimated untreated stroke risk is {risk}%/year. "
                    "Anticoagulation is strongly indicated unless contraindicated."
                    if score >= 2
                    else f"CHA2DS2-VASc is {score}; use individualized anticoagulation decision-making."
                )
                alerts.append(
                    SafetyAlert(
                        type="CALCULATED_STROKE_RISK",
                        severity=severity,
                        title="Deterministic CHA2DS2-VASc result",
                        mechanism="Calculator engine computed score from structured patient history.",
                        recommendation=recommendation,
                        importance=importance_for(severity),
                    )
                )
        if any(term in query_norm for term in ["egfr", "renal", "kidney"]):
            egfr = scores.get("active_egfr")
            status = scores.get("renal_status")
            alerts.append(
                SafetyAlert(
                    type="CALCULATED_RENAL_FUNCTION",
                    severity="MINOR",
                    title="Deterministic renal function result",
                    mechanism="Calculator engine used available eGFR or CKD-EPI 2021 creatinine calculation.",
                    recommendation=f"Active eGFR for dosing is {egfr}; renal status: {status}.",
                    importance=importance_for("MINOR"),
                )
            )
        return alerts

    def _monitoring_alerts(self, medication_norm: str, patient_labs: dict) -> list[SafetyAlert]:
        drug = self.drugs_by_norm.get(medication_norm)
        if not drug:
            return []
        renal = drug.get("renal_dosing") or {}
        monitor = renal.get("monitor")
        if not monitor:
            return []
        severity = "MODERATE" if patient_labs.get("egfr_ml_min", 100) < 60 else "MINOR"
        return [
            SafetyAlert(
                type="MONITORING_REQUIRED",
                severity=severity,
                title=f"{drug['generic_name']} monitoring requirement",
                mechanism="Medication has deterministic monitoring guidance in the validated drug table.",
                recommendation=monitor,
                importance=importance_for(severity),
            )
        ]

    def _antibiotic_option_alerts(self, patient: Patient) -> list[SafetyAlert]:
        screened: list[tuple[str, list[SafetyAlert]]] = []
        for drug in self.drugs:
            if "antibiotic" not in drug["drug_class"].lower():
                continue
            normalized = drug["generic_name_normalized"]
            candidate_alerts: list[SafetyAlert] = []
            candidate_alerts.extend(self.interactions.check(normalized, patient.medications))
            candidate_alerts.extend(self.allergies.check(normalized, patient.allergies))
            candidate_alerts.extend(self.renal.check(normalized, patient.labs))
            screened.append((drug["generic_name"], candidate_alerts))

        lower_signal = [name for name, alerts in screened if not any(alert.severity in {"HARD_BLOCK", "SEVERE", "MODERATE"} for alert in alerts)]
        avoid_or_review = [
            f"{name}: {self._highest_signal(alerts)}"
            for name, alerts in screened
            if any(alert.severity in {"HARD_BLOCK", "SEVERE"} for alert in alerts)
        ][:5]

        recommendation = "Deterministic antibiotic option screen completed. "
        if lower_signal:
            recommendation += f"Lower-signal options in the validated DB: {', '.join(lower_signal[:5])}. "
        if avoid_or_review:
            recommendation += f"Avoid or specialist-review: {'; '.join(avoid_or_review)}. "
        recommendation += "Final antibiotic choice still depends on infection site, cultures, local resistance, and clinician judgement."

        return [
            SafetyAlert(
                type="ANTIBIOTIC_OPTION_SCREEN",
                severity="MINOR",
                title="Deterministic antibiotic option screen",
                mechanism="Validated antibiotic rows were screened against current medications, allergies, and renal function.",
                recommendation=recommendation,
                importance=importance_for("MINOR"),
            )
        ]

    def _highest_signal(self, alerts: list[SafetyAlert]) -> str:
        if not alerts:
            return "no deterministic alert"
        highest = sorted(alerts, key=lambda alert: alert.importance, reverse=True)[0]
        return f"{highest.severity} - {highest.title}"

    def _review_summary(self, alerts: list[SafetyAlert], patient: Patient) -> dict:
        counts = {"HARD_BLOCK": 0, "SEVERE": 0, "MODERATE": 0, "MINOR": 0}
        for alert in alerts:
            counts[alert.severity] = counts.get(alert.severity, 0) + 1
        return {
            "medications_reviewed": len(patient.medications),
            "total_alerts": len(alerts),
            "severity_counts": counts,
            "highest_importance": max([alert.importance for alert in alerts], default=0),
            "summary": self._review_summary_text(counts),
        }

    def _review_summary_text(self, counts: dict) -> str:
        if counts.get("HARD_BLOCK"):
            return "Non-overridable safety issue detected in the current medication profile."
        if counts.get("SEVERE"):
            return "Severe medication safety findings require clinician review."
        if counts.get("MODERATE"):
            return "Moderate medication safety findings require monitoring or adjustment."
        return "No high-priority deterministic findings in the current medication profile."

    def _is_antibiotic_option_query(self, query: str) -> bool:
        query_norm = query.lower()
        return "antibiotic" in query_norm and any(term in query_norm for term in ["safest", "option", "choice", "recommend"])

    def _why_safe_ai_changed(self, alerts: list[SafetyAlert], scores: dict, intent: str) -> list[str]:
        reasons: list[str] = []
        if any(alert.severity == "HARD_BLOCK" for alert in alerts):
            reasons.append("Hard block detected")
        if any(alert.severity == "SEVERE" for alert in alerts):
            reasons.append("Severe safety signal detected")
        if any("INTERACTION" in alert.type for alert in alerts):
            reasons.append("Drug interaction detected")
        if any(alert.type == "RENAL_DOSING" for alert in alerts):
            reasons.append("Renal dosing adjustment required")
        if any("ALLERGY" in alert.type for alert in alerts):
            reasons.append("Allergy conflict identified")
        if intent == "CALCULATOR_QUERY" or scores.get("cha2ds2_vasc") is not None:
            reasons.append("Deterministic clinical score injected")
        return reasons

    def _clarification_alert(self, resolved: ResolvedDrug) -> SafetyAlert:
        recommendation = resolved.message or "Ask the prescriber to confirm the intended drug."
        if resolved.candidates:
            recommendation = f"{recommendation}\nValidated candidates: {', '.join(resolved.candidates)}"
        return SafetyAlert(
            type="ENTITY_CLARIFICATION_REQUIRED",
            severity="HARD_BLOCK",
            title="Medication name requires confirmation",
            mechanism=resolved.confidence_explanation or "Entity resolver confidence is below the safe threshold.",
            recommendation=recommendation,
            importance=importance_for("HARD_BLOCK"),
        )

    def _unknown_drug_alert(self, resolved: ResolvedDrug) -> SafetyAlert:
        candidate_text = f" Possible validated candidates: {', '.join(resolved.candidates)}." if resolved.candidates else ""
        return SafetyAlert(
            type="UNVALIDATED_DRUG",
            severity="SEVERE",
            title="Drug not found in validated clinical database",
            mechanism=(resolved.confidence_explanation or "The proposed medication could not be matched to the curated drug table.") + candidate_text,
            recommendation="Manual pharmacist review recommended before continuing. Do not allow AI to infer medication safety for this drug.",
            importance=importance_for("SEVERE"),
        )

    def _override_attempt_alerts(self, query: str) -> list[SafetyAlert]:
        query_norm = query.lower()
        override_terms = ["override", "prescribe anyway", "proceed anyway", "ignore alert", "ignore warning"]
        if not any(term in query_norm for term in override_terms):
            return []
        return [
            SafetyAlert(
                type="OVERRIDE_ATTEMPT",
                severity="SEVERE",
                title="Potential safety override attempt",
                mechanism="The query appears to request bypassing or overriding deterministic safety governance.",
                recommendation="Require documented senior clinician justification and pharmacist review before proceeding.",
                importance=importance_for("SEVERE"),
            )
        ]

    def _empty_resolved(self, query: str) -> ResolvedDrug:
        return ResolvedDrug(
            input=query,
            normalized_input="",
            status="not_found",
            confidence=0,
            match_type="not_applicable",
            message="No proposed medication required for this intent.",
            confidence_explanation="Intent did not require medication entity resolution.",
        )
