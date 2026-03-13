---
name: tailwind-expert
description: Master of Tailwind CSS. Enforces utility-first styling, responsive design, and integration with the project's design system (UI/UX Pro Max).
---

# Tailwind CSS Expert

This skill equips the agent with advanced knowledge of Tailwind CSS and enforces its use throughout the project as the primary styling mechanism.

## Core Principles

> 📚 **Always cross-reference `../ui-ux-pro-max/resources/refactoring_ui.md`** before implementing layouts. Visual hierarchy, spacing, and color rules from *Refactoring UI* take precedence over aesthetic preferences.

1.  **Utility-First Styling**: Always prefer Tailwind utility classes over custom CSS in `styles.css`. Custom CSS should only be used for complex animations, highly specific component states that Tailwind cannot easily handle, or global root variables (`:root`).
2.  **Zero-Configuration Approach**: Rely on the default Tailwind design system (spacing, typography, colors) as much as possible before reaching for arbitrary values (e.g., `w-[325px]`). 
3.  **Arbitrary Values as Last Resort**: Use arbitrary values (e.g., `text-[14px]`, `bg-[#1a1a1a]`) *only* when the design requires a specific value not available in the default theme or the project's extended `tailwind.config.js`.

## Integration with UI/UX Pro Max

This skill works in tandem with `ui-ux-pro-max`. When designing components:

*   **Colors**: Use semantic color names defined in `tailwind.config.js` (e.g., `bg-primary`, `text-text-main`, `border-border`) rather than default Tailwind colors (e.g., `bg-blue-500`, `text-gray-900`) to ensure consistent theming and dark mode compatibility.
*   **Spacing**: Adhere to the generous spacing requirements of UI/UX Pro Max. Use larger padding (e.g., `p-6`, `p-8`) for cards, modals, and bottom sheets to create "breathing room".
*   **Typography**: Use explicit font weights (`font-medium`, `font-semibold`, `font-bold`) to create visual hierarchy instead of relying solely on text size.

## Responsive Design

1.  **Mobile-First**: Always design for mobile screens first using base utility classes without prefixes (e.g., `flex-col`, `w-full`, `p-4`).
2.  **Scaling Up**: Use responsive breakpoints (`sm:`, `md:`, `lg:`, `xl:`) to adjust the layout for larger screens (e.g., `md:flex-row`, `md:w-1/2`, `lg:p-8`).
3.  **Hidden Elements**: Use `hidden` and breakpoint prefixes (e.g., `md:block`, `lg:table-cell`) to manage element visibility across different device sizes (e.g., hiding less critical table columns on mobile).

## Interactive States

*   **Hover/Focus**: Always define `hover:`, `focus:`, and `active:` states for interactive elements (buttons, links, table rows) to provide immediate visual feedback.
*   **Transitions**: Apply `transition-colors`, `transition-all`, and duration utilities (e.g., `duration-200`) to make state changes smooth.
*   **Touch Interfaces**: Remember that hover states do not exist on mobile. Ensure critical actions are always visible or accessible via direct tap targets (e.g., bottom sheets) rather than relying on `group-hover`.

## Dark Mode (If Applicable)

*   Utilize the `dark:` prefix to define styles for dark mode if the project supports it (e.g., `bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100`). *Note: In this project, rely primarily on semantic CSS variables configured in `tailwind.config.js` for theming.*

## Component Patterns

*   **Flexbox/Grid**: Master `flex` and `grid` utilities for layout. Use `gap-` to manage spacing between child elements reliably.
*   **Centering**: Use `flex items-center justify-center` or `grid place-items-center` for robust vertical and horizontal centering.

## Workflow Execution

When asked to style a component or fix a visual issue:
1.  Analyze the HTML structure.
2.  Apply Tailwind utility classes directly to the elements.
3.  Remove unnecessary custom CSS from external stylesheets if it can be replaced by Tailwind classes.
4.  Verify responsiveness across mobile (`sm`), tablet (`md`), and desktop (`lg`) breakpoints.
