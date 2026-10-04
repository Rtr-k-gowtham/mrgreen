/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#080c0a",
        surface: {
          DEFAULT: "#0f1713",
          light: "#16231d",
          border: "#1e332a",
        },
        green: {
          50: "#f0fdf4",
          100: "#dcfce7",
          200: "#bbf7d0",
          300: "#86efac",
          400: "#4ade80",
          500: "#22c55e",
          600: "#16a34a",
          700: "#15803d",
          800: "#166534",
          900: "#14532d",
          950: "#052e16",
        },
        emerald: {
          400: "#34d399",
          500: "#10b981",
          600: "#059669",
        }
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "spin-slow": "spin 8s linear infinite",
        "orb-idle": "orb-breathe 4s ease-in-out infinite",
        "orb-listening": "orb-pulse 1.5s ease-in-out infinite",
        "orb-speaking": "orb-wave 1.2s ease-in-out infinite",
      },
      keyframes: {
        "orb-breathe": {
          "0%, 100%": { transform: "scale(1)", opacity: "0.85" },
          "50%": { transform: "scale(1.05)", opacity: "1" },
        },
        "orb-pulse": {
          "0%, 100%": { transform: "scale(0.98)", boxShadow: "0 0 20px 2px rgba(16, 185, 129, 0.4)" },
          "50%": { transform: "scale(1.1)", boxShadow: "0 0 35px 8px rgba(16, 185, 129, 0.75)" },
        },
        "orb-wave": {
          "0%, 100%": { transform: "scale(1)", filter: "hue-rotate(0deg)" },
          "50%": { transform: "scale(1.08)", filter: "hue-rotate(25deg)" },
        }
      }
    },
  },
  plugins: [],
};
