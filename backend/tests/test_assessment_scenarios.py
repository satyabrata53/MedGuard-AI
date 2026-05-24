import unittest

from app.cache.interaction_cache import interaction_cache
from app.database.queries import ClinicalRepository
from app.engine.orchestrator import SafetyOrchestrator
from app.models.schemas import Patient


class AssessmentScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ClinicalRepository._remote_disabled = True
        cls.repository = ClinicalRepository()
        interaction_cache.build(cls.repository.get_interactions())
        cls.orchestrator = SafetyOrchestrator(cls.repository)

    def test_seed_data_has_required_breadth(self) -> None:
        self.assertGreaterEqual(len(self.repository.get_drugs()), 50)
        self.assertGreaterEqual(len(self.repository.get_interactions()), 30)

    def test_scenario_1_clarithromycin_catches_multiple_interactions_and_bonus(self) -> None:
        patient = Patient(
            id="DEMO-01",
            name="Scenario 1",
            age=78,
            sex="male",
            medications=["Atorvastatin", "Amlodipine", "Diclofenac", "Telmisartan"],
            labs={"scr_mg_dl": 1.0, "egfr_ml_min": 70},
            history={"hypertension": True, "vascular_disease": True},
        )

        response = self.orchestrator.check(patient, "Can I add Clarithromycin 500mg for pneumonia?", "Clarithromycin")
        text = self._alert_text(response)

        self.assertIn("Clarithromycin + Atorvastatin", text)
        self.assertIn("Clarithromycin + Amlodipine", text)
        self.assertIn("Existing meds: Diclofenac + Telmisartan", text)
        self.assertIn("azithromycin", response.constraints.lower())

    def test_scenario_2_penicillin_anaphylaxis_hard_blocks_augmentin(self) -> None:
        patient = Patient(
            id="DEMO-02",
            name="Scenario 2",
            age=65,
            sex="male",
            allergies=["Penicillin anaphylaxis 2023"],
            labs={"scr_mg_dl": 2.2, "egfr_ml_min": 31.2},
            history={"hypertension": True},
        )

        response = self.orchestrator.check(patient, "UTI treatment - can I use Amoxicillin-Clavulanate?", "Amoxicillin-Clavulanate")

        self.assertTrue(any(alert.severity == "HARD_BLOCK" for alert in response.alerts))
        self.assertIn("penicillin", response.constraints.lower())

    def test_scenario_3_gabapentin_renal_dosing_is_specific(self) -> None:
        patient = Patient(
            id="DEMO-03",
            name="Scenario 3",
            age=35,
            sex="female",
            labs={"scr_mg_dl": 3.2, "egfr_ml_min": 18},
        )

        response = self.orchestrator.check(patient, "Adding Gabapentin 300mg TDS for neuropathic pain", "Gabapentin")

        self.assertIn("100 mg once daily", response.constraints)
        self.assertIn("avoid 300 mg TDS", response.constraints)
        self.assertAlmostEqual(response.scores["ckd_epi_2021_egfr"], 18.7)

    def test_scenario_4_cha2ds2_vasc_drives_anticoagulation_response(self) -> None:
        patient = Patient(
            id="DEMO-04",
            name="Scenario 4",
            age=68,
            sex="male",
            diagnoses=["Atrial fibrillation"],
            medications=["Warfarin"],
            labs={"scr_mg_dl": 1.0},
            history={"chf": True, "hypertension": True, "diabetes": True, "stroke_tia": True},
        )

        response = self.orchestrator.check(patient, "Does this patient still need anticoagulation?")

        self.assertEqual(response.intent, "CALCULATOR_QUERY")
        self.assertEqual(response.scores["cha2ds2_vasc"], 6)
        self.assertIn("CHA2DS2-VASc = 6", response.constraints)
        self.assertIn("strongly indicated", response.constraints.lower())
        self.assertNotIn("UNVALIDATED_DRUG", self._alert_text(response))

    def test_review_query_runs_full_medication_audit_without_new_drug(self) -> None:
        patient = Patient(
            id="REVIEW",
            name="Review",
            age=72,
            sex="female",
            medications=["Warfarin", "Aspirin", "Lisinopril", "Spironolactone", "Ibuprofen"],
            allergies=[],
            labs={"scr_mg_dl": 1.6, "egfr_ml_min": 34, "potassium_mmol_l": 5.1},
            history={"hypertension": True},
        )

        response = self.orchestrator.check(patient, "Review this patient's medications for dangerous interactions")
        text = self._alert_text(response)

        self.assertEqual(response.intent, "REVIEW_QUERY")
        self.assertIn("Existing meds: Warfarin + Aspirin", text)
        self.assertIn("Existing meds: Lisinopril + Spironolactone", text)
        self.assertGreaterEqual(response.review_summary["medications_reviewed"], 5)
        self.assertGreater(response.review_summary["total_alerts"], 0)

    def test_high_risk_combinations_query_is_review_intent(self) -> None:
        patient = Patient(
            id="REVIEW-PHRASE",
            name="Review Phrase",
            age=72,
            sex="female",
            medications=["Warfarin", "Aspirin", "Lisinopril"],
            allergies=[],
            labs={"scr_mg_dl": 1.6, "egfr_ml_min": 34},
        )

        response = self.orchestrator.check(patient, "Are there any high-risk combinations already present in this patient's medications?")

        self.assertEqual(response.intent, "REVIEW_QUERY")
        self.assertTrue(any(alert.type == "EXISTING_DRUG_INTERACTION" for alert in response.alerts))

    def test_general_patient_question_does_not_become_unknown_drug(self) -> None:
        patient = Patient(
            id="GENERAL",
            name="General",
            age=72,
            sex="female",
            diagnoses=["Atrial fibrillation", "CKD stage 3b"],
            medications=["Warfarin", "Atorvastatin"],
            allergies=[],
            labs={"scr_mg_dl": 1.6, "egfr_ml_min": 34},
        )

        response = self.orchestrator.check(patient, "Summarize this patient's main clinical risks.")

        self.assertEqual(response.intent, "GENERAL_QUERY")
        self.assertEqual(response.alerts, [])
        self.assertNotIn("UNVALIDATED_DRUG", response.constraints)

    def test_unknown_drug_in_drug_query_still_fails_safely(self) -> None:
        patient = Patient(
            id="UNKNOWN-DRUG",
            name="Unknown Drug",
            age=72,
            sex="female",
            medications=[],
            allergies=[],
            labs={"scr_mg_dl": 1.0, "egfr_ml_min": 80},
        )

        response = self.orchestrator.check(patient, "Can I add madeupmed?", "madeupmed")

        self.assertEqual(response.intent, "DRUG_QUERY")
        self.assertTrue(any(alert.type == "UNVALIDATED_DRUG" for alert in response.alerts))

    def test_ambiguous_medication_requires_confirmation(self) -> None:
        patient = Patient(
            id="AMBIG",
            name="Ambiguous",
            age=60,
            sex="male",
            medications=[],
            labs={"scr_mg_dl": 1.0, "egfr_ml_min": 80},
        )

        response = self.orchestrator.check(patient, "Can I add met?", "met")

        self.assertEqual(response.resolved_drug.status, "needs_clarification")
        self.assertTrue(response.resolved_drug.candidates)
        self.assertIn("Metformin", response.resolved_drug.candidates)
        self.assertIn("Metoprolol", response.resolved_drug.candidates)
        self.assertIn("Methotrexate", response.resolved_drug.candidates)
        self.assertTrue(any(alert.type == "ENTITY_CLARIFICATION_REQUIRED" for alert in response.alerts))

    def test_alias_requires_confirmation_before_safety_pipeline(self) -> None:
        patient = Patient(
            id="ALIAS",
            name="Alias",
            age=70,
            sex="male",
            medications=["Atorvastatin"],
            labs={"scr_mg_dl": 1.0, "egfr_ml_min": 80},
        )

        response = self.orchestrator.check(patient, "Can I add clarithro?", "clarithro")

        self.assertEqual(response.resolved_drug.status, "needs_clarification")
        self.assertIn("Clarithromycin", response.resolved_drug.candidates)
        self.assertFalse(any(alert.type == "DRUG_INTERACTION" for alert in response.alerts))

    def test_confirmed_candidate_runs_deterministic_pipeline(self) -> None:
        patient = Patient(
            id="CONFIRMED",
            name="Confirmed",
            age=70,
            sex="male",
            medications=["Atorvastatin"],
            labs={"scr_mg_dl": 1.0, "egfr_ml_min": 80},
        )

        response = self.orchestrator.check(patient, "Can I add clarithro?", "Clarithromycin")

        self.assertEqual(response.resolved_drug.status, "resolved")
        self.assertTrue(any(alert.type == "DRUG_INTERACTION" for alert in response.alerts))

    def test_typo_suggests_candidate_instead_of_unknown(self) -> None:
        patient = Patient(
            id="TYPO",
            name="Typo",
            age=70,
            sex="male",
            medications=[],
            labs={"scr_mg_dl": 1.0, "egfr_ml_min": 80},
        )

        response = self.orchestrator.check(patient, "Can I add clarithromicin?", "clarithromicin")

        self.assertEqual(response.resolved_drug.status, "needs_clarification")
        self.assertIn("Clarithromycin", response.resolved_drug.candidates)

    def test_partial_drug_in_sentence_suggests_candidates(self) -> None:
        patient = Patient(
            id="PARTIAL",
            name="Partial",
            age=70,
            sex="male",
            medications=["Atorvastatin"],
            labs={"scr_mg_dl": 1.0, "egfr_ml_min": 80},
        )

        response = self.orchestrator.check(patient, "Can I add clarith?")

        self.assertEqual(response.resolved_drug.status, "needs_clarification")
        self.assertIn("Clarithromycin", response.resolved_drug.candidates)
        self.assertIn("Azithromycin", response.resolved_drug.candidates)
        self.assertFalse(any(alert.type == "DRUG_INTERACTION" for alert in response.alerts))

    def test_bare_drug_fragment_is_treated_as_drug_query(self) -> None:
        patient = Patient(
            id="BARE",
            name="Bare",
            age=70,
            sex="male",
            medications=[],
            labs={"scr_mg_dl": 1.0, "egfr_ml_min": 80},
        )

        response = self.orchestrator.check(patient, "gaba")

        self.assertEqual(response.intent, "DRUG_QUERY")
        self.assertEqual(response.resolved_drug.status, "needs_clarification")
        self.assertIn("Gabapentin", response.resolved_drug.candidates)

    def test_unrelated_unknown_drug_fails_safely_without_random_candidate(self) -> None:
        patient = Patient(
            id="UNKNOWN",
            name="Unknown",
            age=70,
            sex="male",
            medications=[],
            labs={"scr_mg_dl": 1.0, "egfr_ml_min": 80},
        )

        response = self.orchestrator.check(patient, "Can I add zzqnotadrug?", "zzqnotadrug")

        self.assertEqual(response.resolved_drug.status, "drug_not_found")
        self.assertEqual(response.resolved_drug.candidates, [])
        self.assertTrue(any(alert.type == "UNVALIDATED_DRUG" for alert in response.alerts))

    def test_kidney_disease_question_is_general_with_renal_context(self) -> None:
        patient = Patient(
            id="KIDNEY",
            name="Kidney",
            age=72,
            sex="female",
            diagnoses=["CKD stage 3b"],
            medications=["Lisinopril"],
            labs={"scr_mg_dl": 1.7, "egfr_ml_min": 32},
        )

        response = self.orchestrator.check(patient, "How severe is this patient's kidney disease?")

        self.assertEqual(response.intent, "GENERAL_QUERY")
        self.assertEqual(response.alerts, [])
        self.assertIn("CKD-EPI 2021 eGFR", response.constraints)

    def test_safest_antibiotic_option_runs_deterministic_candidate_screen(self) -> None:
        patient = Patient(
            id="ANTIBIOTIC",
            name="Antibiotic",
            age=72,
            sex="female",
            medications=["Warfarin", "Atorvastatin", "Metformin", "Lisinopril"],
            allergies=["Penicillin anaphylaxis"],
            labs={"scr_mg_dl": 1.7, "egfr_ml_min": 32},
        )

        response = self.orchestrator.check(patient, "What is the safest antibiotic option for this patient considering medications, allergies, and kidney function?")
        text = self._alert_text(response)

        self.assertEqual(response.intent, "REVIEW_QUERY")
        self.assertIn("ANTIBIOTIC_OPTION_SCREEN", text)
        self.assertIn("Azithromycin", text)
        self.assertNotIn("UNVALIDATED_DRUG", text)

    def test_override_attempt_is_logged_as_safety_signal(self) -> None:
        patient = Patient(
            id="OVERRIDE",
            name="Override",
            age=65,
            sex="male",
            medications=["Simvastatin"],
            labs={"scr_mg_dl": 1.0, "egfr_ml_min": 80},
        )

        response = self.orchestrator.check(patient, "Can I override the warning and prescribe anyway?", "Clarithromycin")

        self.assertTrue(any(alert.type == "OVERRIDE_ATTEMPT" for alert in response.alerts))
        self.assertTrue(any(alert.severity == "HARD_BLOCK" for alert in response.alerts))

    def test_surprise_patient_checks_existing_interactions_and_new_allergy_block(self) -> None:
        patient = Patient(
            id="SURPRISE",
            name="Surprise",
            age=60,
            sex="female",
            medications=["Fluoxetine", "Tramadol", "Clopidogrel", "Omeprazole"],
            allergies=["NSAID allergy"],
            labs={"scr_mg_dl": 1.0, "egfr_ml_min": 80},
        )

        response = self.orchestrator.check(patient, "Can she take Ibuprofen?", "Ibuprofen")
        text = self._alert_text(response)

        self.assertIn("Existing meds: Fluoxetine + Tramadol", text)
        self.assertIn("Existing meds: Clopidogrel + Omeprazole", text)
        self.assertIn("Ibuprofen cross-reactivity with nsaid allergy", text)
        self.assertTrue(any(alert.severity == "HARD_BLOCK" for alert in response.alerts))

    def _alert_text(self, response) -> str:
        return "\n".join(f"{alert.type} {alert.title} {alert.recommendation}" for alert in response.alerts)


if __name__ == "__main__":
    unittest.main()
