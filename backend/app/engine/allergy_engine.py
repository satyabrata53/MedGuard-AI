from app.models.alerts import SafetyAlert
from app.utils.normalize import normalize_drug_name
from app.utils.severity import importance_for


class AllergyEngine:
    def __init__(self, drugs: list[dict], cross_reactivity: list[dict]) -> None:
        self.drugs = {d["generic_name_normalized"]: d for d in drugs}
        self.cross = cross_reactivity

    def check(self, proposed_drug_norm: str, allergies: list[str]) -> list[SafetyAlert]:
        drug = self.drugs.get(proposed_drug_norm)
        if not drug:
            return []
        drug_class = drug["drug_class"].lower()
        drug_name = drug["generic_name"]
        alerts: list[SafetyAlert] = []

        for allergy in allergies:
            allergy_norm = normalize_drug_name(allergy).replace("-", " ")
            if proposed_drug_norm in normalize_drug_name(allergy):
                alerts.append(
                    SafetyAlert(
                        type="DIRECT_ALLERGY",
                        severity="HARD_BLOCK",
                        title=f"{drug_name} direct allergy risk",
                        mechanism=f"Patient allergy entry includes {drug_name}.",
                        recommendation="Do not administer until allergy is formally reconciled.",
                        importance=importance_for("HARD_BLOCK"),
                    )
                )
            for mapping in self.cross:
                allergy_class = mapping["allergy_class"].lower()
                target_class = mapping["cross_reacts_with"].lower()
                if allergy_class in allergy_norm and target_class in drug_class:
                    severity = "HARD_BLOCK" if "anaphylaxis" in allergy_norm or mapping["cross_reactivity_pct"] >= 80 else "SEVERE"
                    alerts.append(
                        SafetyAlert(
                            type="ALLERGY_CROSS_REACTIVITY",
                            severity=severity,
                            title=f"{drug_name} cross-reactivity with {mapping['allergy_class']} allergy",
                            mechanism=f"Estimated class cross-reactivity {mapping['cross_reactivity_pct']}%.",
                            recommendation=mapping["guidance"],
                            importance=importance_for(severity),
                        )
                    )
        return alerts
