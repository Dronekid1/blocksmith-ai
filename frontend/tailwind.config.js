/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Minecraft-inspired colors
        'mc-green': '#5B8731',
        'mc-brown': '#8B5A2B',
        'mc-stone': '#7F7F7F',
        'mc-dirt': '#79553A',
        'mc-gold': '#FCEE4B',
        'mc-diamond': '#4AEDD9',
        'mc-emerald': '#17DD62',
        'mc-redstone': '#FF0000',
      },
    },
  },
  plugins: [],
}
