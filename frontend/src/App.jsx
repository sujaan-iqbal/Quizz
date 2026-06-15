import React, { useState, useEffect } from 'react'
import Auth from './components/Auth'
import FileUpload from './components/FileUpload'
import QuizSettings from './components/QuizSettings'
import Quiz from './components/Quiz'
import Results from './components/Results'
import { getCurrentUser, signOut } from './services/supabase'
import { generateQuiz, submitQuiz } from './services/api'

const steps = ['upload', 'settings', 'quiz', 'results']
const stepLabels = { upload: 'Upload', settings: 'Configure', quiz: 'Quiz', results: 'Results' }

function App() {
  const [user, setUser] = useState(null)
  const [step, setStep] = useState('auth')
  const [sourceId, setSourceId] = useState(null)
  const [quiz, setQuiz] = useState(null)
  const [quizId, setQuizId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [score, setScore] = useState(0)
  const [percentage, setPercentage] = useState(0)
  const [answers, setAnswers] = useState({})

  useEffect(() => { checkUser() }, [])

  const checkUser = async () => {
    const user = await getCurrentUser()
    setUser(user)
    if (user) setStep('upload')
  }

  const handleAuthSuccess = () => { checkUser() }

  const handleLogout = async () => {
    await signOut()
    setUser(null)
    setStep('auth')
    setSourceId(null)
    setQuiz(null)
  }

  const handleUploadSuccess = (data) => {
    setSourceId(data.source_id)
    setStep('settings')
  }

  const handleGenerateQuiz = async (settings) => {
    setLoading(true)
    setError(null)
    try {
      const response = await generateQuiz({
        source_id: sourceId,
        difficulty: settings.difficulty,
        num_questions: settings.numQuestions,
        topic_focus: settings.topicFocus
      })
      setQuiz(response.questions)
      setQuizId(response.quiz_id)
      setStep('quiz')
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Failed to generate quiz')
    } finally {
      setLoading(false)
    }
  }

  const handleQuizComplete = async (userAnswers, questions) => {
    setLoading(true)
    try {
      const response = await submitQuiz({ quiz_id: quizId, answers: userAnswers, questions })
      setScore(response.score)
      setPercentage(response.percentage)
      setAnswers(userAnswers)
      setStep('results')
    } catch (err) {
      setError('Failed to submit quiz')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setStep('upload')
    setSourceId(null)
    setQuiz(null)
    setQuizId(null)
    setAnswers({})
    setScore(0)
    setPercentage(0)
  }

  if (!user && step === 'auth') {
    return <Auth onAuthSuccess={handleAuthSuccess} />
  }

  const currentStepIdx = steps.indexOf(step)

  return (
    <div>
      <header className="app-header">
  <div
    style={{
      maxWidth: '1100px',
      margin: '0 auto',
      padding: '16px',
      display: 'flex',
      flexDirection: 'column',
      gap: '16px'
    }}
  >
    {/* Top Row */}
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '12px'
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}
      >
        <div style={{ fontSize: '24px' }}>📚</div>

        <div
          style={{
            fontWeight: 800,
            fontSize: '28px',
            background: 'linear-gradient(135deg,#7C3AED,#06B6D4)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}
        >
          QuizzMe
        </div>
      </div>

      {user && (
        <button
          onClick={handleLogout}
          className="btn btn-muted"
        >
          Sign Out
        </button>
      )}
    </div>

    {/* Progress Navigation */}
    {step !== 'auth' && (
      <nav
        style={{
          display: 'flex',
          justifyContent: 'center',
          flexWrap: 'wrap',
          gap: '10px'
        }}
      >
        {steps.map((s) => (
          <div
            key={s}
            className={`progress-pill ${s === step ? 'active' : ''}`}
          >
            {stepLabels[s]}
          </div>
        ))}
      </nav>
    )}
  </div>
</header>

      <main className="container">
        {error && (
          <div className="card" style={{borderColor:'rgba(247,83,83,0.12)',background:'rgba(247,83,83,0.03)'}}>
            {error}
          </div>
        )}

        {step === 'upload'   && <FileUpload onSuccess={handleUploadSuccess} />}
        {step === 'settings' && <QuizSettings onGenerate={handleGenerateQuiz} loading={loading} />}
        {step === 'quiz'     && quiz && <Quiz questions={quiz} onComplete={handleQuizComplete} />}
        {step === 'results'  && quiz && (
          <Results
            score={score} total={quiz.length} percentage={percentage}
            questions={quiz} answers={answers} onReset={handleReset}
          />
        )}

      </main>

      {loading && (
        <div style={{position:'fixed',inset:0,zIndex:50,background:'rgba(10,12,18,0.6)',display:'flex',alignItems:'center',justifyContent:'center'}}>
          <div className="card" style={{textAlign:'center'}}>
            <div style={{width:56,height:56,margin:'0 auto 12px'}}>
              <svg width="56" height="56" viewBox="0 0 56 56">
                <circle cx="28" cy="28" r="22" stroke="rgba(124,58,237,0.18)" strokeWidth="3" fill="none" />
                <path d="M28 6 A22 22 0 0 1 50 28" stroke="url(#g)" strokeWidth="3" strokeLinecap="round" fill="none" />
                <defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#7C3AED"/><stop offset="100%" stopColor="#06B6D4"/></linearGradient></defs>
              </svg>
            </div>
            <div style={{fontWeight:700}}>Processing…</div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App