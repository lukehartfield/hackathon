import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        deep:          '#04080f',
        surface:       '#0c1524',
        card:          '#111d30',
        'card-hover':  '#162640',
        border:        '#1e3050',
        accent:        '#00d4ff',
        overloaded:    '#ff3860',
        balanced:      '#ffb020',
        underutilized: '#00e68a',
        suggested:     '#4d8dff',
      },
      fontFamily: {
        display: ['"Syne"', 'system-ui', 'sans-serif'],
        body:    ['"Outfit"', 'system-ui', 'sans-serif'],
        mono:    ['"Azeret Mono"', 'ui-monospace', 'monospace'],
      },
      animation: {
        'fade-in':    'fade-in 0.5s ease-out both',
        'slide-up':   'slide-up 0.6s ease-out both',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};
export default config;
