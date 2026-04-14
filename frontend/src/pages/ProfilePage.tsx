import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { formatApiError } from '../lib/format'
import { useAuth } from '../context/AuthContext'

export function ProfilePage() {
  const { user, updateUser, changeUserPassword, logout } = useAuth()
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [profileMsg, setProfileMsg] = useState<string | null>(null)
  const [profileErr, setProfileErr] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [newPasswordConfirm, setNewPasswordConfirm] = useState('')
  const [passMsg, setPassMsg] = useState<string | null>(null)
  const [passErr, setPassErr] = useState<string | null>(null)
  const [passLoading, setPassLoading] = useState(false)

  useEffect(() => {
    if (user) {
      setFirstName(user.first_name ?? '')
      setLastName(user.last_name ?? '')
      setEmail(user.email ?? '')
    }
  }, [user])

  if (!user) return null

  const saveProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    setProfileMsg(null)
    setProfileErr(null)
    setSaving(true)
    try {
      await updateUser({
        first_name: firstName,
        last_name: lastName,
        email,
      })
      setProfileMsg('Профіль збережено')
    } catch (err) {
      setProfileErr(formatApiError(err))
    } finally {
      setSaving(false)
    }
  }

  const savePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setPassMsg(null)
    setPassErr(null)
    setPassLoading(true)
    try {
      await changeUserPassword({
        old_password: oldPassword,
        new_password: newPassword,
        new_password_confirm: newPasswordConfirm,
      })
      setPassMsg('Пароль змінено')
      setOldPassword('')
      setNewPassword('')
      setNewPasswordConfirm('')
    } catch (err) {
      setPassErr(formatApiError(err))
    } finally {
      setPassLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="font-display text-3xl font-semibold text-slate-900">Профіль</h1>
      <p className="mt-2 text-slate-600">
        {user.username} · роль: {user.role}
      </p>
      <p className="mt-2 text-sm">
        <Link to="/users" className="text-brand-dark underline">
          Список користувачів (GET /api/users/)
        </Link>
      </p>

      <section className="mt-10 rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Дані профілю</h2>
        <form onSubmit={(e) => void saveProfile(e)} className="mt-6 space-y-4">
          {profileMsg && (
            <p className="rounded-xl bg-emerald-50 px-4 py-2 text-sm text-emerald-800">
              {profileMsg}
            </p>
          )}
          {profileErr && (
            <p className="rounded-xl bg-red-50 px-4 py-2 text-sm text-red-800">{profileErr}</p>
          )}
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="text-sm font-medium text-slate-700">Ім’я</label>
              <input
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand/30"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700">Прізвище</label>
              <input
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand/30"
              />
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand/30"
            />
          </div>
          <button
            type="submit"
            disabled={saving}
            className="rounded-2xl bg-brand px-6 py-2.5 text-sm font-semibold text-white hover:bg-brand-dark disabled:opacity-60"
          >
            {saving ? 'Збереження…' : 'Зберегти зміни'}
          </button>
        </form>
      </section>

      <section className="mt-8 rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Зміна пароля</h2>
        <form onSubmit={(e) => void savePassword(e)} className="mt-6 space-y-4">
          {passMsg && (
            <p className="rounded-xl bg-emerald-50 px-4 py-2 text-sm text-emerald-800">{passMsg}</p>
          )}
          {passErr && (
            <p className="rounded-xl bg-red-50 px-4 py-2 text-sm text-red-800">{passErr}</p>
          )}
          <div>
            <label className="text-sm font-medium text-slate-700">Поточний пароль</label>
            <input
              type="password"
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
              required
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Новий пароль</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
              required
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Підтвердження</label>
            <input
              type="password"
              value={newPasswordConfirm}
              onChange={(e) => setNewPasswordConfirm(e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
              required
            />
          </div>
          <button
            type="submit"
            disabled={passLoading}
            className="rounded-2xl border-2 border-brand px-6 py-2.5 text-sm font-semibold text-brand-dark hover:bg-brand/5 disabled:opacity-60"
          >
            {passLoading ? 'Зміна…' : 'Змінити пароль'}
          </button>
        </form>
      </section>

      <div className="mt-10">
        <button
          type="button"
          onClick={() => void logout()}
          className="rounded-2xl bg-slate-900 px-6 py-2.5 text-sm font-semibold text-white hover:bg-slate-800"
        >
          Вийти з акаунту
        </button>
      </div>
    </div>
  )
}
