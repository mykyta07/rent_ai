import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Home, Lock, Mail, User } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { formatApiError } from '../lib/format'

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await register({
        username,
        email,
        password,
        password_confirm: passwordConfirm,
        first_name: firstName,
        last_name: lastName,
      })
      navigate('/profile', { replace: true })
    } catch (err) {
      setError(formatApiError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <div className="flex flex-1 flex-col justify-center px-6 py-12 md:px-16 lg:px-24">
        <Link to="/" className="flex items-center gap-2">
          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-brand text-white">
            <Home className="h-5 w-5" />
          </span>
          <span className="font-display text-xl font-semibold text-slate-900">RentAI</span>
        </Link>
        <h1 className="mt-10 font-display text-3xl font-semibold text-slate-900 md:text-4xl">
          Створіть акаунт
        </h1>
        <p className="mt-3 max-w-md text-slate-600">
          Приєднуйтесь, щоб зберігати об’єкти та отримувати AI-рекомендації.
        </p>

        <div className="mt-8 flex gap-3">
          <button
            type="button"
            disabled
            className="flex-1 rounded-2xl border border-slate-200 py-3 text-sm font-medium text-slate-400"
          >
            Google (незабаром)
          </button>
          <button
            type="button"
            disabled
            className="flex-1 rounded-2xl border border-slate-200 bg-brand/10 py-3 text-sm font-medium text-slate-400"
          >
            GitHub (незабаром)
          </button>
        </div>
        <p className="my-6 text-center text-xs text-slate-400">або</p>

        <form onSubmit={(e) => void onSubmit(e)} className="max-w-md space-y-4">
          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
              {error}
            </div>
          )}
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="text-sm font-medium text-slate-700">Ім’я</label>
              <div className="mt-1 flex items-center gap-2 rounded-2xl border border-slate-200 px-3 py-2">
                <User className="h-5 w-5 text-slate-400" />
                <input
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  className="w-full bg-transparent text-sm outline-none"
                  placeholder="Ваше ім’я"
                />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700">Прізвище</label>
              <input
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                className="mt-1 w-full rounded-2xl border border-slate-200 px-3 py-2 text-sm outline-none"
                placeholder="Прізвище"
              />
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Username</label>
            <div className="mt-1 flex items-center gap-2 rounded-2xl border border-slate-200 px-3 py-2">
              <User className="h-5 w-5 text-slate-400" />
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-transparent text-sm outline-none"
                required
                autoComplete="username"
              />
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Email</label>
            <div className="mt-1 flex items-center gap-2 rounded-2xl border border-slate-200 px-3 py-2">
              <Mail className="h-5 w-5 text-slate-400" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-transparent text-sm outline-none"
                required
                autoComplete="email"
              />
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Пароль</label>
            <div className="mt-1 flex items-center gap-2 rounded-2xl border border-slate-200 px-3 py-2">
              <Lock className="h-5 w-5 text-slate-400" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-transparent text-sm outline-none"
                required
                autoComplete="new-password"
              />
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Підтвердження пароля</label>
            <div className="mt-1 flex items-center gap-2 rounded-2xl border border-slate-200 px-3 py-2">
              <Lock className="h-5 w-5 text-slate-400" />
              <input
                type="password"
                value={passwordConfirm}
                onChange={(e) => setPasswordConfirm(e.target.value)}
                className="w-full bg-transparent text-sm outline-none"
                required
                autoComplete="new-password"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-2xl bg-accent py-3.5 text-base font-semibold text-white shadow-lg shadow-accent/25 transition hover:bg-accent-hover disabled:opacity-60"
          >
            {loading ? 'Створення…' : 'Створити акаунт'}
          </button>
        </form>
        <p className="mt-8 text-center text-sm text-slate-600">
          Вже маєте акаунт?{' '}
          <Link to="/login" className="font-semibold text-brand-dark underline">
            Увійти
          </Link>
        </p>
      </div>
      <div className="relative flex flex-1 flex-col justify-center bg-gradient-to-b from-brand-dark to-sky-600 px-10 py-16 text-white md:px-16">
        <h2 className="text-center font-display text-3xl font-semibold md:text-4xl">
          Знайдіть свій ідеальний дім
        </h2>
        <p className="mx-auto mt-4 max-w-md text-center text-white/90">
          Приєднуйтесь до тисяч користувачів, які вже знайшли своє ідеальне житло з RentAI.
        </p>
        <div className="mt-12 grid grid-cols-3 gap-6 border-t border-white/20 pt-8 text-center text-sm">
          <div>
            <p className="text-2xl font-bold">10K+</p>
            <p className="text-white/80">Користувачів</p>
          </div>
          <div>
            <p className="text-2xl font-bold">5K+</p>
            <p className="text-white/80">Об’єктів</p>
          </div>
          <div>
            <p className="text-2xl font-bold">98%</p>
            <p className="text-white/80">Задоволених</p>
          </div>
        </div>
      </div>
    </div>
  )
}
