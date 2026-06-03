// frontend/src/App.jsx
import React, { useState, useEffect } from 'react'
import Auth from './components/Auth'
import FileUpload from './components/FileUpload'
import QuizSettings from './components/QuizSettings'
import Quiz from './components/Quiz'
import Results from './components/Results'
import { getCurrentUser, signOut } from './services/supabase'
import { generateQuiz, submitQuiz } from './services/api'

function App() {
  const [user, setUser] = useState(null)
  const [step, setStep] = useState('auth') // auth, upload, settings, quiz, results
  const [sourceId, setSourceId] = useState(null)
  const [quiz, setQuiz] = useState(null)
  const [quizId, setQuizId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  // Results state
  const [score, setScore] = useState(0)
  const [percentage, setPercentage] = useState(0)
  const [answers, setAnswers] = useState({})

  useEffect(() => {
    checkUser()
  }, [])

  const checkUser = async () => {
    const user = await getCurrentUser()
    setUser(user)
    if (user) setStep('upload')
  }

  const handleAuthSuccess = () => {
    checkUser()
  }

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
      const response = await submitQuiz({
        quiz_id: quizId,
        answers: userAnswers,
        questions: questions
      })
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            📚 PDF Quiz Generator
          </h1>
          <p className="text-gray-300">
            Upload any PDF and generate intelligent multiple-choice questions
          </p>
          {user && (
            <button
              onClick={handleLogout}
              className="mt-2 text-sm text-gray-400 hover:text-white"
            >
              Sign out ({user.email})
            </button>
          )}
        </header>

        {error && (
          <div className="max-w-2xl mx-auto mb-4 p-3 bg-red-500/10 border border-red-500 rounded-lg text-red-500 text-sm">
            {error}
          </div>
        )}

        {step === 'upload' && (
          <FileUpload onSuccess={handleUploadSuccess} />
        )}

        {step === 'settings' && (
          <QuizSettings onGenerate={handleGenerateQuiz} loading={loading} />
        )}

        {step === 'quiz' && quiz && (
          <Quiz questions={quiz} onComplete={handleQuizComplete} />
        )}

        {step === 'results' && quiz && (
          <Results
            score={score}
            total={quiz.length}
            percentage={percentage}
            questions={quiz}
            answers={answers}
            onReset={handleReset}
          />
        )}

        {loading && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-gray-800 p-6 rounded-lg">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto"></div>
              <p className="text-white mt-4">Processing...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App