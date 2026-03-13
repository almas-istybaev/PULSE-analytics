/**
 * @fileoverview CashFlowPage — Отчёт о движении денежных средств (ОДДС).
 *
 * Отображает:
 * - 4 KPI карточки: Операционные, Инвестиционные, Финансовые, Итого
 * - Area Chart динамики денежных потоков по месяцам (Recharts)
 * - Детализация по разделам МСФО
 */

import { useState } from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { DollarSign, ArrowUpCircle, ArrowDownCircle, TrendingUp } from 'lucide-react'
import KPICard from '../../components/ui/KPICard'
import { useCashFlow } from '../../services/financial'
import { lastNMonthsParams, formatCurrency, formatPercent } from '../../utils/dateUtils'

const MONTH_NAMES = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="glass" style={{ padding: '12px 16px', minWidth: 180 }}>
      <div style={{ color: 'var(--color-text-muted)', fontSize: 12, marginBottom: 8 }}>{label}</div>
      {payload.map((entry) => (
        <div key={entry.dataKey} style={{ display: 'flex', justifyContent: 'space-between', gap: 16, fontSize: 13, marginBottom: 4 }}>
          <span style={{ color: entry.color }}>{entry.name}</span>
          <span style={{ color: 'var(--color-text-primary)', fontWeight: 600 }}>
            {formatCurrency(entry.value, true)}
          </span>
        </div>
      ))}
    </div>
  )
}

/**
 * Страница ОДДС — Отчёт о движении денежных средств.
 * Подключается к GET /api/v1/financial/cash-flow.
 */
export default function CashFlowPage() {
  const [params] = useState(lastNMonthsParams(12))
  const { data, isLoading, error } = useCashFlow(params)

  if (error) {
    return (
      <div className="glass animate-fade-in" style={{ padding: 24, textAlign: 'center' }}>
        <p style={{ color: 'oklch(65% 0.2 25)' }}>⚠️ Ошибка загрузки: {error.message}</p>
      </div>
    )
  }

  const summary = data?.summary || {}
  const chartData = (data?.by_period || []).map((period) => ({
    name: MONTH_NAMES[new Date(period.period + '-01').getMonth()],
    Операционный: Math.round(period.operating_cf / 1000),
    Инвестиционный: Math.round(period.investing_cf / 1000),
    Финансовый: Math.round(period.financing_cf / 1000),
  }))

  return (
    <div className="animate-fade-in">
      {/* Заголовок */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 'clamp(1.25rem,3vw,1.75rem)', fontWeight: 800, color: 'var(--color-text-primary)', letterSpacing: '-0.02em', marginBottom: 4 }}>
          Движение денежных средств
        </h1>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 14 }}>
          ОДДС по МСФО · {params.start_date} — {params.end_date}
        </p>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 24 }}>
        <KPICard
          label="Операционный CF"
          value={formatCurrency(summary.total_operating_cf || 0, true)}
          subtitle="от основной деятельности"
          isLoading={isLoading}
          icon={<TrendingUp size={14} />}
        />
        <KPICard
          label="Инвестиционный CF"
          value={formatCurrency(summary.total_investing_cf || 0, true)}
          subtitle="CAPEX и инвестиции"
          isLoading={isLoading}
          icon={<ArrowDownCircle size={14} />}
        />
        <KPICard
          label="Финансовый CF"
          value={formatCurrency(summary.total_financing_cf || 0, true)}
          subtitle="кредиты и дивиденды"
          isLoading={isLoading}
          icon={<ArrowUpCircle size={14} />}
        />
        <KPICard
          label="Итого изменение"
          value={formatCurrency(summary.net_cash_flow || 0, true)}
          subtitle="чистое изменение ДС"
          isLoading={isLoading}
          icon={<DollarSign size={14} />}
          change={summary.change_pct}
        />
      </div>

      {/* Area Chart */}
      <div className="glass" style={{ padding: 24, marginBottom: 16 }}>
        <div style={{ color: 'var(--color-text-primary)', fontWeight: 700, marginBottom: 20, fontSize: 15 }}>
          Динамика денежных потоков (тыс. ₸)
        </div>
        {isLoading ? (
          <div className="skeleton" style={{ height: 280 }} />
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={chartData} margin={{ top: 4, right: 4, left: 4, bottom: 4 }}>
              <defs>
                <linearGradient id="opCF" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="oklch(57% 0.21 274)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="oklch(57% 0.21 274)" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="invCF" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="oklch(65% 0.18 145)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="oklch(65% 0.18 145)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" />
              <XAxis dataKey="name" tick={{ fill: 'var(--color-text-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: 'var(--color-text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12, color: 'var(--color-text-secondary)' }} />
              <Area type="monotone" dataKey="Операционный" stroke="oklch(57% 0.21 274)" fill="url(#opCF)" strokeWidth={2} dot={false} />
              <Area type="monotone" dataKey="Инвестиционный" stroke="oklch(65% 0.18 145)" fill="url(#invCF)" strokeWidth={2} dot={false} />
              <Area type="monotone" dataKey="Финансовый" stroke="oklch(68% 0.15 55)" fill="none" strokeWidth={2} dot={false} strokeDasharray="5 5" />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Детализация */}
      {!isLoading && data?.sections && (
        <div className="glass" style={{ padding: 24 }}>
          <div style={{ color: 'var(--color-text-primary)', fontWeight: 700, marginBottom: 16 }}>Разделы МСФО</div>
          {data.sections.map((section, idx) => (
            <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid var(--color-border-subtle)', fontSize: 14 }}>
              <span style={{ color: section.is_total ? 'var(--color-text-primary)' : 'var(--color-text-secondary)', fontWeight: section.is_total ? 700 : 400 }}>
                {section.label}
              </span>
              <span style={{ color: section.value >= 0 ? 'oklch(65% 0.18 145)' : 'oklch(65% 0.2 25)', fontWeight: 600 }}>
                {formatCurrency(section.value, true)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
