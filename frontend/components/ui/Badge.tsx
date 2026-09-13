export function Badge({ children, tone = 'slate' }: { children: React.ReactNode; tone?: string }) {
  return <span className={`badge badge-${tone.toLowerCase()}`}>{children}</span>
}
