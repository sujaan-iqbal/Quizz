import React, { useState } from 'react'

const Quiz = ({ questions, onComplete }) => {
  const [answers, setAnswers] = useState({})
  const [submitted, setSubmitted] = useState(false)

  const handleAnswer = (questionIndex, optionKey) => {
    if (!submitted) {
      setAnswers({ ...answers, [questionIndex]: optionKey })
    }
  }

  const handleSubmit = () => {
    if (Object.keys(answers).length !== questions.length) {
      alert(`Please answer all ${questions.length} questions before submitting.`)
      return
    }
    setSubmitted(true)
    onComplete(answers, questions)
  }

  if (submitted) return null

  const answered = Object.keys(answers).length
  const progress = (answered / questions.length) * 100

  return (
    <div className="anim-fade-up">
      <div className="card sticky-progress" style={{marginBottom:12}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:8}}>
          <h2 style={{fontWeight:700,fontSize:20}}>Quiz</h2>
          <div style={{padding:'6px 10px',borderRadius:999,background:'rgba(124,58,237,0.12)',border:'1px solid rgba(124,58,237,0.24)',color:'var(--accent-purple)',fontWeight:700}}>{answered} / {questions.length}</div>
        </div>
        <div style={{height:6,background:'rgba(255,255,255,0.03)',borderRadius:999,overflow:'hidden'}}>
          <div style={{height:'100%',background:'linear-gradient(90deg,var(--accent-purple),var(--accent-cyan))',width:`${progress}%`,transition:'width 0.4s ease'}} />
        </div>
      </div>

      <div style={{display:'flex',flexDirection:'column',gap:12}}>
        {questions.map((q, idx) => (
          <div key={idx} className="question-card">
            <div style={{marginBottom:10}}>
              <div style={{fontSize:12,fontWeight:700,color:'var(--accent-purple)',marginBottom:6}}>Q{idx+1}</div>
              <div style={{fontWeight:700,fontSize:16,color: 'var(--text-primary)'}}>{q.question}</div>
            </div>

            <div style={{display:'flex',flexDirection:'column',gap:8}}>
              {Object.entries(q.options).map(([key,value])=>{
                const selected = answers[idx] === key
                return (
                  <div key={key} className={`option ${selected? 'selected':''}`} onClick={()=>handleAnswer(idx,key)}>
                    <div style={{width:18,height:18,borderRadius:999,flexShrink:0,background:selected? 'var(--accent-purple)':'transparent',border:`2px solid ${selected? 'var(--accent-purple)':'rgba(255,255,255,0.06)'}`}} />
                    <div style={{color:selected? 'var(--text-primary)':'var(--text-secondary)'}}><strong style={{marginRight:8,color:selected? 'var(--accent-purple)':'var(--text-secondary)'}}>{key}.</strong>{value}</div>
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      <div style={{marginTop:12}}>
        <button onClick={handleSubmit} className="btn btn-primary" style={{width:'100%'}}>
          {answered < questions.length ? `Answer all questions (${questions.length - answered} remaining)` : '✅ Submit Quiz'}
        </button>
      </div>
    </div>
  )
}

export default Quiz