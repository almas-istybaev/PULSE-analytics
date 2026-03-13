/**
 * @fileoverview KPICard — карточка ключевого показателя на дашборде.
 *
 * Поддерживает:
 * - Состояние загрузки (skeleton)
 * - Значение и изменение (delta)
 * - Иконку тренда (вверх/вниз/нейтральная)
 */

import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

/**
 * Карточка KPI-метрики в стиле Indigo Glass.
 *
 * @param {Object} props
 * @param {string} props.label - Название метрики
 * @param {string|number} props.value - Основное значение
 * @param {number} [props.change] - Изменение в % по сравнению с предыдущим периодом
 * @param {string} [props.subtitle] - Подпись под значением
 * @param {boolean} [props.isLoading] - Показывать skeleton
 * @param {React.ReactNode} [props.icon] - Иконка метрики
 * @param {'positive'|'negative'|'neutral'} [props.variant='neutral'] - Цветовой акцент
 */
export default function KPICard({
  label,
  value,
  change,
  subtitle,
  isLoading = false,
  icon,
  variant = 'neutral',
}) {
  const changeColor = change > 0
    ? 'oklch(65% 0.18 145)'  // зелёный
    : change < 0
    ? 'oklch(65% 0.2 25)'    // красный
    : 'var(--color-text-muted)'

  const TrendIcon = change > 0 ? TrendingUp : change < 0 ? TrendingDown : Minus

  return (
    <div
      className="kpi-card"
      style={{ position: 'relative', overflow: 'hidden' }}
    >
      {/* Метка */}
      <div
        style={{
          color: 'var(--color-text-muted)',
          fontSize: 11,
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
          marginBottom: 12,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        {label}
        {icon && (
          <span style={{ color: 'oklch(68% 0.15 274)', opacity: 0.7 }}>
            {icon}
          </span>
        )}
      </div>

      {isLoading ? (
        <>
          <div className="skeleton" style={{ height: 36, width: '70%', marginBottom: 8 }} />
          <div className="skeleton" style={{ height: 14, width: '50%' }} />
        </>
      ) : (
        <>
          {/* Значение */}
          <div
            style={{
              fontSize: 'clamp(1.25rem, 2vw, 1.75rem)',
              fontWeight: 800,
              color: 'var(--color-text-primary)',
              letterSpacing: '-0.02em',
              lineHeight: 1.2,
              marginBottom: 6,
            }}
          >
            {value}
          </div>

          {/* Изменение и подпись */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            {change !== undefined && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
                  fontSize: 12,
                  fontWeight: 600,
                  color: changeColor,
                }}
              >
                <TrendIcon size={12} strokeWidth={2.5} />
                {Math.abs(change).toFixed(1)}%
              </div>
            )}
            {subtitle && (
              <span style={{ color: 'var(--color-text-muted)', fontSize: 12 }}>
                {subtitle}
              </span>
            )}
          </div>
        </>
      )}
    </div>
  )
}
