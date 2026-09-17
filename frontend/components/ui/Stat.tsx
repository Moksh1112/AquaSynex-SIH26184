export function Stat({ label, value, detail, tone = 'cyan', className = '', style }: { label: string; value: string | number; detail: string; tone?: string; className?: string; style?: React.CSSProperties }) {
  return (
    <div className={`stat ${className}`} style={style}>
      <div className="eyebrow">{label}</div>
      <div className={`stat-value text-${tone}`}>{value}</div>
      <div className="stat-detail">{detail}</div>
    </div>
  )
}
