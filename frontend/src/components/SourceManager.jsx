import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'

const STATUS_STYLE = {
  ok: 'bg-green-100 text-green-700',
  empty: 'bg-yellow-100 text-yellow-700',
  failed: 'bg-red-100 text-red-700',
}

function SourceRow({ source, isAdmin, onToggle }) {
  const statusCls = STATUS_STYLE[source.scrape_status] || 'bg-gray-100 text-gray-500'
  const lastScraped = source.last_scraped_at
    ? new Date(source.last_scraped_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
    : 'never'

  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50">
      <td className="py-2.5 px-3 text-sm text-gray-800">{source.name}</td>
      <td className="py-2.5 px-3">
        <span className="text-xs bg-gray-100 text-gray-600 rounded px-1.5 py-0.5">
          {source.scrape_type}
        </span>
      </td>
      <td className="py-2.5 px-3">
        {source.scrape_status ? (
          <span className={`text-xs rounded px-1.5 py-0.5 ${statusCls}`}>
            {source.scrape_status}
          </span>
        ) : (
          <span className="text-xs text-gray-400">pending</span>
        )}
      </td>
      <td className="py-2.5 px-3 text-xs text-gray-400">{lastScraped}</td>
      {isAdmin && (
        <td className="py-2.5 px-3">
          <button
            onClick={() => onToggle(source)}
            className={`text-xs rounded px-2 py-1 ${
              source.active
                ? 'bg-red-50 text-red-600 hover:bg-red-100'
                : 'bg-green-50 text-green-600 hover:bg-green-100'
            }`}
          >
            {source.active ? 'Disable' : 'Enable'}
          </button>
        </td>
      )}
    </tr>
  )
}

export default function SourceManager({ category, isAdmin }) {
  const [sources, setSources] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (category) loadSources()
  }, [category])

  const loadSources = async () => {
    setLoading(true)
    const { data } = await supabase
      .from('sources')
      .select('*')
      .eq('category_id', category.id)
      .order('name')
    setSources(data || [])
    setLoading(false)
  }

  const handleToggle = async (source) => {
    await supabase
      .from('sources')
      .update({ active: !source.active })
      .eq('id', source.id)
    loadSources()
  }

  if (!category) return null

  const activeCount = sources.filter(s => s.active).length
  const failedCount = sources.filter(s => s.scrape_status === 'failed').length

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-gray-700">Sources</h2>
          <p className="text-xs text-gray-400 mt-0.5">
            {activeCount} active{failedCount > 0 && `, ${failedCount} failed`}
          </p>
        </div>
        {failedCount > 0 && (
          <span className="text-xs text-red-600 bg-red-50 rounded px-2 py-1">
            {failedCount} source{failedCount > 1 ? 's' : ''} need attention
          </span>
        )}
      </div>

      {loading ? (
        <p className="text-sm text-gray-400">Loading...</p>
      ) : sources.length === 0 ? (
        <p className="text-sm text-gray-400 italic">No sources configured for this category.</p>
      ) : (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="py-2 px-3 text-left text-xs font-medium text-gray-500">Source</th>
                <th className="py-2 px-3 text-left text-xs font-medium text-gray-500">Type</th>
                <th className="py-2 px-3 text-left text-xs font-medium text-gray-500">Status</th>
                <th className="py-2 px-3 text-left text-xs font-medium text-gray-500">Last Run</th>
                {isAdmin && (
                  <th className="py-2 px-3 text-left text-xs font-medium text-gray-500">Actions</th>
                )}
              </tr>
            </thead>
            <tbody>
              {sources.map(s => (
                <SourceRow key={s.id} source={s} isAdmin={isAdmin} onToggle={handleToggle} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
