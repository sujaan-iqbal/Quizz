import React, { useState } from 'react'

const QuizSettings = ({ onGenerate, loading }) => {
  const [difficulty, setDifficulty] = useState('standard')
  const [numQuestions, setNumQuestions] = useState(10)
  const [topicFocus, setTopicFocus] = useState('')

  const presets = {
    basic:        { label: 'Basic',      questions: 5,  difficulty: 'basic',    description: 'Easy recall',      emoji: '🌱' },
    intermediate: { label: 'Standard',   questions: 10, difficulty: 'standard', description: 'Comprehension',    emoji: '⚡' },
    advanced:     { label: 'Advanced',   questions: 20, difficulty: 'advanced', description: 'Analysis',         emoji: '🔥' },
    deepdive:     { label: 'Deep Dive',  questions: 30, difficulty: 'advanced', description: 'Expert level',     emoji: '💎' },
  }

  const difficultyMeta = {
    basic:    { color: '#34d399', glow: 'rgba(52,211,153,0.35)', label: 'Basic' },
    standard: { color: '#60a5fa', glow: 'rgba(96,165,250,0.35)', label: 'Standard' },
    advanced: { color: '#f472b6', glow: 'rgba(244,114,182,0.35)', label: 'Advanced' },
  }

  const handlePreset = (presetKey) => {
    const preset = presets[presetKey]
    setNumQuestions(preset.questions)
    setDifficulty(preset.difficulty)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    onGenerate({ difficulty, numQuestions, topicFocus })
  }

  const dm = difficultyMeta[difficulty]

  return (
    <div className="anim-fade-up">
      <div style={{textAlign:'center',marginBottom:8}}>
        <h2 style={{fontWeight:700,fontSize:28}}>Configure your quiz</h2>
        <p style={{color:'var(--text-secondary)'}}>Tune the difficulty and scope before generating</p>
      </div>

      <div className="card">
        {/* Quick Presets */}
        <div className="animate-fade-in-delay-1" style={{ marginBottom:'2rem' }}>
          <p style={{ fontSize:12, fontWeight:600, letterSpacing:'0.08em', textTransform:'uppercase', color:'rgba(148,163,184,0.6)', marginBottom:'0.75rem' }}>
            Quick Presets
          </p>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(120px,1fr))',  gap:10 }}>
            {Object.entries(presets).map(([key, preset]) => (
              <button
                key={key}
                type="button"
                onClick={() => handlePreset(key)}
                className="btn btn-muted"
              >
                <div style={{ fontSize:20, marginBottom:4 }}>{preset.emoji}</div>
                <div style={{ fontFamily:'Syne, sans-serif', fontWeight:600, fontSize:13, color:'#e2e8f0', marginBottom:2 }}>
                  {preset.label}
                </div>
                <div style={{ fontSize:11, color:'rgba(148,163,184,0.5)' }}>
                  {preset.questions}Q
                </div>
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Divider */}
          <div style={{ height:1, background:'rgba(255,255,255,0.02)', marginBottom:'1.25rem' }} />

          {/* Difficulty */}
          <div className="animate-fade-in-delay-2" style={{ marginBottom:'1.75rem' }}>
            <p style={{ fontSize:12, fontWeight:600, letterSpacing:'0.08em', textTransform:'uppercase', color:'rgba(148,163,184,0.6)', marginBottom:'0.75rem' }}>
              Difficulty
            </p>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(140px,1fr))', gap:10 }}>
              {Object.entries(difficultyMeta).map(([level, meta]) => {
                const active = difficulty === level
                return (
                  <button key={level} type="button" onClick={() => setDifficulty(level)} className={`btn ${active? 'btn-primary':''}`}>
                    {meta.label}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Number of questions slider */}
          <div className="animate-fade-in-delay-2" style={{ marginBottom:'1.75rem' }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'baseline', marginBottom:'0.75rem' }}>
              <p style={{ fontSize:12, fontWeight:600, letterSpacing:'0.08em', textTransform:'uppercase', color:'rgba(148,163,184,0.6)' }}>
                Questions
              </p>
              <span style={{
                fontFamily:'Syne, sans-serif', fontWeight:700, fontSize:22,
                background:'linear-gradient(135deg, #a78bfa, #06b6d4)',
                WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent', backgroundClip:'text'
              }}>
                {numQuestions}
              </span>
            </div>
            <input type="range" min="3" max="30" value={numQuestions} onChange={(e) => setNumQuestions(parseInt(e.target.value))} style={{ width:'100%' }} />
            <div style={{ display:'flex', justifyContent:'space-between', marginTop:6 }}>
              {[3, 10, 20, 30].map(n => (
                <span key={n} style={{ fontSize:11, color:'rgba(148,163,184,0.35)' }}>{n}</span>
              ))}
            </div>
          </div>

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

          {/* Submit */}
          <button type="submit" disabled={loading} className="btn btn-primary" style={{width:'100%'}}>
            {loading ? 'Generating…' : '✨ Generate Quiz'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default QuizSettings