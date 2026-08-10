/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"IBM Plex Sans"', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
      colors: {
        bg: '#fafaf9',
        panel: '#ffffff',
        border: '#e5e3df',
        ink: '#14140f',
        'ink-soft': '#6b6b63',
        accent: '#00d1b2',
        'accent-soft': '#e3fbf7',
        bull: '#e8734a',
        bear: '#5b7fa6',
        code: '#f2f1ed',
        // 涨跌/买卖三色
        up: '#00d1b2',
        'up-soft': '#1a3a35',
        down: '#ff3860',
        'down-soft': '#3a1a23',
        warn: "#ffdd57",
        gold: "#d4a017",
        'warn-soft': '#3a341a',
        // 深色仪表盘
        surface: '#0a0a0a',
        'surface-2': '#1a1a1a',
        'surface-3': '#222222',
        'surface-border': '#2a2a2a',
        'on-surface': '#e8e8e8',
        'on-surface-soft': '#8a8a8a',
      },
      animation: {
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'fade-in': 'fadeIn 0.2s ease-out',
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
      },
    },
  },
  plugins: [],
}