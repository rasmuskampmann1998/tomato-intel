import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'

const CAT_ICON = {
  news: '📰', competitors: '🏢', crops: '🌱',
  patents: '📋', regulations: '⚖️', genetics: '🧬', social: '💬',
}

export default function TrendingBanner({ onTopicClick }) {
  const [trends, setTrends] = useState([])

  useEffect(() => {
    const since = new Date(Date.now() - 48 * 3600000).toISOString()
    supabase
      .from('trend_alerts')
      .select('id, topic, source_count, category_slug, last_seen')
      .eq('active', true)
      .gte('last_seen', since)
      .order('source_count', { ascending: false })
      .limit(8)
      .then(({ data }) => setTrends(data || []))
  }, [])

  if (!trends.length) return null

  return (
    <div className="bg-paper-deep border-b border-rule px-4 py-1.5 flex items-center gap-3 shrink-0 overflow-x-auto">
      <span className="font-mono text-[9px] tracking-[0.2em] uppercase text-ink-mute shrink-0">
        Trending
      </span>
      <div className="flex items-center gap-1 overflow-x-auto">
        {trends.map(t => {
          const icon = CAT_ICON[t.category_slug] || '📌'
          return (
            <button
              key={t.id}
              onClick={() => onTopicClick?.(t.topic)}
              className="shrink-0 flex items-center gap-1 border border-rule bg-paper hover:bg-tomato-soft hover:border-tomato hover:text-tomato text-ink-soft px-2 py-0.5 transition whitespace-nowrap"
              title={`${t.source_count} sources in last 48h`}
            >
              <span className="text-xs">{icon}</span>
              <span className="font-mono text-[10px]">{t.topic}</span>
              <span className="font-mono text-[9px] text-ink-mute ml-0.5">×{t.source_count}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
