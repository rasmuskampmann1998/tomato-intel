import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../lib/supabase'

const PLATFORM_ICONS = {
  reddit: '🟠',
  twitter: '🐦',
  instagram: '📸',
  linkedin: '💼',
  facebook: '📘',
}

const TAG_COLORS = {
  ToBRFV: 'bg-red-100 text-red-700',
  TYLCV: 'bg-orange-100 text-orange-700',
  disease_resistance: 'bg-yellow-100 text-yellow-700',
  breeding: 'bg-green-100 text-green-700',
  genetics: 'bg-teal-100 text-teal-700',
  patent: 'bg-blue-100 text-blue-700',
  competitor: 'bg-purple-100 text-purple-700',
  regulation: 'bg-pink-100 text-pink-700',
  market: 'bg-indigo-100 text-indigo-700',
}

function TagBadge({ tag }) {
  const cls = TAG_COLORS[tag] || 'bg-gray-100 text-gray-600'
  return (
    <span className={`text-xs rounded px-1.5 py-0.5 ${cls}`}>{tag}</span>
  )
}

function RelevanceDot({ score }) {
  const color = score >= 7 ? 'bg-green-500' : score >= 4 ? 'bg-yellow-500' : 'bg-gray-400'
  return (
    <span className="flex items-center gap-1 text-xs text-gray-500">
      <span className={`w-2 h-2 rounded-full ${color}`} />
      {score}/10
    </span>
  )
}

function ResultCard({ item, isNew }) {
  const si = item.scraped_items
  const ii = si?.interpreted_items
  const title = ii?.title_en || si?.title || '(no title)'
  const summary = ii?.summary_en || si?.content?.slice(0, 200) || ''
  const date = si?.published_at
    ? new Date(si.published_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
    : si?.scraped_at
      ? new Date(si.scraped_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
      : ''
  const platform = si?.platform
  const tags = ii?.tags || []
  const score = ii?.relevance_score

  return (
    <div className={`border rounded-lg p-4 bg-white ${isNew ? 'border-green-300' : 'border-gray-200'}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <a
            href={si?.url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-gray-900 text-sm hover:text-green-700 line-clamp-2"
          >
            {platform && <span className="mr-1">{PLATFORM_ICONS[platform] || ''}</span>}
            {title}
          </a>
          {summary && (
            <p className="text-xs text-gray-500 mt-1 line-clamp-3">{summary}</p>
          )}
          <div className="flex flex-wrap items-center gap-2 mt-2">
            {tags.slice(0, 5).map(t => <TagBadge key={t} tag={t} />)}
            <span className="text-xs text-gray-400">{date}</span>
            {score && <RelevanceDot score={score} />}
          </div>
        </div>
        {isNew && (
          <span className="shrink-0 text-xs bg-green-100 text-green-700 rounded-full px-2 py-0.5">new</span>
        )}
      </div>
    </div>
  )
}

export default function ResultsFeed({ profile }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [filter, setFilter] = useState('all') // 'all' | 'new'
  const [sortBy, setSortBy] = useState('date') // 'date' | 'relevance'
  const [page, setPage] = useState(0)
  const PAGE_SIZE = 25

  const loadItems = useCallback(async () => {
    if (!profile) return
    setLoading(true)

    let query = supabase
      .from('profile_items')
      .select(`
        id, is_new,
        scraped_items (
          id, title, url, content, published_at, scraped_at, platform, language,
          interpreted_items (title_en, summary_en, relevance_score, tags)
        )
      `)
      .eq('search_profile_id', profile.id)

    if (filter === 'new') query = query.eq('is_new', true)

    if (sortBy === 'relevance') {
      // sort done client-side after fetch since it's on a joined table
    } else {
      query = query.order('matched_at', { ascending: false })
    }

    query = query.range(page * PAGE_SIZE, (page + 1) * PAGE_SIZE - 1)

    const { data, error } = await query
    if (!error) {
      let results = data || []
      if (sortBy === 'relevance') {
        results = results.sort((a, b) =>
          (b.scraped_items?.interpreted_items?.relevance_score || 0) - (a.scraped_items?.interpreted_items?.relevance_score || 0)
        )
      }
      setItems(results)
    }
    setLoading(false)

    // Mark new items as seen
    if (filter !== 'new' && data?.some(i => i.is_new)) {
      const newIds = data.filter(i => i.is_new).map(i => i.id)
      await supabase.from('profile_items').update({ is_new: false }).in('id', newIds)
      // Update badge count
      await supabase
        .from('search_profiles')
        .update({ new_since_last_visit: 0 })
        .eq('id', profile.id)
    }
  }, [profile, filter, sortBy, page])

  useEffect(() => {
    setPage(0)
    setItems([])
  }, [profile, filter, sortBy])

  useEffect(() => {
    loadItems()
  }, [loadItems])

  if (!profile) {
    return (
      <div className="flex items-center justify-center h-48 text-sm text-gray-400">
        Select a search profile to see results
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h3 className="text-sm font-semibold text-gray-700">
          Results for "{profile.name || profile.search_terms.join(', ')}"
        </h3>
        <div className="flex gap-2 items-center">
          <div className="flex rounded-lg border border-gray-200 overflow-hidden text-xs">
            {['all', 'new'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 ${filter === f ? 'bg-green-600 text-white' : 'text-gray-600 bg-white hover:bg-gray-50'}`}
              >
                {f === 'all' ? 'All' : 'New only'}
              </button>
            ))}
          </div>
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value)}
            className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 text-gray-600"
          >
            <option value="date">Sort: Date</option>
            <option value="relevance">Sort: Relevance</option>
          </select>
        </div>
      </div>

      {loading && <div className="text-sm text-gray-400 py-4 text-center">Loading...</div>}

      {!loading && items.length === 0 && (
        <div className="text-sm text-gray-400 py-8 text-center">
          No results yet. Scrapers run on schedule and will populate this feed.
        </div>
      )}

      <div className="space-y-2">
        {items.map(item => (
          <ResultCard key={item.id} item={item} isNew={item.is_new} />
        ))}
      </div>

      {items.length === PAGE_SIZE && (
        <button
          onClick={() => setPage(p => p + 1)}
          className="w-full text-sm text-green-600 hover:text-green-700 py-2 border border-gray-200 rounded-lg"
        >
          Load more
        </button>
      )}
    </div>
  )
}
