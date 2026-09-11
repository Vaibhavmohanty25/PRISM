type StateKind = 'loading' | 'empty' | 'error' | 'unavailable' | 'info'

export function StatePanel({ kind, title, message, action }: { kind: StateKind; title: string; message: string; action?: React.ReactNode }) {
  return <section className={`state-panel state-${kind}`} role={kind === 'error' ? 'alert' : 'status'}>
    <div className="state-mark" aria-hidden="true">{kind === 'loading' ? '···' : kind === 'error' ? '!' : kind === 'unavailable' ? '—' : '•'}</div>
    <div><h3>{title}</h3><p>{message}</p>{action}</div>
  </section>
}
