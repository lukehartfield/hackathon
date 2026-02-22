# Remotion Demo Video Design

## Overview

2-minute (120s) animated hackathon demo video for ChargePilot, built with Remotion. Renders as 1920x1080 MP4 at 30fps (3600 frames). Lives in `video/` directory alongside `web/`.

## Style

- Animated walkthrough recreating the app UI as Remotion React components
- Text overlay captions at key moments (no voiceover needed)
- Simplified SVG map of Austin with real lat/lng data from GeoJSON
- Same dark theme as web app: `#04080f` bg, `#00d4ff` cyan accents, Syne/Outfit fonts

## Scene Breakdown

| # | Scene | Frames | Seconds | Description |
|---|-------|--------|---------|-------------|
| 1 | Title Card | 0–240 | 0–8s | Logo glow-in, tagline fade, "Austin, TX" |
| 2 | The Problem | 240–600 | 8–20s | "684 stations. Growing demand." SVG map, white dots scatter in |
| 3 | Overview | 600–1050 | 20–35s | Dots colorize by utilization. Stat cards animate in. Breakdown bar grows |
| 4 | Congestion | 1050–1500 | 35–50s | Zoom downtown, red pulses, heatmap gradient, top 5 list |
| 5 | Graph Optimization | 1500–1950 | 50–65s | GNN explainer text, network lines animate, clusters shade purple |
| 6 | Expansion Nodes | 1950–2400 | 65–80s | Blue dots pulse in one-by-one, connection lines, "Top 10 sites" |
| 7 | Run Optimization | 2400–2850 | 80–95s | Button click sim, spinner, AI narrative types in |
| 8 | Results | 2850–3300 | 95–110s | Coverage gauge 67%→89%, "+22% lift" counter |
| 9 | Closing | 3300–3600 | 110–120s | Tech stack, team name, hackathon branding, fade to black |

## Technical Architecture

```
video/
├── package.json              # Remotion + React deps
├── remotion.config.ts        # 30fps, 1920x1080, 3600 frames
├── src/
│   ├── Root.tsx              # <Composition> with <Series>
│   ├── Video.tsx             # Main composition orchestrating scenes
│   ├── scenes/
│   │   ├── TitleCard.tsx
│   │   ├── TheProblem.tsx
│   │   ├── Overview.tsx
│   │   ├── Congestion.tsx
│   │   ├── GraphOptimization.tsx
│   │   ├── ExpansionNodes.tsx
│   │   ├── RunOptimization.tsx
│   │   ├── Results.tsx
│   │   └── Closing.tsx
│   ├── components/
│   │   ├── AustinMap.tsx     # SVG map with projected station dots
│   │   ├── StationDot.tsx    # Animated circle for a station
│   │   ├── StatCard.tsx      # Animated stat display
│   │   ├── TextOverlay.tsx   # Caption text with fade-in
│   │   ├── CoverageGauge.tsx # Animated arc gauge
│   │   └── TypeWriter.tsx    # Character-by-character text reveal
│   ├── lib/
│   │   ├── data.ts           # Load + parse GeoJSON at build time
│   │   ├── projections.ts    # lat/lng → screen x/y conversion
│   │   └── theme.ts          # Colors, fonts, shared constants
│   └── index.ts              # Remotion entry point
```

## Data Flow

- GeoJSON files read from `../web/public/data/` at build/bundle time
- `projections.ts` converts lat/lng to pixel coordinates using a simple Mercator projection bounded to Austin area
- Station status colors derived from same logic as `web/lib/scoring.ts`

## Color System (matches web app)

| Token | Hex | Usage |
|-------|-----|-------|
| bg | `#04080f` | Video background |
| card | `#111d30` | Card backgrounds |
| border | `#1e3050` | Subtle edges |
| accent | `#00d4ff` | Logo, highlights, borders |
| overloaded | `#ff3860` | Red station dots |
| balanced | `#ffb020` | Yellow station dots |
| underutilized | `#00e68a` | Green station dots |
| suggested | `#4d8dff` | Blue expansion dots |
| cluster | `#8b5cf6` | Purple cluster shading |
| textPrimary | `#e8f0ff` | Main text |
| textSecondary | `#7b8ea8` | Muted text |

## Animation Patterns

- `spring()` for entrances (damping: 15, mass: 0.5)
- `interpolate()` for opacity fades and scale transforms
- Staggered delays for sequential dot/card reveals
- `<Series>` for scene sequencing within the composition
