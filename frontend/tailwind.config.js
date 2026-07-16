/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        darkBg: '#0b0f19',
        cardBg: '#161b26',
        borderBg: '#232d3f',
      },
    },
  },
  plugins: [],
}
