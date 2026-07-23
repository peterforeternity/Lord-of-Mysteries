/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        mystic: {
          bg: "#1a1a2e",
          surface: "#16213e",
          card: "#0f3460",
          accent: "#c9a95c",
          "accent-dim": "#a8883a",
          text: "#e0e0e0",
          "text-dim": "#9e9e9e",
          danger: "#b91c1c",
          warning: "#d97706",
          success: "#059669",
          gold: "#c9a95c",
          "gold-light": "#e8d48b",
        },
      },
      fontFamily: {
        serif: ["Noto Serif SC", "Source Han Serif SC", "serif"],
        sans: ["Noto Sans SC", "Source Han Sans SC", "sans-serif"],
      },
    },
  },
  plugins: [],
};
