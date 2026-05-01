import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'

const CAT_ICON = {
  news: '📰', competitors: '🏢', crop_recommendations: '🌱',
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
    <div className="bg-white border-b border-gray-200 px-4 py-2 flex items-center gap-3 shrink-0 overflow-x-auto">
      <span className="text-xs font-semibold text-gray-500 shrink-0 flex items-center gap-1">
        📈 Trending
      </span>
      <div className="flex items-center gap-1.5 overflow-x-auto">
        {trends.map(t => {
          const icon = CAT_ICON[t.category_slug] || '📌'
          return (
            <button
              key={t.id}
              onClick={() => onTopicClick?.(t.topic)}
              className="shrink-0 flex items-center gap-1 bg-gray-100 hover:bg-green-100 hover:text-green-800 text-gray-700 rounded-full px-2.5 py-1 text-xs font-medium transition whitespace-nowrap"
              title={`${t.source_count} sources in last 48h`}
            >
              {icon} {t.topic}
              <span className="text-gray-400 font-normal ml-0.5">×{t.source_count}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
