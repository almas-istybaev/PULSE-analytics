/**
 * @fileoverview CFODashboard — Сводный финансовый дашборд для CFO.
 *
 * Агрегирует данные из нескольких API в единый управленческий вид:
 * - 4 ключевых KPI (Выручка, GP, EBITDA, Net CF)
 * - Area Chart денежных потоков
 * - EBITDA Waterfall
 * - A/R vs A/P Aging summary
 */

import { useState } from 'react'
import {
  AreaChart, Area, BarChart, Bar, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { TrendingUp, DollarSign, BarChart3, Activity } from 'lucide-react'
import KPICard from '../../components/ui/KPICard'
import { useCFODashboard } from '../../services/financial'
import { currentMonthParams, formatCurrency, formatPercent } from '../../utils/dateUtils'

const MONTH_NAMES = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="glass" style={{ padding: '10px 14px', minWidth: 160 }}>
      <div style={{ color: 'var(--color-text-muted)', fontSize: 11, marginBottom: 6 }}>{label}</div>
      {payload.map((entry) => (
        <div key={entry.dataKey} style={{ fontSize: 13, color: entry.color, marginBottom: 2 }}>
          {entry.name}: <strong>{formatCurrency(entry.value, true)}</strong>
        </div>
      ))}
    </div>
  )
}

/**
 * Главный CFO дашборд — агрегированный финансовый вид.
 */
export default function CFODashboard() {
  const [params] = useState(currentMonthParams())
  const { data, isLoading, error } = useCFODashboard(params)

  const kpis = data?.kpis || {}
  const cfTrend = (data?.cf_trend || []).map((p) => ({
    name: MONTH_NAMES[new Date(p.period + '-01').getMonth()],
    'Выручка': Math.round((p.revenue || 0) / 1000),
    'Net CF': Math.round((p.net_cf || 0) / 1000),
  }))

  const ebitdaBridge = [
    { label: 'Выручка', value: kpis.revenue || 0, fill: 'oklch(65% 0.18 145)' },
    { label: 'COGS', value: -(kpis.cogs || 0), fill: 'oklch(65% 0.2 25)' },
    { label: 'OpEx', value: -(kpis.opex || 0), fill: 'oklch(65% 0.2 25)' },
    { label: 'EBITDA', value: kpis.ebitda || 0, fill: 'oklch(57% 0.21 274)' },
  ]

  if (error) {
    return (
      <div className="glass" style={{ padding: 24, textAlign: 'center' }}>
        <p style={{ color: 'oklch(65% 0.2 25)' }}>⚠️ {error.message}</p>
      </div>
    )
  }

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 'clamp(1.25rem,3vw,1.75rem)', fontWeight: 800, color: 'var(--color-text-primary)', letterSpacing: '-0.02em', marginBottom: 4 }}>
          CFO Дашборд
        </h1>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 14 }}>
          Управленческая сводка · {params.start_date} — {params.end_date}
        </p>
      </div>

      {/* KPI Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 24 }}>
        <KPICard label="Выручка" value={formatCurrency(kpis.revenue || 0, true)} isLoading={isLoading} icon={<TrendingUp size={14} />} change={kpis.revenue_change_pct} />
        <KPICard label="Валовая прибыль" value={formatCurrency(kpis.gross_profit || 0, true)} subtitle={formatPercent(kpis.gross_margin_pct || 0)} isLoading={isLoading} icon={<DollarSign size={14} />} />
        <KPICard label="EBITDA" value={formatCurrency(kpis.ebitda || 0, true)} subtitle={`маржа ${formatPercent(kpis.ebitda_margin_pct || 0)}`} isLoading={isLoading} icon={<BarChart3 size={14} />} change={kpis.ebitda_change_pct} />
        <KPICard label="Net Cash Flow" value={formatCurrency(kpis.net_cf || 0, true)} subtitle="за период" isLoading={isLoading} icon={<Activity size={14} />} change={kpis.net_cf_change_pct} />
      </div>

      {/* Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: 16, marginBottom: 16 }}>
        {/* CF Trend Area Chart */}
        <div className="glass" style={{ padding: 24 }}>
          <div style={{ color: 'var(--color-text-primary)', fontWeight: 700, marginBottom: 20, fontSize: 14 }}>
            Динамика (тыс. ₸)
          </div>
          {isLoading ? (
            <div className="skeleton" style={{ height: 220 }} />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={cfTrend} margin={{ top: 4, right: 4, left: 0, bottom: 4 }}>
                <defs>
                  <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="oklch(57% 0.21 274)" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="oklch(57% 0.21 274)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" />
                <XAxis dataKey="name" tick={{ fill: 'var(--color-text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: 'var(--color-text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="Выручка" stroke="oklch(57% 0.21 274)" fill="url(#revGrad)" strokeWidth={2} dot={false} />
                <Area type="monotone" dataKey="Net CF" stroke="oklch(65% 0.18 145)" fill="none" strokeWidth={2} dot={false} strokeDasharray="4 4" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* EBITDA Bridge */}
        <div className="glass" style={{ padding: 24 }}>
          <div style={{ color: 'var(--color-text-primary)', fontWeight: 700, marginBottom: 20, fontSize: 14 }}>
            EBITDA Bridge
          </div>
          {isLoading ? (
            <div className="skeleton" style={{ height: 220 }} />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={ebitdaBridge} margin={{ top: 4, right: 4, left: 0, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" vertical={false} />
                <XAxis dataKey="label" tick={{ fill: 'var(--color-text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: 'var(--color-text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip formatter={(v) => formatCurrency(Math.abs(v), true)} labelStyle={{ color: 'var(--color-text-primary)' }} contentStyle={{ background: 'var(--color-bg-elevated)', border: '1px solid var(--color-border-subtle)', borderRadius: 8 }} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {ebitdaBridge.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} fillOpacity={0.85} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* AR/AP Summary */}
      {!isLoading && data?.aging_summary && (
        <div className="glass" style={{ padding: 24 }}>
          <div style={{ color: 'var(--color-text-primary)', fontWeight: 700, marginBottom: 16, fontSize: 14 }}>
            Дебиторка vs Кредиторка
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            {[
              { label: 'Дебиторская (A/R)', total: data.aging_summary.ar_total, overdue: data.aging_summary.ar_overdue, color: 'oklch(57% 0.21 274)' },
              { label: 'Кредиторская (A/P)', total: data.aging_summary.ap_total, overdue: data.aging_summary.ap_overdue, color: 'oklch(65% 0.18 145)' },
            ].map((item) => (
              <div key={item.label} style={{ padding: 16, background: 'var(--color-bg-elevated)', borderRadius: 8 }}>
                <div style={{ color: 'var(--color-text-muted)', fontSize: 12, marginBottom: 8 }}>{item.label}</div>
                <div style={{ fontSize: 20, fontWeight: 800, color: item.color, marginBottom: 4 }}>
                  {formatCurrency(item.total || 0, true)}
                </div>
                <div style={{ fontSize: 12, color: 'oklch(65% 0.2 25)' }}>
                  Просрочено: {formatCurrency(item.overdue || 0, true)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
