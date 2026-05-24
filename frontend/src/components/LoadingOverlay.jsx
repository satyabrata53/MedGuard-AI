export default function LoadingOverlay({ show }) {
  if (!show) return null;
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/60 backdrop-blur-sm">
      <div className="monitor-panel px-6 py-5 text-center">
        <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-2 border-clinical-line border-t-clinical-cyan" />
        <div className="text-sm font-semibold text-slate-100">Running deterministic safety middleware</div>
        <div className="mt-1 text-xs text-slate-500">Cache lookup, allergy validation, renal rules, constrained AI</div>
      </div>
    </div>
  );
}
