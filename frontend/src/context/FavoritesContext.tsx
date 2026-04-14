import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import {
  addFavoriteProperty,
  fetchFavoriteProperties,
  removeFavoriteProperty,
} from '../api/properties'
import type { PropertyListItem } from '../api/types'
import { useAuth } from './AuthContext'

type FavoritesContextValue = {
  ids: number[]
  favorites: PropertyListItem[]
  loading: boolean
  has: (id: number) => boolean
  toggle: (id: number) => Promise<void>
  remove: (id: number) => Promise<void>
  refresh: () => Promise<void>
}

const FavoritesContext = createContext<FavoritesContextValue | null>(null)

export function FavoritesProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const [favorites, setFavorites] = useState<PropertyListItem[]>([])
  const [loading, setLoading] = useState(false)
  const idsRef = useRef<number[]>([])

  const ids = useMemo(() => favorites.map((p) => p.id), [favorites])
  idsRef.current = ids

  const load = useCallback(async () => {
    if (!user) {
      setFavorites([])
      return
    }
    setLoading(true)
    try {
      const list = await fetchFavoriteProperties()
      setFavorites(list)
    } catch {
      setFavorites([])
    } finally {
      setLoading(false)
    }
  }, [user])

  useEffect(() => {
    void load()
  }, [load])

  const has = useCallback(
    (propertyId: number) => idsRef.current.includes(propertyId),
    []
  )

  const toggle = useCallback(
    async (propertyId: number) => {
      if (!user) return
      try {
        if (idsRef.current.includes(propertyId)) {
          await removeFavoriteProperty(propertyId)
        } else {
          await addFavoriteProperty(propertyId)
        }
        await load()
      } catch {
        /* залишаємо попередній стан після невдалого запиту */
        await load()
      }
    },
    [user, load]
  )

  const remove = useCallback(
    async (propertyId: number) => {
      if (!user) return
      try {
        await removeFavoriteProperty(propertyId)
        await load()
      } catch {
        await load()
      }
    },
    [user, load]
  )

  const value = useMemo(
    () => ({
      ids,
      favorites,
      loading,
      has,
      toggle,
      remove,
      refresh: load,
    }),
    [ids, favorites, loading, has, toggle, remove, load]
  )

  return (
    <FavoritesContext.Provider value={value}>{children}</FavoritesContext.Provider>
  )
}

export function useFavorites() {
  const ctx = useContext(FavoritesContext)
  if (!ctx) throw new Error('useFavorites must be used within FavoritesProvider')
  return ctx
}
