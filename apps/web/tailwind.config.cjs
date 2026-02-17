/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#f5f7fa",
        panel: "#ffffff",
        accent: "#2f6fed",
        accentSoft: "#e8efff",
        ink: "#1f2937",
        muted: "#6b7280"
      }
    }
  },
  plugins: []
};
