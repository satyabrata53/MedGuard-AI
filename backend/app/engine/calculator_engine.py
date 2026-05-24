class CalculatorEngine:
    def ckd_epi_2021(self, age: int, sex: str, scr_mg_dl: float | None) -> float | None:
        if not scr_mg_dl or scr_mg_dl <= 0:
            return None
        female = sex.lower() == "female"
        kappa = 0.7 if female else 0.9
        alpha = -0.241 if female else -0.302
        sex_factor = 1.012 if female else 1.0
        egfr = 142 * min(scr_mg_dl / kappa, 1) ** alpha * max(scr_mg_dl / kappa, 1) ** -1.2 * 0.9938 ** age * sex_factor
        return round(egfr, 1)

    def cha2ds2_vasc(self, patient: dict) -> int:
        age = patient.get("age", 0)
        sex = patient.get("sex", "")
        history = patient.get("history", {})
        score = 0
        score += 1 if history.get("chf") else 0
        score += 1 if history.get("hypertension") else 0
        score += 1 if history.get("diabetes") else 0
        score += 2 if history.get("stroke_tia") else 0
        score += 1 if history.get("vascular_disease") else 0
        score += 2 if age >= 75 else 1 if age >= 65 else 0
        score += 1 if sex == "female" else 0
        return score

    def calculate(self, patient: dict) -> dict:
        labs = patient.get("labs", {})
        computed_egfr = self.ckd_epi_2021(patient.get("age", 0), patient.get("sex", ""), labs.get("scr_mg_dl"))
        egfr = labs.get("egfr_ml_min") or computed_egfr
        cha_score = self.cha2ds2_vasc(patient)
        return {
            "ckd_epi_2021_egfr": computed_egfr,
            "active_egfr": egfr,
            "renal_status": self.renal_status(egfr),
            "cha2ds2_vasc": cha_score,
            "stroke_risk_pct_year": self.stroke_risk_pct(cha_score),
        }

    def stroke_risk_pct(self, score: int) -> float:
        risks = {0: 0.2, 1: 0.6, 2: 2.2, 3: 3.2, 4: 4.8, 5: 7.2, 6: 6.7, 7: 9.6, 8: 6.7, 9: 15.2}
        return risks.get(score, 15.2)

    def renal_status(self, egfr: float | None) -> str:
        if egfr is None:
            return "Unknown"
        if egfr < 15:
            return "Kidney failure"
        if egfr < 30:
            return "Severe renal impairment"
        if egfr < 45:
            return "Moderate-severe renal impairment"
        if egfr < 60:
            return "Mild-moderate renal impairment"
        return "No renal dosing restriction by eGFR"
