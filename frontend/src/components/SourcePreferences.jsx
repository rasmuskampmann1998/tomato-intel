import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import AddSourceModal from './AddSourceModal'

function daysSince(iso) {
  if (!iso) return null
  return Math.floor((Date.now() - new Date(iso).getTime()) / 86400000)
}

function HealthDot({ source }) {
  const days = daysSince(source.last_scraped_at)
  const failed = source.scrape_status === 'failed'
  if (failed || days === null) return <span className="w-2 h-2 rounded-full bg-tomato inline-block" title="Failed / never scraped" />
  if (days <= 7)  return <span className="w-2 h-2 rounded-full bg-leaf inline-block" title={`${days}d ago`} />
  if (days <= 14) return <span className="w-2 h-2 rounded-full bg-amber inline-block" title={`${days}d ago`} />
  return <span className="w-2 h-2 rounded-full bg-tomato inline-block" title={`${days}d ago — stale`} />
}

function SourceRow({ source, isFollowed, isAdmin, onToggleFollow, onToggleActive }) {
  const lastScraped = source.last_scraped_at
    ? new Date(source.last_scraped_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
    : 'never'
  const statusColor = source.scrape_status === 'ok' ? 'text-leaf' : source.scrape_status === 'failed' ? 'text-tomato' : 'text-amber'

  return (
    <tr className="border-b border-rule hover:bg-paper-deep">
      <td className="py-2 px-3">
        <div className="flex items-center gap-2">
          <HealthDot source={source} />
          <span className="font-body text-sm text-ink">{source.name}</span>
          {source.submitted_by && (
            <span className="font-mono text-[9px] tracking-[0.1em] uppercase border border-rule px-1 text-ink-mute">user</span>
          )}
        </div>
      </td>
      <td className="py-2 px-3">
        <span className="font-mono text-[9px] tracking-[0.1em] uppercase border border-rule px-1.5 py-0.5 text-ink-mute bg-paper-deep">
          {source.scrape_type}
        </span>
      </td>
      <td className="py-2 px-3">
        <span className={`font-mono text-[10px] ${statusColor}`}>
          {source.scrape_status || 'pending'}
        </span>
      </td>
      <td className="py-2 px-3 font-mono text-[10px] text-ink-mute">{lastScraped}</td>
      <td className="py-2 px-3">
        {onToggleFollow ? (
          <button
            onClick={() => onToggleFollow(source.id, !isFollowed)}
            className={`font-mono text-[9px] tracking-[0.1em] uppercase border px-2 py-1 transition ${
              isFollowed
                ? 'bg-tomato text-paper border-tomato'
                : 'border-rule text-ink-mute hover:border-ink-mute'
            }`}
          >
            {isFollowed ? 'Following' : 'Follow'}
          </button>
        ) : (
          <span className="text-ink-mute">—</span>
        )}
      </td>
      {isAdmin && (
        <td className="py-2 px-3">
          <button
            onClick={() => onToggleActive(source)}
            className={`font-mono text-[9px] tracking-[0.1em] uppercase border px-2 py-1 transition ${
              source.active
                ? 'border-tomato/40 text-tomato hover:bg-tomato-soft'
                : 'border-leaf/40 text-leaf hover:bg-leaf/10'
            }`}
          >
            {source.active ? 'Disable' : 'Enable'}
          </button>
        </td>
      )}
    </tr>
  )
}

function HealthRow({ source, count7d }) {
  const days = daysSince(source.last_scraped_at)
  const failed = source.scrape_status === 'failed'
  let freshLabel, freshCls
  if (failed || days === null) { freshLabel = 'Failed'; freshCls = 'text-tomato' }
  else if (days <= 1)  { freshLabel = 'Today';        freshCls = 'text-leaf' }
  else if (days <= 7)  { freshLabel = `${days}d ago`; freshCls = 'text-leaf' }
  else if (days <= 14) { freshLabel = `${days}d ago`; freshCls = 'text-amber' }
  else                 { freshLabel = `${days}d ago`; freshCls = 'text-tomato' }

  return (
    <div className="flex items-center gap-3 py-2 px-3 hover:bg-paper-deep">
      <HealthDot source={source} />
      <span className="font-body text-sm text-ink flex-1 min-w-0 truncate">{source.name}</span>
      <span className={`font-mono text-[10px] w-16 text-right ${freshCls}`}>{freshLabel}</span>
      <span className="font-mono text-[10px] text-ink-mute w-20 text-right">
        {count7d > 0 ? `${count7d} /7d` : <span className="text-rule">0 items</span>}
      </span>
      <span className={`font-mono text-[9px] tracking-[0.1em] uppercase w-14 text-center ${
        source.scrape_status === 'ok' ? 'text-leaf' : source.scrape_status === 'failed' ? 'text-tomato' : 'text-amber'
      }`}>
        {source.scrape_status || 'pending'}
      </span>
      {source.url && (
        <a href={source.url} target="_blank" rel="noopener noreferrer"
          className="font-mono text-[10px] text-ink-mute hover:text-tomato shrink-0">↗</a>
      )}
    </div>
  )
}

export default function SourcePreferences({ category, userId, isAdmin, followedSourceIds, onPrefChange }) {
  const [sources, setSources] = useState([])
  const [loading, setLoading] = useState(false)
  const [counts7d, setCounts7d] = useState({})
  const [tab, setTab] = useState('sources')
  const [showAddModal, setShowAddModal] = useState(false)

  useEffect(() => {
    if (category) { loadSources(); loadCounts() }
  }, [category])

  const loadSources = async () => {
    setLoading(true)
    const { data } = await supabase.from('sources').select('*').eq('category_id', category.id).order('name')
    setSources(data || [])
    setLoading(false)
  }

  const loadCounts = async () => {
    const since = new Date(Date.now() - 7 * 86400000).toISOString()
    const { data } = await supabase.from('scraped_items').select('source_id').eq('category_slug', category.slug).gte('scraped_at', since)
    if (!data) return
    const map = {}
    for (const row of data) map[row.source_id] = (map[row.source_id] || 0) + 1
    setCounts7d(map)
  }

  const handleToggleFollow = async (sourceId, follow) => {
    if (userId) {
      await supabase.from('user_source_prefs').upsert(
        { user_id: userId, source_id: sourceId, is_followed: follow, updated_at: new Date().toISOString() },
        { onConflict: 'user_id,source_id' }
      )
    }
    onPrefChange(sourceId, follow)
  }

  const handleToggleActive = async (source) => {
    await supabase.from('sources').update({ active: !source.active }).eq('id', source.id)
    loadSources()
  }

  const handleSourceAdded = (sourceId) => {
    loadSources(); loadCounts()
    onPrefChange(sourceId, true)
    setShowAddModal(false)
  }

  if (!category) return null

  const followedCount = sources.filter(s => followedSourceIds.includes(s.id)).length
  const failedCount = sources.filter(s => s.scrape_status === 'failed' || !s.last_scraped_at).length
  const healthySources = sources.filter(s => {
    const d = daysSince(s.last_scraped_at)
    return d !== null && d <= 7 && s.scrape_status !== 'failed'
  }).length

  const healthSorted = [...sources].sort((a, b) => {
    const score = s => {
      if (s.scrape_status === 'failed' || !s.last_scraped_at) return 3
      const d = daysSince(s.last_scraped_at)
      if (d > 14) return 2
      if (d > 7) return 1
      return 0
    }
    return score(b) - score(a)
  })

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <p className="font-mono text-[9px] tracking-[0.2em] uppercase text-ink-mute">Sources</p>
          <p className="font-mono text-[10px] text-ink-mute mt-0.5">
            {tab === 'sources'
              ? `${followedCount} followed · ${sources.length} total${failedCount > 0 ? ` · ${failedCount} need attention` : ''}`
              : `${healthySources} healthy · ${sources.length - healthySources} need attention`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex border border-rule overflow-hidden">
            {[['sources', '📋 Sources'], ['health', '🩺 Health']].map(([t, label]) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`font-mono text-[9px] tracking-[0.1em] uppercase px-2.5 py-1.5 transition ${
                  tab === t ? 'bg-ink text-paper' : 'text-ink-mute hover:bg-paper-deep'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          {tab === 'sources' && (
            <button
              onClick={() => setShowAddModal(true)}
              className="font-mono text-[9px] tracking-[0.12em] uppercase border border-rule text-ink-mute hover:text-tomato hover:border-tomato px-2.5 py-1.5 transition"
            >
              + Add source
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <p className="font-mono text-[10px] tracking-[0.12em] uppercase text-ink-mute">Loading…</p>
      ) : sources.length === 0 ? (
        <p className="font-display italic text-sm text-ink-mute">No sources configured for this category.</p>
      ) : tab === 'sources' ? (
        <div className="border border-rule overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-paper-deep border-b border-rule">
                {['Source', 'Type', 'Status', 'Last run', 'Your feed', ...(isAdmin ? ['Global'] : [])].map(h => (
                  <th key={h} className="py-2 px-3 text-left font-mono text-[9px] tracking-[0.14em] uppercase text-ink-mute">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sources.map(s => (
                <SourceRow
                  key={s.id}
                  source={s}
                  isFollowed={followedSourceIds.includes(s.id)}
                  isAdmin={isAdmin}
                  onToggleFollow={handleToggleFollow}
                  onToggleActive={handleToggleActive}
                />
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="border border-rule divide-y divide-rule">
          <div className="flex items-center gap-3 py-1.5 px-3 bg-paper-deep">
            <span className="w-2 h-2" />
            <span className="font-mono text-[9px] uppercase text-ink-mute flex-1">Source</span>
            <span className="font-mono text-[9px] uppercase text-ink-mute w-16 text-right">Last scraped</span>
            <span className="font-mono text-[9px] uppercase text-ink-mute w-20 text-right">Activity</span>
            <span className="font-mono text-[9px] uppercase text-ink-mute w-14 text-center">Status</span>
            <span className="w-4" />
          </div>
          {healthSorted.map(s => (
            <HealthRow key={s.id} source={s} count7d={counts7d[s.id] || 0} />
          ))}
        </div>
      )}

      {showAddModal && (
        <AddSourceModal
          category={category}
          onClose={() => setShowAddModal(false)}
          onAdded={handleSourceAdded}
        />
      )}
    </div>
  )
}
