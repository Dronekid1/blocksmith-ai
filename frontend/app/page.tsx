'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase'
import Link from 'next/link'
import { Hammer, Package, Palette, Zap, CreditCard, Download } from 'lucide-react'

export default function Home() {
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const supabase = createClient()
    
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null)
      setLoading(false)
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
    })

    return () => subscription.unsubscribe()
  }, [])

  const handleLogin = async () => {
    const supabase = createClient()
    await supabase.auth.signInWithOAuth({
      provider: 'discord',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`
      }
    })
  }

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="border-b border-gray-700 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Hammer className="w-8 h-8 text-mc-diamond" />
            <span className="text-2xl font-bold">BlockSmith AI</span>
          </div>
          
          {!loading && (
            user ? (
              <Link 
                href="/dashboard"
                className="btn-minecraft"
              >
                Dashboard
              </Link>
            ) : (
              <button 
                onClick={handleLogin}
                className="btn-minecraft flex items-center space-x-2"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515a.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0a12.64 12.64 0 0 0-.617-1.25a.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057a19.9 19.9 0 0 0 5.993 3.03a.078.078 0 0 0 .084-.028a14.09 14.09 0 0 0 1.226-1.994a.076.076 0 0 0-.041-.106a13.107 13.107 0 0 1-1.872-.892a.077.077 0 0 1-.008-.128a10.2 10.2 0 0 0 .372-.292a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127a12.299 12.299 0 0 1-1.873.892a.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028a19.839 19.839 0 0 0 6.002-3.03a.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.956-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.955-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.946 2.418-2.157 2.418z"/>
                </svg>
                <span>Login with Discord</span>
              </button>
            )
          )}
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
        <h1 className="text-5xl md:text-6xl font-bold mb-6">
          Generate Minecraft Content
          <span className="text-mc-diamond"> with AI</span>
        </h1>
        <p className="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
          Create custom plugins, datapacks, and texture packs in seconds. 
          Just describe what you want, and let AI do the heavy lifting.
        </p>
        
        {!loading && !user && (
          <button 
            onClick={handleLogin}
            className="btn-minecraft text-lg px-8 py-3"
          >
            Get Started Free
          </button>
        )}
        
        {user && (
          <Link 
            href="/dashboard"
            className="btn-minecraft text-lg px-8 py-3 inline-block"
          >
            Go to Dashboard
          </Link>
        )}
      </section>

      {/* Features */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">What You Can Create</h2>
        
        <div className="grid md:grid-cols-3 gap-8">
          {/* Plugins */}
          <div className="card p-6">
            <div className="w-12 h-12 bg-mc-emerald/20 rounded-lg flex items-center justify-center mb-4">
              <Package className="w-6 h-6 text-mc-emerald" />
            </div>
            <h3 className="text-xl font-bold mb-2">Plugins</h3>
            <p className="text-gray-400 mb-4">
              Generate Spigot/Paper plugins with custom commands, events, and features. 
              From simple utilities to complex game modes.
            </p>
            <ul className="text-sm text-gray-500 space-y-1">
              <li>• Custom commands & permissions</li>
              <li>• Event listeners</li>
              <li>• Config files included</li>
              <li>• Compiled .jar ready to use</li>
            </ul>
          </div>

          {/* Datapacks */}
          <div className="card p-6">
            <div className="w-12 h-12 bg-mc-gold/20 rounded-lg flex items-center justify-center mb-4">
              <Zap className="w-6 h-6 text-mc-gold" />
            </div>
            <h3 className="text-xl font-bold mb-2">Datapacks</h3>
            <p className="text-gray-400 mb-4">
              Create custom recipes, advancements, loot tables, and even custom dimensions 
              without any coding.
            </p>
            <ul className="text-sm text-gray-500 space-y-1">
              <li>• Custom crafting recipes</li>
              <li>• Advancement trees</li>
              <li>• Loot table modifications</li>
              <li>• Custom dimensions</li>
            </ul>
          </div>

          {/* Texture Packs */}
          <div className="card p-6">
            <div className="w-12 h-12 bg-mc-diamond/20 rounded-lg flex items-center justify-center mb-4">
              <Palette className="w-6 h-6 text-mc-diamond" />
            </div>
            <h3 className="text-xl font-bold mb-2">Texture Packs</h3>
            <p className="text-gray-400 mb-4">
              Generate custom textures for specific blocks and items. 
              Choose your style and which textures to create.
            </p>
            <ul className="text-sm text-gray-500 space-y-1">
              <li>• AI-generated pixel art</li>
              <li>• Any style you want</li>
              <li>• Pick specific textures</li>
              <li>• Resource pack ready</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Pricing Preview */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h2 className="text-3xl font-bold text-center mb-4">Simple Credit-Based Pricing</h2>
        <p className="text-center text-gray-400 mb-12">
          Buy credits and use them for any generation. No subscriptions, no hidden fees.
        </p>

        <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          <div className="card p-6 text-center">
            <h3 className="font-bold mb-2">Starter</h3>
            <div className="text-3xl font-bold text-mc-diamond mb-2">$5</div>
            <p className="text-gray-400">60 credits</p>
          </div>
          
          <div className="card p-6 text-center border-mc-diamond">
            <h3 className="font-bold mb-2">Standard</h3>
            <div className="text-3xl font-bold text-mc-diamond mb-2">$15</div>
            <p className="text-gray-400">200 credits</p>
            <span className="text-xs text-mc-emerald">Best Value</span>
          </div>
          
          <div className="card p-6 text-center">
            <h3 className="font-bold mb-2">Pro</h3>
            <div className="text-3xl font-bold text-mc-diamond mb-2">$40</div>
            <p className="text-gray-400">600 credits</p>
          </div>
        </div>

        <div className="text-center mt-8 text-sm text-gray-500">
          <p>Simple plugins start at 20 credits • Datapacks from 5 credits • Textures from 10 credits</p>
        </div>
      </section>

      {/* How it Works */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">How It Works</h2>
        
        <div className="grid md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="w-12 h-12 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
              1
            </div>
            <h3 className="font-bold mb-2">Sign In</h3>
            <p className="text-sm text-gray-400">Login with Discord in one click</p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
              2
            </div>
            <h3 className="font-bold mb-2">Get Credits</h3>
            <p className="text-sm text-gray-400">Start with 10 free credits or buy more</p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
              3
            </div>
            <h3 className="font-bold mb-2">Describe</h3>
            <p className="text-sm text-gray-400">Tell us what you want to create</p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
              4
            </div>
            <h3 className="font-bold mb-2">Download</h3>
            <p className="text-sm text-gray-400">Get your generated content instantly</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-700 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <Hammer className="w-6 h-6 text-mc-diamond" />
              <span className="font-bold">BlockSmith AI</span>
            </div>
            <p className="text-sm text-gray-500">
              Not affiliated with Mojang or Microsoft
            </p>
          </div>
        </div>
      </footer>
    </main>
  )
}
