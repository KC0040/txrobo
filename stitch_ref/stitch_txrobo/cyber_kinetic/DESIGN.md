# Design System Strategy: Robotics & AI Editorial

## 1. Overview & Creative North Star
The Creative North Star for this design system is **"The Precision Architect."** 

In the world of high-end robotics and AI, the interface must mirror the product: precise, highly engineered, yet effortless in its execution. We are moving away from the "generic SaaS" look of rounded blue buttons and heavy borders. Instead, we are leaning into a **Tech-Forward Editorial** aesthetic. This means leveraging the stark, geometric qualities of Space Grotesk against a deep, multi-layered "Deep Space" canvas.

The system breaks the template look by prioritizing **Intentional Asymmetry**. We use vast amounts of negative space to create a "gallery" feel, where every piece of data and every robotic asset is treated like a work of art. By layering semi-transparent surfaces and utilizing tonal shifts rather than lines, we create a UI that feels "grown" rather than built.

---

## 2. Colors: Tonal Depth & The "No-Line" Rule
The palette is rooted in the original brand colors but expanded into a sophisticated Material-based spectrum that provides the depth required for a premium dark-mode experience.

### The Palette
- **Primary (`#b2c5ff`):** An energized, high-clarity blue used for critical interactive paths and highlights.
- **Surface & Background (`#0d131f`):** A deep, nocturnal navy that provides more soul than pure black.
- **On-Surface (`#dde2f4`):** A soft, cool white that reduces eye strain and feels more integrated than `#FFFFFF`.

### The "No-Line" Rule
To achieve a high-end feel, **1px solid borders for sectioning are strictly prohibited.** Do not use lines to separate the header from the hero, or cards from the background. 
- **Boundaries** must be defined by background color shifts. For example, a `surface-container-low` section sitting on a `surface` background.
- **The Glass & Gradient Rule:** Use Glassmorphism for floating elements. Combine `surface-variant` at 40% opacity with a `backdrop-blur` (12px–20px) to create a "frosted glass" effect.
- **Signature Textures:** For primary CTAs, use a subtle linear gradient from `primary` to `primary-container` at a 135-degree angle. This adds a "machined" metallic sheen that feels premium.

---

## 3. Typography: The Geometric Voice
We use a dual-font strategy to balance technical precision with human-centric readability.

- **Space Grotesk (Display, Headline, Label):** This is our "Precision" font. Its quirky terminals and geometric construction scream high-tech. Use `display-lg` (3.5rem) with tight letter-spacing (-0.02em) for hero statements to create an authoritative, editorial impact.
- **Inter (Title, Body):** Our "Utility" font. Inter is used for all long-form reading and functional UI text. Its neutral tone allows the Space Grotesk headlines to take center stage.

**Hierarchy as Identity:** 
We use extreme scale contrast. A small `label-md` in all-caps Space Grotesk paired with a massive `display-lg` creates a sophisticated, "blueprint-style" hierarchy that feels more like a technical manual for a luxury vehicle than a standard website.

---

## 4. Elevation & Depth: Tonal Layering
In this system, depth is not "shadows on white," it is "light within darkness."

### The Layering Principle
Depth is achieved by "stacking" surface tiers. 
1. **Base Layer:** `surface` (The foundation).
2. **Secondary Layer:** `surface-container-low` (Used for large layout blocks).
3. **Tertiary Layer:** `surface-container-highest` (Used for interactive cards or modals).

### Ambient Shadows
When an element must float (like a dropdown or a floating robot spec card), use an **Ambient Shadow**:
- **Color:** A tinted version of `on-surface` at 6% opacity.
- **Blur:** 40px to 60px.
- **Spread:** -10px.
This creates a soft "glow" or lift rather than a harsh shadow.

### The "Ghost Border" Fallback
If a boundary is required for accessibility, use a **Ghost Border**:
- **Token:** `outline-variant` at 15% opacity.
- **Style:** 1px solid. It should be barely perceptible, acting more as a light-catch on an edge than a container.

---

## 5. Components: The Machined Aesthetic

### Buttons
- **Primary:** `primary-container` background, `on-primary-container` text. Corner radius: `md` (0.375rem). No border.
- **Secondary (The Glass Button):** `surface-variant` at 20% opacity with a `backdrop-blur`. This makes the button feel like part of the interface’s "cockpit."
- **Tertiary:** Pure text in `primary` with an icon. No background.

### Cards
Forbid the use of divider lines. Separate content using the **Spacing Scale** (e.g., 24px vertical gap) or by nesting a `surface-container-highest` block inside a `surface-container-low` card.

### Input Fields
- **State:** Unfocused inputs should have no visible border, only a `surface-container-highest` background.
- **Focus:** Transition to a "Ghost Border" of `primary` at 40% and a subtle `surface-tint` inner glow.

### Chips (Robotic Status)
Use `secondary-container` for the background. For "Active" status, use a small 4px pulse dot of `primary` instead of a full background color change.

### Added Component: "The Data Monolith"
A specific component for this app: A vertical, high-contrast sidebar or information panel using `surface-container-lowest` to house technical specifications. It should feel like a "black box" of data separate from the main narrative flow.

---

## 6. Do’s and Don’ts

### Do:
- **Do** use `display-lg` typography that overlaps image containers slightly for an editorial look.
- **Do** use "Surface Nesting" to create hierarchy (e.g., a dark card on a slightly lighter section).
- **Do** leverage the `primary-fixed-dim` color for icons to ensure they feel "tech-forward" but not neon.

### Don't:
- **Don't** use 100% opaque borders. They break the immersion of the "Deep Space" aesthetic.
- **Don't** use standard "drop shadows" (Black #000000 at 25%). They look muddy on dark navy backgrounds.
- **Don't** crowd the layout. If you think there is enough white space, add 20% more. Premium design requires "room to breathe."
- **Don't** use dividers. If you feel the need to separate two items, use a 16px background color shift or a larger vertical gap.