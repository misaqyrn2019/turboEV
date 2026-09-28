import type { Bootstrap, Row, Value } from './types'
export const fa = (n: number | null | undefined, digits = 1) => n == null || !Number.isFinite(n) ? '—' : new Intl.NumberFormat('fa-IR', { maximumFractionDigits: digits }).format(n)
export function date(value: Value | undefined, withTime = false) {
  if (!value || typeof value !== 'string') return '—'
  const parsed = new Date(value.includes('T') && !/[Z+-]\d*:?\d*$/.test(value.slice(10)) ? value + '+03:30' : value)
  if (isNaN(parsed.getTime())) return value
  return new Intl.DateTimeFormat('fa-IR', { year: 'numeric', month: 'short', day: 'numeric', ...(withTime ? { hour: '2-digit', minute: '2-digit' } : {}), timeZone: 'Asia/Tehran' }).format(parsed)
}
export function epoch(value: Value | undefined) { return typeof value === 'string' && value ? new Date(value.includes('T') && !/(Z|[+-]\d\d:\d\d)$/.test(value) ? value+'+03:30' : value).getTime() : NaN }
export function dayKey(value: Value | undefined) { if(typeof value!=='string'||!value)return ''; if(!value.includes('T'))return value.slice(0,10);const ts=epoch(value);return Number.isFinite(ts)?new Date(ts).toLocaleDateString('en-CA',{timeZone:'Asia/Tehran'}):'' }
export const minutes = (a: Value, b: Value) => (epoch(b) - epoch(a)) / 60000
export const sum = (rows: Row[], key: string) => rows.reduce((s, r) => s + Number(r[key] || 0), 0)
export const mean = (rows: Row[], key: string) => { const valid = rows.filter(r => r[key] !== null && r[key] !== ''); return valid.length ? sum(valid, key) / valid.length : null }
export const label = (row?: Row) => row ? String(row.name || row.title || row.model || row.code) : '—'
export const norm = (s: string) => s.toLowerCase().replace(/ي/g, 'ی').replace(/ك/g, 'ک').replace(/[۰-۹]/g, d => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(d)))
export function centerOf(kind: string, row: Row, data: Bootstrap): string | null {
  if (kind === 'centers') return row.id
  if (row.center_id) return String(row.center_id)
  if (row.fleet_id) return String(data.records.fleets.find(f => f.id === row.fleet_id)?.center_id || '')
  if (row.vehicle_id) { const v = data.records.vehicles.find(v => v.id === row.vehicle_id); return v ? centerOf('vehicles', v, data) : null }
  return null
}
export function sla(row: Row, data: Bootstrap) {
  const threshold = Number(data.settings['sla_' + (row.priority || row.severity) + '_minutes'] || 120)
  const elapsed = (Number.isFinite(epoch(row.responded_at)) ? epoch(row.responded_at) : Date.now()) - epoch(row.reported_at)
  return { elapsed: elapsed / 60000, threshold, met: elapsed <= threshold * 60000, answered: !!row.responded_at }
}
export function localInputNow() {
  const d = new Date(Date.now() + 3.5 * 3600000)
  return d.toISOString().slice(0, 16)
}
