const ICONS = {
  news: '📰',
  competitors: '🏢',
  crop_recommendations: '🌱',
  patents: '📋',
  regulations: '⚖️',
  genetics: '🧬',
  social: '💬',
}

export default function CategorySidebar({ categories, selected, onSelect, badgeCounts }) {
  return (
    <aside className="w-52 shrink-0 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-4 border-b border-gray-100">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Categories</p>
      </div>
      <nav className="flex-1 overflow-y-auto py-2">
        {categories.map(cat => {
          const badge = badgeCounts?.[cat.id] || 0
          const isSelected = selected?.id === cat.id
          return (
            <button
              key={cat.id}
              onClick={() => onSelect(cat)}
              className={`w-full flex items-center justify-between px-4 py-2.5 text-sm transition ${
                isSelected
                  ? 'bg-green-50 text-green-700 font-medium'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <span className="flex items-center gap-2">
                <span>{ICONS[cat.slug] || '📁'}</span>
                <span>{cat.name}</span>
              </span>
              {badge > 0 && (
                <span className="bg-green-500 text-white text-xs rounded-full px-1.5 py-0.5 min-w-[20px] text-center">
                  {badge > 99 ? '99+' : badge}
                </span>
              )}
            </button>
          )
        })}
      </nav>
    </aside>
  )
}
