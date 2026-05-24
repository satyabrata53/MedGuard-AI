from app.models.alerts import SafetyAlert


class ConstraintGenerator:
    def generate(self, alerts: list[SafetyAlert], scores: dict | None = None, query: str = "", intent: str = "DRUG_QUERY") -> str:
        scores = scores or {}
        sections = self._score_sections(scores, query, intent)

        for alert in alerts:
            label = "HARD BLOCK" if alert.severity == "HARD_BLOCK" else alert.severity
            icon = "STOP" if alert.severity == "HARD_BLOCK" else "WARNING"
            sections.append(
                f"{icon} {label}:\n"
                f"{alert.title}\n"
                f"Mechanism: {alert.mechanism}\n"
                f"Recommendation: {alert.recommendation}"
            )
        if sections:
            return "\n\n".join(sections)
        return "No deterministic safety alerts were detected in the validated database. Continue standard clinical review."

    def _score_sections(self, scores: dict, query: str, intent: str) -> list[str]:
        sections: list[str] = []
        query_norm = query.lower()
        cha_score = scores.get("cha2ds2_vasc")
        if cha_score is not None and any(term in query_norm for term in ["anticoag", "atrial fibrillation", " af", "cha"]):
            risk = self._cha2ds2_vasc_risk(cha_score)
            if cha_score >= 2:
                guidance = "Oral anticoagulation is strongly indicated unless bleeding risk or contraindication outweighs benefit."
            elif cha_score == 1:
                guidance = "Anticoagulation should be individualized using patient-specific risk and shared decision-making."
            else:
                guidance = "Anticoagulation is usually not required for stroke prevention based on this score alone."
            sections.append(
                "INFO CALCULATED SCORE:\n"
                f"CHA2DS2-VASc = {cha_score}. Estimated untreated stroke risk: {risk}.\n"
                f"Recommendation: {guidance}"
            )

        egfr = scores.get("ckd_epi_2021_egfr")
        should_include_egfr = intent == "DRUG_QUERY" or any(term in query_norm for term in ["egfr", "renal", "kidney"])
        if egfr is not None and should_include_egfr:
            sections.append(
                "INFO CALCULATED RENAL FUNCTION:\n"
                f"CKD-EPI 2021 eGFR = {egfr} mL/min/1.73m2.\n"
                "Recommendation: Use this deterministic value for renal dosing checks."
            )
        return sections

    def _cha2ds2_vasc_risk(self, score: int) -> str:
        risks = {
            0: "0.2%/year",
            1: "0.6%/year",
            2: "2.2%/year",
            3: "3.2%/year",
            4: "4.8%/year",
            5: "7.2%/year",
            6: "6.7%/year",
            7: "9.6%/year",
            8: "6.7%/year",
            9: "15.2%/year",
        }
        return risks.get(score, "high annual risk")
