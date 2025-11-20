const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ApiOptions {
  method?: string
  body?: any
  token?: string
}

export async function apiClient(endpoint: string, options: ApiOptions = {}) {
  const { method = 'GET', body, token } = options

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `API error: ${response.status}`)
  }

  return response.json()
}

// Generation types
export interface PluginRequest {
  prompt: string
  tier: 'simple' | 'medium' | 'complex'
  name?: string
}

export interface DatapackRequest {
  prompt: string
  tier: 'simple' | 'medium' | 'complex'
  name?: string
}

export interface TexturePackRequest {
  style_description: string
  textures: string[]
  name?: string
}

export interface Generation {
  id: string
  type: string
  tier: string
  status: string
  prompt: string
  credits_used: number
  file_url?: string
  file_name?: string
  error_message?: string
  created_at: string
  completed_at?: string
}

// API functions
export const api = {
  // User
  getProfile: (token: string) => 
    apiClient('/api/users/me', { token }),
  
  getGenerations: (token: string, limit = 20) => 
    apiClient(`/api/users/me/generations?limit=${limit}`, { token }),
  
  getTransactions: (token: string, limit = 50) => 
    apiClient(`/api/users/me/transactions?limit=${limit}`, { token }),

  // Generations
  generatePlugin: (token: string, data: PluginRequest) =>
    apiClient('/api/generations/plugin', { method: 'POST', body: data, token }),
  
  generateDatapack: (token: string, data: DatapackRequest) =>
    apiClient('/api/generations/datapack', { method: 'POST', body: data, token }),
  
  generateTexturePack: (token: string, data: TexturePackRequest) =>
    apiClient('/api/generations/texture-pack', { method: 'POST', body: data, token }),
  
  getGeneration: (token: string, id: string) =>
    apiClient(`/api/generations/${id}`, { token }),
  
  getPricing: () =>
    apiClient('/api/generations/pricing'),
  
  estimateCredits: (type: string, tier?: string, textures?: string[]) =>
    apiClient('/api/generations/estimate', { 
      method: 'POST', 
      body: { generation_type: type, tier, textures } 
    }),

  // Credits
  getPackages: () =>
    apiClient('/api/credits/packages'),
  
  getBalance: (token: string) =>
    apiClient('/api/credits/balance', { token }),
  
  createCheckout: (token: string, packageId: string, successUrl: string, cancelUrl: string) =>
    apiClient('/api/credits/checkout', {
      method: 'POST',
      body: { package_id: packageId, success_url: successUrl, cancel_url: cancelUrl },
      token
    }),
}
