import { History } from "lucide-react";

export default function QueryHistory({ items }) {
  return (
    <div className="monitor-panel p-4">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-100">
        <History size={16} className="text-clinical-cyan" />
        Query History
      </div>
      <div className="space-y-2">
        {items.length === 0 ? (
          <div className="text-sm text-slate-500">No queries yet.</div>
        ) : (
          items.map((item) => (
            <div key={item.id} className="rounded-md border border-clinical-line bg-slate-950/40 p-2 text-xs text-slate-300">
              <div className="font-mono text-slate-500">{item.time}</div>
              <div className="mt-1">{item.query}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
