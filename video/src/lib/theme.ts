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
  title:       { from: 0,    duration: 240  },  // 0-8s
  problem:     { from: 240,  duration: 360  },  // 8-20s
  overview:    { from: 600,  duration: 450  },  // 20-35s
  congestion:  { from: 1050, duration: 450  },  // 35-50s
  graphOpt:    { from: 1500, duration: 450  },  // 50-65s
  expansion:   { from: 1950, duration: 450  },  // 65-80s
  runOpt:      { from: 2400, duration: 450  },  // 80-95s
  results:     { from: 2850, duration: 450  },  // 95-110s
  closing:     { from: 3300, duration: 300  },  // 110-120s
} as const;
