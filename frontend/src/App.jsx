/**
 * @fileoverview Pulse App — Корневой компонент приложения.
 *
 * Реализует:
 * - «Indigo Glass» layout с mesh-gradient фоном
 * - PWA-ready навигацию: сайдбар (десктоп) + bottom nav (мобайл)
 * - Интеграцию TanStack Query для серверного состояния
 * - React Router для маршрутизации
 */

import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard,
  TrendingUp,
  Package,
  Users,
  Truck,
  BarChart3,
  PieChart,
  Settings,
  Zap,
} from 'lucide-react'

// ── Lazy-loaded Feature Pages ──────────────────────────────────────────────
const CFODashboard       = lazy(() => import('./features/dashboards/CFODashboard'))
const CashFlowPage       = lazy(() => import('./features/financial/CashFlowPage'))
const IncomeStatementPage = lazy(() => import('./features/financial/IncomeStatementPage'))
const ABCXYZPage         = lazy(() => import('./features/inventory/ABCXYZPage'))

// ── TanStack Query Client ──────────────────────────────────────────────────
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
})

// ── Navigation ─────────────────────────────────────────────────────────────
const NAV_ITEMS = [
  { path: '/',           icon: LayoutDashboard, label: 'Дашборд',    short: 'Главная' },
  { path: '/financial',  icon: TrendingUp,      label: 'Финансы',    short: 'Финансы' },
  { path: '/inventory',  icon: Package,         label: 'Запасы',     short: 'Запасы' },
  { path: '/analytics',  icon: Users,           label: 'Клиенты',    short: 'Клиенты' },
  { path: '/supply',     icon: Truck,           label: 'Поставки',   short: 'Логист.' },
  { path: '/reports',    icon: BarChart3,       label: 'Отчёты',     short: 'Отчёты' },
  { path: '/investor',   icon: PieChart,        label: 'Инвесторам', short: 'Invest' },
]

function Sidebar() {
  return (
    <nav className="sidebar" aria-label="Основная навигация">
      <div className="flex items-center gap-3 mb-8 px-2">
        <div
          className="w-9 h-9 rounded-xl flex items-center justify-center animate-pulse-glow"
          style={{ background: 'linear-gradient(135deg, oklch(57% 0.21 274), oklch(55% 0.25 295))' }}
        >
          <Zap size={18} color="white" strokeWidth={2.5} />
        </div>
        <div>
          <div style={{ color: 'var(--color-text-primary)', fontWeight: 700, fontSize: 16 }}>Pulse</div>
          <div style={{ color: 'var(--color-text-muted)', fontSize: 10, letterSpacing: '0.08em' }}>ANALYTICS</div>
        </div>
      </div>

      <div className="flex flex-col gap-1 flex-1">
        {NAV_ITEMS.map((item) => <SidebarLink key={item.path} item={item} />)}
      </div>

      <div style={{ borderTop: '1px solid var(--color-border-subtle)', paddingTop: 12, marginTop: 12 }}>
        <SidebarLink item={{ path: '/settings', icon: Settings, label: 'Настройки' }} />
      </div>
    </nav>
  )
}

function SidebarLink({ item }) {
  const { icon: Icon, path, label } = item
  return (
    <NavLink
      to={path}
      end={path === '/'}
      style={({ isActive }) => ({
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '9px 12px', borderRadius: 'var(--radius-md)',
        fontSize: 14, fontWeight: 500, textDecoration: 'none',
        transition: 'all 150ms ease',
        color: isActive ? 'oklch(68% 0.15 274)' : 'var(--color-text-secondary)',
        background: isActive ? 'color-mix(in oklch, oklch(57% 0.21 274) 12%, transparent)' : 'transparent',
        borderLeft: isActive ? '2px solid oklch(57% 0.21 274)' : '2px solid transparent',
      })}
    >
      <Icon size={16} />
      {label}
    </NavLink>
  )
}

function BottomNav() {
  const mobileItems = NAV_ITEMS.slice(0, 5)
  return (
    <nav className="bottom-nav" aria-label="Мобильная навигация">
      {mobileItems.map((item) => <BottomNavItem key={item.path} item={item} />)}
    </nav>
  )
}

function BottomNavItem({ item }) {
  const { icon: Icon, path, short } = item
  return (
    <NavLink
      to={path}
      end={path === '/'}
      className={({ isActive }) => `bottom-nav-item flex-1 ${isActive ? 'active' : ''}`}
    >
      {({ isActive }) => (
        <>
          <Icon size={20} strokeWidth={isActive ? 2.5 : 1.8} />
          <span>{short}</span>
          {isActive && (
            <motion.div
              layoutId="bottom-nav-indicator"
              style={{ position: 'absolute', top: 0, left: '50%', transform: 'translateX(-50%)', width: 24, height: 2, borderRadius: '0 0 4px 4px', background: 'oklch(68% 0.15 274)' }}
            />
          )}
        </>
      )}
    </NavLink>
  )
}

/** Skeleton fallback во время lazy-loading */
function PageSkeleton() {
  return (
    <div style={{ padding: 8 }}>
      <div className="skeleton" style={{ height: 36, width: '40%', marginBottom: 24 }} />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        {[1,2,3,4].map(i => <div key={i} className="skeleton" style={{ height: 100 }} />)}
      </div>
      <div className="skeleton" style={{ height: 280 }} />
    </div>
  )
}

/** Заглушка для страниц ещё не реализованных */
function ComingSoonPage({ title, icon: Icon, description }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-6 animate-fade-in" style={{ textAlign: 'center' }}>
      <div className="w-20 h-20 rounded-2xl glass-glow flex items-center justify-center glass animate-float">
        <Icon size={36} style={{ color: 'oklch(68% 0.15 274)' }} />
      </div>
      <div>
        <h1 style={{ fontSize: 'clamp(1.5rem, 4vw, 2rem)', fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 8 }}>{title}</h1>
        <p style={{ color: 'var(--color-text-secondary)', maxWidth: 420, lineHeight: 1.6 }}>{description}</p>
      </div>
      <div className="flex gap-2">
        <div className="badge badge-info">В разработке</div>
      </div>
    </div>
  )
}

function PageTransition({ children }) {
  const location = useLocation()
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  )
}

/**
 * Корневой компонент приложения Pulse Analytics.
 */
export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="mesh-bg" aria-hidden="true" />
        <Sidebar />
        <main className="main-content">
          <PageTransition>
            <Suspense fallback={<PageSkeleton />}>
              <Routes>
                {/* Dashboard */}
                <Route path="/" element={<CFODashboard />} />

                {/* Financial */}
                <Route path="/financial" element={<CashFlowPage />} />
                <Route path="/financial/cash-flow" element={<CashFlowPage />} />
                <Route path="/financial/income-statement" element={<IncomeStatementPage />} />

                {/* Inventory */}
                <Route path="/inventory" element={<ABCXYZPage />} />

                {/* Coming Soon */}
                <Route path="/analytics" element={<ComingSoonPage title="Клиентская аналитика" icon={Users} description="LTV/CAC расчёты, когортный анализ удержания, сегментация клиентов." />} />
                <Route path="/supply" element={<ComingSoonPage title="Управление поставками" icon={Truck} description="OTIF-метрики, анализ надёжности поставщиков, CCC." />} />
                <Route path="/reports" element={<ComingSoonPage title="Отчёты и документы" icon={BarChart3} description="Экспорт финансовых отчётов в Excel и PDF." />} />
                <Route path="/investor" element={<ComingSoonPage title="Инвесторские показатели" icon={PieChart} description="CAPEX-анализ, ROE (DuPont), дивидендная политика." />} />
                <Route path="/settings" element={<ComingSoonPage title="Настройки" icon={Settings} description="Подключение МойСклад API, управление пользователями и ролями." />} />
              </Routes>
            </Suspense>
          </PageTransition>
        </main>
        <BottomNav />
      </BrowserRouter>
    </QueryClientProvider>
  )
}
