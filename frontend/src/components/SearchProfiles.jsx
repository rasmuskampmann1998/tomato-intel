import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8004'

const FREQ_OPTIONS = ['daily', 'weekly', 'monthly']

const LANG_OPTIONS = [
  { code: 'en', flag: '🇬🇧', name: 'English' },
  { code: 'zh', flag: '🇨🇳', name: 'Chinese' },
  { code: 'hi', flag: '🇮🇳', name: 'Hindi' },
  { code: 'ja', flag: '🇯🇵', name: 'Japanese' },
  { code: 'es', flag: '🇪🇸', name: 'Spanish' },
  { code: 'pt', flag: '🇧🇷', name: 'Portuguese' },
  { code: 'ar', flag: '🇸🇦', name: 'Arabic' },
  { code: 'tr', flag: '🇹🇷', name: 'Turkish' },
  { code: 'ru', flag: '🇷🇺', name: 'Russian' },
  { code: 'fr', flag: '🇫🇷', name: 'French' },
  { code: 'de', flag: '🇩🇪', name: 'German' },
  { code: 'nl', flag: '🇳🇱', name: 'Dutch' },
  { code: 'da', flag: '🇩🇰', name: 'Danish' },
  { code: 'sv', flag: '🇸🇪', name: 'Swedish' },
  { code: 'ko', flag: '🇰🇷', name: 'Korean' },
]

function ProfileCard({ profile, selected, onSelect, onEdit, onDelete }) {
  const langs = (profile.languages || ['en'])
  const isSelected = selected?.id === profile.id

  return (
    <div
      onClick={() => onSelect(profile)}
      className={`border cursor-pointer transition p-3 ${
        isSelected ? 'border-tomato bg-tomato-soft' : 'border-rule bg-paper hover:bg-paper-deep'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className={`font-display text-[14px] truncate ${isSelected ? 'text-tomato' : 'text-ink'}`}>
            {profile.name || profile.search_terms.join(' + ')}
          </p>
          <div className="flex flex-wrap gap-1 mt-1.5">
            {profile.search_terms.map((t, i) => (
              <span key={t} className="flex items-center">
                <span className="font-mono text-[10px] bg-paper-deep border border-rule px-1.5 py-0.5 text-ink-soft">
                  {t}
                </span>
                {i < profile.search_terms.length - 1 && (
                  <span className="font-mono text-[10px] text-tomato mx-0.5">+</span>
                )}
              </span>
            ))}
          </div>
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <span className="font-mono text-[9px] text-ink-mute">
              🌐 {langs.length} {langs.length === 1 ? 'language' : 'languages'}
            </span>
            <span className="font-mono text-[9px] border border-rule px-1.5 py-0.5 text-ink-mute bg-paper-deep">
              {profile.frequency || 'weekly'}
            </span>
            {profile.intelligence_brief && (
              <span className="font-mono text-[9px] text-tomato">AI brief</span>
            )}
          </div>
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          {profile.new_since_last_visit > 0 && (
            <span className="font-mono text-[9px] tracking-[0.1em] uppercase bg-tomato text-paper px-1.5 py-0.5">
              +{profile.new_since_last_visit}
            </span>
          )}
          <div className="flex gap-1 mt-1">
            <button
              onClick={e => { e.stopPropagation(); onEdit(profile) }}
              className="font-mono text-[9px] tracking-[0.1em] uppercase text-ink-mute hover:text-ink px-1"
            >
              Edit
            </button>
            <button
              onClick={e => { e.stopPropagation(); onDelete(profile.id) }}
              className="font-mono text-[9px] tracking-[0.1em] uppercase text-tomato/60 hover:text-tomato px-1"
            >
              ×
            </button>
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
      e.preventDefault(); addTag(tagInput); setTagInput('')
    } else if (e.key === 'Backspace' && !tagInput && termTags.length > 0) {
      setTermTags(prev => prev.slice(0, -1))
    }
  }

  const toggleLang = (code) =>
    setLangs(prev => prev.includes(code) ? prev.filter(x => x !== code) : [...prev, code])

  const handleSuggest = async () => {
    if (termTags.length === 0) return
    setSuggesting(true); setAiSuggestions([]); setSuggestError('')
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
    <div className="border border-tomato/40 bg-tomato-soft p-4 space-y-4">
      {/* Name */}
      <div>
        <label className="font-mono text-[9px] tracking-[0.16em] uppercase text-ink-mute block mb-1">
          Profile name
        </label>
        <input
          value={name}
          onChange={e => setName(e.target.value)}
          placeholder="e.g. ToBRFV Resistance"
          className="w-full border border-rule bg-paper px-3 py-1.5 text-sm text-ink outline-none focus:border-tomato"
        />
      </div>

      {/* Keywords */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="font-mono text-[9px] tracking-[0.16em] uppercase text-ink-mute">Keywords</label>
          <button
            onClick={handleSuggest}
            disabled={suggesting || termTags.length === 0}
            className="font-mono text-[9px] tracking-[0.1em] uppercase border border-rule bg-paper text-ink-mute hover:text-tomato hover:border-tomato px-2 py-1 disabled:opacity-40 transition"
          >
            {suggesting ? '⟳ Suggesting…' : '✦ AI Suggest'}
          </button>
        </div>
        <div
          className="flex flex-wrap gap-1.5 w-full border border-rule bg-paper px-3 py-2 focus-within:border-tomato cursor-text"
          onClick={() => document.getElementById('tag-input')?.focus()}
        >
          {termTags.map((t, i) => (
            <span key={t} className="flex items-center gap-0.5">
              <span className="font-mono text-[10px] bg-paper-deep border border-rule px-2 py-0.5 text-ink-soft flex items-center gap-1">
                {t}
                <button
                  onClick={e => { e.stopPropagation(); setTermTags(prev => prev.filter(x => x !== t)) }}
                  className="text-tomato hover:text-tomato-deep leading-none ml-0.5"
                >×</button>
              </span>
              {i < termTags.length - 1 && (
                <span className="font-mono text-[10px] text-tomato">+</span>
              )}
            </span>
          ))}
          <input
            id="tag-input"
            value={tagInput}
            onChange={e => setTagInput(e.target.value)}
            onKeyDown={handleTagKeyDown}
            onBlur={() => { if (tagInput.trim()) { addTag(tagInput); setTagInput('') } }}
            placeholder={termTags.length === 0 ? 'Type a term and press Enter…' : ''}
            className="flex-1 min-w-[120px] outline-none text-sm bg-transparent py-0.5 text-ink"
          />
        </div>
        <p className="font-mono text-[9px] text-ink-mute mt-1">Enter or comma to add · Backspace removes last</p>

        {aiSuggestions.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {aiSuggestions.map(s => (
              <button
                key={s}
                onClick={() => { setTermTags(p => p.includes(s) ? p : [...p, s]); setAiSuggestions(p => p.filter(x => x !== s)) }}
                className="font-mono text-[9px] tracking-[0.1em] uppercase border border-tomato/40 bg-paper text-tomato px-2 py-0.5 hover:bg-tomato-soft transition"
              >
                + {s}
              </button>
            ))}
          </div>
        )}
        {suggestError && <p className="font-mono text-[10px] text-tomato mt-1">{suggestError}</p>}
      </div>

      {/* Languages */}
      <div>
        <label className="font-mono text-[9px] tracking-[0.16em] uppercase text-ink-mute block mb-2">
          Search languages
        </label>
        <div className="flex flex-wrap gap-1.5">
          {LANG_OPTIONS.map(l => (
            <button
              key={l.code}
              onClick={() => toggleLang(l.code)}
              className={`flex items-center gap-1 px-2 py-1 font-mono text-[10px] border transition ${
                langs.includes(l.code)
                  ? 'bg-tomato text-paper border-tomato'
                  : 'bg-paper border-rule text-ink-soft hover:border-ink-mute'
              }`}
            >
              <span>{l.flag}</span>
              <span>{l.name}</span>
            </button>
          ))}
        </div>
        <p className="font-display italic text-[11px] text-ink-mute mt-2">
          {langs.length === 1 && langs[0] === 'en'
            ? 'Searching in English only.'
            : `Searching across ${langs.length} languages. Non-English results will include English abstracts.`
          }
        </p>
      </div>

      {/* Frequency */}
      <div>
        <label className="font-mono text-[9px] tracking-[0.16em] uppercase text-ink-mute block mb-1">Frequency</label>
        <div className="flex border border-rule overflow-hidden">
          {FREQ_OPTIONS.map(f => (
            <button
              key={f}
              onClick={() => setFreq(f)}
              className={`font-mono text-[10px] tracking-[0.1em] uppercase px-3 py-1.5 transition ${
                freq === f ? 'bg-ink text-paper' : 'bg-paper text-ink-soft hover:bg-paper-deep'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Intelligence brief */}
      <div>
        <label className="font-mono text-[9px] tracking-[0.16em] uppercase text-ink-mute block mb-1">
          Intelligence brief
          <span className="ml-1 normal-case font-body text-[10px] text-ink-mute">(optional)</span>
        </label>
        <textarea
          value={brief}
          onChange={e => setBrief(e.target.value)}
          rows={4}
          placeholder="Describe what is relevant to you. E.g. We are a tomato seed breeder focused on ToBRFV and TYLCV resistance. We compete with Rijk Zwaan and Enza Zaden. Key markets: Netherlands, Spain, Mexico."
          className="w-full border border-rule bg-paper px-3 py-2 text-sm text-ink outline-none focus:border-tomato leading-relaxed resize-y"
        />
        <p className="font-mono text-[9px] text-ink-mute mt-1">
          Claude scores each matched article against this brief.
        </p>
      </div>

      <div className="flex gap-2 pt-1">
        <button
          onClick={handleSave}
          disabled={saving || termTags.length === 0}
          className="font-mono text-[10px] tracking-[0.12em] uppercase bg-tomato text-paper px-4 py-2 hover:bg-tomato-deep disabled:opacity-50 transition"
        >
          {saving ? 'Saving…' : 'Save profile'}
        </button>
        <button
          onClick={onCancel}
          className="font-mono text-[10px] tracking-[0.12em] uppercase border border-rule text-ink-mute px-4 py-2 hover:bg-paper-deep transition"
        >
          Cancel
        </button>
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
    if (autoSelect && data?.length > 0) onProfileSelect(data[0])
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
        <p className="font-mono text-[9px] tracking-[0.2em] uppercase text-ink-mute">
          Search profiles <span className="text-ink-soft">({profiles.length})</span>
        </p>
        {!showForm && (
          <button
            onClick={() => { setEditingProfile(null); setShowForm(true) }}
            className="font-mono text-[9px] tracking-[0.12em] uppercase text-tomato hover:text-tomato-deep"
          >
            + Add profile
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
        <p className="font-display italic text-sm text-ink-mute">No profiles yet. Create one to start tracking.</p>
      )}

      <div className="grid grid-cols-1 gap-1 sm:grid-cols-2">
        {profiles.map(p => (
          <ProfileCard
            key={p.id}
            profile={p}
            selected={selectedProfile}
            onSelect={onProfileSelect}
            onEdit={prof => { setEditingProfile(prof); setShowForm(true) }}
            onDelete={handleDelete}
          />
        ))}
      </div>
    </div>
  )
}
