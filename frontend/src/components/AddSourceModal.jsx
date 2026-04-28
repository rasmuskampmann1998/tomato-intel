import { useState } from 'react'
import { supabase } from '../lib/supabase'
import { fetchEventSource } from '@microsoft/fetch-event-source'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8004'

const STEP_ICONS = {
  running: '⟳',
  success: '✓',
  failed: '✗',
  pending: '○',
}
const STEP_COLORS = {
  running: 'text-blue-500',
  success: 'text-green-500',
  failed: 'text-red-400',
  pending: 'text-gray-300',
}

function StepRow({ step, strategy, status, message, itemsFound }) {
  const icon = STEP_ICONS[status] || STEP_ICONS.pending
  const color = STEP_COLORS[status] || STEP_COLORS.pending
  return (
    <div className="flex items-start gap-3 py-1.5">
      <span className={`text-base font-bold shrink-0 w-5 text-center ${color} ${status === 'running' ? 'animate-spin' : ''}`}>
        {icon}
      </span>
      <div className="flex-1 min-w-0">
        <span className="text-sm font-medium text-gray-700">{strategy}</span>
        {message && (
          <p className={`text-xs mt-0.5 ${status === 'failed' ? 'text-red-400' : status === 'success' ? 'text-green-600' : 'text-gray-400'}`}>
            {message}
          </p>
        )}
      </div>
      {status === 'success' && itemsFound > 0 && (
        <span className="text-xs text-green-600 font-medium shrink-0">{itemsFound} articles</span>
      )}
    </div>
  )
}

export default function AddSourceModal({ category, onClose, onAdded }) {
  const [phase, setPhase] = useState('input')   // 'input' | 'analyzing' | 'confirm' | 'done' | 'failed'
  const [url, setUrl] = useState('')
  const [sourceName, setSourceName] = useState('')
  const [steps, setSteps] = useState([])
  const [winningConfig, setWinningConfig] = useState(null)
  const [itemsFound, setItemsFound] = useState(0)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const startAnalysis = async () => {
    if (!url.trim()) return
    setPhase('analyzing')
    setSteps([])
    setError('')

    const { data: { session } } = await supabase.auth.getSession()
    const token = session?.access_token
    if (!token) { setError('Not authenticated'); setPhase('input'); return }

    // Derive source name from URL hostname as default
    try {
      setSourceName(new URL(url).hostname.replace(/^www\./, ''))
    } catch {}

    const endpoint = `${API_BASE}/sources/analyze?url=${encodeURIComponent(url)}&category_slug=${category.slug}`

    await fetchEventSource(endpoint, {
      headers: { Authorization: `Bearer ${token}` },
      onopen(response) {
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
      },
      onmessage(event) {
        const status = JSON.parse(event.data)

        if (status.strategy === 'complete') {
          if (status.status === 'success') {
            setWinningConfig(status.config)
            setItemsFound(status.items_found)
            setPhase('confirm')
          } else {
            setPhase('failed')
          }
          return
        }

        setSteps(prev => {
          // Replace running step with same strategy, otherwise append
          const idx = prev.findIndex(s => s.strategy === status.strategy && s.status === 'running')
          if (idx >= 0) {
            const next = [...prev]
            next[idx] = status
            return next
          }
          return [...prev, status]
        })
      },
      onerror(err) {
        setError(`Connection error: ${err.message || 'unknown'}`)
        setPhase('failed')
        throw err  // stops retry loop
      },
    })
  }

  const handleSubmit = async () => {
    if (!winningConfig || !sourceName.trim()) return
    setSaving(true)
    const { data: { session } } = await supabase.auth.getSession()
    const token = session?.access_token

    try {
      const res = await fetch(`${API_BASE}/sources/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          url,
          name: sourceName,
          category_id: category.id,
          scrape_type: winningConfig.scrape_type,
          rss_url: winningConfig.rss_url || null,
          css_selector: winningConfig.css_selector || null,
          language: winningConfig.language || 'en',
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Submit failed')
      setPhase('done')
      onAdded(data.source_id)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-gray-900">Add a source</h2>
            <p className="text-xs text-gray-400 mt-0.5">{category.name}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-lg">✕</button>
        </div>

        <div className="px-6 py-5">
          {/* Phase: input */}
          {phase === 'input' && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Page URL</label>
                <input
                  type="url" value={url} onChange={e => setUrl(e.target.value)}
                  placeholder="https://example.com/news"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                  onKeyDown={e => e.key === 'Enter' && startAnalysis()}
                />
                <p className="text-xs text-gray-400 mt-1">
                  Paste the homepage or article listing page. The AI will figure out how to scrape it.
                </p>
              </div>
              {error && <p className="text-xs text-red-500">{error}</p>}
              <button
                onClick={startAnalysis}
                disabled={!url.trim()}
                className="w-full bg-green-600 hover:bg-green-700 text-white text-sm font-medium py-2 rounded-lg disabled:opacity-40 transition"
              >
                Analyse →
              </button>
            </div>
          )}

          {/* Phase: analyzing */}
          {phase === 'analyzing' && (
            <div className="space-y-1">
              <p className="text-xs text-gray-400 mb-3">Agent is trying strategies one by one...</p>
              {steps.map((s, i) => (
                <StepRow key={i} {...s} />
              ))}
              {steps.length === 0 && (
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <span className="animate-spin">⟳</span> Fetching page...
                </div>
              )}
            </div>
          )}

          {/* Phase: confirm */}
          {phase === 'confirm' && (
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                <p className="text-sm font-medium text-green-700">
                  Found {itemsFound} articles
                </p>
                <div className="mt-1 text-xs text-green-600 space-y-0.5">
                  <div>Strategy: <strong>{winningConfig.scrape_type}</strong></div>
                  {winningConfig.rss_url && <div>RSS: {winningConfig.rss_url}</div>}
                  {winningConfig.css_selector && <div>Selector: <code>{winningConfig.css_selector}</code></div>}
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Source name</label>
                <input
                  type="text" value={sourceName} onChange={e => setSourceName(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              {error && <p className="text-xs text-red-500">{error}</p>}
              <div className="flex gap-2">
                <button onClick={onClose}
                  className="flex-1 border border-gray-300 text-gray-600 text-sm py-2 rounded-lg hover:bg-gray-50">
                  Cancel
                </button>
                <button onClick={handleSubmit} disabled={saving || !sourceName.trim()}
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white text-sm font-medium py-2 rounded-lg disabled:opacity-50 transition">
                  {saving ? 'Adding...' : 'Add to my feed'}
                </button>
              </div>
            </div>
          )}

          {/* Phase: done */}
          {phase === 'done' && (
            <div className="text-center py-4">
              <div className="text-green-500 text-4xl mb-3">✓</div>
              <p className="text-sm font-medium text-gray-900">Source added!</p>
              <p className="text-xs text-gray-400 mt-1">
                Articles from <strong>{sourceName}</strong> will appear in your feed after the next scrape run.
              </p>
              <button onClick={onClose}
                className="mt-4 text-sm text-green-600 hover:underline">
                Close
              </button>
            </div>
          )}

          {/* Phase: failed */}
          {phase === 'failed' && (
            <div className="space-y-3">
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-sm font-medium text-red-700">Could not find a working scraper</p>
                <p className="text-xs text-red-500 mt-1">
                  This site may be behind a hard paywall or aggressive bot-blocking.
                  Try a different page from the same site (e.g. an RSS feed URL directly).
                </p>
              </div>
              {steps.length > 0 && (
                <div className="space-y-1">
                  {steps.map((s, i) => <StepRow key={i} {...s} />)}
                </div>
              )}
              <div className="flex gap-2">
                <button onClick={() => { setPhase('input'); setUrl(''); setSteps([]) }}
                  className="flex-1 border border-gray-300 text-gray-600 text-sm py-2 rounded-lg hover:bg-gray-50">
                  Try again
                </button>
                <button onClick={onClose}
                  className="flex-1 bg-gray-100 text-gray-600 text-sm py-2 rounded-lg hover:bg-gray-200">
                  Close
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
