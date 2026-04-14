import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Sparkles } from 'lucide-react'
import { explainProperty } from '../api/ai'
import { formatApiError } from '../lib/format'

export function PropertyExplainPage() {
  const { id } = useParams<{ id: string }>()
  const pid = Number(id)
  const [prefs, setPrefs] = useState('')
  const [text, setText] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!Number.isFinite(pid)) return
    setLoading(true)
    setError(null)
    setText(null)
    try {
      const res = await explainProperty(pid, prefs.trim() || undefined)
      setText(res.explanation)
    } catch (err) {
      setError(formatApiError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <Link to={`/properties/${id}`} className="text-sm text-brand-dark underline">
        ← До оголошення
      </Link>
      <div className="mt-6 flex items-center gap-2">
        <Sparkles className="h-8 w-8 text-brand" />
        <h1 className="font-display text-2xl font-semibold text-slate-900">
          AI пояснення для об’єкта #{id}
        </h1>
      </div>

      <form onSubmit={(e) => void onSubmit(e)} className="mt-8 space-y-4">
        <div>
          <label className="text-sm font-medium text-slate-700">
            Ваші побажання (необов’язково)
          </label>
          <textarea
            value={prefs}
            onChange={(e) => setPrefs(e.target.value)}
            rows={3}
            className="mt-1 w-full rounded-2xl border border-slate-200 px-3 py-2 text-sm outline-none"
            placeholder="Наприклад: сім’я з дитиною, важлива транспортна доступність…"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="rounded-2xl bg-brand px-6 py-2.5 font-semibold text-white hover:bg-brand-dark disabled:opacity-60"
        >
          {loading ? 'Аналіз…' : 'Отримати пояснення'}
        </button>
      </form>

      {error && (
        <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      )}

      {text && (
        <div className="mt-8 rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
          <h2 className="font-semibold text-slate-900">Результат</h2>
          <p className="mt-4 whitespace-pre-wrap text-slate-700">{text}</p>
        </div>
      )}
    </div>
  )
}
