import { useState, useEffect, useCallback, useRef } from 'react'
import { supabase } from '../lib/supabase'

const CAT_LABELS = {
  news: 'News', competitors: 'Competitors', crops: 'Crops',
  patents: 'Patents', regulations: 'Regulations', genetics: 'Genetics', social: 'Social',
}

function highlight(text, query) {
  if (!text || !query) return text
  const idx = text.toLowerCase().indexOf(query.toLowerCase())
  if (idx === -1) return text.slice(0, 120)
  const start = Math.max(0, idx - 40)
  const end = Math.min(text.length, idx + query.length + 80)
  return (start > 0 ? '…' : '') + text.slice(start, end) + (end < text.length ? '…' : '')
}

export default function SearchOverlay({ onClose }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [activeIdx, setActiveIdx] = useState(0)
  const inputRef = useRef(null)
  const debounceRef = useRef(null)

  useEffect(() => { inputRef.current?.focus() }, [])

  const search = useCallback(async (q) => {
    if (!q.trim() || q.trim().length < 2) { setResults([]); return }
    setLoading(true)
    const term = `%${q.trim()}%`
    const { data } = await supabase
      .from('interpreted_items')
      .select('id, title_en, summary_en, category_slug, tags, relevance_score, scraped_items (url, published_at, language, title)')
      .or(`title_en.ilike.${term},summary_en.ilike.${term}`)
      .order('relevance_score', { ascending: false })
      .limit(12)
    setResults(data || [])
    setActiveIdx(0)
    setLoading(false)
  }, [])

  useEffect(() => {
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => search(query), 280)
    return () => clearTimeout(debounceRef.current)
  }, [query, search])

  const handleKey = (e) => {
    if (e.key === 'Escape') { onClose(); return }
    if (e.key === 'ArrowDown') { e.preventDefault(); setActiveIdx(i => Math.min(i + 1, results.length - 1)) }
    if (e.key === 'ArrowUp') { e.preventDefault(); setActiveIdx(i => Math.max(i - 1, 0)) }
    if (e.key === 'Enter' && results[activeIdx]?.scraped_items?.url) {
      window.open(results[activeIdx].scraped_items.url, '_blank')
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-16 px-4"
      style={{ background: 'rgba(26,22,20,0.6)', backdropFilter: 'blur(2px)' }}
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl bg-paper border border-rule overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* Input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-rule">
          <span className="text-ink-mute text-sm">🔍</span>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Search articles, summaries, tags…"
            className="flex-1 bg-transparent text-sm text-ink placeholder-ink-mute outline-none font-body"
          />
          {loading && (
            <span className="font-mono text-[9px] tracking-[0.14em] uppercase text-ink-mute animate-pulse">
              Searching…
            </span>
          )}
          <kbd className="font-mono text-[9px] border border-rule px-1.5 py-0.5 text-ink-mute">Esc</kbd>
        </div>

        {/* Results */}
        {results.length > 0 ? (
          <ul className="max-h-96 overflow-y-auto divide-y divide-rule">
            {results.map((item, idx) => {
              const si = item.scraped_items
              const score = item.relevance_score
              const scoreColor = score >= 7 ? 'text-leaf' : score >= 4 ? 'text-amber' : 'text-ink-mute'
              const snippet = highlight(item.summary_en || si?.title || '', query)
              const date = si?.published_at
                ? new Date(si.published_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
                : ''
              const isActive = idx === activeIdx

              return (
                <li key={item.id}>
                  <a
                    href={si?.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`flex items-start gap-3 px-4 py-3 transition cursor-pointer ${isActive ? 'bg-paper-deep' : 'hover:bg-paper-deep'}`}
                    onMouseEnter={() => setActiveIdx(idx)}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                        <span className="font-mono text-[9px] tracking-[0.12em] uppercase border border-rule px-1.5 py-0.5 text-ink-mute bg-paper-deep">
                          {CAT_LABELS[item.category_slug] || item.category_slug}
                        </span>
                        {date && <span className="font-mono text-[10px] text-ink-mute">{date}</span>}
                        {score > 0 && <span className={`font-mono text-[10px] ${scoreColor}`}>{score}/10</span>}
                        {si?.language && si.language !== 'en' && (
                          <span className="font-mono text-[9px] tracking-[0.1em] uppercase border border-rule px-1 text-ink-mute">
                            {si.language.toUpperCase()} → EN
                          </span>
                        )}
                      </div>
                      <p className="font-display text-[14px] text-ink line-clamp-1">
                        {item.title_en || si?.title}
                      </p>
                      {snippet && (
                        <p className="text-xs text-ink-mute mt-0.5 line-clamp-2 leading-relaxed">{snippet}</p>
                      )}
                    </div>
                    <span className="shrink-0 font-mono text-[10px] text-ink-mute mt-1">↗</span>
                  </a>
                </li>
              )
            })}
          </ul>
        ) : query.length >= 2 && !loading ? (
          <div className="px-4 py-10 text-center">
            <p className="font-display italic text-ink-mute">No results for "{query}"</p>
          </div>
        ) : query.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <p className="font-mono text-[9px] tracking-[0.14em] uppercase text-ink-mute">
              Type to search across all indexed articles
            </p>
          </div>
        ) : null}

        {/* Footer */}
        <div className="px-4 py-2 border-t border-rule flex items-center gap-4">
          {[['↑↓', 'navigate'], ['↵', 'open'], ['Esc', 'close']].map(([k, label]) => (
            <span key={k} className="font-mono text-[9px] tracking-[0.1em] uppercase text-ink-mute flex items-center gap-1">
              <kbd className="border border-rule px-1">{k}</kbd> {label}
            </span>
          ))}
          {results.length > 0 && (
            <span className="ml-auto font-mono text-[9px] text-ink-mute">{results.length} results</span>
          )}
        </div>
      </div>
    </div>
  )
}
