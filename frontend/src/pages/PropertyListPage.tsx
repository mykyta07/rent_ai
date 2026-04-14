import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useSearchParams } from 'react-router-dom'
import { Filter, MapPin, Search as SearchIcon, Sparkles } from 'lucide-react'
import { fetchProperties } from '../api/properties'
import {
  fetchChatHistory,
  semanticSearch as aiSemanticSearch,
} from '../api/ai'
import type { PropertyListItem } from '../api/types'
import { PropertyCard } from '../components/PropertyCard'
import { formatApiError } from '../lib/format'
import { useAuth } from '../context/AuthContext'

const PAGE_SIZE = 9

const DEFAULT_HERO_IMAGE =
  'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=2070&q=80'

function heroImageSrc(): string {
  const custom = import.meta.env.VITE_HERO_IMAGE_URL?.trim()
  return custom && custom.length > 0 ? custom : DEFAULT_HERO_IMAGE
}

type CatalogFilters = {
  district: string
  rooms: string
  min_price: string
  max_price: string
  min_area: string
  max_area: string
  metro: string
  type: string
  sale_type: string
  ordering: string
}

function useQueryFilters(searchParams: URLSearchParams): CatalogFilters {
  return useMemo(
    () => ({
      district: searchParams.get('district') ?? '',
      rooms: searchParams.get('rooms') ?? '',
      min_price: searchParams.get('min_price') ?? '',
      max_price: searchParams.get('max_price') ?? '',
      min_area: searchParams.get('min_area') ?? '',
      max_area: searchParams.get('max_area') ?? '',
      metro: searchParams.get('metro') ?? '',
      type: searchParams.get('type') ?? '',
      sale_type: searchParams.get('sale_type') ?? '',
      ordering: searchParams.get('ordering') ?? '-created_at',
    }),
    [searchParams]
  )
}

function filtersToFetchParams(f: CatalogFilters): Parameters<typeof fetchProperties>[0] {
  const params: Parameters<typeof fetchProperties>[0] = {
    ordering: f.ordering || undefined,
  }
  if (f.district) params.district = f.district
  if (f.rooms) params.rooms = f.rooms
  if (f.min_price) params.min_price = f.min_price
  if (f.max_price) params.max_price = f.max_price
  if (f.min_area) params.min_area = f.min_area
  if (f.max_area) params.max_area = f.max_area
  if (f.metro) params.metro = f.metro
  if (f.type) params.type = f.type
  if (f.sale_type) params.sale_type = f.sale_type
  return params
}

const REALTY_UK: Record<string, string> = {
  apartment: 'квартира',
  house: 'будинок',
  commercial: 'комерційна нерухомість',
}

function buildQueryFromChatUserMessages(
  messages: { role: string; content: string }[]
): string | null {
  const userTexts = messages
    .filter((m) => m.role === 'user')
    .map((m) => m.content.trim())
    .filter((t) => t.length > 0)
  if (userTexts.length === 0) return null
  const recent = userTexts.slice(-6)
  const joined = recent.join('. ')
  const trimmed = joined.slice(0, 1000)
  return trimmed.length >= 12 ? trimmed : null
}

/** Короткий опис поточних фільтрів для семантичного пошуку */
function buildQueryFromFilters(f: CatalogFilters): string | null {
  const parts: string[] = []
  if (f.sale_type === 'rent') parts.push('оренда')
  else if (f.sale_type === 'sale') parts.push('продаж, купівля')
  if (f.type) {
    parts.push(REALTY_UK[f.type] ?? f.type)
  }
  if (f.district.trim()) parts.push(`район / місто: ${f.district.trim()}`)
  if (f.metro.trim()) parts.push(`метро: ${f.metro.trim()}`)
  if (f.rooms) parts.push(`${f.rooms} кімнат`)
  if (f.min_price || f.max_price) {
    parts.push(`ціна від ${f.min_price || '—'} до ${f.max_price || '—'}`)
  }
  if (f.min_area || f.max_area) {
    parts.push(`площа ${f.min_area || '—'}–${f.max_area || '—'} м²`)
  }
  if (parts.length === 0) return null
  return `Шукаю нерухомість: ${parts.join(', ')}. Україна.`
}

function defaultSemanticFallback(saleType: string): string {
  return saleType === 'rent'
    ? 'Затишне житло для оренди в Україні, біля метро'
    : 'Сучасне житло для сім’ї, хороша ціна'
}

type AiRecSource = 'chat' | 'filters' | 'default'

function buildPersonalizedSearchQuery(f: CatalogFilters, chatUserBlob: string | null): {
  query: string
  source: AiRecSource
} {
  const filterPart = buildQueryFromFilters(f)
  if (chatUserBlob) {
    const query = filterPart
      ? `${chatUserBlob}\n\nУрахувати також: ${filterPart}`
      : chatUserBlob
    return { query, source: 'chat' }
  }
  if (filterPart) {
    return { query: filterPart, source: 'filters' }
  }
  return { query: defaultSemanticFallback(f.sale_type), source: 'default' }
}

export function PropertyListPage() {
  const location = useLocation()
  const showHero = location.pathname === '/'
  const { user } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const filters = useQueryFilters(searchParams)

  const [items, setItems] = useState<PropertyListItem[]>([])
  const [aiRecs, setAiRecs] = useState<PropertyListItem[]>([])
  const [aiRecSource, setAiRecSource] = useState<AiRecSource>('default')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)

  const loadList = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchProperties(filtersToFetchParams(filters))
      setItems(data)
    } catch (e) {
      setError(formatApiError(e))
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    void loadList()
  }, [loadList])

  useEffect(() => {
    setPage(1)
  }, [searchParams])

  useEffect(() => {
    if (!user) {
      setAiRecs([])
      setAiRecSource('default')
      return
    }
    let cancelled = false
    void (async () => {
      try {
        let chatBlob: string | null = null
        try {
          const hist = await fetchChatHistory(100)
          chatBlob = buildQueryFromChatUserMessages(hist.results)
        } catch {
          /* немає історії або помилка — працюємо з фільтрами / fallback */
        }

        const { query, source } = buildPersonalizedSearchQuery(filters, chatBlob)
        if (!cancelled) setAiRecSource(source)

        const results = await aiSemanticSearch(query)
        const ids = results.map((r) => r.property_id)
        const base = await fetchProperties(filtersToFetchParams(filters))
        const byId = new Map(base.map((p) => [p.id, p]))
        const picked = ids.map((id) => byId.get(id)).filter(Boolean) as PropertyListItem[]
        if (!cancelled) setAiRecs(picked.slice(0, 3))
      } catch {
        if (!cancelled) {
          setAiRecs([])
          setAiRecSource('default')
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [user, filters, location.key])

  const totalPages = Math.max(1, Math.ceil(items.length / PAGE_SIZE))
  const pageItems = useMemo(
    () => items.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE),
    [items, page]
  )

  const onSubmitFilters = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const form = e.currentTarget
    const fd = new FormData(form)
    const next = new URLSearchParams(searchParams)
    const keys = [
      'district',
      'rooms',
      'min_price',
      'max_price',
      'min_area',
      'max_area',
      'metro',
      'type',
      'sale_type',
      'ordering',
    ] as const
    for (const k of keys) {
      const v = (fd.get(k) as string) || ''
      if (!v) next.delete(k)
      else next.set(k, v)
    }
    setSearchParams(next, { replace: true })
  }

  return (
    <div>
      {showHero && (
        <section className="relative isolate min-h-[520px] overflow-hidden bg-slate-900 px-4 pb-28 pt-6 md:min-h-[580px]">
          <img
            src={heroImageSrc()}
            alt=""
            className="pointer-events-none absolute inset-0 h-full w-full object-cover"
            loading="eager"
            decoding="async"
          />
          <div
            className="absolute inset-0 bg-gradient-to-b from-slate-900/80 via-slate-900/60 to-slate-900/92"
            aria-hidden
          />
          <div className="relative z-10 mx-auto max-w-6xl pt-10 text-center text-white md:pt-14">
            <p className="mx-auto inline-flex items-center gap-2 rounded-full bg-white/15 px-4 py-1.5 text-sm backdrop-blur">
              Понад 15,000 об’єктів нерухомості
            </p>
            <h1 className="mt-6 font-display text-4xl font-semibold leading-tight md:text-5xl">
              Знайдіть свій{' '}
              <span className="text-brand-light">ідеальний дім</span>
            </h1>
            <p className="mx-auto mt-4 max-w-2xl text-lg text-white/85">
              Розумний пошук з AI-асистентом. Купівля, оренда та керування
              оголошеннями — усе в одному місці.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-4">
              <Link
                to="/properties"
                className="inline-flex items-center gap-2 rounded-full bg-accent px-8 py-3.5 text-base font-semibold text-white shadow-lg shadow-accent/30 transition hover:bg-accent-hover"
              >
                Розпочати пошук
              </Link>
              <Link
                to="/ai/chat"
                className="inline-flex items-center gap-2 rounded-full bg-white px-8 py-3.5 text-base font-semibold text-brand-dark shadow-md transition hover:bg-white/90"
              >
                <span className="h-2 w-2 rounded-full bg-brand" />
                Поговорити з AI
              </Link>
            </div>
          </div>
        </section>
      )}

      <div className={`mx-auto max-w-6xl px-4 ${showHero ? '-mt-20' : 'pt-10'}`}>
        <form
          id="property-list-filters"
          key={searchParams.toString()}
          onSubmit={onSubmitFilters}
        >
          <div className="flex flex-col gap-3 rounded-3xl bg-white p-4 shadow-card md:flex-row md:items-center">
            <div className="flex flex-1 items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2">
              <MapPin className="h-5 w-5 text-brand" />
              <input
                name="district"
                defaultValue={filters.district}
                placeholder="Район, місто…"
                className="w-full bg-transparent text-sm outline-none placeholder:text-slate-400"
              />
            </div>
            <div className="flex flex-1 items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2">
              <Filter className="h-5 w-5 text-brand" />
              <select
                name="type"
                defaultValue={filters.type}
                className="w-full bg-transparent text-sm outline-none"
              >
                <option value="">Тип: усі</option>
                <option value="apartment">Квартира</option>
                <option value="house">Будинок</option>
                <option value="commercial">Комерція</option>
              </select>
            </div>
            <div className="flex flex-1 items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2">
              <select
                name="sale_type"
                defaultValue={filters.sale_type}
                className="w-full bg-transparent text-sm outline-none"
              >
                <option value="">Угода: усі</option>
                <option value="sale">Продаж</option>
                <option value="rent">Оренда</option>
              </select>
            </div>
            <button
              type="submit"
              className="inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-accent to-amber-400 px-8 py-3 font-semibold text-white shadow-md transition hover:from-accent-hover hover:to-amber-500"
            >
              <SearchIcon className="h-5 w-5" />
              Шукати
            </button>
          </div>

          <div className="mt-6 flex flex-col gap-4 rounded-3xl border border-slate-100 bg-white p-4 shadow-sm md:flex-row md:items-end md:justify-between">
            <div className="grid flex-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <label className="text-xs font-medium text-slate-500">Кімнати</label>
                <input
                  name="rooms"
                  defaultValue={filters.rooms}
                  className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand/30"
                  placeholder="Напр. 2"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-500">Ціна від</label>
                <input
                  name="min_price"
                  defaultValue={filters.min_price}
                  type="number"
                  className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand/30"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-500">Ціна до</label>
                <input
                  name="max_price"
                  defaultValue={filters.max_price}
                  type="number"
                  className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand/30"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-500">Метро</label>
                <input
                  name="metro"
                  defaultValue={filters.metro}
                  className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand/30"
                  placeholder="Назва станції"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-500">Площа від (м²)</label>
                <input
                  name="min_area"
                  defaultValue={filters.min_area}
                  type="number"
                  step="0.1"
                  className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand/30"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-500">Площа до (м²)</label>
                <input
                  name="max_area"
                  defaultValue={filters.max_area}
                  type="number"
                  step="0.1"
                  className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand/30"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="text-xs font-medium text-slate-500">Сортування</label>
                <select
                  name="ordering"
                  defaultValue={filters.ordering}
                  className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand/30"
                >
                  <option value="-created_at">Спочатку нові</option>
                  <option value="price">Ціна за зростанням</option>
                  <option value="-price">Ціна за спаданням</option>
                  <option value="total_area">Площа за зростанням</option>
                  <option value="-total_area">Площа за спаданням</option>
                </select>
              </div>
            </div>
            <button
              type="submit"
              className="rounded-2xl border border-brand/30 px-4 py-2 text-sm font-semibold text-brand-dark hover:bg-brand/5"
            >
              Застосувати фільтри
            </button>
          </div>
        </form>

        {user && aiRecs.length > 0 && (
          <section className="mt-10 rounded-3xl border border-brand/15 bg-brand/5 p-6">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-brand" />
              <div>
                <h2 className="font-display text-lg font-semibold text-slate-900">
                  AI рекомендації
                </h2>
                <p className="text-sm text-slate-600">
                  {aiRecSource === 'chat' &&
                    'Підбір за останніми запитами в AI-чаті (доповнено поточними фільтрами) та семантичним пошуком.'}
                  {aiRecSource === 'filters' &&
                    'Підбір за поточними фільтрами пошуку та семантичним пошуком.'}
                  {aiRecSource === 'default' &&
                    'Загальний підбір за типом угоди; додайте фільтри або поговоріть з AI — рекомендації стануть точнішими.'}
                </p>
              </div>
            </div>
            <div className="mt-4 grid gap-4 md:grid-cols-3">
              {aiRecs.map((p) => (
                <PropertyCard key={`ai-${p.id}`} property={p} />
              ))}
            </div>
          </section>
        )}

        <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="font-display text-2xl font-semibold text-slate-900">
              Пошук нерухомості
            </h1>
            <p className="text-sm text-slate-500">
              Знайдено {items.length} об’єктів
              {items.length > 0 && (
                <>
                  {' '}
                  · Показано {(page - 1) * PAGE_SIZE + 1}–
                  {Math.min(page * PAGE_SIZE, items.length)} з {items.length}
                </>
              )}
            </p>
          </div>
          <div className="flex flex-wrap gap-2 text-sm text-slate-500">
            <Link to="/properties/create" className="font-medium text-brand-dark hover:underline">
              + Додати оголошення
            </Link>
            <span>·</span>
            <Link to="/my-properties" className="font-medium text-brand-dark hover:underline">
              Мої оголошення
            </Link>
          </div>
        </div>

        {error && (
          <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {error}
          </div>
        )}

        {loading ? (
          <div className="mt-12 flex justify-center text-slate-500">Завантаження…</div>
        ) : (
          <>
            <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {pageItems.map((p) => (
                <PropertyCard key={p.id} property={p} />
              ))}
            </div>
            {totalPages > 1 && (
              <div className="mt-10 flex items-center justify-center gap-2">
                <button
                  type="button"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="rounded-full border border-slate-200 px-4 py-2 text-sm disabled:opacity-40"
                >
                  Назад
                </button>
                <span className="text-sm text-slate-600">
                  Сторінка {page} з {totalPages}
                </span>
                <button
                  type="button"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="rounded-full border border-slate-200 px-4 py-2 text-sm disabled:opacity-40"
                >
                  Далі </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
