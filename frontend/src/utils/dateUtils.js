/**
 * @fileoverview Утилиты для работы с датами в Pulse.
 */
import { format, startOfMonth, endOfMonth, subMonths, isAfter, parseISO } from 'date-fns'

/**
 * Форматирует дату в формат API (YYYY-MM-DD).
 * @param {Date} date
 * @returns {string}
 */
export const toApiDate = (date) => format(date, 'yyyy-MM-dd')

/**
 * Возвращает текущий месяц как {start_date, end_date}.
 * @returns {{ start_date: string, end_date: string }}
 */
export function currentMonthParams() {
  const now = new Date()
  return {
    start_date: toApiDate(startOfMonth(now)),
    end_date: toApiDate(endOfMonth(now)),
  }
}

/**
 * Возвращает последние N месяцев как {start_date, end_date}.
 * @param {number} months
 * @returns {{ start_date: string, end_date: string }}
 */
export function lastNMonthsParams(months = 12) {
  const now = new Date()
  return {
    start_date: toApiDate(startOfMonth(subMonths(now, months - 1))),
    end_date: toApiDate(endOfMonth(now)),
  }
}

/**
 * Определяет, является ли дата окончания текущим периодом.
 * Используется для определения staleTime кеша.
 * @param {string|undefined} endDate - ISO дата
 * @returns {boolean}
 */
export function isCurrentPeriod(endDate) {
  if (!endDate) return true
  try {
    const end = parseISO(endDate)
    return isAfter(end, startOfMonth(new Date()))
  } catch {
    return true
  }
}

/**
 * Форматирует число в валюту KZT.
 * @param {number} value
 * @param {boolean} [compact=false] - Компактный формат (1.2М)
 * @returns {string}
 */
export function formatCurrency(value, compact = false) {
  if (compact && Math.abs(value) >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)}М ₸`
  }
  if (compact && Math.abs(value) >= 1_000) {
    return `${(value / 1_000).toFixed(0)}К ₸`
  }
  return new Intl.NumberFormat('ru-KZ', {
    style: 'currency',
    currency: 'KZT',
    maximumFractionDigits: 0,
  }).format(value)
}

/**
 * Форматирует процент с знаком + для положительных значений.
 * @param {number} value
 * @returns {string}
 */
export function formatPercent(value) {
  const prefix = value > 0 ? '+' : ''
  return `${prefix}${value.toFixed(1)}%`
}
