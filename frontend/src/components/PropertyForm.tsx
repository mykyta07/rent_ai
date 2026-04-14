import { useState } from 'react'
import type { PropertyCreatePayload, PropertyDetail } from '../api/types'
import { generateListingDescription } from '../api/ai'
import { formatApiError } from '../lib/format'

const emptyLocation = (): PropertyCreatePayload['location'] => ({
  city: '',
  district: '',
  street: '',
  building_number: '',
  latitude: null,
  longitude: null,
  metro_station: '',
  metro_distance_minutes: null,
})

export function buildPayloadFromDetail(d: PropertyDetail): PropertyCreatePayload {
  return {
    title: d.title,
    description: d.description,
    price: d.price,
    currency: d.currency,
    rooms_count: d.rooms_count,
    total_area: d.total_area,
    living_area: d.living_area,
    kitchen_area: d.kitchen_area,
    floor: d.floor,
    floors_count: d.floors_count,
    building_type: d.building_type,
    is_commercial: d.is_commercial,
    realty_type: d.realty_type,
    sale_type: d.sale_type,
    location: {
      city: d.location.city,
      district: d.location.district,
      street: d.location.street,
      building_number: d.location.building_number,
      latitude: d.location.latitude,
      longitude: d.location.longitude,
      metro_station: d.location.metro_station,
      metro_distance_minutes: d.location.metro_distance_minutes,
    },
    photos: d.photos.map((p) => ({ url: p.url, is_main: p.is_main })),
  }
}

type Props = {
  initial: PropertyCreatePayload
  submitLabel: string
  onSubmit: (payload: PropertyCreatePayload) => Promise<void>
  onCancel?: () => void
  /** Кнопка «Згенерувати опис» через Gemini (потрібен GEMINI_API_KEY на бекенді). */
  enableAiDescription?: boolean
}

export function PropertyForm({
  initial,
  submitLabel,
  onSubmit,
  onCancel,
  enableAiDescription = true,
}: Props) {
  const [payload, setPayload] = useState<PropertyCreatePayload>(initial)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [generatingDescription, setGeneratingDescription] = useState(false)
  const [descriptionHints, setDescriptionHints] = useState('')

  const setField = <K extends keyof PropertyCreatePayload>(
    key: K,
    value: PropertyCreatePayload[K]
  ) => {
    setPayload((p) => ({ ...p, [key]: value }))
  }

  const setLoc = <K extends keyof PropertyCreatePayload['location']>(
    key: K,
    value: PropertyCreatePayload['location'][K]
  ) => {
    setPayload((p) => ({
      ...p,
      location: { ...p.location, [key]: value },
    }))
  }

  const addPhoto = () => {
    setPayload((p) => ({
      ...p,
      photos: [...p.photos, { url: '', is_main: false }],
    }))
  }

  const updatePhoto = (i: number, patch: Partial<{ url: string; is_main: boolean }>) => {
    setPayload((p) => {
      const photos = [...p.photos]
      photos[i] = { ...photos[i], ...patch }
      return { ...p, photos }
    })
  }

  const removePhoto = (i: number) => {
    setPayload((p) => ({
      ...p,
      photos: p.photos.filter((_, idx) => idx !== i),
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      const cleaned: PropertyCreatePayload = {
        ...payload,
        photos: payload.photos.filter((ph) => ph.url.trim().length > 0),
        location: {
          ...payload.location,
          city: payload.location.city.trim(),
        },
      }
      if (!cleaned.location.city) {
        setError('Вкажіть місто')
        setSaving(false)
        return
      }
      await onSubmit(cleaned)
       } catch (err) {
      setError(formatApiError(err))
    } finally {
      setSaving(false)
    }
  }

  const buildDescriptionGenerateBody = () => ({
    title: payload.title,
    hints: descriptionHints.trim() || undefined,
    price: payload.price,
    currency: payload.currency,
    rooms_count: payload.rooms_count,
    total_area: payload.total_area,
    living_area: payload.living_area,
    kitchen_area: payload.kitchen_area,
    floor: payload.floor,
    floors_count: payload.floors_count,
    building_type: payload.building_type,
    is_commercial: payload.is_commercial,
    realty_type: payload.realty_type,
    sale_type: payload.sale_type,
    city: payload.location.city,
    district: payload.location.district,
    street: payload.location.street,
    building_number: payload.location.building_number,
    metro_station: payload.location.metro_station,
    metro_distance_minutes: payload.location.metro_distance_minutes,
  })

  const handleGenerateDescription = async () => {
    setError(null)
    const city = payload.location.city.trim()
    const title = payload.title.trim()
    const hints = descriptionHints.trim()
    if (!city && !title && !hints) {
      setError('Щоб згенерувати опис: вкажіть місто або заголовок, або коротку підказку нижче.')
      return
    }
    setGeneratingDescription(true)
    try {
      const { description } = await generateListingDescription(buildDescriptionGenerateBody())
      setField('description', description)
    } catch (err) {
      setError(formatApiError(err))
    } finally {
      setGeneratingDescription(false)
    }
  }

  return (
    <form onSubmit={(e) => void handleSubmit(e)} className="space-y-8">
      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      )}

      <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Основне</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div className="md:col-span-2">
            <label className="text-sm font-medium text-slate-700">Заголовок</label>
            <input
              value={payload.title}
              onChange={(e) => setField('title', e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
              required
            />
          </div>
          <div className="md:col-span-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <label className="text-sm font-medium text-slate-700">Опис</label>
              {enableAiDescription && (
                <button
                  type="button"
                  onClick={() => void handleGenerateDescription()}
                  disabled={saving || generatingDescription}
                  className="rounded-xl border border-violet-200 bg-violet-50 px-3 py-1.5 text-xs font-semibold text-violet-800 hover:bg-violet-100 disabled:opacity-50"
                >
                  {generatingDescription ? 'Генеруємо…' : 'Згенерувати з полів (ШІ)'}
                </button>
              )}
            </div>
            <textarea
              value={payload.description}
              onChange={(e) => setField('description', e.target.value)}
              rows={5}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
              required
            />
            {enableAiDescription && (
              <p className="mt-1 text-xs text-slate-500">
                ШІ використовує заголовок, ціну, площу, тип, угоду та локацію. За потреби додайте
                коротку підказку:
              </p>
            )}
            {enableAiDescription && (
              <input
                type="text"
                value={descriptionHints}
                onChange={(e) => setDescriptionHints(e.target.value)}
                maxLength={800}
                placeholder="Напр.: з ремонтом, тихий двір, поруч парк…"
                className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
              />
            )}
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Ціна</label>
            <input
              type="number"
              min={0}
              value={payload.price}
              onChange={(e) => setField('price', Number(e.target.value))}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
              required
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Валюта</label>
            <input
              value={payload.currency}
              onChange={(e) => setField('currency', e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
              placeholder="$"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Кімнати</label>
            <input
              type="number"
              min={0}
              value={payload.rooms_count ?? ''}
              onChange={(e) =>
                setField('rooms_count', e.target.value ? Number(e.target.value) : null)
              }
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Загальна площа</label>
            <input
              type="number"
              step="0.1"
              value={payload.total_area ?? ''}
              onChange={(e) =>
                setField('total_area', e.target.value ? Number(e.target.value) : null)
              }
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Житлова площа</label>
            <input
              type="number"
              step="0.1"
              value={payload.living_area ?? ''}
              onChange={(e) =>
                setField('living_area', e.target.value ? Number(e.target.value) : null)
              }
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Кухня</label>
            <input
              type="number"
              step="0.1"
              value={payload.kitchen_area ?? ''}
              onChange={(e) =>
                setField('kitchen_area', e.target.value ? Number(e.target.value) : null)
              }
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Поверх</label>
            <input
              type="number"
              value={payload.floor ?? ''}
              onChange={(e) =>
                setField('floor', e.target.value ? Number(e.target.value) : null)
              }
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Поверховість</label>
            <input
              type="number"
              value={payload.floors_count ?? ''}
              onChange={(e) =>
                setField('floors_count', e.target.value ? Number(e.target.value) : null)
              }
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Тип будинку</label>
            <input
              value={payload.building_type ?? ''}
              onChange={(e) => setField('building_type', e.target.value || null)}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Тип нерухомості</label>
            <select
              value={payload.realty_type}
              onChange={(e) => setField('realty_type', e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
            >
              <option value="apartment">Квартира</option>
              <option value="house">Будинок</option>
              <option value="commercial">Комерція</option>
            </select>
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Угода</label>
            <select
              value={payload.sale_type}
              onChange={(e) => setField('sale_type', e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
            >
              <option value="sale">Продаж</option>
              <option value="rent">Оренда</option>
            </select>
          </div>
          <div className="flex items-center gap-2 pt-6">
            <input
              id="is_commercial"
              type="checkbox"
              checked={payload.is_commercial}
              onChange={(e) => setField('is_commercial', e.target.checked)}
              className="h-4 w-4 rounded border-slate-300 text-brand"
            />
            <label htmlFor="is_commercial" className="text-sm text-slate-700">
              Комерційне призначення
            </label>
          </div>
        </div>
      </section>

      <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Локація</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <label className="text-sm font-medium text-slate-700">Місто *</label>
            <input
              value={payload.location.city}
              onChange={(e) => setLoc('city', e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
              required
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Район</label>
            <input
              value={payload.location.district ?? ''}
              onChange={(e) => setLoc('district', e.target.value || null)}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Вулиця</label>
            <input
              value={payload.location.street ?? ''}
              onChange={(e) => setLoc('street', e.target.value || null)}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Номер будинку</label>
            <input
              value={payload.location.building_number ?? ''}
              onChange={(e) => setLoc('building_number', e.target.value || null)}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Широта</label>
            <input
              value={payload.location.latitude ?? ''}
              onChange={(e) => setLoc('latitude', e.target.value || null)}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Довгота</label>
            <input
              value={payload.location.longitude ?? ''}
              onChange={(e) => setLoc('longitude', e.target.value || null)}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Метро</label>
            <input
              value={payload.location.metro_station ?? ''}
              onChange={(e) => setLoc('metro_station', e.target.value || null)}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Хв. до метро</label>
            <input
              type="number"
              value={payload.location.metro_distance_minutes ?? ''}
              onChange={(e) =>
                setLoc(
                  'metro_distance_minutes',
                  e.target.value ? Number(e.target.value) : null
                )
              }
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
            />
          </div>
        </div>
      </section>

      <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-lg font-semibold text-slate-900">Фото</h2>
          <button
            type="button"
            onClick={addPhoto}
            className="rounded-xl border border-brand/40 px-4 py-2 text-sm font-semibold text-brand-dark hover:bg-brand/5"
          >
            + URL фото
          </button>
        </div>
        <div className="mt-4 space-y-3">
          {payload.photos.length === 0 && (
            <p className="text-sm text-slate-500">Додайте посилання на зображення.</p>
          )}
          {payload.photos.map((ph, i) => (
            <div key={i} className="flex flex-wrap items-end gap-3 rounded-2xl border border-slate-100 p-3">
              <div className="min-w-[200px] flex-1">
                <label className="text-xs text-slate-500">URL</label>
                <input
                  value={ph.url}
                  onChange={(e) => updatePhoto(i, { url: e.target.value })}
                  className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none"
                  placeholder="https://..."
                />
              </div>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={ph.is_main}
                  onChange={(e) => updatePhoto(i, { is_main: e.target.checked })}
                />
                Головне
              </label>
              <button
                type="button"
                onClick={() => removePhoto(i)}
                className="text-sm text-red-600 hover:underline"
              >
                Видалити
              </button>
            </div>
          ))}
        </div>
      </section>

      <div className="flex flex-wrap gap-3">
        <button
          type="submit"
          disabled={saving}
          className="rounded-2xl bg-accent px-8 py-3 font-semibold text-white hover:bg-accent-hover disabled:opacity-60"
        >
          {saving ? 'Збереження…' : submitLabel}
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="rounded-2xl border border-slate-200 px-8 py-3 font-semibold text-slate-700 hover:bg-slate-50"
          >
            Скасувати
          </button>
        )}
      </div>
    </form>
  )
}

export function defaultEmptyProperty(): PropertyCreatePayload {
  return {
    title: '',
    description: '',
    price: 0,
    currency: '$',
    rooms_count: null,
    total_area: null,
    living_area: null,
    kitchen_area: null,
    floor: null,
    floors_count: null,
    building_type: null,
    is_commercial: false,
    realty_type: 'apartment',
    sale_type: 'sale',
    location: emptyLocation(),
    photos: [],
  }
}
