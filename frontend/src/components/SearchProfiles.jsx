import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8004'

const FREQ_OPTIONS = ['daily', 'weekly', 'monthly']

const LANG_OPTIONS = [
  { code: 'en', flag: '🇬🇧', name: 'English' },
  { code: 'nl', flag: '🇳🇱', name: 'Dutch' },
  { code: 'de', flag: '🇩🇪', name: 'German' },
  { code: 'fr', flag: '🇫🇷', name: 'French' },
  { code: 'es', flag: '🇪🇸', name: 'Spanish' },
  { code: 'da', flag: '🇩🇰', name: 'Danish' },
  { code: 'sv', flag: '🇸🇪', name: 'Swedish' },
  { code: 'zh', flag: '🇨🇳', name: 'Chinese' },
  { code: 'ja', flag: '🇯🇵', name: 'Japanese' },
  { code: 'ar', flag: '🇸🇦', name: 'Arabic' },
  { code: 'hi', flag: '🇮🇳', name: 'Hindi' },
  { code: 'tr', flag: '🇹🇷', name: 'Turkish' },
  { code: 'pt', flag: '🇧🇷', name: 'Portuguese' },
  { code: 'ko', flag: '🇰🇷', name: 'Korean' },
  { code: 'ru', flag: '🇷🇺', name: 'Russian' },
]

function ProfileCard({ profile, selected, onSelect, onEdit, onDelete }) {
  const langLabels = (profile.languages || ['en']).map(code => {
    const l = LANG_OPTIONS.find(o => o.code === code)
    return l ? `${l.flag} ${l.name}` : code.toUpperCase()
  })

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
          <div className="flex flex-wrap gap-1 mt-1.5">
            {profile.search_terms.map(t => (
              <span key={t} className="text-xs bg-green-100 text-green-800 rounded-full px-2 py-0.5">{t}</span>
            ))}
          </div>
          {profile.intelligence_brief && (
            <p className="text-xs text-blue-600 mt-1.5">AI brief active</p>
          )}
          <div className="flex gap-1.5 mt-2 flex-wrap">
            {langLabels.map(l => (
              <span key={l} className="text-xs bg-gray-100 text-gray-600 rounded px-1.5 py-0.5">{l}</span>
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

function ProfileForm({ categoryId, categorySlug, profile, onSave, onCancel }) {
  const [name, setName] = useState(profile?.name || '')
  const [termTags, setTermTags] = useState(profile?.search_terms || [])
  const [tagInput, setTagInput] = useState('')
  const [langs, setLangs] = useState(profile?.languages || ['en'])
  const [freq, setFreq] = useState(profile?.frequency || 'weekly')
  const [brief, setBrief] = useState(profile?.intelligence_brief || '')
  const [saving, setSaving] = useState(false)
  const [suggesting, setSuggesting] = useState(false)
  const [aiSuggestions, setAiSuggestions] = useState([])
  const [suggestError, setSuggestError] = useState('')

  const addTag = (raw) => {
    const t = raw.trim().replace(/,+$/, '')
    if (t && !termTags.includes(t)) setTermTags(prev => [...prev, t])
  }

  const handleTagKeyDown = (e) => {
    if ((e.key === 'Enter' || e.key === ',') && tagInput.trim()) {
      e.preventDefault()
      addTag(tagInput)
      setTagInput('')
    } else if (e.key === 'Backspace' && !tagInput && termTags.length > 0) {
      setTermTags(prev => prev.slice(0, -1))
    }
  }

  const toggleLang = (code) =>
    setLangs(prev => prev.includes(code) ? prev.filter(x => x !== code) : [...prev, code])

  const handleSuggest = async () => {
    if (termTags.length === 0) return
    setSuggesting(true)
    setAiSuggestions([])
    setSuggestError('')
    try {
      const res = await fetch(`${API_BASE}/search/suggest-keywords`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ terms: termTags, brief, category_slug: categorySlug || '' }),
      })
      const data = await res.json()
      setAiSuggestions((data.suggestions || []).filter(s => !termTags.includes(s)))
    } catch {
      setSuggestError('Could not reach suggestion service')
    } finally {
      setSuggesting(false)
    }
  }

  const handleSave = async () => {
    if (!termTags.length) return
    setSaving(true)
    const { data: { session } } = await supabase.auth.getSession()
    const row = {
      user_id: session?.user?.id ?? null,
      category_id: categoryId,
      name: name || termTags.join(', '),
      search_terms: termTags,
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
    <div className="border border-green-200 bg-green-50 rounded-xl p-4 space-y-4">
      {/* Profile name */}
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Profile name</label>
        <input value={name} onChange={e => setName(e.target.value)} placeholder="e.g. ToBRFV Resistance"
          className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500" />
      </div>

      {/* Keyword tag input */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="text-xs font-medium text-gray-600">Keywords</label>
          <button
            onClick={handleSuggest}
            disabled={suggesting || termTags.length === 0}
            className="text-xs text-purple-600 hover:text-purple-800 border border-purple-200 bg-white rounded-lg px-2.5 py-1 disabled:opacity-40 transition"
          >
            {suggesting ? '⟳ Suggesting…' : '✨ AI Suggest'}
          </button>
        </div>

        {/* Tag pills + text input in one box */}
        <div
          className="flex flex-wrap gap-1.5 w-full border border-gray-300 bg-white rounded-lg px-3 py-2 focus-within:ring-2 focus-within:ring-green-500 cursor-text"
          onClick={() => document.getElementById('tag-input')?.focus()}
        >
          {termTags.map(t => (
            <span key={t} className="flex items-center gap-0.5 bg-green-100 text-green-800 text-xs rounded-full px-2.5 py-1 shrink-0">
              {t}
              <button
                onClick={e => { e.stopPropagation(); setTermTags(prev => prev.filter(x => x !== t)) }}
                className="text-green-600 hover:text-green-900 ml-0.5 leading-none"
              >×</button>
            </span>
          ))}
          <input
            id="tag-input"
            value={tagInput}
            onChange={e => setTagInput(e.target.value)}
            onKeyDown={handleTagKeyDown}
            onBlur={() => { if (tagInput.trim()) { addTag(tagInput); setTagInput('') } }}
            placeholder={termTags.length === 0 ? 'Type a term and press Enter…' : ''}
            className="flex-1 min-w-[120px] outline-none text-sm bg-transparent py-0.5"
          />
        </div>
        <p className="text-xs text-gray-400 mt-1">Press Enter or comma to add · Backspace removes last tag</p>

        {/* AI suggestion chips */}
        {aiSuggestions.length > 0 && (
          <div className="mt-2">
            <p className="text-xs text-gray-400 mb-1.5">Click to add:</p>
            <div className="flex flex-wrap gap-1.5">
              {aiSuggestions.map(s => (
                <button
                  key={s}
                  onClick={() => {
                    setTermTags(p => p.includes(s) ? p : [...p, s])
                    setAiSuggestions(p => p.filter(x => x !== s))
                  }}
                  className="text-xs bg-purple-50 text-purple-700 border border-purple-200 rounded-full px-2.5 py-0.5 hover:bg-purple-100 transition"
                >
                  + {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {suggestError && <p className="text-xs text-red-500 mt-1">{suggestError}</p>}
      </div>

      {/* Language picker */}
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1.5">Languages</label>
        <div className="flex flex-wrap gap-1.5">
          {LANG_OPTIONS.map(l => (
            <button
              key={l.code}
              onClick={() => toggleLang(l.code)}
              className={`flex items-center gap-1 px-2.5 py-1 text-xs rounded-full border transition ${
                langs.includes(l.code)
                  ? 'bg-green-600 text-white border-green-600'
                  : 'bg-white text-gray-600 border-gray-300 hover:border-gray-400'
              }`}
            >
              <span>{l.flag}</span>
              <span>{l.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Frequency */}
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

      {/* Intelligence brief */}
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">
          Intelligence Brief
          <span className="ml-1 font-normal text-gray-400">(optional — AI uses this to filter relevance)</span>
        </label>
        <textarea
          value={brief} onChange={e => setBrief(e.target.value)} rows={5}
          placeholder="Describe what is relevant to you. Example: We are a tomato seed breeder focused on ToBRFV and TYLCV resistance. We compete with Rijk Zwaan and Enza Zaden. Key markets: Netherlands, Spain, Mexico. We care about new variety launches, resistance breakthroughs, and regulatory approvals."
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 leading-relaxed resize-y"
        />
        <p className="text-xs text-gray-400 mt-1">Claude scores each matched article against this brief and surfaces the most relevant ones.</p>
      </div>

      <div className="flex gap-2 pt-1">
        <button onClick={handleSave} disabled={saving || termTags.length === 0}
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
        <ProfileForm
          categoryId={category.id}
          categorySlug={category.slug}
          profile={editingProfile}
          onSave={handleSaved}
          onCancel={() => { setShowForm(false); setEditingProfile(null) }}
        />
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
