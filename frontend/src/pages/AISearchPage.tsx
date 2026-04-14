import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Search } from 'lucide-react'
import { semanticSearch } from '../api/ai'
import type { SemanticSearchResult } from '../api/types'
import { formatApiError } from '../lib/format'

export function AISearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SemanticSearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const q = query.trim()
    if (!q) return
    setLoading(true)
    setError(null)
    try {
      const data = await semanticSearch(q)
      setResults(data)
    } catch (err) {
      setError(formatApiError(err))
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="font-display text-3xl font-semibold text-slate-900">AI пошук</h1>
      <p className="mt-2 text-slate-600">
        Опишіть бажане словами — знайдемо найближчі за змістом оголошення.
      </p>

      <form onSubmit={(e) => void onSubmit(e)} className="mt-8 flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Наприклад: світла квартира з терасою біля парку"
          className="flex-1 rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-brand/30"
        />
        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-2xl bg-brand px-6 font-semibold text-white hover:bg-brand-dark disabled:opacity-60"
        >
          <Search className="h-5 w-5" />
          Шукати
        </button>
      </form>

      {error && (
        <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      )}

      <ul className="mt-8 space-y-4">
        {results.map((r) => (
          <li
            key={r.property_id}
            className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm"
          >
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <Link
                  to={`/properties/${r.property_id}`}
                  className="font-semibold text-slate-900 hover:text-brand-dark"
                >
                  {r.title}
                </Link>
                <p className="mt-1 text-xs text-slate-500">
                  Релевантність: {(r.similarity_score * 100).toFixed(1)}%
                </p>
              </div>
              <Link
                to={`/properties/${r.property_id}`}
                className="text-sm font-medium text-brand-dark underline"
              >
                Відкрити
              </Link>
            </div>
            <p className="mt-2 text-sm text-slate-600">{r.description}</p>
          </li>
        ))}
      </ul>

      {!loading && results.length === 0 && query && !error && (
        <p className="mt-8 text-center text-slate-500">Нічого не знайдено.</p>
      )}
    </div>
  )
}
