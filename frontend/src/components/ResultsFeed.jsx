import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../lib/supabase'

const PLATFORM_ICONS = {
  reddit: '🟠', twitter: '𝕏', instagram: '📸', linkedin: '💼', facebook: '📘',
}

const LANG_NAMES = {
  en: 'English', es: 'Spanish', pt: 'Portuguese', zh: 'Chinese',
  hi: 'Hindi', ja: 'Japanese', ru: 'Russian', ar: 'Arabic',
  tr: 'Turkish', fr: 'French', de: 'German', nl: 'Dutch',
  da: 'Danish', sv: 'Swedish', ko: 'Korean', it: 'Italian',
  he: 'Hebrew', id: 'Indonesian',
}

const LANG_FLAGS = {
  en: '🇬🇧', es: '🇪🇸', pt: '🇧🇷', zh: '🇨🇳', hi: '🇮🇳', ja: '🇯🇵',
  ru: '🇷🇺', ar: '🇸🇦', tr: '🇹🇷', fr: '🇫🇷', de: '🇩🇪', nl: '🇳🇱',
  da: '🇩🇰', sv: '🇸🇪', ko: '🇰🇷', it: '🇮🇹', he: '🇮🇱', id: '🇮🇩',
}

// ZH → EN chip, or plain EN chip
function LangChip({ lang }) {
  if (!lang) return null
  const isEn = lang === 'en'
  const code = lang.toUpperCase()
  const name = LANG_NAMES[lang] || code
  return (
    <span
      className="font-mono text-[10px] tracking-[0.12em] uppercase px-1.5 py-0.5 border border-rule bg-paper-deep text-ink-mute flex items-center gap-1"
      title={isEn ? 'English' : `Translated from ${name}`}
    >
      {!isEn && <>{code} <span className="text-tomato">→</span> </>}EN
    </span>
  )
}

const TAG_COLORS = {
  ToBRFV: 'bg-tomato-soft text-tomato border-tomato/20',
  TYLCV: 'bg-amber/10 text-amber border-amber/20',
  disease_resistance: 'bg-amber/10 text-amber border-amber/20',
  breeding: 'bg-leaf/10 text-leaf border-leaf/20',
  genetics: 'bg-leaf/10 text-leaf border-leaf/20',
  patent: 'bg-paper-deep text-ink-soft border-rule',
  competitor: 'bg-paper-deep text-ink-soft border-rule',
  regulation: 'bg-paper-deep text-ink-soft border-rule',
  market: 'bg-paper-deep text-ink-soft border-rule',
}

function TagPill({ tag }) {
  const cls = TAG_COLORS[tag] || 'bg-paper-deep text-ink-mute border-rule'
  return (
    <span className={`font-mono text-[10px] tracking-[0.1em] uppercase border px-1.5 py-0.5 ${cls}`}>
      {tag}
    </span>
  )
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
    return `<div style="margin-bottom:18px;padding-bottom:18px;border-bottom:1px solid #D9CFB8">
      <a href="${url}" style="font-weight:600;color:#1A1614;font-size:13px;text-decoration:none">${title}</a>
      ${summary ? `<p style="margin:5px 0 0;font-size:12px;color:#4A413A;line-height:1.5">${summary}</p>` : ''}
      <div style="font-size:11px;color:#8A7E72;margin-top:5px;font-family:monospace">
        ${date}${score ? ` · ${score}` : ''}${tags ? ` · ${tags}` : ''}
      </div>
    </div>`
  }).join('')

  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${safe(profileName)}</title>
    <style>
      body { font-family: Georgia, serif; max-width: 680px; margin: 40px auto; padding: 0 24px; color: #1A1614; background: #F5F0E6 }
      h1 { font-size: 22px; font-weight: 400; margin-bottom: 4px }
      p.meta { font-size: 11px; color: #8A7E72; margin: 0 0 28px; font-family: monospace }
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

// ── Expanded body shown inside a card when clicked ───────────────────────────

function ExpandedBody({ si, ii, showOriginal }) {
  const lang = si?.language || 'en'
  const isEn = lang === 'en'
  const langName = LANG_NAMES[lang] || lang.toUpperCase()

  const summaryEn = ii?.summary_en || si?.content?.slice(0, 600) || ''
  const summaryOriginal = si?.content ? si.content.slice(0, 600) : ''
  const bodyRaw = si?.content || ''
  const bodyPreview = bodyRaw.slice(0, 1500)
  const hasMore = bodyRaw.length > 1500

  return (
    <div className="mt-3 pt-3 border-t border-rule space-y-3">
      {/* English abstract */}
      {summaryEn && (
        <p className="text-sm text-ink-soft leading-relaxed">{summaryEn}</p>
      )}

      {/* Full body if available */}
      {bodyPreview && bodyPreview !== summaryEn && (
        <p className="text-xs text-ink-mute leading-relaxed whitespace-pre-line">
          {bodyPreview}{hasMore ? '…' : ''}
        </p>
      )}

      {/* Original-language section for non-English */}
      {!isEn && !showOriginal && summaryOriginal && summaryOriginal !== summaryEn && (
        <details className="group">
          <summary className="font-mono text-[10px] tracking-[0.14em] uppercase text-tomato cursor-pointer hover:text-tomato-deep list-none">
            View original ({langName}) ▸
          </summary>
          <p
            className="mt-2 text-xs text-ink-soft leading-relaxed"
            dir={lang === 'ar' ? 'rtl' : 'ltr'}
            lang={lang}
          >
            {summaryOriginal}
          </p>
        </details>
      )}

      {si?.url && (
        <a
          href={si.url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={e => e.stopPropagation()}
          className="font-mono text-[10px] tracking-[0.12em] uppercase text-tomato hover:text-tomato-deep"
        >
          Open source ↗
        </a>
      )}
    </div>
  )
}

// ── Score dot ─────────────────────────────────────────────────────────────────

function ScoreDot({ score }) {
  if (!score) return null
  const color = score >= 7 ? 'bg-leaf' : score >= 4 ? 'bg-amber' : 'bg-ink-mute'
  return (
    <span className="flex items-center gap-1 font-mono text-[10px] text-ink-mute">
      <span className={`w-1.5 h-1.5 rounded-full ${color}`} />{score}/10
    </span>
  )
}

// ── Card variants ─────────────────────────────────────────────────────────────

function ResultCard({ item, isNew, showOriginal }) {
  const [expanded, setExpanded] = useState(false)
  const si = item.scraped_items
  const ii = si?.interpreted_items
  const lang = si?.language || 'en'
  const title = (showOriginal || lang === 'en')
    ? (si?.title || ii?.title_en || '(no title)')
    : (ii?.title_en || si?.title || '(no title)')

  return (
    <div
      className={`border border-rule bg-paper cursor-pointer transition-colors hover:bg-paper-deep ${isNew ? 'border-l-2 border-l-tomato' : ''} ${expanded ? 'bg-paper-deep' : ''}`}
      onClick={() => setExpanded(v => !v)}
    >
      <div className="px-4 py-3">
        {/* Meta row */}
        <div className="flex items-center gap-2 mb-1.5">
          <span className="font-mono text-[10px] text-ink-mute">{formatDate(si)}</span>
          <LangChip lang={lang} />
          <ScoreDot score={ii?.relevance_score} />
          {isNew && (
            <span className="font-mono text-[10px] tracking-[0.12em] uppercase bg-tomato text-paper px-1.5 py-0.5">new</span>
          )}
          <span className="ml-auto text-ink-mute text-xs">{expanded ? '▲' : '▼'}</span>
        </div>

        {/* Title */}
        <a
          href={si?.url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={e => e.stopPropagation()}
          className="font-display text-[15px] font-400 text-ink hover:text-tomato leading-snug block"
        >
          {si?.platform && <span className="mr-1 font-body">{PLATFORM_ICONS[si.platform] || ''}</span>}
          {title}
        </a>

        {/* Summary (collapsed) */}
        {!expanded && (
          <p className="text-xs text-ink-mute mt-1 line-clamp-2 leading-relaxed">
            {ii?.summary_en || si?.content?.slice(0, 180) || ''}
          </p>
        )}

        {/* Tags */}
        {(ii?.tags || []).length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {(ii.tags).slice(0, expanded ? 99 : 5).map(t => <TagPill key={t} tag={t} />)}
          </div>
        )}
      </div>

      {expanded && (
        <div className="px-4 pb-3">
          <ExpandedBody si={si} ii={ii} showOriginal={showOriginal} />
        </div>
      )}
    </div>
  )
}

function AlertCard({ item, isNew, showOriginal }) {
  const [expanded, setExpanded] = useState(false)
  const si = item.scraped_items
  const ii = si?.interpreted_items
  const lang = si?.language || 'en'
  const title = (showOriginal || lang === 'en')
    ? (si?.title || ii?.title_en || '(no title)')
    : (ii?.title_en || si?.title || '(no title)')
  const score = ii?.relevance_score || 0
  const accentColor = score >= 7 ? 'border-l-tomato' : score >= 4 ? 'border-l-amber' : 'border-l-rule'
  const urgencyLabel = score >= 7 ? 'HIGH' : score >= 4 ? 'MED' : 'LOW'
  const urgencyColor = score >= 7 ? 'bg-tomato-soft text-tomato' : score >= 4 ? 'bg-amber/10 text-amber' : 'bg-paper-deep text-ink-mute'

  return (
    <div
      className={`border border-rule border-l-4 ${accentColor} bg-paper cursor-pointer hover:bg-paper-deep ${expanded ? 'bg-paper-deep' : ''}`}
      onClick={() => setExpanded(v => !v)}
    >
      <div className="px-4 py-3">
        <div className="flex items-center gap-2 mb-1.5">
          <span className={`font-mono text-[10px] tracking-[0.12em] uppercase px-1.5 py-0.5 ${urgencyColor}`}>{urgencyLabel}</span>
          <span className="font-mono text-[10px] text-ink-mute">{formatDate(si)}</span>
          <LangChip lang={lang} />
          {isNew && <span className="font-mono text-[10px] tracking-[0.12em] uppercase bg-tomato text-paper px-1.5 py-0.5">new</span>}
          <span className="ml-auto text-ink-mute text-xs">{expanded ? '▲' : '▼'}</span>
        </div>
        <a
          href={si?.url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={e => e.stopPropagation()}
          className="font-display text-[15px] font-400 text-ink hover:text-tomato leading-snug block"
        >
          {title}
        </a>
        {!expanded && (
          <p className="text-xs text-ink-mute mt-1 line-clamp-2 leading-relaxed">
            {ii?.summary_en || si?.content?.slice(0, 180) || ''}
          </p>
        )}
        {(ii?.tags || []).length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {(ii.tags).slice(0, expanded ? 99 : 4).map(t => <TagPill key={t} tag={t} />)}
          </div>
        )}
      </div>
      {expanded && (
        <div className="px-4 pb-3">
          <ExpandedBody si={si} ii={ii} showOriginal={showOriginal} />
        </div>
      )}
    </div>
  )
}

function DataCard({ item, isNew, showOriginal }) {
  const [expanded, setExpanded] = useState(false)
  const si = item.scraped_items
  const ii = si?.interpreted_items
  const lang = si?.language || 'en'
  const title = (showOriginal || lang === 'en')
    ? (si?.title || ii?.title_en || '(no title)')
    : (ii?.title_en || si?.title || '(no title)')
  const score = ii?.relevance_score || 0
  const barWidth = `${(score / 10) * 100}%`
  const barColor = score >= 7 ? 'bg-tomato' : score >= 4 ? 'bg-amber' : 'bg-rule'

  return (
    <div
      className={`border border-rule bg-paper cursor-pointer hover:bg-paper-deep ${isNew ? 'border-l-2 border-l-tomato' : ''} ${expanded ? 'bg-paper-deep' : ''}`}
      onClick={() => setExpanded(v => !v)}
    >
      <div className="px-4 py-3 flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-[10px] text-ink-mute">{formatDate(si)}</span>
            <LangChip lang={lang} />
            {isNew && <span className="font-mono text-[10px] tracking-[0.12em] uppercase bg-tomato text-paper px-1.5 py-0.5">new</span>}
          </div>
          <a
            href={si?.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={e => e.stopPropagation()}
            className="font-display text-[14px] text-ink hover:text-tomato line-clamp-1 block"
          >
            {title}
          </a>
          {(ii?.tags || []).length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {(ii.tags).slice(0, expanded ? 99 : 6).map(t => <TagPill key={t} tag={t} />)}
            </div>
          )}
        </div>
        <div className="shrink-0 flex flex-col items-end gap-1.5 pt-0.5">
          <span className="font-mono text-[10px] text-ink-mute">{score}/10</span>
          <div className="w-14 h-1 bg-rule overflow-hidden">
            <div className={`h-full ${barColor}`} style={{ width: barWidth }} />
          </div>
          <span className="text-ink-mute text-xs">{expanded ? '▲' : '▼'}</span>
        </div>
      </div>
      {expanded && (
        <div className="px-4 pb-3">
          <ExpandedBody si={si} ii={ii} showOriginal={showOriginal} />
        </div>
      )}
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
  const [minRelevance, setMinRelevance] = useState(0)
  const [langFilter, setLangFilter] = useState('all')
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
    if (minRelevance > 0) {
      results = results.filter(item =>
        (item.scraped_items?.interpreted_items?.relevance_score || 0) >= minRelevance
      )
    }
    if (sortBy === 'relevance') {
      results = results.sort((a, b) =>
        (b.scraped_items?.interpreted_items?.relevance_score || 0) -
        (a.scraped_items?.interpreted_items?.relevance_score || 0)
      )
    }

    setItems(results)
    setLoading(false)
  }, [profile, category, filter, sortBy, minRelevance, page, followedSourceIds])

  const [newCount, setNewCount] = useState(0)

  useEffect(() => { setPage(0); setItems([]); setNewCount(0); setLangFilter('all') }, [profile, filter, sortBy, minRelevance])
  useEffect(() => { loadItems() }, [loadItems])

  useEffect(() => {
    if (!profile?.id) return
    const channel = supabase
      .channel(`profile-items-${profile.id}`)
      .on('postgres_changes', {
        event: 'INSERT',
        schema: 'public',
        table: 'profile_items',
        filter: `search_profile_id=eq.${profile.id}`,
      }, () => setNewCount(n => n + 1))
      .subscribe()
    return () => supabase.removeChannel(channel)
  }, [profile?.id])

  const availableLangs = [...new Set(items.map(i => i.scraped_items?.language).filter(Boolean))]
  const displayItems = langFilter === 'all'
    ? items
    : items.filter(i => i.scraped_items?.language === langFilter)

  const Card = CARD_COMPONENTS[cardStyle] || ResultCard
  const profileName = profile?.name || profile?.search_terms?.join(', ') || 'export'

  if (!profile) {
    return (
      <div className="flex items-center justify-center h-48 text-sm text-ink-mute font-display italic">
        Select a search profile to see results
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <span className="font-mono text-[10px] tracking-[0.14em] uppercase text-ink-mute truncate max-w-[220px]">
          {profileName}
        </span>

        <div className="flex items-center gap-2 flex-wrap">
          {/* All / New */}
          <div className="flex border border-rule overflow-hidden font-mono text-[10px] tracking-[0.1em] uppercase">
            {['all', 'new'].map(f => (
              <button key={f} onClick={() => setFilter(f)}
                className={`px-3 py-1.5 transition ${filter === f ? 'bg-ink text-paper' : 'text-ink-soft hover:bg-paper-deep'}`}>
                {f === 'all' ? 'All' : 'New'}
              </button>
            ))}
          </div>

          {/* Sort */}
          <select value={sortBy} onChange={e => setSortBy(e.target.value)}
            className="font-mono text-[10px] tracking-[0.1em] uppercase border border-rule px-2 py-1.5 bg-paper text-ink-soft">
            <option value="date">Date</option>
            <option value="relevance">Relevance</option>
          </select>

          {/* Relevance */}
          <select value={minRelevance} onChange={e => setMinRelevance(Number(e.target.value))}
            className="font-mono text-[10px] tracking-[0.1em] uppercase border border-rule px-2 py-1.5 bg-paper text-ink-soft">
            <option value={0}>All scores</option>
            <option value={5}>5+ relevant</option>
            <option value={7}>7+ important</option>
            <option value={9}>9+ critical</option>
          </select>

          {/* Language filter — only shown when multiple languages present */}
          {availableLangs.length > 1 && (
            <select
              value={langFilter}
              onChange={e => setLangFilter(e.target.value)}
              className="font-mono text-[10px] tracking-[0.1em] uppercase border border-rule px-2 py-1.5 bg-paper text-ink-soft"
            >
              <option value="all">All langs</option>
              {availableLangs.map(lang => (
                <option key={lang} value={lang}>
                  {LANG_FLAGS[lang] || ''} {lang.toUpperCase()}
                </option>
              ))}
            </select>
          )}

          {/* Original / Translated toggle */}
          <button
            onClick={() => setShowOriginal(v => !v)}
            className={`font-mono text-[10px] tracking-[0.1em] uppercase border px-2.5 py-1.5 transition ${
              showOriginal ? 'bg-ink text-paper border-ink' : 'border-rule text-ink-soft hover:bg-paper-deep'
            }`}
            title={showOriginal ? 'Showing original language' : 'Showing English abstracts'}
          >
            {showOriginal ? 'Original' : 'Translated'}
          </button>

          {/* Export */}
          <div className="flex border border-rule overflow-hidden font-mono text-[10px] tracking-[0.1em] uppercase">
            <button
              onClick={() => exportCSV(displayItems, profileName)}
              disabled={displayItems.length === 0}
              className="px-2.5 py-1.5 text-ink-soft hover:bg-paper-deep disabled:opacity-40 transition"
            >↓ CSV</button>
            <span className="w-px bg-rule shrink-0" />
            <button
              onClick={() => exportPDF(displayItems, profileName)}
              disabled={displayItems.length === 0}
              className="px-2.5 py-1.5 text-ink-soft hover:bg-paper-deep disabled:opacity-40 transition"
            >↓ PDF</button>
          </div>
        </div>
      </div>

      {newCount > 0 && (
        <button
          onClick={() => { setNewCount(0); loadItems() }}
          className="w-full font-mono text-[10px] tracking-[0.12em] uppercase border border-tomato text-tomato bg-tomato-soft py-2 hover:bg-tomato hover:text-paper transition"
        >
          ↑ {newCount} new {newCount === 1 ? 'result' : 'results'} — click to refresh
        </button>
      )}

      {loading && (
        <div className="font-mono text-[10px] tracking-[0.14em] uppercase text-ink-mute py-8 text-center">
          Loading…
        </div>
      )}

      {!loading && displayItems.length === 0 && (
        <div className="py-12 text-center border border-rule bg-paper">
          <p className="font-display italic text-ink-mute text-base">No results yet.</p>
          <p className="font-mono text-[10px] tracking-[0.12em] uppercase text-ink-mute mt-1">
            Scrapers run on schedule and will populate this feed.
          </p>
        </div>
      )}

      <div className="space-y-px">
        {displayItems.map(item => (
          <Card key={item.id} item={item} isNew={item.is_new} showOriginal={showOriginal} />
        ))}
      </div>

      {items.length === PAGE_SIZE && (
        <button
          onClick={() => setPage(p => p + 1)}
          className="w-full font-mono text-[10px] tracking-[0.12em] uppercase text-tomato border border-rule py-2 hover:bg-paper-deep transition"
        >
          Load more
        </button>
      )}
    </div>
  )
}
