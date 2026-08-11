/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"IBM Plex Sans"', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'SF Mono', 'Menlo', 'Consolas', 'Roboto Mono', 'monospace'],
      },
      colors: {
        bg: '#0a0a0a',
        panel: '#161616',
        'panel-hover': '#1c1c1c',
        border: '#262626',
        'border-light': '#333333',
        ink: '#f5f5f5',
        'ink-soft': '#888888',
        'ink-dim': '#555555',
        gold: '#FFD700',
        up: '#ff3860',
        warn: '#ffdd57',
        down: '#ff3860',
      },
      animation: {
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'fade-in': 'fadeIn 0.2s ease-out',
        'fade-in-up': 'fadeInUp 0.3s ease-out both',
      },
      keyframes: {
        slideInRight: {
          '0%': { transform: 'translateX(100%)', opacity: 0 },
          '100%': { transform: 'translateX(0)', opacity: 1 },
        },
        fadeIn: {
          '0%': { opacity: 0 },
          '100%': { opacity: 1 },
        },
        fadeInUp: {
          '0%': { opacity: 0, transform: 'translateY(8px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
