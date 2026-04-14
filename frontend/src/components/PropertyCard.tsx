import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Heart, MapPin } from 'lucide-react'
import type { PropertyListItem } from '../api/types'
import { formatMoney, realtyTypeLabel, saleTypeLabel } from '../lib/format'
import { useFavorites } from '../context/FavoritesContext'
import { useAuth } from '../context/AuthContext'

type Props = {
  property: PropertyListItem
}

export function PropertyCard({ property }: Props) {
  const { user } = useAuth()
  const { toggle, has } = useFavorites()
  const navigate = useNavigate()
  const location = useLocation()
  const img =
    property.main_photo ||
    'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800&q=80'

  const locationLine = [
    property.location?.street,
    property.location?.district,
    property.location?.city,
  ]
    .filter(Boolean)
    .join(', ')

  return (
    <article className="group overflow-hidden rounded-3xl bg-white shadow-card transition hover:-translate-y-0.5 hover:shadow-xl">
      <div className="relative aspect-[4/3] overflow-hidden">
        <img
          src={img}
          alt=""
          className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
        />
        <div className="absolute left-3 top-3 flex flex-wrap gap-2">
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold text-white ${
              property.sale_type === 'rent' ? 'bg-blue-600' : 'bg-brand'
            }`}
          >
            {saleTypeLabel(property.sale_type)}
          </span>
          {property.is_mine && (
            <span className="rounded-full bg-accent px-3 py-1 text-xs font-semibold text-white">
              Моє
            </span>
          )}
        </div>
        <span className="absolute bottom-3 left-3 rounded-full bg-white/95 px-3 py-1 text-xs font-medium text-slate-700 shadow">
          {realtyTypeLabel(property.realty_type)}
        </span>
        <button
          type="button"
          onClick={(e) => {
            e.preventDefault()
            if (!user) {
              navigate('/login', { state: { from: location } })
              return
            }
            void toggle(property.id)
          }}
          className="absolute right-3 top-3 flex h-10 w-10 items-center justify-center rounded-full bg-white/95 text-slate-600 shadow hover:text-accent"
          aria-label="Обране"
        >
          <Heart
            className={`h-5 w-5 ${has(property.id) ? 'fill-accent text-accent' : ''}`}
          />
        </button>
      </div>
      <div className="p-5">
        <Link to={`/properties/${property.id}`}>
          <h2 className="font-display text-xl font-semibold text-slate-900 hover:text-brand-dark">
            {property.title}
          </h2>
        </Link>
        <p className="mt-2 flex items-start gap-1 text-sm text-slate-500">
          <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-brand" />
          <span>{locationLine || 'Локація уточнюється'}</span>
        </p>
        <div className="mt-4 flex items-center justify-between gap-3">
          <div className="flex gap-4 text-sm text-slate-600">
            {property.rooms_count != null && (
              <span>{property.rooms_count} кімн.</span>
            )}
            {property.total_area != null && (
              <span>{property.total_area} м²</span>
            )}
          </div>
          <p className="text-lg font-bold text-brand-dark">
            {formatMoney(property.price, property.currency)}
          </p>
        </div>
      </div>
    </article>
  )
}
