from app.models.alerts import SafetyAlert
from app.utils.severity import importance_for


class RenalEngine:
    def __init__(self, drugs: list[dict]) -> None:
        self.drugs = {d["generic_name_normalized"]: d for d in drugs}

    def check(self, proposed_drug_norm: str, patient_labs: dict) -> list[SafetyAlert]:
        drug = self.drugs.get(proposed_drug_norm)
        if not drug:
            return []
        egfr = patient_labs.get("egfr_ml_min")
        if egfr is None:
            return [
                SafetyAlert(
                    type="RENAL_DATA_GAP",
                    severity="MODERATE",
                    title=f"Renal function required for {drug['generic_name']}",
                    mechanism="No eGFR is available in the patient context.",
                    recommendation="Obtain renal function before final medication order.",
                    importance=importance_for("MODERATE"),
                )
            ]

        renal = drug.get("renal_dosing") or {}
        alerts: list[SafetyAlert] = []
        if renal.get("contraindicated_below") is not None and egfr < renal["contraindicated_below"]:
            alerts.append(self._alert("HARD_BLOCK", drug["generic_name"], egfr, f"Contraindicated when eGFR < {renal['contraindicated_below']}."))
        elif renal.get("avoid_below") is not None and egfr < renal["avoid_below"]:
            alerts.append(self._alert("SEVERE", drug["generic_name"], egfr, f"Avoid when eGFR < {renal['avoid_below']} unless specialist-directed."))
        elif renal.get("min_egfr") is not None and egfr < renal["min_egfr"]:
            alerts.append(self._alert("HARD_BLOCK", drug["generic_name"], egfr, f"Below minimum supported eGFR threshold of {renal['min_egfr']}."))

        for adjustment in renal.get("dose_adjust", []):
            if egfr < adjustment["below"]:
                alerts.append(self._alert(adjustment.get("severity", "MODERATE"), drug["generic_name"], egfr, adjustment["guidance"]))
        return alerts

    def _alert(self, severity: str, drug_name: str, egfr: float, guidance: str) -> SafetyAlert:
        return SafetyAlert(
            type="RENAL_DOSING",
            severity=severity,
            title=f"{drug_name} renal dosing constraint",
            mechanism=f"Patient eGFR is {egfr} mL/min/1.73m2.",
            recommendation=guidance,
            importance=importance_for(severity),
        )
