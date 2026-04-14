import { useEffect, useState } from 'react'
import { fetchUsers } from '../api/auth'
import type { User } from '../api/types'
import { formatApiError } from '../lib/format'

export function UsersPage() {
  const [users, setUsers] = useState<User[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    void (async () => {
      try {
        const data = await fetchUsers()
        setUsers(data)
      } catch (e) {
        setError(formatApiError(e))
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  if (loading) {
    return (
      <div className="flex justify-center py-20 text-slate-500">Завантаження…</div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-12">
      <h1 className="font-display text-3xl font-semibold text-slate-900">Користувачі</h1>
      <p className="mt-2 text-sm text-slate-600">
        Для звичайного користувача API повертає лише ваш запис.
      </p>
      {error && (
        <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      )}
      <ul className="mt-8 divide-y divide-slate-100 rounded-2xl border border-slate-100 bg-white shadow-sm">
        {users.map((u) => (
          <li key={u.id} className="flex flex-wrap items-center justify-between gap-2 px-4 py-4">
            <div>
              <p className="font-medium text-slate-900">
                {u.username}{' '}
                <span className="text-sm font-normal text-slate-500">
                  ({u.first_name} {u.last_name})
                </span>
              </p>
              <p className="text-sm text-slate-500">{u.email}</p>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
              {u.role}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
