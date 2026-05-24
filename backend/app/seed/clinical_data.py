from app.utils.normalize import normalize_drug_name


DRUG_NAMES = [
    ("Amoxicillin", "Penicillin antibiotic", {"min_egfr": 10, "dose_adjust": [{"below": 30, "guidance": "Extend interval; review dose."}]}),
    ("Amoxicillin-Clavulanate", "Penicillin antibiotic", {"min_egfr": 10, "dose_adjust": [{"below": 30, "guidance": "Use renal-adjusted dosing."}]}),
    ("Azithromycin", "Macrolide antibiotic", {"min_egfr": 10}),
    ("Clarithromycin", "Macrolide antibiotic", {"min_egfr": 30, "dose_adjust": [{"below": 60, "guidance": "Reduce dose by 50% when eGFR <60."}]}),
    ("Ciprofloxacin", "Fluoroquinolone antibiotic", {"min_egfr": 15, "dose_adjust": [{"below": 30, "guidance": "Reduce dose or extend interval."}]}),
    ("Levofloxacin", "Fluoroquinolone antibiotic", {"min_egfr": 15, "dose_adjust": [{"below": 50, "guidance": "Renal dose adjustment required."}]}),
    ("Doxycycline", "Tetracycline antibiotic", {"min_egfr": 10}),
    ("Trimethoprim-Sulfamethoxazole", "Sulfonamide antibiotic", {"min_egfr": 15, "dose_adjust": [{"below": 30, "guidance": "Reduce dose; avoid if severe renal impairment."}]}),
    ("Vancomycin", "Glycopeptide antibiotic", {"min_egfr": 10, "dose_adjust": [{"below": 60, "guidance": "Dose by levels and renal function."}]}),
    ("Metformin", "Biguanide", {"contraindicated_below": 30, "dose_adjust": [{"below": 45, "guidance": "Do not initiate; reassess risk/benefit."}]}),
    ("Insulin Glargine", "Long-acting insulin", {"min_egfr": 10}),
    ("Glipizide", "Sulfonylurea", {"min_egfr": 10}),
    ("Empagliflozin", "SGLT2 inhibitor", {"contraindicated_below": 20}),
    ("Lisinopril", "ACE inhibitor", {"min_egfr": 10, "monitor": "Monitor potassium and creatinine."}),
    ("Losartan", "ARB", {"min_egfr": 10, "monitor": "Monitor potassium and creatinine."}),
    ("Spironolactone", "Mineralocorticoid receptor antagonist", {"contraindicated_below": 30}),
    ("Furosemide", "Loop diuretic", {"min_egfr": 10}),
    ("Hydrochlorothiazide", "Thiazide diuretic", {"avoid_below": 30}),
    ("Amlodipine", "Calcium channel blocker", {"min_egfr": 10}),
    ("Metoprolol", "Beta blocker", {"min_egfr": 10}),
    ("Diltiazem", "Calcium channel blocker", {"min_egfr": 10}),
    ("Atorvastatin", "Statin", {"min_egfr": 10}),
    ("Simvastatin", "Statin", {"min_egfr": 10}),
    ("Rosuvastatin", "Statin", {"dose_adjust": [{"below": 30, "guidance": "Start 5 mg; max 10 mg daily."}]}),
    ("Warfarin", "Vitamin K antagonist", {"min_egfr": 10}),
    ("Apixaban", "DOAC", {"min_egfr": 15, "monitor": "Assess age, weight, creatinine for dose criteria."}),
    ("Rivaroxaban", "DOAC", {"contraindicated_below": 15}),
    ("Clopidogrel", "Antiplatelet", {"min_egfr": 10}),
    ("Aspirin", "NSAID antiplatelet", {"avoid_below": 30}),
    ("Ibuprofen", "NSAID", {"avoid_below": 60}),
    ("Naproxen", "NSAID", {"avoid_below": 60}),
    ("Prednisone", "Corticosteroid", {"min_egfr": 10}),
    ("Omeprazole", "PPI", {"min_egfr": 10}),
    ("Pantoprazole", "PPI", {"min_egfr": 10}),
    ("Levothyroxine", "Thyroid hormone", {"min_egfr": 10}),
    ("Sertraline", "SSRI", {"min_egfr": 10}),
    ("Fluoxetine", "SSRI", {"min_egfr": 10}),
    ("Citalopram", "SSRI", {"min_egfr": 10}),
    ("Tramadol", "Opioid analgesic", {"dose_adjust": [{"below": 30, "guidance": "Extend interval; max 200 mg/day."}]}),
    ("Morphine", "Opioid analgesic", {"avoid_below": 30}),
    ("Oxycodone", "Opioid analgesic", {"dose_adjust": [{"below": 60, "guidance": "Start low and titrate cautiously."}]}),
    ("Gabapentin", "Anticonvulsant analgesic", {"dose_adjust": [{"below": 30, "severity": "SEVERE", "guidance": "At eGFR 15-29, use 100 mg once daily; avoid 300 mg TDS because accumulation and neurotoxicity risk are high."}, {"below": 60, "guidance": "Renal dose adjustment required."}]}),
    ("Pregabalin", "Anticonvulsant analgesic", {"dose_adjust": [{"below": 60, "guidance": "Renal dose adjustment required."}]}),
    ("Allopurinol", "Xanthine oxidase inhibitor", {"dose_adjust": [{"below": 60, "guidance": "Start low; titrate by urate and renal function."}]}),
    ("Colchicine", "Antigout", {"contraindicated_below": 30}),
    ("Digoxin", "Cardiac glycoside", {"dose_adjust": [{"below": 60, "guidance": "Use lower dose and monitor levels."}]}),
    ("Amiodarone", "Antiarrhythmic", {"min_egfr": 10}),
    ("Phenytoin", "Anticonvulsant", {"min_egfr": 10}),
    ("Carbamazepine", "Anticonvulsant", {"min_egfr": 10}),
    ("Paracetamol", "Analgesic antipyretic", {"min_egfr": 10}),
    ("Diclofenac", "NSAID", {"avoid_below": 60}),
    ("Telmisartan", "ARB", {"min_egfr": 10, "monitor": "Monitor potassium and creatinine."}),
    ("Methotrexate", "Antimetabolite immunosuppressant", {"contraindicated_below": 30, "dose_adjust": [{"below": 60, "guidance": "Renal dose adjustment and specialist monitoring required."}]}),
]

DRUGS = [
    {"id": idx + 1, "generic_name": name, "generic_name_normalized": normalize_drug_name(name), "drug_class": klass, "renal_dosing": renal}
    for idx, (name, klass, renal) in enumerate(DRUG_NAMES)
]

ALIASES = [
    ("augmentin", "Amoxicillin-Clavulanate"), ("tylenol", "Paracetamol"), ("acetaminophen", "Paracetamol"),
    ("gaba", "Gabapentin"), ("clarithro", "Clarithromycin"), ("azithro", "Azithromycin"),
    ("bactrim", "Trimethoprim-Sulfamethoxazole"), ("co-trimoxazole", "Trimethoprim-Sulfamethoxazole"),
    ("lasix", "Furosemide"), ("coumadin", "Warfarin"), ("eliquis", "Apixaban"), ("xarelto", "Rivaroxaban"),
    ("plavix", "Clopidogrel"), ("motrin", "Ibuprofen"), ("advil", "Ibuprofen"), ("synthroid", "Levothyroxine"),
    ("voltaren", "Diclofenac"), ("micardis", "Telmisartan"),
    ("mtx", "Methotrexate"),
]

INTERACTIONS = [
    ("Clarithromycin", "Atorvastatin", "SEVERE", "CYP3A4 inhibition raises statin exposure.", "Myopathy and rhabdomyolysis.", "Hold atorvastatin or use azithromycin."),
    ("Clarithromycin", "Amlodipine", "MODERATE", "CYP3A4 inhibition raises calcium-channel blocker exposure.", "Hypotension, bradycardia, and acute kidney injury risk.", "Prefer azithromycin or monitor blood pressure closely if unavoidable."),
    ("Clarithromycin", "Simvastatin", "HARD_BLOCK", "Strong CYP3A4 inhibition.", "Life-threatening rhabdomyolysis.", "Avoid combination; choose non-CYP3A4 macrolide."),
    ("Warfarin", "Trimethoprim-Sulfamethoxazole", "SEVERE", "CYP2C9 inhibition and gut flora change.", "Marked INR elevation and bleeding.", "Avoid or preemptively reduce warfarin with close INR."),
    ("Warfarin", "Amiodarone", "SEVERE", "CYP inhibition increases warfarin effect.", "Bleeding risk.", "Reduce warfarin and monitor INR."),
    ("Warfarin", "Aspirin", "SEVERE", "Additive anticoagulant/antiplatelet effect.", "Major bleeding.", "Use only if compelling indication."),
    ("Apixaban", "Clarithromycin", "SEVERE", "P-gp/CYP3A4 inhibition.", "Increased anticoagulant exposure.", "Avoid or adjust per protocol."),
    ("Rivaroxaban", "Clarithromycin", "SEVERE", "P-gp/CYP3A4 inhibition.", "Increased bleeding risk.", "Prefer azithromycin or alternative."),
    ("Lisinopril", "Spironolactone", "SEVERE", "Additive potassium retention.", "Hyperkalemia.", "Avoid in high-risk CKD; monitor K closely."),
    ("Losartan", "Spironolactone", "SEVERE", "Additive potassium retention.", "Hyperkalemia.", "Avoid in high-risk CKD; monitor K closely."),
    ("Lisinopril", "Ibuprofen", "MODERATE", "Afferent/efferent renal hemodynamic effect.", "AKI risk.", "Avoid NSAIDs; monitor renal function."),
    ("Losartan", "Ibuprofen", "MODERATE", "Renal hemodynamic interaction.", "AKI risk.", "Avoid NSAIDs; monitor renal function."),
    ("Telmisartan", "Diclofenac", "MODERATE", "ARB plus NSAID reduces renal autoregulation; risk is higher with dehydration or diuretics.", "Acute kidney injury and hyperkalemia risk.", "Avoid NSAID exposure and monitor creatinine/potassium if already taken."),
    ("Furosemide", "Ibuprofen", "MODERATE", "NSAID blunts diuretic effect.", "Fluid retention and renal injury.", "Use acetaminophen when possible."),
    ("Aspirin", "Ibuprofen", "MODERATE", "Competitive COX-1 binding and additive NSAID toxicity.", "Reduced aspirin cardioprotection and increased GI/renal toxicity.", "Avoid routine combination; separate dosing only if clinician-directed."),
    ("Digoxin", "Amiodarone", "SEVERE", "P-gp inhibition raises digoxin levels.", "Digoxin toxicity.", "Reduce digoxin dose and monitor levels."),
    ("Digoxin", "Clarithromycin", "SEVERE", "P-gp inhibition and gut flora effect.", "Digoxin toxicity.", "Avoid or monitor level closely."),
    ("Metformin", "Ciprofloxacin", "MODERATE", "Fluoroquinolones alter glycemic control.", "Hypo/hyperglycemia.", "Monitor glucose."),
    ("Citalopram", "Clarithromycin", "SEVERE", "Additive QT prolongation.", "Torsades de pointes.", "Avoid combination; ECG if unavoidable."),
    ("Amiodarone", "Levofloxacin", "SEVERE", "Additive QT prolongation.", "Torsades de pointes.", "Avoid or monitor ECG/electrolytes."),
    ("Amiodarone", "Azithromycin", "MODERATE", "Additive QT prolongation.", "Arrhythmia risk.", "Monitor ECG and electrolytes."),
    ("Sertraline", "Tramadol", "SEVERE", "Serotonergic synergy.", "Serotonin syndrome and seizures.", "Avoid or choose non-serotonergic analgesic."),
    ("Fluoxetine", "Tramadol", "SEVERE", "Serotonergic synergy and CYP2D6 inhibition.", "Serotonin syndrome; reduced analgesia.", "Avoid combination."),
    ("Gabapentin", "Oxycodone", "MODERATE", "Additive CNS/respiratory depression.", "Sedation and respiratory depression.", "Use lowest doses and monitor."),
    ("Pregabalin", "Oxycodone", "MODERATE", "Additive CNS depression.", "Sedation and falls.", "Use caution and monitor."),
    ("Colchicine", "Clarithromycin", "HARD_BLOCK", "CYP3A4/P-gp inhibition sharply raises colchicine.", "Fatal colchicine toxicity.", "Contraindicated."),
    ("Allopurinol", "Amoxicillin", "MODERATE", "Immune-mediated rash risk increased.", "Severe rash risk.", "Counsel and monitor; consider alternative."),
    ("Phenytoin", "Warfarin", "MODERATE", "Complex CYP/protein binding interaction.", "INR instability.", "Monitor INR and phenytoin levels."),
    ("Carbamazepine", "Apixaban", "SEVERE", "Strong CYP3A4/P-gp induction lowers DOAC.", "Thromboembolism risk.", "Avoid combination."),
    ("Carbamazepine", "Rivaroxaban", "SEVERE", "Strong CYP3A4/P-gp induction lowers DOAC.", "Thromboembolism risk.", "Avoid combination."),
    ("Diltiazem", "Simvastatin", "SEVERE", "CYP3A4 inhibition.", "Myopathy/rhabdomyolysis.", "Limit simvastatin dose or switch statin."),
    ("Omeprazole", "Clopidogrel", "MODERATE", "CYP2C19 inhibition reduces activation.", "Reduced antiplatelet effect.", "Prefer pantoprazole."),
]

INTERACTIONS = [
    {
        "id": idx + 1,
        "drug_a_normalized": normalize_drug_name(a),
        "drug_b_normalized": normalize_drug_name(b),
        "severity": sev,
        "mechanism": mech,
        "clinical_effect": effect,
        "management": mgmt,
    }
    for idx, (a, b, sev, mech, effect, mgmt) in enumerate(INTERACTIONS)
]

ALLERGY_CROSS_REACTIVITY = [
    ("penicillin", "penicillin antibiotic", 100, "Avoid penicillins in true anaphylaxis; use specialist-guided alternative."),
    ("penicillin", "cephalosporin antibiotic", 2, "Assess reaction history; avoid high-risk beta-lactams in anaphylaxis."),
    ("cephalosporin", "penicillin antibiotic", 2, "Assess side-chain similarity and reaction severity."),
    ("sulfonamide", "sulfonamide antibiotic", 100, "Avoid sulfonamide antibiotics after severe sulfa reaction."),
    ("macrolide", "macrolide antibiotic", 100, "Avoid class rechallenge after serious immediate reaction."),
    ("fluoroquinolone", "fluoroquinolone antibiotic", 100, "Avoid fluoroquinolone class after severe reaction."),
    ("nsaid", "nsaid", 80, "Avoid nonselective NSAIDs in cross-reactive NSAID hypersensitivity."),
    ("opioid", "opioid analgesic", 20, "Differentiate intolerance from allergy; monitor if alternative opioid used."),
]

ALLERGY_CROSS_REACTIVITY = [
    {"id": idx + 1, "allergy_class": a, "cross_reacts_with": b, "cross_reactivity_pct": pct, "guidance": g}
    for idx, (a, b, pct, g) in enumerate(ALLERGY_CROSS_REACTIVITY)
]
