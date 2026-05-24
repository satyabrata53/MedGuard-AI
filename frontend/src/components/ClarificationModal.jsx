import { HelpCircle } from "lucide-react";
import { useEffect, useState } from "react";

export default function ClarificationModal({ resolvedDrug, onConfirm, onClose }) {
  const candidates = resolvedDrug?.candidates || [];
  const open = ["needs_clarification", "clarify"].includes(resolvedDrug?.status) && candidates.length > 0;
  const [selected, setSelected] = useState("");

  useEffect(() => {
    setSelected(candidates[0] || "");
  }, [resolvedDrug?.message]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 px-4 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-lg border border-clinical-line bg-[#0b1220] p-5 shadow-monitor">
        <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-white">
          <HelpCircle size={17} className="text-amber-200" />
          Confirm Medication
        </div>
        <p className="mb-4 whitespace-pre-wrap text-sm leading-6 text-slate-300">
          {resolvedDrug.message || "Did you mean one of these validated medications?"}
        </p>
        <div className="space-y-2">
          {candidates.map((candidate) => (
            <label key={candidate} className="flex cursor-pointer items-center gap-3 rounded-md border border-clinical-line bg-slate-950/45 px-3 py-2 text-sm text-slate-100">
              <input
                type="radio"
                name="candidate"
                value={candidate}
                checked={selected === candidate}
                onChange={() => setSelected(candidate)}
                className="h-4 w-4 accent-cyan-300"
              />
              {candidate}
            </label>
          ))}
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <button type="button" onClick={onClose} className="rounded-md border border-clinical-line px-3 py-2 text-sm text-slate-300">
            Cancel
          </button>
          <button
            type="button"
            onClick={() => selected && onConfirm(selected)}
            className="rounded-md border border-clinical-cyan/40 bg-clinical-cyan/14 px-3 py-2 text-sm font-semibold text-cyan-50"
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
}
