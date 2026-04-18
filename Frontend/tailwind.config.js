/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html","./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#080D1A",
        surface: "#0F1628",
        surfaceHigh: "#161E35",
        primary: { DEFAULT: "#6366F1", dark: "#4F46E5", light: "#818CF8" },
        secondary: { DEFAULT: "#8B5CF6", dark: "#7C3AED" },
        accent: { DEFAULT: "#22D3EE", dark: "#0EA5E9" },
        success: "#10B981",
        warning: "#F59E0B",
        error: "#EF4444",
        textMain: "#F1F5F9",
        textMuted: "#64748B",
      },
      fontFamily: {
        display: ['Syne', 'system-ui', 'sans-serif'],
        sans: ['DM Sans', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'grid-pattern': "linear-gradient(to right, rgba(99,102,241,0.06) 1px, transparent 1px), linear-gradient(to bottom, rgba(99,102,241,0.06) 1px, transparent 1px)",
      },
    },
  },
  plugins: [],
}
