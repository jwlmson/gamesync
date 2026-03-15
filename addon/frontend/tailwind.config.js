/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: '#F4F1EA',
        navy: '#1C2B36',
        accent: '#D94833',
        muted: '#3A5063',
        'green-status': '#27ae60',
      },
      fontFamily: {
        rokkitt: ['Rokkitt', 'serif'],
        archivo: ['Archivo', 'sans-serif'],
        handwritten: ['Reenie Beanie', 'cursive'],
      },
      boxShadow: {
        hard: '4px 6px 0px #1C2B36',
        'hard-sm': '2px 3px 0px #1C2B36',
        'hard-accent': '4px 6px 0px #D94833',
      },
    },
  },
  plugins: [],
}
