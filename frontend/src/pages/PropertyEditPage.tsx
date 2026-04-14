import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { fetchProperty, updateProperty } from '../api/properties'
import { formatApiError } from '../lib/format'
import { PropertyForm, buildPayloadFromDetail } from '../components/PropertyForm'
import type { PropertyCreatePayload } from '../api/types'

export function PropertyEditPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const pid = Number(id)
  const [initial, setInitial] = useState<PropertyCreatePayload | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!Number.isFinite(pid)) {
      setError('Невірний ID')
      setLoading(false)
      return
    }
    let cancelled = false
    void (async () => {
      try {
        const d = await fetchProperty(pid)
        if (!cancelled) {
          if (!d.is_mine) {
            setError('Немає прав на редагування')
            setInitial(null)
          } else {
            setInitial(buildPayloadFromDetail(d))
          }
        }
      } catch (e) {
        if (!cancelled) setError(formatApiError(e))
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [pid])

  if (loading) {
    return (
      <div className="flex justify-center py-24 text-slate-500">Завантаження…</div>
    )
  }

  if (error || !initial) {
    return (
      <div className="mx-auto max-w-lg px-4 py-24 text-center">
        <p className="text-red-700">{error ?? 'Немає даних'}</p>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="font-display text-3xl font-semibold text-slate-900">
        Редагування оголошення
      </h1>
      <div className="mt-8">
        <PropertyForm
          key={pid}
          initial={initial}
          submitLabel="Зберегти зміни"
          onCancel={() => navigate(`/properties/${pid}`)}
          onSubmit={async (payload) => {
            try {
              await updateProperty(pid, payload)
              navigate(`/properties/${pid}`, { replace: true })
            } catch (e) {
              throw new Error(formatApiError(e))
            }
          }}
        />
      </div>
    </div>
  )
}
