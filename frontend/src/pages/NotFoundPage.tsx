import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
      <p className="text-6xl font-bold text-slate-200">404</p>
      <h1 className="mt-4 font-display text-2xl font-semibold text-slate-900">
        Сторінку не знайдено
      </h1>
      <p className="mt-2 text-slate-600">Перевірте адресу або поверніться на головну.</p>
      <Link
        to="/"
        className="mt-8 rounded-2xl bg-brand px-8 py-3 font-semibold text-white hover:bg-brand-dark"
      >
        На головну
      </Link>
    </div>
  )
}
