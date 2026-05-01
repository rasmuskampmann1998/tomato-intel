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
          <h1 className="font-display text-lg text-ink">Social Intelligence Feed</h1>
          <p className="font-mono text-[10px] text-ink-mute mt-0.5">
            {filtered.length} posts · updated every 3 days
          </p>
        </div>
        <button
          onClick={() => setShowManage(m => !m)}
          className={`font-mono text-[9px] tracking-[0.1em] uppercase border px-3 py-1.5 transition ${
            showManage
              ? 'bg-tomato text-paper border-tomato'
              : 'text-ink-mute border-rule hover:border-ink-mute'
          }`}
        >
          ⚙ Manage
        </button>
      </div>

      {/* Manage drawer */}
      {showManage && (
        <div className="bg-paper border border-rule p-4 space-y-4">
          {/* Tabs */}
          <div className="flex gap-2 border-b border-rule pb-3">
            {['accounts', 'keywords'].map(tab => (
              <button
                key={tab}
                onClick={() => setManageTab(tab)}
                className={`font-mono text-[9px] tracking-[0.1em] uppercase px-3 py-1.5 transition ${
                  manageTab === tab ? 'bg-ink text-paper' : 'text-ink-mute hover:bg-paper-deep'
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
                  <label className="font-mono text-[9px] tracking-[0.1em] uppercase text-ink-mute block mb-1">Platform</label>
                  <select
                    value={newPlatform}
                    onChange={e => setNewPlatform(e.target.value)}
                    className="text-sm border border-rule bg-paper text-ink px-2 py-1.5"
                  >
                    {PLATFORMS.filter(p => p.key !== 'all').map(p => (
                      <option key={p.key} value={p.key}>{p.icon} {p.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="font-mono text-[9px] tracking-[0.1em] uppercase text-ink-mute block mb-1">Handle / slug</label>
                  <input
                    value={newHandle}
                    onChange={e => setNewHandle(e.target.value)}
                    placeholder="@username or company-slug"
                    className="text-sm border border-rule bg-paper text-ink px-2 py-1.5 w-48"
                  />
                </div>
                <div>
                  <label className="font-mono text-[9px] tracking-[0.1em] uppercase text-ink-mute block mb-1">Display name</label>
                  <input
                    value={newDisplayName}
                    onChange={e => setNewDisplayName(e.target.value)}
                    placeholder="optional"
                    className="text-sm border border-rule bg-paper text-ink px-2 py-1.5 w-36"
                  />
                </div>
                <div>
                  <label className="font-mono text-[9px] tracking-[0.1em] uppercase text-ink-mute block mb-1">Type</label>
                  <select
                    value={newType}
                    onChange={e => setNewType(e.target.value)}
                    className="text-sm border border-rule bg-paper text-ink px-2 py-1.5"
                  >
                    {['competitor', 'media', 'researcher', 'influencer'].map(t => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <button
                  type="submit"
                  className="text-sm bg-tomato text-paper px-3 py-1.5 hover:bg-tomato-deep transition font-medium"
                >
                  + Add
                </button>
                {addError && <span className="font-mono text-[10px] text-tomato self-center">{addError}</span>}
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
                      <p className="font-mono text-[9px] tracking-[0.14em] uppercase text-ink-mute px-1 py-1">
                        {pConf?.icon} {pConf?.label || plat}
                      </p>
                      {accts.map(a => (
                        <div key={a.id} className="flex items-center justify-between px-2 py-1.5 hover:bg-paper-deep">
                          <div className="flex items-center gap-2">
                            <span className={`font-mono text-[10px] ${a.active ? 'text-ink' : 'text-ink-mute line-through'}`}>
                              @{a.handle}
                            </span>
                            {a.display_name && a.display_name !== a.handle && (
                              <span className="font-mono text-[10px] text-ink-mute">{a.display_name}</span>
                            )}
                            <span className="font-mono text-[9px] uppercase border border-rule px-1.5 text-ink-mute bg-paper-deep">{a.account_type}</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <button
                              onClick={() => handleToggleAccount(a.id, a.active)}
                              className="font-mono text-[10px] text-ink-mute hover:text-ink"
                            >
                              {a.active ? 'Pause' : 'Resume'}
                            </button>
                            <button
                              onClick={() => handleDeleteAccount(a.id)}
                              className="font-mono text-[10px] text-tomato hover:text-tomato-deep"
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
                  <p className="font-body text-sm text-ink-mute text-center py-4">No accounts watched yet</p>
                )}
              </div>
            </div>
          )}

          {manageTab === 'keywords' && (
            <div className="font-body text-sm text-ink-soft py-4 text-center">
              Keywords are configured via the Search Profiles panel in each category.
              Social search terms come from the <strong>Social Media</strong> search profile.
            </div>
          )}
        </div>
      )}

      {newPosts > 0 && (
        <button
          onClick={() => { setNewPosts(0); loadItems() }}
          className="w-full font-mono text-[10px] bg-tomato-soft border border-tomato/30 text-tomato py-2 hover:bg-tomato/10 transition font-medium"
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
            className={`shrink-0 flex items-center gap-1 px-3 py-1.5 text-sm font-medium whitespace-nowrap transition border ${
              platform === p.key
                ? 'bg-tomato text-paper border-tomato'
                : 'bg-paper border-rule text-ink-soft hover:border-ink-mute'
            }`}
          >
            <span>{p.icon}</span>
            <span>{p.label}</span>
            {p.key !== 'all' && counts[p.key] > 0 && (
              <span className={`font-mono text-[9px] rounded-full px-1.5 ${platform === p.key ? 'bg-paper/20' : 'bg-paper-deep text-ink-mute'}`}>
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
          className="text-sm border border-rule bg-paper text-ink px-2 py-1.5"
        >
          {DAYS_OPTIONS.map(o => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>

        <select
          value={typeFilter}
          onChange={e => setTypeFilter(e.target.value)}
          className="text-sm border border-rule bg-paper text-ink px-2 py-1.5 capitalize"
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
            className="w-full text-sm border border-rule bg-paper text-ink px-3 py-1.5 pr-7"
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-ink-mute hover:text-ink text-xs"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Feed */}
      {loading ? (
        <div className="text-center font-mono text-[10px] text-ink-mute py-12">Loading…</div>
      ) : filtered.length === 0 ? (
        <div className="text-center font-body text-sm text-ink-mute py-12 bg-paper border border-rule">
          No posts found for the selected filters.
          <br />
          <span className="font-mono text-[10px] mt-1 block">
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
