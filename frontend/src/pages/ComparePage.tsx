import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { GitCompare } from 'lucide-react'
import { compareProperties } from '../api/ai'
import { formatApiError, formatMoney, saleTypeLabel } from '../lib/format'
import { useAuth } from '../context/AuthContext'
import { useFavorites } from '../context/FavoritesContext'

function parseIds(s: string): number[] {
  return s
    .split(/[\s,;]+/)
    .map((x) => Number(x.trim()))
    .filter((n) => Number.isFinite(n) && n > 0)
}

export function ComparePage() {
  const { user } = useAuth()
  const { ids, favorites, loading: favLoading } = useFavorites()
  const [raw, setRaw] = useState('')
  const [result, setResult] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const parsedIds = useMemo(() => parseIds(raw), [raw])

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
    setError(null)
  }

  const toggleFavoriteInCompare = (propertyId: number) => {
    const cur = parseIds(raw)
    let next: number[]
    if (cur.includes(propertyId)) {
      next = cur.filter((x) => x !== propertyId)
    } else {
      if (cur.length >= 3) {
        setError('Для порівняння можна обрати не більше 3 об’єктів. Зніміть позначку або приберіть ID з поля.')
        return
      }
      next = [...cur, propertyId]
    }
    setError(null)
    setRaw(next.join(', '))
  }

  const checkboxDisabled = (propertyId: number) =>
    !parsedIds.includes(propertyId) && parsedIds.length >= 3

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <div className="flex items-center gap-2">
        <GitCompare className="h-8 w-8 text-brand" />
        <h1 className="font-display text-3xl font-semibold text-slate-900">
          Порівняння об’єктів
        </h1>
      </div>
      <p className="mt-2 text-slate-600">
        Введіть від 2 до 3 ідентифікаторів оголошень або підставте з обраного. Нижче можна швидко
        обрати улюблені картки чекбоксами.
      </p>

      <form onSubmit={(e) => void onSubmit(e)} className="mt-8 space-y-4">
        <div>
          <label className="text-sm font-medium text-slate-700">ID об’єктів</label>
          <input
            value={raw}
            onChange={(e) => {
              setRaw(e.target.value)
              setError(null)
            }}
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

      <section className="mt-12 border-t border-slate-200 pt-8">
        <h2 className="text-lg font-semibold text-slate-900">Улюблені — швидкий вибір</h2>
        {!user ? (
          <p className="mt-3 text-sm text-slate-600">
            <Link to="/login" className="text-brand-dark underline">
              Увійдіть
            </Link>
            , щоб бачити обрані оголошення тут.
          </p>
        ) : favLoading ? (
          <p className="mt-4 text-sm text-slate-500">Завантаження обраного…</p>
        ) : favorites.length === 0 ? (
          <p className="mt-3 text-sm text-slate-600">
            Поки немає улюблених. Додайте їх зі сторінки оголошення або зі{' '}
            <Link to="/favorites" className="text-brand-dark underline">
              списку обраного
            </Link>
            .
          </p>
        ) : (
          <>
            <p className="mt-2 text-sm text-slate-600">
              Позначте до 3 об’єктів — ID підставляться у поле вище. Можна комбінувати з
              довільними ID у полі.
            </p>
            <ul className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
              {favorites.map((p) => {
                const checked = parsedIds.includes(p.id)
                const disabled = checkboxDisabled(p.id)
                const thumb =
                  p.main_photo ||
                  'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=200&q=80'
                return (
                  <li key={p.id}>
                    <div
                      className={`flex gap-3 rounded-2xl border bg-white p-3 shadow-sm transition ${
                        checked ? 'border-brand ring-1 ring-brand/25' : 'border-slate-100'
                      } ${disabled && !checked ? 'opacity-60' : ''}`}
                    >
                      <label className="flex shrink-0 cursor-pointer items-start pt-0.5">
                        <input
                          type="checkbox"
                          className="mt-1 h-4 w-4 rounded border-slate-300 text-brand focus:ring-brand/40"
                          checked={checked}
                          disabled={disabled}
                          onChange={() => toggleFavoriteInCompare(p.id)}
                          aria-label={`Обрати для порівняння: ${p.title}`}
                        />
                      </label>
                      <Link
                        to={`/properties/${p.id}`}
                        className="flex min-w-0 flex-1 gap-3 hover:opacity-90"
                      >
                        <img
                          src={thumb}
                          alt=""
                          className="h-16 w-20 shrink-0 rounded-xl object-cover"
                        />
                        <div className="min-w-0 flex-1">
                          <p className="line-clamp-2 text-sm font-medium text-slate-900">
                            {p.title}
                          </p>
                          <p className="mt-1 text-xs font-semibold text-brand-dark">
                            {formatMoney(p.price, p.currency)}
                          </p>
                          <p className="mt-0.5 text-xs text-slate-500">
                            #{p.id} · {saleTypeLabel(p.sale_type)}
                          </p>
                        </div>
                      </Link>
                    </div>
                  </li>
                )
              })}
            </ul>
          </>
        )}
      </section>
    </div>
  )
}
