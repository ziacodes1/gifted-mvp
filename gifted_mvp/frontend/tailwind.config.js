/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Gifted visual system: cream surfaces, forest green, warm gold, sage.
        cream: {
          DEFAULT: "#F7F3EA",
          50: "#FCFAF4",
          100: "#F7F3EA",
          200: "#EFE7D6",
        },
        forest: {
          DEFAULT: "#1E4636",
          50: "#EAF0ED",
          600: "#255140",
          700: "#1E4636",
          800: "#163326",
          900: "#0F2419",
        },
        gold: {
          DEFAULT: "#C9A24B",
          50: "#FBF5E6",
          400: "#D8B968",
          500: "#C9A24B",
          600: "#A9853A",
        },
        sage: {
          DEFAULT: "#8FA697",
          200: "#D3DED6",
          400: "#A9BDB0",
          600: "#6E8577",
        },
        ink: "#22302A",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        serif: ["'Fraunces'", "Georgia", "serif"],
      },
      borderRadius: {
        xl: "1rem",
        "2xl": "1.5rem",
        "3xl": "2rem",
      },
      keyframes: {
        fadeIn: { from: { opacity: "0", transform: "translateY(2px)" }, to: { opacity: "1", transform: "none" } },
      },
      animation: {
        "fade-in": "fadeIn 400ms ease-out",
      },
      boxShadow: {
        card: "0 1px 2px rgba(30,70,54,0.04), 0 8px 24px rgba(30,70,54,0.06)",
        soft: "0 2px 12px rgba(30,70,54,0.05)",
      },
    },
  },
  plugins: [],
};
