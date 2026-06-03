// frontend/src/components/Results.jsx
import React from 'react'
import { Award, RotateCcw, CheckCircle, XCircle } from 'lucide-react'

const Results = ({ score, total, percentage, questions, answers, onReset }) => {
  const getMessage = () => {
    if (percentage >= 80) return { text: 'Excellent! You really know this material!', color: 'text-green-400' }
    if (percentage >= 60) return { text: 'Good job! A bit more review and you will ace it!', color: 'text-yellow-400' }
    return { text: 'Keep studying! Review the material and try again.', color: 'text-blue-400' }
  }

  const message = getMessage()

  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-gray-800 rounded-lg p-8 text-center mb-6">
        <Award className="w-20 h-20 text-yellow-500 mx-auto mb-4" />
        <h2 className="text-3xl font-bold text-white mb-2">Quiz Complete!</h2>
        <div className="my-6">
          <div className="text-6xl font-bold text-purple-400 mb-2">
            {percentage}%
          </div>
          <p className="text-gray-400">
            {score} out of {total} correct
          </p>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-4 mb-6">
          <div
            className="bg-purple-600 h-4 rounded-full transition-all duration-500"
            style={{ width: `${percentage}%` }}
          />
        </div>
        <p className={`text-lg ${message.color} mb-8`}>
          {message.text}
        </p>
        <button
          onClick={onReset}
          className="inline-flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
          Create New Quiz
        </button>
      </div>

      {/* Detailed explanations for each question */}
      <div className="space-y-4">
        <h3 className="text-xl font-bold text-white">Detailed Review</h3>
        {questions.map((q, idx) => {
          const userAnswer = answers[idx]
          const isCorrect = userAnswer === q.correct
          return (
            <div key={idx} className="bg-gray-800 rounded-lg p-6">
              <div className="flex items-start gap-3">
                {isCorrect ? (
                  <CheckCircle className="w-6 h-6 text-green-500 flex-shrink-0 mt-1" />
                ) : (
                  <XCircle className="w-6 h-6 text-red-500 flex-shrink-0 mt-1" />
                )}
                <div className="flex-1">
                  <p className="text-white font-semibold">{q.question}</p>
                  <div className="mt-2 space-y-1 text-sm">
                    <p className="text-green-400">
                      ✅ Correct answer: {q.correct}. {q.options[q.correct]}
                    </p>
                    {!isCorrect && (
                      <p className="text-red-400">
                        ❌ Your answer: {userAnswer}. {userAnswer && q.options[userAnswer]}
                      </p>
                    )}
                    {q.explanation && (
                      <details className="mt-2">
                        <summary className="cursor-pointer text-gray-400 hover:text-white">View Explanation</summary>
                        <p className="mt-2 text-gray-300 bg-gray-700 p-3 rounded-lg">
                          {q.explanation}
                        </p>
                      </details>
                    )}
                  </div>
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