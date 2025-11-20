'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase'
import { api, Generation } from '@/lib/api'
import { 
  Hammer, 
  Package, 
  Zap, 
  Palette, 
  CreditCard, 
  Download, 
  LogOut,
  Clock,
  CheckCircle,
  XCircle,
  Loader2
} from 'lucide-react'

type GenerationType = 'plugin' | 'datapack' | 'texture_pack'
type Tier = 'simple' | 'medium' | 'complex'

export default function Dashboard() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [profile, setProfile] = useState<any>(null)
  const [generations, setGenerations] = useState<Generation[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')

  // Form state
  const [generationType, setGenerationType] = useState<GenerationType>('plugin')
  const [tier, setTier] = useState<Tier>('simple')
  const [prompt, setPrompt] = useState('')
  const [name, setName] = useState('')
  
  // Texture pack specific
  const [styleDescription, setStyleDescription] = useState('')
  const [textureInput, setTextureInput] = useState('')
  const [estimatedCredits, setEstimatedCredits] = useState(0)

  useEffect(() => {
    const supabase = createClient()
    
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) {
        router.push('/')
        return
      }
      setUser(session.user)
      loadUserData(session.access_token)
    })
  }, [router])

  const loadUserData = async (token: string) => {
    try {
      const [profileData, generationsData] = await Promise.all([
        api.getProfile(token),
        api.getGenerations(token)
      ])
      setProfile(profileData)
      setGenerations(generationsData.generations)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push('/')
  }

  const getToken = async () => {
    const supabase = createClient()
    const { data: { session } } = await supabase.auth.getSession()
    return session?.access_token
  }

  const handleGenerate = async () => {
    setError('')
    setGenerating(true)

    try {
      const token = await getToken()
      if (!token) throw new Error('Not authenticated')

      let result
      if (generationType === 'plugin') {
        result = await api.generatePlugin(token, { prompt, tier, name: name || undefined })
      } else if (generationType === 'datapack') {
        result = await api.generateDatapack(token, { prompt, tier, name: name || undefined })
      } else {
        const textures = textureInput.split(',').map(t => t.trim()).filter(Boolean)
        result = await api.generateTexturePack(token, { 
          style_description: styleDescription, 
          textures, 
          name: name || undefined 
        })
      }

      // Refresh data
      await loadUserData(token)
      
      // Clear form
      setPrompt('')
      setName('')
      setStyleDescription('')
      setTextureInput('')

      // Poll for completion
      pollGeneration(token, result.generation_id)

    } catch (err: any) {
      setError(err.message)
    } finally {
      setGenerating(false)
    }
  }

  const pollGeneration = async (token: string, generationId: string) => {
    const poll = async () => {
      try {
        const gen = await api.getGeneration(token, generationId)
        
        // Update in list
        setGenerations(prev => 
          prev.map(g => g.id === generationId ? gen : g)
        )

        if (gen.status === 'pending' || gen.status === 'processing') {
          setTimeout(poll, 3000)
        }
      } catch (err) {
        console.error('Poll error:', err)
      }
    }
    poll()
  }

  const handleBuyCredits = async (packageId: string) => {
    try {
      const token = await getToken()
      if (!token) throw new Error('Not authenticated')

      const { checkout_url } = await api.createCheckout(
        token,
        packageId,
        `${window.location.origin}/dashboard?success=true`,
        `${window.location.origin}/dashboard?canceled=true`
      )

      window.location.href = checkout_url
    } catch (err: any) {
      setError(err.message)
    }
  }

  // Estimate credits for texture packs
  useEffect(() => {
    if (generationType === 'texture_pack' && textureInput) {
      const textures = textureInput.split(',').map(t => t.trim()).filter(Boolean)
      api.estimateCredits('texture_pack', undefined, textures)
        .then(data => setEstimatedCredits(data.credits))
        .catch(() => setEstimatedCredits(0))
    }
  }, [generationType, textureInput])

  const getCreditsNeeded = () => {
    if (generationType === 'texture_pack') return estimatedCredits
    const pricing: Record<string, Record<string, number>> = {
      plugin: { simple: 20, medium: 35, complex: 50 },
      datapack: { simple: 5, medium: 10, complex: 15 }
    }
    return pricing[generationType]?.[tier] || 0
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-mc-diamond" />
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-gray-700 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Hammer className="w-8 h-8 text-mc-diamond" />
            <span className="text-2xl font-bold">BlockSmith AI</span>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 bg-gray-800 px-4 py-2 rounded-lg">
              <CreditCard className="w-4 h-4 text-mc-gold" />
              <span className="font-bold">{profile?.credits || 0}</span>
              <span className="text-gray-400">credits</span>
            </div>
            
            <button 
              onClick={handleLogout}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="bg-red-900/50 border border-red-500 rounded-lg p-4 mb-6">
            <p className="text-red-200">{error}</p>
          </div>
        )}

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Generation Form */}
          <div className="lg:col-span-2">
            <div className="card p-6">
              <h2 className="text-xl font-bold mb-6">Create Something New</h2>

              {/* Type Selection */}
              <div className="grid grid-cols-3 gap-4 mb-6">
                <button
                  onClick={() => setGenerationType('plugin')}
                  className={`p-4 rounded-lg border-2 transition-colors ${
                    generationType === 'plugin' 
                      ? 'border-mc-emerald bg-mc-emerald/10' 
                      : 'border-gray-600 hover:border-gray-500'
                  }`}
                >
                  <Package className={`w-6 h-6 mx-auto mb-2 ${
                    generationType === 'plugin' ? 'text-mc-emerald' : 'text-gray-400'
                  }`} />
                  <span className="text-sm">Plugin</span>
                </button>

                <button
                  onClick={() => setGenerationType('datapack')}
                  className={`p-4 rounded-lg border-2 transition-colors ${
                    generationType === 'datapack' 
                      ? 'border-mc-gold bg-mc-gold/10' 
                      : 'border-gray-600 hover:border-gray-500'
                  }`}
                >
                  <Zap className={`w-6 h-6 mx-auto mb-2 ${
                    generationType === 'datapack' ? 'text-mc-gold' : 'text-gray-400'
                  }`} />
                  <span className="text-sm">Datapack</span>
                </button>

                <button
                  onClick={() => setGenerationType('texture_pack')}
                  className={`p-4 rounded-lg border-2 transition-colors ${
                    generationType === 'texture_pack' 
                      ? 'border-mc-diamond bg-mc-diamond/10' 
                      : 'border-gray-600 hover:border-gray-500'
                  }`}
                >
                  <Palette className={`w-6 h-6 mx-auto mb-2 ${
                    generationType === 'texture_pack' ? 'text-mc-diamond' : 'text-gray-400'
                  }`} />
                  <span className="text-sm">Textures</span>
                </button>
              </div>

              {/* Tier Selection (for plugins and datapacks) */}
              {generationType !== 'texture_pack' && (
                <div className="mb-6">
                  <label className="block text-sm font-medium mb-2">Complexity</label>
                  <select 
                    value={tier} 
                    onChange={(e) => setTier(e.target.value as Tier)}
                    className="select"
                  >
                    <option value="simple">Simple - Basic functionality</option>
                    <option value="medium">Medium - Multiple features</option>
                    <option value="complex">Complex - Full-featured</option>
                  </select>
                </div>
              )}

              {/* Name */}
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2">
                  Name (optional)
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder={`My${generationType === 'plugin' ? 'Plugin' : generationType === 'datapack' ? 'Datapack' : 'Textures'}`}
                  className="input"
                />
              </div>

              {/* Prompt / Description */}
              {generationType === 'texture_pack' ? (
                <>
                  <div className="mb-6">
                    <label className="block text-sm font-medium mb-2">
                      Style Description
                    </label>
                    <textarea
                      value={styleDescription}
                      onChange={(e) => setStyleDescription(e.target.value)}
                      placeholder="e.g., Dark fantasy with purple and black tones, glowing runes..."
                      rows={3}
                      className="textarea"
                    />
                  </div>
                  
                  <div className="mb-6">
                    <label className="block text-sm font-medium mb-2">
                      Textures to Generate
                    </label>
                    <textarea
                      value={textureInput}
                      onChange={(e) => setTextureInput(e.target.value)}
                      placeholder="e.g., diamond_sword, iron_pickaxe, ores, stone&#10;&#10;You can use categories: ores, swords, pickaxes, food, gems"
                      rows={3}
                      className="textarea"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Comma-separated. Use category names like "ores" or "swords" for groups.
                    </p>
                  </div>
                </>
              ) : (
                <div className="mb-6">
                  <label className="block text-sm font-medium mb-2">
                    Describe what you want
                  </label>
                  <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder={
                      generationType === 'plugin'
                        ? 'e.g., A plugin that adds a /home command to teleport to your bed, with a 5 minute cooldown and permission node homes.use'
                        : 'e.g., A datapack that adds a recipe to craft diamonds from 9 emeralds'
                    }
                    rows={5}
                    className="textarea"
                  />
                </div>
              )}

              {/* Generate Button */}
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-400">
                  Cost: <span className="text-mc-gold font-bold">{getCreditsNeeded()}</span> credits
                </div>
                
                <button
                  onClick={handleGenerate}
                  disabled={generating || (profile?.credits || 0) < getCreditsNeeded()}
                  className="btn-minecraft flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {generating ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Generating...</span>
                    </>
                  ) : (
                    <span>Generate</span>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Buy Credits */}
            <div className="card p-6">
              <h3 className="font-bold mb-4">Buy Credits</h3>
              <div className="space-y-3">
                <button 
                  onClick={() => handleBuyCredits('starter')}
                  className="w-full p-3 bg-gray-700 hover:bg-gray-600 rounded-lg text-left transition-colors"
                >
                  <div className="flex justify-between items-center">
                    <span>Starter</span>
                    <span className="text-mc-gold font-bold">$5</span>
                  </div>
                  <span className="text-sm text-gray-400">60 credits</span>
                </button>
                
                <button 
                  onClick={() => handleBuyCredits('standard')}
                  className="w-full p-3 bg-gray-700 hover:bg-gray-600 rounded-lg text-left transition-colors border border-mc-diamond"
                >
                  <div className="flex justify-between items-center">
                    <span>Standard</span>
                    <span className="text-mc-gold font-bold">$15</span>
                  </div>
                  <span className="text-sm text-gray-400">200 credits</span>
                </button>
                
                <button 
                  onClick={() => handleBuyCredits('pro')}
                  className="w-full p-3 bg-gray-700 hover:bg-gray-600 rounded-lg text-left transition-colors"
                >
                  <div className="flex justify-between items-center">
                    <span>Pro</span>
                    <span className="text-mc-gold font-bold">$40</span>
                  </div>
                  <span className="text-sm text-gray-400">600 credits</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Generation History */}
        <div className="mt-8">
          <h2 className="text-xl font-bold mb-4">Your Generations</h2>
          
          {generations.length === 0 ? (
            <div className="card p-8 text-center text-gray-400">
              <p>No generations yet. Create something above!</p>
            </div>
          ) : (
            <div className="space-y-4">
              {generations.map((gen) => (
                <div key={gen.id} className="card p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      {gen.type === 'plugin' && <Package className="w-5 h-5 text-mc-emerald" />}
                      {gen.type === 'datapack' && <Zap className="w-5 h-5 text-mc-gold" />}
                      {gen.type === 'texture_pack' && <Palette className="w-5 h-5 text-mc-diamond" />}
                      
                      <div>
                        <p className="font-medium">{gen.file_name || `${gen.type} - ${gen.tier}`}</p>
                        <p className="text-sm text-gray-400 truncate max-w-md">{gen.prompt}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-4">
                      {gen.status === 'pending' && (
                        <span className="flex items-center text-gray-400">
                          <Clock className="w-4 h-4 mr-1" />
                          Queued
                        </span>
                      )}
                      {gen.status === 'processing' && (
                        <span className="flex items-center text-mc-gold">
                          <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                          Processing
                        </span>
                      )}
                      {gen.status === 'completed' && gen.file_url && (
                        <a 
                          href={gen.file_url}
                          className="flex items-center text-mc-emerald hover:underline"
                          download
                        >
                          <Download className="w-4 h-4 mr-1" />
                          Download
                        </a>
                      )}
                      {gen.status === 'failed' && (
                        <span className="flex items-center text-red-400">
                          <XCircle className="w-4 h-4 mr-1" />
                          Failed
                        </span>
                      )}
                      
                      <span className="text-sm text-gray-500">
                        {new Date(gen.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  
                  {gen.status === 'failed' && gen.error_message && (
                    <p className="text-sm text-red-400 mt-2">{gen.error_message}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
