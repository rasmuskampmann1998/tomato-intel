import { useState } from 'react'
import { Link } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { EXPERIENCE_CONFIG } from '../lib/experienceConfig'

const EXPERIENCES = ['researcher', 'grower', 'breeder']

export default function Register() {
  const [step, setStep] = useState(1)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [organization, setOrganization] = useState('')
  const [experience, setExperience] = useState('researcher')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleNext = (e) => {
    e.preventDefault()
    setError('')
    setStep(2)
  }

  const handleRegister = async () => {
    setError('')
    setLoading(true)
    const { data, error: signUpError } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { full_name: fullName, organization, experience },
      },
    })
    if (signUpError) {
      setError(signUpError.message)
      setLoading(false)
      return
    }
    // Seed source prefs for the chosen experience (best-effort)
    const userId = data?.user?.id
    if (userId) {
      await supabase.rpc('seed_source_prefs_for_user', {
        p_user_id: userId,
        p_experience: experience,
      }).catch(() => {})
    }
    setSuccess(true)
    setLoading(false)
  }

  if (success) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 w-full max-w-sm text-center">
          <div className="text-green-600 text-4xl mb-4">✓</div>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Check your email</h2>
          <p className="text-sm text-gray-500">
            We sent a confirmation link to <strong>{email}</strong>. Click it to activate your account.
          </p>
          <Link to="/login" className="block mt-6 text-sm text-green-600 hover:underline">
            Back to login
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 w-full max-w-sm">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Tomato Intel</h1>

        {step === 1 ? (
          <>
            <p className="text-sm text-gray-500 mb-6">Create your account</p>
            <form onSubmit={handleNext} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                <input
                  type="text" required value={fullName}
                  onChange={e => setFullName(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Organization</label>
                <input
                  type="text" value={organization}
                  onChange={e => setOrganization(e.target.value)}
                  placeholder="Optional"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email" required value={email}
                  onChange={e => setEmail(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <input
                  type="password" required value={password} minLength={6}
                  onChange={e => setPassword(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              <button
                type="submit"
                className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 rounded-lg text-sm transition"
              >
                Next →
              </button>
            </form>
          </>
        ) : (
          <>
            <p className="text-sm text-gray-500 mb-6">I am a...</p>
            <div className="space-y-3 mb-6">
              {EXPERIENCES.map(exp => {
                const cfg = EXPERIENCE_CONFIG[exp]
                const selected = experience === exp
                return (
                  <button
                    key={exp}
                    onClick={() => setExperience(exp)}
                    className={`w-full text-left border-2 rounded-xl p-4 transition ${
                      selected
                        ? 'border-green-500 bg-green-50'
                        : 'border-gray-200 bg-white hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{cfg.icon}</span>
                      <div>
                        <p className={`font-semibold text-sm ${selected ? 'text-green-700' : 'text-gray-900'}`}>
                          {cfg.label}
                        </p>
                        <p className="text-xs text-gray-500 mt-0.5">{cfg.description}</p>
                      </div>
                      {selected && (
                        <span className="ml-auto text-green-500 text-lg">✓</span>
                      )}
                    </div>
                  </button>
                )
              })}
            </div>
            {error && <p className="text-red-600 text-sm mb-3">{error}</p>}
            <div className="flex gap-2">
              <button
                onClick={() => setStep(1)}
                className="flex-1 border border-gray-300 text-gray-600 font-medium py-2 rounded-lg text-sm hover:bg-gray-50"
              >
                ← Back
              </button>
              <button
                onClick={handleRegister}
                disabled={loading}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 rounded-lg text-sm transition disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Account'}
              </button>
            </div>
          </>
        )}

        <p className="text-center text-sm text-gray-500 mt-4">
          Already have an account?{' '}
          <Link to="/login" className="text-green-600 hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
