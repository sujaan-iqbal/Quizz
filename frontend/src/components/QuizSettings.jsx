// frontend/src/components/QuizSettings.jsx
import React, { useState } from 'react'

const QuizSettings = ({ onGenerate, loading }) => {
  const [difficulty, setDifficulty] = useState('standard')
  const [numQuestions, setNumQuestions] = useState(10)
  const [topicFocus, setTopicFocus] = useState('')

  const presets = {
    basic: { label: 'Basic', questions: 5, difficulty: 'basic', description: 'Easy factual recall' },
    intermediate: { label: 'Intermediate', questions: 10, difficulty: 'standard', description: 'Medium comprehension' },
    advanced: { label: 'Advanced', questions: 20, difficulty: 'advanced', description: 'Hard analysis' },
    deepdive: { label: 'Deep Dive', questions: 30, difficulty: 'advanced', description: 'Expert level' }
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

  return (
    <div className="max-w-2xl mx-auto bg-gray-800 rounded-lg p-6">
      <h2 className="text-2xl font-bold text-white mb-6">Quiz Settings</h2>
      
      {/* Preset Buttons */}
      <div className="mb-6">
        <label className="block text-gray-300 mb-2">Quick Presets</label>
        <div className="grid grid-cols-4 gap-2">
          {Object.entries(presets).map(([key, preset]) => (
            <button
              key={key}
              type="button"
              onClick={() => handlePreset(key)}
              className="px-3 py-2 bg-gray-700 hover:bg-purple-600 text-white rounded-lg text-sm transition-colors"
            >
              {preset.label}<br/>
              <span className="text-xs text-gray-400">{preset.questions} Q</span>
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="mb-6">
          <label className="block text-gray-300 mb-2">Difficulty Level</label>
          <div className="grid grid-cols-3 gap-3">
            {['basic', 'standard', 'advanced'].map((level) => (
              <button
                key={level}
                type="button"
                onClick={() => setDifficulty(level)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  difficulty === level
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {level.charAt(0).toUpperCase() + level.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div className="mb-6">
          <label className="block text-gray-300 mb-2">
            Number of Questions: {numQuestions}
          </label>
          <input
            type="range"
            min="3"
            max="30"
            value={numQuestions}
            onChange={(e) => setNumQuestions(parseInt(e.target.value))}
            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-gray-500 text-sm mt-1">
            <span>3</span>
            <span>15</span>
            <span>30</span>
          </div>
        </div>

        <div className="mb-6">
          <label className="block text-gray-300 mb-2">
            Topic Focus (optional)
          </label>
          <input
            type="text"
            value={topicFocus}
            onChange={(e) => setTopicFocus(e.target.value)}
            placeholder="e.g., machine learning, statistics, history..."
            className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500"
          />
          <p className="text-gray-500 text-sm mt-1">
            Leave empty to focus on main concepts
          </p>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Generating Quiz...' : 'Generate Quiz'}
        </button>
      </form>
    </div>
  )
}

export default QuizSettings