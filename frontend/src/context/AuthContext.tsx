import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import {
  changePassword,
  fetchProfile,
  login as apiLogin,
  logout as apiLogout,
  register as apiRegister,
  updateProfile,
  type LoginPayload,
  type RegisterPayload,
} from '../api/auth'
import { clearTokens, getStoredAccess, setTokens } from '../api/client'
import type { User } from '../api/types'

type AuthContextValue = {
  user: User | null
  loading: boolean
  login: (payload: LoginPayload) => Promise<void>
  register: (payload: RegisterPayload) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
  updateUser: (
    data: Partial<Pick<User, 'first_name' | 'last_name' | 'email'>>
  ) => Promise<void>
  changeUserPassword: (payload: {
    old_password: string
    new_password: string
    new_password_confirm: string
  }) => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    const token = getStoredAccess()
    if (!token) {
      setUser(null)
      return
    }
    try {
      const u = await fetchProfile()
      setUser(u)
    } catch {
      setUser(null)
      clearTokens()
    }
  }, [])

  useEffect(() => {
    void (async () => {
      setLoading(true)
      await refreshUser()
      setLoading(false)
    })()
  }, [refreshUser])

  const login = useCallback(async (payload: LoginPayload) => {
    await apiLogin(payload)
    await refreshUser()
  }, [refreshUser])

  const register = useCallback(async (payload: RegisterPayload) => {
    const res = await apiRegister(payload)
    setTokens(res.tokens.access, res.tokens.refresh)
    setUser(res.user)
  }, [])

  const logout = useCallback(async () => {
    const refresh = localStorage.getItem('refresh')
    if (refresh) {
      await apiLogout(refresh)
    } else {
      clearTokens()
    }
    setUser(null)
  }, [])

  const updateUser = useCallback(
    async (data: Partial<Pick<User, 'first_name' | 'last_name' | 'email'>>) => {
      const u = await updateProfile(data)
      setUser(u)
    },
    []
  )

  const changeUserPassword = useCallback(
    async (payload: {
      old_password: string
      new_password: string
      new_password_confirm: string
    }) => {
      await changePassword(payload)
    },
    []
  )

  const value = useMemo(
    () => ({
      user,
      loading,
      login,
      register,
      logout,
      refreshUser,
      updateUser,
      changeUserPassword,
    }),
    [
      user,
      loading,
      login,
      register,
      logout,
      refreshUser,
      updateUser,
      changeUserPassword,
    ]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
