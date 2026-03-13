/**
 * @fileoverview API Client — обёртка для запросов к Pulse Backend.
 *
 * Автоматически:
 * - Добавляет Bearer токен из localStorage
 * - Обрабатывает 401 → редирект на /login
 * - Возвращает JSON или выбрасывает ошибку с полем message
 */

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

/**
 * Базовая функция запроса к API.
 *
 * @param {string} path - Путь относительно /api/v1 (напр. "/financial/cash-flow")
 * @param {RequestInit} [options={}] - Дополнительные опции fetch
 * @returns {Promise<any>} Декодированный JSON ответ
 * @throws {Error} С полем `message` из тела ошибки API
 */
async function request(path, options = {}) {
  const token = localStorage.getItem('pulse_token')

  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  })

  // 401 → очищаем токен и редиректим на логин
  if (response.status === 401) {
    localStorage.removeItem('pulse_token')
    window.location.href = '/login'
    return
  }

  const data = await response.json()

  if (!response.ok) {
    const message = data?.error?.message || data?.detail || `HTTP ${response.status}`
    const error = new Error(message)
    error.status = response.status
    error.code = data?.error?.code
    throw error
  }

  return data
}

// ──────────────────────────────────────────────
// API Methods
// ──────────────────────────────────────────────

export const api = {
  /** Аутентификация */
  auth: {
    login: (email, password) =>
      request('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),
    me: () => request('/auth/me'),
    refresh: (refreshToken) =>
      request('/auth/refresh', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: refreshToken }),
      }),
  },

  /** Финансовые отчёты */
  financial: {
    cashFlow: (params) =>
      request(`/financial/cash-flow?${new URLSearchParams(params)}`),
    incomeStatement: (params) =>
      request(`/financial/income-statement?${new URLSearchParams(params)}`),
    balanceSheet: (params) =>
      request(`/financial/balance-sheet?${new URLSearchParams(params)}`),
  },

  /** Оборотный капитал */
  workingCapital: {
    ccc: (params) =>
      request(`/working-capital/ccc?${new URLSearchParams(params)}`),
    arAging: (params) =>
      request(`/working-capital/ar-aging?${new URLSearchParams(params)}`),
    apAging: (params) =>
      request(`/working-capital/ap-aging?${new URLSearchParams(params)}`),
  },

  /** Складская аналитика */
  inventory: {
    abcXyz: (params) =>
      request(`/inventory/abc-xyz?${new URLSearchParams(params)}`),
    gmroi: (params) =>
      request(`/inventory/gmroi?${new URLSearchParams(params)}`),
  },

  /** Клиентская аналитика */
  analytics: {
    ltvCac: (params) =>
      request(`/analytics/ltv-cac?${new URLSearchParams(params)}`),
  },

  /** Дашборды */
  dashboards: {
    cfo: (params) =>
      request(`/dashboards/cfo?${new URLSearchParams(params)}`),
    commercial: (params) =>
      request(`/dashboards/commercial?${new URLSearchParams(params)}`),
  },

  /** Синхронизация */
  sync: {
    status: () => request('/sync/status'),
    triggerFull: () => request('/admin/sync/full', { method: 'POST' }),
  },
}

export default api
