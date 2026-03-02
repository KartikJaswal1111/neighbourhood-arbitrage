/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          900: '#312e81',
        },
      },
      boxShadow: {
        card:        '0 1px 3px 0 rgba(0,0,0,0.04), 0 4px 16px 0 rgba(99,102,241,0.06)',
        'card-hover':'0 4px 12px 0 rgba(0,0,0,0.06), 0 12px 40px 0 rgba(99,102,241,0.14)',
        brand:       '0 4px 20px rgba(99,102,241,0.35)',
        success:     '0 4px 20px rgba(16,185,129,0.28)',
        danger:      '0 4px 20px rgba(244,63,94,0.28)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-in':   'slideIn 0.3s ease-out',
        'fade-up':    'fadeUp 0.5s ease-out',
      },
      keyframes: {
        slideIn: {
          '0%':   { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeUp: {
          '0%':   { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
