import { apiJson } from './client'
import type {
  PropertyCreatePayload,
  PropertyDetail,
  PropertyListItem,
  PropertyPhoto,
  Location,
} from './types'

export type PropertyListParams = {
  rooms?: string
  district?: string
  min_price?: string
  max_price?: string
  type?: string
  sale_type?: string
  min_area?: string
  max_area?: string
  metro?: string
  mine?: boolean
  ordering?: string
}

function buildQuery(params: PropertyListParams): string {
  const q = new URLSearchParams()
  if (params.rooms) q.set('rooms', params.rooms)
  if (params.district) q.set('district', params.district)
  if (params.min_price) q.set('min_price', params.min_price)
  if (params.max_price) q.set('max_price', params.max_price)
  if (params.type) q.set('type', params.type)
  if (params.sale_type) q.set('sale_type', params.sale_type)
  if (params.min_area) q.set('min_area', params.min_area)
  if (params.max_area) q.set('max_area', params.max_area)
  if (params.metro) q.set('metro', params.metro)
  if (params.mine) q.set('mine', 'true')
  if (params.ordering) q.set('ordering', params.ordering)
  const s = q.toString()
  return s ? `?${s}` : ''
}

export async function fetchProperties(
  params: PropertyListParams = {}
): Promise<PropertyListItem[]> {
  return apiJson<PropertyListItem[]>(`/api/properties/${buildQuery(params)}`)
}

export async function fetchMyProperties(): Promise<PropertyListItem[]> {
  return apiJson<PropertyListItem[]>('/api/properties/my/')
}

export async function fetchProperty(id: number): Promise<PropertyDetail> {
  return apiJson<PropertyDetail>(`/api/properties/${id}/`)
}

export async function fetchPropertyPhotos(id: number): Promise<PropertyPhoto[]> {
  return apiJson<PropertyPhoto[]>(`/api/properties/${id}/photos/`)
}

export async function fetchPropertyLocation(id: number): Promise<Location> {
  return apiJson<Location>(`/api/properties/${id}/location/`)
}

export async function createProperty(
  payload: PropertyCreatePayload
): Promise<PropertyDetail> {
  return apiJson<PropertyDetail>('/api/properties/create/', {
    method: 'POST',
    body: payload,
  })
}

export async function updateProperty(
  id: number,
  payload: Partial<PropertyCreatePayload>
): Promise<PropertyDetail> {
  return apiJson<PropertyDetail>(`/api/properties/${id}/update/`, {
    method: 'PATCH',
    body: payload,
  })
}

export async function deleteProperty(id: number): Promise<void> {
  await apiJson<void>(`/api/properties/${id}/delete/`, {
    method: 'DELETE',
  })
}

/** Обране (потрібна авторизація) */
export async function fetchFavoriteProperties(): Promise<PropertyListItem[]> {
  return apiJson<PropertyListItem[]>('/api/properties/favorites/')
}

export async function addFavoriteProperty(propertyId: number): Promise<void> {
  await apiJson('/api/properties/favorites/', {
    method: 'POST',
    body: { property_id: propertyId },
  })
}

export async function removeFavoriteProperty(propertyId: number): Promise<void> {
  await apiJson<void>(`/api/properties/favorites/${propertyId}/`, {
    method: 'DELETE',
  })
}
