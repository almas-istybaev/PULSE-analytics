# Refactoring UI (Adam Wathan & Steve Schoger)
*Applied to our V2 React + Tailwind CSS Stack*

"Refactoring UI" teaches developers to design beautiful interfaces systematically — without relying on raw artistic talent. These are the most actionable rules for our project.

---

## 1. Design Process: Start Right

### Start with a Feature, Not a Layout
Never begin with the navigation shell or sidebar. Design the core of one feature first (e.g., the Inventory Card) because it gives you essential context about sizing, density, and content needs. The layout flows naturally *from* the content.

### Design in Grayscale First ("Hold the Color")
Start every new component without any color. Force yourself to build a strong hierarchy using only:
- Font weight (`font-semibold`, `font-bold`)
- Font size (`text-sm`, `text-xl`)
- Whitespace and spacing
- Opacity / subtle gray backgrounds
Only add color once the visual hierarchy feels solid. This prevents color from masking poor layout decisions.

### Limit Your Choices with Design Systems
Decision fatigue is the enemy of consistency. Define upfront:
- A **type scale**: e.g., `text-xs`, `text-sm`, `text-base`, `text-lg`, `text-xl`, `text-2xl`, `text-4xl`
- A **spacing scale**: only use multiples of 4px (aligned to Tailwind's default: `p-1`=4px, `p-2`=8px, `p-4`=16px, etc.)
- A **color palette** with 8-10 shades per color (Tailwind's built-in shades work perfectly)
Never invent arbitrary values if a system value is close enough.

---

## 2. Visual Hierarchy is Everything

### Not All Elements Are Equal
Every page should have **one** dominant element (the H1, the CTA button, the Hero). Supporting elements must be visually subdued relative to it. If everything is emphasized, nothing is.

### De-emphasize to Emphasize
Instead of making important elements louder (larger, bolder), make surrounding elements *quieter* (lighter text color, smaller font, more spacing). This is often more elegant.
- Use `text-muted-foreground` / `text-slate-500` for secondary labels.
- Use `font-normal` for labels, `font-semibold` for values.

### Action Hierarchy: Primary → Secondary → Tertiary
- **Primary actions:** Solid filled button (`bg-primary text-white`)
- **Secondary actions:** Outlined or ghost button (`border border-primary text-primary`)
- **Tertiary / destructive:** Text-only link, no border, or subdued color

### Labels Are a Last Resort
Avoid writing `Name: Almas` when you can write just `Almas` with a secondary size and style. Context makes labels obvious. Reserve explicit labels for forms and data-dense tables only.

---

## 3. Layout and Spacing

### Start with Too Much Whitespace
Begin by adding *more* space than feels comfortable (generous `p-6`, `p-8`, `gap-6`). Then gradually reduce it. Under-spacing is always the biggest amateur mistake.

### Establish Spacing Groups to Show Relationships
Elements that are related should be *closer* together. Unrelated sections should be *further* apart. Use `space-y-1` within a form field group, `space-y-6` between different form sections, and `mt-12` between major page sections.

### You Don't Need to Fill the Screen
Resist the urge to stretch inputs and cards to fill 100% of the screen width on desktop. A form with `max-w-md` that's centered on a desktop looks far more polished than the same form stretched to 1440px wide.

---

## 4. Typography Rules

### Establish a Type Scale and Never Deviate
Define a strict, non-linear scale. In Tailwind:
`text-xs` → `text-sm` → `text-base` → `text-lg` → `text-xl` → `text-2xl` → `text-3xl` → `text-4xl`

### Line Length (The 45-75 Character Rule)
Paragraphs must be between 45 and 75 characters per line for optimal readability. In Tailwind, use `max-w-prose` on paragraph containers.

### Line Height is Proportional
- Short lines (headlines): `leading-tight` or `leading-snug`
- Body text: `leading-normal` or `leading-relaxed`
- Long paragraphs: `leading-loose`

### Baseline Alignment
When combining elements of different font sizes in a row (e.g., an icon and text), align by `items-baseline`, not `items-center`.

---

## 5. Color Theory

### Use HSL, Not Hex
HSL (Hue, Saturation, Lightness) makes color manipulation intuitive. Tailwind's color system is built on this principle. To darken a color, decrease Lightness. To desaturate it, decrease Saturation. Never hardcode hex values.

### You Need More Palette Shades Than You Think
A proper palette needs ~9 shades per color (Tailwind provides 100–900). You'll use light shades for backgrounds, medium for borders, and dark for text.

### Use Color to Communicate, Not Just Decorate
- **Green / `text-emerald-600`**: Success states, positive inventory changes
- **Red / `text-red-600`**: Errors, negative stock alerts
- **Blue / `text-blue-600`**: Information, links
- **Amber / `text-amber-500`**: Warnings, low stock alerts
- **Gray**: Neutral, secondary content

### Avoid Pure Black for Text
Use `text-slate-900` or `text-zinc-900` instead of `text-black`. Pure black text on white feels harsh and dated.

---

## 6. Depth and Shadows

### Shadows Convey Elevation, Not Style
Use shadows to communicate that an element is above the page surface (modals, dropdowns, bottom sheets). Don't use aggressive shadows for decorative purposes.
- **Flat context (in-page cards):** `shadow-sm`
- **Elevated (modals, popovers):** `shadow-lg`
- **Absolute top (notifications):** `shadow-xl`

### Avoid Outline/Border-as-Shadow
Don't replace real drop shadows with thicker borders. Use Tailwind's `shadow-*` utilities with muted shadow colors.

---

## 7. Practical Anti-Patterns (Don'ts)

| ❌ Anti-Pattern | ✅ Better Way |
|---|---|
| Using `text-black` on dark backgrounds | Use `text-slate-50` or `text-zinc-100` |
| Centering wall-of-text paragraphs | Left-align body text; center only headlines |
| Using `border-radius: 0` (square corners) | Use `rounded-md` or `rounded-xl` — it feels friendlier |
| Giant walls of icons with no labels | Use icons + short text labels for clarity |
| Using color as the only status indicator | Combine color with an icon or text (accessibility) |
| All-caps body text for decoration | Full uppercase only for very short labels/badges |
