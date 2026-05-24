from app.cache.interaction_cache import interaction_cache
from app.models.alerts import SafetyAlert
from app.utils.normalize import normalize_drug_name
from app.utils.severity import importance_for


class InteractionEngine:
    def check(self, proposed_drug_norm: str, current_medications: list[str]) -> list[SafetyAlert]:
        alerts: list[SafetyAlert] = []
        for med in current_medications:
            interaction = interaction_cache.lookup(proposed_drug_norm, normalize_drug_name(med))
            if not interaction:
                continue
            alerts.append(
                SafetyAlert(
                    type="DRUG_INTERACTION",
                    severity=interaction.severity,
                    title=f"{proposed_drug_norm.replace('-', ' ').title()} + {med}",
                    mechanism=interaction.mechanism,
                    recommendation=f"{interaction.clinical_effect} {interaction.management}",
                    importance=importance_for(interaction.severity),
                )
            )
        return alerts

    def check_existing(self, current_medications: list[str]) -> list[SafetyAlert]:
        alerts: list[SafetyAlert] = []
        normalized = [(med, normalize_drug_name(med)) for med in current_medications]
        seen: set[str] = set()
        for idx, (left_name, left_norm) in enumerate(normalized):
            for right_name, right_norm in normalized[idx + 1 :]:
                interaction = interaction_cache.lookup(left_norm, right_norm)
                if not interaction:
                    continue
                key = f"{interaction.drug_a_normalized}::{interaction.drug_b_normalized}"
                if key in seen:
                    continue
                seen.add(key)
                alerts.append(
                    SafetyAlert(
                        type="EXISTING_DRUG_INTERACTION",
                        severity=interaction.severity,
                        title=f"Existing meds: {left_name} + {right_name}",
                        mechanism=interaction.mechanism,
                        recommendation=f"{interaction.clinical_effect} {interaction.management}",
                        importance=importance_for(interaction.severity),
                    )
                )
        return alerts
