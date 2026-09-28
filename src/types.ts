export type Value = string | number | boolean | null | string[]
export type Row = { id: string; code: string; created_at: string; updated_at: string; demo: boolean; [key: string]: Value }
export type Field = { key: string; label: string; type: string; required?: boolean; default?: Value; min?: number; max?: number; source?: string; options?: { value: string; label: string }[] }
export type Module = { label: string; singular: string; icon: string; description: string; fields: Field[]; columns: string[] }
export type User = { id: string; name: string; username: string; role: string; active?: boolean }
export type Bootstrap = { catalog: Record<string, Module>; records: Record<string, Row[]>; settings: Record<string, Value>; permissions: string[]; roles: Record<string, string>; demo_count: number; server_time: string }
export type Notify = (message: string, error?: boolean) => void
