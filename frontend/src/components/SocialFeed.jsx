import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../lib/supabase'
import SocialCard from './SocialCard'

const PLATFORMS = [
  { key: 'all',       label: 'All',       icon: '💬' },
  { key: 'twitter',   label: 'X',         icon: '𝕏' },
  { key: 'reddit',    label: 'Reddit',    icon: '🟠' },
  { key: 'linkedin',  label: 'LinkedIn',  icon: '💼' },
  { key: 'instagram', label: 'Instagram', icon: '📸' },
  { key: 'facebook',  label: 'Facebook',  icon: '📘' },
  { key: 'tiktok',    label: 'TikTok',    icon: '🎵' },
]

const DAYS_OPTIONS = [
  { value: 3,   label: 'Last 3 days' },
  { value: 7,   label: 'Last 7 days' },
  { value: 30,  label: 'Last 30 days' },
  { value: 90,  label: 'Last 3 months' },
]

const TYPE_OPTIONS = ['all', 'competitor', 'media', 'researcher', 'influencer']

export default function SocialFeed() {
  const [items, setItems] = useState([])
  const [watchedAccounts, setWatchedAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [platform, setPlatform] = useState('all')
  const [days, setDays] = useState(7)
  const [typeFilter, setTypeFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [showManage, setShowManage] = useState(false)
  const [manageTab, setManageTab] = useState('accounts')
  // Add-account form state
  const [newHandle, setNewHandle] = useState('')
  const [newPlatform, setNewPlatform] = useState('twitter')
  const [newDisplayName, setNewDisplayName] = useState('')
  const [newType, setNewType] = useState('competitor')
  const [addError, setAddError] = useState('')

  // Platform counts
  const counts = items.reduce((acc, i) => {
    acc[i.platform] = (acc[i.platform] || 0) + 1
    return acc
  }, {})

  const loadItems = useCallback(async () => {
    setLoading(true)
    const since = new Date(Date.now() - days * 86400000).toISOString()
    let q = supabase
      .from('scraped_items')
      .select('*')
      .eq('category_slug', 'social')
      .gte('scraped_at', since)
      .order('like_count', { ascending: false })
      .limit(300)

    if (platform !== 'all') q = q.eq('platform', platform)

    const { data, error } = await q
    if (!error) setItems(data || [])
    setLoading(false)
  }, [platform, days])

  const loadWatchedAccounts = useCallback(async () => {
    const { data } = await supabase
      .from('social_watched_accounts')
      .select('*')
      .order('platform')
    setWatchedAccounts(data || [])
  }, [])

  const [newPosts, setNewPosts] = useState(0)

  useEffect(() => { loadItems() }, [loadItems])
  useEffect(() => { loadWatchedAccounts() }, [loadWatchedAccounts])

  // Realtime: listen for new social scraped_items
  useEffect(() => {
    const channel = supabase
      .channel('social-items-live')
      .on('postgres_changes', {
        event: 'INSERT',
        schema: 'public',
        table: 'scraped_items',
        filter: 'category_slug=eq.social',
      }, () => {
        setNewPosts(n => n + 1)
      })
      .subscribe()
    return () => supabase.removeChannel(channel)
  }, [])

  // Build a lookup: author+platform → account_type
  const accountTypeMap = {}
  for (const a of watchedAccounts) {
    accountTypeMap[`${a.platform}:${a.handle}`] = a.account_type
  }

  const filtered = items.filter(item => {
    if (typeFilter !== 'all') {
      const at = accountTypeMap[`${item.platform}:${item.author}`]
      if (at !== typeFilter) return false
    }
    if (search) {
      const q = search.toLowerCase()
      return (item.title || '').toLowerCase().includes(q) ||
             (item.content || '').toLowerCase().includes(q) ||
             (item.author || '').toLowerCase().includes(q)
    }
    return true
  })

  const handleToggleAccount = async (id, active) => {
    await supabase.from('social_watched_accounts').update({ active: !active }).eq('id', id)
    loadWatchedAccounts()
  }

  const handleDeleteAccount = async (id) => {
    await supabase.from('social_watched_accounts').delete().eq('id', id)
    loadWatchedAccounts()
  }

  const handleAddAccount = async (e) => {
    e.preventDefault()
    setAddError('')
    if (!newHandle.trim()) { setAddError('Handle is required'); return }
    const handle = newHandle.trim().replace(/^@/, '')
    const { error } = await supabase.from('social_watched_accounts').insert({
      platform: newPlatform,
      handle,
      display_name: newDisplayName.trim() || handle,
      account_type: newType,
      active: true,
    })
    if (error) {
      setAddError(error.message.includes('unique') ? 'Already watching this account' : error.message)
    } else {
      setNewHandle(''); setNewDisplayName(''); setAddError('')
      loadWatchedAccounts()
    }
  }

  return (
    <div className="space-y-4">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-gray-900">Social Intelligence Feed</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {filtered.length} posts · updated every 3 days
          </p>
        </div>
        <button
          onClick={() => setShowManage(m => !m)}
          className={`text-xs border rounded-lg px-3 py-1.5 transition ${
            showManage
              ? 'bg-green-600 text-white border-green-600'
              : 'text-gray-600 border-gray-200 hover:border-gray-400'
          }`}
        >
          ⚙ Manage
        </button>
      </div>

      {/* Manage drawer */}
      {showManage && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-4">
          {/* Tabs */}
          <div className="flex gap-2 border-b border-gray-100 pb-3">
            {['accounts', 'keywords'].map(tab => (
              <button
                key={tab}
                onClick={() => setManageTab(tab)}
                className={`text-sm px-3 py-1.5 rounded-lg capitalize transition ${
                  manageTab === tab ? 'bg-green-600 text-white' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {tab === 'accounts' ? '👤 Watched Accounts' : '🔍 Keywords'}
              </button>
            ))}
          </div>

          {manageTab === 'accounts' && (
            <div className="space-y-4">
              {/* Add account form */}
              <form onSubmit={handleAddAccount} className="flex flex-wrap gap-2 items-end">
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Platform</label>
                  <select
                    value={newPlatform}
                    onChange={e => setNewPlatform(e.target.value)}
                    className="text-sm border border-gray-200 rounded-lg px-2 py-1.5"
                  >
                    {PLATFORMS.filter(p => p.key !== 'all').map(p => (
                      <option key={p.key} value={p.key}>{p.icon} {p.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Handle / slug</label>
                  <input
                    value={newHandle}
                    onChange={e => setNewHandle(e.target.value)}
                    placeholder="@username or company-slug"
                    className="text-sm border border-gray-200 rounded-lg px-2 py-1.5 w-48"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Display name</label>
                  <input
                    value={newDisplayName}
                    onChange={e => setNewDisplayName(e.target.value)}
                    placeholder="optional"
                    className="text-sm border border-gray-200 rounded-lg px-2 py-1.5 w-36"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Type</label>
                  <select
                    value={newType}
                    onChange={e => setNewType(e.target.value)}
                    className="text-sm border border-gray-200 rounded-lg px-2 py-1.5"
                  >
                    {['competitor', 'media', 'researcher', 'influencer'].map(t => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <button
                  type="submit"
                  className="text-sm bg-green-600 text-white rounded-lg px-3 py-1.5 hover:bg-green-700 transition"
                >
                  + Add
                </button>
                {addError && <span className="text-xs text-red-500 self-center">{addError}</span>}
              </form>

              {/* Accounts table */}
              <div className="space-y-1 max-h-64 overflow-y-auto">
                {Object.entries(
                  watchedAccounts.reduce((g, a) => {
                    ;(g[a.platform] = g[a.platform] || []).push(a)
                    return g
                  }, {})
                ).map(([plat, accts]) => {
                  const pConf = PLATFORMS.find(p => p.key === plat)
                  return (
                    <div key={plat}>
                      <p className="text-xs font-medium text-gray-400 uppercase tracking-wider px-1 py-1">
                        {pConf?.icon} {pConf?.label || plat}
                      </p>
                      {accts.map(a => (
                        <div key={a.id} className="flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-gray-50">
                          <div className="flex items-center gap-2">
                            <span className={`text-xs font-medium ${a.active ? 'text-gray-800' : 'text-gray-400 line-through'}`}>
                              @{a.handle}
                            </span>
                            {a.display_name && a.display_name !== a.handle && (
                              <span className="text-xs text-gray-400">{a.display_name}</span>
                            )}
                            <span className="text-xs bg-gray-100 text-gray-500 rounded px-1.5">{a.account_type}</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <button
                              onClick={() => handleToggleAccount(a.id, a.active)}
                              className="text-xs text-gray-400 hover:text-gray-600"
                            >
                              {a.active ? 'Pause' : 'Resume'}
                            </button>
                            <button
                              onClick={() => handleDeleteAccount(a.id)}
                              className="text-xs text-red-400 hover:text-red-600"
                            >
                              ✕
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )
                })}
                {watchedAccounts.length === 0 && (
                  <p className="text-sm text-gray-400 text-center py-4">No accounts watched yet</p>
                )}
              </div>
            </div>
          )}

          {manageTab === 'keywords' && (
            <div className="text-sm text-gray-500 py-4 text-center">
              Keywords are configured via the Search Profiles panel in each category.
              Social search terms come from the <strong>Social Media</strong> search profile.
            </div>
          )}
        </div>
      )}

      {newPosts > 0 && (
        <button
          onClick={() => { setNewPosts(0); loadItems() }}
          className="w-full text-xs bg-green-50 border border-green-200 text-green-700 rounded-lg py-2 hover:bg-green-100 transition font-medium"
        >
          ↑ {newPosts} new {newPosts === 1 ? 'post' : 'posts'} — click to refresh
        </button>
      )}

      {/* Platform tab bar */}
      <div className="flex gap-1.5 overflow-x-auto pb-1">
        {PLATFORMS.map(p => (
          <button
            key={p.key}
            onClick={() => setPlatform(p.key)}
            className={`shrink-0 flex items-center gap-1 rounded-full px-3 py-1.5 text-sm font-medium whitespace-nowrap transition ${
              platform === p.key
                ? 'bg-green-600 text-white'
                : 'bg-white border border-gray-200 text-gray-600 hover:border-gray-400'
            }`}
          >
            <span>{p.icon}</span>
            <span>{p.label}</span>
            {p.key !== 'all' && counts[p.key] > 0 && (
              <span className={`text-xs rounded-full px-1.5 ${platform === p.key ? 'bg-white/20' : 'bg-gray-100 text-gray-500'}`}>
                {counts[p.key]}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Filters row */}
      <div className="flex flex-wrap gap-2 items-center">
        <select
          value={days}
          onChange={e => setDays(Number(e.target.value))}
          className="text-sm border border-gray-200 rounded-lg px-2 py-1.5 bg-white"
        >
          {DAYS_OPTIONS.map(o => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>

        <select
          value={typeFilter}
          onChange={e => setTypeFilter(e.target.value)}
          className="text-sm border border-gray-200 rounded-lg px-2 py-1.5 bg-white capitalize"
        >
          {TYPE_OPTIONS.map(t => (
            <option key={t} value={t}>{t === 'all' ? 'All types' : t}</option>
          ))}
        </select>

        <div className="relative flex-1 min-w-40">
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search posts…"
            className="w-full text-sm border border-gray-200 rounded-lg px-3 py-1.5 pr-7"
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-xs"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Feed */}
      {loading ? (
        <div className="text-center text-sm text-gray-400 py-12">Loading…</div>
      ) : filtered.length === 0 ? (
        <div className="text-center text-sm text-gray-400 py-12 bg-white rounded-xl border border-gray-200">
          No posts found for the selected filters.
          <br />
          <span className="text-xs mt-1 block">
            Social scraping runs every 3 days — trigger manually via GitHub Actions if needed.
          </span>
        </div>
      ) : (
        <div className="grid gap-3">
          {filtered.map(item => (
            <SocialCard
              key={item.id}
              item={item}
              accountType={accountTypeMap[`${item.platform}:${item.author}`]}
            />
          ))}
        </div>
      )}
    </div>
  )
}
