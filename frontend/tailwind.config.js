/** @type {import("tailwindcss").Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["IBM Plex Sans", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
      colors: {
        bg: "#0a0a0a",
        panel: "#161616",
        "panel-hover": "#1c1c1c",
        border: "#262626",
        "border-light": "#333333",
        ink: "#f5f5f5",
        "ink-soft": "#888888",
        "ink-dim": "#555555",
        gold: "#FFD700",
        up: "#ff3860",
        down: "#00d1b2",
        warn: "#ffdd57",
      },
      animation: {
        "fade-in-up": "fadeInUp 0.3s ease-out",
        "slide-in-right": "slideInRight 0.3s ease-out",
        "fade-in": "fadeIn 0.2s ease-out",
      },
      keyframes: {
        fadeInUp: {
          "0%": { transform: "translateY(8px)", opacity: 0 },
          "100%": { transform: "translateY(0)", opacity: 1 },
        },
        slideInRight: {
          "0%": { transform: "translateX(100%)", opacity: 0 },
          "100%": { transform: "translateX(0)", opacity: 1 },
        },
        fadeIn: {
          "0%": { opacity: 0 },
          "100%": { opacity: 1 },
        },
      },
    },
  },
  plugins: [],
}
