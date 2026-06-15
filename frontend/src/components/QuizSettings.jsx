import React, { useState } from 'react'

const QuizSettings = ({ onGenerate, loading }) => {
  const [selectedPreset, setSelectedPreset] = useState('intermediate') // default Standard
  const [topicFocus, setTopicFocus] = useState('')

  const presets = {
    basic:        { label: 'Basic',      questions: 10,  difficulty: 'basic',    emoji: '🌱' },
    intermediate: { label: 'Standard',   questions: 10,  difficulty: 'standard', emoji: '⚡' },
    advanced:     { label: 'Advanced',   questions: 20,  difficulty: 'advanced', emoji: '🔥' },
    deepdive:     { label: 'Deep Dive',  questions: 30,  difficulty: 'advanced', emoji: '💎' },
  }

  const handlePreset = (presetKey) => {
    setSelectedPreset(presetKey)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    const preset = presets[selectedPreset]
    onGenerate({ 
      difficulty: preset.difficulty, 
      numQuestions: preset.questions, 
      topicFocus 
    })
  }

  return (
    <div className="anim-fade-up">
      <div style={{textAlign:'center',marginBottom:8}}>
        <h2 style={{fontWeight:700,fontSize:28}}>Configure your quiz</h2>
        <p style={{color:'var(--text-secondary)'}}>Tune the difficulty and scope before generating</p>
      </div>

      <div className="card">
        {/* Quiz Type Presets */}
        <div className="animate-fade-in-delay-1" style={{ marginBottom:'2rem' }}>
          <p style={{ fontSize:12, fontWeight:600, letterSpacing:'0.08em', textTransform:'uppercase', color:'rgba(148,163,184,0.6)', marginBottom:'0.75rem' }}>
            Quiz type
          </p>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(120px,1fr))', gap:10 }}>
            {Object.entries(presets).map(([key, preset]) => {
              const isActive = selectedPreset === key
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => handlePreset(key)}
                  className={`btn ${isActive ? 'btn-primary' : 'btn-muted'}`}
                  style={{
                    transition: 'all 0.2s ease',
                    transform: isActive ? 'scale(1.02)' : 'scale(1)',
                    boxShadow: isActive ? '0 0 0 2px var(--accent-purple), 0 4px 12px rgba(0,0,0,0.15)' : 'none'
                  }}
                >
                  <div style={{ fontSize:20, marginBottom:4 }}>{preset.emoji}</div>
                  <div style={{ fontFamily:'Syne, sans-serif', fontWeight:600, fontSize:13, color: isActive ? '#fff' : '#e2e8f0', marginBottom:2 }}>
                    {preset.label}
                  </div>
                </button>
              )
            })}
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ height:1, background:'rgba(255,255,255,0.02)', marginBottom:'1.25rem' }} />

          {/* Topic focus */}
          <div className="animate-fade-in-delay-3" style={{ marginBottom:'2rem' }}>
            <p style={{ fontSize:12, fontWeight:600, letterSpacing:'0.08em', textTransform:'uppercase', color:'rgba(148,163,184,0.6)', marginBottom:'0.75rem' }}>
              Topic Focus <span style={{ color:'rgba(148,163,184,0.3)', fontWeight:400, textTransform:'none', letterSpacing:0, fontSize:11 }}>optional</span>
            </p>
            <input type="text" value={topicFocus} onChange={(e) => setTopicFocus(e.target.value)} placeholder="e.g. machine learning, chapter 3, neural networks…" className="input" />
            <p style={{ fontSize:11, color:'rgba(148,163,184,0.35)', marginTop:6 }}>
              Leave blank to cover all key concepts
            </p>
          </div>

          <button type="submit" disabled={loading} className="btn btn-primary" style={{width:'100%'}}>
            {loading ? 'Generating…' : '✨ Generate Quiz'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default QuizSettings