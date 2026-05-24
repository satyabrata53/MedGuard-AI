const styles = {
  HARD_BLOCK: "border-red-400/50 bg-red-500/15 text-red-100",
  SEVERE: "border-red-300/40 bg-red-500/10 text-red-100",
  MODERATE: "border-amber-300/40 bg-amber-400/12 text-amber-100",
  MINOR: "border-blue-300/40 bg-blue-400/10 text-blue-100",
};

export default function SeverityBadge({ severity }) {
  return (
    <span className={`inline-flex items-center rounded border px-2 py-1 text-[11px] font-semibold tracking-wide ${styles[severity] || styles.MINOR}`}>
      {severity?.replace("_", " ")}
    </span>
  );
}
