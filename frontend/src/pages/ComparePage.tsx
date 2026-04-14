import { useState } from 'react'
import { Link } from 'react-router-dom'
import { GitCompare } from 'lucide-react'
import { compareProperties } from '../api/ai'
import { formatApiError } from '../lib/format'
import { useFavorites } from '../context/FavoritesContext'

export function ComparePage() {
  const { ids } = useFavorites()
  const [raw, setRaw] = useState('')
  const [result, setResult] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const parseIds = (s: string): number[] =>
    s
      .split(/[\s,;]+/)
      .map((x) => Number(x.trim()))
      .filter((n) => Number.isFinite(n))

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const list = parseIds(raw)
    if (list.length < 2 || list.length > 3) {
      setError('Вкажіть 2–3 ID через кому або пробіл')
      return
    }
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await compareProperties(list)
      setResult(res.comparison)
    } catch (err) {
      setError(formatApiError(err))
    } finally {
      setLoading(false)
    }
  }

  const useFav = () => {
    const u = [...new Set(ids)].slice(0, 3)
    setRaw(u.join(', '))
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <div className="flex items-center gap-2">
        <GitCompare className="h-8 w-8 text-brand" />
        <h1 className="font-display text-3xl font-semibold text-slate-900">
          Порівняння об’єктів
        </h1>
      </div>
      <p className="mt-2 text-slate-600">
        Введіть від 2 до 3 ідентифікаторів оголошень або підставте з обраного.
      </p>

      <form onSubmit={(e) => void onSubmit(e)} className="mt-8 space-y-4">
        <div>
          <label className="text-sm font-medium text-slate-700">ID об’єктів</label>
          <input
            value={raw}
            onChange={(e) => setRaw(e.target.value)}
            className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none"
            placeholder="наприклад: 12, 15, 20"
          />
        </div>
        <div className="flex flex-wrap gap-3">
          <button
            type="submit"
            disabled={loading}
            className="rounded-2xl bg-accent px-6 py-2.5 font-semibold text-white hover:bg-accent-hover disabled:opacity-60"
          >
            {loading ? 'Порівняння…' : 'Порівняти'}
          </button>
          <button
            type="button"
            onClick={useFav}
            disabled={ids.length < 2}
            className="rounded-2xl border border-brand/40 px-6 py-2.5 text-sm font-semibold text-brand-dark hover:bg-brand/5 disabled:opacity-40"
          >
            З обраного ({ids.length})
          </button>
        </div>
      </form>

      {error && (
        <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-8 rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
          <h2 className="font-semibold text-slate-900">Висновок AI</h2>
          <p className="mt-4 whitespace-pre-wrap text-slate-700">{result}</p>
          <p className="mt-6 text-sm text-slate-500">
            Перейти до карток:{' '}
            {parseIds(raw).map((id) => (
              <span key={id}>
                <Link to={`/properties/${id}`} className="text-brand-dark underline">
                  #{id}
                </Link>{' '}
              </span>
            ))}
          </p>
        </div>
      )}
    </div>
  )
}
