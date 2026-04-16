export type User = {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: string
  date_joined: string
}

export type Location = {
  city: string
  district: string | null
  street: string | null
  building_number: string | null
  latitude: string | null
  longitude: string | null
  metro_station: string | null
  metro_distance_minutes: number | null
}

export type PropertyPhoto = {
  id: number
  url: string
  is_main: boolean
}

export type PropertyListItem = {
  id: number
  title: string
  price: number
  currency: string
  rooms_count: number | null
  total_area: number | null
  realty_type: string
  sale_type: string
  location: Location
  main_photo: string | null
  is_mine: boolean
}

/** Публічні дані власника з GET /api/properties/:id/ (може бути null для імпорту). */
export type PropertyOwnerPublic = {
  id: number
  username: string
  first_name: string
  last_name: string
  date_joined: string
}

export type PropertyDetail = {
  id: number
  title: string
  description: string
  price: number
  currency: string
  rooms_count: number | null
  total_area: number | null
  living_area: number | null
  kitchen_area: number | null
  floor: number | null
  floors_count: number | null
  building_type: string | null
  is_commercial: boolean
  realty_type: string
  sale_type: string
  location: Location
  photos: PropertyPhoto[]
  created_at: string
  /** Відсутній або null — імпорт / старі записи без власника в БД. */
  owner?: PropertyOwnerPublic | null
  is_mine: boolean
}

export type PropertyCreatePayload = {
  title: string
  description: string
  price: number
  currency: string
  rooms_count: number | null
  total_area: number | null
  living_area: number | null
  kitchen_area: number | null
  floor: number | null
  floors_count: number | null
  building_type: string | null
  is_commercial: boolean
  realty_type: string
  sale_type: string
  location: Omit<Location, 'latitude' | 'longitude'> & {
    latitude?: string | null
    longitude?: string | null
  }
  photos: { url: string; is_main: boolean }[]
}

/** Тіло POST /api/ai/generate-listing-description/ (поля форми оголошення). */
export type ListingDescriptionGeneratePayload = {
  title?: string
  hints?: string
  price?: number
  currency?: string
  rooms_count?: number | null
  total_area?: number | null
  living_area?: number | null
  kitchen_area?: number | null
  floor?: number | null
  floors_count?: number | null
  building_type?: string | null
  is_commercial?: boolean
  realty_type?: string
  sale_type?: string
  city?: string
  district?: string | null
  street?: string | null
  building_number?: string | null
  metro_station?: string | null
  metro_distance_minutes?: number | null
}

export type ChatResponse = {
  assistant_message: string
  properties?: number[]
  total_in_db?: number
  searched_count?: number
  relevance_scores?: number[]
}

export type ChatHistoryMessage = {
  id: number
  role: 'user' | 'assistant'
  content: string
  properties?: number[]
  created_at: string
}

export type SemanticSearchResult = {
  property_id: number
  title: string
  description: string
  similarity_score: number
}

export type PropertyExplainChatResponse = {
  assistant_message: string
}

export type PropertyExplainChatHistoryMessage = {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}
