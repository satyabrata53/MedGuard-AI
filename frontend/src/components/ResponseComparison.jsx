import { Bot, GitCompareArrows, LockKeyhole } from "lucide-react";

function ResponsePane({ title, icon: Icon, tone, response }) {
  return (
    <div className="min-h-[260px] rounded-md border border-clinical-line bg-slate-950/48 p-4">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-100">
        <Icon size={16} className={tone} />
        {title}
      </div>
      <p className="whitespace-pre-wrap text-sm leading-6 text-slate-200">
        {response || "Awaiting analysis."}
      </p>
    </div>
  );
}

export default function ResponseComparison({ genericResponse, safeResponse, whySafeChanged = [] }) {
  return (
    <div className="monitor-panel p-4">
      <div className="mb-4">
        <div className="text-sm font-semibold text-white">AI Response Comparison</div>
        <div className="mt-1 text-xs text-slate-500">Generic output versus deterministic-constraint protected output</div>
      </div>
      <div className="grid gap-3 xl:grid-cols-2">
        <ResponsePane title="Generic AI" icon={Bot} tone="text-amber-300" response={genericResponse} />
        <ResponsePane title="Safe AI" icon={LockKeyhole} tone="text-clinical-green" response={safeResponse} />
      </div>
      <div className="mt-3 rounded-md border border-clinical-line bg-slate-950/45 p-3">
        <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-100">
          <GitCompareArrows size={15} className="text-clinical-cyan" />
          Why Safe AI Differed
        </div>
        {whySafeChanged.length ? (
          <div className="flex flex-wrap gap-2">
            {whySafeChanged.map((reason) => (
              <span key={reason} className="rounded border border-clinical-line bg-slate-900/80 px-2 py-1 text-xs text-slate-200">
                {reason}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-500">No deterministic constraint has changed the response yet.</p>
        )}
      </div>
    </div>
  );
}
