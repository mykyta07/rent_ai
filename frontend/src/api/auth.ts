import { apiJson, clearTokens, setTokens } from './client'
import type { User } from './types'

export type RegisterPayload = {
  username: string
  email: string
  password: string
  password_confirm: string
  first_name?: string
  last_name?: string
}

export type LoginPayload = {
  username: string
  password: string
}

export type RegisterResponse = {
  user: User
  tokens: { refresh: string; access: string }
}

export type LoginResponse = {
  refresh: string
  access: string
}

export async function register(payload: RegisterPayload): Promise<RegisterResponse> {
  return apiJson<RegisterResponse>('/api/auth/register/', {
    method: 'POST',
    body: payload,
    skipAuth: true,
  })
}

export async function login(payload: LoginPayload): Promise<LoginResponse> {
  const data = await apiJson<LoginResponse>('/api/auth/login/', {
    method: 'POST',
    body: payload,
    skipAuth: true,
  })
  setTokens(data.access, data.refresh)
  return data
}

export async function logout(refresh: string): Promise<void> {
  try {
    await apiJson('/api/auth/logout/', {
      method: 'POST',
      body: { refresh },
    })
  } finally {
    clearTokens()
  }
}

export async function fetchProfile(): Promise<User> {
  return apiJson<User>('/api/auth/profile/')
}

export async function updateProfile(
  data: Partial<Pick<User, 'first_name' | 'last_name' | 'email'>>
): Promise<User> {
  return apiJson<User>('/api/auth/profile/', {
    method: 'PATCH',
    body: data,
  })
}

export async function changePassword(payload: {
  old_password: string
  new_password: string
  new_password_confirm: string
}): Promise<{ message: string }> {
  return apiJson<{ message: string }>('/api/auth/change-password/', {
    method: 'POST',
    body: payload,
  })
}

export async function fetchUsers(): Promise<User[]> {
  return apiJson<User[]>('/api/users/')
}
