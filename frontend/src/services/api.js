import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE,
  timeout: 120_000,
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
  getAll:  (params) => api.get('/shipments', { params }),
  create:  (data)   => api.post('/shipments', data),
  seed:    (params) => api.post('/dev/seed', null, { params }),
}

// ── Optimize — POST /optimize · GET /plan/{id} ────────────
export const optimizeApi = {
  run:     (params) => api.post('/optimize', null, { params }),
  getPlan: (id)     => api.get(`/plan/${id}`),
}

// ── Simulate — POST /simulate ─────────────────────────────
export const simulateApi = {
  run:     (params) => api.post('/simulate', null, { params }),
}

// ── Metrics — GET /metrics ────────────────────────────────
export const metricsApi = {
  get:     (planId) => api.get('/metrics', { params: { plan_id: planId } }),
}

export default api