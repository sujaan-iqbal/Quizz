import axios from 'axios'

// Update this to your Cloudflare Worker URL after deployment
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://quiz-ai-backend.your-subdomain.workers.dev'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes for AI generation
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add user ID to all requests
api.interceptors.request.use(async (config) => {
  const userId = localStorage.getItem('user_id')
  if (userId) {
    config.headers['X-User-Id'] = userId
  }
  return config
})

export const uploadPDF = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await api.post('/api/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data
}

export const generateQuiz = async (sourceId, difficulty, numQuestions, topicFocus = '') => {
  const response = await api.post('/api/generate-quiz', {
    source_id: sourceId,
    difficulty,
    num_questions: numQuestions,
    topic_focus: topicFocus
  })
  return response.data
}

export const submitQuiz = async (quizId, answers, questions) => {
  const response = await api.post('/api/submit-quiz', {
    quiz_id: quizId,
    answers,
    questions
  })
  return response.data
}

export const getUserQuizzes = async () => {
  const response = await api.get('/api/user/quizzes')
  return response.data
}

export const healthCheck = async () => {
  const response = await api.get('/api/health')
  return response.data
}

export default api