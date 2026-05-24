import { ShieldCheck, Send } from "lucide-react";

export default function QuestionInput({ query, setQuery, proposedDrug, setProposedDrug, onSubmit, loading }) {
  return (
    <form onSubmit={onSubmit} className="monitor-panel p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-100">
          <ShieldCheck size={16} className="text-clinical-green" />
          Deterministic Safety Check
        </div>
        <div className="h-2 w-2 rounded-full bg-clinical-green shadow-[0_0_18px_rgba(51,214,159,0.9)]" />
      </div>
      <textarea
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Can I add clarithro for this patient?"
        rows={4}
        className="w-full resize-none rounded-md border border-clinical-line bg-slate-950/80 px-3 py-3 text-sm text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-clinical-cyan"
      />
      <div className="mt-3 grid gap-3 sm:grid-cols-[1fr_auto]">
        <input
          value={proposedDrug}
          onChange={(event) => setProposedDrug(event.target.value)}
          placeholder="Optional medication field"
          className="rounded-md border border-clinical-line bg-slate-950/80 px-3 py-2 text-sm text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-clinical-cyan"
        />
        <button
          disabled={loading || !query.trim()}
          className="inline-flex items-center justify-center gap-2 rounded-md border border-clinical-cyan/40 bg-clinical-cyan/14 px-4 py-2 text-sm font-semibold text-cyan-50 transition hover:bg-clinical-cyan/22 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Send size={16} />
          Analyze
        </button>
      </div>
    </form>
  );
}
