import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { PropertyCard } from '../components/PropertyCard'
import { useFavorites } from '../context/FavoritesContext'

export function FavoritesPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const { favorites, loading, remove } = useFavorites()

  if (!user) {
    return (
      <div className="mx-auto max-w-lg px-4 py-24 text-center">
        <h1 className="font-display text-2xl font-semibold text-slate-900">Обране</h1>
        <p className="mt-3 text-slate-600">
          Увійдіть, щоб зберігати обране на сервері та відкривати його з будь-якого пристрою.
        </p>
        <button
          type="button"
          onClick={() => navigate('/login', { state: { from: { pathname: '/favorites' } } })}
          className="mt-8 rounded-2xl bg-brand px-8 py-3 font-semibold text-white hover:bg-brand-dark"
        >
          Увійти
        </button>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <h1 className="font-display text-3xl font-semibold text-slate-900">Обране</h1>
      <p className="mt-2 text-slate-600">
        Зберігається в акаунті на сервері.{' '}
        <Link to="/compare" className="text-brand-dark underline">
          Порівняти об’єкти
        </Link>
      </p>

      {loading ? (
        <div className="mt-16 text-center text-slate-500">Завантаження…</div>
      ) : favorites.length === 0 ? (
        <p className="mt-16 text-center text-slate-500">
          Поки порожньо. Додайте сердечком зі списку або картки оголошення.
        </p>
      ) : (
        <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {favorites.map((p) => (
            <div key={p.id}>
              <PropertyCard property={p} />
              <button
                type="button"
                onClick={() => void remove(p.id)}
                className="mt-2 w-full rounded-xl border border-slate-200 py-2 text-sm text-slate-600 hover:bg-slate-50"
              >
                Прибрати з обраного
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
