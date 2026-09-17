export function PageHeader({ eyebrow, title, subtitle, action }: { eyebrow?: string; title: string; subtitle: string; action?: React.ReactNode }) {
  return (
    <div className="page-header">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      {action && <div>{action}</div>}
    </div>
  )
}
