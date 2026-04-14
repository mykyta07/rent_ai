import { Link, NavLink } from 'react-router-dom'
import { Heart, Home, Search, Sparkles, UserRound } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useFavorites } from '../context/FavoritesContext'

const navClass = ({ isActive }: { isActive: boolean }) =>
  [
    'rounded-full px-4 py-2 text-sm font-medium transition-colors',
    isActive ? 'bg-brand/10 text-brand-dark' : 'text-slate-600 hover:text-brand-dark',
  ].join(' ')

export function Navbar() {
  const { user, logout } = useAuth()
  const { ids } = useFavorites()

  return (
    <header className="sticky top-0 z-40 px-4 pt-4">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 rounded-full bg-white/90 px-4 py-3 shadow-nav backdrop-blur-md">
        <Link to="/" className="flex items-center gap-2">
          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-brand text-white shadow-md">
            <Home className="h-5 w-5" strokeWidth={2} />
          </span>
          <span className="font-display text-lg font-semibold text-slate-900">
            RentAI
          </span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          <NavLink to="/properties?sale_type=sale" className={navClass}>
            Купити
          </NavLink>
          <NavLink to="/properties?sale_type=rent" className={navClass}>
            Орендувати
          </NavLink>
          <NavLink to="/properties" className={navClass}>
            Пошук
          </NavLink>
          <NavLink to="/ai/search" className={navClass}>
            AI пошук
          </NavLink>
        </nav>

        <div className="flex items-center gap-2">
          <Link
            to="/properties"
            className="hidden rounded-full p-2 text-slate-500 hover:bg-slate-100 hover:text-brand-dark sm:inline-flex"
            aria-label="Пошук"
          >
            <Search className="h-5 w-5" />
          </Link>
          <Link
            to="/favorites"
            className="relative rounded-full p-2 text-slate-500 hover:bg-slate-100 hover:text-brand-dark"
            aria-label="Обране"
          >
            <Heart className="h-5 w-5" />
            {ids.length > 0 && (
              <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-accent px-1 text-[10px] font-bold text-white">
                {ids.length > 9 ? '9+' : ids.length}
              </span>
            )}
          </Link>
          <Link
            to="/ai/chat"
            className="hidden rounded-full p-2 text-brand hover:bg-brand/10 sm:inline-flex"
            aria-label="AI чат"
          >
            <Sparkles className="h-5 w-5" />
          </Link>

          {user ? (
            <div className="flex items-center gap-2">
              <Link
                to="/profile"
                className="rounded-full border border-brand/40 px-3 py-2 text-sm font-medium text-brand-dark hover:bg-brand/5"
              >
                Профіль
              </Link>
              <button
                type="button"
                onClick={() => void logout()}
                className="rounded-full px-3 py-2 text-sm text-slate-500 hover:bg-slate-100"
              >
                Вийти
              </button>
            </div>
          ) : (
            <Link
              to="/login"
              className="inline-flex items-center gap-2 rounded-full border-2 border-brand px-4 py-2 text-sm font-semibold text-brand-dark transition-colors hover:bg-brand/10"
            >
              <UserRound className="h-4 w-4" />
              Увійти
            </Link>
          )}
        </div>
      </div>
    </header>
  )
}
