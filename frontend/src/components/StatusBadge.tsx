const words = (value: string) => value.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')

export function StatusBadge({ value, tone = 'neutral' }: { value: string | null | undefined; tone?: string }) {
  const label = value ? words(value) : 'Not available'
  return <span className={`badge badge-${tone} badge-${value ?? 'empty'}`}>{label}</span>
}

export function toneFor(value: string | null | undefined): string {
  if (!value) return 'neutral'
  if (['high', 'investigate', 'declining'].includes(value)) return 'danger'
  if (['medium', 'review', 'variable', 'stalled', 'insufficient_data', 'review_only'].includes(value)) return 'warning'
  if (['low', 'supported', 'available', 'stable', 'improving', 'monitor'].includes(value)) return 'success'
  return 'neutral'
}
