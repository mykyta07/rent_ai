import { apiJson } from './client'
import type {
  ChatHistoryMessage,
  ChatResponse,
  ListingDescriptionGeneratePayload,
  SemanticSearchResult,
} from './types'

export async function sendChatMessage(message: string): Promise<ChatResponse> {
  return apiJson<ChatResponse>('/api/ai/chat/', {
    method: 'POST',
    body: { message },
  })
}

export async function fetchChatHistory(limit = 50): Promise<{
  count: number
  limit: number
  results: ChatHistoryMessage[]
}> {
  return apiJson(`/api/ai/chat/history/?limit=${limit}`)
}

export async function semanticSearch(query: string): Promise<SemanticSearchResult[]> {
  return apiJson<SemanticSearchResult[]>('/api/ai/search/', {
    method: 'POST',
    body: { query },
  })
}

export async function explainProperty(
  propertyId: number,
  userPreferences?: string
): Promise<{ explanation: string }> {
  return apiJson<{ explanation: string }>('/api/ai/explain/', {
    method: 'POST',
    body: {
      property_id: propertyId,
      ...(userPreferences ? { user_preferences: userPreferences } : {}),
    },
  })
}

export async function explainPropertyBrief(
  propertyId: number
): Promise<{ explanation: string }> {
  return apiJson<{ explanation: string }>('/api/ai/explain/brief/', {
    method: 'POST',
    body: {
      property_id: propertyId,
    },
  })
}

export async function compareProperties(
  propertyIds: number[]
): Promise<{ comparison: string }> {
  return apiJson<{ comparison: string }>('/api/ai/compare/', {
    method: 'POST',
    body: { property_ids: propertyIds },
  })
}

export async function generateListingDescription(
  body: ListingDescriptionGeneratePayload
): Promise<{ description: string }> {
  return apiJson<{ description: string }>('/api/ai/generate-listing-description/', {
    method: 'POST',
    body,
  })
}
