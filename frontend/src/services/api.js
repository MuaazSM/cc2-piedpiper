import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Interceptors ──────────────────────────────────────────
api.interceptors.response.use(
  res  => res.data,
  err  => {
    const msg = err.response?.data?.detail ?? err.message ?? 'API Error'
    return Promise.reject(new Error(msg))
  }
)

// ── Shipments — POST /shipments · GET /shipments ──────────
export const shipmentApi = {
  getAll:  ()       => api.get('/shipments'),
  create:  (data)   => api.post('/shipments', data),
  seed:    ()       => api.post('/seed'),          // seed synthetic data
}

// ── Optimize — POST /optimize · GET /plan/{id} ────────────
export const optimizeApi = {
  run:     (body)   => api.post('/optimize', body),
  getPlan: (id)     => api.get(`/plan/${id}`),
}

// ── Simulate — POST /simulate ─────────────────────────────
export const simulateApi = {
  run:     (body)   => api.post('/simulate', body),
}

// ── Metrics — GET /metrics ────────────────────────────────
export const metricsApi = {
  get:     ()       => api.get('/metrics'),
}

export default api