import { ApiError } from '../api/client'

export function formatMoney(price: number, currency: string): string {
  const formatted = new Intl.NumberFormat('uk-UA').format(price)
  if (currency === '$' || currency === 'USD') {
    return `$${formatted}`
  }
  return `${formatted} ${currency}`
}

export function saleTypeLabel(saleType: string): string {
  if (saleType === 'rent') return 'Оренда'
  if (saleType === 'sale') return 'Продаж'
  return saleType
}

export function realtyTypeLabel(t: string): string {
  const map: Record<string, string> = {
    apartment: 'Квартира',
    house: 'Будинок',
    commercial: 'Комерція',
  }
  return map[t] ?? t
}

export function formatApiError(err: unknown): string {
  if (err instanceof ApiError) {
    const b = err.body
    if (typeof b === 'string') return b
    if (b && typeof b === 'object') {
      const o = b as Record<string, unknown>
      if (typeof o.detail === 'string') return o.detail
      if (typeof o.error === 'string') return o.error
      if (typeof o.message === 'string') return o.message
      const parts: string[] = []
      for (const [k, v] of Object.entries(o)) {
        if (Array.isArray(v)) {
          parts.push(`${k}: ${v.join(', ')}`)
        } else if (typeof v === 'string') {
          parts.push(`${k}: ${v}`)
        }
      }
      if (parts.length) return parts.join('; ')
    }
    return err.message
  }
  if (err instanceof Error) return err.message
  return 'Невідома помилка'
}
