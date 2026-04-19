/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html","./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        background:  "#ffffff",
        surface:     "#fafafa",
        surfaceHigh: "#f4f4f5",
        // Deep violet primary (Solus-style)
        primary:   { DEFAULT: "#6d28d9", dark: "#4c1d95", light: "#8b5cf6" },
        // Dark near-black for contrast sections
        secondary: { DEFAULT: "#0a0a0a", dark: "#000000" },
        // Gold accent (underline highlights, NEW badges)
        accent:    { DEFAULT: "#f5c518", dark: "#fbbf24" },
        success:   "#16a34a",
        warning:   "#d97706",
        error:     "#b91c1c",
        // Near-black body text on white
        textMain:  "#0a0a0a",
        textMuted: "#71717a",
      },
      fontFamily: {
        // Heavy grotesk for display (big bold headings like Solus)
        display: ['"Space Grotesk"', 'Inter', 'system-ui', 'sans-serif'],
        sans:    ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono:    ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      backgroundImage: {
        'grid-pattern': "linear-gradient(to right, rgba(10,10,10,0.04) 1px, transparent 1px), linear-gradient(to bottom, rgba(10,10,10,0.04) 1px, transparent 1px)",
      },
      letterSpacing: {
        tightest: '-0.05em',
        tighter2: '-0.03em',
      },
    },
  },
  plugins: [],
}
