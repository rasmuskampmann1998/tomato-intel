import { useState } from 'react'

const PLATFORM_CONFIG = {
  twitter:   { icon: '𝕏',  label: 'X' },
  reddit:    { icon: '🟠', label: 'Reddit' },
  linkedin:  { icon: '💼', label: 'LinkedIn' },
  instagram: { icon: '📸', label: 'Instagram' },
  facebook:  { icon: '📘', label: 'Facebook' },
  tiktok:    { icon: '🎵', label: 'TikTok' },
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
  const platform = PLATFORM_CONFIG[item.platform] || { icon: '💬', label: item.platform }
  const text = item.content || item.title || ''
  const isLong = text.length > 240
  const displayText = isLong && !expanded ? text.slice(0, 240) + '…' : text

  return (
    <div className="bg-paper border border-rule hover:bg-paper-deep transition p-4 space-y-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <span className="shrink-0 text-base w-7 h-7 flex items-center justify-center border border-rule bg-paper-deep">
            {platform.icon}
          </span>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-display text-[14px] text-ink truncate">
                {item.author ? `@${item.author}` : platform.label}
              </span>
              {accountType && (
                <span className="font-mono text-[9px] tracking-[0.1em] uppercase border border-rule px-1.5 py-0.5 text-ink-mute bg-paper-deep">
                  {accountType}
                </span>
              )}
            </div>
            <span className="font-mono text-[10px] text-ink-mute">{timeAgo(item.published_at)}</span>
          </div>
        </div>
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0 font-mono text-[9px] tracking-[0.12em] uppercase border border-rule px-2 py-1 text-ink-mute hover:text-tomato hover:border-tomato transition whitespace-nowrap"
        >
          View ↗
        </a>
      </div>

      {/* Content */}
      <p className="text-sm text-ink-soft leading-relaxed whitespace-pre-line">
        {displayText}
        {isLong && (
          <button
            onClick={() => setExpanded(e => !e)}
            className="ml-1 font-mono text-[9px] tracking-[0.1em] uppercase text-tomato hover:text-tomato-deep"
          >
            {expanded ? 'less' : 'more'}
          </button>
        )}
      </p>

      {/* Engagement */}
      <div className="flex items-center gap-4 border-t border-rule pt-2">
        {item.like_count > 0 && (
          <span className="font-mono text-[10px] text-ink-mute">❤ {fmt(item.like_count)}</span>
        )}
        {item.comment_count > 0 && (
          <span className="font-mono text-[10px] text-ink-mute">💬 {fmt(item.comment_count)}</span>
        )}
        {item.share_count > 0 && (
          <span className="font-mono text-[10px] text-ink-mute">↺ {fmt(item.share_count)}</span>
        )}
        {item.view_count > 0 && (
          <span className="font-mono text-[10px] text-ink-mute">👁 {fmt(item.view_count)}</span>
        )}
        {item.language && item.language !== 'en' && (
          <span className="ml-auto font-mono text-[9px] tracking-[0.1em] uppercase border border-rule px-1.5 py-0.5 text-ink-mute">
            {item.language.toUpperCase()} → EN
          </span>
        )}
      </div>
    </div>
  )
}
