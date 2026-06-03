// frontend/src/components/Quiz.jsx
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

  if (submitted) {
    return null // Results will be shown by parent component
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-gray-800 rounded-lg p-6 mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">Quiz</h2>
        <p className="text-gray-400">Select an answer for each question. Click Submit when done.</p>
        <p className="text-purple-400 mt-2">Answered: {Object.keys(answers).length} / {questions.length}</p>
      </div>

      {questions.map((q, idx) => (
        <div key={idx} className="bg-gray-800 rounded-lg p-6 mb-4">
          <div className="mb-4">
            <span className="text-purple-400 text-sm font-semibold">
              Question {idx + 1} of {questions.length}
            </span>
            <h3 className="text-white text-lg mt-1">{q.question}</h3>
          </div>

          <div className="space-y-3">
            {Object.entries(q.options).map(([key, value]) => (
              <label
                key={key}
                className={`flex items-center p-3 rounded-lg cursor-pointer transition-colors ${
                  answers[idx] === key
                    ? 'bg-purple-600/20 border-2 border-purple-500'
                    : 'bg-gray-700/50 border-2 border-transparent hover:bg-gray-700'
                }`}
              >
                <input
                  type="radio"
                  name={`q${idx}`}
                  value={key}
                  checked={answers[idx] === key}
                  onChange={() => handleAnswer(idx, key)}
                  className="w-4 h-4 text-purple-600 focus:ring-purple-500 mr-3"
                />
                <span className="text-gray-200">
                  <span className="font-semibold mr-2">{key}.</span>
                  {value}
                </span>
              </label>
            ))}
          </div>
        </div>
      ))}

      <button
        onClick={handleSubmit}
        className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
      >
        Submit Quiz
      </button>
    </div>
  )
}

export default Quiz