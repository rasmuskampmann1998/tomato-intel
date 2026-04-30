import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../lib/supabase'

const PLATFORM_ICONS = {
  reddit: '🟠', twitter: '🐦', instagram: '📸', linkedin: '💼', facebook: '📘',
}

const LANG_FLAGS = {
  nl: '🇳🇱', de: '🇩🇪', fr: '🇫🇷', zh: '🇨🇳', hi: '🇮🇳',
  es: '🇪🇸', pt: '🇧🇷', ja: '🇯🇵', ar: '🇸🇦', ko: '🇰🇷',
  da: '🇩🇰', sv: '🇸🇪', no: '🇳🇴', fi: '🇫🇮', it: '🇮🇹',
  ru: '🇷🇺', pl: '🇵🇱', tr: '🇹🇷', id: '🇮🇩', th: '🇹🇭',
  en: '🇬🇧',
}

function LanguageBadge({ lang }) {
  if (!lang) return null
  const flag = LANG_FLAGS[lang] || '🌐'
  return (
    <span className="text-xs text-gray-400 flex items-center gap-0.5">
      {flag} {lang.toUpperCase()}
    </span>
  )
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
  return <span className={`text-xs rounded px-1.5 py-0.5 ${cls}`}>{tag}</span>
}

function formatDate(si) {
  const d = si?.published_at || si?.scraped_at
  if (!d) return ''
  return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

// ── Export helpers ────────────────────────────────────────────────────────────

function exportCSV(items, profileName) {
  const cols = ['Title', 'Summary', 'URL', 'Date', 'Tags', 'Relevance', 'Language']
  const rows = items.map(item => {
    const si = item.scraped_items
    const ii = si?.interpreted_items
    return [
      ii?.title_en || si?.title || '',
      ii?.summary_en || '',
      si?.url || '',
      si?.published_at ? new Date(si.published_at).toLocaleDateString('en-GB') : '',
      (ii?.tags || []).join('; '),
      ii?.relevance_score || '',
      si?.language || '',
    ].map(v => `"${String(v).replace(/"/g, '""')}"`)
  })
  const csv = [cols.join(','), ...rows.map(r => r.join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `tomato-intel-${profileName.replace(/[^a-z0-9]/gi, '-').toLowerCase()}-${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(a.href)
}

function exportPDF(items, profileName) {
  const safe = s => String(s || '').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  const rows = items.map(item => {
    const si = item.scraped_items
    const ii = si?.interpreted_items
    const title = safe(ii?.title_en || si?.title || '')
    const summary = safe(ii?.summary_en || '')
    const tags = safe((ii?.tags || []).join(', '))
    const date = si?.published_at ? new Date(si.published_at).toLocaleDateString('en-GB') : ''
    const score = ii?.relevance_score ? `${ii.relevance_score}/10` : ''
    const url = si?.url || '#'
    return `<div style="margin-bottom:18px;padding-bottom:18px;border-bottom:1px solid #e5e7eb">
      <a href="${url}" style="font-weight:600;color:#111827;font-size:13px;text-decoration:none">${title}</a>
      ${summary ? `<p style="margin:5px 0 0;font-size:12px;color:#4b5563;line-height:1.5">${summary}</p>` : ''}
      <div style="font-size:11px;color:#9ca3af;margin-top:5px">
        ${date}${score ? ` · Relevance ${score}` : ''}${tags ? ` · ${tags}` : ''}
      </div>
    </div>`
  }).join('')

  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${safe(profileName)}</title>
    <style>
      body { font-family: -apple-system, sans-serif; max-width: 700px; margin: 40px auto; padding: 0 24px; color: #111827 }
      h1 { font-size: 15px; font-weight: 700; margin-bottom: 6px }
      p.meta { font-size: 11px; color: #6b7280; margin: 0 0 28px }
      @media print { a { color: #111827 } }
    </style></head>
    <body>
      <h1>Tomato Intel — ${safe(profileName)}</h1>
      <p class="meta">Exported ${new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })} · ${items.length} results</p>
      ${rows}
    </body></html>`

  const w = window.open('', '_blank')
  w.document.write(html)
  w.document.close()
  w.focus()
  setTimeout(() => w.print(), 400)
}

// ── Card variants ─────────────────────────────────────────────────────────────

function ResultCard({ item, isNew, showOriginal }) {
  const si = item.scraped_items
  const ii = si?.interpreted_items
  const title   = showOriginal ? (si?.title || '') : (ii?.title_en || si?.title || '(no title)')
  const summary = showOriginal ? (si?.content?.slice(0, 300) || '') : (ii?.summary_en || si?.content?.slice(0, 220) || '')
  const score = ii?.relevance_score
  const scoreColor = score >= 7 ? 'bg-green-500' : score >= 4 ? 'bg-yellow-500' : 'bg-gray-400'

  return (
    <div className={`border rounded-lg p-4 bg-white ${isNew ? 'border-green-300' : 'border-gray-200'}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <a href={si?.url} target="_blank" rel="noopener noreferrer"
            className="font-medium text-gray-900 text-sm hover:text-green-700 line-clamp-2">
            {si?.platform && <span className="mr-1">{PLATFORM_ICONS[si.platform] || ''}</span>}
            {title}
          </a>
          {summary && <p className="text-xs text-gray-500 mt-1 line-clamp-3">{summary}</p>}
          <div className="flex flex-wrap items-center gap-2 mt-2">
            {(ii?.tags || []).slice(0, 5).map(t => <TagBadge key={t} tag={t} />)}
            <span className="text-xs text-gray-400">{formatDate(si)}</span>
            <LanguageBadge lang={si?.language} />
            {score && (
              <span className="flex items-center gap-1 text-xs text-gray-500">
                <span className={`w-2 h-2 rounded-full ${scoreColor}`} />{score}/10
              </span>
            )}
          </div>
        </div>
        {isNew && <span className="shrink-0 text-xs bg-green-100 text-green-700 rounded-full px-2 py-0.5">new</span>}
      </div>
    </div>
  )
}

function AlertCard({ item, isNew, showOriginal }) {
  const si = item.scraped_items
  const ii = si?.interpreted_items
  const title   = showOriginal ? (si?.title || '') : (ii?.title_en || si?.title || '(no title)')
  const summary = showOriginal ? (si?.content?.slice(0, 200) || '') : (ii?.summary_en || si?.content?.slice(0, 150) || '')
  const score = ii?.relevance_score || 0
  const urgencyColor = score >= 7 ? 'border-red-400 bg-red-50' : score >= 4 ? 'border-yellow-400 bg-yellow-50' : 'border-gray-200 bg-white'
  const urgencyLabel = score >= 7 ? 'High' : score >= 4 ? 'Medium' : 'Low'
  const urgencyBadge = score >= 7 ? 'bg-red-100 text-red-700' : score >= 4 ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-500'

  return (
    <div className={`border-l-4 rounded-lg p-4 ${urgencyColor} ${isNew ? 'ring-1 ring-green-300' : ''}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-medium rounded-full px-2 py-0.5 ${urgencyBadge}`}>{urgencyLabel}</span>
            <span className="text-xs text-gray-400">{formatDate(si)}</span>
            <LanguageBadge lang={si?.language} />
            {isNew && <span className="text-xs bg-green-100 text-green-700 rounded-full px-2 py-0.5">new</span>}
          </div>
          <a href={si?.url} target="_blank" rel="noopener noreferrer"
            className="font-semibold text-gray-900 text-sm hover:text-green-700 line-clamp-2 block">
            {title}
          </a>
          {summary && <p className="text-xs text-gray-600 mt-1 line-clamp-2">{summary}</p>}
          {(ii?.tags || []).length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {(ii.tags).slice(0, 4).map(t => <TagBadge key={t} tag={t} />)}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function DataCard({ item, isNew, showOriginal }) {
  const si = item.scraped_items
  const ii = si?.interpreted_items
  const title = showOriginal ? (si?.title || '') : (ii?.title_en || si?.title || '(no title)')
  const score = ii?.relevance_score || 0
  const barWidth = `${(score / 10) * 100}%`
  const barColor = score >= 7 ? 'bg-purple-500' : score >= 4 ? 'bg-blue-400' : 'bg-gray-300'

  return (
    <div className={`border rounded-lg p-3 bg-white flex items-center gap-3 ${isNew ? 'border-purple-300' : 'border-gray-200'}`}>
      <div className="flex-1 min-w-0">
        <a href={si?.url} target="_blank" rel="noopener noreferrer"
          className="text-sm font-medium text-gray-900 hover:text-purple-700 line-clamp-1 block">
          {title}
        </a>
        <div className="flex flex-wrap items-center gap-1.5 mt-1">
          {(ii?.tags || []).slice(0, 6).map(t => <TagBadge key={t} tag={t} />)}
          <span className="text-xs text-gray-400 ml-1">{formatDate(si)}</span>
          <LanguageBadge lang={si?.language} />
        </div>
      </div>
      <div className="shrink-0 w-16 flex flex-col items-end gap-1">
        <span className="text-xs text-gray-400">{score}/10</span>
        <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div className={`h-full rounded-full ${barColor}`} style={{ width: barWidth }} />
        </div>
        {isNew && <span className="text-xs text-purple-600 font-medium">new</span>}
      </div>
    </div>
  )
}

const CARD_COMPONENTS = { article: ResultCard, alert: AlertCard, data: DataCard }

// ── Main feed component ───────────────────────────────────────────────────────
const SCRAPED_SELECT = `
  id, title, url, content, published_at, scraped_at, platform, language, source_id,
  interpreted_items (title_en, summary_en, relevance_score, tags)
`

export default function ResultsFeed({ profile, category, cardStyle = 'article', followedSourceIds = [], userId }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [filter, setFilter] = useState('all')
  const [sortBy, setSortBy] = useState('date')
  const [showOriginal, setShowOriginal] = useState(false)
  const [page, setPage] = useState(0)
  const PAGE_SIZE = 25

  const loadItems = useCallback(async () => {
    if (!profile) return
    setLoading(true)

    let results = []
    let piQuery = supabase
      .from('profile_items')
      .select(`id, is_new, matched_at, scraped_items!inner (${SCRAPED_SELECT})`)
      .eq('search_profile_id', profile.id)

    // Wire up language filter from profile
    if (profile.languages?.length > 0) {
      piQuery = piQuery.filter('scraped_items.language', 'in', `(${profile.languages.join(',')})`)
    }

    const { data: piData } = await (filter === 'new' ? piQuery.eq('is_new', true) : piQuery)
      .order('matched_at', { ascending: false })
      .range(page * PAGE_SIZE, (page + 1) * PAGE_SIZE - 1)

    if (piData?.length > 0) {
      results = piData
      if (filter !== 'new' && piData.some(i => i.is_new)) {
        const newIds = piData.filter(i => i.is_new).map(i => i.id)
        await supabase.from('profile_items').update({ is_new: false }).in('id', newIds)
        await supabase.from('search_profiles').update({ new_since_last_visit: 0 }).eq('id', profile.id)
      }
    } else if (category?.slug) {
      let siQuery = supabase
        .from('scraped_items')
        .select(SCRAPED_SELECT)
        .eq('category_slug', category.slug)
      if (profile.languages?.length > 0) {
        siQuery = siQuery.in('language', profile.languages)
      }
      const { data: siData } = await siQuery
        .order('scraped_at', { ascending: false })
        .range(page * PAGE_SIZE, (page + 1) * PAGE_SIZE - 1)
      results = (siData || []).map(si => ({ id: si.id, is_new: false, scraped_items: si }))
    }

    if (followedSourceIds.length > 0) {
      results = results.filter(item => followedSourceIds.includes(item.scraped_items?.source_id))
    }
    if (sortBy === 'relevance') {
      results = results.sort((a, b) =>
        (b.scraped_items?.interpreted_items?.relevance_score || 0) -
        (a.scraped_items?.interpreted_items?.relevance_score || 0)
      )
    }

    setItems(results)
    setLoading(false)
  }, [profile, category, filter, sortBy, page, followedSourceIds])

  useEffect(() => { setPage(0); setItems([]) }, [profile, filter, sortBy])
  useEffect(() => { loadItems() }, [loadItems])

  const Card = CARD_COMPONENTS[cardStyle] || ResultCard
  const profileName = profile?.name || profile?.search_terms?.join(', ') || 'export'

  if (!profile) {
    return (
      <div className="flex items-center justify-center h-48 text-sm text-gray-400">
        Select a search profile to see results
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <h3 className="text-sm font-semibold text-gray-700 truncate max-w-[200px]">
          "{profileName}"
        </h3>

        <div className="flex items-center gap-2 flex-wrap">
          {/* New / All toggle */}
          <div className="flex rounded-lg border border-gray-200 overflow-hidden text-xs">
            {['all', 'new'].map(f => (
              <button key={f} onClick={() => setFilter(f)}
                className={`px-3 py-1.5 ${filter === f ? 'bg-green-600 text-white' : 'text-gray-600 bg-white hover:bg-gray-50'}`}>
                {f === 'all' ? 'All' : 'New only'}
              </button>
            ))}
          </div>

          {/* Sort */}
          <select value={sortBy} onChange={e => setSortBy(e.target.value)}
            className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 text-gray-600">
            <option value="date">Sort: Date</option>
            <option value="relevance">Sort: Relevance</option>
          </select>

          {/* Original / Translated toggle */}
          <button
            onClick={() => setShowOriginal(v => !v)}
            className={`text-xs rounded-lg px-2.5 py-1.5 border transition ${
              showOriginal
                ? 'bg-gray-800 text-white border-gray-800'
                : 'border-gray-200 text-gray-600 hover:bg-gray-50'
            }`}
            title={showOriginal ? 'Showing original language' : 'Showing English translation'}
          >
            {showOriginal ? '🌐 Original' : '🇬🇧 Translated'}
          </button>

          {/* Export */}
          <div className="flex items-center rounded-lg border border-gray-200 overflow-hidden text-xs">
            <button
              onClick={() => exportCSV(items, profileName)}
              disabled={items.length === 0}
              className="px-2.5 py-1.5 text-gray-600 hover:bg-gray-50 disabled:opacity-40 transition"
              title="Export as CSV"
            >↓ CSV</button>
            <span className="w-px h-4 bg-gray-200 shrink-0" />
            <button
              onClick={() => exportPDF(items, profileName)}
              disabled={items.length === 0}
              className="px-2.5 py-1.5 text-gray-600 hover:bg-gray-50 disabled:opacity-40 transition"
              title="Export as PDF"
            >↓ PDF</button>
          </div>
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
          <Card key={item.id} item={item} isNew={item.is_new} showOriginal={showOriginal} />
        ))}
      </div>

      {items.length === PAGE_SIZE && (
        <button onClick={() => setPage(p => p + 1)}
          className="w-full text-sm text-green-600 hover:text-green-700 py-2 border border-gray-200 rounded-lg">
          Load more
        </button>
      )}
    </div>
  )
}
