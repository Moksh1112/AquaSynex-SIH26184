export function Stat({ label, value, detail, tone = 'cyan' }: { label: string; value: string | number; detail: string; tone?: string }) {
  return (
    <div className="stat">
      <div className="eyebrow">{label}</div>
      <div className={`stat-value text-${tone}`}>{value}</div>
      <div className="stat-detail">{detail}</div>
    </div>
  )
}
