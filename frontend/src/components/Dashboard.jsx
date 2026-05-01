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
  crops: '🌱',
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
    <div className="h-screen flex flex-col bg-paper">
      {/* Header */}
      <header className="bg-paper-deep border-b border-rule px-5 py-2.5 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setShowSearch(true)}
            className="hidden sm:flex items-center gap-2 text-ink-mute hover:text-ink transition"
            title="Search (Ctrl+K)"
          >
            <span className="text-sm">🔍</span>
            <span className="font-mono text-[10px] tracking-[0.12em] uppercase">Search</span>
            <kbd className="font-mono text-[9px] border border-rule px-1 py-0.5 text-ink-mute">⌘K</kbd>
          </button>
        </div>
        <div className="flex items-center gap-2">
          <div className="hidden sm:flex border border-rule overflow-hidden">
            {Object.entries(EXPERIENCE_CONFIG).map(([key, cfg]) => (
              <button
                key={key}
                onClick={() => setExperience(key)}
                title={cfg.description}
                className={`font-mono text-[10px] tracking-[0.1em] uppercase px-3 py-1.5 transition ${
                  experience === key
                    ? 'bg-ink text-paper'
                    : 'text-ink-soft hover:bg-paper'
                }`}
              >
                {cfg.label}
              </button>
            ))}
          </div>
          <span className="font-mono text-[9px] tracking-[0.14em] uppercase border border-rule text-ink-mute px-2 py-1">Demo</span>
        </div>
      </header>

      <TrendingBanner onTopicClick={() => setShowSearch(true)} />

      {/* Mobile category tabs — hidden on desktop */}
      <div className="lg:hidden bg-paper-deep border-b border-rule overflow-x-auto flex gap-0 shrink-0">
        {categories.map(cat => (
          <button
            key={cat.id}
            onClick={() => handleCategorySelect(cat)}
            className={`shrink-0 flex items-center gap-1.5 px-3 py-2 whitespace-nowrap border-r border-rule transition ${
              selectedCategory?.id === cat.id
                ? 'bg-tomato text-paper'
                : 'text-ink-soft hover:bg-paper'
            }`}
          >
            <span className="text-sm">{ICONS[cat.slug] || '📁'}</span>
            <span className="font-display text-[13px]">{cat.name}</span>
            {(badgeCounts?.[cat.id] || 0) > 0 && (
              <span className="font-mono text-[9px] bg-tomato text-paper px-1 ml-0.5">
                +{badgeCounts[cat.id]}
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

        <main className="flex-1 overflow-y-auto p-4 lg:p-8">
          {selectedCategory && (
            <div className="max-w-4xl mx-auto space-y-6">
              <div className="flex items-start justify-between gap-4 border-b border-rule pb-4">
                <div>
                  <p className="font-mono text-[9px] tracking-[0.2em] uppercase text-ink-mute mb-1">
                    Category
                  </p>
                  <h1 className="font-display text-4xl font-400 text-ink leading-tight">{selectedCategory.name}</h1>
                  {selectedCategory.description && (
                    <p className="font-display italic text-base text-ink-soft mt-1">{selectedCategory.description}</p>
                  )}
                </div>
                <button
                  onClick={() => setShowSources(s => !s)}
                  className={`font-mono text-[10px] tracking-[0.12em] uppercase border px-3 py-1.5 transition shrink-0 mt-2 ${
                    showSources ? 'bg-ink text-paper border-ink' : 'border-rule text-ink-mute hover:bg-paper-deep'
                  }`}
                >
                  {showSources ? 'Hide sources' : 'Sources'}
                </button>
              </div>

              {selectedCategory.slug === 'social' ? (
                <SocialFeed />
              ) : (
                <>
                  {showSources && (
                    <div className="bg-paper border border-rule p-4">
                      <SourcePreferences
                        category={selectedCategory}
                        userId={user?.id}
                        isAdmin={userRole === 'admin'}
                        followedSourceIds={followedSourceIds}
                        onPrefChange={handleSourcePrefChange}
                      />
                    </div>
                  )}

                  <div className="bg-paper border border-rule p-4">
                    <SearchProfiles
                      category={selectedCategory}
                      selectedProfile={selectedProfile}
                      onProfileSelect={setSelectedProfile}
                    />
                  </div>

                  {selectedProfile ? (
                    <div className="bg-paper border border-rule p-4">
                      <ResultsFeed
                        profile={selectedProfile}
                        category={selectedCategory}
                        cardStyle={expConfig.cardStyle}
                        followedSourceIds={followedSourceIds}
                        userId={user?.id}
                      />
                    </div>
                  ) : (
                    <div className="bg-paper border border-rule p-8 text-center">
                      <p className="font-display italic text-ink-mute">Select a search profile above to view results.</p>
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
