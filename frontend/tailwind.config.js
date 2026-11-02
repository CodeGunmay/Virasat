/** @type {import('tailwindcss').Config} */
module.exports = {
  content: {
    files: [
      "./index.html",
      "./src/**/*.{js,ts,jsx,tsx}",
    ],
  },
  theme: {
    extend: {
      colors: {
        sandbox: {
          50: "#faf3f0",
          100: "#f5e8e2",
          200: "#ede1d5",
          300: "#e8d5c8",
          500: "#deb2ae",
          600: "#c59aa0",
          800: "#81686a",
          900: "#58454a",
        },
        virasat: {
          sandstone: "#f4e8d2",
          "warm-ivory": "#f5f0e2",
          "heritage-maroon": "#b84f55",
          "deep-indigo": "#2a3a5c",
          "rest-gold": "#d4af3c",
        },
      },
      fontFamily: {
        display: ["'Playfair Display'", "serif"],
        body: ["'Inter'", "sans-serif"],
      },
    },
  },
  plugins: [],
};
