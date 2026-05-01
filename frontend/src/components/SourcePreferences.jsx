import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import AddSourceModal from './AddSourceModal'

const STATUS_STYLE = {
  ok:     'bg-green-100 text-green-700',
  empty:  'bg-yellow-100 text-yellow-700',
  failed: 'bg-red-100 text-red-700',
}

function daysSince(iso) {
  if (!iso) return null
  return Math.floor((Date.now() - new Date(iso).getTime()) / 86400000)
}

function HealthDot({ source }) {
  const days = daysSince(source.last_scraped_at)
  const failed = source.scrape_status === 'failed'
  if (failed || days === null) return <span className="w-2 h-2 rounded-full bg-red-400 inline-block" title="Failed / never scraped" />
  if (days <= 7) return <span className="w-2 h-2 rounded-full bg-green-400 inline-block" title={`${days}d ago`} />
  if (days <= 14) return <span className="w-2 h-2 rounded-full bg-yellow-400 inline-block" title={`${days}d ago`} />
  return <span className="w-2 h-2 rounded-full bg-red-400 inline-block" title={`${days}d ago — stale`} />
}

function SourceRow({ source, isFollowed, isAdmin, onToggleFollow, onToggleActive }) {
  const statusCls = STATUS_STYLE[source.scrape_status] || 'bg-gray-100 text-gray-500'
  const lastScraped = source.last_scraped_at
    ? new Date(source.last_scraped_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
    : 'never'

  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50">
      <td className="py-2.5 px-3">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-800">{source.name}</span>
          {source.submitted_by && (
            <span className="text-xs bg-blue-50 text-blue-600 rounded px-1.5 py-0.5">user</span>
          )}
        </div>
      </td>
      <td className="py-2.5 px-3">
        <span className="text-xs bg-gray-100 text-gray-600 rounded px-1.5 py-0.5">
          {source.scrape_type}
        </span>
      </td>
      <td className="py-2.5 px-3">
        {source.scrape_status ? (
          <span className={`text-xs rounded px-1.5 py-0.5 ${statusCls}`}>{source.scrape_status}</span>
        ) : (
          <span className="text-xs text-gray-400">pending</span>
        )}
      </td>
      <td className="py-2.5 px-3 text-xs text-gray-400">{lastScraped}</td>
      <td className="py-2.5 px-3">
        {onToggleFollow ? (
          <button
            onClick={() => onToggleFollow(source.id, !isFollowed)}
            className={`text-xs rounded px-2.5 py-1 font-medium transition ${
              isFollowed
                ? 'bg-green-100 text-green-700 hover:bg-green-200'
                : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
            }`}
          >
            {isFollowed ? 'Following' : 'Follow'}
          </button>
        ) : (
          <span className="text-xs text-gray-400">—</span>
        )}
      </td>
      {isAdmin && (
        <td className="py-2.5 px-3">
          <button
            onClick={() => onToggleActive(source)}
            className={`text-xs rounded px-2 py-1 ${
              source.active
                ? 'bg-red-50 text-red-600 hover:bg-red-100'
                : 'bg-green-50 text-green-600 hover:bg-green-100'
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
  if (failed || days === null) { freshLabel = 'Failed'; freshCls = 'text-red-600' }
  else if (days <= 1)  { freshLabel = 'Today';    freshCls = 'text-green-600' }
  else if (days <= 7)  { freshLabel = `${days}d ago`; freshCls = 'text-green-600' }
  else if (days <= 14) { freshLabel = `${days}d ago`; freshCls = 'text-yellow-600' }
  else                 { freshLabel = `${days}d ago`; freshCls = 'text-red-500' }

  return (
    <div className="flex items-center gap-3 py-2 px-3 rounded-lg hover:bg-gray-50">
      <HealthDot source={source} />
      <span className="text-sm text-gray-800 flex-1 min-w-0 truncate">{source.name}</span>
      <span className={`text-xs w-16 text-right ${freshCls}`}>{freshLabel}</span>
      <span className="text-xs text-gray-500 w-20 text-right">
        {count7d > 0 ? `${count7d} items/7d` : <span className="text-gray-300">0 items</span>}
      </span>
      <span className={`text-xs rounded px-1.5 py-0.5 w-14 text-center ${STATUS_STYLE[source.scrape_status] || 'bg-gray-100 text-gray-400'}`}>
        {source.scrape_status || 'pending'}
      </span>
      {source.url && (
        <a href={source.url} target="_blank" rel="noopener noreferrer"
          className="text-xs text-gray-400 hover:text-green-600 shrink-0">↗</a>
      )}
    </div>
  )
}

export default function SourcePreferences({
  category,
  userId,
  isAdmin,
  followedSourceIds,
  onPrefChange,
}) {
  const [sources, setSources] = useState([])
  const [loading, setLoading] = useState(false)
  const [counts7d, setCounts7d] = useState({})
  const [tab, setTab] = useState('sources')
  const [showAddModal, setShowAddModal] = useState(false)

  useEffect(() => {
    if (category) {
      loadSources()
      loadCounts()
    }
  }, [category])

  const loadSources = async () => {
    setLoading(true)
    const { data } = await supabase
      .from('sources')
      .select('*')
      .eq('category_id', category.id)
      .order('name')
    setSources(data || [])
    setLoading(false)
  }

  const loadCounts = async () => {
    const since = new Date(Date.now() - 7 * 86400000).toISOString()
    const { data } = await supabase
      .from('scraped_items')
      .select('source_id')
      .eq('category_slug', category.slug)
      .gte('scraped_at', since)
    if (!data) return
    const map = {}
    for (const row of data) {
      map[row.source_id] = (map[row.source_id] || 0) + 1
    }
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
    loadSources()
    loadCounts()
    onPrefChange(sourceId, true)
    setShowAddModal(false)
  }

  if (!category) return null

  const followedCount = sources.filter(s => followedSourceIds.includes(s.id)).length
  const failedCount = sources.filter(s => s.scrape_status === 'failed').length
  const healthySources = sources.filter(s => {
    const d = daysSince(s.last_scraped_at)
    return d !== null && d <= 7 && s.scrape_status !== 'failed'
  }).length

  const healthSorted = [...sources].sort((a, b) => {
    const score = (s) => {
      if (s.scrape_status === 'failed') return 3
      const d = daysSince(s.last_scraped_at)
      if (d === null) return 3
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
          <h2 className="text-sm font-semibold text-gray-700">Sources</h2>
          <p className="text-xs text-gray-400 mt-0.5">
            {tab === 'sources'
              ? `Following ${followedCount} of ${sources.length}${failedCount > 0 ? ` · ${failedCount} failed` : ''}`
              : `${healthySources} healthy · ${sources.length - healthySources} need attention`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex bg-gray-100 rounded-lg p-0.5">
            {['sources', 'health'].map(t => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`text-xs px-2.5 py-1 rounded-md font-medium capitalize transition ${
                  tab === t ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {t === 'health' ? '🩺 Health' : '📋 Sources'}
              </button>
            ))}
          </div>
          {tab === 'sources' && (
            <button
              onClick={() => setShowAddModal(true)}
              className="text-xs bg-green-600 hover:bg-green-700 text-white rounded-lg px-3 py-1.5 font-medium"
            >
              + Add source
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <p className="text-sm text-gray-400">Loading...</p>
      ) : sources.length === 0 ? (
        <p className="text-sm text-gray-400 italic">No sources configured for this category.</p>
      ) : tab === 'sources' ? (
        <div className="border border-gray-200 rounded-lg overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="py-2 px-3 text-left text-xs font-medium text-gray-500">Source</th>
                <th className="py-2 px-3 text-left text-xs font-medium text-gray-500">Type</th>
                <th className="py-2 px-3 text-left text-xs font-medium text-gray-500">Status</th>
                <th className="py-2 px-3 text-left text-xs font-medium text-gray-500">Last Run</th>
                <th className="py-2 px-3 text-left text-xs font-medium text-gray-500">Your Feed</th>
                {isAdmin && (
                  <th className="py-2 px-3 text-left text-xs font-medium text-gray-500">Global</th>
                )}
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
        <div className="border border-gray-200 rounded-lg divide-y divide-gray-100">
          <div className="flex items-center gap-3 py-1.5 px-3 bg-gray-50 rounded-t-lg">
            <span className="w-2 h-2" />
            <span className="text-xs text-gray-400 flex-1">Source</span>
            <span className="text-xs text-gray-400 w-16 text-right">Last scraped</span>
            <span className="text-xs text-gray-400 w-20 text-right">Activity</span>
            <span className="text-xs text-gray-400 w-14 text-center">Status</span>
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
