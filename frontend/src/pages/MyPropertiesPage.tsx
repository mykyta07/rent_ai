import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Pencil, Trash2 } from 'lucide-react'
import { deleteProperty, fetchMyProperties } from '../api/properties'
import type { PropertyListItem } from '../api/types'
import { PropertyCard } from '../components/PropertyCard'
import { formatApiError } from '../lib/format'

export function MyPropertiesPage() {
  const [items, setItems] = useState<PropertyListItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchMyProperties()
      setItems(data)
    } catch (e) {
      setError(formatApiError(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const onDelete = async (id: number) => {
    if (!window.confirm('Видалити це оголошення?')) return
    try {
      await deleteProperty(id)
      setItems((prev) => prev.filter((p) => p.id !== id))
    } catch (e) {
      alert(formatApiError(e))
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-semibold text-slate-900">
            Мої оголошення
          </h1>
          <p className="mt-1 text-slate-600">Керуйте своїми картками на майданчику.</p>
        </div>
        <Link
          to="/properties/create"
          className="rounded-2xl bg-accent px-6 py-2.5 text-sm font-semibold text-white hover:bg-accent-hover"
        >
          + Створити
        </Link>
      </div>

      {error && (
        <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      )}

      {loading ? (
        <div className="mt-16 text-center text-slate-500">Завантаження…</div>
      ) : items.length === 0 ? (
        <p className="mt-16 text-center text-slate-500">
          Поки немає оголошень.{' '}
          <Link to="/properties/create" className="text-brand-dark underline">
            Створити перше
          </Link>
        </p>
      ) : (
        <div className="mt-10 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((p) => (
            <div key={p.id} className="relative">
              <PropertyCard property={p} />
              <div className="mt-3 flex gap-2">
                <Link
                  to={`/properties/${p.id}/edit`}
                  className="inline-flex flex-1 items-center justify-center gap-1 rounded-xl border border-brand/40 py-2 text-sm font-semibold text-brand-dark hover:bg-brand/5"
                >
                  <Pencil className="h-4 w-4" />
                  Редагувати
                </Link>
                <button
                  type="button"
                  onClick={() => void onDelete(p.id)}
                  className="inline-flex flex-1 items-center justify-center gap-1 rounded-xl border border-red-200 py-2 text-sm font-semibold text-red-700 hover:bg-red-50"
                >
                  <Trash2 className="h-4 w-4" />
                  Видалити
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
