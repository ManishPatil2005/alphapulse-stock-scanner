# Platform Design System & UI/UX Specification

This document details the user interface and user experience design for the platform.

## Design Philosophy
**Institutional-Grade Dark Terminal Aesthetic:** The platform embraces an information-dense yet scannable UI. Traders need to digest massive amounts of data instantly. The focus is on clarity, precision, and pedagogical value—teaching how markets operate without generating simplistic buy/sell signals.

## Color System
- **Backgrounds:**
  - Base: `#0a0e17` (Deep space dark)
  - Panels/Cards: `#111827`
  - Hover/Active: `#1f2937`
- **Text:**
  - Primary: `#f3f4f6`
  - Secondary: `#9ca3af`
- **Semantic/Accent Colors:**
  - Bullish: `#10b981` (Emerald)
  - Bearish: `#ef4444` (Red)
  - Neutral/Info: `#3b82f6` (Blue)
  - Institutional/Smart Money: `#8b5cf6` (Purple)

## Typography
- **Data/Prices:** `JetBrains Mono` or `Roboto Mono` for monospace tabular alignment.
- **UI/Headings/Body:** `Inter` or `San Francisco` for clean, modern sans-serif legibility.

## Component Library
Developed using Tailwind CSS + Headless UI / Radix Primitives:
- **Charts:** High-performance WebGL-based charting components.
- **Panels:** Resizable, dockable window frames.
- **Tables:** Virtualized data tables capable of rendering 10k+ rows at 60fps.
- **Badges:** Status indicators (e.g., Live, Delayed, Disconnected).
- **Buttons, Inputs, Dropdowns:** Minimalist forms with instant feedback.
- **Modals & Toasts:** Non-intrusive alerts and configuration dialogs.

## Layout System
- **Bloomberg Terminal Inspiration:** Highly modular interface.
- **Resizable Panels:** Grid-based drag-and-drop workspace manager.
- **Tab Groups:** Allow stacking multiple tools (e.g., Chart, Order Flow, Scanner) in a single quadrant.

## Chart Component Hierarchy
1. **Base Layer:** Candlesticks, Bar charts, or Line series.
2. **Overlays:** EMA, VWAP, Bollinger Bands (rendered on the main price axis).
3. **Sub-panels:** RSI, MACD, Volume, Cumulative Volume Delta (CVD) (rendered in separated lower panes).
4. **Annotations Layer:** FVG (Fair Value Gaps) zones, Order Blocks, Liquidity levels, and Market Profiles.

## Heatmap Design
- **Treemap View:** Visualizes sector and industry performance. Size = Market Cap, Color = % Change.
- **Gradients:** Smooth transitions from deep red (bearish extreme) to bright emerald (bullish extreme).
- **Interactivity:** Click-through to drill down from Sector → Industry → Specific Instrument.

## Scanner Builder UI
- **Drag-and-Drop:** Visual block builder for conditions (e.g., "RSI < 30").
- **Logic Connectors:** Easily link blocks with AND / OR / NOT logic.
- **Live Preview:** A side panel showing real-time matches as the scan logic is tweaked.

## Responsive Strategy
- **Primary:** Desktop-first (1920x1080) for full terminal experience.
- **Tablet (1024px):** Collapsible sidebars, simplified grids.
- **Mobile:** Companion mode only (monitoring active alerts, basic quotes, no complex strategy builder).

## Accessibility
- **Standards:** WCAG 2.1 AA compliant.
- **Navigation:** Full keyboard support (shortcuts for common actions like changing timeframes).
- **Screen Readers:** ARIA labels on dynamic data tables.

## Animation Principles
- **Performance:** 60fps chart updates and smooth DOM transitions.
- **Subtlety:** No jarring flashes. State changes (like price ticks) use slight color pulses rather than full-screen flashes.
