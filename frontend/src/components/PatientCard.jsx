import { Activity, AlertTriangle, Beaker, HeartPulse, Pill } from "lucide-react";

function Section({ icon: Icon, title, children }) {
  return (
    <section className="border-t border-clinical-line pt-4">
      <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
        <Icon size={14} className="text-clinical-cyan" />
        {title}
      </div>
      {children}
    </section>
  );
}

export default function PatientCard({ patient }) {
  if (!patient) return null;
  return (
    <div className="monitor-panel space-y-4 p-4">
      <div>
        <div className="font-mono text-xs text-clinical-cyan">{patient.id}</div>
        <h2 className="mt-1 text-xl font-semibold text-white">{patient.name}</h2>
        <p className="text-sm text-slate-400">
          {patient.age} years / {patient.sex} / {patient.weight_kg || "--"} kg
        </p>
      </div>

      <Section icon={Activity} title="Clinical Summary">
        <div className="flex flex-wrap gap-2">
          {patient.diagnoses.map((item) => (
            <span key={item} className="rounded border border-clinical-line bg-slate-950/50 px-2 py-1 text-xs text-slate-200">
              {item}
            </span>
          ))}
        </div>
      </Section>

      <Section icon={Pill} title="Current Medications">
        <ul className="space-y-1 text-sm text-slate-200">
          {patient.medications.map((med) => <li key={med}>{med}</li>)}
        </ul>
      </Section>

      <Section icon={AlertTriangle} title="Allergies">
        <div className="text-sm text-red-100">{patient.allergies.length ? patient.allergies.join(", ") : "None listed"}</div>
      </Section>

      <Section icon={Beaker} title="Labs">
        <div className="grid grid-cols-2 gap-2">
          {Object.entries(patient.labs).map(([key, value]) => (
            <div key={key} className="rounded border border-clinical-line bg-slate-950/40 px-2 py-2">
              <div className="font-mono text-[10px] uppercase text-slate-500">{key}</div>
              <div className="font-mono text-sm text-slate-100">{String(value)}</div>
            </div>
          ))}
        </div>
      </Section>

      <Section icon={HeartPulse} title="Vitals">
        <div className="grid grid-cols-3 gap-2">
          {Object.entries(patient.vitals).map(([key, value]) => (
            <div key={key} className="rounded border border-clinical-line bg-slate-950/40 px-2 py-2 text-center">
              <div className="font-mono text-[10px] uppercase text-slate-500">{key}</div>
              <div className="font-mono text-sm text-clinical-green">{String(value)}</div>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}
