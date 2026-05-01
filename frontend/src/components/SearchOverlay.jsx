import { useState, useEffect, useCallback, useRef } from 'react'
import { supabase } from '../lib/supabase'

const CATEGORY_COLORS = {
  news: 'bg-blue-100 text-blue-700',
  competitors: 'bg-purple-100 text-purple-700',
  crop_recommendations: 'bg-green-100 text-green-700',
  patents: 'bg-indigo-100 text-indigo-700',
  regulations: 'bg-pink-100 text-pink-700',
  genetics: 'bg-teal-100 text-teal-700',
  social: 'bg-orange-100 text-orange-700',
}

function highlight(text, query) {
  if (!text || !query) return text
  const idx = text.toLowerCase().indexOf(query.toLowerCase())
  if (idx === -1) return text.slice(0, 120)
  const start = Math.max(0, idx - 40)
  const end = Math.min(text.length, idx + query.length + 80)
  const snippet = (start > 0 ? '…' : '') + text.slice(start, end) + (end < text.length ? '…' : '')
  return snippet
}

export default function SearchOverlay({ onClose }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [activeIdx, setActiveIdx] = useState(0)
  const inputRef = useRef(null)
  const debounceRef = useRef(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const search = useCallback(async (q) => {
    if (!q.trim() || q.trim().length < 2) { setResults([]); return }
    setLoading(true)
    const term = `%${q.trim()}%`
    const { data } = await supabase
      .from('interpreted_items')
      .select(`
        id, title_en, summary_en, category_slug, tags, relevance_score,
        scraped_items (url, published_at, language, title)
      `)
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
      className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4"
      style={{ background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(2px)' }}
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl bg-white rounded-2xl shadow-2xl overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-gray-100">
          <span className="text-gray-400 text-lg">🔍</span>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Search articles, summaries, tags…"
            className="flex-1 text-sm text-gray-900 placeholder-gray-400 outline-none"
          />
          {loading && <span className="text-xs text-gray-400 animate-pulse">Searching…</span>}
          <kbd className="text-xs bg-gray-100 text-gray-400 rounded px-1.5 py-0.5">Esc</kbd>
        </div>

        {/* Results */}
        {results.length > 0 ? (
          <ul className="max-h-96 overflow-y-auto divide-y divide-gray-50">
            {results.map((item, idx) => {
              const si = item.scraped_items
              const catCls = CATEGORY_COLORS[item.category_slug] || 'bg-gray-100 text-gray-500'
              const score = item.relevance_score
              const scoreColor = score >= 7 ? 'text-green-600' : score >= 4 ? 'text-yellow-600' : 'text-gray-400'
              const snippet = highlight(item.summary_en || si?.title || '', query)
              const date = si?.published_at
                ? new Date(si.published_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
                : ''

              return (
                <li key={item.id}>
                  <a
                    href={si?.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`flex items-start gap-3 px-4 py-3 hover:bg-gray-50 transition cursor-pointer ${idx === activeIdx ? 'bg-gray-50' : ''}`}
                    onMouseEnter={() => setActiveIdx(idx)}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                        <span className={`text-xs rounded px-1.5 py-0.5 font-medium ${catCls}`}>
                          {item.category_slug?.replace('_', ' ')}
                        </span>
                        {date && <span className="text-xs text-gray-400">{date}</span>}
                        {score > 0 && <span className={`text-xs font-medium ${scoreColor}`}>{score}/10</span>}
                      </div>
                      <p className="text-sm font-medium text-gray-900 line-clamp-1">
                        {item.title_en || si?.title}
                      </p>
                      {snippet && (
                        <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{snippet}</p>
                      )}
                    </div>
                    <span className="shrink-0 text-gray-300 text-xs mt-1">↗</span>
                  </a>
                </li>
              )
            })}
          </ul>
        ) : query.length >= 2 && !loading ? (
          <div className="px-4 py-8 text-center text-sm text-gray-400">
            No results for "{query}"
          </div>
        ) : query.length === 0 ? (
          <div className="px-4 py-6 text-center text-xs text-gray-400">
            Type to search across all interpreted articles
          </div>
        ) : null}

        {/* Footer */}
        <div className="px-4 py-2 border-t border-gray-100 flex items-center gap-4 text-xs text-gray-400">
          <span><kbd className="bg-gray-100 rounded px-1">↑↓</kbd> navigate</span>
          <span><kbd className="bg-gray-100 rounded px-1">↵</kbd> open</span>
          <span><kbd className="bg-gray-100 rounded px-1">Esc</kbd> close</span>
          {results.length > 0 && <span className="ml-auto">{results.length} results</span>}
        </div>
      </div>
    </div>
  )
}
