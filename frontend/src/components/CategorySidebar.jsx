const ICONS = {
  news: '📰', competitors: '🏢', crops: '🌱', crop_recommendations: '🌱',
  patents: '📋', regulations: '⚖️', genetics: '🧬', social: '💬',
}

const ORDER = ['news', 'competitors', 'genetics', 'patents', 'regulations', 'crops', 'social']

export default function CategorySidebar({ categories, selected, onSelect, badgeCounts }) {
  const sorted = [...categories].sort((a, b) => {
    const ai = ORDER.indexOf(a.slug)
    const bi = ORDER.indexOf(b.slug)
    return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi)
  })

  return (
    <aside className="w-56 shrink-0 bg-paper-deep border-r border-rule flex flex-col h-full">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-rule">
        <p className="font-display text-[22px] leading-tight">
          <span className="text-tomato">Tomato</span>
          <span className="text-ink italic"> Intel</span>
        </p>
        <p className="font-mono text-[9px] tracking-[0.2em] uppercase text-ink-mute mt-0.5">
          Seed Intelligence
        </p>
      </div>

      {/* Section label */}
      <div className="px-5 pt-4 pb-1">
        <p className="font-mono text-[9px] tracking-[0.2em] uppercase text-ink-mute">Categories</p>
      </div>

      <nav className="flex-1 overflow-y-auto py-1">
        {sorted.map((cat, idx) => {
          const badge = badgeCounts?.[cat.id] || 0
          const isSelected = selected?.id === cat.id
          const num = String(idx + 1).padStart(2, '0')
          return (
            <button
              key={cat.id}
              onClick={() => onSelect(cat)}
              className={`w-full flex items-center justify-between px-5 py-2.5 transition text-left ${
                isSelected
                  ? 'bg-tomato text-paper'
                  : 'text-ink-soft hover:bg-paper'
              }`}
            >
              <span className="flex items-center gap-2.5 min-w-0">
                <span className={`font-mono text-[10px] shrink-0 ${isSelected ? 'text-paper/60' : 'text-ink-mute'}`}>
                  {num}
                </span>
                <span className="text-sm shrink-0">{ICONS[cat.slug] || '📁'}</span>
                <span className="font-display text-[13px] truncate">{cat.name}</span>
              </span>
              {badge > 0 && (
                <span className={`font-mono text-[10px] px-1.5 py-0.5 shrink-0 ml-1 ${
                  isSelected ? 'bg-paper text-tomato' : 'bg-tomato text-paper'
                }`}>
                  +{badge > 99 ? '99' : badge}
                </span>
              )}
            </button>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-3 border-t border-rule">
        <p className="font-mono text-[9px] tracking-[0.14em] uppercase text-ink-mute flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-leaf inline-block" />
          Scrapers active
        </p>
      </div>
    </aside>
  )
}
