/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#0d9488',
          dark: '#0f766e',
          light: '#5eead4',
        },
        accent: {
          DEFAULT: '#f97316',
          hover: '#ea580c',
        },
        surface: '#f8fafc',
      },
      fontFamily: {
        sans: ['"DM Sans"', 'system-ui', 'sans-serif'],
        display: ['"Fraunces"', 'Georgia', 'serif'],
      },
      boxShadow: {
        nav: '0 8px 32px rgba(15, 118, 110, 0.08)',
        card: '0 12px 40px rgba(15, 23, 42, 0.08)',
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.25rem',
      },
    },
  },
  plugins: [],
}
