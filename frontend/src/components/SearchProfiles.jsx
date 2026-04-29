import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'

const FREQ_OPTIONS = ['daily', 'weekly', 'monthly']
const LANG_OPTIONS = ['en', 'zh', 'ja', 'hi', 'es', 'ar', 'tr', 'nl', 'da', 'de', 'fr']

function ProfileCard({ profile, selected, onSelect, onEdit, onDelete }) {
  return (
    <div
      onClick={() => onSelect(profile)}
      className={`border rounded-xl p-4 cursor-pointer transition ${
        selected?.id === profile.id
          ? 'border-green-400 bg-green-50'
          : 'border-gray-200 bg-white hover:border-gray-300'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="font-medium text-gray-900 text-sm truncate">
            {profile.name || profile.search_terms.join(', ')}
          </p>
          <p className="text-xs text-gray-500 mt-0.5">
            {profile.search_terms.join(' · ')}
          </p>
          {profile.intelligence_brief && (
            <p className="text-xs text-blue-600 mt-1">AI brief active</p>
          )}
          <div className="flex gap-2 mt-2 flex-wrap">
            {(profile.languages || ['en']).map(l => (
              <span key={l} className="text-xs bg-gray-100 text-gray-600 rounded px-1.5 py-0.5">{l.toUpperCase()}</span>
            ))}
            <span className="text-xs bg-gray-100 text-gray-600 rounded px-1.5 py-0.5">{profile.frequency || 'weekly'}</span>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          {profile.new_since_last_visit > 0 && (
            <span className="bg-green-500 text-white text-xs rounded-full px-2 py-0.5">
              {profile.new_since_last_visit} new
            </span>
          )}
          <div className="flex gap-1 mt-1">
            <button onClick={e => { e.stopPropagation(); onEdit(profile) }} className="text-xs text-gray-400 hover:text-gray-600 px-1">Edit</button>
            <button onClick={e => { e.stopPropagation(); onDelete(profile.id) }} className="text-xs text-red-400 hover:text-red-600 px-1">Delete</button>
          </div>
        </div>
      </div>
    </div>
  )
}

function ProfileForm({ categoryId, profile, onSave, onCancel }) {
  const [name, setName] = useState(profile?.name || '')
  const [terms, setTerms] = useState(profile?.search_terms?.join(', ') || '')
  const [langs, setLangs] = useState(profile?.languages || ['en'])
  const [freq, setFreq] = useState(profile?.frequency || 'weekly')
  const [brief, setBrief] = useState(profile?.intelligence_brief || '')
  const [saving, setSaving] = useState(false)

  const toggleLang = (l) => setLangs(prev => prev.includes(l) ? prev.filter(x => x !== l) : [...prev, l])

  const handleSave = async () => {
    const searchTerms = terms.split(',').map(t => t.trim()).filter(Boolean)
    if (!searchTerms.length) return
    setSaving(true)
    const { data: { session } } = await supabase.auth.getSession()
    const row = {
      user_id: session?.user?.id ?? null,
      category_id: categoryId,
      name: name || searchTerms.join(', '),
      search_terms: searchTerms,
      languages: langs,
      frequency: freq,
      intelligence_brief: brief || null,
    }
    let error
    if (profile?.id) {
      ;({ error } = await supabase.from('search_profiles').update(row).eq('id', profile.id))
    } else {
      ;({ error } = await supabase.from('search_profiles').insert(row))
    }
    setSaving(false)
    if (!error) onSave()
  }

  return (
    <div className="border border-green-200 bg-green-50 rounded-xl p-4 space-y-3">
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Profile name</label>
        <input value={name} onChange={e => setName(e.target.value)} placeholder="e.g. ToBRFV Resistance"
          className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500" />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Search terms (comma-separated)</label>
        <input value={terms} onChange={e => setTerms(e.target.value)} placeholder="tomato, ToBRFV, disease resistance"
          className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500" />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Languages</label>
        <div className="flex flex-wrap gap-1.5">
          {LANG_OPTIONS.map(l => (
            <button key={l} onClick={() => toggleLang(l)}
              className={`px-2 py-1 text-xs rounded-md border ${langs.includes(l) ? 'bg-green-600 text-white border-green-600' : 'bg-white text-gray-600 border-gray-300'}`}>
              {l.toUpperCase()}
            </button>
          ))}
        </div>
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Frequency</label>
        <div className="flex gap-2">
          {FREQ_OPTIONS.map(f => (
            <button key={f} onClick={() => setFreq(f)}
              className={`px-3 py-1 text-xs rounded-md border ${freq === f ? 'bg-green-600 text-white border-green-600' : 'bg-white text-gray-600 border-gray-300'}`}>
              {f}
            </button>
          ))}
        </div>
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">
          Intelligence Brief
          <span className="ml-1 font-normal text-gray-400">(optional â€” AI uses this to filter relevance)</span>
        </label>
        <textarea
          value={brief} onChange={e => setBrief(e.target.value)} rows={5}
          placeholder="Describe what is relevant to you. Example: We are a tomato seed breeder focused on ToBRFV and TYLCV resistance. We compete with Rijk Zwaan and Enza Zaden. Key markets: Netherlands, Spain, Mexico. We care about new variety launches, resistance breakthroughs, and regulatory approvals."
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 leading-relaxed resize-y"
        />
        <p className="text-xs text-gray-400 mt-1">Claude scores each matched article against this brief and surfaces the most relevant ones.</p>
      </div>
      <div className="flex gap-2 pt-1">
        <button onClick={handleSave} disabled={saving}
          className="px-4 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg disabled:opacity-50">
          {saving ? 'Saving...' : 'Save Profile'}
        </button>
        <button onClick={onCancel} className="px-4 py-1.5 border border-gray-300 text-gray-600 text-sm rounded-lg hover:bg-gray-50">Cancel</button>
      </div>
    </div>
  )
}

export default function SearchProfiles({ category, selectedProfile, onProfileSelect }) {
  const [profiles, setProfiles] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [editingProfile, setEditingProfile] = useState(null)

  useEffect(() => { if (category) loadProfiles(true) }, [category])

  const loadProfiles = async (autoSelect = false) => {
    const { data } = await supabase.from('search_profiles').select('*').eq('category_id', category.id).order('created_at', { ascending: false })
    setProfiles(data || [])
    if (autoSelect && data?.length > 0) {
      onProfileSelect(data[0])
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this profile?')) return
    await supabase.from('search_profiles').delete().eq('id', id)
    loadProfiles()
    if (selectedProfile?.id === id) onProfileSelect(null)
  }

  const handleSaved = () => { setShowForm(false); setEditingProfile(null); loadProfiles() }

  if (!category) return null

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-700">Your Search Profiles</h2>
        {!showForm && (
          <button onClick={() => { setEditingProfile(null); setShowForm(true) }} className="text-xs text-green-600 hover:text-green-700 font-medium">
            + Add Profile
          </button>
        )}
      </div>
      {showForm && (
        <ProfileForm categoryId={category.id} profile={editingProfile} onSave={handleSaved}
          onCancel={() => { setShowForm(false); setEditingProfile(null) }} />
      )}
      {profiles.length === 0 && !showForm && (
        <p className="text-sm text-gray-400 italic">No profiles yet. Create one to start tracking.</p>
      )}
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {profiles.map(p => (
          <ProfileCard key={p.id} profile={p} selected={selectedProfile} onSelect={onProfileSelect}
            onEdit={prof => { setEditingProfile(prof); setShowForm(true) }} onDelete={handleDelete} />
        ))}
      </div>
    </div>
  )
}
