import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { useUserProfile } from '../hooks/useUserProfile'
import { getCategoryOrder, EXPERIENCE_CONFIG } from '../lib/experienceConfig'
import CategorySidebar from './CategorySidebar'
import SearchProfiles from './SearchProfiles'
import ResultsFeed from './ResultsFeed'
import SourcePreferences from './SourcePreferences'

export default function Dashboard() {
  const [user, setUser] = useState(null)
  const [userRole, setUserRole] = useState('user')
  const [categories, setCategories] = useState([])
  const [selectedCategory, setSelectedCategory] = useState(null)
  const [selectedProfile, setSelectedProfile] = useState(null)
  const [badgeCounts, setBadgeCounts] = useState({})
  const [showSources, setShowSources] = useState(false)
  const [followedSourceIds, setFollowedSourceIds] = useState([])

  const { profile } = useUserProfile(user?.id)
  const experience = profile?.experience || 'researcher'
  const expConfig = EXPERIENCE_CONFIG[experience] || EXPERIENCE_CONFIG.researcher

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      if (data?.user) {
        setUser(data.user)
        loadUserRole(data.user.id)
      }
    })
  }, [])

  useEffect(() => {
    if (user?.id) loadFollowedSourceIds(user.id)
  }, [user?.id])

  // Re-order categories whenever experience loads
  useEffect(() => {
    if (categories.length && profile) {
      const ordered = getCategoryOrder(experience, categories)
      setCategories(ordered)
      setSelectedCategory(prev => prev || ordered[0])
    }
  }, [profile?.experience])

  const loadUserRole = async (userId) => {
    const { data } = await supabase
      .from('user_profiles')
      .select('role')
      .eq('id', userId)
      .single()
    if (data?.role) setUserRole(data.role)
  }

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

  const loadFollowedSourceIds = async (userId) => {
    const { data } = await supabase
      .from('user_source_prefs')
      .select('source_id')
      .eq('user_id', userId)
      .eq('is_followed', true)
    setFollowedSourceIds((data || []).map(r => r.source_id))
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

  const handleCategorySelect = (cat) => {
    setSelectedCategory(cat)
    setSelectedProfile(null)
    setShowSources(false)
  }

  const handleSignOut = async () => {
    await supabase.auth.signOut()
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
        <div className="flex items-center gap-3">
          {/* Experience badge */}
          <span className={`text-xs rounded-full px-2.5 py-0.5 font-medium bg-${expConfig.color}-100 text-${expConfig.color}-700`}>
            {expConfig.icon} {expConfig.label}
          </span>
          {userRole === 'admin' && (
            <span className="text-xs bg-purple-100 text-purple-700 rounded px-2 py-0.5">admin</span>
          )}
          <span className="text-sm text-gray-600">{user?.email}</span>
          <button onClick={handleSignOut} className="text-sm text-gray-400 hover:text-gray-600">
            Sign out
          </button>
        </div>
      </header>

      {/* Body */}
      <div className="flex flex-1 overflow-hidden">
        <CategorySidebar
          categories={categories}
          selected={selectedCategory}
          onSelect={handleCategorySelect}
          badgeCounts={badgeCounts}
        />

        <main className="flex-1 overflow-y-auto p-6">
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
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
