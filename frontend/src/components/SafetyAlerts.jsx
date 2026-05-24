import { HelpCircle, OctagonAlert, ShieldCheck } from "lucide-react";
import SeverityBadge from "./SeverityBadge.jsx";

export default function SafetyAlerts({ alerts, resolvedDrug, onCandidateSelect }) {
  const groupedAlerts = groupAlerts(alerts);
  const candidateList = resolvedDrug?.candidates || [];
  const needsClarification = ["needs_clarification", "clarify"].includes(resolvedDrug?.status) && candidateList.length > 0;

  return (
    <div className="monitor-panel p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-100">
          <OctagonAlert size={16} className="text-clinical-red" />
          Safety Alerts
        </div>
        <span className="font-mono text-xs text-slate-400">{alerts.length} signals</span>
      </div>

      {resolvedDrug && (
        <div className="mb-3 rounded-md border border-clinical-line bg-slate-950/40 p-3 text-sm">
          <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Resolved medication</div>
          <div className="mt-1 text-slate-100">
            {resolvedDrug.resolved_name || resolvedDrug.input}
            <span className="ml-2 font-mono text-xs text-slate-500">{Math.round((resolvedDrug.confidence || 0) * 100)}%</span>
          </div>
          {resolvedDrug.confidence_explanation && <div className="mt-2 text-xs leading-5 text-slate-400">{resolvedDrug.confidence_explanation}</div>}
          {resolvedDrug.message && <div className="mt-2 text-amber-100">{resolvedDrug.message}</div>}
          {needsClarification && (
            <div className="mt-3 rounded-md border border-amber-300/30 bg-amber-400/10 p-3">
              <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-amber-100">
                <HelpCircle size={14} />
                Confirm medication
              </div>
              <div className="flex flex-wrap gap-2">
                {candidateList.map((candidate) => (
                  <button
                    type="button"
                    key={candidate}
                    onClick={() => onCandidateSelect?.(candidate)}
                    className="rounded border border-clinical-line bg-slate-950/70 px-2 py-1 text-xs text-slate-200 transition hover:border-clinical-cyan hover:text-white"
                    title={`Use ${candidate} as the confirmed medication`}
                  >
                    {candidate}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="space-y-3">
        {alerts.length === 0 ? (
          <div className="flex items-center gap-2 rounded-md border border-green-300/30 bg-green-400/10 p-3 text-sm text-green-100">
            <ShieldCheck size={16} />
            No deterministic safety alerts detected.
          </div>
        ) : (
          Object.entries(groupedAlerts).map(([severity, items]) => (
            <section key={severity} className="space-y-2">
              <div className="flex items-center justify-between border-b border-clinical-line pb-2">
                <SeverityBadge severity={severity} />
                <span className="font-mono text-xs text-slate-500">{items.length} alerts</span>
              </div>
              {items.map((alert, index) => (
                <article key={`${alert.title}-${index}`} className={`rounded-md border p-3 ${panelTone(alert.severity)}`}>
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-slate-500">{alert.type.replaceAll("_", " ")}</span>
                    <span className="font-mono text-xs text-slate-500">I={alert.importance}</span>
                  </div>
                  <h3 className="text-sm font-semibold text-white">{alert.title}</h3>
                  <p className="mt-2 text-xs leading-5 text-slate-300">{alert.mechanism}</p>
                  <p className="mt-2 whitespace-pre-wrap text-xs leading-5 text-slate-100">{alert.recommendation}</p>
                </article>
              ))}
            </section>
          ))
        )}
      </div>
    </div>
  );
}

function groupAlerts(alerts) {
  const order = ["HARD_BLOCK", "SEVERE", "MODERATE", "MINOR"];
  return order.reduce((groups, severity) => {
    const items = alerts.filter((alert) => alert.severity === severity);
    if (items.length) groups[severity] = items;
    return groups;
  }, {});
}

function panelTone(severity) {
  if (severity === "HARD_BLOCK") return "border-red-400/50 bg-red-500/12";
  if (severity === "SEVERE") return "border-red-300/35 bg-red-500/8";
  if (severity === "MODERATE") return "border-amber-300/35 bg-amber-400/10";
  return "border-clinical-line bg-slate-950/48";
}
