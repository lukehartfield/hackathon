# Remotion Demo Video Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a 2-minute animated hackathon demo video for ChargePilot using Remotion, rendering the app's map, data, and UI as animated React components.

**Architecture:** Standalone Remotion project in `video/` reading real GeoJSON data from `../web/public/data/`. Nine scene components orchestrated via `<Series>`. SVG-based Austin map with Mercator-projected station dots.

**Tech Stack:** Remotion 4.x, React 18, TypeScript, SVG for map rendering

---

### Task 1: Scaffold Remotion Project

**Files:**
- Create: `video/package.json`
- Create: `video/tsconfig.json`
- Create: `video/remotion.config.ts`
- Create: `video/src/index.ts`
- Create: `video/src/Root.tsx`

**Step 1: Create `video/package.json`**

```json
{
  "name": "chargepilot-demo-video",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "studio": "remotion studio src/index.ts",
    "render": "remotion render src/index.ts DemoVideo out/demo.mp4",
    "build": "remotion render src/index.ts DemoVideo out/demo.mp4 --codec h264"
  },
  "dependencies": {
    "@remotion/cli": "4.0.261",
    "remotion": "4.0.261",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "typescript": "^5.5.0"
  }
}
```

**Step 2: Create `video/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "outDir": "./dist",
    "baseUrl": ".",
    "paths": { "@/*": ["src/*"] }
  },
  "include": ["src/**/*"]
}
```

**Step 3: Create `video/remotion.config.ts`**

```ts
import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
```

**Step 4: Create `video/src/index.ts`**

```ts
import { registerRoot } from "remotion";
import { Root } from "./Root";

registerRoot(Root);
```

**Step 5: Create `video/src/Root.tsx`**

```tsx
import { Composition } from "remotion";
import { DemoVideo } from "./Video";

export const Root: React.FC = () => {
  return (
    <Composition
      id="DemoVideo"
      component={DemoVideo}
      durationInFrames={3600}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
```

**Step 6: Create placeholder `video/src/Video.tsx`**

```tsx
import { AbsoluteFill } from "remotion";

export const DemoVideo: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#04080f" }}>
      <div style={{ color: "#e8f0ff", fontSize: 48, textAlign: "center", marginTop: 480 }}>
        ChargePilot Demo
      </div>
    </AbsoluteFill>
  );
};
```

**Step 7: Install dependencies**

Run: `cd video && npm install`

**Step 8: Verify Remotion Studio launches**

Run: `cd video && npx remotion studio src/index.ts`
Expected: Browser opens with Remotion Studio showing "ChargePilot Demo" text on dark background.

**Step 9: Commit**

```bash
git add video/
git commit -m "feat: scaffold Remotion project for demo video"
```

---

### Task 2: Theme + Data Loading Utilities

**Files:**
- Create: `video/src/lib/theme.ts`
- Create: `video/src/lib/data.ts`
- Create: `video/src/lib/projections.ts`

**Step 1: Create `video/src/lib/theme.ts`**

```ts
export const THEME = {
  bg: "#04080f",
  bgDeep: "#0a1628",
  card: "#111d30",
  border: "#1e3050",
  accent: "#00d4ff",
  overloaded: "#ff3860",
  balanced: "#ffb020",
  underutilized: "#00e68a",
  suggested: "#4d8dff",
  cluster: "#8b5cf6",
  textPrimary: "#e8f0ff",
  textSecondary: "#7b8ea8",
  textMuted: "#4a5d78",
} as const;

export const FONTS = {
  display: "Syne, sans-serif",
  body: "Outfit, sans-serif",
  mono: "'Azeret Mono', monospace",
} as const;

// Scene frame ranges (30fps, 3600 total)
export const SCENES = {
  title:       { from: 0,    duration: 240  },  // 0–8s
  problem:     { from: 240,  duration: 360  },  // 8–20s
  overview:    { from: 600,  duration: 450  },  // 20–35s
  congestion:  { from: 1050, duration: 450  },  // 35–50s
  graphOpt:    { from: 1500, duration: 450  },  // 50–65s
  expansion:   { from: 1950, duration: 450  },  // 65–80s
  runOpt:      { from: 2400, duration: 450  },  // 80–95s
  results:     { from: 2850, duration: 450  },  // 95–110s
  closing:     { from: 3300, duration: 300  },  // 110–120s
} as const;
```

**Step 2: Create `video/src/lib/projections.ts`**

Austin coordinate bounds (from real data):
- Lat: 30.1276 to 30.5223
- Lng: -97.9465 to -97.5540

```ts
// Austin bounding box with padding
const LAT_MIN = 30.10;
const LAT_MAX = 30.55;
const LNG_MIN = -97.97;
const LNG_MAX = -97.53;

// Map area within the 1920x1080 frame (left 70% like the web app)
const MAP_X = 0;
const MAP_Y = 0;
const MAP_W = 1344; // 70% of 1920
const MAP_H = 1080;

export function projectToScreen(lat: number, lng: number): { x: number; y: number } {
  const xNorm = (lng - LNG_MIN) / (LNG_MAX - LNG_MIN);
  const yNorm = 1 - (lat - LAT_MIN) / (LAT_MAX - LAT_MIN); // flip Y
  return {
    x: MAP_X + xNorm * MAP_W,
    y: MAP_Y + yNorm * MAP_H,
  };
}

export const MAP_BOUNDS = { MAP_X, MAP_Y, MAP_W, MAP_H };
```

**Step 3: Create `video/src/lib/data.ts`**

This reads the real GeoJSON and extracts what we need for the video.

```ts
import ocmRaw from "../../../web/public/data/ocm_austin.geojson";
import recsRaw from "../../../web/public/data/recommendations.geojson";
import clustersRaw from "../../../web/public/data/clusters.geojson";

export interface StationPoint {
  lat: number;
  lng: number;
  id: number;
  title: string;
  town: string;
  chargerCount: number;
  trafficScore: number;
  utilization: number;
  status: "overloaded" | "balanced" | "underutilized";
  optimizationScore: number;
}

export interface RecommendationPoint {
  lat: number;
  lng: number;
  rank: number;
  site_id: string;
  node_weight: number;
  marginal_gain: number;
}

export interface ClusterPoint {
  lat: number;
  lng: number;
  community_id: number;
  is_existing: boolean;
}

// Demand centers (same as web/lib/scoring.ts)
const DEMAND_CENTERS: [number, number, number][] = [
  [30.2672, -97.7431, 1.0],
  [30.2849, -97.7341, 0.85],
  [30.3600, -97.7200, 0.75],
  [30.2900, -97.6970, 0.70],
  [30.2200, -97.7900, 0.65],
  [30.2500, -97.7300, 0.60],
  [30.3100, -97.7500, 0.55],
  [30.2400, -97.7650, 0.50],
];

function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

function simulateTrafficScore(lat: number, lng: number): number {
  let score = 0;
  for (const [clat, clng, weight] of DEMAND_CENTERS) {
    score += weight * Math.exp(-haversineKm(lat, lng, clat, clng) / 2.6);
  }
  const seed = Math.sin(lat * 12.9898 + lng * 78.233) * 43758.5453;
  const noise = seed - Math.floor(seed);
  const jitter = (noise - 0.5) * 0.25;
  const normalized = 1 / (1 + Math.exp(-2.2 * (score - 0.7)));
  return 0.15 + Math.max(0, Math.min(1, normalized + jitter)) * 0.8;
}

function synthOptimizationScore(lat: number, lng: number, trafficScore: number, normStations: number): number {
  const seed = Math.sin(lat * 91.123 + lng * 47.77) * 15731.743;
  const noise = seed - Math.floor(seed);
  const base = Math.pow(noise, 0.35);
  const signal = 0.2 * trafficScore + 0.15 * normStations;
  return Math.max(0, Math.min(1, base * 0.75 + signal));
}

function deriveChargerCount(feature: any): number {
  const props = feature.properties;
  if (props.NumberOfPoints != null) return props.NumberOfPoints;
  if (props.Connections?.length) {
    return props.Connections.reduce((s: number, c: any) => s + (c.Quantity ?? 1), 0);
  }
  return 1;
}

export function loadStations(): StationPoint[] {
  const features = (ocmRaw as any).features;
  const maxChargerCount = Math.max(...features.map((f: any) => deriveChargerCount(f)));

  return features.map((f: any) => {
    const lat = f.geometry.coordinates[1];
    const lng = f.geometry.coordinates[0];
    const chargerCount = deriveChargerCount(f);
    const trafficScore = simulateTrafficScore(lat, lng);
    const normStations = maxChargerCount > 0 ? chargerCount / maxChargerCount : 0;
    const optimizationScore = synthOptimizationScore(lat, lng, trafficScore, normStations);
    const utilization = (trafficScore * 100) / chargerCount;
    const status: StationPoint["status"] =
      optimizationScore < 0.33 ? "overloaded" :
      optimizationScore < 0.66 ? "balanced" :
      "underutilized";

    return {
      lat, lng,
      id: f.properties.ID,
      title: f.properties.AddressInfo?.Title ?? "",
      town: f.properties.AddressInfo?.Town ?? "Austin",
      chargerCount,
      trafficScore,
      utilization,
      status,
      optimizationScore,
    };
  });
}

export function loadRecommendations(): RecommendationPoint[] {
  return (recsRaw as any).features
    .filter((f: any) => f.properties.rank != null)
    .sort((a: any, b: any) => a.properties.rank - b.properties.rank)
    .map((f: any) => ({
      lat: f.geometry.coordinates[1],
      lng: f.geometry.coordinates[0],
      rank: f.properties.rank,
      site_id: f.properties.site_id,
      node_weight: f.properties.node_weight,
      marginal_gain: f.properties.marginal_demand_gain,
    }));
}

export function loadClusters(): ClusterPoint[] {
  return (clustersRaw as any).features.map((f: any) => ({
    lat: f.geometry.coordinates[1],
    lng: f.geometry.coordinates[0],
    community_id: f.properties.community_id,
    is_existing: f.properties.is_existing,
  }));
}

// Pre-computed stats for display
export function computeStats(stations: StationPoint[]) {
  const totalChargers = stations.reduce((s, st) => s + st.chargerCount, 0);
  const avgUtil = stations.reduce((s, st) => s + st.utilization, 0) / stations.length;
  const overloaded = stations.filter((s) => s.status === "overloaded").length;
  const balanced = stations.filter((s) => s.status === "balanced").length;
  const underutilized = stations.filter((s) => s.status === "underutilized").length;

  return {
    stationCount: stations.length,
    totalChargers,
    avgUtilization: Math.round(avgUtil),
    overloaded,
    balanced,
    underutilized,
    overloadedPct: Math.round((overloaded / stations.length) * 100),
    balancedPct: Math.round((balanced / stations.length) * 100),
    underutilizedPct: Math.round((underutilized / stations.length) * 100),
  };
}
```

**Step 4: Commit**

```bash
git add video/src/lib/
git commit -m "feat: add theme, projections, and data loading for video"
```

---

### Task 3: Shared UI Components

**Files:**
- Create: `video/src/components/TextOverlay.tsx`
- Create: `video/src/components/StatCard.tsx`
- Create: `video/src/components/CoverageGauge.tsx`
- Create: `video/src/components/TypeWriter.tsx`
- Create: `video/src/components/AustinMap.tsx`
- Create: `video/src/components/StationDot.tsx`

**Step 1: Create `video/src/components/TextOverlay.tsx`**

Animated caption that fades in from bottom.

```tsx
import { interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { THEME, FONTS } from "../lib/theme";

export const TextOverlay: React.FC<{
  text: string;
  delay?: number;
  fontSize?: number;
  color?: string;
  style?: React.CSSProperties;
  subtitle?: boolean;
}> = ({ text, delay = 0, fontSize = 32, color = THEME.textPrimary, style, subtitle }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({ frame: frame - delay, fps, config: { damping: 15, mass: 0.5 } });
  const opacity = interpolate(progress, [0, 1], [0, 1]);
  const translateY = interpolate(progress, [0, 1], [30, 0]);

  return (
    <div
      style={{
        opacity,
        transform: `translateY(${translateY}px)`,
        color,
        fontSize,
        fontFamily: subtitle ? FONTS.body : FONTS.display,
        fontWeight: subtitle ? 400 : 700,
        letterSpacing: subtitle ? 0 : "0.02em",
        ...style,
      }}
    >
      {text}
    </div>
  );
};
```

**Step 2: Create `video/src/components/StatCard.tsx`**

Animated stat display that counts up.

```tsx
import { interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { THEME, FONTS } from "../lib/theme";

export const StatCard: React.FC<{
  label: string;
  value: number;
  suffix?: string;
  delay?: number;
  color?: string;
}> = ({ label, value, suffix = "", delay = 0, color = THEME.accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enter = spring({ frame: frame - delay, fps, config: { damping: 15, mass: 0.5 } });
  const opacity = interpolate(enter, [0, 1], [0, 1]);
  const scale = interpolate(enter, [0, 1], [0.8, 1]);
  const countTo = Math.round(interpolate(enter, [0, 1], [0, value]));

  return (
    <div
      style={{
        opacity,
        transform: `scale(${scale})`,
        backgroundColor: THEME.card,
        border: `1px solid ${THEME.border}`,
        borderRadius: 12,
        padding: "20px 28px",
        minWidth: 180,
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: 42, fontFamily: FONTS.display, fontWeight: 700, color }}>
        {countTo.toLocaleString()}{suffix}
      </div>
      <div style={{ fontSize: 16, fontFamily: FONTS.body, color: THEME.textSecondary, marginTop: 6 }}>
        {label}
      </div>
    </div>
  );
};
```

**Step 3: Create `video/src/components/CoverageGauge.tsx`**

Animated arc gauge for the results scene.

```tsx
import { interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { THEME, FONTS } from "../lib/theme";

export const CoverageGauge: React.FC<{
  from: number;
  to: number;
  delay?: number;
}> = ({ from, to, delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({ frame: frame - delay, fps, config: { damping: 20, mass: 1 } });
  const currentValue = interpolate(progress, [0, 1], [from, to]);
  const angle = interpolate(currentValue, [0, 100], [-180, 0]);

  const r = 120;
  const cx = 150;
  const cy = 150;

  // Arc path
  const endAngle = (angle * Math.PI) / 180;
  const startAngle = Math.PI; // -180 degrees
  const x1 = cx + r * Math.cos(startAngle);
  const y1 = cy + r * Math.sin(startAngle);
  const x2 = cx + r * Math.cos(Math.PI + endAngle);
  const y2 = cy + r * Math.sin(Math.PI + endAngle);
  const largeArc = currentValue > 50 ? 1 : 0;

  return (
    <div style={{ textAlign: "center" }}>
      <svg width={300} height={180} viewBox="0 0 300 180">
        {/* Background arc */}
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 1 1 ${cx + r} ${cy}`}
          fill="none"
          stroke={THEME.border}
          strokeWidth={16}
          strokeLinecap="round"
        />
        {/* Value arc */}
        <path
          d={`M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`}
          fill="none"
          stroke={currentValue > 80 ? THEME.underutilized : currentValue > 50 ? THEME.balanced : THEME.overloaded}
          strokeWidth={16}
          strokeLinecap="round"
        />
        {/* Value text */}
        <text
          x={cx}
          y={cy - 10}
          textAnchor="middle"
          fill={THEME.textPrimary}
          fontSize={48}
          fontFamily={FONTS.display}
          fontWeight={700}
        >
          {Math.round(currentValue)}%
        </text>
        <text
          x={cx}
          y={cy + 20}
          textAnchor="middle"
          fill={THEME.textSecondary}
          fontSize={16}
          fontFamily={FONTS.body}
        >
          Network Coverage
        </text>
      </svg>
    </div>
  );
};
```

**Step 4: Create `video/src/components/TypeWriter.tsx`**

Character-by-character text reveal.

```tsx
import { useCurrentFrame, useVideoConfig } from "remotion";
import { THEME, FONTS } from "../lib/theme";

export const TypeWriter: React.FC<{
  text: string;
  delay?: number;
  charsPerFrame?: number;
  fontSize?: number;
  style?: React.CSSProperties;
}> = ({ text, delay = 0, charsPerFrame = 0.8, fontSize = 20, style }) => {
  const frame = useCurrentFrame();
  const elapsed = Math.max(0, frame - delay);
  const charCount = Math.min(text.length, Math.floor(elapsed * charsPerFrame));

  return (
    <div
      style={{
        fontFamily: FONTS.body,
        fontSize,
        color: THEME.textPrimary,
        lineHeight: 1.6,
        whiteSpace: "pre-wrap",
        ...style,
      }}
    >
      {text.slice(0, charCount)}
      {charCount < text.length && (
        <span style={{ opacity: Math.sin(frame * 0.3) > 0 ? 1 : 0, color: THEME.accent }}>|</span>
      )}
    </div>
  );
};
```

**Step 5: Create `video/src/components/StationDot.tsx`**

Single animated station dot for SVG map.

```tsx
import { interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { THEME } from "../lib/theme";

const STATUS_COLORS = {
  overloaded: THEME.overloaded,
  balanced: THEME.balanced,
  underutilized: THEME.underutilized,
};

export const StationDot: React.FC<{
  x: number;
  y: number;
  status: "overloaded" | "balanced" | "underutilized";
  delay?: number;
  radius?: number;
  colorOverride?: string;
  pulse?: boolean;
}> = ({ x, y, status, delay = 0, radius = 3.5, colorOverride, pulse }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enter = spring({ frame: frame - delay, fps, config: { damping: 12, mass: 0.3 } });
  const scale = interpolate(enter, [0, 1], [0, 1]);
  const color = colorOverride ?? STATUS_COLORS[status];
  const pulseScale = pulse ? 1 + 0.3 * Math.sin(frame * 0.15) : 1;

  return (
    <circle
      cx={x}
      cy={y}
      r={radius * scale * pulseScale}
      fill={color}
      opacity={interpolate(enter, [0, 1], [0, 0.85])}
    />
  );
};
```

**Step 6: Create `video/src/components/AustinMap.tsx`**

SVG container for the Austin map area with grid lines and boundary.

```tsx
import { interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { THEME } from "../lib/theme";
import { MAP_BOUNDS } from "../lib/projections";

export const AustinMap: React.FC<{
  children: React.ReactNode;
  delay?: number;
  showGrid?: boolean;
}> = ({ children, delay = 0, showGrid = true }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { MAP_X, MAP_Y, MAP_W, MAP_H } = MAP_BOUNDS;

  const enter = spring({ frame: frame - delay, fps, config: { damping: 20, mass: 0.8 } });
  const opacity = interpolate(enter, [0, 1], [0, 1]);

  const gridLines = [];
  if (showGrid) {
    for (let i = 0; i <= 8; i++) {
      const x = MAP_X + (MAP_W / 8) * i;
      gridLines.push(
        <line key={`v${i}`} x1={x} y1={MAP_Y} x2={x} y2={MAP_H} stroke={THEME.border} strokeWidth={0.5} opacity={0.3} />
      );
    }
    for (let i = 0; i <= 6; i++) {
      const y = MAP_Y + (MAP_H / 6) * i;
      gridLines.push(
        <line key={`h${i}`} x1={MAP_X} y1={y} x2={MAP_W} y2={y} stroke={THEME.border} strokeWidth={0.5} opacity={0.3} />
      );
    }
  }

  return (
    <svg
      width={MAP_W}
      height={MAP_H}
      viewBox={`${MAP_X} ${MAP_Y} ${MAP_W} ${MAP_H}`}
      style={{ opacity, position: "absolute", left: 0, top: 0 }}
    >
      {/* Dark map background */}
      <rect x={MAP_X} y={MAP_Y} width={MAP_W} height={MAP_H} fill={THEME.bgDeep} rx={0} />
      {/* Grid */}
      {gridLines}
      {/* Border */}
      <rect x={MAP_X} y={MAP_Y} width={MAP_W} height={MAP_H} fill="none" stroke={THEME.border} strokeWidth={1} />
      {/* Station dots + overlays */}
      {children}
    </svg>
  );
};
```

**Step 7: Commit**

```bash
git add video/src/components/
git commit -m "feat: add shared video components (TextOverlay, StatCard, Gauge, Map, etc.)"
```

---

### Task 4: Scenes 1–3 (Title, Problem, Overview)

**Files:**
- Create: `video/src/scenes/TitleCard.tsx`
- Create: `video/src/scenes/TheProblem.tsx`
- Create: `video/src/scenes/Overview.tsx`

**Step 1: Create `video/src/scenes/TitleCard.tsx`**

```tsx
import { AbsoluteFill, interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { THEME, FONTS } from "../lib/theme";

export const TitleCard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const logoSpring = spring({ frame, fps, config: { damping: 12, mass: 0.5 } });
  const taglineSpring = spring({ frame: frame - 30, fps, config: { damping: 15, mass: 0.5 } });
  const subtitleSpring = spring({ frame: frame - 60, fps, config: { damping: 15, mass: 0.5 } });

  // Glow pulse
  const glowIntensity = 20 + 10 * Math.sin(frame * 0.08);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: THEME.bg,
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {/* Logo */}
      <div
        style={{
          opacity: interpolate(logoSpring, [0, 1], [0, 1]),
          transform: `scale(${interpolate(logoSpring, [0, 1], [0.5, 1])})`,
          fontSize: 96,
          fontFamily: FONTS.display,
          fontWeight: 800,
          color: THEME.textPrimary,
          textShadow: `0 0 ${glowIntensity}px ${THEME.accent}, 0 0 ${glowIntensity * 2}px ${THEME.accent}40`,
          letterSpacing: "0.04em",
        }}
      >
        ⚡ ChargePilot
      </div>

      {/* Tagline */}
      <div
        style={{
          opacity: interpolate(taglineSpring, [0, 1], [0, 1]),
          transform: `translateY(${interpolate(taglineSpring, [0, 1], [20, 0])}px)`,
          fontSize: 32,
          fontFamily: FONTS.body,
          color: THEME.textSecondary,
          marginTop: 24,
          letterSpacing: "0.08em",
        }}
      >
        AI-Powered EV Charging Network Optimizer
      </div>

      {/* Subtitle */}
      <div
        style={{
          opacity: interpolate(subtitleSpring, [0, 1], [0, 1]),
          fontSize: 24,
          fontFamily: FONTS.body,
          color: THEME.accent,
          marginTop: 16,
          letterSpacing: "0.12em",
          textTransform: "uppercase",
        }}
      >
        Austin, TX
      </div>

      {/* Decorative line */}
      <div
        style={{
          width: interpolate(logoSpring, [0, 1], [0, 400]),
          height: 2,
          backgroundColor: THEME.accent,
          marginTop: 40,
          opacity: 0.5,
          boxShadow: `0 0 10px ${THEME.accent}`,
        }}
      />
    </AbsoluteFill>
  );
};
```

**Step 2: Create `video/src/scenes/TheProblem.tsx`**

```tsx
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { THEME, FONTS } from "../lib/theme";
import { AustinMap } from "../components/AustinMap";
import { StationDot } from "../components/StationDot";
import { TextOverlay } from "../components/TextOverlay";
import { loadStations } from "../lib/data";
import { projectToScreen } from "../lib/projections";

const stations = loadStations();

export const TheProblem: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: THEME.bg }}>
      {/* Map with white dots scattering in */}
      <AustinMap delay={15}>
        {stations.map((s, i) => {
          const { x, y } = projectToScreen(s.lat, s.lng);
          const staggerDelay = 20 + Math.floor(i * 0.3);
          return (
            <StationDot
              key={s.id}
              x={x}
              y={y}
              status="balanced"
              delay={staggerDelay}
              colorOverride={THEME.textSecondary}
              radius={2.5}
            />
          );
        })}
      </AustinMap>

      {/* Right panel text */}
      <div
        style={{
          position: "absolute",
          right: 0,
          top: 0,
          width: 576,
          height: 1080,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "0 48px",
          backgroundColor: `${THEME.bg}e0`,
        }}
      >
        <TextOverlay
          text="684 Stations"
          fontSize={64}
          color={THEME.accent}
          delay={10}
        />
        <TextOverlay
          text="Growing Demand"
          fontSize={48}
          color={THEME.textPrimary}
          delay={40}
          style={{ marginTop: 16 }}
        />
        <TextOverlay
          text="Where should Austin expand its EV charging network?"
          fontSize={28}
          color={THEME.textSecondary}
          delay={80}
          subtitle
          style={{ marginTop: 32, lineHeight: "1.5" }}
        />
      </div>
    </AbsoluteFill>
  );
};
```

**Step 3: Create `video/src/scenes/Overview.tsx`**

```tsx
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { THEME, FONTS } from "../lib/theme";
import { AustinMap } from "../components/AustinMap";
import { StationDot } from "../components/StationDot";
import { StatCard } from "../components/StatCard";
import { TextOverlay } from "../components/TextOverlay";
import { loadStations, computeStats } from "../lib/data";
import { projectToScreen } from "../lib/projections";

const stations = loadStations();
const stats = computeStats(stations);

export const Overview: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Colorization transition: dots go from grey to their real colors
  const colorProgress = spring({ frame: frame - 20, fps, config: { damping: 20, mass: 1 } });

  return (
    <AbsoluteFill style={{ backgroundColor: THEME.bg }}>
      {/* Map with colorized dots */}
      <AustinMap delay={0}>
        {stations.map((s, i) => {
          const { x, y } = projectToScreen(s.lat, s.lng);
          return (
            <StationDot
              key={s.id}
              x={x}
              y={y}
              status={s.status}
              delay={0}
              radius={3}
            />
          );
        })}
      </AustinMap>

      {/* Right panel with stats */}
      <div
        style={{
          position: "absolute",
          right: 0,
          top: 0,
          width: 576,
          height: 1080,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "0 40px",
          backgroundColor: `${THEME.bg}e0`,
          gap: 24,
        }}
      >
        <TextOverlay text="Network Overview" fontSize={40} color={THEME.accent} delay={10} />

        <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginTop: 16 }}>
          <StatCard label="Stations" value={stats.stationCount} delay={30} />
          <StatCard label="Chargers" value={stats.totalChargers} delay={45} />
          <StatCard label="Avg Utilization" value={stats.avgUtilization} suffix="%" delay={60} color={THEME.balanced} />
        </div>

        {/* Utilization breakdown bar */}
        <div style={{ marginTop: 24 }}>
          <TextOverlay text="Utilization Breakdown" fontSize={20} color={THEME.textSecondary} delay={80} subtitle />
          <div style={{ display: "flex", height: 32, borderRadius: 8, overflow: "hidden", marginTop: 12 }}>
            <BarSegment color={THEME.overloaded} pct={stats.overloadedPct} label={`${stats.overloadedPct}% Overloaded`} delay={90} />
            <BarSegment color={THEME.balanced} pct={stats.balancedPct} label={`${stats.balancedPct}% Balanced`} delay={100} />
            <BarSegment color={THEME.underutilized} pct={stats.underutilizedPct} label={`${stats.underutilizedPct}% Under`} delay={110} />
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const BarSegment: React.FC<{
  color: string; pct: number; label: string; delay: number;
}> = ({ color, pct, label, delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const grow = spring({ frame: frame - delay, fps, config: { damping: 15, mass: 0.5 } });

  return (
    <div
      style={{
        width: `${pct * interpolate(grow, [0, 1], [0, 1])}%`,
        backgroundColor: color,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: 12,
        fontFamily: "Outfit, sans-serif",
        color: "#fff",
        fontWeight: 600,
        overflow: "hidden",
        whiteSpace: "nowrap",
      }}
    >
      {pct > 15 ? label : ""}
    </div>
  );
};
```

**Step 4: Commit**

```bash
git add video/src/scenes/TitleCard.tsx video/src/scenes/TheProblem.tsx video/src/scenes/Overview.tsx
git commit -m "feat: add title, problem, and overview scenes"
```

---

### Task 5: Scenes 4–6 (Congestion, Graph Optimization, Expansion)

**Files:**
- Create: `video/src/scenes/Congestion.tsx`
- Create: `video/src/scenes/GraphOptimization.tsx`
- Create: `video/src/scenes/ExpansionNodes.tsx`

**Step 1: Create `video/src/scenes/Congestion.tsx`**

```tsx
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { THEME, FONTS } from "../lib/theme";
import { AustinMap } from "../components/AustinMap";
import { StationDot } from "../components/StationDot";
import { TextOverlay } from "../components/TextOverlay";
import { loadStations } from "../lib/data";
import { projectToScreen } from "../lib/projections";

const stations = loadStations();
const congested = [...stations]
  .sort((a, b) => b.utilization - a.utilization)
  .slice(0, 15);

export const Congestion: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Zoom effect toward downtown
  const zoomProgress = spring({ frame, fps, config: { damping: 25, mass: 1.5 } });
  const scale = interpolate(zoomProgress, [0, 1], [1, 1.3]);
  const translateX = interpolate(zoomProgress, [0, 1], [0, -100]);
  const translateY = interpolate(zoomProgress, [0, 1], [0, -50]);

  // Heatmap gradient opacity
  const heatOpacity = interpolate(frame, [30, 120], [0, 0.4], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: THEME.bg }}>
      <div style={{ transform: `scale(${scale}) translate(${translateX}px, ${translateY}px)`, transformOrigin: "center center" }}>
        <AustinMap delay={0}>
          {/* Heatmap glow under overloaded stations */}
          {stations
            .filter((s) => s.status === "overloaded")
            .map((s, i) => {
              const { x, y } = projectToScreen(s.lat, s.lng);
              return (
                <circle
                  key={`heat-${s.id}`}
                  cx={x}
                  cy={y}
                  r={30}
                  fill={THEME.overloaded}
                  opacity={heatOpacity * 0.5}
                  filter="url(#blur)"
                />
              );
            })}
          {/* Blur filter for heatmap */}
          <defs>
            <filter id="blur">
              <feGaussianBlur stdDeviation="15" />
            </filter>
          </defs>
          {/* All station dots */}
          {stations.map((s) => {
            const { x, y } = projectToScreen(s.lat, s.lng);
            return (
              <StationDot
                key={s.id}
                x={x}
                y={y}
                status={s.status}
                radius={3}
                pulse={s.status === "overloaded"}
              />
            );
          })}
        </AustinMap>
      </div>

      {/* Right panel: top congested list */}
      <div
        style={{
          position: "absolute",
          right: 0,
          top: 0,
          width: 576,
          height: 1080,
          display: "flex",
          flexDirection: "column",
          padding: "60px 40px",
          backgroundColor: `${THEME.bg}e0`,
        }}
      >
        <TextOverlay text="Congestion Hotspots" fontSize={36} color={THEME.overloaded} delay={10} />
        <TextOverlay text="Critical areas where demand exceeds supply" fontSize={18} color={THEME.textSecondary} delay={30} subtitle style={{ marginTop: 8 }} />

        <div style={{ marginTop: 28, display: "flex", flexDirection: "column", gap: 8 }}>
          {congested.slice(0, 10).map((s, i) => (
            <CongestionRow key={s.id} rank={i + 1} name={s.title || s.town} utilization={Math.round(s.utilization)} delay={50 + i * 10} />
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const CongestionRow: React.FC<{
  rank: number; name: string; utilization: number; delay: number;
}> = ({ rank, name, utilization, delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame: frame - delay, fps, config: { damping: 15, mass: 0.4 } });

  return (
    <div
      style={{
        opacity: interpolate(enter, [0, 1], [0, 1]),
        transform: `translateX(${interpolate(enter, [0, 1], [40, 0])}px)`,
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: "8px 12px",
        backgroundColor: `${THEME.card}80`,
        borderRadius: 8,
        borderLeft: `3px solid ${THEME.overloaded}`,
      }}
    >
      <span style={{ fontFamily: FONTS.mono, fontSize: 14, color: THEME.textMuted, width: 24 }}>#{rank}</span>
      <span style={{ fontFamily: FONTS.body, fontSize: 14, color: THEME.textPrimary, flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
        {name}
      </span>
      <span style={{ fontFamily: FONTS.mono, fontSize: 14, color: THEME.overloaded, fontWeight: 700 }}>
        {utilization}%
      </span>
    </div>
  );
};
```

**Step 2: Create `video/src/scenes/GraphOptimization.tsx`**

```tsx
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { THEME, FONTS } from "../lib/theme";
import { AustinMap } from "../components/AustinMap";
import { StationDot } from "../components/StationDot";
import { TextOverlay } from "../components/TextOverlay";
import { loadStations, loadClusters } from "../lib/data";
import { projectToScreen } from "../lib/projections";

const stations = loadStations();
const clusters = loadClusters();

// Group clusters by community for shading
const communityGroups = new Map<number, { x: number; y: number }[]>();
clusters.forEach((c) => {
  const { x, y } = projectToScreen(c.lat, c.lng);
  if (!communityGroups.has(c.community_id)) communityGroups.set(c.community_id, []);
  communityGroups.get(c.community_id)!.push({ x, y });
});

// Compute centroids per community
const communityCentroids = Array.from(communityGroups.entries()).map(([id, points]) => ({
  id,
  cx: points.reduce((s, p) => s + p.x, 0) / points.length,
  cy: points.reduce((s, p) => s + p.y, 0) / points.length,
  count: points.length,
}));

export const GraphOptimization: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const clusterOpacity = interpolate(frame, [30, 120], [0, 0.25], { extrapolateRight: "clamp" });
  const lineProgress = interpolate(frame, [60, 200], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: THEME.bg }}>
      <AustinMap delay={0}>
        {/* Cluster shading */}
        {communityCentroids.map((c) => (
          <circle
            key={`cluster-${c.id}`}
            cx={c.cx}
            cy={c.cy}
            r={Math.max(40, c.count * 4)}
            fill={THEME.cluster}
            opacity={clusterOpacity}
          />
        ))}

        {/* Network lines between nearby stations */}
        {stations.slice(0, 100).map((s, i) => {
          if (i === 0) return null;
          const prev = stations[i - 1];
          const p1 = projectToScreen(s.lat, s.lng);
          const p2 = projectToScreen(prev.lat, prev.lng);
          const dist = Math.hypot(p1.x - p2.x, p1.y - p2.y);
          if (dist > 80) return null;
          const lineDelay = 60 + i * 0.5;
          const lineOpacity = interpolate(frame - lineDelay, [0, 30], [0, 0.15], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <line
              key={`line-${i}`}
              x1={p1.x}
              y1={p1.y}
              x2={p2.x}
              y2={p2.y}
              stroke={THEME.accent}
              strokeWidth={0.8}
              opacity={lineOpacity}
            />
          );
        })}

        {/* Station dots */}
        {stations.map((s) => {
          const { x, y } = projectToScreen(s.lat, s.lng);
          return <StationDot key={s.id} x={x} y={y} status={s.status} radius={2.5} />;
        })}
      </AustinMap>

      {/* Right panel */}
      <div
        style={{
          position: "absolute", right: 0, top: 0, width: 576, height: 1080,
          display: "flex", flexDirection: "column", justifyContent: "center",
          padding: "0 48px", backgroundColor: `${THEME.bg}e0`,
        }}
      >
        <TextOverlay text="Graph Optimization" fontSize={40} color={THEME.cluster} delay={10} />
        <TextOverlay text="Community Detection + GNN" fontSize={24} color={THEME.textSecondary} delay={40} subtitle style={{ marginTop: 8 }} />

        <div style={{ marginTop: 40, display: "flex", flexDirection: "column", gap: 20 }}>
          <MethodCard icon="🔗" title="Graph Neural Network" desc="Models station connectivity and demand propagation across the network" delay={70} />
          <MethodCard icon="🏘️" title="Community Detection" desc="Identifies 17 distinct service communities in Austin's charging network" delay={100} />
          <MethodCard icon="📊" title="Coverage Optimization" desc="Maximizes marginal coverage gain per new station placement" delay={130} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

const MethodCard: React.FC<{
  icon: string; title: string; desc: string; delay: number;
}> = ({ icon, title, desc, delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame: frame - delay, fps, config: { damping: 15, mass: 0.5 } });

  return (
    <div
      style={{
        opacity: interpolate(enter, [0, 1], [0, 1]),
        transform: `translateY(${interpolate(enter, [0, 1], [20, 0])}px)`,
        backgroundColor: THEME.card,
        border: `1px solid ${THEME.border}`,
        borderRadius: 12,
        padding: "20px 24px",
        display: "flex",
        gap: 16,
        alignItems: "flex-start",
      }}
    >
      <span style={{ fontSize: 28 }}>{icon}</span>
      <div>
        <div style={{ fontSize: 18, fontFamily: FONTS.display, color: THEME.textPrimary, fontWeight: 600 }}>{title}</div>
        <div style={{ fontSize: 14, fontFamily: FONTS.body, color: THEME.textSecondary, marginTop: 4, lineHeight: 1.4 }}>{desc}</div>
      </div>
    </div>
  );
};
```

**Step 3: Create `video/src/scenes/ExpansionNodes.tsx`**

```tsx
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { THEME, FONTS } from "../lib/theme";
import { AustinMap } from "../components/AustinMap";
import { StationDot } from "../components/StationDot";
import { TextOverlay } from "../components/TextOverlay";
import { loadStations, loadRecommendations } from "../lib/data";
import { projectToScreen } from "../lib/projections";

const stations = loadStations();
const recommendations = loadRecommendations().slice(0, 10);

export const ExpansionNodes: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: THEME.bg }}>
      <AustinMap delay={0}>
        {/* Existing stations (dimmed) */}
        {stations.map((s) => {
          const { x, y } = projectToScreen(s.lat, s.lng);
          return <StationDot key={s.id} x={x} y={y} status={s.status} radius={2} />;
        })}

        {/* Connection lines from recommendations to nearest stations */}
        {recommendations.map((r, i) => {
          const rPos = projectToScreen(r.lat, r.lng);
          // Find 3 nearest stations for visual effect
          const nearest = stations
            .map((s) => ({ s, dist: Math.hypot(projectToScreen(s.lat, s.lng).x - rPos.x, projectToScreen(s.lat, s.lng).y - rPos.y) }))
            .sort((a, b) => a.dist - b.dist)
            .slice(0, 3);

          const lineDelay = 40 + i * 25;
          const lineOpacity = interpolate(frame - lineDelay, [0, 30], [0, 0.3], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

          return nearest.map((n, j) => {
            const sPos = projectToScreen(n.s.lat, n.s.lng);
            return (
              <line
                key={`conn-${i}-${j}`}
                x1={rPos.x}
                y1={rPos.y}
                x2={sPos.x}
                y2={sPos.y}
                stroke={THEME.suggested}
                strokeWidth={1}
                opacity={lineOpacity}
                strokeDasharray="4 4"
              />
            );
          });
        })}

        {/* Blue recommendation dots - appear one by one */}
        {recommendations.map((r, i) => {
          const { x, y } = projectToScreen(r.lat, r.lng);
          return (
            <StationDot
              key={`rec-${r.site_id}`}
              x={x}
              y={y}
              status="balanced"
              colorOverride={THEME.suggested}
              delay={30 + i * 25}
              radius={6}
              pulse
            />
          );
        })}
      </AustinMap>

      {/* Right panel: recommendation list */}
      <div
        style={{
          position: "absolute", right: 0, top: 0, width: 576, height: 1080,
          display: "flex", flexDirection: "column", padding: "60px 40px",
          backgroundColor: `${THEME.bg}e0`,
        }}
      >
        <TextOverlay text="Expansion Sites" fontSize={40} color={THEME.suggested} delay={10} />
        <TextOverlay text="Top 10 optimal new station locations" fontSize={18} color={THEME.textSecondary} delay={30} subtitle style={{ marginTop: 8 }} />

        <div style={{ marginTop: 24, display: "flex", flexDirection: "column", gap: 8 }}>
          {recommendations.map((r, i) => (
            <NodeRow key={r.site_id} rank={r.rank} siteId={r.site_id} weight={r.node_weight} gain={r.marginal_gain} delay={40 + i * 20} />
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const NodeRow: React.FC<{
  rank: number; siteId: string; weight: number; gain: number; delay: number;
}> = ({ rank, siteId, weight, gain, delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame: frame - delay, fps, config: { damping: 15, mass: 0.4 } });

  return (
    <div
      style={{
        opacity: interpolate(enter, [0, 1], [0, 1]),
        transform: `translateX(${interpolate(enter, [0, 1], [40, 0])}px)`,
        display: "flex", alignItems: "center", gap: 12,
        padding: "8px 12px", backgroundColor: `${THEME.card}80`,
        borderRadius: 8, borderLeft: `3px solid ${THEME.suggested}`,
      }}
    >
      <span style={{ fontFamily: FONTS.mono, fontSize: 14, color: THEME.suggested, width: 24, fontWeight: 700 }}>#{rank}</span>
      <span style={{ fontFamily: FONTS.body, fontSize: 14, color: THEME.textPrimary, flex: 1 }}>{siteId}</span>
      <span style={{ fontFamily: FONTS.mono, fontSize: 12, color: THEME.textSecondary }}>+{gain.toFixed(1)}</span>
      {/* Weight bar */}
      <div style={{ width: 60, height: 6, backgroundColor: THEME.border, borderRadius: 3 }}>
        <div style={{ width: `${weight * 100}%`, height: "100%", backgroundColor: THEME.suggested, borderRadius: 3 }} />
      </div>
    </div>
  );
};
```

**Step 4: Commit**

```bash
git add video/src/scenes/Congestion.tsx video/src/scenes/GraphOptimization.tsx video/src/scenes/ExpansionNodes.tsx
git commit -m "feat: add congestion, graph optimization, and expansion scenes"
```

---

### Task 6: Scenes 7–9 (Run Optimization, Results, Closing)

**Files:**
- Create: `video/src/scenes/RunOptimization.tsx`
- Create: `video/src/scenes/Results.tsx`
- Create: `video/src/scenes/Closing.tsx`

**Step 1: Create `video/src/scenes/RunOptimization.tsx`**

```tsx
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { THEME, FONTS } from "../lib/theme";
import { TypeWriter } from "../components/TypeWriter";
import { TextOverlay } from "../components/TextOverlay";

const AI_NARRATIVE = `Austin's EV charging network shows significant pressure across downtown and university corridors, with 31% of stations operating above 150% capacity during peak hours.

Our graph-based analysis identifies 10 high-impact expansion sites concentrated in East Riverside, Mueller, and South Congress — areas where demand growth outpaces current infrastructure by 2.4x.

Deploying these recommended stations would lift network coverage from 67% to 89%, reducing average wait times by an estimated 12 minutes during peak demand windows.`;

export const RunOptimization: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Button click at frame 0, spinner from 0-90, then narrative
  const buttonPress = spring({ frame, fps, config: { damping: 10, mass: 0.3 } });
  const spinnerVisible = frame >= 10 && frame < 90;
  const narrativeStart = 100;

  return (
    <AbsoluteFill style={{ backgroundColor: THEME.bg }}>
      {/* Simulated app panel (centered) */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          transform: "translate(-50%, -50%)",
          width: 800,
          backgroundColor: THEME.card,
          border: `1px solid ${THEME.border}`,
          borderRadius: 16,
          padding: 48,
          boxShadow: `0 0 60px ${THEME.accent}15`,
        }}
      >
        {/* Button */}
        <div
          style={{
            backgroundColor: frame < 10 ? THEME.accent : `${THEME.accent}40`,
            borderRadius: 12,
            padding: "16px 32px",
            textAlign: "center",
            fontFamily: FONTS.display,
            fontSize: 20,
            color: THEME.bg,
            fontWeight: 700,
            transform: `scale(${frame < 10 ? interpolate(buttonPress, [0, 1], [1, 0.95]) : 0.95})`,
            marginBottom: 32,
          }}
        >
          {spinnerVisible ? "⏳ Computing..." : frame < 10 ? "Run Optimization Demo" : "✓ Analysis Complete"}
        </div>

        {/* Spinner dots */}
        {spinnerVisible && (
          <div style={{ display: "flex", justifyContent: "center", gap: 8, marginBottom: 24 }}>
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: "50%",
                  backgroundColor: THEME.accent,
                  opacity: Math.sin((frame - 10) * 0.15 + i * 2) > 0 ? 1 : 0.3,
                }}
              />
            ))}
          </div>
        )}

        {/* AI Narrative */}
        {frame >= narrativeStart && (
          <div>
            <TextOverlay text="AI Insights" fontSize={24} color={THEME.accent} delay={narrativeStart} />
            <div style={{ marginTop: 16 }}>
              <TypeWriter text={AI_NARRATIVE} delay={narrativeStart + 15} charsPerFrame={1.2} fontSize={17} />
            </div>
          </div>
        )}
      </div>

      {/* Powered by badge */}
      <div
        style={{
          position: "absolute",
          bottom: 40,
          left: "50%",
          transform: "translateX(-50%)",
          opacity: interpolate(frame, [narrativeStart, narrativeStart + 30], [0, 0.6], { extrapolateRight: "clamp" }),
          fontFamily: FONTS.mono,
          fontSize: 14,
          color: THEME.textMuted,
        }}
      >
        Powered by Groq · LLaMA 3.3 70B
      </div>
    </AbsoluteFill>
  );
};
```

**Step 2: Create `video/src/scenes/Results.tsx`**

```tsx
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { THEME, FONTS } from "../lib/theme";
import { CoverageGauge } from "../components/CoverageGauge";
import { StatCard } from "../components/StatCard";
import { TextOverlay } from "../components/TextOverlay";

export const Results: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const liftSpring = spring({ frame: frame - 120, fps, config: { damping: 12, mass: 0.5 } });
  const liftOpacity = interpolate(liftSpring, [0, 1], [0, 1]);
  const liftScale = interpolate(liftSpring, [0, 1], [0.5, 1]);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: THEME.bg,
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div style={{ display: "flex", gap: 80, alignItems: "center" }}>
        {/* Before gauge */}
        <div style={{ textAlign: "center" }}>
          <TextOverlay text="Current" fontSize={24} color={THEME.textSecondary} delay={10} />
          <div style={{ marginTop: 16 }}>
            <CoverageGauge from={0} to={67} delay={20} />
          </div>
        </div>

        {/* Arrow + lift */}
        <div
          style={{
            opacity: liftOpacity,
            transform: `scale(${liftScale})`,
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: 72, fontFamily: FONTS.display, fontWeight: 800, color: THEME.underutilized }}>
            +22%
          </div>
          <div style={{ fontSize: 20, fontFamily: FONTS.body, color: THEME.textSecondary, marginTop: 4 }}>
            Coverage Lift
          </div>
        </div>

        {/* After gauge */}
        <div style={{ textAlign: "center" }}>
          <TextOverlay text="Projected" fontSize={24} color={THEME.accent} delay={60} />
          <div style={{ marginTop: 16 }}>
            <CoverageGauge from={0} to={89} delay={70} />
          </div>
        </div>
      </div>

      {/* Bottom stats row */}
      <div style={{ display: "flex", gap: 24, marginTop: 80 }}>
        <StatCard label="New Stations" value={10} delay={160} color={THEME.suggested} />
        <StatCard label="Communities Served" value={17} delay={175} color={THEME.cluster} />
        <StatCard label="Avg Wait Reduction" value={12} suffix=" min" delay={190} color={THEME.underutilized} />
      </div>
    </AbsoluteFill>
  );
};
```

**Step 3: Create `video/src/scenes/Closing.tsx`**

```tsx
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { THEME, FONTS } from "../lib/theme";
import { TextOverlay } from "../components/TextOverlay";

const TECH_STACK = [
  { name: "Next.js 14", color: "#fff" },
  { name: "Python", color: "#3776AB" },
  { name: "Groq AI", color: "#f55036" },
  { name: "Leaflet", color: "#199900" },
  { name: "GNN", color: THEME.cluster },
  { name: "Open Charge Map", color: THEME.accent },
];

export const Closing: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Fade out at the end
  const fadeOut = interpolate(frame, [240, 300], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: THEME.bg,
        justifyContent: "center",
        alignItems: "center",
        opacity: fadeOut,
      }}
    >
      {/* Logo */}
      <div
        style={{
          fontSize: 64,
          fontFamily: FONTS.display,
          fontWeight: 800,
          color: THEME.textPrimary,
          textShadow: `0 0 20px ${THEME.accent}, 0 0 40px ${THEME.accent}40`,
        }}
      >
        ⚡ ChargePilot
      </div>

      {/* Tech stack pills */}
      <div style={{ display: "flex", gap: 12, marginTop: 40, flexWrap: "wrap", justifyContent: "center", maxWidth: 600 }}>
        {TECH_STACK.map((tech, i) => {
          const enter = spring({ frame: frame - 30 - i * 8, fps, config: { damping: 12, mass: 0.4 } });
          return (
            <div
              key={tech.name}
              style={{
                opacity: interpolate(enter, [0, 1], [0, 1]),
                transform: `scale(${interpolate(enter, [0, 1], [0.5, 1])})`,
                padding: "8px 20px",
                borderRadius: 20,
                border: `1px solid ${tech.color}60`,
                backgroundColor: `${tech.color}15`,
                fontFamily: FONTS.mono,
                fontSize: 14,
                color: tech.color,
              }}
            >
              {tech.name}
            </div>
          );
        })}
      </div>

      {/* Hackathon branding */}
      <TextOverlay
        text="Built at Hackathon 2026"
        fontSize={28}
        color={THEME.textSecondary}
        delay={80}
        subtitle
        style={{ marginTop: 48 }}
      />

      {/* Decorative line */}
      <div
        style={{
          width: 300,
          height: 2,
          backgroundColor: THEME.accent,
          marginTop: 32,
          opacity: 0.4,
          boxShadow: `0 0 10px ${THEME.accent}`,
        }}
      />
    </AbsoluteFill>
  );
};
```

**Step 4: Commit**

```bash
git add video/src/scenes/RunOptimization.tsx video/src/scenes/Results.tsx video/src/scenes/Closing.tsx
git commit -m "feat: add run optimization, results, and closing scenes"
```

---

### Task 7: Wire Up Video.tsx with Series + Verify

**Files:**
- Modify: `video/src/Video.tsx`

**Step 1: Update `video/src/Video.tsx` to compose all scenes**

```tsx
import { Series } from "remotion";
import { SCENES } from "./lib/theme";
import { TitleCard } from "./scenes/TitleCard";
import { TheProblem } from "./scenes/TheProblem";
import { Overview } from "./scenes/Overview";
import { Congestion } from "./scenes/Congestion";
import { GraphOptimization } from "./scenes/GraphOptimization";
import { ExpansionNodes } from "./scenes/ExpansionNodes";
import { RunOptimization } from "./scenes/RunOptimization";
import { Results } from "./scenes/Results";
import { Closing } from "./scenes/Closing";

export const DemoVideo: React.FC = () => {
  return (
    <Series>
      <Series.Sequence durationInFrames={SCENES.title.duration}>
        <TitleCard />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.problem.duration}>
        <TheProblem />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.overview.duration}>
        <Overview />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.congestion.duration}>
        <Congestion />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.graphOpt.duration}>
        <GraphOptimization />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.expansion.duration}>
        <ExpansionNodes />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.runOpt.duration}>
        <RunOptimization />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.results.duration}>
        <Results />
      </Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.closing.duration}>
        <Closing />
      </Series.Sequence>
    </Series>
  );
};
```

**Step 2: Launch Remotion Studio and verify all scenes render**

Run: `cd video && npx remotion studio src/index.ts`
Expected: All 9 scenes visible in the timeline, animations play smoothly.

**Step 3: Fix any TypeScript or rendering errors**

Iterate until all scenes render without errors.

**Step 4: Commit**

```bash
git add video/src/Video.tsx
git commit -m "feat: wire up all scenes into video composition"
```

---

### Task 8: Google Fonts Loading + Final Polish

**Files:**
- Modify: `video/src/Root.tsx` (add font loading)
- Create: `video/src/fonts.ts`

**Step 1: Create `video/src/fonts.ts`**

Remotion needs fonts loaded via `@remotion/google-fonts` or manual CSS.

```ts
import { continueRender, delayRender, staticFile } from "remotion";

const FONT_URLS = [
  "https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&display=swap",
  "https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap",
  "https://fonts.googleapis.com/css2?family=Azeret+Mono:wght@400;500;600;700&display=swap",
];

let fontsLoaded = false;

export async function loadFonts() {
  if (fontsLoaded) return;
  await Promise.all(
    FONT_URLS.map((url) =>
      fetch(url)
        .then((res) => res.text())
        .then((css) => {
          const style = document.createElement("style");
          style.textContent = css;
          document.head.appendChild(style);
        })
    )
  );
  fontsLoaded = true;
}
```

**Step 2: Load fonts in Root.tsx**

Update `Root.tsx` to call `calculateMetadata` for font loading:

```tsx
import { Composition } from "remotion";
import { DemoVideo } from "./Video";
import { loadFonts } from "./fonts";

export const Root: React.FC = () => {
  return (
    <Composition
      id="DemoVideo"
      component={DemoVideo}
      durationInFrames={3600}
      fps={30}
      width={1920}
      height={1080}
      calculateMetadata={async () => {
        await loadFonts();
        return { durationInFrames: 3600, fps: 30, width: 1920, height: 1080 };
      }}
    />
  );
};
```

**Step 3: Install `@remotion/google-fonts` as alternative**

Run: `cd video && npm install @remotion/google-fonts`

If Google Fonts import approach works better, switch to:
```ts
import { loadFont } from "@remotion/google-fonts/Syne";
import { loadFont as loadOutfit } from "@remotion/google-fonts/Outfit";
```

**Step 4: Verify fonts render correctly in Studio**

Run: `cd video && npx remotion studio src/index.ts`
Expected: Syne display font on titles, Outfit on body text, Azeret Mono on data.

**Step 5: Commit**

```bash
git add video/
git commit -m "feat: add font loading and final polish"
```

---

### Task 9: Render Final MP4

**Step 1: Render the video**

Run: `cd video && npx remotion render src/index.ts DemoVideo out/demo.mp4 --codec h264`
Expected: 2-minute MP4 at `video/out/demo.mp4`, 1920x1080, ~30-60MB

**Step 2: Add `out/` to `.gitignore`**

```
# video/out/
out/
```

**Step 3: Final commit**

```bash
git add video/.gitignore
git commit -m "feat: complete ChargePilot demo video pipeline"
```
