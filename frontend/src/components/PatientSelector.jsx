import { Users } from "lucide-react";

export default function PatientSelector({ patients, selectedId, onSelect }) {
  return (
    <div className="monitor-panel p-4">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-100">
        <Users size={16} className="text-clinical-cyan" />
        Patient Registry
      </div>
      <select
        value={selectedId || ""}
        onChange={(event) => onSelect(event.target.value)}
        className="w-full rounded-md border border-clinical-line bg-slate-950/80 px-3 py-2 text-sm text-slate-100 outline-none transition focus:border-clinical-cyan"
      >
        {patients.map((patient) => (
          <option key={patient.id} value={patient.id}>
            {patient.id} - {patient.name}
          </option>
        ))}
      </select>
    </div>
  );
}
