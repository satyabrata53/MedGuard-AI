import { Activity, Gauge, HeartPulse } from "lucide-react";

export default function ClinicalScores({ scores, intent, reviewSummary }) {
  return (
    <div className="monitor-panel p-4">
      <div className="mb-3 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-100">
          <Gauge size={16} className="text-clinical-cyan" />
          Deterministic Scores
        </div>
        {intent && <span className="rounded border border-clinical-line px-2 py-1 font-mono text-[10px] text-slate-400">{intent}</span>}
      </div>
      <div className="grid grid-cols-2 gap-3">
        <ScoreCard icon={Gauge} label="CKD-EPI 2021" value={scores?.ckd_epi_2021_egfr ?? "--"} tone="text-clinical-cyan" />
        <ScoreCard icon={HeartPulse} label="CHA2DS2-VASc" value={scores?.cha2ds2_vasc ?? "--"} tone="text-clinical-green" />
        <ScoreCard icon={Activity} label="Stroke risk/year" value={scores?.stroke_risk_pct_year != null ? `${scores.stroke_risk_pct_year}%` : "--"} tone="text-amber-200" />
        <div className="rounded-md border border-clinical-line bg-slate-950/45 p-3">
          <div className="font-mono text-[10px] uppercase text-slate-500">Renal status</div>
          <div className="mt-2 text-sm leading-5 text-slate-100">{scores?.renal_status ?? "--"}</div>
        </div>
      </div>
      {reviewSummary?.summary && (
        <div className="mt-3 rounded-md border border-clinical-line bg-slate-950/45 p-3 text-xs leading-5 text-slate-300">
          <span className="font-semibold text-slate-100">{reviewSummary.medications_reviewed} meds reviewed.</span>{" "}
          {reviewSummary.summary}
        </div>
      )}
    </div>
  );
}

function ScoreCard({ icon: Icon, label, value, tone }) {
  return (
    <div className="rounded-md border border-clinical-line bg-slate-950/45 p-3">
      <div className="flex items-center gap-2 font-mono text-[10px] uppercase text-slate-500">
        <Icon size={13} className={tone} />
        {label}
      </div>
      <div className={`mt-1 font-mono text-2xl ${tone}`}>{value}</div>
    </div>
  );
}
