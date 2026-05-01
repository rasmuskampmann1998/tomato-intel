import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { useUserProfile } from '../hooks/useUserProfile'
import { getCategoryOrder, EXPERIENCE_CONFIG } from '../lib/experienceConfig'
import CategorySidebar from './CategorySidebar'
import SearchProfiles from './SearchProfiles'
import ResultsFeed from './ResultsFeed'
import SourcePreferences from './SourcePreferences'
import SocialFeed from './SocialFeed'
import SearchOverlay from './SearchOverlay'
import TrendingBanner from './TrendingBanner'

const ICONS = {
  news: '📰',
  competitors: '🏢',
  crop_recommendations: '🌱',
  patents: '📋',
  regulations: '⚖️',
  genetics: '🧬',
  social: '💬',
}

export default function Dashboard() {
  const [user] = useState(null)  // demo: no auth
  const [userRole] = useState('user')
  const [categories, setCategories] = useState([])
  const [selectedCategory, setSelectedCategory] = useState(null)
  const [selectedProfile, setSelectedProfile] = useState(null)
  const [badgeCounts, setBadgeCounts] = useState({})
  const [showSources, setShowSources] = useState(false)
  const [followedSourceIds, setFollowedSourceIds] = useState([])
  const [showSearch, setShowSearch] = useState(false)

  const { profile } = useUserProfile(null)
  const [experience, setExperience] = useState('researcher')
  const expConfig = EXPERIENCE_CONFIG[experience]

  // Re-order categories whenever experience changes
  useEffect(() => {
    if (categories.length) {
      const ordered = getCategoryOrder(experience, categories)
      setCategories(ordered)
      setSelectedCategory(prev => prev || ordered[0])
    }
  }, [experience])

  const loadCategories = async () => {
    const { data } = await supabase
      .from('categories')
      .select('*')
      .order('sort_order')
    if (data?.length) {
      setCategories(data)
      setSelectedCategory(data[0])
    }
  }

  const loadBadgeCounts = async () => {
    const { data } = await supabase
      .from('search_profiles')
      .select('category_id, new_since_last_visit')
    if (!data) return
    const counts = {}
    for (const p of data) {
      counts[p.category_id] = (counts[p.category_id] || 0) + (p.new_since_last_visit || 0)
    }
    setBadgeCounts(counts)
  }

  useEffect(() => { loadCategories() }, [])
  useEffect(() => { loadBadgeCounts() }, [selectedCategory])

  // Cmd+K / Ctrl+K to open search
  useEffect(() => {
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setShowSearch(s => !s)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  const handleCategorySelect = (cat) => {
    setSelectedCategory(cat)
    setSelectedProfile(null)
    setShowSources(false)
  }

  const handleSourcePrefChange = (sourceId, isFollowed) => {
    setFollowedSourceIds(prev =>
      isFollowed ? [...prev, sourceId] : prev.filter(id => id !== sourceId)
    )
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <span className="text-green-600 text-xl">🍅</span>
          <div>
            <span className="font-bold text-gray-900 text-sm">Tomato Intel</span>
            <span className="text-gray-400 text-xs ml-2">{expConfig.description}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSearch(true)}
            className="hidden sm:flex items-center gap-2 text-xs text-gray-500 bg-gray-100 hover:bg-gray-200 rounded-lg px-3 py-1.5 transition"
            title="Search (Ctrl+K)"
          >
            🔍 <span className="text-gray-400">Search</span>
            <kbd className="bg-white text-gray-400 rounded px-1 py-0.5 text-xs shadow-sm">⌘K</kbd>
          </button>
          <div className="hidden sm:flex bg-gray-100 rounded-lg p-0.5 gap-0.5">
            {Object.entries(EXPERIENCE_CONFIG).map(([key, cfg]) => (
              <button
                key={key}
                onClick={() => setExperience(key)}
                title={cfg.description}
                className={`text-xs px-2 py-1 rounded-md font-medium transition ${
                  experience === key
                    ? 'bg-white text-gray-800 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {cfg.icon} {cfg.label}
              </button>
            ))}
          </div>
          <span className="text-xs bg-gray-100 text-gray-500 rounded px-2 py-0.5">Demo</span>
        </div>
      </header>

      <TrendingBanner onTopicClick={() => setShowSearch(true)} />

      {/* Mobile category pill tabs — hidden on desktop */}
      <div className="lg:hidden bg-white border-b border-gray-200 overflow-x-auto flex gap-2 px-3 py-2 shrink-0">
        {categories.map(cat => (
          <button
            key={cat.id}
            onClick={() => handleCategorySelect(cat)}
            className={`shrink-0 flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium whitespace-nowrap transition ${
              selectedCategory?.id === cat.id
                ? 'bg-green-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <span>{ICONS[cat.slug] || '📁'}</span>
            <span>{cat.name}</span>
            {(badgeCounts?.[cat.id] || 0) > 0 && (
              <span className="bg-black/20 text-white text-xs rounded-full px-1.5 ml-0.5">
                {badgeCounts[cat.id]}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Body */}
      <div className="flex flex-1 overflow-hidden">
        <div className="hidden lg:block">
          <CategorySidebar
            categories={categories}
            selected={selectedCategory}
            onSelect={handleCategorySelect}
            badgeCounts={badgeCounts}
          />
        </div>

        <main className="flex-1 overflow-y-auto p-3 lg:p-6">
          {selectedCategory && (
            <div className="max-w-4xl mx-auto space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-lg font-bold text-gray-900">{selectedCategory.name}</h1>
                  {selectedCategory.description && (
                    <p className="text-sm text-gray-500 mt-0.5">{selectedCategory.description}</p>
                  )}
                </div>
                <button
                  onClick={() => setShowSources(s => !s)}
                  className="text-xs text-gray-500 hover:text-gray-700 border border-gray-200 rounded-lg px-3 py-1.5"
                >
                  {showSources ? 'Hide sources' : 'Sources'}
                </button>
              </div>

              {selectedCategory.slug === 'social' ? (
                <SocialFeed />
              ) : (
                <>
                  {showSources && (
                    <div className="bg-white rounded-xl border border-gray-200 p-4">
                      <SourcePreferences
                        category={selectedCategory}
                        userId={user?.id}
                        isAdmin={userRole === 'admin'}
                        followedSourceIds={followedSourceIds}
                        onPrefChange={handleSourcePrefChange}
                      />
                    </div>
                  )}

                  <div className="bg-white rounded-xl border border-gray-200 p-4">
                    <SearchProfiles
                      category={selectedCategory}
                      selectedProfile={selectedProfile}
                      onProfileSelect={setSelectedProfile}
                    />
                  </div>

                  {selectedProfile ? (
                    <div className="bg-white rounded-xl border border-gray-200 p-4">
                      <ResultsFeed
                        profile={selectedProfile}
                        category={selectedCategory}
                        cardStyle={expConfig.cardStyle}
                        followedSourceIds={followedSourceIds}
                        userId={user?.id}
                      />
                    </div>
                  ) : (
                    <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-sm text-gray-400">
                      Select a search profile above to view matching results
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </main>
      </div>

      {showSearch && <SearchOverlay onClose={() => setShowSearch(false)} />}
    </div>
  )
}
