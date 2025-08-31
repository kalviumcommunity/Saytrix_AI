/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'deep-charcoal': '#0D1117',
        'neon-green': '#00FFA2',
        'electric-blue': '#00C2FF',
        'fuchsia': '#FF0077',
        'light-gray': '#B0B3B8',
        'stock-green': '#00C851',
        'stock-red': '#FF4444',
      },
      fontFamily: {
        'sans': ['Calibri', 'system-ui', 'sans-serif']
      }
    },
  },
  plugins: [],
}

