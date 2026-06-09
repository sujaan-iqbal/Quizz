import React, { useEffect, useState } from 'react'
import { RotateCcw } from 'lucide-react'

const ScoreRing = ({ percentage }) => {
  const [animatedPct, setAnimatedPct] = useState(0)
  const radius = 56
  const circ = 2 * Math.PI * radius
  const offset = circ - (animatedPct / 100) * circ

  useEffect(() => {
    const timer = setTimeout(() => setAnimatedPct(percentage), 100)
    return () => clearTimeout(timer)
  }, [percentage])

  const color = percentage >= 80 ? 'var(--accent-cyan)' : percentage >= 60 ? 'var(--accent-coral)' : 'var(--accent-purple)'
  const glow = percentage >= 80 ? 'rgba(6,182,212,0.44)' : percentage >= 60 ? 'rgba(249,115,96,0.38)' : 'rgba(124,58,237,0.38)'

  return (
  <div style={{ position:'relative', width:140, height:140, margin:'0 auto 1.5rem' }} className="score-ring">
      <svg width="140" height="140" viewBox="0 0 140 140">
        {/* Track */}
        <circle cx="70" cy="70" r={radius} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" />
        {/* Progress */}
        <circle
          cx="70" cy="70" r={radius}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          style={{ transition:'stroke-dashoffset 1s ease-out', transformOrigin:'70px 70px', transform:'rotate(-90deg)', filter:`drop-shadow(0 0 8px ${glow})` }}
        />
      </svg>
      {/* Center text */}
      <div style={{ position:'absolute', inset:0, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center' }}>
        <span style={{fontWeight:800,fontSize:30,color:color,lineHeight:1,textShadow:`0 0 20px ${glow}`}}>{percentage}</span>
        <span style={{ fontSize:12, color:'var(--text-secondary)', fontWeight:500 }}>%</span>
      </div>
    </div>
  )
}

const Results = ({ score, total, percentage, questions, answers, onReset }) => {
  const getMessage = () => {
    if (percentage >= 80) return { text: 'Excellent! You really know this material.', color: '#34d399' }
    if (percentage >= 60) return { text: 'Good job! A bit more review and you\'ll ace it.', color: '#fbbf24' }
    return { text: 'Keep studying — review the material and try again.', color: '#60a5fa' }
  }

  const message = getMessage()
  const [expandedIdx, setExpandedIdx] = useState(null)

  return (
    <div className="anim-fade-up" style={{paddingBottom:24}}>
      <div className="card" style={{textAlign:'center'}}>
        <ScoreRing percentage={percentage} />
        <h2 style={{fontWeight:800,fontSize:28,marginBottom:8}}>Quiz Complete</h2>
        <p style={{color:'var(--text-secondary)',marginBottom:12}}>{score} of {total} correct</p>
        <p style={{color:message.color,marginBottom:16,fontWeight:600}}>{message.text}</p>
        <button onClick={onReset} className="btn btn-primary"><RotateCcw style={{width:16,height:16}}/> New Quiz</button>
      </div>

      <h3 style={{fontWeight:700,fontSize:18,marginTop:12,color:'var(--text-primary)'}}>Detailed Review</h3>

      <div style={{display:'flex',flexDirection:'column',gap:10,marginTop:8}}>
        {questions.map((q, idx)=>{
          const userAnswer = answers[idx]
          const isCorrect = userAnswer === q.correct
          const open = expandedIdx === idx
          return (
            <div key={idx} className="card" style={{borderColor:isCorrect? 'rgba(124,58,237,0.06)': 'rgba(255,255,255,0.02)'}}>
              <div style={{display:'flex',gap:12,alignItems:'flex-start'}}>
                <div style={{width:36,height:36,borderRadius:999,flexShrink:0,display:'flex',alignItems:'center',justifyContent:'center',background:isCorrect? 'rgba(124,58,237,0.06)':'rgba(255,255,255,0.02)',border:`1px solid ${isCorrect? 'rgba(124,58,237,0.12)':'rgba(255,255,255,0.03)'}`}}>{isCorrect? '✓':'✗'}</div>
                <div
                    style={{
                    flex:1,
                    minWidth:0
                    }}
                  >
                  <div style={{fontWeight:700,color:'var(--text-primary)',marginBottom:8}}>{q.question}</div>
                  <div style={{display:'flex',flexDirection:'column',gap:6}}>
                    <div style={{color:'var(--accent-cyan)'}}>✅ {q.correct}. {q.options[q.correct]}</div>
                    {!isCorrect && <div style={{color:'var(--accent-coral)'}}>❌ {userAnswer}. {userAnswer && q.options[userAnswer]}</div>}
                  </div>
                  {q.explanation && (
                    <div style={{marginTop:10}}>
                      <button onClick={()=>setExpandedIdx(open? null: idx)} style={{background:'none',border:'none',color:'var(--text-secondary)',cursor:'pointer'}}>{open? 'Hide':'View'} explanation</button>
                      {open && <div className="card" style={{marginTop:8,background:'rgba(255,255,255,0.02)'}}>{q.explanation}</div>}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default Results