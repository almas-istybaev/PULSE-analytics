/**
 * @fileoverview IncomeStatementPage — Отчёт о прибылях и убытках (ОПиУ).
 *
 * Отображает:
 * - Waterfall диаграмму: Выручка → COGS → GP → EBITDA → Чистая прибыль
 * - 4 KPI карточки с маржой
 * - Таблицу строк ОПиУ
 */

import { useState } from 'react'
import {
  BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, LabelList,
} from 'recharts'
import KPICard from '../../components/ui/KPICard'
import { useIncomeStatement } from '../../services/financial'
import { currentMonthParams, formatCurrency, formatPercent } from '../../utils/dateUtils'

const COLORS = {
  positive: 'oklch(65% 0.18 145)',
  negative: 'oklch(65% 0.2 25)',
  neutral: 'oklch(57% 0.21 274)',
  total: 'oklch(68% 0.15 274)',
}

function WaterfallTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const { label, value } = payload[0].payload
  return (
    <div className="glass" style={{ padding: '10px 14px' }}>
      <div style={{ color: 'var(--color-text-muted)', fontSize: 12, marginBottom: 4 }}>{label}</div>
      <div style={{ color: 'var(--color-text-primary)', fontWeight: 700, fontSize: 14 }}>
        {formatCurrency(value, true)}
      </div>
    </div>
  )
}

/**
 * Страница ОПиУ — Отчёт о прибылях и убытках.
 */
export default function IncomeStatementPage() {
  const [params] = useState(currentMonthParams())
  const { data, isLoading, error } = useIncomeStatement(params)

  if (error) {
    return (
      <div className="glass" style={{ padding: 24, textAlign: 'center' }}>
        <p style={{ color: 'oklch(65% 0.2 25)' }}>⚠️ {error.message}</p>
      </div>
    )
  }

  const s = data?.summary || {}

  // Данные для waterfall
  const waterfallData = [
    { label: 'Выручка', value: s.revenue || 0, fill: COLORS.positive },
    { label: 'COGS', value: -(s.cogs || 0), fill: COLORS.negative },
    { label: 'Валовая прибыль', value: s.gross_profit || 0, fill: COLORS.total },
    { label: 'Операционные расх.', value: -(s.opex || 0), fill: COLORS.negative },
    { label: 'EBITDA', value: s.ebitda || 0, fill: COLORS.total },
    { label: 'Амортизация', value: -(s.depreciation || 0), fill: COLORS.negative },
    { label: 'Проценты', value: -(s.interest || 0), fill: COLORS.negative },
    { label: 'Налог', value: -(s.tax || 0), fill: COLORS.negative },
    { label: 'Чистая прибыль', value: s.net_profit || 0, fill: COLORS.total },
  ]

  return (
    <div className="animate-fade-in">
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 'clamp(1.25rem,3vw,1.75rem)', fontWeight: 800, color: 'var(--color-text-primary)', letterSpacing: '-0.02em', marginBottom: 4 }}>
          Прибыли и убытки
        </h1>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 14 }}>
          ОПиУ · {params.start_date} — {params.end_date}
        </p>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 24 }}>
        <KPICard label="Выручка" value={formatCurrency(s.revenue || 0, true)} isLoading={isLoading} />
        <KPICard
          label="Валовая маржа"
          value={formatPercent(s.gross_margin_pct || 0)}
          subtitle={formatCurrency(s.gross_profit || 0, true)}
          isLoading={isLoading}
        />
        <KPICard
          label="EBITDA"
          value={formatCurrency(s.ebitda || 0, true)}
          subtitle={`маржа ${formatPercent(s.ebitda_margin_pct || 0)}`}
          isLoading={isLoading}
          change={s.ebitda_change_pct}
        />
        <KPICard
          label="Чистая прибыль"
          value={formatCurrency(s.net_profit || 0, true)}
          subtitle={`маржа ${formatPercent(s.net_margin_pct || 0)}`}
          isLoading={isLoading}
          change={s.net_profit_change_pct}
        />
      </div>

      {/* Waterfall Chart */}
      <div className="glass" style={{ padding: 24, marginBottom: 16 }}>
        <div style={{ color: 'var(--color-text-primary)', fontWeight: 700, marginBottom: 20, fontSize: 15 }}>
          Структура прибыли (тыс. ₸)
        </div>
        {isLoading ? (
          <div className="skeleton" style={{ height: 300 }} />
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={waterfallData} margin={{ top: 20, right: 4, left: 4, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" vertical={false} />
              <XAxis dataKey="label" tick={{ fill: 'var(--color-text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: 'var(--color-text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<WaterfallTooltip />} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {waterfallData.map((entry, index) => (
                  <Cell key={index} fill={entry.fill} fillOpacity={0.85} />
                ))}
                <LabelList
                  dataKey="value"
                  position="top"
                  style={{ fill: 'var(--color-text-muted)', fontSize: 10 }}
                  formatter={(v) => formatCurrency(Math.abs(v), true)}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Таблица строк ОПиУ */}
      {!isLoading && data?.lines && (
        <div className="glass" style={{ padding: 24 }}>
          <div style={{ color: 'var(--color-text-primary)', fontWeight: 700, marginBottom: 16 }}>Детализация ОПиУ</div>
          {data.lines.map((line, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex', justifyContent: 'space-between',
                padding: '10px 0',
                paddingLeft: line.indent ? line.indent * 16 : 0,
                borderBottom: '1px solid var(--color-border-subtle)',
                fontSize: line.is_total ? 14 : 13,
                fontWeight: line.is_total ? 700 : 400,
              }}
            >
              <span style={{ color: line.is_total ? 'var(--color-text-primary)' : 'var(--color-text-secondary)' }}>
                {line.label}
              </span>
              <span style={{
                color: (line.value || 0) >= 0 ? 'oklch(65% 0.18 145)' : 'oklch(65% 0.2 25)',
                fontWeight: 600,
              }}>
                {formatCurrency(line.value || 0, true)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
