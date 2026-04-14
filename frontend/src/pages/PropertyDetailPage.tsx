import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import {
  ArrowLeft,
  Heart,
  MapPin,
  Pencil,
  Sparkles,
  Trash2,
} from 'lucide-react'
import {
  deleteProperty,
  fetchProperty,
  fetchPropertyLocation,
  fetchPropertyPhotos,
} from '../api/properties'
import type { PropertyDetail, PropertyPhoto, Location } from '../api/types'
import { formatApiError, formatMoney, realtyTypeLabel, saleTypeLabel } from '../lib/format'
import { useFavorites } from '../context/FavoritesContext'
import { useAuth } from '../context/AuthContext'

export function PropertyDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const routeLocation = useLocation()
  const { user } = useAuth()
  const { toggle, has } = useFavorites()
  const pid = Number(id)

  const [detail, setDetail] = useState<PropertyDetail | null>(null)
  const [photos, setPhotos] = useState<PropertyPhoto[]>([])
  const [location, setLocation] = useState<Location | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [mainIdx, setMainIdx] = useState(0)

  useEffect(() => {
    if (!Number.isFinite(pid)) {
      setError('Невірний ID')
      setLoading(false)
      return
    }
    let cancelled = false
    void (async () => {
      setLoading(true)
      setError(null)
      try {
        const [d, ph, loc] = await Promise.all([
          fetchProperty(pid),
          fetchPropertyPhotos(pid).catch(() => []),
          fetchPropertyLocation(pid).catch(() => null),
        ])
        if (cancelled) return
        setDetail(d)
        setPhotos(ph.length ? ph : d.photos)
        setLocation(loc ?? d.location)
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

  const onDelete = async () => {
    if (!detail || !window.confirm('Видалити оголошення назавжди?')) return
    try {
      await deleteProperty(detail.id)
      navigate('/properties', { replace: true })
    } catch (e) {
      alert(formatApiError(e))
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-24 text-slate-500">Завантаження…</div>
    )
  }

  if (error || !detail) {
    return (
      <div className="mx-auto max-w-lg px-4 py-24 text-center">
        <p className="text-red-700">{error ?? 'Не знайдено'}</p>
        <Link to="/properties" className="mt-4 inline-block text-brand-dark underline">
          До списку
        </Link>
      </div>
    )
  }

  const displayPhotos = photos.length ? photos : detail.photos
  const activeUrl =
    displayPhotos[mainIdx]?.url ||
    'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1200&q=80'

  const locLine = location
    ? [location.street, location.district, location.city].filter(Boolean).join(', ')
    : ''

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <button
        type="button"
        onClick={() => navigate(-1)}
        className="mb-6 inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-brand-dark"
      >
        <ArrowLeft className="h-4 w-4" />
        Назад
      </button>

      <div className="grid gap-10 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="overflow-hidden rounded-3xl bg-white shadow-card">
            <div className="relative aspect-[16/10]">
              <img src={activeUrl} alt="" className="h-full w-full object-cover" />
              <div className="absolute left-4 top-4 flex flex-wrap gap-2">
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold text-white ${
                    detail.sale_type === 'rent' ? 'bg-blue-600' : 'bg-brand'
                  }`}
                >
                  {saleTypeLabel(detail.sale_type)}
                </span>
                <span className="rounded-full bg-white/95 px-3 py-1 text-xs font-medium text-slate-800">
                  {realtyTypeLabel(detail.realty_type)}
                </span>
              </div>
              <button
                type="button"
                onClick={() => {
                  if (!user) {
                    navigate('/login', { state: { from: routeLocation } })
                    return
                  }
                  void toggle(detail.id)
                }}
                className="absolute right-4 top-4 flex h-11 w-11 items-center justify-center rounded-full bg-white/95 text-slate-600 shadow"
              >
                <Heart
                  className={`h-5 w-5 ${has(detail.id) ? 'fill-accent text-accent' : ''}`}
                />
              </button>
              {displayPhotos.length > 1 && (
                <>
                  <button
                    type="button"
                    className="absolute bottom-4 left-4 rounded-full bg-white/90 px-3 py-1 text-xs font-medium"
                    onClick={() =>
                      setMainIdx((i) => (i - 1 + displayPhotos.length) % displayPhotos.length)
                    }
                  >
                    ‹
                  </button>
                  <button
                    type="button"
                    className="absolute bottom-4 right-4 rounded-full bg-white/90 px-3 py-1 text-xs font-medium"
                    onClick={() => setMainIdx((i) => (i + 1) % displayPhotos.length)}
                  >
                    ›
                  </button>
                </>
              )}
            </div>
            {displayPhotos.length > 1 && (
              <div className="flex gap-2 overflow-x-auto p-4">
                {displayPhotos.map((p, i) => (
                  <button
                    key={p.id ?? i}
                    type="button"
                    onClick={() => setMainIdx(i)}
                    className={`h-16 w-24 shrink-0 overflow-hidden rounded-xl ring-2 ${
                      i === mainIdx ? 'ring-brand' : 'ring-transparent'
                    }`}
                  >
                    <img src={p.url} alt="" className="h-full w-full object-cover" />
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="mt-8">
            <h1 className="font-display text-3xl font-semibold text-slate-900 md:text-4xl">
              {detail.title}
            </h1>
            <p className="mt-3 flex items-start gap-2 text-slate-600">
              <MapPin className="mt-0.5 h-5 w-5 shrink-0 text-brand" />
              {locLine || 'Локація'}
            </p>
            <p className="mt-6 text-3xl font-bold text-brand-dark">
              {formatMoney(detail.price, detail.currency)}
            </p>
            <div className="mt-6 flex flex-wrap gap-4 text-sm text-slate-600">
              {detail.rooms_count != null && <span>{detail.rooms_count} кімн.</span>}
              {detail.total_area != null && <span>{detail.total_area} м² заг.</span>}
              {detail.floor != null && (
                <span>
                  Поверх {detail.floor}
                  {detail.floors_count != null ? ` / ${detail.floors_count}` : ''}
                </span>
              )}
            </div>
            <div className="prose prose-slate mt-8 max-w-none">
              <p className="whitespace-pre-wrap text-slate-700">{detail.description}</p>
            </div>
          </div>
        </div>

        <aside className="space-y-6">
          <div className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
            <h2 className="font-semibold text-slate-900">Дії</h2>
            <div className="mt-4 flex flex-col gap-3">
              <Link
                to={`/properties/${detail.id}/explain`}
                className="inline-flex items-center justify-center gap-2 rounded-2xl bg-brand px-4 py-3 text-sm font-semibold text-white hover:bg-brand-dark"
              >
                <Sparkles className="h-4 w-4" />
                AI пояснення
              </Link>
              {detail.is_mine && (
                <>
                  <Link
                    to={`/properties/${detail.id}/edit`}
                    className="inline-flex items-center justify-center gap-2 rounded-2xl border-2 border-brand px-4 py-3 text-sm font-semibold text-brand-dark hover:bg-brand/5"
                  >
                    <Pencil className="h-4 w-4" />
                    Редагувати
                  </Link>
                  <button
                    type="button"
                    onClick={() => void onDelete()}
                    className="inline-flex items-center justify-center gap-2 rounded-2xl border border-red-200 px-4 py-3 text-sm font-semibold text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="h-4 w-4" />
                    Видалити
                  </button>
                </>
              )}
            </div>
          </div>

          {location && (
            <div className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
              <h2 className="font-semibold text-slate-900">Локація (API)</h2>
              <ul className="mt-3 space-y-1 text-sm text-slate-600">
                <li>Місто: {location.city}</li>
                {location.district && <li>Район: {location.district}</li>}
                {location.metro_station && <li>Метро: {location.metro_station}</li>}
                {(location.latitude || location.longitude) && (
                  <li>
                    Коорд.: {location.latitude}, {location.longitude}
                  </li>
                )}
              </ul>
            </div>
          )}
        </aside>
      </div>
    </div>
  )
}
