/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        sidebar: "#404040",
      },
      fontFamily: {
        sans: ["Montserrat", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
