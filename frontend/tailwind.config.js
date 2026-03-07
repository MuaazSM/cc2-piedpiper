/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Syne"', 'sans-serif'],
        body: ['"DM Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        // Page accent colors — fox stroke + glow per route
        amber:  { fox: '#f59e0b', glow: '#b45309' },
        cyan:   { fox: '#06b6d4', glow: '#0e7490' },
        emerald:{ fox: '#10b981', glow: '#047857' },
        violet: { fox: '#8b5cf6', glow: '#6d28d9' },
        rose:   { fox: '#f43f5e', glow: '#be123c' },
        // Base
        surface: '#0d0d0d',
        card:    '#141414',
        border:  '#1f1f1f',
        muted:   '#6b6b6b',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
}