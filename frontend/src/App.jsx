import { useEffect, useMemo, useState } from "react";
import { Activity, Database, ServerCog, Shield } from "lucide-react";

import ClinicalScores from "./components/ClinicalScores.jsx";
import ClarificationModal from "./components/ClarificationModal.jsx";
import LoadingOverlay from "./components/LoadingOverlay.jsx";
import PatientCard from "./components/PatientCard.jsx";
import PatientSelector from "./components/PatientSelector.jsx";
import QueryHistory from "./components/QueryHistory.jsx";
import QuestionInput from "./components/QuestionInput.jsx";
import ResponseComparison from "./components/ResponseComparison.jsx";
import SafetyAlerts from "./components/SafetyAlerts.jsx";
import { api } from "./lib/api.js";

export default function App() {
  const [patients, setPatients] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [query, setQuery] = useState("Can I add clarithro?");
  const [proposedDrug, setProposedDrug] = useState("");
  const [alerts, setAlerts] = useState([]);
  const [scores, setScores] = useState({});
  const [intent, setIntent] = useState("");
  const [reviewSummary, setReviewSummary] = useState({});
  const [whySafeChanged, setWhySafeChanged] = useState([]);
  const [resolvedDrug, setResolvedDrug] = useState(null);
  const [genericResponse, setGenericResponse] = useState("");
  const [safeResponse, setSafeResponse] = useState("");
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.patients()
      .then((data) => {
        setPatients(data);
        setSelectedId(data[0]?.id || "");
      })
      .catch((err) => setError(err.message));
  }, []);

  const selectedPatient = useMemo(
    () => patients.find((patient) => patient.id === selectedId),
    [patients, selectedId]
  );

  async function runAnalysis(event, confirmedDrug = null) {
    event?.preventDefault();
    if (!selectedPatient || !query.trim()) return;
    setLoading(true);
    setError("");
    try {
      const safety = await api.safetyCheck({
        patient: selectedPatient,
        query,
        proposed_drug: confirmedDrug || proposedDrug.trim() || null,
      });
      setAlerts(safety.alerts);
      setScores(safety.scores);
      setIntent(safety.intent);
      setReviewSummary(safety.review_summary || {});
      setWhySafeChanged(safety.why_safe_ai_changed || []);
      setResolvedDrug(safety.resolved_drug);

      const aiPayload = {
        patient: selectedPatient,
        query,
        alerts: safety.alerts,
        scores: safety.scores,
        constraints: safety.constraints,
      };
      const [generic, safe] = await Promise.all([
        api.askGeneric(aiPayload),
        api.askSafe(aiPayload),
      ]);
      setGenericResponse(generic.response);
      setSafeResponse(safe.response);
      setHistory((items) => [
        { id: crypto.randomUUID(), query, time: new Date().toLocaleTimeString() },
        ...items.slice(0, 5),
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen px-4 py-4 sm:px-6 lg:px-8">
      <LoadingOverlay show={loading} />
      <ClarificationModal
        resolvedDrug={resolvedDrug}
        onClose={() => setResolvedDrug((current) => (current ? { ...current, candidates: [] } : current))}
        onConfirm={(candidate) => {
          setProposedDrug(candidate);
          setResolvedDrug((current) => (current ? { ...current, candidates: [] } : current));
          setQuery((current) => current || `Can I use ${candidate}?`);
          runAnalysis(null, candidate);
        }}
      />
      <header className="mb-4 flex flex-col gap-4 border-b border-clinical-line pb-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2 font-mono text-xs uppercase tracking-[0.24em] text-clinical-cyan">
            <Shield size={15} />
            Deterministic Clinical Safety Middleware
          </div>
          <h1 className="text-2xl font-semibold text-white sm:text-3xl">MedGuard AI Clinical Drug Safety Engine</h1>
        </div>
        <div className="grid grid-cols-3 gap-2 text-xs text-slate-300 sm:min-w-[460px]">
          <Status icon={Database} label="DB Truth" value="Validated" />
          <Status icon={ServerCog} label="Lookup" value="O(1)" />
          <Status icon={Activity} label="Mode" value="Constrained" />
        </div>
      </header>

      {error && (
        <div className="mb-4 rounded-md border border-red-400/40 bg-red-500/12 p-3 text-sm text-red-100">
          {error}
        </div>
      )}

      <div className="grid gap-4 xl:grid-cols-[320px_minmax(420px,0.95fr)_minmax(460px,1.25fr)]">
        <aside className="space-y-4">
          <PatientSelector patients={patients} selectedId={selectedId} onSelect={setSelectedId} />
          <PatientCard patient={selectedPatient} />
        </aside>

        <section className="space-y-4">
          <QuestionInput
            query={query}
            setQuery={setQuery}
            proposedDrug={proposedDrug}
            setProposedDrug={setProposedDrug}
            onSubmit={runAnalysis}
            loading={loading}
          />
          <SafetyAlerts
            alerts={alerts}
            resolvedDrug={resolvedDrug}
            onCandidateSelect={(candidate) => {
              setProposedDrug(candidate);
              setQuery((current) => current || `Can I use ${candidate}?`);
            }}
          />
          <ClinicalScores scores={scores} intent={intent} reviewSummary={reviewSummary} />
          <QueryHistory items={history} />
        </section>

        <section className="space-y-4">
          <ResponseComparison genericResponse={genericResponse} safeResponse={safeResponse} whySafeChanged={whySafeChanged} />
          <div className="monitor-panel overflow-hidden p-4">
            <div className="mb-3 text-sm font-semibold text-white">Safety Pipeline</div>
            <div className="grid gap-2 text-xs text-slate-300 md:grid-cols-4 xl:grid-cols-2 2xl:grid-cols-4">
              {["Resolver", "Interactions", "Allergy", "Renal", "Scores", "Constraints", "LLM", "Response"].map((step) => (
                <div key={step} className="rounded border border-clinical-line bg-slate-950/45 px-3 py-2 text-center font-mono">
                  {step}
                </div>
              ))}
            </div>
            <div className="signal-line mt-4 h-px w-full" />
          </div>
        </section>
      </div>
    </main>
  );
}

function Status({ icon: Icon, label, value }) {
  return (
    <div className="rounded-md border border-clinical-line bg-slate-950/45 p-3">
      <div className="flex items-center gap-2 text-slate-500">
        <Icon size={14} className="text-clinical-cyan" />
        {label}
      </div>
      <div className="mt-1 font-mono text-slate-100">{value}</div>
    </div>
  );
}
