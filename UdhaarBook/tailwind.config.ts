import type { Config } from 'tailwindcss'

export default <Config>{
  content: ['./app/**/*.{js,ts,jsx,tsx}', './components/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: 'hsl(210, 80%, 55%)',
        accent: 'hsl(35, 90%, 55%)',
        background: 'hsl(210, 20%, 98%)',
        foreground: 'hsl(210, 10%, 10%)',
      },
    },
  },
  plugins: [],
}
