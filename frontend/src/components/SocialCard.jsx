import { useState } from 'react'

const PLATFORM_CONFIG = {
  twitter:   { icon: '𝕏',  label: 'X',         color: 'text-gray-900',   bg: 'bg-gray-100' },
  reddit:    { icon: '🟠', label: 'Reddit',     color: 'text-orange-700', bg: 'bg-orange-50' },
  linkedin:  { icon: '💼', label: 'LinkedIn',   color: 'text-blue-700',   bg: 'bg-blue-50' },
  instagram: { icon: '📸', label: 'Instagram',  color: 'text-pink-700',   bg: 'bg-pink-50' },
  facebook:  { icon: '📘', label: 'Facebook',   color: 'text-blue-600',   bg: 'bg-blue-50' },
  tiktok:    { icon: '🎵', label: 'TikTok',     color: 'text-gray-900',   bg: 'bg-gray-100' },
}

const TYPE_BADGE = {
  competitor:  'bg-purple-100 text-purple-700',
  media:       'bg-blue-100 text-blue-700',
  researcher:  'bg-teal-100 text-teal-700',
  influencer:  'bg-yellow-100 text-yellow-700',
}

function timeAgo(iso) {
  if (!iso) return ''
  const diff = Date.now() - new Date(iso).getTime()
  const h = Math.floor(diff / 3600000)
  if (h < 1) return `${Math.floor(diff / 60000)}m ago`
  if (h < 24) return `${h}h ago`
  return `${Math.floor(h / 24)}d ago`
}

function fmt(n) {
  if (!n) return '0'
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
  return String(n)
}

export default function SocialCard({ item, accountType }) {
  const [expanded, setExpanded] = useState(false)
  const platform = PLATFORM_CONFIG[item.platform] || { icon: '💬', label: item.platform, color: 'text-gray-600', bg: 'bg-gray-50' }
  const text = item.content || item.title || ''
  const isLong = text.length > 240
  const displayText = isLong && !expanded ? text.slice(0, 240) + '…' : text

  return (
    <div className="bg-white rounded-xl border border-gray-200 hover:border-gray-300 transition p-4 space-y-3">
      {/* Header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className={`shrink-0 text-base w-7 h-7 flex items-center justify-center rounded-full ${platform.bg}`}>
            {platform.icon}
          </span>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-sm font-medium text-gray-900 truncate">
                {item.author ? `@${item.author}` : platform.label}
              </span>
              {accountType && (
                <span className={`text-xs rounded px-1.5 py-0.5 font-medium ${TYPE_BADGE[accountType] || 'bg-gray-100 text-gray-500'}`}>
                  {accountType}
                </span>
              )}
            </div>
            <span className="text-xs text-gray-400">{timeAgo(item.published_at)}</span>
          </div>
        </div>
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0 text-xs text-gray-400 hover:text-green-600 border border-gray-200 rounded px-2 py-1 whitespace-nowrap"
        >
          View →
        </a>
      </div>

      {/* Post text */}
      <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
        {displayText}
        {isLong && (
          <button
            onClick={() => setExpanded(e => !e)}
            className="ml-1 text-xs text-green-600 hover:underline"
          >
            {expanded ? 'less' : 'more'}
          </button>
        )}
      </p>

      {/* Engagement bar */}
      <div className="flex items-center gap-4 text-xs text-gray-400 border-t border-gray-100 pt-2">
        {item.like_count > 0 && <span>❤ {fmt(item.like_count)}</span>}
        {item.comment_count > 0 && <span>💬 {fmt(item.comment_count)}</span>}
        {item.share_count > 0 && <span>🔁 {fmt(item.share_count)}</span>}
        {item.view_count > 0 && <span>👁 {fmt(item.view_count)}</span>}
        {item.language && item.language !== 'en' && (
          <span className="ml-auto uppercase font-medium">{item.language}</span>
        )}
      </div>
    </div>
  )
}
