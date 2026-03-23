/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0E1117",
        surface: "#1E1E2E",
        "surface-hover": "#2A2A3C",
        border: "#3A3A4A",
        accent: "#6C5CE7",
        "accent-light": "#A29BFE",
        neutral: "#2ecc71",
        mild: "#f39c12",
        stressed: "#e74c3c",
        muted: "#a0a0b0",
      },
    },
  },
  plugins: [],
};
