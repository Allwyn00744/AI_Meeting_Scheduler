import type { Config } from "tailwindcss";

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0A1220",
          900: "#0F1A2E",
          800: "#16213A",
          700: "#1E2C48",
        },
        brand: {
          50: "#EBF0FE",
          100: "#DCE6FD",
          500: "#3A66EC",
          600: "#2F5AE0",
          700: "#2447C0",
        },
      },
      borderRadius: {
        xl: "0.875rem",
        "2xl": "1.25rem",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px 0 rgba(16, 24, 40, 0.04)",
      },
    },
  },
  plugins: [],
} satisfies Config;
