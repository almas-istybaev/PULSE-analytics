/**
 * @fileoverview ABCXYZPage — ABC/XYZ анализ товаров.
 *
 * Отображает:
 * - 3×3 матрицу сегментов с цветовым кодированием
 * - Таблицу товаров с фильтром по классу и сортировкой
 * - Badge-статистику по классам
 */

import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../services/apiClient'
import { formatCurrency, lastNMonthsParams } from '../../utils/dateUtils'

// Цвета 3×3 матрицы ABC/XYZ
const MATRIX_COLORS = {
  AX: { bg: 'oklch(65% 0.18 145)', label: 'Звёзды' },
  AY: { bg: 'oklch(62% 0.16 145)', label: 'Перспективные' },
  AZ: { bg: 'oklch(58% 0.14 145)', label: 'Проблемные' },
  BX: { bg: 'oklch(68% 0.15 274)', label: 'Хорошие' },
  BY: { bg: 'oklch(62% 0.13 274)', label: 'Средние' },
  BZ: { bg: 'oklch(58% 0.11 274)', label: 'Слабые' },
  CX: { bg: 'oklch(68% 0.15 55)', label: 'Плановые' },
  CY: { bg: 'oklch(62% 0.13 55)', label: 'Случайные' },
  CZ: { bg: 'oklch(65% 0.2 25)', label: 'Балласт' },
}

const ABC_CLASSES = ['A', 'B', 'C']
const XYZ_CLASSES = ['X', 'Y', 'Z']

function MatrixCell({ abc, xyz, count, selected, onSelect }) {
  const key = `${abc}${xyz}`
  const color = MATRIX_COLORS[key]
  const isSelected = selected === key

  return (
    <button
      onClick={() => onSelect(isSelected ? null : key)}
      style={{
        background: isSelected
          ? color.bg
          : `color-mix(in oklch, ${color.bg} 20%, transparent)`,
        border: `2px solid ${isSelected ? color.bg : 'var(--color-border-subtle)'}`,
        borderRadius: 8,
        padding: '8px 4px',
        cursor: 'pointer',
        transition: 'all 200ms ease',
        textAlign: 'center',
        minWidth: 80,
      }}
    >
      <div style={{ fontSize: 16, fontWeight: 800, color: isSelected ? '#fff' : 'var(--color-text-primary)' }}>
        {key}
      </div>
      <div style={{ fontSize: 11, color: isSelected ? 'rgba(255,255,255,0.8)' : 'var(--color-text-muted)', marginTop: 2 }}>
        {color.label}
      </div>
      <div style={{ fontSize: 13, fontWeight: 600, color: isSelected ? '#fff' : 'var(--color-text-secondary)', marginTop: 2 }}>
        {count ?? 0}
      </div>
    </button>
  )
}

/**
 * Страница ABC/XYZ анализа товаров.
 */
export default function ABCXYZPage() {
  const [params] = useState(lastNMonthsParams(12))
  const [selectedSegment, setSelectedSegment] = useState(null)
  const [search, setSearch] = useState('')

  const { data, isLoading, error } = useQuery({
    queryKey: ['abcXyz', params],
    queryFn: () => api.inventory.abcXyz(params),
    staleTime: 60 * 60 * 1000,
  })

  const segmentCounts = useMemo(() => {
    const counts = {}
    for (const item of data?.items || []) {
      const key = `${item.abc_class}${item.xyz_class}`
      counts[key] = (counts[key] || 0) + 1
    }
    return counts
  }, [data?.items])

  const filteredItems = useMemo(() => {
    let items = data?.items || []
    if (selectedSegment) {
      items = items.filter(
        (i) => `${i.abc_class}${i.xyz_class}` === selectedSegment
      )
    }
    if (search) {
      items = items.filter((i) => i.name.toLowerCase().includes(search.toLowerCase()))
    }
    return items
  }, [data?.items, selectedSegment, search])

  if (error) {
    return <div className="glass" style={{ padding: 24, textAlign: 'center', color: 'oklch(65% 0.2 25)' }}>⚠️ {error.message}</div>
  }

  return (
    <div className="animate-fade-in">
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 'clamp(1.25rem,3vw,1.75rem)', fontWeight: 800, color: 'var(--color-text-primary)', letterSpacing: '-0.02em', marginBottom: 4 }}>
          ABC/XYZ Анализ
        </h1>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 14 }}>
          Матрица 9 сегментов · {data?.items?.length || 0} товаров
        </p>
      </div>

      {/* 3×3 Matrix */}
      <div className="glass" style={{ padding: 20, marginBottom: 20 }}>
        <div style={{ color: 'var(--color-text-primary)', fontWeight: 700, marginBottom: 16 }}>
          Матрица сегментов {selectedSegment && `· выбран ${selectedSegment}`}
        </div>
        {isLoading ? (
          <div className="skeleton" style={{ height: 140 }} />
        ) : (
          <div>
            {/* Header row */}
            <div style={{ display: 'flex', gap: 8, paddingLeft: 36, marginBottom: 4 }}>
              {XYZ_CLASSES.map((xyz) => (
                <div key={xyz} style={{ flex: 1, textAlign: 'center', fontSize: 12, fontWeight: 700, color: 'var(--color-text-muted)' }}>
                  {xyz}
                </div>
              ))}
            </div>
            {/* Matrix rows */}
            {ABC_CLASSES.map((abc) => (
              <div key={abc} style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
                <div style={{ width: 28, textAlign: 'center', fontWeight: 700, color: 'var(--color-text-muted)', fontSize: 13 }}>
                  {abc}
                </div>
                {XYZ_CLASSES.map((xyz) => (
                  <div key={xyz} style={{ flex: 1 }}>
                    <MatrixCell
                      abc={abc}
                      xyz={xyz}
                      count={segmentCounts[`${abc}${xyz}`]}
                      selected={selectedSegment}
                      onSelect={setSelectedSegment}
                    />
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Поиск */}
      <div style={{ marginBottom: 16 }}>
        <input
          type="text"
          placeholder="Поиск товара..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            width: '100%',
            padding: '10px 14px',
            background: 'var(--color-bg-elevated)',
            border: '1px solid var(--color-border-subtle)',
            borderRadius: 8,
            color: 'var(--color-text-primary)',
            fontSize: 14,
            outline: 'none',
          }}
        />
      </div>

      {/* Таблица */}
      <div className="glass" style={{ padding: 24 }}>
        {isLoading ? (
          <>
            {[1,2,3,4,5].map((i) => (
              <div key={i} className="skeleton" style={{ height: 40, marginBottom: 8 }} />
            ))}
          </>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--color-border-subtle)' }}>
                {['Сегмент', 'Товар', 'Выручка', 'Кол-во прод.', 'CV%'].map((h) => (
                  <th key={h} style={{ padding: '8px 12px', textAlign: h === 'Сегмент' ? 'center' : 'left', color: 'var(--color-text-muted)', fontWeight: 600, fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredItems.slice(0, 50).map((item, idx) => {
                const segKey = `${item.abc_class}${item.xyz_class}`
                const cellColor = MATRIX_COLORS[segKey]?.bg || 'var(--color-text-muted)'
                return (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                    <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                      <span style={{ background: `color-mix(in oklch, ${cellColor} 25%, transparent)`, color: cellColor, fontWeight: 700, padding: '2px 8px', borderRadius: 4, fontSize: 12 }}>
                        {segKey}
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px', color: 'var(--color-text-primary)', maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {item.name}
                    </td>
                    <td style={{ padding: '10px 12px', color: 'var(--color-text-secondary)' }}>
                      {formatCurrency(item.revenue || 0, true)}
                    </td>
                    <td style={{ padding: '10px 12px', color: 'var(--color-text-secondary)' }}>
                      {item.quantity_sold?.toFixed(0) || 0}
                    </td>
                    <td style={{ padding: '10px 12px', color: 'var(--color-text-secondary)' }}>
                      {item.cv_pct?.toFixed(1) || '—'}%
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
        {filteredItems.length === 0 && !isLoading && (
          <p style={{ textAlign: 'center', color: 'var(--color-text-muted)', marginTop: 20 }}>
            Нет товаров для отображения
          </p>
        )}
      </div>
    </div>
  )
}
