# Component-Based Architecture in Frontend Development (React)
*Applied to our V2 React + Vite + Tailwind Stack*

---

## 1. Core Philosophy

A component is an **independent, reusable unit of UI and logic**. The component paradigm is the foundation of every modern React application. Every screen is a tree of components, from the smallest button to the entire page layout.

**Key benefits:**
- **Reusability:** Write once, use everywhere (e.g., `<Badge />`, `<Card />`, `<Spinner />`).
- **Isolation:** A component's internals are hidden from the outside world. It communicates only through `props` (input) and events/callbacks (output).
- **Testability:** A focused component with clear props is trivially unit-testable.
- **Maintainability:** Changing one component doesn't break unrelated ones.

---

## 2. Atomic Design Methodology

Atomic Design (Brad Frost) provides a systematic hierarchy for building UI systems. Think bottom-up.

```
Atoms → Molecules → Organisms → Templates → Pages
```

### Atoms (Lowest Level)
The smallest functional UI elements. Cannot be broken down further without losing meaning.
- **Examples:** `<Button />`, `<Input />`, `<Label />`, `<Badge />`, `<Spinner />`, `<Icon />`
- **Rules:**
  - Must be **stateless** (no internal state, pure props).
  - Must be **generic** (not domain-aware: "Button", not "InventoryActionButton").
  - Must accept standard HTML attributes via props spread (`...rest`).
  - Located in `client/src/components/ui/`.

### Molecules (Combining Atoms)
Groups of atoms forming a simple component with a **single responsibility**.
- **Examples:** `<SearchBar />` (Input + Icon + Button), `<FormField />` (Label + Input + Error), `<StockBadge />` (Badge + Icon)
- **Rules:**
  - May have minimal local UI state (e.g., `isFocused`).
  - Still **not domain-aware** — no direct API calls.
  - Located in `client/src/components/common/`.

### Organisms (Complex Sections)
Combinations of molecules and atoms forming a distinct, recognizable section of the UI. **Can be domain-aware.**
- **Examples:** `<InventoryCard />`, `<NavigationBar />`, `<FilterPanel />`, `<LoginForm />`
- **Rules:**
  - May receive domain data through props (e.g., `item: InventoryItem`).
  - **Still should NOT fetch data themselves.** Receive data from parent containers.
  - Located in `client/src/features/<featureName>/components/`.

### Templates (Page Layout Skeletons)
Page-level blueprints that define where organisms live. Contain no real data — only layout.
- **Examples:** `<DashboardLayout />`, `<AuthLayout />`
- Located in `client/src/layouts/`.

### Pages (Real Instances with Data)
The top-level components hooked into the router. They fetch data (via React Query) and pass it down to organisms.
- **Examples:** `<InventoryPage />`, `<LoginPage />`, `<AdminPage />`
- Located in `client/src/pages/` or `client/src/features/<featureName>/<FeatureName>Page.tsx`.

---

## 3. Smart vs. Dumb Components (Container/Presentational Pattern)

This is the **most important pattern** to enforce in our codebase.

### Dumb (Presentational) Components
- **Purpose:** Render UI based on props. Period.
- Know nothing about *where* data comes from.
- Are **pure** — same props always produce the same output.
- May have trivial local state (e.g., `isOpen` for a dropdown toggle).
- **Easy to reuse and test.**

```tsx
// ✅ Dumb Component
const InventoryCard = ({ item, onSelect }: { item: Item; onSelect: () => void }) => (
  <div onClick={onSelect} className="rounded-xl p-4 shadow-sm bg-white">
    <h3 className="font-semibold text-slate-900">{item.name}</h3>
    <span className="text-slate-500 text-sm">{item.stock} шт.</span>
  </div>
);
```

### Smart (Container) Components / Pages
- **Purpose:** Manage data fetching, business state, and orchestration.
- Use `React Query` (`useQuery`, `useMutation`) to fetch server data.
- Pass resolved data down as props to dumb presentational components.
- Know *how things work*, not necessarily *how they look*.

```tsx
// ✅ Smart Component (Page)
const InventoryPage = () => {
  const { data: items, isLoading } = useInventoryItems();
  
  if (isLoading) return <Spinner />;
  
  return (
    <div className="space-y-3">
      {items?.map(item => <InventoryCard key={item.id} item={item} onSelect={...} />)}
    </div>
  );
};
```

---

## 4. Custom Hooks: The Logic Extraction Layer

Custom Hooks are the **DRY solution** for shared component logic. They encapsulate state and side-effects that would otherwise be duplicated across multiple components.

**Create a Custom Hook when:**
- Two or more components need the same `useQuery` call.
- A component's `useEffect` logic grows complex.
- You need to share stateful logic (debouncing, pagination, local storage sync).

```tsx
// ✅ Good: Shared logic extracted into a hook
const useInventoryItems = (filters?: Filters) =>
  useQuery({ queryKey: ['inventory', filters], queryFn: () => fetchItems(filters) });

// ❌ Bad: Duplicating fetch logic in every component that needs items
useEffect(() => {
  fetch('/api/inventory').then(r => r.json()).then(setItems);
}, []);
```

---

## 5. Recommended Folder Structure

```
client/src/
├── components/
│   ├── ui/              # 🔵 Atoms — generic, reusable primitives
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   └── Badge.tsx
│   └── common/          # 🟡 Molecules — reusable domain-agnostic combos
│       ├── SearchBar.tsx
│       └── FormField.tsx
├── features/            # 🟢 Organisms + Feature-level logic
│   ├── inventory/
│   │   ├── components/  # InventoryCard, FilterPanel
│   │   ├── hooks/       # useInventoryItems, useInventoryFilters
│   │   └── InventoryPage.tsx
│   └── auth/
│       ├── components/  # LoginForm, PasswordInput
│       └── LoginPage.tsx
├── layouts/             # 🟣 Templates — page layout shells
│   ├── DashboardLayout.tsx
│   └── AuthLayout.tsx
├── lib/                 # helpers, API client, utils
└── hooks/               # Global custom hooks (useDebounce, useLocalStorage)
```

---

## 6. Anti-Patterns to Reject

| ❌ Anti-Pattern | ✅ Correct Solution |
|---|---|
| **"God Components"** — 500+ lines, do everything | Break into Atoms → Molecules → Organisms |
| Fetching data inside presentational components | Extract fetching to a Page or Custom Hook |
| Passing props through 5+ levels (Prop Drilling) | Use Context API or state manager (Zustand) |
| Using component state for server data | Use `React Query` — it IS the server cache |
| `import ../../../../../../components/Button` | Use path aliases (`@/components/ui/Button`) |
| Inline styles (`style={{ color: 'red' }}`) | Tailwind classes exclusively |

---

## 7. Component Design Checklist

Before writing a new component, ask:
- [ ] Does it have **one clear responsibility**? (SRP)
- [ ] Is it **pure** — does the same input always produce the same output?
- [ ] Is it **prop-typed** with clear, minimal interface?
- [ ] Is it at the **right atomic level** (Atom, Molecule, Organism)?
- [ ] Does it belong in the right **folder** (ui/, common/, features/)?
- [ ] Have I extracted **repeated logic** into a custom hook?
