import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add user ID to requests
api.interceptors.request.use(async (config) => {
  const { getCurrentUser } = await import('./supabase')
  const user = await getCurrentUser()
  if (user) {
    config.headers['X-User-Id'] = user.id
  }
  return config
})


export const uploadPDF = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data
}

export const generateQuiz = async (data) => {
  const response = await api.post('/generate-quiz', data)
  return response.data
}

export const submitQuiz = async (data) => {
  const response = await api.post('/submit-quiz', data)
  return response.data
}

export const getUserQuizzes = async () => {
  const response = await api.get('/user/quizzes')
  return response.data
}

export const healthCheck = async () => {
  const response = await api.get('/health')
  return response.data
}

export default api
