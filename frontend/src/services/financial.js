/**
 * @fileoverview TanStack Query хуки для финансовых отчётов.
 *
 * Каждый хук принимает объект params и стейл-таймы:
 * - Текущий месяц: 5 минут
 * - Прошлые периоды: 1 час (практически immutable)
 */

import { useQuery } from '@tanstack/react-query'
import { api } from './apiClient'
import { isCurrentPeriod } from '../utils/dateUtils'

// ──────────────────────────────────────────────
// Утилиты
// ──────────────────────────────────────────────

/**
 * Определяет staleTime в зависимости от периода.
 * Данные прошлых периодов кешируются на 1 час.
 *
 * @param {Object} params - Параметры запроса с start_date/end_date
 * @returns {number} staleTime в миллисекундах
 */
function getStaleTime(params) {
  if (isCurrentPeriod(params?.end_date)) {
    return 5 * 60 * 1000   // 5 минут — текущий период
  }
  return 60 * 60 * 1000    // 1 час — прошлые периоды
}

// ──────────────────────────────────────────────
// ОДДС — Cash Flow
// ──────────────────────────────────────────────

/**
 * Хук для получения ОДДС (Отчёт о движении денежных средств).
 *
 * @param {Object} params - {start_date, end_date, group_by?}
 * @returns TanStack Query result с данными денежного потока
 */
export function useCashFlow(params) {
  return useQuery({
    queryKey: ['cashFlow', params],
    queryFn: () => api.financial.cashFlow(params),
    staleTime: getStaleTime(params),
    enabled: !!(params?.start_date && params?.end_date),
  })
}

// ──────────────────────────────────────────────
// ОПиУ — Income Statement
// ──────────────────────────────────────────────

/**
 * Хук для получения ОПиУ (Отчёт о прибылях и убытках).
 *
 * @param {Object} params - {start_date, end_date, compare_prev_period?}
 * @returns TanStack Query result с данными ОПиУ
 */
export function useIncomeStatement(params) {
  return useQuery({
    queryKey: ['incomeStatement', params],
    queryFn: () => api.financial.incomeStatement(params),
    staleTime: getStaleTime(params),
    enabled: !!(params?.start_date && params?.end_date),
  })
}

// ──────────────────────────────────────────────
// Баланс — Balance Sheet
// ──────────────────────────────────────────────

/**
 * Хук для получения балансового отчёта.
 *
 * @param {Object} params - {period} — формат YYYY-MM
 * @returns TanStack Query result с данными баланса
 */
export function useBalanceSheet(params) {
  return useQuery({
    queryKey: ['balanceSheet', params],
    queryFn: () => api.financial.balanceSheet(params),
    staleTime: 60 * 60 * 1000,
    enabled: !!params?.period,
  })
}

// ──────────────────────────────────────────────
// CFO Dashboard
// ──────────────────────────────────────────────

/**
 * Хук для агрегированного CFO дашборда.
 *
 * @param {Object} params - {start_date, end_date}
 * @returns TanStack Query result с KPI и агрегированными данными
 */
export function useCFODashboard(params) {
  return useQuery({
    queryKey: ['cfoDashboard', params],
    queryFn: () => api.dashboards.cfo(params),
    staleTime: getStaleTime(params),
    enabled: !!(params?.start_date && params?.end_date),
  })
}
